import unittest

from src.innovation_inspiration import InnovationInspirationEngine
from src.innovation_reasoning import InnovationReasoningEngine
from src.retrieval import (
    DeterministicTestEmbeddingProvider,
    EmbeddingProvider,
    HybridRetriever,
    KeywordRetriever,
    SemanticRetriever,
)


class MappingEmbeddingProvider(EmbeddingProvider):
    """Deterministic test double with deliberately specified vectors."""

    def __init__(self, vectors):
        self.vectors = vectors

    def embed(self, text):
        for marker, vector in self.vectors.items():
            if marker in text:
                return vector
        return [0.0, 0.0]


class InvalidEmbeddingProvider(EmbeddingProvider):
    """Test double that returns an invalid embedding result."""

    def embed(self, text):
        return "not a vector"


class TestSemanticRetriever(unittest.TestCase):

    def setUp(self):
        self.inspiration_engine = InnovationInspirationEngine()
        self.inspirations = [
            self.inspiration_engine.create(
                source_type="community",
                title="Peer navigation",
                context="Community services",
                mechanism="Trusted peers guide people through services.",
                observed_result="Service access improved.",
                transferability="moderate",
            ),
            self.inspiration_engine.create(
                source_type="research",
                title="Mobile outreach",
                context="Health access",
                mechanism="Mobile teams bring services closer to people.",
                observed_result="Outreach increased participation.",
                transferability="high",
            ),
        ]

    @staticmethod
    def _provider():
        return MappingEmbeddingProvider(
            {
                "access support": [1.0, 0.0],
                "Peer navigation": [0.9, 0.1],
                "Mobile outreach": [0.2, 0.8],
            }
        )

    def test_deterministic_test_provider_is_local_and_repeatable(self):
        provider = DeterministicTestEmbeddingProvider(dimensions=8)

        self.assertEqual(
            provider.embed("Peer support improves access."),
            provider.embed("Peer support improves access."),
        )
        self.assertEqual(len(provider.embed("Peer support improves access.")), 8)

    def test_semantic_similarity_ranks_and_serializes_candidate_metadata(self):
        retriever = SemanticRetriever(self._provider(), minimum_similarity=-1.0)

        matches = retriever.retrieve_matches(
            "Young people need access support.",
            self.inspirations,
        )

        self.assertEqual(
            [match.inspiration.title for match in matches],
            ["Peer navigation", "Mobile outreach"],
        )
        self.assertEqual(matches[0].strategy, "semantic")
        self.assertGreater(matches[0].semantic_similarity, 0.9)
        serialized = matches[0].to_dict()
        self.assertEqual(serialized["source_type"], "community")
        self.assertEqual(serialized["context"], "Community services")
        self.assertEqual(serialized["inspiration"]["title"], "Peer navigation")

    def test_semantic_threshold_and_empty_candidates_return_no_matches(self):
        retriever = SemanticRetriever(self._provider(), minimum_similarity=0.999)

        self.assertEqual(
            retriever.retrieve("Young people need access support.", self.inspirations),
            [],
        )
        self.assertEqual(retriever.retrieve("Any problem", []), [])

    def test_zero_vectors_do_not_produce_semantic_matches(self):
        retriever = SemanticRetriever(
            MappingEmbeddingProvider({"access support": [0.0, 0.0]}),
        )

        self.assertEqual(
            retriever.retrieve("Young people need access support.", self.inspirations),
            [],
        )

    def test_incompatible_embedding_dimensions_are_rejected(self):
        retriever = SemanticRetriever(
            MappingEmbeddingProvider(
                {
                    "access support": [1.0, 0.0],
                    "Peer navigation": [1.0, 0.0, 0.0],
                }
            )
        )

        with self.assertRaisesRegex(ValueError, "dimensions"):
            retriever.retrieve("Young people need access support.", self.inspirations)

    def test_invalid_provider_output_is_rejected(self):
        retriever = SemanticRetriever(InvalidEmbeddingProvider())

        with self.assertRaisesRegex(TypeError, "sequence of numbers"):
            retriever.retrieve("Young people need access support.", self.inspirations)

    def test_semantic_ties_preserve_candidate_input_order(self):
        retriever = SemanticRetriever(
            MappingEmbeddingProvider(
                {
                    "access support": [1.0, 0.0],
                    "Peer navigation": [1.0, 0.0],
                    "Mobile outreach": [1.0, 0.0],
                }
            ),
            minimum_similarity=0.5,
        )

        self.assertEqual(
            [
                inspiration.title
                for inspiration in retriever.retrieve(
                    "Young people need access support.",
                    self.inspirations,
                )
            ],
            ["Peer navigation", "Mobile outreach"],
        )

    def test_semantic_retriever_can_be_injected_into_reasoning(self):
        inspiration_engine = InnovationInspirationEngine(
            retriever=SemanticRetriever(self._provider(), minimum_similarity=0.5)
        )
        reasoning = InnovationReasoningEngine(
            retriever=SemanticRetriever(self._provider(), minimum_similarity=0.5)
        )
        opportunity = type(
            "Opportunity",
            (),
            {
                "opportunity_type": "transfer_opportunity",
                "description": "A local pattern suggests adaptation may help.",
                "evidence_basis": ["Pattern evidence", "Community feedback"],
                "confidence": "exploratory",
                "uncertainty": ["Local conditions may differ."],
            },
        )()

        matches = inspiration_engine.find_relevant_matches(
            "Young people need access support.",
            self.inspirations,
        )
        hypotheses = reasoning.generate(
            "Young people need access support.",
            [opportunity],
            self.inspirations,
        )

        self.assertEqual(matches[0].strategy, "semantic")
        self.assertIn("Peer navigation", hypotheses[0].inspiration_source)

    def test_semantic_retrieval_does_not_override_evidence_gap_or_contradiction(self):
        reasoning = InnovationReasoningEngine(
            retriever=SemanticRetriever(self._provider(), minimum_similarity=0.0)
        )
        common = {
            "description": "More contextual investigation is required.",
            "evidence_basis": ["Pattern evidence", "Community feedback"],
            "confidence": "exploratory",
            "uncertainty": ["Local conditions may differ."],
        }
        evidence_gap = type(
            "Opportunity",
            (),
            {"opportunity_type": "evidence_gap", **common},
        )()
        contradiction = type(
            "Opportunity",
            (),
            {"opportunity_type": "contradiction", **common},
        )()

        hypotheses = reasoning.generate(
            "Young people need access support.",
            [evidence_gap, contradiction],
            self.inspirations,
        )

        self.assertEqual(len(hypotheses), 2)
        self.assertTrue(all(not item.title.startswith("Combine") for item in hypotheses))
        self.assertIn("evidence", hypotheses[0].underlying_mechanism.lower())
        self.assertTrue(
            "context" in hypotheses[1].underlying_mechanism.lower()
            or "different" in hypotheses[1].why_it_might_work.lower()
        )

    def test_semantic_matches_can_still_create_a_safe_combination(self):
        provider = MappingEmbeddingProvider(
            {
                "access support": [1.0, 0.0],
                "Peer navigation": [1.0, 0.0],
                "Mobile outreach": [1.0, 0.0],
            }
        )
        reasoning = InnovationReasoningEngine(
            retriever=SemanticRetriever(provider, minimum_similarity=0.5)
        )
        opportunity = type(
            "Opportunity",
            (),
            {
                "opportunity_type": "transfer_opportunity",
                "description": "A local pattern supports cautious adaptation.",
                "evidence_basis": ["Pattern evidence", "Community feedback"],
                "confidence": "exploratory",
                "uncertainty": ["Local conditions may differ."],
            },
        )()

        hypothesis = reasoning.generate(
            "Young people need access support.",
            [opportunity],
            self.inspirations,
        )[0]

        self.assertTrue(hypothesis.title.startswith("Combine"))
        self.assertIn("combined inspirations", hypothesis.inspiration_source)


class TestHybridRetriever(unittest.TestCase):

    def setUp(self):
        engine = InnovationInspirationEngine()
        self.inspirations = [
            engine.create(
                source_type="community",
                title="Peer navigation",
                context="Community services",
                mechanism="Trusted peers guide people through services.",
                observed_result="Service access improved.",
            ),
            engine.create(
                source_type="research",
                title="Mobile outreach",
                context="Health access",
                mechanism="Mobile teams bring services closer to people.",
                observed_result="Outreach increased participation.",
            ),
        ]
        self.semantic = SemanticRetriever(
            MappingEmbeddingProvider(
                {
                    "semantic target": [1.0, 0.0],
                    "Peer navigation": [0.2, 0.8],
                    "Mobile outreach": [1.0, 0.0],
                }
            ),
            minimum_similarity=0.5,
        )

    def test_hybrid_supports_keyword_only_and_semantic_only_matches(self):
        retriever = HybridRetriever(self.semantic)

        matches = retriever.retrieve_matches(
            "Young people need peer semantic target.",
            self.inspirations,
        )

        by_title = {match.inspiration.title: match for match in matches}
        self.assertGreater(by_title["Peer navigation"].keyword_score, 0)
        self.assertEqual(by_title["Peer navigation"].semantic_similarity, 0.0)
        self.assertEqual(by_title["Mobile outreach"].keyword_score, 0.0)
        self.assertGreater(by_title["Mobile outreach"].semantic_similarity, 0.9)

    def test_hybrid_uses_weights_for_ranking(self):
        retriever = HybridRetriever(
            self.semantic,
            keyword_retriever=KeywordRetriever(),
            keyword_weight=0.0,
            semantic_weight=1.0,
        )

        self.assertEqual(
            retriever.retrieve(
                "Young people need peer semantic target.",
                self.inspirations,
            )[0].title,
            "Mobile outreach",
        )

    def test_hybrid_ties_preserve_candidate_input_order(self):
        tied_semantic = SemanticRetriever(
            MappingEmbeddingProvider(
                {
                    "semantic target": [1.0, 0.0],
                    "Peer navigation": [1.0, 0.0],
                    "Mobile outreach": [1.0, 0.0],
                }
            ),
            minimum_similarity=0.5,
        )
        retriever = HybridRetriever(
            tied_semantic,
            keyword_weight=0.0,
            semantic_weight=1.0,
        )

        self.assertEqual(
            [
                inspiration.title
                for inspiration in retriever.retrieve(
                    "Young people need semantic target.",
                    self.inspirations,
                )
            ],
            ["Peer navigation", "Mobile outreach"],
        )


if __name__ == "__main__":
    unittest.main()
