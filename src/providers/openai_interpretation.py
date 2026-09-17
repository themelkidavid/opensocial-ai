"""Optional OpenAI Responses API adapter for structured evidence interpretation.

The SDK is imported only when a real client is needed. This module does not
validate, persist, or promote output; the provider-neutral validator remains
the authoritative boundary.
"""

import json
import os
from typing import Optional

from src.llm_interpretation import InterpretationProvider, InterpretationRequest, InterpretationResponse


class OpenAIInterpretationConfigurationError(RuntimeError):
    """Raised when the optional OpenAI adapter lacks usable configuration."""


class OpenAIInterpretationError(RuntimeError):
    """Stable, credential-safe error for an OpenAI interpretation request."""


class OpenAIInterpretationProvider(InterpretationProvider):
    """Translate the Responses API into the existing untrusted response schema."""

    DEFAULT_MODEL = "gpt-4.1-mini"
    SYSTEM_INSTRUCTION = (
        "Extract only structured, source-attributed evidence interpretations. "
        "Use only supplied evidence and quote a short supporting text span for every claim or mechanism. "
        "Unknown information must remain unknown. Identify possible disagreements or context differences without deciding truth. "
        "Do not recommend, rank, select a strategy, infer effectiveness or causality, authorize anything, infer consent, "
        "or provide chain-of-thought. Return JSON matching the requested schema."
    )
    _SCHEMA = {
        "type": "object", "additionalProperties": False,
        "properties": {
            "claims": {"type": "array", "items": {"type": "object"}},
            "mechanisms": {"type": "array", "items": {"type": "object"}},
            "conflicts": {"type": "array", "items": {"type": "object"}},
            "uncertainties": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["claims", "mechanisms", "conflicts", "uncertainties"],
    }

    def __init__(self, model: Optional[str] = None, client=None) -> None:
        self.model = (model or os.environ.get("OPENAI_INTERPRETATION_MODEL") or self.DEFAULT_MODEL).strip()
        if not self.model:
            raise OpenAIInterpretationConfigurationError("An OpenAI interpretation model is required")
        self._client = client

    def _client_or_raise(self):
        if self._client is not None:
            return self._client
        if not os.environ.get("OPENAI_API_KEY"):
            raise OpenAIInterpretationConfigurationError("OPENAI_API_KEY is required to use OpenAIInterpretationProvider")
        try:
            from openai import OpenAI
        except ImportError as error:
            raise OpenAIInterpretationConfigurationError(
                "OpenAI support is optional; install requirements-openai.txt to use OpenAIInterpretationProvider"
            ) from error
        self._client = OpenAI()
        return self._client

    def interpret(self, request: InterpretationRequest) -> InterpretationResponse:
        if not isinstance(request, InterpretationRequest):
            raise TypeError("OpenAI interpretation requires an InterpretationRequest")
        try:
            response = self._client_or_raise().responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": self.SYSTEM_INSTRUCTION},
                    {"role": "user", "content": json.dumps(request.to_dict(), separators=(",", ":"))},
                ],
                text={"format": {"type": "json_schema", "name": "evidence_interpretation", "strict": False,
                                  "schema": self._SCHEMA}},
            )
        except OpenAIInterpretationConfigurationError:
            raise
        except Exception as error:
            name = error.__class__.__name__.casefold()
            if "timeout" in name:
                raise OpenAIInterpretationError("OpenAI interpretation request timed out") from None
            if "rate" in name or "limit" in name:
                raise OpenAIInterpretationError("OpenAI interpretation request was rate limited") from None
            if "auth" in name or "permission" in name:
                raise OpenAIInterpretationError("OpenAI interpretation authentication failed") from None
            raise OpenAIInterpretationError("OpenAI interpretation request failed") from None
        return self._parse_response(response)

    def _parse_response(self, response) -> InterpretationResponse:
        text = getattr(response, "output_text", None)
        if not isinstance(text, str) or not text.strip():
            raise OpenAIInterpretationError("OpenAI response did not contain structured JSON")
        try:
            payload = json.loads(text)
        except (TypeError, json.JSONDecodeError):
            raise OpenAIInterpretationError("OpenAI response contained malformed structured JSON") from None
        if not isinstance(payload, dict) or set(payload) - {"claims", "mechanisms", "conflicts", "uncertainties"}:
            raise OpenAIInterpretationError("OpenAI response used an unsupported interpretation schema")
        try:
            return InterpretationResponse(
                claims=payload["claims"], mechanisms=payload["mechanisms"], conflicts=payload["conflicts"],
                uncertainties=payload["uncertainties"], provider_name="openai", provider_version=self.model,
                interpretation_id=("openai-" + response.id) if isinstance(getattr(response, "id", None), str) else None,
            )
        except (KeyError, TypeError, ValueError):
            raise OpenAIInterpretationError("OpenAI response used an unsupported interpretation schema") from None
