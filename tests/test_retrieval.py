import unittest
from types import SimpleNamespace

from src.innovation_inspiration import (
    InnovationInspiration,
    InnovationInspirationEngine,
)
from src.innovation_reasoning import InnovationReasoningEngine
from src.retrieval import KeywordRetriever, RelevanceRetriever


class RecordingRetriever(RelevanceRetriever):
    """Simple deterministic test retriever for dependency injection."""

    def __init__(self):
        self.calls = []

    def retrieve(self, problem, inspirations=None):
        self.calls.append((problem, list(inspirations or [])))
        return list(inspirations or [])[:1]


class FabricatingRetriever(RelevanceRetriever):
    """An unsafe retriever used to verify corpus-boundary enforcement."""

    def retrieve(self, problem, inspirations=None):
        return [
            InnovationInspiration(
                source_type="research",
                title="Fabricated inspiration",
                context="Unknown",
                mechanism="Unverified mechanism",
                observed_result="Unverified result",
                transferability="high",
                adaptation_notes="",
            )
        ]


class DuplicatingRetriever(RelevanceRetriever):
    """A retriever that repeats one valid source."""

    def retrieve(self, problem, inspirations=None):
        return [inspirations[0], inspirations[0]]


class TestRetrievalAbstraction(unittest.TestCase):

    def setUp(self):
        self.inspiration_engine = InnovationInspirationEngine()

    def _inspirations(self):
        return [
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

    def test_default_engine_uses_keyword_retriever(self):
        self.assertIsInstance(
            self.inspiration_engine.retriever,
            KeywordRetriever,
        )

    def test_keyword_retriever_preserves_transparent_relevance_ranking(self):
        inspirations = self._inspirations()

        relevant = self.inspiration_engine.find_relevant(
            "Young people need peer support to access services.",
            inspirations,
        )

        self.assertEqual(relevant[0].title, "Peer navigation")
        self.assertEqual(
            [item.title for item in relevant],
            ["Peer navigation", "Mobile outreach"],
        )

    def test_keyword_retrieval_returns_empty_for_no_matches_or_empty_corpus(self):
        inspirations = self._inspirations()

        self.assertEqual(
            KeywordRetriever().retrieve("Housing affordability", inspirations),
            [],
        )
        self.assertEqual(
            self.inspiration_engine.find_relevant("Service access", []),
            [],
        )

    def test_custom_retriever_is_used_without_rewriting_reasoning(self):
        retriever = RecordingRetriever()
        reasoning = InnovationReasoningEngine(retriever=retriever)
        inspirations = self._inspirations()
        opportunity = SimpleNamespace(
            opportunity_type="transfer_opportunity",
            description="A local pattern suggests an adaptation may help.",
            evidence_basis=["Pattern evidence", "Solution hypothesis"],
            confidence="exploratory",
            uncertainty=["Local conditions may differ."],
        )

        hypotheses = reasoning.generate(
            "Young people need service access support.",
            [opportunity],
            inspirations,
        )

        self.assertEqual(len(retriever.calls), 1)
        self.assertEqual(
            retriever.calls[0][0],
            "Young people need service access support.",
        )
        self.assertEqual(hypotheses[0].inspiration_source, "community inspiration: Peer navigation")

    def test_invalid_retriever_is_rejected(self):
        with self.assertRaises(TypeError):
            InnovationInspirationEngine(retriever=object())

    def test_retriever_cannot_return_a_fabricated_inspiration(self):
        engine = InnovationInspirationEngine(retriever=FabricatingRetriever())

        with self.assertRaisesRegex(ValueError, "supplied inspiration corpus"):
            engine.find_relevant(
                "Young people need service access support.",
                self._inspirations(),
            )

    def test_retriever_cannot_turn_one_source_into_a_combination(self):
        inspiration = self._inspirations()[0]
        reasoning = InnovationReasoningEngine(
            retriever=DuplicatingRetriever()
        )
        opportunity = SimpleNamespace(
            opportunity_type="transfer_opportunity",
            description="A local pattern suggests an adaptation may help.",
            evidence_basis=["Pattern evidence", "Community feedback"],
            confidence="exploratory",
            uncertainty=["Local conditions may differ."],
        )

        hypothesis = reasoning.generate(
            "Young people need service access support.",
            [opportunity],
            [inspiration],
        )[0]

        self.assertFalse(hypothesis.title.startswith("Combine"))
        self.assertNotIn("combined inspirations", hypothesis.inspiration_source)


if __name__ == "__main__":
    unittest.main()
