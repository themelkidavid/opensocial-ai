"""Retained narrative promotion boundaries; speculative strategy tests removed."""
from copy import deepcopy
import json
import tempfile
from types import SimpleNamespace
import unittest

from src.evidence import EvidenceItem
from src.innovation_combination import InnovationCombinationEngine
from src.innovation_inspiration import InnovationInspiration, InnovationInspirationEngine, promote_narrative_mechanism
from src.innovation_reasoning import InnovationReasoningEngine
from src.narrative_reasoning import NarrativeReasoningConfig, NarrativeReasoningEngine
from src.persistence import SQLitePersistenceStore
from src.portfolio_learning import ProgrammePortfolio, PortfolioLearningEngine, StrategyDiscoveryEngine
from src.strategic_scenarios import StrategicScenarioEngine
from src.workflow import OpenSocialWorkflow
from examples.pilot_02.run_pilot import run_pilot


class TestNarrativeStrategyIntegration(unittest.TestCase):
    def setUp(self):
        self.config = NarrativeReasoningConfig({"mentoring": ["peer coaching", "mentoring"]})
        self.extractor = NarrativeReasoningEngine(self.config)
        self.evidence = [EvidenceItem("report", "Teams introduced mentoring. Mentoring increased attendance.",
            date="2026-Q1", location="North", population="staff", metadata={"source_identifier": "s1"}),
            EvidenceItem("interview", "Teams introduced mentoring. Peer coaching increased attendance.",
            date="2026-Q1", location="North", population="staff", metadata={"source_identifier": "s2"})]
        self.analysis = self.extractor.analyse(self.evidence, ["e1", "e2"])
        self.portfolio = ProgrammePortfolio("P", "Supplied source statements")

    def promote(self, candidate=None):
        candidate = candidate or self.analysis.mechanism_candidates[0]
        return promote_narrative_mechanism(candidate, approved=True,
            observed_result="The source reported increased attendance.", observed_result_evidence_id=candidate.evidence_id)

    def opportunity(self, kind="transfer_opportunity", basis=None):
        return SimpleNamespace(opportunity_type=kind, description="Investigate mentoring attendance", evidence_basis=basis if basis is not None else ["e1", "e2"], uncertainty=["Source statements need review."])

    def test_adjectival_shared_and_negated_actions_stay_unpromoted(self):
        for text in ("Staff described a shared service centre.", "Teams had not introduced mentoring."):
            candidate = self.extractor.analyse([EvidenceItem("report", text)]).mechanism_candidates[0]
            self.assertIsNone(self.promote(candidate))

    def test_explicit_promotion_preserves_candidate_and_attributed_result(self):
        candidate = self.analysis.mechanism_candidates[0]
        inspiration = self.promote(candidate)
        self.assertIsInstance(inspiration, InnovationInspiration)
        self.assertEqual(inspiration.transferability, "exploratory")
        self.assertEqual(inspiration.narrative_sources[0]["candidate"], candidate.to_dict())
        self.assertEqual(inspiration.narrative_sources[0]["evidence_ids"], [candidate.evidence_id])
        self.assertEqual(inspiration.observed_result, "The source reported increased attendance.")

    def test_missing_result_or_direction_label_is_never_fabricated(self):
        candidate = self.analysis.mechanism_candidates[0]
        for value in (None, "", "unknown", "increase", "no_change"):
            self.assertIsNone(promote_narrative_mechanism(candidate, approved=True, observed_result=value, observed_result_evidence_id=candidate.evidence_id))

    def test_result_requires_matching_evidence_reference(self):
        with self.assertRaisesRegex(ValueError, "source evidence"):
            promote_narrative_mechanism(self.analysis.mechanism_candidates[0], approved=True, observed_result="Reported attendance", observed_result_evidence_id="missing")

    def test_combination_respects_priority_even_when_called_directly(self):
        inspirations = [self.promote(c) for c in self.analysis.mechanism_candidates]
        for kind in ("evidence_gap", "contradiction", "unmet_need"):
            self.assertFalse(InnovationCombinationEngine().combine("mentoring", self.opportunity(kind), inspirations))

    def test_promoted_combination_hypothesis_has_full_lineage(self):
        inspirations = [self.promote(c) for c in self.analysis.mechanism_candidates]
        hypothesis = InnovationReasoningEngine().generate("mentoring attendance", [self.opportunity()], inspirations=inspirations)[0]
        self.assertEqual({s["candidate"]["candidate_id"] for s in hypothesis.narrative_sources}, {c.candidate_id for c in self.analysis.mechanism_candidates})
        self.assertEqual(hypothesis.title[:7], "Combine")

    def test_supplied_provenance_metadata_is_not_overwritten(self):
        supplied = {"source_reference": "archive:1", "metadata": {"programme_id": "documented-programme"}}
        original = deepcopy(supplied)
        analysis = self.extractor.analyse(self.evidence[:1], ["e1"], [supplied])
        for claim in analysis.claims:
            for name, value in original.items():
                self.assertEqual(claim.provenance[name], value)
        self.assertEqual(supplied, original)

    def test_raw_candidate_cannot_enter_combination_even_alone(self):
        for candidates in (self.analysis.mechanism_candidates[:1], self.analysis.mechanism_candidates):
            with self.assertRaises(TypeError):
                InnovationCombinationEngine().combine("mentoring", inspirations=candidates)
            with self.assertRaises(TypeError):
                InnovationReasoningEngine().generate("mentoring", [self.opportunity()], inspirations=candidates)

    def test_promoted_inspiration_enters_reasoning_and_keeps_source_snapshot(self):
        inspiration = self.promote()
        hypothesis = InnovationReasoningEngine().generate("mentoring attendance", [self.opportunity()], inspirations=[inspiration])[0]
        self.assertEqual(hypothesis.narrative_sources, inspiration.narrative_sources)
        self.assertIn(inspiration.provenance_source_id, " ".join(hypothesis.evidence_basis))

    def test_tampered_promoted_record_rejected(self):
        inspiration = self.promote()
        inspiration.observed_result = "Invented result"
        with self.assertRaisesRegex(ValueError, "promotion record"):
            InnovationReasoningEngine().generate("mentoring", [self.opportunity()], inspirations=[inspiration])

    def test_promoted_combination_preserves_each_candidate_and_limits(self):
        inspirations = [self.promote(c) for c in self.analysis.mechanism_candidates]
        combo = InnovationCombinationEngine().combine("mentoring attendance", inspirations=inspirations)[0]
        self.assertEqual({s["candidate"]["candidate_id"] for s in combo.narrative_sources}, {c.candidate_id for c in self.analysis.mechanism_candidates})
        for candidate in self.analysis.mechanism_candidates:
            self.assertTrue(set(candidate.limitations).issubset(combo.uncertainty))

    def test_one_source_cannot_become_two_narrative_combination_sources(self):
        inspiration = self.promote()
        self.assertEqual(InnovationCombinationEngine().combine("mentoring", inspirations=[inspiration, deepcopy(inspiration)]), [])

    def test_evidence_gap_priority_is_unchanged(self):
        self.assert_priority("evidence_gap")

    def test_contradiction_priority_is_unchanged(self):
        self.assert_priority("contradiction")

    def assert_priority(self, kind):
        engine = InnovationReasoningEngine()
        expected = engine.generate("mentoring attendance", [self.opportunity(kind)])[0]
        actual = engine.generate("mentoring attendance", [self.opportunity(kind)], inspirations=[self.promote(c) for c in self.analysis.mechanism_candidates])[0]
        self.assertEqual(actual.to_dict(), expected.to_dict())

    def test_weak_opportunity_cannot_use_promoted_inspiration(self):
        result = InnovationReasoningEngine().generate("mentoring", [self.opportunity(basis=["e1"])], inspirations=[self.promote()])[0]
        self.assertFalse(result.narrative_sources)

    def test_legacy_opportunity_objects_keep_existing_scenario_behavior(self):
        self.assertEqual(StrategicScenarioEngine().generate(opportunities=[self.opportunity()]), [])

    def test_promotion_requires_explicit_boolean_opt_in(self):
        candidate = self.analysis.mechanism_candidates[0]
        for approved in (False, None, "yes", 1):
            self.assertIsNone(promote_narrative_mechanism(candidate, approved=approved,
                observed_result="The source reported attendance.", observed_result_evidence_id=candidate.evidence_id))
        with self.assertRaises(TypeError):
            InnovationInspirationEngine().find_relevant("mentoring", [candidate])

    def test_promotion_and_optional_reasoning_are_deterministic_snapshots(self):
        candidate = self.analysis.mechanism_candidates[0]
        first, second = self.promote(candidate), self.promote(candidate)
        self.assertEqual(first.to_dict(), second.to_dict())
        engine = InnovationReasoningEngine()
        a = engine.generate("mentoring", [self.opportunity()], inspirations=[first])[0]
        b = engine.generate("mentoring", [self.opportunity()], inspirations=[second])[0]
        self.assertEqual(a.to_dict(), b.to_dict())
        snapshot = a.to_dict()
        first.narrative_sources[0]["candidate"]["provenance"]["changed"] = True
        self.assertEqual(a.to_dict(), snapshot)
        self.assertEqual(json.loads(json.dumps(snapshot)), snapshot)

    def test_default_engines_do_not_turn_single_source_into_narrative_strategy(self):
        patterns = PortfolioLearningEngine().analyse(self.portfolio)
        self.assertEqual([p.pattern_type for p in patterns], ["evidence_gap"])
        self.assertTrue(all("narrative_sources" not in o.to_dict() for o in StrategyDiscoveryEngine().discover(patterns)))
        with SQLitePersistenceStore() as store:
            result = OpenSocialWorkflow(store).run("mentoring", self.evidence[:1])
            self.assertEqual(result.scenario_ids, [])
            self.assertEqual(result.strategy_opportunity_ids, [])
            self.assertEqual(result.authorization_ids, [])
            self.assertTrue(all(not h.narrative_sources for h in result.report.innovation_hypotheses))
            self.assertTrue(all("narrative_sources" not in h for h in result.report.to_dict()["innovation_hypotheses"]))

    def test_pilot_preserves_negative_result_and_attributed_filtering(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_pilot(directory)
        review = result["narrative_candidate_review"]
        self.assertEqual([len(result[k]) for k in ("portfolio_patterns", "strategy_opportunities", "scenarios")], [9, 9, 9])
        self.assertEqual(len(review["candidates"]), 5)
        self.assertEqual(sum(not c["action_parse_accepted"] for c in review["candidates"]), 4)
        self.assertTrue(all(not c["promoted"] for c in review["candidates"]))
        candidates = {c["candidate_id"]: c for c in result["narrative_reasoning"]["mechanism_candidates"]}
        for candidate in review["candidates"]:
            source = candidates[candidate["candidate_id"]]
            self.assertEqual(candidate["provenance"], source["provenance"])
            self.assertEqual(candidate["evidence_id"], source["evidence_id"])
        for key in ("new_useful_recombinations", "new_cross_context_adaptations", "new_non_obvious_connections"):
            self.assertEqual(review[key], [])

    def test_retained_reasoning_adds_no_ranking_or_effectiveness_claim(self):
        hypothesis = InnovationReasoningEngine().generate("mentoring", [self.opportunity()], inspirations=[self.promote()])[0]
        self.assertFalse({"rank", "score", "winner", "authorization", "recommendation"} & set(hypothesis.to_dict()))
        for phrase in ("proven effective", "preferred scenario", "source is correct", "predicted success", "automatically authorized"):
            self.assertNotIn(phrase, json.dumps(hypothesis.to_dict()).lower())
        self.assertIn("do not establish effectiveness", " ".join(hypothesis.uncertainty))


if __name__ == "__main__":
    unittest.main()
