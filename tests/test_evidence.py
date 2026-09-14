import unittest

from src.evidence import EvidenceItem, create_evidence


class TestEvidenceItem(unittest.TestCase):

    def test_create_evidence(self):
        evidence = create_evidence(
            source_type="programme_report",
            content="Service uptake increased by 18% after peer support was introduced.",
            date="2026-01-15",
            location="Tamil Nadu",
            population="Young people",
        )

        self.assertIsInstance(evidence, EvidenceItem)
        self.assertEqual(evidence.source_type, "programme_report")
        self.assertEqual(
            evidence.content,
            "Service uptake increased by 18% after peer support was introduced.",
        )
        self.assertEqual(evidence.date, "2026-01-15")
        self.assertEqual(evidence.location, "Tamil Nadu")
        self.assertEqual(evidence.population, "Young people")

    def test_evidence_to_dict(self):
        evidence = create_evidence(
            source_type="community_feedback",
            content="Participants reported difficulty accessing services.",
            metadata={"method": "focus_group"},
        )

        result = evidence.to_dict()

        self.assertEqual(result["source_type"], "community_feedback")
        self.assertEqual(
            result["content"],
            "Participants reported difficulty accessing services.",
        )
        self.assertEqual(result["metadata"]["method"], "focus_group")

    def test_empty_source_type_is_rejected(self):
        with self.assertRaises(ValueError):
            create_evidence(
                source_type="",
                content="Some evidence",
            )

    def test_empty_content_is_rejected(self):
        with self.assertRaises(ValueError):
            create_evidence(
                source_type="research",
                content="",
            )

    def test_metadata_defaults_to_empty_dictionary(self):
        evidence = create_evidence(
            source_type="field_observation",
            content="Service access varies between locations.",
        )

        self.assertEqual(evidence.metadata, {})


if __name__ == "__main__":
    unittest.main()