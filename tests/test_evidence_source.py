import unittest

from src.evidence_source import EvidenceSource, create_source


class TestEvidenceSource(unittest.TestCase):

    def test_create_source(self):
        source = create_source(
            source_type="programme_report",
            name="Annual Programme Report 2025",
            description="Annual report on programme implementation and outcomes.",
            date="2025-12-31",
            organisation="OpenSocial AI",
        )

        self.assertIsInstance(source, EvidenceSource)
        self.assertEqual(source.source_type, "programme_report")
        self.assertEqual(source.name, "Annual Programme Report 2025")
        self.assertEqual(source.date, "2025-12-31")
        self.assertEqual(source.organisation, "OpenSocial AI")

    def test_source_to_dict(self):
        source = create_source(
            source_type="research",
            name="Community Access Study",
            metadata={"method": "survey"},
        )

        result = source.to_dict()

        self.assertEqual(result["source_type"], "research")
        self.assertEqual(result["name"], "Community Access Study")
        self.assertEqual(result["metadata"]["method"], "survey")

    def test_empty_source_type_is_rejected(self):
        with self.assertRaises(ValueError):
            create_source(
                source_type="",
                name="Test Source",
            )

    def test_empty_name_is_rejected(self):
        with self.assertRaises(ValueError):
            create_source(
                source_type="research",
                name="",
            )

    def test_metadata_defaults_to_empty_dictionary(self):
        source = create_source(
            source_type="field_observation",
            name="Field Visit Notes",
        )

        self.assertEqual(source.metadata, {})


if __name__ == "__main__":
    unittest.main()