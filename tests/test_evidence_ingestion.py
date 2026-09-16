import csv
from io import StringIO
import json
import tempfile
import unittest
from pathlib import Path

from src.evidence_ingestion import (
    EvidenceIngestionAdapter,
    EvidenceIngestionError,
    ImportedEvidence,
)


class TestEvidenceIngestionAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = EvidenceIngestionAdapter()

    def test_json_ingestion_creates_existing_evidence_with_provenance(self):
        payload = json.dumps(
            [
                {
                    "source_type": "community_feedback",
                    "content": "Participants reported difficulty reaching services.",
                    "date": "2026-01-15",
                    "location": "Madurai",
                    "population": "Young people",
                    "metadata": {"method": "focus_group"},
                    "original_source_id": "feedback-17",
                }
            ]
        )

        records = self.adapter.from_json(
            payload,
            source_reference="community-feedback.json",
        )

        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], ImportedEvidence)
        self.assertEqual(records[0].evidence.source_type, "community_feedback")
        self.assertEqual(records[0].evidence.metadata["method"], "focus_group")
        self.assertEqual(records[0].provenance.entry_method, "imported")
        self.assertEqual(records[0].provenance.import_format, "json")
        self.assertEqual(records[0].provenance.original_source_id, "feedback-17")
        self.assertEqual(
            records[0].provenance.source_reference,
            "community-feedback.json",
        )

    def test_json_object_with_records_is_supported(self):
        records = self.adapter.from_json(
            json.dumps(
                {
                    "records": [
                        {
                            "source_type": "research",
                            "content": "A study described access barriers.",
                        }
                    ]
                }
            )
        )

        self.assertEqual(records[0].evidence.source_type, "research")
        self.assertIsNone(records[0].provenance.original_source_id)
        self.assertIsNone(records[0].provenance.source_reference)

    def test_csv_ingestion_preserves_metadata_and_original_source_identifier(self):
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "source_type",
                "content",
                "location",
                "metadata",
                "original_source_id",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "source_type": "programme_report",
                "content": "Peer support improved reported access.",
                "location": "Madurai",
                "metadata": json.dumps({"year": "2025"}),
                "original_source_id": "report-row-4",
            }
        )

        records = self.adapter.from_csv(
            output.getvalue(),
            source_reference="programme-export.csv",
        )

        self.assertEqual(records[0].evidence.location, "Madurai")
        self.assertEqual(records[0].evidence.metadata, {"year": "2025"})
        self.assertEqual(records[0].provenance.import_format, "csv")
        self.assertEqual(records[0].provenance.original_source_id, "report-row-4")

    def test_file_adapters_use_filename_not_an_absolute_machine_path(self):
        with tempfile.TemporaryDirectory() as directory:
            json_path = Path(directory) / "evidence.json"
            json_path.write_text(
                json.dumps(
                    [
                        {
                            "source_type": "research",
                            "content": "A local study described access barriers.",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            records = self.adapter.from_json_file(json_path)

        self.assertEqual(records[0].provenance.source_reference, "evidence.json")

    def test_malformed_json_is_rejected_clearly(self):
        with self.assertRaisesRegex(EvidenceIngestionError, "Invalid JSON"):
            self.adapter.from_json("{not valid JSON")

    def test_missing_required_fields_are_rejected_without_partial_import(self):
        payload = json.dumps(
            [
                {
                    "source_type": "research",
                    "content": "A valid first record.",
                },
                {
                    "source_type": "research",
                },
            ]
        )

        with self.assertRaisesRegex(EvidenceIngestionError, "record 2"):
            self.adapter.from_json(payload)

    def test_csv_requires_headers_and_required_columns(self):
        with self.assertRaisesRegex(EvidenceIngestionError, "headers"):
            self.adapter.from_csv("")

        with self.assertRaisesRegex(EvidenceIngestionError, "content"):
            self.adapter.from_csv("source_type\nresearch\n")

    def test_malformed_csv_metadata_and_non_text_fields_are_rejected(self):
        with self.assertRaisesRegex(EvidenceIngestionError, "metadata JSON"):
            self.adapter.from_csv(
                "source_type,content,metadata\n"
                "research,Study findings,{not json}\n"
            )

        with self.assertRaisesRegex(EvidenceIngestionError, "date must be text"):
            self.adapter.from_json(
                json.dumps(
                    [
                        {
                            "source_type": "research",
                            "content": "Study findings.",
                            "date": 20260115,
                        }
                    ]
                )
            )

    def test_empty_json_and_csv_data_return_empty_records(self):
        self.assertEqual(self.adapter.from_json("[]"), [])
        self.assertEqual(
            self.adapter.from_csv("source_type,content\n"),
            [],
        )

    def test_imported_record_serialization_preserves_unknown_provenance(self):
        record = self.adapter.from_json(
            json.dumps(
                [
                    {
                        "source_type": "field_observation",
                        "content": "Access varied by location.",
                    }
                ]
            )
        )[0]

        serialized = record.to_dict()

        self.assertIsNone(serialized["provenance"]["original_source_id"])
        self.assertIsNone(serialized["provenance"]["source_reference"])
        self.assertEqual(serialized["provenance"]["entry_method"], "imported")


if __name__ == "__main__":
    unittest.main()
