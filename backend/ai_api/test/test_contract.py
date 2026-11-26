"""Contract tests for the extraction response (plan step A1).

The point of the step: the response says where each text comes from, carries the
prices it found with the page that supports them, and returns null instead of an
invented number when there is nothing to back it.
"""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from rest_framework import status

from _backend.settings import AI_ISSUES_EXTRACTION_URL_V1
from ai_api.api.serializers.series_extraction_response_serializer import (
    SeriesExtractionResponseSerializer,
)
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client
from common.test.ai_api_test_data import (
    series_extraction_cleaned_data,
    series_extraction_request_payload_ok,
    series_extraction_response_data,
)


@pytest.fixture(autouse=True)
def no_catalogue_match():
    """Keep the catalogue off the network: this file tests the response shape."""
    from unittest.mock import Mock as _Mock

    from ai_api.sources.fesofi import Match

    stub = _Mock()
    stub.identify.return_value = Match(gap="not in the catalogue")
    stub.facts.return_value = {}

    with patch(
        "ai_api.api.views.series_extraction_view.FesofiCatalogue", return_value=stub
    ):
        yield stub


FULL_PAYLOAD = {
    "issue_name": "Isabel II",
    "description": "Primer sello español, 6 cuartos negro sin dentar.",
    "description_source": "fesofi",
    "issue_date": "1850-01-01",
    "artist": "Bartolomé Coromina",
    "printer": "Fábrica Nacional del Sello",
    "print_type": "Litografía",
    "perforation": "Sin dentar",
    "paper_type": None,
    "stamp_type": "Sello",
    "notes": "",
    "total_printed": 6226727,
    "market_value_mnh": None,
    "market_value_used": None,
    "sources": [
        {
            "source": "fesofi",
            "status": "ok",
            "url": "https://catalogodesellos.fesofi.es/producto/0001/",
        },
        {"source": "colnect", "status": "skipped"},
    ],
    "observations": [
        {
            "source": "todocoleccion",
            "external_id": "123",
            "url": "https://www.todocoleccion.net/lote/123",
            "kind": "ask",
            "price": "24.00",
            "currency": "EUR",
            "condition": "used",
            "observed_at": "2026-11-25T10:00:00Z",
        }
    ],
    "valuation": {
        "estimate": "22.00",
        "min": "19.00",
        "max": "31.00",
        "currency": "EUR",
        "sample_size": 4,
        "method": "trimmed_mean",
        "sources": ["todocoleccion"],
        "as_of": "2026-11-25T10:00:00Z",
    },
    "gaps": [{"field": "market_value_mnh", "reason": "no mint observation"}],
    "stamps": [
        {
            "edifil_code": "1",
            "face_value": "6 cuartos",
            "description": "Isabel II mirando a la izquierda.",
        }
    ],
}


class TestResponseContract:
    """The serializer accepts and returns the whole contract."""

    def test_a_full_payload_round_trips(self):
        serializer = SeriesExtractionResponseSerializer(data=FULL_PAYLOAD)

        assert serializer.is_valid(), serializer.errors
        data = serializer.data

        assert data["description_source"] == "fesofi"
        assert data["observations"][0]["source"] == "todocoleccion"
        assert data["observations"][0]["kind"] == "ask"
        assert data["observations"][0]["price"] == Decimal("24.00")
        assert data["valuation"]["sample_size"] == 4
        assert data["valuation"]["method"] == "trimmed_mean"
        assert data["valuation"]["sources"] == ["todocoleccion"]
        assert data["sources"][1]["status"] == "skipped"
        assert data["gaps"][0]["field"] == "market_value_mnh"

    def test_a_payload_without_the_new_blocks_still_validates(
        self, series_extraction_response_data
    ):
        serializer = SeriesExtractionResponseSerializer(
            data=series_extraction_response_data
        )

        assert serializer.is_valid(), serializer.errors
        data = serializer.data

        assert data["observations"] == []
        assert data["sources"] == []
        assert data["valuation"] is None
        assert data["gaps"] == []

    def test_the_description_is_labelled_as_written_by_the_model(self):
        payload = dict(FULL_PAYLOAD)
        payload.pop("description_source")

        serializer = SeriesExtractionResponseSerializer(data=payload)
        serializer.is_valid()

        assert serializer.data["description_source"] == "llm"

    def test_every_stamp_description_carries_the_same_label(self):
        serializer = SeriesExtractionResponseSerializer(data=FULL_PAYLOAD)
        serializer.is_valid()

        assert serializer.data["stamps"][0]["description_source"] == "llm"

    def test_an_observation_needs_a_known_source(self):
        payload = dict(FULL_PAYLOAD)
        payload["observations"] = [
            {"source": "wallapop", "kind": "ask", "price": "1.00"}
        ]

        serializer = SeriesExtractionResponseSerializer(data=payload)

        assert not serializer.is_valid()
        assert "observations" in serializer.errors

    def test_a_valuation_without_an_estimate_is_allowed(self):
        payload = dict(FULL_PAYLOAD)
        payload["valuation"] = {"estimate": None, "sample_size": 1}

        serializer = SeriesExtractionResponseSerializer(data=payload)

        assert serializer.is_valid(), serializer.errors
        assert serializer.data["valuation"]["estimate"] is None


class TestEndpointNeverInventsPrices(AbstractApiUnitTest):
    """The endpoint returns the new blocks and leaves the prices empty (A1)."""

    def test_prices_are_null_even_when_the_provider_writes_them(
        self,
        api_client,
        series_extraction_request_payload_ok,
        series_extraction_response_data,
        series_extraction_cleaned_data,
    ):
        self.permission(granted=True)

        search = Mock()
        search.find_series_url.return_value = "https://example.invalid/serie"

        scraping = Mock()
        scraping.extract_links.return_value = ["https://example.invalid/serie"]
        scraping.scrape_content.return_value = "raw"
        scraping.clean_scraped_data.return_value = series_extraction_cleaned_data

        llm = Mock()
        llm.series_extract.return_value = series_extraction_response_data

        with patch(
            "ai_api.api.views.series_extraction_view.SearchService", return_value=search
        ), patch(
            "ai_api.api.views.series_extraction_view.ScrapingService",
            return_value=scraping,
        ), patch(
            "ai_api.api.views.series_extraction_view.LLMService", return_value=llm
        ):
            response = api_client.post(
                f"/{AI_ISSUES_EXTRACTION_URL_V1}",
                series_extraction_request_payload_ok,
                format="json",
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]

        assert data["market_value_mnh"] is None
        assert data["market_value_used"] is None
        assert data["stamps"][0]["market_value_mnh"] is None
        assert data["stamps"][0]["market_value_used"] is None
        assert data["observations"] == []
        assert data["sources"] == []
        assert data["valuation"] is None
        # The catalogue did not identify it and the search rescued it: the
        # response says so instead of pretending the identity is certain.
        assert [gap["field"] for gap in data["gaps"]] == ["identity"]
        assert data["description_source"] == "llm"
