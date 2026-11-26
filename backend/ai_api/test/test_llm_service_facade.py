"""
Tests for LLMService (facade pattern).

The service is a thin door to whichever provider the factory builds; with one
provider that is opencode. These tests check the delegation and the error
wrapping, not the transport (that is `test_opencode_provider.py`).
"""

from unittest.mock import Mock

import pytest

from ai_api.services.llm_service import LLMService
from ai_api.services.opencode_provider import OpenCodeProvider
from ai_api.services.provider_factory import ProviderFactory
from common.api.messages import Messages


def use_provider(mocker, provider):
    """Make every LLMService built in this test use `provider`."""
    mocker.patch.object(ProviderFactory, "create_provider", return_value=provider)
    return provider


class TestLLMServiceInit:
    """What the service builds when it starts."""

    def test_init_creates_provider_factory(self, mocker):
        mock_provider = Mock()
        use_provider(mocker, mock_provider)

        service = LLMService()

        assert service.provider_factory is not None
        assert service.provider == mock_provider

    def test_init_uses_the_opencode_provider(self, settings):
        settings.OPENCODE_API_KEY = "oc_sk_test"
        settings.OPENCODE_MODEL = "test-model"

        service = LLMService()

        assert isinstance(service.provider, OpenCodeProvider)

    def test_a_stale_llm_provider_variable_is_ignored(self, settings, monkeypatch):
        settings.OPENCODE_API_KEY = "oc_sk_test"
        settings.OPENCODE_MODEL = "test-model"
        monkeypatch.setenv("LLM_PROVIDER", "groq")

        service = LLMService()

        assert isinstance(service.provider, OpenCodeProvider)

    def test_a_missing_key_stops_the_service(self, settings):
        settings.OPENCODE_API_KEY = None
        settings.OPENCODE_MODEL = "test-model"

        with pytest.raises(Exception, match="Provider initialization failed"):
            LLMService()


class TestLLMServiceSeriesExtract:
    """The service's only job: hand the call to the provider and wrap failures."""

    def test_series_extract_delegates_to_provider(self, mocker):
        mock_provider = Mock()
        mock_provider.series_extract.return_value = {
            "issue_name": "Test Series",
            "description": "Test description",
            "stamps": [],
        }
        use_provider(mocker, mock_provider)

        service = LLMService()
        result = service.series_extract("Test Series", "1992", '{"data": "test"}')

        mock_provider.series_extract.assert_called_once_with(
            "Test Series", "1992", '{"data": "test"}'
        )
        assert result["issue_name"] == "Test Series"

    def test_series_extract_passes_all_arguments(self, mocker):
        mock_provider = Mock()
        mock_provider.series_extract.return_value = {"result": "success"}
        use_provider(mocker, mock_provider)

        service = LLMService()
        service.series_extract("Name", "Date", "CleanData")

        mock_provider.series_extract.assert_called_once_with(
            "Name", "Date", "CleanData"
        )

    def test_a_validation_error_becomes_a_service_error(self, mocker):
        mock_provider = Mock()
        mock_provider.series_extract.side_effect = ValueError(
            Messages.AI.missing_input_data()
        )
        use_provider(mocker, mock_provider)

        service = LLMService()

        with pytest.raises(Exception, match="Extraction service error"):
            service.series_extract("Test", "1992", "")

    def test_a_generic_error_becomes_a_service_error(self, mocker):
        mock_provider = Mock()
        mock_provider.series_extract.side_effect = Exception("API connection failed")
        use_provider(mocker, mock_provider)

        service = LLMService()

        with pytest.raises(Exception, match="Extraction service error"):
            service.series_extract("Test", "1992", "data")


class TestLLMServiceFacade:
    """The caller does not need to know what is behind the door."""

    def test_the_service_returns_what_the_provider_returns(self, mocker):
        mock_provider = Mock()
        mock_provider.series_extract.return_value = {
            "issue_name": "Castillos",
            "description_source": "llm",
            "stamps": [{"edifil_code": "4349"}],
        }
        use_provider(mocker, mock_provider)

        service = LLMService()
        result = service.series_extract("Castillos", "2007", '{"serie_info": {}}')

        assert result["stamps"][0]["edifil_code"] == "4349"
        assert result["description_source"] == "llm"
