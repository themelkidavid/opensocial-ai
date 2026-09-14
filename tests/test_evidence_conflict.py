import unittest

from src.evidence import EvidenceItem, create_evidence
from src.evidence_conflict import EvidenceConflictDetector


class TestEvidenceConflictDetector(unittest.TestCase):

    def setUp(self):
        self.detector = EvidenceConflictDetector()

    def test_conflicting_outcomes_are_detected(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased after peer support.",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Young people reported that service uptake decreased.",
                location="Madurai",
                population="Young people",
            ),
        ]

        conflicts = self.detector.discover(evidence)

        self.assertEqual(len(conflicts), 1)

        conflict = conflicts[0]

        self.assertEqual(conflict.first_index, 0)
        self.assertEqual(conflict.second_index, 1)
        self.assertIn("programme_report", conflict.first_source_type)
        self.assertIn("community_feedback", conflict.second_source_type)

    def test_conflict_description_is_transparent(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service access improved.",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Service access worsened.",
                location="Madurai",
                population="Young people",
            ),
        ]

        conflicts = self.detector.discover(evidence)

        self.assertEqual(len(conflicts), 1)

        conflict = conflicts[0]

        self.assertIn("conflicting", conflict.description.lower())
        self.assertIn("Madurai", conflict.description)
        self.assertIn(
            "timeframe",
            conflict.investigation_question.lower(),
        )

    def test_same_population_can_make_evidence_comparable(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Service uptake decreased.",
                location="Chennai",
                population="Young people",
            ),
        ]

        conflicts = self.detector.discover(evidence)

        self.assertEqual(len(conflicts), 1)

    def test_same_location_can_make_evidence_comparable(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Service uptake decreased.",
                location="Madurai",
                population="Women",
            ),
        ]

        conflicts = self.detector.discover(evidence)

        self.assertEqual(len(conflicts), 1)

    def test_different_contexts_are_not_flagged(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Service uptake decreased.",
                location="Chennai",
                population="Women",
            ),
        ]

        conflicts = self.detector.discover(evidence)

        self.assertEqual(conflicts, [])

    def test_agreeing_evidence_is_not_flagged(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Service uptake improved.",
                location="Madurai",
                population="Young people",
            ),
        ]

        conflicts = self.detector.discover(evidence)

        self.assertEqual(conflicts, [])

    def test_single_evidence_item_has_no_conflict(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                location="Madurai",
                population="Young people",
            )
        ]

        conflicts = self.detector.discover(evidence)

        self.assertEqual(conflicts, [])

    def test_empty_evidence_returns_no_conflicts(self):
        conflicts = self.detector.discover([])

        self.assertEqual(conflicts, [])

    def test_invalid_evidence_type_is_rejected(self):
        with self.assertRaises(TypeError):
            self.detector.discover(["not evidence"])

    def test_empty_source_type_is_rejected(self):
        evidence = [
            EvidenceItem(
                source_type="",
                content="Service uptake increased.",
                location="Madurai",
                population="Young people",
            )
        ]

        with self.assertRaises(ValueError):
            self.detector.discover(evidence)

    def test_empty_content_is_rejected(self):
        evidence = [
            EvidenceItem(
                source_type="programme_report",
                content="",
                location="Madurai",
                population="Young people",
            )
        ]

        with self.assertRaises(ValueError):
            self.detector.discover(evidence)

    def test_conflict_can_be_converted_to_dict(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Service uptake decreased.",
                location="Madurai",
                population="Young people",
            ),
        ]

        conflicts = self.detector.discover(evidence)

        self.assertEqual(len(conflicts), 1)

        result = conflicts[0].to_dict()

        self.assertIn("first_index", result)
        self.assertIn("second_index", result)
        self.assertIn("description", result)
        self.assertIn("investigation_question", result)


if __name__ == "__main__":
    unittest.main()