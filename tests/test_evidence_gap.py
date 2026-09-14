import unittest

from src.evidence import create_evidence
from src.evidence_gap import EvidenceGap, EvidenceGapAnalysis


class TestEvidenceGapAnalysis(unittest.TestCase):

    def setUp(self):
        self.analysis = EvidenceGapAnalysis()

    def test_no_evidence_creates_high_priority_gap(self):
        gaps = self.analysis.discover([])

        self.assertEqual(len(gaps), 1)
        self.assertIsInstance(gaps[0], EvidenceGap)
        self.assertEqual(gaps[0].gap_type, "missing_evidence")
        self.assertEqual(gaps[0].priority, "high")

    def test_complete_evidence_has_no_basic_gaps(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased after peer support.",
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Participants reported improved engagement.",
                date="2025-09-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        gaps = self.analysis.discover(evidence)

        self.assertEqual(gaps, [])

    def test_missing_location_is_detected(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                date="2025-06-30",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Participants reported improved access.",
                date="2025-09-15",
                population="Young people",
            ),
        ]

        gaps = self.analysis.discover(evidence)

        gap_types = {gap.gap_type for gap in gaps}

        self.assertIn("location", gap_types)

    def test_missing_population_is_detected(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                date="2025-06-30",
                location="Madurai",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Participants reported improved access.",
                date="2025-09-15",
                location="Madurai",
            ),
        ]

        gaps = self.analysis.discover(evidence)

        gap_types = {gap.gap_type for gap in gaps}

        self.assertIn("population", gap_types)

    def test_missing_dates_are_detected(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Participants reported improved access.",
                location="Madurai",
                population="Young people",
            ),
        ]

        gaps = self.analysis.discover(evidence)

        gap_types = {gap.gap_type for gap in gaps}

        self.assertIn("time", gap_types)

    def test_single_source_type_creates_source_diversity_gap(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="programme_report",
                content="Service engagement improved.",
                date="2025-09-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        gaps = self.analysis.discover(evidence)

        gap_types = {gap.gap_type for gap in gaps}

        self.assertIn("source_diversity", gap_types)

    def test_single_evidence_item_creates_comparison_gap(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            )
        ]

        gaps = self.analysis.discover(evidence)

        gap_types = {gap.gap_type for gap in gaps}

        self.assertIn("comparison", gap_types)

    def test_missing_outcome_signal_is_detected(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Participants described the service.",
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Participants discussed their experience.",
                date="2025-09-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        gaps = self.analysis.discover(evidence)

        gap_types = {gap.gap_type for gap in gaps}

        self.assertIn("outcome", gap_types)

    def test_gap_contains_investigation_question(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service access is difficult.",
            )
        ]

        gaps = self.analysis.discover(evidence)

        for gap in gaps:
            self.assertTrue(gap.description)
            self.assertTrue(gap.investigation_question)
            self.assertTrue(gap.priority)

    def test_gap_can_be_converted_to_dict(self):
        gaps = self.analysis.discover([])

        result = gaps[0].to_dict()

        self.assertIn("gap_type", result)
        self.assertIn("description", result)
        self.assertIn("investigation_question", result)
        self.assertIn("priority", result)


if __name__ == "__main__":
    unittest.main()