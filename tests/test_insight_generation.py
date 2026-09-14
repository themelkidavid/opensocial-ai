import unittest
from types import SimpleNamespace

from src.insight_generation import (
    InsightCandidate,
    InsightGenerator,
)
from src.pattern_discovery import ObservedPattern


class TestInsightGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = InsightGenerator()

    def test_pattern_generates_insight(self):
        patterns = [
            ObservedPattern(
                pattern_type="repeated_location",
                description=(
                    "Madurai appears repeatedly across "
                    "the evidence."
                ),
                evidence_count=2,
                confidence="exploratory",
            )
        ]

        insights = self.generator.generate(
            patterns=patterns,
            evidence=["evidence-1", "evidence-2"],
        )

        self.assertEqual(len(insights), 1)

        insight = insights[0]

        self.assertIsInstance(
            insight,
            InsightCandidate,
        )

        self.assertTrue(insight.title)
        self.assertTrue(insight.insight)
        self.assertTrue(insight.evidence_basis)
        self.assertTrue(insight.investigation_question)

    def test_pattern_insight_has_explicit_uncertainty(self):
        patterns = [
            ObservedPattern(
                pattern_type="repeated_population",
                description=(
                    "Young people appear repeatedly "
                    "across the evidence."
                ),
                evidence_count=3,
                confidence="exploratory",
            )
        ]

        insights = self.generator.generate(
            patterns=patterns,
            evidence=["evidence-1", "evidence-2"],
        )

        self.assertEqual(len(insights), 1)

        insight = insights[0]

        self.assertGreater(
            len(insight.uncertainty),
            0,
        )

        uncertainty = " ".join(
            insight.uncertainty
        ).lower()

        self.assertIn(
            "causation",
            uncertainty,
        )

    def test_high_quality_evidence_produces_high_confidence(self):
        patterns = [
            ObservedPattern(
                pattern_type="recurring_term",
                description=(
                    "Peer support appears repeatedly "
                    "across the evidence."
                ),
                evidence_count=3,
                confidence="exploratory",
            )
        ]

        quality = [
            SimpleNamespace(score=90),
            SimpleNamespace(score=85),
        ]

        insights = self.generator.generate(
            patterns=patterns,
            evidence=["evidence-1", "evidence-2"],
            evidence_quality=quality,
        )

        self.assertEqual(
            insights[0].confidence,
            "high",
        )

    def test_moderate_quality_evidence_produces_moderate_confidence(self):
        patterns = [
            ObservedPattern(
                pattern_type="recurring_term",
                description=(
                    "Peer support appears repeatedly "
                    "across the evidence."
                ),
                evidence_count=3,
                confidence="exploratory",
            )
        ]

        quality = [
            SimpleNamespace(score=65),
            SimpleNamespace(score=70),
        ]

        insights = self.generator.generate(
            patterns=patterns,
            evidence=["evidence-1", "evidence-2"],
            evidence_quality=quality,
        )

        self.assertEqual(
            insights[0].confidence,
            "moderate",
        )

    def test_low_quality_evidence_produces_low_confidence(self):
        patterns = [
            ObservedPattern(
                pattern_type="recurring_term",
                description=(
                    "Peer support appears repeatedly "
                    "across the evidence."
                ),
                evidence_count=2,
                confidence="exploratory",
            )
        ]

        quality = [
            SimpleNamespace(score=35),
            SimpleNamespace(score=45),
        ]

        insights = self.generator.generate(
            patterns=patterns,
            evidence=["evidence-1", "evidence-2"],
            evidence_quality=quality,
        )

        self.assertEqual(
            insights[0].confidence,
            "low",
        )

    def test_conflicting_evidence_generates_conflict_insight(self):
        conflicts = [
            SimpleNamespace(
                description=(
                    "Programme data reports increased uptake "
                    "while community feedback reports decreased uptake."
                )
            )
        ]

        insights = self.generator.generate(
            conflicts=conflicts,
            evidence=["evidence-1", "evidence-2"],
        )

        self.assertEqual(len(insights), 1)

        insight = insights[0]

        self.assertEqual(
            insight.title,
            "Investigate the conflicting evidence",
        )

        self.assertEqual(
            insight.confidence,
            "low",
        )

        self.assertTrue(
            insight.evidence_basis
        )

        self.assertTrue(
            insight.investigation_question
        )

        uncertainty = " ".join(
            insight.uncertainty
        ).lower()

        self.assertIn(
            "disagree",
            uncertainty,
        )

    def test_conflict_insight_accounts_for_evidence_gaps(self):
        conflicts = [
            SimpleNamespace(
                description=(
                    "Evidence sources report different "
                    "outcomes."
                )
            )
        ]

        evidence_gaps = [
            "Population information is missing."
        ]

        insights = self.generator.generate(
            conflicts=conflicts,
            evidence_gaps=evidence_gaps,
        )

        self.assertEqual(len(insights), 1)

        uncertainty = " ".join(
            insights[0].uncertainty
        ).lower()

        self.assertIn(
            "evidence gaps",
            uncertainty,
        )

    def test_no_pattern_with_evidence_generates_evidence_review(self):
        evidence = [
            "evidence-1",
            "evidence-2",
        ]

        insights = self.generator.generate(
            evidence=evidence,
        )

        self.assertEqual(len(insights), 1)

        insight = insights[0]

        self.assertEqual(
            insight.title,
            "Strengthen the evidence base",
        )

        self.assertEqual(
            insight.confidence,
            "low",
        )

        self.assertTrue(
            insight.investigation_question
        )

    def test_no_evidence_returns_no_insights(self):
        insights = self.generator.generate()

        self.assertEqual(
            insights,
            [],
        )

    def test_multiple_patterns_generate_multiple_insights(self):
        patterns = [
            ObservedPattern(
                pattern_type="repeated_location",
                description=(
                    "Madurai appears repeatedly."
                ),
                evidence_count=3,
                confidence="exploratory",
            ),
            ObservedPattern(
                pattern_type="repeated_population",
                description=(
                    "Young people appear repeatedly."
                ),
                evidence_count=3,
                confidence="exploratory",
            ),
        ]

        insights = self.generator.generate(
            patterns=patterns,
            evidence=["evidence-1", "evidence-2"],
        )

        self.assertEqual(
            len(insights),
            2,
        )

    def test_insight_can_be_converted_to_dict(self):
        patterns = [
            ObservedPattern(
                pattern_type="repeated_location",
                description=(
                    "Madurai appears repeatedly."
                ),
                evidence_count=2,
                confidence="exploratory",
            )
        ]

        insights = self.generator.generate(
            patterns=patterns,
            evidence=["evidence-1", "evidence-2"],
        )

        result = insights[0].to_dict()

        self.assertIn(
            "title",
            result,
        )

        self.assertIn(
            "insight",
            result,
        )

        self.assertIn(
            "evidence_basis",
            result,
        )

        self.assertIn(
            "confidence",
            result,
        )

        self.assertIn(
            "uncertainty",
            result,
        )

        self.assertIn(
            "investigation_question",
            result,
        )


if __name__ == "__main__":
    unittest.main()