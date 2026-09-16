"""
OpenSocial AI – Evidence Ingestion

Provides deterministic JSON and CSV adapters for creating validated
EvidenceItem objects with explicit import provenance. It intentionally
does not perform OCR, web collection, external API calls, or model-based
extraction.
"""

import csv
from dataclasses import dataclass
from io import StringIO
import json
from pathlib import Path
from typing import Dict, List, Optional, Union


try:
    from src.evidence import EvidenceItem, create_evidence
    from src.persistence import EvidenceProvenance
except ModuleNotFoundError:
    from evidence import EvidenceItem, create_evidence
    from persistence import EvidenceProvenance


class EvidenceIngestionError(ValueError):
    """Raised when an input cannot safely become evidence."""


@dataclass
class ImportedEvidence:
    """A validated evidence object together with factual import provenance."""

    evidence: EvidenceItem
    provenance: EvidenceProvenance

    def to_dict(self) -> Dict:
        """Return the imported record as a serializable dictionary."""

        return {
            "evidence": self.evidence.to_dict(),
            "provenance": self.provenance.to_dict(),
        }


class EvidenceIngestionAdapter:
    """Parse supported local formats without inventing missing data."""

    REQUIRED_FIELDS = {"source_type", "content"}

    def from_json(
        self,
        payload: Union[str, bytes],
        source_reference: Optional[str] = None,
    ) -> List[ImportedEvidence]:
        """Parse JSON records from a list or an object with a records list."""

        try:
            parsed = json.loads(payload)
        except (TypeError, json.JSONDecodeError) as error:
            raise EvidenceIngestionError("Invalid JSON evidence input") from error

        if isinstance(parsed, dict):
            if set(parsed) != {"records"} or not isinstance(parsed["records"], list):
                raise EvidenceIngestionError(
                    "JSON evidence must be a list or an object with a records list"
                )
            records = parsed["records"]
        elif isinstance(parsed, list):
            records = parsed
        else:
            raise EvidenceIngestionError(
                "JSON evidence must contain a list of records"
            )

        return self._build_records(
            records,
            import_format="json",
            source_reference=source_reference,
        )

    def from_csv(
        self,
        payload: str,
        source_reference: Optional[str] = None,
    ) -> List[ImportedEvidence]:
        """Parse CSV records with source_type and content columns."""

        if not isinstance(payload, str):
            raise EvidenceIngestionError("CSV evidence input must be text")

        reader = csv.DictReader(StringIO(payload))

        if reader.fieldnames is None:
            raise EvidenceIngestionError("CSV evidence input must include headers")

        headers = set(reader.fieldnames)
        missing = self.REQUIRED_FIELDS - headers
        if missing:
            fields = ", ".join(sorted(missing))
            raise EvidenceIngestionError(
                f"CSV evidence is missing required fields: {fields}"
            )

        records = []
        for line_number, row in enumerate(reader, start=2):
            if None in row:
                raise EvidenceIngestionError(
                    f"CSV evidence row {line_number} has more values than headers"
                )
            records.append(row)

        return self._build_records(
            records,
            import_format="csv",
            source_reference=source_reference,
            csv_metadata=True,
        )

    def from_json_file(
        self,
        path: Union[str, Path],
        source_reference: Optional[str] = None,
    ) -> List[ImportedEvidence]:
        """Read JSON evidence from a UTF-8 file with a non-absolute reference."""

        source_path = Path(path)
        return self.from_json(
            source_path.read_text(encoding="utf-8"),
            source_reference=source_reference or source_path.name,
        )

    def from_csv_file(
        self,
        path: Union[str, Path],
        source_reference: Optional[str] = None,
    ) -> List[ImportedEvidence]:
        """Read CSV evidence from a UTF-8 file with a non-absolute reference."""

        source_path = Path(path)
        return self.from_csv(
            source_path.read_text(encoding="utf-8"),
            source_reference=source_reference or source_path.name,
        )

    def _build_records(
        self,
        records: List,
        import_format: str,
        source_reference: Optional[str],
        csv_metadata: bool = False,
    ) -> List[ImportedEvidence]:
        """Validate all raw records before returning any imported evidence."""

        if source_reference is not None and not isinstance(source_reference, str):
            raise EvidenceIngestionError("source_reference must be text or None")

        imported = []
        for index, record in enumerate(records, start=1):
            imported.append(
                self._build_record(
                    record=record,
                    record_number=index,
                    import_format=import_format,
                    source_reference=source_reference,
                    csv_metadata=csv_metadata,
                )
            )

        return imported

    @staticmethod
    def _build_record(
        record: Dict,
        record_number: int,
        import_format: str,
        source_reference: Optional[str],
        csv_metadata: bool,
    ) -> ImportedEvidence:
        """Convert one validated mapping into existing evidence and provenance."""

        if not isinstance(record, dict):
            raise EvidenceIngestionError(
                f"Evidence record {record_number} must be an object"
            )

        source_type = _required_text(record, "source_type", record_number)
        content = _required_text(record, "content", record_number)
        date = _optional_text(record.get("date"), "date", record_number)
        location = _optional_text(record.get("location"), "location", record_number)
        population = _optional_text(
            record.get("population"),
            "population",
            record_number,
        )
        metadata = _metadata(
            record.get("metadata"),
            record_number,
            csv_metadata,
        )

        record_source_reference = _optional_text(
            record.get("source_reference"),
            "source_reference",
            record_number,
        )
        original_source_id = _optional_text(
            record.get("original_source_id"),
            "original_source_id",
            record_number,
        )

        evidence = create_evidence(
            source_type=source_type,
            content=content,
            date=date,
            location=location,
            population=population,
            metadata=metadata,
        )

        return ImportedEvidence(
            evidence=evidence,
            provenance=EvidenceProvenance(
                entry_method="imported",
                original_source_id=original_source_id,
                source_reference=(record_source_reference or source_reference),
                import_format=import_format,
            ),
        )


def _required_text(record: Dict, field: str, record_number: int) -> str:
    """Return a required non-empty text field or raise a clear import error."""

    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise EvidenceIngestionError(
            f"Evidence record {record_number} requires non-empty {field}"
        )
    return value.strip()


def _optional_text(
    value: object,
    field: str,
    record_number: int,
) -> Optional[str]:
    """Return optional text without turning an unknown value into a value."""

    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise EvidenceIngestionError(
            f"Evidence record {record_number} field {field} must be text or null"
        )
    return value.strip() or None


def _metadata(
    value: object,
    record_number: int,
    csv_metadata: bool,
) -> Dict:
    """Return a metadata mapping, parsing CSV JSON only when supplied."""

    if value is None or value == "":
        return {}

    if csv_metadata and isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            raise EvidenceIngestionError(
                f"Evidence record {record_number} has invalid metadata JSON"
            ) from error

    if not isinstance(value, dict):
        raise EvidenceIngestionError(
            f"Evidence record {record_number} metadata must be an object"
        )

    try:
        json.dumps(value)
    except (TypeError, ValueError) as error:
        raise EvidenceIngestionError(
            f"Evidence record {record_number} metadata is not serializable"
        ) from error

    return value
