import unittest
from types import SimpleNamespace

from src.innovation_opportunity import (
    InnovationOpportunity,
    InnovationOpportunityDetector,
)


class TestInnovationOpportunityDetector(unittest.TestCase):

    def setUp(self):
        self.detector = InnovationOpportunityDetector()

    def test_pattern_creates_emerging_pattern_opportunity(self):
        patterns = [
            SimpleNamespace(
                pattern_type="repeated_location",
                description=(
                    "Madurai appears repeatedly across "
                    "the evidence."
                ),
                evidence_count=3,
                confidence="exploratory",
            )
        ]

        opportunities = self.detector.detect(
            patterns=patterns
        )

        self.assertEqual(
            len(opportunities),
            1,
        )

        opportunity = opportunities[0]

        self.assertIsInstance(
            opportunity,
            InnovationOpportunity,
        )

        self.assertEqual(
            opportunity.opportunity_type,
            "emerging_pattern",
        )

        self.assertTrue(
            opportunity.title
        )

        self.assertTrue(
            opportunity.description
        )

        self.assertTrue(
            opportunity.evidence_basis
        )

    def test_small_pattern_has_low_confidence(self):
        patterns = [
            SimpleNamespace(
                pattern_type="repeated_population",
                description=(
                    "Young people appear repeatedly."
                ),
                evidence_count=2,
                confidence="exploratory",
            )
        ]

        opportunities = self.detector.detect(
            patterns=patterns
        )

        self.assertEqual(
            opportunities[0].confidence,
            "low",
        )

    def test_stronger_pattern_has_moderate_confidence(self):
        patterns = [
            SimpleNamespace(
                pattern_type="recurring_term",
                description=(
                    "Peer support appears repeatedly."
                ),
                evidence_count=3,
                confidence="exploratory",
            )
        ]

        opportunities = self.detector.detect(
            patterns=patterns
        )

        self.assertEqual(
            opportunities[0].confidence,
            "moderate",
        )

    def test_pattern_opportunity_has_uncertainty(self):
        patterns = [
            SimpleNamespace(
                pattern_type="repeated_location",
                description=(
                    "Madurai appears repeatedly."
                ),
                evidence_count=3,
                confidence="exploratory",
            )
        ]

        opportunities = self.detector.detect(
            patterns=patterns
        )

        uncertainty = " ".join(
            opportunities[0].uncertainty
        ).lower()

        self.assertIn(
            "causation",
            uncertainty,
        )

    def test_evidence_gap_creates_opportunity(self):
        gaps = [
            SimpleNamespace(
                description=(
                    "Population information is missing."
                ),
                priority="high",
                investigation_question=(
                    "Which populations are affected?"
                ),
            )
        ]

        opportunities = self.detector.detect(
            evidence_gaps=gaps
        )

        self.assertEqual(
            len(opportunities),
            1,
        )

        opportunity = opportunities[0]

        self.assertEqual(
            opportunity.opportunity_type,
            "evidence_gap",
        )

        self.assertIn(
            "evidence gap",
            opportunity.title.lower(),
        )

        self.assertEqual(
            opportunity.confidence,
            "low",
        )

        self.assertTrue(
            opportunity.investigation_question
        )

    def test_conflict_creates_contradiction_opportunity(self):
        conflicts = [
            SimpleNamespace(
                description=(
                    "Programme data reports increased uptake "
                    "while community feedback reports decreased uptake."
                ),
                investigation_question=(
                    "What explains the different outcomes?"
                ),
            )
        ]

        opportunities = self.detector.detect(
            conflicts=conflicts
        )

        self.assertEqual(
            len(opportunities),
            1,
        )

        opportunity = opportunities[0]

        self.assertEqual(
            opportunity.opportunity_type,
            "contradiction",
        )

        self.assertIn(
            "conflicting",
            opportunity.description.lower(),
        )

        self.assertEqual(
            opportunity.confidence,
            "low",
        )

    def test_conflict_opportunity_has_contextual_uncertainty(self):
        conflicts = [
            SimpleNamespace(
                description=(
                    "Evidence sources report different outcomes."
                )
            )
        ]

        opportunities = self.detector.detect(
            conflicts=conflicts
        )

        uncertainty = " ".join(
            opportunities[0].uncertainty
        ).lower()

        self.assertIn(
            "population",
            uncertainty,
        )

        self.assertIn(
            "measurement",
            uncertainty,
        )

    def test_transfer_opportunity_requires_pattern_and_solution(self):
        patterns = [
            SimpleNamespace(
                pattern_type="repeated_location",
                description=(
                    "Peer support appears repeatedly "
                    "in Madurai."
                ),
                evidence_count=3,
                confidence="exploratory",
            )
        ]

        solutions = [
            SimpleNamespace(
                title="Peer-led support",
            )
        ]

        opportunities = self.detector.detect(
            patterns=patterns,
            solution_hypotheses=solutions,
        )

        self.assertEqual(
            len(opportunities),
            2,
        )

        transfer_opportunities = [
            opportunity
            for opportunity in opportunities
            if opportunity.opportunity_type
            == "transfer_opportunity"
        ]

        self.assertEqual(
            len(transfer_opportunities),
            1,
        )

    def test_transfer_opportunity_not_created_without_solution(self):
        patterns = [
            SimpleNamespace(
                pattern_type="repeated_location",
                description=(
                    "Peer support appears repeatedly."
                ),
                evidence_count=3,
                confidence="exploratory",
            )
        ]

        opportunities = self.detector.detect(
            patterns=patterns
        )

        self.assertEqual(
            len(opportunities),
            1,
        )

        self.assertNotIn(
            "transfer_opportunity",
            [
                opportunity.opportunity_type
                for opportunity in opportunities
            ],
        )

    def test_insight_can_create_fallback_opportunity(self):
        insights = [
            SimpleNamespace(
                title="Strengthen the evidence base",
                insight=(
                    "The current evidence may be insufficient "
                    "to identify a reliable innovation opportunity."
                ),
                confidence="low",
                uncertainty=[
                    "Important evidence gaps remain."
                ],
                investigation_question=(
                    "What additional evidence is needed?"
                ),
            )
        ]

        opportunities = self.detector.detect(
            insights=insights
        )

        self.assertEqual(
            len(opportunities),
            1,
        )

        opportunity = opportunities[0]

        self.assertEqual(
            opportunity.opportunity_type,
            "unmet_need",
        )

        self.assertEqual(
            opportunity.confidence,
            "low",
        )

    def test_structural_opportunities_take_priority_over_insight_fallback(self):
        patterns = [
            SimpleNamespace(
                pattern_type="repeated_location",
                description=(
                    "Madurai appears repeatedly."
                ),
                evidence_count=3,
                confidence="exploratory",
            )
        ]

        insights = [
            SimpleNamespace(
                title="Generated insight",
                insight=(
                    "A possible opportunity has been identified."
                ),
                confidence="moderate",
                uncertainty=[],
                investigation_question=(
                    "What should be tested?"
                ),
            )
        ]

        opportunities = self.detector.detect(
            patterns=patterns,
            insights=insights,
        )

        self.assertEqual(
            len(opportunities),
            1,
        )

        self.assertEqual(
            opportunities[0].opportunity_type,
            "emerging_pattern",
        )

    def test_multiple_patterns_create_multiple_opportunities(self):
        patterns = [
            SimpleNamespace(
                pattern_type="repeated_location",
                description="Madurai appears repeatedly.",
                evidence_count=3,
                confidence="exploratory",
            ),
            SimpleNamespace(
                pattern_type="repeated_population",
                description=(
                    "Young people appear repeatedly."
                ),
                evidence_count=3,
                confidence="exploratory",
            ),
        ]

        opportunities = self.detector.detect(
            patterns=patterns
        )

        self.assertEqual(
            len(opportunities),
            2,
        )

    def test_empty_inputs_return_no_opportunities(self):
        opportunities = self.detector.detect()

        self.assertEqual(
            opportunities,
            [],
        )

    def test_opportunity_can_be_converted_to_dict(self):
        patterns = [
            SimpleNamespace(
                pattern_type="repeated_location",
                description=(
                    "Madurai appears repeatedly."
                ),
                evidence_count=3,
                confidence="exploratory",
            )
        ]

        opportunities = self.detector.detect(
            patterns=patterns
        )

        result = opportunities[0].to_dict()

        self.assertIn(
            "opportunity_type",
            result,
        )

        self.assertIn(
            "title",
            result,
        )

        self.assertIn(
            "description",
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

        self.assertIn(
            "suggested_experiment",
            result,
        )


if __name__ == "__main__":
    unittest.main()