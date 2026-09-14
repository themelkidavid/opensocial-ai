import unittest

from src.evidence import create_evidence
from src.evidence_quality import EvidenceQualityAssessor


class TestEvidenceQualityAssessor(unittest.TestCase):

    def setUp(self):
        self.assessor = EvidenceQualityAssessor()

    def test_complete_evidence_gets_moderate_quality(self):
        evidence = create_evidence(
            source_type="community_feedback",
            content="Young people reported improved access to services.",
            date="2025-09-15",
            location="Madurai",
            population="Young people",
        )

        quality = self.assessor.assess(evidence)

        self.assertEqual(quality.score, 70)
        self.assertEqual(quality.confidence, "moderate")

    def test_detailed_corroborated_evidence_gets_high_quality(self):
        evidence = create_evidence(
            source_type="community_feedback",
            content=(
                "Young people reported substantially improved access to "
                "services after peer support was introduced. Participants "
                "described improved trust, easier communication, and greater "
                "willingness to use the service."
            ),
            date="2025-09-15",
            location="Madurai",
            population="Young people",
        )

        corroborating_evidence = create_evidence(
            source_type="programme_report",
            content=(
                "Programme records show increased service uptake after "
                "peer support was introduced."
            ),
            date="2025-09-30",
            location="Madurai",
            population="Young people",
        )

        quality = self.assessor.assess(
            evidence,
            all_evidence=[
                evidence,
                corroborating_evidence,
            ],
        )

        self.assertEqual(quality.score, 100)
        self.assertEqual(quality.confidence, "high")
        self.assertIn(
            "corroborated",
            " ".join(quality.strengths).lower(),
        )

    def test_missing_metadata_reduces_quality(self):
        evidence = create_evidence(
            source_type="community_feedback",
            content="Service access remains inconsistent.",
        )

        quality = self.assessor.assess(evidence)

        self.assertEqual(quality.score, 30)
        self.assertEqual(quality.confidence, "low")

        limitations = " ".join(quality.limitations).lower()

        self.assertIn("date", limitations)
        self.assertIn("location", limitations)
        self.assertIn("population", limitations)

    def test_brief_evidence_is_flagged(self):
        evidence = create_evidence(
            source_type="programme_report",
            content="Improved.",
            date="2025-01-01",
            location="Chennai",
            population="Women",
        )

        quality = self.assessor.assess(evidence)

        self.assertIn(
            "brief",
            " ".join(quality.limitations).lower(),
        )

    def test_corroboration_requires_different_source_type(self):
        evidence = create_evidence(
            source_type="community_feedback",
            content=(
                "Young people reported improved access to services "
                "after peer support."
            ),
            location="Madurai",
            population="Young people",
        )

        same_source = create_evidence(
            source_type="community_feedback",
            content=(
                "Young people reported better engagement with services."
            ),
            location="Madurai",
            population="Young people",
        )

        quality = self.assessor.assess(
            evidence,
            all_evidence=[evidence, same_source],
        )

        self.assertNotIn(
            "corroborated",
            " ".join(quality.strengths).lower(),
        )

    def test_different_source_same_population_can_corroborate(self):
        evidence = create_evidence(
            source_type="community_feedback",
            content=(
                "Young people reported improved access to services "
                "after peer support."
            ),
            location="Madurai",
            population="Young people",
        )

        second_source = create_evidence(
            source_type="programme_report",
            content=(
                "Programme records indicate increased service uptake."
            ),
            location="Chennai",
            population="Young people",
        )

        quality = self.assessor.assess(
            evidence,
            all_evidence=[evidence, second_source],
        )

        self.assertIn(
            "corroborated",
            " ".join(quality.strengths).lower(),
        )

    def test_invalid_evidence_type_is_rejected(self):
        with self.assertRaises(TypeError):
            self.assessor.assess("not evidence")

    def test_empty_source_type_is_rejected(self):
        evidence = create_evidence(
            source_type="",
            content="Service access remains inconsistent.",
        )

        with self.assertRaises(ValueError):
            self.assessor.assess(evidence)

    def test_empty_content_is_rejected(self):
        evidence = create_evidence(
            source_type="community_feedback",
            content="",
        )

        with self.assertRaises(ValueError):
            self.assessor.assess(evidence)

    def test_quality_can_be_converted_to_dict(self):
        evidence = create_evidence(
            source_type="programme_report",
            content="Service uptake increased.",
            date="2025-06-30",
            location="Madurai",
            population="Young people",
        )

        quality = self.assessor.assess(evidence)

        result = quality.to_dict()

        self.assertIn("score", result)
        self.assertIn("confidence", result)
        self.assertIn("strengths", result)
        self.assertIn("limitations", result)


if __name__ == "__main__":
    unittest.main()