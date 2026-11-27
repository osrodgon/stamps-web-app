"""
Search service for AI-powered stamp series extraction.

This module provides web search capabilities to locate stamp series information
from external philatelic catalogs. It integrates with the Serper API (Google Search API)
to find reference URLs for stamp issues, which are then used by the AI service
to gather additional data for series extraction.

The service is specifically designed to search the Spanish philatelic catalog
(catalogodesellos.fesofi.es) to find product pages for stamp issues based on
their name and publication date.

Dependencies:
    - ai_api.sources.http: the shared client that performs the request
    - common.log.logger: For consistent logging throughout the application
    - _backend.settings: For accessing Serper API configuration

Integration:
    - Used by SeriesExtractionView in the AI workflow
    - Part of the ai_api.services module
    - Works in conjunction with LLMService for complete series extraction
"""

from typing import Optional

from ai_api.sources.errors import (
    SourceConfigurationError,
    SourceError,
    SourceUnavailable,
)
from ai_api.sources.fesofi import FesofiCatalogue
from ai_api.sources.http import HttpClient, get_client
from common.log.logger import Logger
from _backend.settings import SERPER_URL, SERPER_API_KEY


class SearchService(Logger):
    """
    Service class for performing web searches to locate stamp series information.
    
    This service uses the Serper API to search for stamp issues on the Spanish
    philatelic catalog (catalogodesellos.fesofi.es). It constructs targeted search
    queries using stamp name and publication date to find the corresponding product
    page URLs.
    
    The search results are used by the AI service pipeline to gather reference data
    for stamp series extraction and validation.
    
    Attributes:
        Inherits from Logger for consistent application logging
        
    Methods:
        find_series_url: Searches for and returns the URL of a stamp series page
        
    Usage:
        search_service = SearchService()
        url = search_service.find_series_url("Olimpiadas", "1992")
    """
    def __init__(self, client: Optional[HttpClient] = None) -> None:
        """Take the shared HTTP client, or the one a test injects."""
        super().__init__()
        self.client = client or get_client()

    def find_series_url(self, name: str, date: str) -> Optional[str]:
        """
        Search for and return the URL of a stamp series page from the Spanish philatelic catalog.
        
        This method performs a targeted web search using the Serper API to find product pages
        for specific stamp issues on catalogodesellos.fesofi.es. The search is constructed
        using the stamp issue name and publication date to ensure precise results.
        
        Args:
            name (str): The name of the stamp issue (e.g., "Olimpiadas", "Animales")
            date (str): The publication date of the stamp issue (e.g., "1992", "2023")
            
        Returns:
            Optional[str]:  The URL of the first matching product page if found, otherwise None.
                            Returns None if the search worked and no organic
                            result contains "/producto/".
        
        Raises:
            SourceConfigurationError: If the backend has no URL or key, or the key
                is refused. A deployment problem must not look like "not found".
            SourceUnavailable: If the backend is down or keeps failing.
            SourceError: If the answer is not JSON.
            
        Example:
            >>> search_service = SearchService()
            >>> url = search_service.find_series_url("Olimpiadas", "1992")
            >>> print(url)  # https://catalogodesellos.fesofi.es/producto/olimpiadas-1992/
            
        Note:
            ``None`` means the search worked and the catalogue has no product page
            for that series. A failure to ask at all raises instead: the endpoint
            answers 404 only when the answer was "there is nothing here".
        """
        # The catalogue comes first: it answers by attribute, so "navidad 1986"
        # finds the series whose name contains those words, which a quoted web
        # search does not. Serper stays as the fallback for anything else.
        catalogue_url = self._catalogue_url(name, date)
        if catalogue_url is not None:
            return catalogue_url

        if not SERPER_URL or not SERPER_API_KEY:
            raise SourceConfigurationError(
                "The search backend is not configured: SERPER_URL and "
                "SERPER_API_KEY are required."
            )

        query = f'site:catalogodesellos.fesofi.es "{name}" "{date}"'

        self.log.debug(f"Sending request to Serper API for query: {query}")
        response = self.client.post(
            SERPER_URL,
            json={
                "q": query,
                "gl": "es",  # Geographic location: Spain for regional accuracy
            },
            headers={"X-API-KEY": SERPER_API_KEY},
        )

        if response.status_code in (401, 403):
            raise SourceConfigurationError(
                f"The search backend refused the key (HTTP {response.status_code})."
            )

        if response.status_code >= 400:
            raise SourceUnavailable(
                f"The search backend answered HTTP {response.status_code}."
            )

        try:
            results = response.json()
        except ValueError as error:
            raise SourceError("The search backend did not answer JSON.") from error

        for item in results.get("organic") or []:
            link = item.get("link", "")
            if "/producto/" in link:
                return link

        # None means the search worked and there is no product page for it.
        return None

    def _catalogue_url(self, name: str, date: str) -> Optional[str]:
        """Ask the Fesofi catalogue first; None when it has no answer.

        A catalogue failure is logged and swallowed on purpose: the fallback can
        still find the page, and a source being down must not fail the whole
        lookup before trying the other one.
        """
        try:
            urls = FesofiCatalogue(self.client).find_product_urls(name, date)
        except SourceError as error:
            self.log.warning(f"Fesofi lookup failed, falling back to search: {error}")
            return None

        return urls[0] if urls else None
