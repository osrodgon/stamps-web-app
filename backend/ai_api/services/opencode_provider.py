"""
opencode LLM provider for AI-powered stamp series extraction.

The only provider the API talks to. It calls the opencode Console **inference
API**, which serves the OpenAI chat completions shape over plain HTTP, so neither
the opencode binary nor `opencode serve` runs anywhere near the backend:

    POST https://opencode.ai/inference/openai/v1/chat/completions
    Authorization: Bearer <OPENCODE_API_KEY>

The model is configuration, not code: it travels in the request body
(`OPENCODE_MODEL`), so swapping engines is an `.env` change. Requests use the
OpenAI chat completions shape; Console translates every text model to it, so a
GPT, Claude or Gemini model works from here too — its native endpoint in the
Console catalogue only says what its provider speaks.

Batching, prompt formatting, JSON cleaning and the orchestration of a large
series live in `BaseLLMProvider`; this module only does the transport and the
three extraction hooks.

Dependencies:
    - requests: HTTP client for the inference API
    - django.conf.settings: for `OPENCODE_*`
    - ai_api.services.base_llm_provider: the shared workflow
    - ai_api.services.prompts: prompt templates

Usage:
    from ai_api.services.opencode_provider import OpenCodeProvider
    provider = OpenCodeProvider()
    result = provider.series_extract("Olimpiadas", "1992", "cleaned_data")
"""

from typing import Any, Dict, List

import requests
from django.conf import settings

from ai_api.services.base_llm_provider import BaseLLMProvider
from ai_api.services.prompts import (
    SERIES_EXTRACTION_PROMPT_TEMPLATE,
    SERIES_HEADER_EXTRACTION_PROMPT_TEMPLATE,
    SERIES_BATCH_EXTRACTION_PROMPT_TEMPLATE,
)
from common.api.messages import Messages


class OpenCodeProvider(BaseLLMProvider):
    """
    opencode provider for research on stamp series.

    Reads its configuration from Django settings, sends one chat completion per
    prompt and returns the parsed JSON. Errors are logged with the status code and
    the beginning of the body, because that is what tells a wrong key (401) from a
    model that is not available to this account (403) from a rate limit (429).

    Attributes:
        api_key: Console API key, sent as a bearer token.
        model_name: model to ask for, taken from `OPENCODE_MODEL`.
        base_url: API root, `OPENCODE_BASE_URL` by default.
        timeout: seconds to wait for one call, `OPENCODE_TIMEOUT` by default.
    """

    def __init__(self) -> None:
        """Load the configuration and the prompt templates."""
        super().__init__()

        self.api_key = settings.OPENCODE_API_KEY
        if not self.api_key:
            raise ValueError(Messages.AI.missing_api_key())

        self.model_name = settings.OPENCODE_MODEL
        if not self.model_name:
            raise ValueError(Messages.AI.missing_model_name())

        self.base_url = settings.OPENCODE_BASE_URL.rstrip("/")
        self.timeout = settings.OPENCODE_TIMEOUT
        self.max_tokens = settings.OPENCODE_MAX_TOKENS

        self.prompt_template = SERIES_EXTRACTION_PROMPT_TEMPLATE
        self.header_prompt_template = SERIES_HEADER_EXTRACTION_PROMPT_TEMPLATE
        self.batch_prompt_template = SERIES_BATCH_EXTRACTION_PROMPT_TEMPLATE

        self.log.debug(f"OpenCodeProvider initialized with model: {self.model_name}")

    # ------------------------------------------------------------------
    # Extraction hooks
    # ------------------------------------------------------------------

    def _single_extract(self, clean_data: str) -> Dict[str, Any]:
        """Extract the whole series in one call."""
        return self._complete(self._format_prompt(clean_data), "series")

    def _extract_header(self, serie_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the series-level fields in one call."""
        return self._complete(self._format_header_prompt(serie_info), "header")

    def _extract_batch(
        self,
        serie_info: Dict[str, Any],
        stamp_batch: List[Dict[str, Any]],
        batch_number: int,
        total_batches: int
    ) -> Dict[str, Any]:
        """Extract one batch of stamps."""
        prompt = self._format_batch_prompt(
            serie_info, stamp_batch, batch_number, total_batches
        )
        return self._complete(prompt, f"batch {batch_number}/{total_batches}")

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------

    def _complete(self, prompt: str, label: str) -> Dict[str, Any]:
        """
        Ask the model for one JSON answer and return it parsed.

        Args:
            prompt: the formatted prompt to send.
            label: what this call is, for the log lines.

        Returns:
            The response parsed as a dictionary.

        Raises:
            ValueError: if the answer carries no text or is not valid JSON.
            Exception: if the request fails, or the API answers with an error.
        """
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }

        self.log.debug(
            f"Sending {label} request to the opencode inference API "
            f"({self.model_name})"
        )

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as error:
            self.log.error(f"{label} request failed: {error}")
            raise Exception(Messages.AI.service_error(f"request failed: {error}"))

        if response.status_code >= 400:
            body = (response.text or "")[:300]
            self.log.error(
                f"{label} request answered {response.status_code}: {body}"
            )
            raise Exception(
                Messages.AI.service_error(f"HTTP {response.status_code}: {body}")
            )

        data = response.json()
        self.log.debug(f"Usage for {label}: {data.get('usage')}")

        content = self._content_of(data)
        if not content:
            self.log.warning(f"Received empty response for {label}")
            raise ValueError(Messages.AI.empty_response())

        self.log.debug(f"Received {label} response (length: {len(content)})")
        self.log.debug(content)

        cleaned_response = self._clean_json_response(content)
        return self._parse_json_response(cleaned_response)

    @staticmethod
    def _content_of(data: Dict[str, Any]) -> str:
        """Return the text of the first choice, or an empty string."""
        choices = data.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        return message.get("content") or ""
