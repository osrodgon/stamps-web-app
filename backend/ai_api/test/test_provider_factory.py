"""
Tests for the LLM provider factory (plan step A1b).

With a single provider the factory is thin, and these tests keep it that way:
it builds opencode, it does not read `LLM_PROVIDER` any more, and a failure to
build says why.
"""

from unittest.mock import Mock

import pytest

from ai_api.services.opencode_provider import OpenCodeProvider
from ai_api.services.provider_factory import ProviderFactory
from common.api.messages import Messages


class TestCreateProvider:
    """What the factory builds."""

    def test_it_builds_the_opencode_provider(self, settings):
        settings.OPENCODE_API_KEY = "oc_sk_test"
        settings.OPENCODE_MODEL = "test-model"

        provider = ProviderFactory().create_provider()

        assert isinstance(provider, OpenCodeProvider)

    def test_a_stale_llm_provider_variable_is_ignored(self, settings, monkeypatch):
        settings.OPENCODE_API_KEY = "oc_sk_test"
        settings.OPENCODE_MODEL = "test-model"
        monkeypatch.setenv("LLM_PROVIDER", "gemini")

        provider = ProviderFactory().create_provider()

        assert isinstance(provider, OpenCodeProvider)

    def test_a_missing_key_surfaces_as_an_initialization_error(self, settings):
        settings.OPENCODE_API_KEY = None
        settings.OPENCODE_MODEL = "test-model"

        with pytest.raises(Exception) as error:
            ProviderFactory().create_provider()

        assert "Provider initialization failed" in str(error.value)
        assert Messages.AI.missing_api_key() in str(error.value)

    def test_a_missing_model_surfaces_too(self, settings):
        settings.OPENCODE_API_KEY = "oc_sk_test"
        settings.OPENCODE_MODEL = None

        with pytest.raises(Exception) as error:
            ProviderFactory().create_provider()

        assert Messages.AI.missing_model_name() in str(error.value)

    def test_it_reports_a_failed_construction(self, mocker):
        broken = Mock(side_effect=RuntimeError("boom"))
        mocker.patch.dict(ProviderFactory.PROVIDER_TYPES, {"opencode": broken})

        with pytest.raises(Exception) as error:
            ProviderFactory().create_provider()

        assert "boom" in str(error.value)


class TestAvailableProviders:
    """The class-level helpers, which now answer for one provider."""

    def test_the_list_has_only_opencode(self):
        assert ProviderFactory.get_available_providers() == ["opencode"]

    def test_opencode_is_available(self):
        assert ProviderFactory.is_provider_available("opencode") is True
        assert ProviderFactory.is_provider_available("OPENCODE") is True

    def test_gemini_and_groq_are_not(self):
        assert ProviderFactory.is_provider_available("gemini") is False
        assert ProviderFactory.is_provider_available("groq") is False
