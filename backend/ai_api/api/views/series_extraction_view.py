from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from dataclasses import replace
from typing import Any, Dict, List
from urllib.parse import urlparse

from django.conf import settings
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from ai_api.sources.errors import (
    SourceConfigurationError,
    SourceError,
    SourceNotAllowed,
    SourceNotFound,
    SourceUnavailable,
)
from ai_api.budget import Budget, BudgetExpired
from ai_api.sources.base import Observation
from ai_api.sources.fesofi import FesofiCatalogue
from ai_api.sources.filatelia import FilateliaCatalogue
from ai_api.sources.http import get_client
from ai_api.sources.search_prices import SearchPrices
from ai_api.valuation import MINIMUM_SAMPLE, value
from ai_api.services.search_service import SearchService
from ai_api.services.scraping_service import ScrapingService
from ai_api.services.llm_service import LLMService
from ai_api.api.serializers.series_extraction_request_serializer import SeriesExtractionRequestSerializer
from ai_api.api.serializers.series_extraction_response_serializer import SeriesExtractionResponseSerializer


class SeriesExtractionView(Logger, APIView):
    """
    API view for AI-powered series extraction.

    This view handles POST requests to extract information for series with the LLM provider.
    It validates input data, calls the AI service, and returns structured research results.
    """
    serializer_class = SeriesExtractionResponseSerializer
    
    @extend_schema(
        operation_id="series_extraction_post",
        tags=['AI Services'],
        summary="Extract Information for Series using AI",
        description="Performs AI-powered extraction of series information with the LLM provider. "
                    "Requires a name (either series name or the motive of one of the stamps in the serie) and publication date.",
        request=SeriesExtractionRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                SeriesExtractionResponseSerializer, 
                name="SeriesExtractionCompleted",
                description="Series extraction completed successfully.",
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="SeriesExtractionInvalidPayload",
                success=False,
                description="Invalid request payload (e.g., missing required fields)."
                ),
            status.HTTP_401_UNAUTHORIZED: standardized_response(
                GenericResponseSerializer,
                name="SeriesExtractionUnauthorized",
                success=False,
                description="Authentication required."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                GenericResponseSerializer,
                name="SeriesExtractionPermissionDenied",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="SeriesExtractionNotFound",
                success=False,
                description="Series not found."
            ),
            status.HTTP_422_UNPROCESSABLE_ENTITY: standardized_response(
                GenericResponseSerializer,
                name="SeriesExtractionValidationError",
                success=False,
                description="AI returned invalid or unparseable data."
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: standardized_response(
                GenericResponseSerializer,
                name="SeriesExtractionServiceError",
                success=False,
                description="AI service unavailable or internal error."
            )
        }
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Handles POST requests to perform AI series extraction.

        Args:
            request: The incoming HTTP request containing series extraction parameters.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with extraction results and appropriate HTTP status.
        """
        self.log.debug(Messages.Post.create_one("research request", request.data))
        
        # Get payload and validate it
        payload = SeriesExtractionRequestSerializer(data=request.data)
        
        if not payload.is_valid():
            self.log.warning(Messages.Post.validation_failed("research request", payload.errors))
            return Response(
                data=GenericResponseSerializer(GenericResponse(payload.errors)).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract data from payload
        name = payload.validated_data.get('name')
        date = payload.validated_data.get('date')
        
        try:
            # The clock for this request: when it runs out, the answer is partial.
            budget = Budget(
                total=settings.AI_BUDGET_SECONDS,
                per_call=settings.AI_BUDGET_PER_CALL,
            )

            # Initialize the catalogue, the search, the scraper and the model
            self.log.debug(f"Starting AI research for name: {name} ({date})")
            catalogue = FesofiCatalogue()
            # The catalogue has its own chain of calls; each one gets what the
            # budget allows, so a slow shop cannot hold the request forever.
            try:
                catalogue.timeout = budget.timeout_for(settings.AI_SOURCE_TIMEOUT)
            except BudgetExpired:
                catalogue.timeout = 0.5

            search_service = SearchService()
            scraping_service = ScrapingService()
            llm_service = LLMService()

            match = None
            identity_gap = None

            # A URL plus date "0" skips every lookup, but only for a host the
            # client may fetch: accepting any URL here made the endpoint an
            # authenticated HTTP proxy (SSRF, §1 #3).
            if self._is_url(name) and self._is_zero_date(date):
                if not self._is_source_url(name):
                    raise SourceNotAllowed(
                        f"{urlparse(name).hostname or name} is not an allowed host."
                    )
                self.log.debug(f"Using provided URL directly: {name}")
                clean_data = self._scraped(scraping_service, name)
            else:
                # The catalogue answers with the facts themselves; the search and
                # the scraper are what is left when it does not.
                match = catalogue.identify(name, date)
                if match.found:
                    term = (match.term or {}).get("name", "")
                    self.log.debug(
                        f"Catalogue match: '{term}' (score {match.score})"
                    )
                    clean_data = catalogue.facts(match.products)
                else:
                    self.log.warning(f"Catalogue has no answer: {match.gap}")
                    identity_gap = match.gap
                    url = search_service.find_series_url(name, date)
                    if url is None:
                        message = (
                            f"Could not find anything for name: {name} "
                            f"and date: {date}"
                        )
                        if match.gap:
                            message = f"{message} ({match.gap})"
                        self.log.warning(message)
                        return Response(
                            data=GenericResponseSerializer(GenericResponse({
                                "error": None,
                                "message": message
                            })).data,
                            status=status.HTTP_404_NOT_FOUND
                        )
                    clean_data = self._scraped(scraping_service, url)

            serie_info = clean_data.get("serie_info") or {}

            # Send cleaned scraped data to LLM
            name = serie_info.get("issue_name")
            date = serie_info.get("issue_date")
            llm_result = llm_service.series_extract(
                name=name,
                date=date,
                clean_data=str(clean_data),
            )
            
            # Create response serializer
            response_serializer = SeriesExtractionResponseSerializer(data=llm_result)
            
            if not response_serializer.is_valid():
                self.log.error(f"AI response validation failed: {response_serializer.errors}")
                return Response(
                    data=GenericResponseSerializer(GenericResponse({
                        "error": response_serializer.errors,
                        "message": Messages.AI.response_format_error()
                    })).data,
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )

            validated = response_serializer.validated_data

            # Every value comes from an observation: whatever the provider wrote
            # is overwritten with what the sources support, or with null.
            observations, unfinished = self._prices(clean_data, budget)
            by_code = self._by_code(observations)

            for stamp in validated.get("stamps") or []:
                if not isinstance(stamp, dict):
                    continue
                code = str(stamp.get("edifil_code") or "").strip()
                found = by_code.get(code, [])
                stamp["market_value_mnh"] = self._number(value(found, condition="mnh"))
                stamp["market_value_used"] = self._number(value(found, condition="used"))

            # A series is not the sum of its stamps: without an observation of the
            # complete set there is no series value, and adding one up would be
            # inventing it.
            validated["market_value_mnh"] = None
            validated["market_value_used"] = None
            validated["observations"] = [self._observation_row(item) for item in observations]

            gaps = list(validated.get("gaps") or [])
            if identity_gap:
                gaps.append({"field": "identity", "reason": identity_gap})
            if unfinished:
                gaps.append(
                    {
                        "field": "budget",
                        "reason": (
                            f"The {budget.total:g}s budget ran out before pricing "
                            f"every stamp; ask again and the cache finishes it."
                        ),
                    }
                )
            if not observations:
                gaps.append(
                    {
                        "field": "market_value",
                        "reason": "No price was found for any of the stamps.",
                    }
                )
            validated["gaps"] = gaps
            validated["partial"] = bool(unfinished)

            self.log.debug(f"AI series extraction completed successfully for series: {name}")
            return Response(
                data=response_serializer.data,
                status=status.HTTP_200_OK
            )
        
        except SourceConfigurationError as e:
            # A missing URL or key is a deployment problem: it is not "not found".
            self.log.error(f"AI series extraction is not configured: {str(e)}")
            return Response(
                data=GenericResponseSerializer(GenericResponse({
                    "error": Messages.AI.error(),
                    "message": str(e)
                })).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except SourceNotAllowed as e:
            self.log.error(f"AI series extraction refused a host: {str(e)}")
            return Response(
                data=GenericResponseSerializer(GenericResponse({
                    "error": Messages.AI.validation_error(),
                    "message": str(e)
                })).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        except SourceNotFound as e:
            self.log.warning(f"AI series extraction found nothing: {str(e)}")
            return Response(
                data=GenericResponseSerializer(GenericResponse({
                    "error": None,
                    "message": str(e) or Messages.AI.error()
                })).data,
                status=status.HTTP_404_NOT_FOUND
            )
        except SourceUnavailable as e:
            self.log.error(f"AI series extraction source unavailable: {str(e)}")
            return Response(
                data=GenericResponseSerializer(GenericResponse({
                    "error": Messages.AI.unavailable(),
                    "message": str(e)
                })).data,
                status=status.HTTP_502_BAD_GATEWAY
            )
        except ValueError as e:
            self.log.error(f"AI series extraction validation error: {str(e)}")
            return Response(
                data=GenericResponseSerializer(GenericResponse({
                    "error": Messages.AI.validation_error(),
                    "message": str(e)
                })).data,
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as e:
            self.log.error(f"AI series extraction failed for series: {name}: {str(e)}")
            return Response(
                data=GenericResponseSerializer(GenericResponse({
                    "error": Messages.AI.error(),
                    "message": Messages.AI.unavailable()
                })).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _prices(
        self, clean_data: dict, budget: Budget
    ) -> tuple[List[Observation], bool]:
        """Ask the sources for the price of the first stamps of the series.

        The shop answers with stock and a written condition; the search answers
        with asking prices and a condition guessed from the listing. The search is
        only asked when the shop did not give enough prices to estimate, because
        every stamp costs one query.

        Returns:
            The observations found, and whether the budget cut the work short.
        """
        shop = FilateliaCatalogue()
        search = SearchPrices()

        stamps = (clean_data.get("stamps") or [])[: settings.AI_PRICE_STAMPS]
        serie = clean_data.get("serie_info") or {}
        year = str(serie.get("year") or "")
        label = str(serie.get("issue_name") or "")

        observations: List[Observation] = []
        seen = set()
        unfinished = False

        for stamp in stamps:
            code = str(stamp.get("edifil_code") or "").strip()
            if not code:
                continue

            try:
                timeout = budget.timeout_for(settings.AI_SOURCE_TIMEOUT)
            except BudgetExpired:
                self.log.warning("Budget exhausted while pricing; answering what we have")
                unfinished = True
                break

            found = self._ask(shop.prices, code, year, timeout)
            if len(found) < MINIMUM_SAMPLE:
                found += self._ask(search.prices, code, label, year, timeout)

            for observation in found:
                key = (observation.source, observation.url, observation.price)
                if key in seen:
                    continue
                seen.add(key)
                # The code we asked for is the link between a price and a stamp,
                # so it is set here even if a source forgets to carry it.
                observations.append(
                    observation
                    if observation.subject_code
                    else replace(observation, subject_code=code)
                )

        self.log.debug(f"{len(observations)} observation(s) for the series")
        return observations, unfinished

    def _ask(self, prices, *args) -> List[Observation]:
        """Call a price source, turning its failure into a log line."""
        try:
            return list(prices(*args))
        except SourceError as error:
            self.log.warning(f"Could not price {args[0]}: {error}")
            return []

    @staticmethod
    def _by_code(observations: List[Observation]) -> Dict[str, List[Observation]]:
        """Group the observations by the catalogue code they price."""
        grouped: Dict[str, List[Observation]] = {}
        for observation in observations:
            grouped.setdefault(observation.subject_code, []).append(observation)
        return grouped

    @staticmethod
    def _number(estimate) -> float | None:
        """Return the estimate as a JSON number, or None when there is none."""
        if estimate.estimate is None:
            return None
        return float(estimate.estimate)

    @staticmethod
    def _observation_row(observation: Observation) -> Dict[str, Any]:
        """Shape one observation the way the response contract speaks."""
        return {
            "source": observation.source,
            "external_id": observation.external_id,
            "url": observation.url,
            "kind": observation.kind,
            "price": observation.price,
            "currency": observation.currency,
            "condition": observation.condition,
            "observed_at": observation.observed_at,
            "subject_code": observation.subject_code,
        }

    def _scraped(self, scraping_service: ScrapingService, url: str) -> dict:
        """Fetch a series page and clean it, or fail with a reason (422)."""
        series_urls = scraping_service.extract_links(url)
        content = scraping_service.scrape_content(series_urls)
        clean_data = scraping_service.clean_scraped_data(content)

        if not content or not (clean_data.get("serie_info") or {}):
            # Nothing was scraped: that is a contract problem (422), not a
            # missing series (404) and not a crash behind a 500.
            self.log.warning(f"Nothing could be scraped from {url}")
            raise ValueError(f"No catalogue data could be read from {url}.")

        return clean_data

    @staticmethod
    def _is_url(name: str) -> bool:
        """Return True when the value carries an http(s) scheme."""
        if not name or not isinstance(name, str):
            return False

        return urlparse(name.strip()).scheme in ("http", "https")

    def _is_source_url(self, name: str) -> bool:
        """
        Check whether the name is a URL the source client may fetch.

        The allowlist decides, not a regex: before this, any host was accepted and
        the endpoint worked as an authenticated HTTP proxy.

        Args:
            name (str): The value received in the `name` field.

        Returns:
            bool: True when it is an http(s) URL of an allowlisted host.
        """
        if not name or not isinstance(name, str):
            return False

        return get_client().is_allowed(name.strip())

    def _is_zero_date(self, date: str) -> bool:
        """
        Check if the provided date represents zero or empty value.
        
        Args:
            date (str): The date to check
            
        Returns:
            bool: True if the date is zero, empty, or represents no date, False otherwise
        """
        if not date:
            return True
        
        # Convert to string and normalize
        date_str = str(date).strip().lower()
        
        # Check for various representations of zero/empty date
        zero_values = ['0', '00', '0000', '0000-00-00', '00/00/0000', 
                      'none', 'null', '', 'undefined', 'n/a', 'na']
        
        return date_str in zero_values
