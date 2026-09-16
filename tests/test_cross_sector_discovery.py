import unittest
from types import SimpleNamespace

from src.cross_sector_discovery import CrossSectorDiscoveryEngine
from src.innovation_inspiration import InnovationInspirationEngine
from src.innovation_reasoning import InnovationReasoningEngine
from src.retrieval import EmbeddingProvider, HybridRetriever, SemanticRetriever


class MappingEmbeddingProvider(EmbeddingProvider):
    def embed(self, text):
        if "access support" in text or "Peer navigation" in text:
            return [1.0, 0.0]
        if "Mobile outreach" in text:
            return [0.8, 0.2]
        return [0.0, 0.0]


class TestCrossSectorDiscovery(unittest.TestCase):

    def setUp(self):
        engine = InnovationInspirationEngine()
        self.same_sector = engine.create(
            source_type="research",
            title="Peer navigation",
            context="Health access",
            mechanism="Trusted peers guide people through services.",
            observed_result="Access improved in a bounded study.",
            sector="health",
            geography="Madurai",
            target_population="Young people",
            provenance_source_id="study-1",
            provenance_reference="local-study",
        )
        self.cross_sector = engine.create(
            source_type="community",
            title="Mobile outreach",
            context="Agricultural extension",
            mechanism="Mobile teams bring support closer to people.",
            observed_result="Participation increased locally.",
            sector="agriculture",
            provenance_source_id="community-2",
        )
        self.unknown_sector = engine.create(
            source_type="historical",
            title="Historical peer support",
            context="Archived programme",
            mechanism="Peers guide people through access barriers.",
            observed_result="The record describes participation.",
        )

    def test_metadata_preserves_known_and_unknown_values(self):
        self.assertEqual(self.same_sector.sector, "health")
        self.assertEqual(self.same_sector.geography, "Madurai")
        self.assertEqual(self.same_sector.provenance_source_id, "study-1")
        self.assertIsNone(self.unknown_sector.sector)
        self.assertIsNone(self.unknown_sector.provenance_reference)

    def test_keyword_discovery_returns_same_and_cross_sector_candidates(self):
        candidates = CrossSectorDiscoveryEngine().discover(
            "Young people need peer access support.",
            [self.same_sector, self.cross_sector],
            target_sector="health",
        )

        self.assertEqual(len(candidates), 2)
        self.assertFalse(candidates[0].is_cross_sector)
        self.assertTrue(candidates[1].is_cross_sector)
        self.assertEqual(candidates[1].retrieval_strategy, "keyword")

    def test_cross_sector_preference_is_configurable_and_deterministic(self):
        discovery = CrossSectorDiscoveryEngine()
        baseline = discovery.discover(
            "Young people need peer access support.",
            [self.same_sector, self.cross_sector],
            target_sector="health",
        )
        preferred = discovery.discover(
            "Young people need peer access support.",
            [self.same_sector, self.cross_sector],
            target_sector="health",
            prefer_cross_sector=True,
            cross_sector_boost=10.0,
        )

        self.assertEqual(baseline[0].inspiration.title, "Peer navigation")
        self.assertEqual(preferred[0].inspiration.title, "Mobile outreach")
        self.assertEqual(preferred[0].diversity_boost, 10.0)
        self.assertEqual(len(preferred), 2)

    def test_candidate_preserves_scores_provenance_questions_and_serialization(self):
        candidate = CrossSectorDiscoveryEngine().discover(
            "Young people need peer access support.",
            [self.same_sector],
            target_sector="health",
        )[0]

        self.assertGreater(candidate.retrieval_score, 0)
        self.assertTrue(all(question.endswith("?") for question in candidate.adaptation_questions))
        serialized = candidate.to_dict()
        self.assertEqual(serialized["inspiration"]["provenance_source_id"], "study-1")
        self.assertIn("potential relevance only", candidate.why_it_may_be_relevant)

    def test_unknown_sector_is_not_fabricated_as_cross_sector(self):
        candidate = CrossSectorDiscoveryEngine().discover(
            "People need peer access support.",
            [self.unknown_sector],
            target_sector="health",
        )[0]

        self.assertIsNone(candidate.source_sector)
        self.assertFalse(candidate.is_cross_sector)
        self.assertIn("Unknown sector metadata", " ".join(candidate.uncertainty))

    def test_semantic_and_hybrid_retrievers_are_supported(self):
        semantic = SemanticRetriever(MappingEmbeddingProvider(), minimum_similarity=0.5)
        hybrid = HybridRetriever(semantic)

        semantic_candidate = CrossSectorDiscoveryEngine(semantic).discover(
            "Young people need access support.", [self.same_sector], "health"
        )[0]
        hybrid_candidate = CrossSectorDiscoveryEngine(hybrid).discover(
            "Young people need access support.", [self.same_sector], "health"
        )[0]

        self.assertEqual(semantic_candidate.retrieval_strategy, "semantic")
        self.assertEqual(hybrid_candidate.retrieval_strategy, "hybrid")

    def test_threshold_can_exclude_candidates(self):
        self.assertEqual(
            CrossSectorDiscoveryEngine().discover(
                "Young people need peer access support.",
                [self.same_sector],
                minimum_score=99.0,
            ),
            [],
        )

    def test_reasoning_uses_candidates_without_bypassing_safeguards(self):
        candidates = CrossSectorDiscoveryEngine().discover(
            "Young people need peer access support.",
            [self.same_sector, self.cross_sector],
            target_sector="health",
        )
        reasoning = InnovationReasoningEngine()
        gap = SimpleNamespace(
            opportunity_type="evidence_gap",
            description="More evidence is required.",
            evidence_basis=["One source"],
            confidence="low",
            uncertainty=["Evidence is incomplete."],
        )
        transfer = SimpleNamespace(
            opportunity_type="transfer_opportunity",
            description="A pattern supports cautious adaptation.",
            evidence_basis=["Pattern", "Community feedback"],
            confidence="exploratory",
            uncertainty=["Conditions may differ."],
        )

        hypotheses = reasoning.generate(
            "Young people need peer access support.",
            [gap, transfer],
            cross_sector_candidates=candidates,
        )

        self.assertFalse(hypotheses[0].title.startswith("Combine"))
        self.assertTrue(hypotheses[1].title.startswith("Combine"))
        self.assertIn("source sector", hypotheses[1].inspiration_source)

    def test_combination_preserves_source_sector_and_provenance(self):
        candidates = CrossSectorDiscoveryEngine().discover(
            "Young people need peer access support.",
            [self.same_sector, self.cross_sector],
            target_sector="health",
        )
        transfer = SimpleNamespace(
            opportunity_type="transfer_opportunity",
            description="A pattern supports cautious adaptation.",
            evidence_basis=["Pattern", "Community feedback"],
            confidence="exploratory",
            uncertainty=["Conditions may differ."],
        )
        hypothesis = InnovationReasoningEngine().generate(
            "Young people need peer access support.",
            [transfer],
            cross_sector_candidates=candidates,
        )[0]

        self.assertIn("Peer navigation", hypothesis.underlying_mechanism)
        self.assertIn("Mobile outreach", hypothesis.underlying_mechanism)
        self.assertIn("combined inspirations", hypothesis.inspiration_source)


if __name__ == "__main__":
    unittest.main()
