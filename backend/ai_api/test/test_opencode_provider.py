"""
Tests for the opencode provider (plan step A1b).

The provider is the only door to a model now, so these tests pin three things:
the request it builds (endpoint, bearer token, model in the body), what it does
with the answer (JSON, fences, empty, error), and that a large series still goes
header + batches without a second code path.
"""

import json
import re
from unittest.mock import Mock, patch

import pytest
import requests

from ai_api.services.base_llm_provider import BaseLLMProvider
from ai_api.services.opencode_provider import OpenCodeProvider
from common.api.messages import Messages


SETTINGS = {
    "OPENCODE_API_KEY": "oc_sk_test",
    "OPENCODE_MODEL": "test-model",
    "OPENCODE_BASE_URL": "https://opencode.test/inference/openai/v1",
    "OPENCODE_TIMEOUT": 30,
    "OPENCODE_MAX_TOKENS": 4096,
}


@pytest.fixture
def settings_patch(settings):
    """Point the provider at a fake endpoint with a fake key."""
    for key, value in SETTINGS.items():
        setattr(settings, key, value)
    return settings


@pytest.fixture
def provider(settings_patch) -> OpenCodeProvider:
    """A provider configured against the fake endpoint."""
    return OpenCodeProvider()


def response(content: str, status_code: int = 200, usage=None) -> Mock:
    """Build a fake `requests.Response` carrying one chat completion."""
    reply = Mock()
    reply.status_code = status_code
    reply.text = content
    reply.json.return_value = {
        "choices": [{"message": {"content": content}}],
        "usage": usage or {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.001},
    }
    return reply


class TestConfiguration:
    """The provider refuses to run without a key and a model."""

    def test_missing_api_key_raises(self, settings):
        settings.OPENCODE_API_KEY = None

        with pytest.raises(ValueError, match=re.escape(Messages.AI.missing_api_key())):
            OpenCodeProvider()

    def test_missing_model_raises(self, settings):
        settings.OPENCODE_MODEL = None

        with pytest.raises(
            ValueError, match=re.escape(Messages.AI.missing_model_name())
        ):
            OpenCodeProvider()

    def test_it_reads_the_endpoint_and_the_limits_from_settings(self, provider):
        assert provider.base_url == "https://opencode.test/inference/openai/v1"
        assert provider.model_name == "test-model"
        assert provider.timeout == 30
        assert provider.max_tokens == 4096

    def test_it_is_a_base_llm_provider(self, provider):
        assert isinstance(provider, BaseLLMProvider)


class TestRequest:
    """What goes out: endpoint, token and model."""

    @patch("ai_api.services.opencode_provider.requests.post")
    def test_it_posts_to_chat_completions_with_a_bearer_token(self, post, provider):
        post.return_value = response('{"issue_name": "Castillos"}')

        provider._single_extract('{"serie_info": {}}')

        url = post.call_args.args[0]
        headers = post.call_args.kwargs["headers"]
        assert url == "https://opencode.test/inference/openai/v1/chat/completions"
        assert headers["Authorization"] == "Bearer oc_sk_test"
        assert post.call_args.kwargs["timeout"] == 30

    @patch("ai_api.services.opencode_provider.requests.post")
    def test_the_model_travels_in_the_body(self, post, provider):
        post.return_value = response('{"issue_name": "Castillos"}')

        provider._single_extract('{"serie_info": {}}')

        payload = post.call_args.kwargs["json"]
        assert payload["model"] == "test-model"
        assert payload["temperature"] == 0
        assert payload["max_tokens"] == 4096
        assert payload["response_format"] == {"type": "json_object"}
        assert payload["messages"][0]["role"] == "user"


class TestAnswer:
    """What comes back: JSON, fenced JSON, empty or broken."""

    @patch("ai_api.services.opencode_provider.requests.post")
    def test_it_parses_the_json_it_gets(self, post, provider):
        post.return_value = response('{"issue_name": "Castillos", "stamps": []}')

        result = provider._single_extract('{"serie_info": {}}')

        assert result["issue_name"] == "Castillos"

    @patch("ai_api.services.opencode_provider.requests.post")
    def test_it_strips_a_markdown_fence(self, post, provider):
        fenced = '```json\n{"issue_name": "Castillos"}\n```'
        post.return_value = response(fenced)

        result = provider._single_extract('{"serie_info": {}}')

        assert result["issue_name"] == "Castillos"

    @patch("ai_api.services.opencode_provider.requests.post")
    def test_an_empty_answer_raises(self, post, provider):
        post.return_value = response("")

        with pytest.raises(ValueError, match=Messages.AI.empty_response()):
            provider._single_extract('{"serie_info": {}}')

    @patch("ai_api.services.opencode_provider.requests.post")
    def test_a_payload_without_choices_raises(self, post, provider):
        empty = Mock()
        empty.status_code = 200
        empty.json.return_value = {"choices": []}
        post.return_value = empty

        with pytest.raises(ValueError, match=Messages.AI.empty_response()):
            provider._single_extract('{"serie_info": {}}')


class TestFailures:
    """A bad key, a missing model and a network error say what happened."""

    @patch("ai_api.services.opencode_provider.requests.post")
    def test_a_401_names_the_status_and_the_body(self, post, provider):
        post.return_value = response('{"error": "invalid api key"}', status_code=401)

        with pytest.raises(Exception) as error:
            provider._single_extract('{"serie_info": {}}')

        assert "401" in str(error.value)
        assert "invalid api key" in str(error.value)

    @patch("ai_api.services.opencode_provider.requests.post")
    def test_a_403_is_reported_too(self, post, provider):
        post.return_value = response("free models are not available here", 403)

        with pytest.raises(Exception) as error:
            provider._single_extract('{"serie_info": {}}')

        assert "403" in str(error.value)

    @patch("ai_api.services.opencode_provider.requests.post")
    def test_a_connection_error_is_wrapped(self, post, provider):
        post.side_effect = requests.ConnectionError("no route to host")

        with pytest.raises(Exception) as error:
            provider._single_extract('{"serie_info": {}}')

        assert "request failed" in str(error.value)


class TestWorkflow:
    """Small series one call, large series header plus batches (from the base)."""

    @patch("ai_api.services.opencode_provider.OpenCodeProvider._complete")
    def test_a_small_series_is_one_call(self, complete, provider):
        complete.return_value = {
            "issue_name": "Castillos",
            "stamps": [{"edifil_code": "1"}],
        }
        clean_data = json.dumps(
            {"serie_info": {"título serie": "Castillos"}, "stamps": [{"id": 1}]}
        )

        result = provider.series_extract("Castillos", "2007", clean_data)

        assert complete.call_count == 1
        assert "Castillos" in complete.call_args.args[0]
        assert result["issue_name"] == "Castillos"

    @patch("ai_api.services.opencode_provider.OpenCodeProvider._complete")
    def test_a_large_series_is_header_plus_batches(self, complete, provider, settings):
        stamps = [
            {"id": index} for index in range(settings.LLM_BATCH_SIZE * 2 + 1)
        ]
        clean_data = json.dumps(
            {"serie_info": {"título serie": "Grande"}, "stamps": stamps}
        )

        complete.side_effect = [
            {"issue_name": "Grande"},
            {"stamps": [{"edifil_code": "1"}]},
            {"stamps": [{"edifil_code": "2"}]},
            {"stamps": [{"edifil_code": "3"}]},
        ]

        result = provider.series_extract("Grande", "1992", clean_data)

        assert complete.call_count == 4
        assert len(result["stamps"]) == 3

    def test_empty_input_is_refused(self, provider):
        with pytest.raises(ValueError, match="No input data provided"):
            provider.series_extract("Castillos", "2007", "   ")
