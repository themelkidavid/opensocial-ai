import unittest

from src.evidence import EvidenceItem
from src.llm_interpretation import (
    InterpretationEvidence, InterpretationRequest, InterpretationResponse,
    InterpretationValidator, StaticInterpretationProvider, compare_interpretations,
    set_interpretation_review_state,
)
from src.narrative_reasoning import NarrativeReasoningEngine


class _BrokenProvider:
    def interpret(self, request):
        raise RuntimeError("no network")


class _CaptureProvider:
    def __init__(self, response): self.response, self.request = response, None
    def interpret(self, request): self.request = request; return self.response


class TestLLMInterpretation(unittest.TestCase):
    def setUp(self):
        self.evidence = {
            "e1": EvidenceItem("report", "Members reported that peer meetings improved coordination.", "2026", "North", "members"),
            "e2": EvidenceItem("report", "Members reported that peer meetings showed no meaningful change in coordination.", "2026", "South", "members"),
        }

    def claim(self, evidence_id="e1", identifier="c1"):
        return {"claim_id": identifier, "evidence_id": evidence_id,
                "statement": self.evidence[evidence_id].content, "subject": "peer meetings",
                "relation": "reported_outcome", "object_or_outcome": "coordination",
                "direction": "increase" if evidence_id == "e1" else "no_change",
                "polarity": "positive" if evidence_id == "e1" else "neutral",
                "qualifiers": [], "context": {}, "supporting_text_span": self.evidence[evidence_id].content}

    def mechanism(self):
        item = EvidenceItem("report", "Teams introduced peer meetings to support coordination.", location="North")
        return item, {"evidence_id": "m1", "mechanism_text": item.content, "action": "introduced",
                      "target": "peer meetings", "intended_or_observed_effect": "coordination",
                      "context": {}, "supporting_text_span": item.content}

    def response(self, **changes):
        value = InterpretationResponse(claims=[self.claim()], provider_name="fixture")
        for key, item in changes.items(): setattr(value, key, item)
        return value

    def test_request_response_and_fixture_provider_are_deterministic(self):
        request = InterpretationRequest([InterpretationEvidence("e1", "text", "report")])
        provider = StaticInterpretationProvider(self.response())
        self.assertEqual(request.to_dict(), InterpretationRequest([InterpretationEvidence("e1", "text", "report")]).to_dict())
        self.assertEqual(provider.interpret(request).to_dict(), provider.interpret(request).to_dict())

    def test_grounded_claim_is_machine_extracted_not_fact(self):
        result = InterpretationValidator().validate(self.response(), self.evidence)
        claim = result.claims[0]
        self.assertEqual(claim.review_state, "machine_extracted")
        self.assertEqual(claim.provenance["interpretation_method"], "llm_assisted")
        self.assertEqual(claim.evidence_id, "e1")
        supplied = self.claim(); supplied["review_state"] = "human_reviewed"
        self.assertEqual(InterpretationValidator().validate(self.response(claims=[supplied]), self.evidence).claims[0].review_state, "machine_extracted")
        self.assertEqual(set_interpretation_review_state(claim, "human_reviewed").review_state, "human_reviewed")
        self.assertEqual(set_interpretation_review_state(claim, "rejected").review_state, "rejected")

    def test_deterministic_identifier_and_duplicate_suppression(self):
        generated = self.claim(); generated.pop("claim_id")
        first = InterpretationValidator().validate(self.response(claims=[generated]), self.evidence)
        second = InterpretationValidator().validate(self.response(claims=[generated]), self.evidence)
        self.assertEqual(first.claims[0].claim_id, second.claims[0].claim_id)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            InterpretationValidator().validate(self.response(claims=[self.claim(), self.claim()]), self.evidence)

    def test_unsupported_text_numeric_location_span_and_evidence_are_rejected(self):
        for key, value in (("subject", "invented organisation"), ("object_or_outcome", "99 participants"),
                           ("supporting_text_span", "not in source"), ("evidence_id", "missing")):
            record = self.claim(); record[key] = value
            with self.assertRaises(ValueError): InterpretationValidator().validate(self.response(claims=[record]), self.evidence)
        record = self.claim(); record["context"] = {"location": "Invented place"}
        with self.assertRaises(ValueError): InterpretationValidator().validate(self.response(claims=[record]), self.evidence)

    def test_invalid_direction_relation_and_missing_provider_provenance_are_rejected(self):
        for key, value in (("direction", "guaranteed"), ("relation", "causes"), ("polarity", "certain")):
            record = self.claim(); record[key] = value
            with self.assertRaises(ValueError): InterpretationValidator().validate(self.response(claims=[record]), self.evidence)
        with self.assertRaises(ValueError):
            InterpretationValidator().validate(InterpretationResponse(claims=[self.claim()], provider_name=""), self.evidence)

    def test_mechanism_is_grounded_candidate_and_never_inspiration(self):
        item, record = self.mechanism()
        result = InterpretationValidator().validate(self.response(claims=[], mechanisms=[record]), {"m1": item})
        self.assertEqual(result.mechanism_candidates[0].review_state, "machine_extracted")
        self.assertIn("not a proven intervention", result.mechanism_candidates[0].limitations[0])
        record["action"] = "recommend"
        with self.assertRaises(ValueError): InterpretationValidator().validate(self.response(claims=[], mechanisms=[record]), {"m1": item})

    def test_conflicts_require_known_claims_and_keep_context_difference(self):
        conflict = {"conflict_id": "x", "topic": "peer meetings", "claim_a_reference": "c1", "claim_b_reference": "c2",
                    "conflict_type": "context_difference", "explanation": "Sources describe different contexts.",
                    "context_difference": {"location": "different"}}
        result = InterpretationValidator().validate(self.response(claims=[self.claim("e1", "c1"), self.claim("e2", "c2")], conflicts=[conflict]), self.evidence)
        self.assertEqual(result.conflict_candidates[0].conflict_type, "context_difference")
        conflict["claim_b_reference"] = "unknown"
        with self.assertRaises(ValueError): InterpretationValidator().validate(self.response(claims=[self.claim()], conflicts=[conflict]), self.evidence)

    def test_malformed_freeform_response_fails_closed(self):
        with self.assertRaises(TypeError): InterpretationValidator().validate(InterpretationResponse(claims=["prose"], provider_name="fixture"), self.evidence)

    def test_no_provider_keeps_rule_based_analysis_unchanged(self):
        items = list(self.evidence.values())
        first = NarrativeReasoningEngine().analyse(items, ["e1", "e2"])
        second = NarrativeReasoningEngine().analyse(items, ["e1", "e2"])
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertNotIn("assisted_claims", first.to_dict())

    def test_provider_results_are_separate_and_fail_closed_on_error(self):
        response = self.response()
        analysis = NarrativeReasoningEngine(interpretation_provider=StaticInterpretationProvider(response)).analyse([self.evidence["e1"]], ["e1"])
        self.assertTrue(analysis.claims)
        self.assertEqual(len(analysis.assisted_interpretation.claims), 1)
        self.assertNotEqual(analysis.claims[0].claim_id, analysis.assisted_interpretation.claims[0].claim_id)
        failed = NarrativeReasoningEngine(interpretation_provider=_BrokenProvider()).analyse([self.evidence["e1"]], ["e1"])
        self.assertTrue(failed.claims)
        self.assertIsNone(failed.assisted_interpretation)
        self.assertIn("provider error", failed.interpretation_errors[0])

    def test_provider_receives_only_explicit_interpretation_input(self):
        self.evidence["e1"].metadata["unrelated_private_note"] = "do not send"
        provider = _CaptureProvider(self.response())
        NarrativeReasoningEngine(interpretation_provider=provider).analyse([self.evidence["e1"]], ["e1"])
        payload = provider.request.to_dict()
        self.assertEqual(set(payload), {"request_id", "evidence"})
        self.assertEqual(set(payload["evidence"][0]), {"evidence_id", "text", "source_type", "date", "location", "population", "metadata"})
        self.assertEqual(payload["evidence"][0]["metadata"], {})
        self.assertNotIn("database", str(payload).lower())

    def test_comparison_is_descriptive_without_a_quality_score(self):
        rule = NarrativeReasoningEngine().analyse([self.evidence["e1"]], ["e1"])
        assisted = InterpretationValidator().validate(self.response(), {"e1": self.evidence["e1"]})
        comparison = compare_interpretations(rule, assisted)
        self.assertIn("claims_found_by_both", comparison)
        self.assertNotIn("score", comparison)


if __name__ == "__main__":
    unittest.main()
