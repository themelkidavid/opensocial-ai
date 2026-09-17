import json
import os
import unittest

from src.evidence import EvidenceItem
from src.llm_interpretation import InterpretationEvidence, InterpretationRequest, InterpretationValidator
from src.providers.openai_interpretation import (
    OpenAIInterpretationConfigurationError, OpenAIInterpretationError, OpenAIInterpretationProvider,
)


class _Response:
    def __init__(self, output_text, identifier="resp-safe-1"):
        self.output_text, self.id = output_text, identifier


class _Responses:
    def __init__(self, outcome): self.outcome, self.calls = outcome, []
    def create(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.outcome, Exception): raise self.outcome
        return self.outcome


class _Client:
    def __init__(self, outcome): self.responses = _Responses(outcome)


class TimeoutFailure(Exception): pass
class RateLimitFailure(Exception): pass
class AuthenticationFailure(Exception): pass


class TestOpenAIInterpretation(unittest.TestCase):
    def setUp(self):
        self.item = EvidenceItem("report", "Members reported that peer meetings improved coordination.", location="North", population="members")
        self.request = InterpretationRequest([InterpretationEvidence("e1", self.item.content, "report", location="North", population="members")])
        self.claim = {"claim_id": "c1", "evidence_id": "e1", "statement": self.item.content,
                      "subject": "peer meetings", "relation": "reported_outcome", "object_or_outcome": "coordination",
                      "direction": "increase", "polarity": "positive", "qualifiers": [], "context": {},
                      "supporting_text_span": self.item.content}

    def provider(self, payload):
        return OpenAIInterpretationProvider(model="test-model", client=_Client(_Response(json.dumps(payload))))

    def test_adapter_implements_contract_and_preserves_model_provenance(self):
        provider = self.provider({"claims": [self.claim], "mechanisms": [], "conflicts": [], "uncertainties": []})
        response = provider.interpret(self.request)
        self.assertEqual((response.provider_name, response.provider_version), ("openai", "test-model"))
        result = InterpretationValidator().validate(response, {"e1": self.item})
        self.assertEqual(result.claims[0].provenance["provider_version"], "test-model")

    def test_injected_client_receives_only_request_data_and_no_network(self):
        client = _Client(_Response(json.dumps({"claims": [], "mechanisms": [], "conflicts": [], "uncertainties": []})))
        OpenAIInterpretationProvider(model="test-model", client=client).interpret(self.request)
        call = client.responses.calls[0]
        body = json.loads(call["input"][1]["content"])
        self.assertEqual(body, self.request.to_dict())
        self.assertNotIn("OPENAI_API_KEY", str(call))
        self.assertEqual(call["model"], "test-model")

    def test_missing_key_or_optional_sdk_is_a_clear_configuration_error(self):
        saved = os.environ.pop("OPENAI_API_KEY", None)
        try:
            with self.assertRaisesRegex(OpenAIInterpretationConfigurationError, "OPENAI_API_KEY"):
                OpenAIInterpretationProvider(model="test-model").interpret(self.request)
        finally:
            if saved is not None: os.environ["OPENAI_API_KEY"] = saved

    def test_malformed_empty_and_unsupported_responses_are_rejected(self):
        for output in ("", "not-json", json.dumps({"claims": []}), json.dumps({"claims": [], "mechanisms": [], "conflicts": [], "uncertainties": [], "prose": "no"})):
            with self.assertRaises(OpenAIInterpretationError):
                OpenAIInterpretationProvider(model="test-model", client=_Client(_Response(output))).interpret(self.request)

    def test_hallucinated_content_still_fails_provider_neutral_validator(self):
        for key, value in (("subject", "invented organisation"), ("object_or_outcome", "99 participants"),
                           ("evidence_id", "unknown"), ("supporting_text_span", "not in source")):
            claim = dict(self.claim); claim[key] = value
            response = self.provider({"claims": [claim], "mechanisms": [], "conflicts": [], "uncertainties": []}).interpret(self.request)
            with self.assertRaises(ValueError): InterpretationValidator().validate(response, {"e1": self.item})

    def test_provider_failures_are_stable_and_do_not_expose_secrets(self):
        for error, expected in ((TimeoutFailure(), "timed out"), (RateLimitFailure(), "rate limited"),
                                (AuthenticationFailure(), "authentication failed"), (RuntimeError("sk-test-secret"), "request failed")):
            with self.assertRaisesRegex(OpenAIInterpretationError, expected) as raised:
                OpenAIInterpretationProvider(model="test-model", client=_Client(error)).interpret(self.request)
            self.assertNotIn("sk-test-secret", str(raised.exception))

    def test_core_imports_without_openai_sdk_or_configuration(self):
        from src.narrative_reasoning import NarrativeReasoningEngine
        self.assertTrue(NarrativeReasoningEngine().analyse([self.item], ["e1"]).claims)


if __name__ == "__main__":
    unittest.main()
