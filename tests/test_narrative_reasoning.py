import unittest

from src.evidence import EvidenceItem
from src.innovation_discovery import InnovationDiscoveryEngine
from src.narrative_reasoning import NarrativeReasoningConfig, NarrativeReasoningEngine


class _Retriever:
    def retrieve(self, problem, inspirations=None):
        return []


class TestNarrativeReasoning(unittest.TestCase):
    def setUp(self):
        self.engine = NarrativeReasoningEngine(NarrativeReasoningConfig({
            "knowledge_reuse": ["repository", "material reuse"],
        }))

    def test_claim_extraction_is_deterministic_serializable_and_preserves_context(self):
        evidence = [EvidenceItem("member_feedback", "Members reported that the repository increased material reuse.", "2025-Q1", "North", "member organisations", {"source_identifier": "r1"})]
        first = self.engine.analyse(evidence, ["ev-1"])
        second = self.engine.analyse(evidence, ["ev-1"])
        self.assertEqual(first.to_dict(), second.to_dict())
        claim = first.claims[0]
        self.assertEqual((claim.evidence_id, claim.subject, claim.direction, claim.population, claim.location), ("ev-1", "knowledge_reuse", "increase", "member organisations", "North"))
        self.assertEqual(claim.provenance["source_identifier"], "r1")

    def test_negative_negated_and_no_change_phrases(self):
        analysis = self.engine.analyse([
            EvidenceItem("report", "Use decreased."),
            EvidenceItem("report", "The repository did not improve reuse."),
            EvidenceItem("report", "There was no meaningful change in material reuse."),
        ])
        self.assertEqual(sorted(claim.direction for claim in analysis.claims), ["decrease", "no_change", "no_change"])

    def test_aliases_are_optional_and_do_not_create_facts(self):
        plain = NarrativeReasoningEngine().analyse([EvidenceItem("report", "Engagement increased.")])
        configured = self.engine.analyse([EvidenceItem("report", "Repository use increased.")])
        self.assertEqual(plain.claims[0].direction, "increase")
        self.assertEqual(configured.claims[0].subject, "knowledge_reuse")
        self.assertIn("source statements", plain.extraction_notes[0])

    def test_comparable_opposing_claims_are_conflicts(self):
        analysis = self.engine.analyse([
            EvidenceItem("report", "The repository increased material reuse.", location="North", population="members"),
            EvidenceItem("feedback", "The repository decreased material reuse.", location="North", population="members"),
        ], ["a", "b"])
        self.assertEqual(len(analysis.narrative_conflicts), 1)
        self.assertEqual(analysis.narrative_conflicts[0].conflict_type, "directional_conflict")

    def test_different_context_becomes_dependency_not_conflict(self):
        analysis = self.engine.analyse([
            EvidenceItem("report", "The repository increased material reuse.", location="North", population="members"),
            EvidenceItem("feedback", "The repository showed no meaningful change in material reuse.", location="South", population="new members"),
        ])
        self.assertFalse(analysis.narrative_conflicts)
        self.assertEqual(len(analysis.context_dependencies), 1)
        self.assertEqual(analysis.context_dependencies[0].context_comparison["location"], "different")

    def test_unrelated_opposing_claims_do_not_conflict(self):
        analysis = self.engine.analyse([
            EvidenceItem("report", "Engagement increased."),
            EvidenceItem("report", "Funding decreased."),
        ])
        self.assertFalse(analysis.narrative_conflicts)
        self.assertFalse(analysis.context_dependencies)

    def test_mechanism_candidate_preserves_provenance_without_claiming_success(self):
        analysis = self.engine.analyse([EvidenceItem("report", "Teams introduced a shared knowledge exchange.", location="North", metadata={"source_identifier": "p1"})], ["e-1"])
        self.assertEqual(len(analysis.mechanism_candidates), 1)
        candidate = analysis.mechanism_candidates[0]
        self.assertEqual((candidate.evidence_id, candidate.action, candidate.provenance["source_identifier"]), ("e-1", "introduced", "p1"))
        self.assertIn("not evidence", candidate.limitations[0])

    def test_empty_malformed_and_optional_retriever_handling(self):
        self.assertEqual(NarrativeReasoningEngine().analyse([]).to_dict()["claims"], [])
        with self.assertRaises(TypeError):
            self.engine.analyse([object()])
        with self.assertRaises(ValueError):
            self.engine.analyse([EvidenceItem("", "text")])
        self.assertIn("optional retriever", NarrativeReasoningEngine(retriever=_Retriever()).analyse([]).extraction_notes[-1])
        with self.assertRaises(TypeError):
            NarrativeReasoningEngine(retriever=object())

    def test_discovery_report_adds_narrative_analysis_without_replacing_formal_conflicts(self):
        evidence = [
            EvidenceItem("report", "Access increased.", location="North", population="members"),
            EvidenceItem("feedback", "Access decreased.", location="North", population="members"),
        ]
        report = InnovationDiscoveryEngine().analyse("Investigate access", evidence)
        self.assertTrue(report.evidence_conflicts)
        self.assertIsNotNone(report.narrative_analysis)
        self.assertTrue(report.narrative_analysis.narrative_conflicts)


if __name__ == "__main__":
    unittest.main()
