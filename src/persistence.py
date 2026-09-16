"""
OpenSocial AI – Persistence and Audit

Provides a small, optional SQLite-backed storage boundary for evidence,
experiments, reviewer-attributed observations, and exploratory learning. The domain
engines remain independent of SQLite: callers can continue to use the
in-memory workflow or supply a PersistenceStore implementation.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Union
import uuid


try:
    from src.evidence import EvidenceItem, create_evidence
    from src.experiment_design import ExperimentDesign
    from src.validation_learning import (
        ValidatedLearning,
        ValidationLearningEngine,
        ValidationObservation,
    )
    from src.historical_memory import HistoricalProgramme, MechanismRecord
    from src.outcome_metrics import ComparativeLearningEngine, OutcomeMetric, OutcomeObservation
except ModuleNotFoundError:
    from evidence import EvidenceItem, create_evidence
    from experiment_design import ExperimentDesign
    from validation_learning import (
        ValidatedLearning,
        ValidationLearningEngine,
        ValidationObservation,
    )
    from historical_memory import HistoricalProgramme, MechanismRecord
    from outcome_metrics import ComparativeLearningEngine, OutcomeMetric, OutcomeObservation


@dataclass
class EvidenceProvenance:
    """Known provenance for an evidence record; unknown values stay None."""

    entry_method: str = "manual"
    original_source_id: Optional[str] = None
    source_reference: Optional[str] = None
    import_format: Optional[str] = None

    def to_dict(self) -> Dict:
        """Return the provenance as a serializable dictionary."""

        return {
            "entry_method": self.entry_method,
            "original_source_id": self.original_source_id,
            "source_reference": self.source_reference,
            "import_format": self.import_format,
        }


@dataclass
class StoredEvidence:
    """An evidence item together with its persistent identity and provenance."""

    evidence_id: str
    evidence: EvidenceItem
    provenance: EvidenceProvenance
    created_at: str

    def to_dict(self) -> Dict:
        """Return the stored evidence as a serializable dictionary."""

        return {
            "evidence_id": self.evidence_id,
            "evidence": self.evidence.to_dict(),
            "provenance": self.provenance.to_dict(),
            "created_at": self.created_at,
        }


@dataclass
class StoredExperiment:
    """An experiment design together with its persistence timestamp."""

    experiment: ExperimentDesign
    created_at: str

    @property
    def experiment_id(self) -> str:
        """Return the stable experiment identifier."""

        return self.experiment.experiment_id

    def to_dict(self) -> Dict:
        """Return the stored experiment as a serializable dictionary."""

        result = self.experiment.to_dict()
        result["created_at"] = self.created_at
        return result


@dataclass
class StoredObservation:
    """A reviewer-attributed observation with its persistent identity."""

    observation_id: str
    observation: ValidationObservation
    created_at: str

    def to_dict(self) -> Dict:
        """Return the stored observation as a serializable dictionary."""

        return {
            "observation_id": self.observation_id,
            "observation": self.observation.to_dict(),
            "created_at": self.created_at,
        }


@dataclass
class StoredLearning:
    """Exploratory learning linked to the observation that produced it."""

    learning_id: str
    observation_id: str
    learning: ValidatedLearning
    created_at: str

    def to_dict(self) -> Dict:
        """Return the stored learning as a serializable dictionary."""

        return {
            "learning_id": self.learning_id,
            "observation_id": self.observation_id,
            "learning": self.learning.to_dict(),
            "created_at": self.created_at,
        }


@dataclass
class AuditEvent:
    """A factual record of a state transition; never an approval decision."""

    event_id: str
    event_type: str
    entity_type: str
    entity_id: str
    timestamp: str
    description: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict:
        """Return the event as a serializable dictionary."""

        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp,
            "description": self.description,
            "metadata": self.metadata,
        }


class PersistenceStore:
    """Storage interface used by orchestration without a SQLite dependency."""

    def save_evidence(
        self,
        evidence: EvidenceItem,
        provenance: Optional[EvidenceProvenance] = None,
    ) -> StoredEvidence:
        """Persist one validated evidence item."""

        raise NotImplementedError

    @contextmanager
    def transaction(self):
        """Group related storage operations when an implementation supports it.

        The base interface deliberately provides a no-op transaction so custom
        in-memory stores remain compatible. SQLite overrides it to make a
        discovery run atomic.
        """

        yield self

    def save_experiment(
        self,
        experiment: ExperimentDesign,
    ) -> StoredExperiment:
        """Persist one experiment design."""

        raise NotImplementedError

    def record_observation(
        self,
        observation: ValidationObservation,
    ) -> StoredObservation:
        """Persist a reviewer-attributed observation for a known experiment."""

        raise NotImplementedError

    def save_learning(
        self,
        learning: ValidatedLearning,
        observation_id: str,
    ) -> StoredLearning:
        """Persist exploratory learning linked to a known observation."""

        raise NotImplementedError


class SQLiteAuditRepository:
    """Stores append-only audit events in the active SQLite connection."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def record(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Record and commit one audit event."""

        with _write_transaction(self._connection):
            return self._record(
                event_type,
                entity_type,
                entity_id,
                description,
                metadata,
            )

    def _record(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Insert one event without opening a separate transaction."""

        for name, value in (
            ("event_type", event_type),
            ("entity_type", entity_type),
            ("entity_id", entity_id),
            ("description", description),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} cannot be empty")

        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("metadata must be a dictionary")

        event = AuditEvent(
            event_id=f"audit-{uuid.uuid4().hex}",
            event_type=event_type.strip(),
            entity_type=entity_type.strip(),
            entity_id=entity_id.strip(),
            timestamp=_timestamp(),
            description=description.strip(),
            metadata=metadata or {},
        )

        self._connection.execute(
            """
            INSERT INTO audit_events (
                event_id, event_type, entity_type, entity_id,
                timestamp, description, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.event_type,
                event.entity_type,
                event.entity_id,
                event.timestamp,
                event.description,
                _dump_json(event.metadata),
            ),
        )

        return event

    def list_events(
        self,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> List[AuditEvent]:
        """Return audit events in the order they were recorded."""

        clauses = []
        values = []

        if entity_id is not None:
            clauses.append("entity_id = ?")
            values.append(entity_id)

        if entity_type is not None:
            clauses.append("entity_type = ?")
            values.append(entity_type)

        query = (
            "SELECT event_id, event_type, entity_type, entity_id, "
            "timestamp, description, metadata_json FROM audit_events"
        )

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY sequence"

        rows = self._connection.execute(query, values).fetchall()

        return [
            AuditEvent(
                event_id=row["event_id"],
                event_type=row["event_type"],
                entity_type=row["entity_type"],
                entity_id=row["entity_id"],
                timestamp=row["timestamp"],
                description=row["description"],
                metadata=_load_mapping(row["metadata_json"]),
            )
            for row in rows
        ]


class SQLiteEvidenceRepository:
    """SQLite repository for evidence and explicit provenance."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        audit_events: SQLiteAuditRepository,
    ) -> None:
        self._connection = connection
        self._audit_events = audit_events

    def save(
        self,
        evidence: EvidenceItem,
        provenance: Optional[EvidenceProvenance] = None,
    ) -> StoredEvidence:
        """Validate, persist, and audit one evidence record idempotently."""

        evidence = _validated_evidence(evidence)
        provenance = _validated_provenance(provenance)
        evidence_id = _stable_id(
            "evidence",
            {
                "evidence": evidence.to_dict(),
                "provenance": provenance.to_dict(),
            },
        )

        created_at = _timestamp()

        with _write_transaction(self._connection):
            existing = self.get(evidence_id)

            if existing is not None:
                return existing

            self._connection.execute(
                """
                INSERT INTO evidence_records (
                    evidence_id, source_type, content, evidence_date,
                    location, population, metadata_json, entry_method,
                    original_source_id, source_reference, import_format,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence_id,
                    evidence.source_type,
                    evidence.content,
                    evidence.date,
                    evidence.location,
                    evidence.population,
                    _dump_json(evidence.metadata),
                    provenance.entry_method,
                    provenance.original_source_id,
                    provenance.source_reference,
                    provenance.import_format,
                    created_at,
                ),
            )
            event_type = (
                "evidence_imported"
                if provenance.entry_method == "imported"
                else "evidence_created"
            )
            self._audit_events._record(
                event_type=event_type,
                entity_type="evidence",
                entity_id=evidence_id,
                description=(
                    "Evidence was persisted with recorded provenance; "
                    "this does not establish that its content is true."
                ),
                metadata={
                    "source_type": evidence.source_type,
                    "entry_method": provenance.entry_method,
                    "original_source_id": provenance.original_source_id,
                },
            )

        return StoredEvidence(
            evidence_id=evidence_id,
            evidence=evidence,
            provenance=provenance,
            created_at=created_at,
        )

    def get(self, evidence_id: str) -> Optional[StoredEvidence]:
        """Load one evidence record by its stable identifier."""

        row = self._connection.execute(
            "SELECT * FROM evidence_records WHERE evidence_id = ?",
            (evidence_id,),
        ).fetchone()

        if row is None:
            return None

        return StoredEvidence(
            evidence_id=row["evidence_id"],
            evidence=EvidenceItem(
                source_type=row["source_type"],
                content=row["content"],
                date=row["evidence_date"],
                location=row["location"],
                population=row["population"],
                metadata=_load_mapping(row["metadata_json"]),
            ),
            provenance=EvidenceProvenance(
                entry_method=row["entry_method"],
                original_source_id=row["original_source_id"],
                source_reference=row["source_reference"],
                import_format=row["import_format"],
            ),
            created_at=row["created_at"],
        )

    def list(self) -> List[StoredEvidence]:
        """Load all evidence records in insertion order."""

        rows = self._connection.execute(
            "SELECT evidence_id FROM evidence_records ORDER BY created_at, evidence_id"
        ).fetchall()
        return [self.get(row["evidence_id"]) for row in rows]


class SQLiteExperimentRepository:
    """SQLite repository for deterministic experiment designs."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        audit_events: SQLiteAuditRepository,
        evidence: SQLiteEvidenceRepository,
    ) -> None:
        self._connection = connection
        self._audit_events = audit_events
        self._evidence = evidence

    def save(self, experiment: ExperimentDesign) -> StoredExperiment:
        """Persist an experiment or return the identical existing design."""

        _validate_experiment(experiment)

        for evidence_id in experiment.analysis_evidence_ids:
            if self._evidence.get(evidence_id) is None:
                raise ValueError(
                    f"Unknown evidence_id for experiment: {evidence_id}"
                )

        created_at = _timestamp()

        with _write_transaction(self._connection):
            existing = self.get(experiment.experiment_id)

            if existing is not None:
                if _experiment_definition(existing.experiment) != _experiment_definition(
                    experiment
                ):
                    raise ValueError(
                        "experiment_id already belongs to a different design"
                    )
                self._link_new_evidence(existing, experiment)
                return self.get(experiment.experiment_id)

            self._connection.execute(
                """
                INSERT INTO experiments (
                    experiment_id, title, hypothesis_title, objective,
                    intervention, comparison, measures_json,
                    evidence_basis_json, uncertainty_json, safeguards_json,
                    stop_conditions_json, validation_question, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment.experiment_id,
                    experiment.title,
                    experiment.hypothesis_title,
                    experiment.objective,
                    experiment.intervention,
                    experiment.comparison,
                    _dump_json(experiment.measures),
                    _dump_json(experiment.evidence_basis),
                    _dump_json(experiment.uncertainty),
                    _dump_json(experiment.safeguards),
                    _dump_json(experiment.stop_conditions),
                    experiment.validation_question,
                    created_at,
                ),
            )
            for position, evidence_id in enumerate(
                experiment.analysis_evidence_ids
            ):
                self._connection.execute(
                    """
                    INSERT INTO experiment_evidence (
                        experiment_id, evidence_id, position
                    ) VALUES (?, ?, ?)
                    """,
                    (experiment.experiment_id, evidence_id, position),
                )
            self._audit_events._record(
                event_type="experiment_created",
                entity_type="experiment",
                entity_id=experiment.experiment_id,
                description=(
                    "An experiment design was recorded for human review; "
                    "it is not authorization to implement or scale."
                ),
                metadata={
                    "hypothesis_title": experiment.hypothesis_title,
                    "analysis_evidence_ids": experiment.analysis_evidence_ids,
                },
            )

        return StoredExperiment(experiment=experiment, created_at=created_at)

    def _link_new_evidence(
        self,
        existing: StoredExperiment,
        experiment: ExperimentDesign,
    ) -> None:
        """Append new analysis-corpus lineage without erasing earlier links."""

        existing_ids = existing.experiment.analysis_evidence_ids

        new_ids = [
            evidence_id
            for evidence_id in experiment.analysis_evidence_ids
            if evidence_id not in existing_ids
        ]

        if not new_ids:
            return

        with _write_transaction(self._connection):
            for offset, evidence_id in enumerate(new_ids):
                self._connection.execute(
                    """
                    INSERT INTO experiment_evidence (
                        experiment_id, evidence_id, position
                    ) VALUES (?, ?, ?)
                    """,
                    (
                        experiment.experiment_id,
                        evidence_id,
                        len(existing_ids) + offset,
                    ),
                )
            self._audit_events._record(
                event_type="experiment_evidence_linked",
                entity_type="experiment",
                entity_id=experiment.experiment_id,
                description=(
                    "Additional analysis-corpus evidence lineage was linked "
                    "to an existing experiment; this does not establish "
                    "direct support or effectiveness."
                ),
                metadata={"analysis_evidence_ids": new_ids},
            )

    def get(self, experiment_id: str) -> Optional[StoredExperiment]:
        """Load one experiment design by its stable identifier."""

        row = self._connection.execute(
            "SELECT * FROM experiments WHERE experiment_id = ?",
            (experiment_id,),
        ).fetchone()

        if row is None:
            return None

        evidence_rows = self._connection.execute(
            """
            SELECT evidence_id FROM experiment_evidence
            WHERE experiment_id = ? ORDER BY position
            """,
            (experiment_id,),
        ).fetchall()

        return StoredExperiment(
            experiment=ExperimentDesign(
                experiment_id=row["experiment_id"],
                title=row["title"],
                hypothesis_title=row["hypothesis_title"],
                objective=row["objective"],
                intervention=row["intervention"],
                comparison=row["comparison"],
                measures=_load_list(row["measures_json"]),
                evidence_basis=_load_list(row["evidence_basis_json"]),
                uncertainty=_load_list(row["uncertainty_json"]),
                safeguards=_load_list(row["safeguards_json"]),
                stop_conditions=_load_list(row["stop_conditions_json"]),
                validation_question=row["validation_question"],
                analysis_evidence_ids=[
                    evidence_row["evidence_id"]
                    for evidence_row in evidence_rows
                ],
                outcome_metrics=[
                    OutcomeMetric(**_load_mapping(metric_row["payload_json"]))
                    for metric_row in self._connection.execute(
                        "SELECT outcome_metrics.payload_json FROM outcome_metrics "
                        "JOIN experiment_metrics USING (metric_id) "
                        "WHERE experiment_metrics.experiment_id = ?",
                        (experiment_id,),
                    ).fetchall()
                ],
            ),
            created_at=row["created_at"],
        )

    def list(self) -> List[StoredExperiment]:
        """Load all experiment designs in insertion order."""

        rows = self._connection.execute(
            "SELECT experiment_id FROM experiments ORDER BY created_at, experiment_id"
        ).fetchall()
        return [self.get(row["experiment_id"]) for row in rows]


class SQLiteLearningRepository:
    """SQLite repository for reviewer-attributed observations and learning."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        experiments: SQLiteExperimentRepository,
        audit_events: SQLiteAuditRepository,
    ) -> None:
        self._connection = connection
        self._experiments = experiments
        self._audit_events = audit_events

    def record_observation(
        self,
        observation: ValidationObservation,
    ) -> StoredObservation:
        """Store a reviewer-attributed observation for a known experiment."""

        ValidationLearningEngine.validate_observation(observation)
        experiment = self._experiments.get(observation.experiment_id)

        if experiment is None:
            raise ValueError(
                f"Unknown experiment_id: {observation.experiment_id}"
            )

        if observation.experiment_title != experiment.experiment.title:
            raise ValueError(
                "observation experiment_title does not match the stored experiment"
            )

        observation_id = _stable_id(
            "observation",
            observation.to_dict(),
        )
        created_at = _timestamp()

        with _write_transaction(self._connection):
            existing = self.get_observation(observation_id)

            if existing is not None:
                return existing

            self._connection.execute(
                """
                INSERT INTO observations (
                    observation_id, experiment_id, experiment_title,
                    outcome, evidence_basis_json, limitations_json,
                    reviewer, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observation_id,
                    observation.experiment_id,
                    observation.experiment_title,
                    observation.outcome,
                    _dump_json(observation.evidence_basis),
                    _dump_json(observation.limitations),
                    observation.reviewer,
                    created_at,
                ),
            )
            self._audit_events._record(
                event_type="observation_recorded",
                entity_type="observation",
                entity_id=observation_id,
                description=(
                    "A reviewer-attributed observation was recorded; "
                    "the system does not verify reviewer identity."
                ),
                metadata={"experiment_id": observation.experiment_id},
            )
            self._audit_events._record(
                event_type="reviewer_attributed",
                entity_type="observation",
                entity_id=observation_id,
                description=(
                    "Reviewer attribution was preserved for the observation; "
                    "the system does not verify that review occurred."
                ),
                metadata={
                    "reviewer": observation.reviewer,
                    "review_status": "attributed_not_verified",
                },
            )

        return StoredObservation(
            observation_id=observation_id,
            observation=observation,
            created_at=created_at,
        )

    def save_learning(
        self,
        learning: ValidatedLearning,
        observation_id: str,
    ) -> StoredLearning:
        """Store learning only when it preserves a stored observation."""

        ValidationLearningEngine.validate_learning(learning)
        observation = self.get_observation(observation_id)

        if observation is None:
            raise ValueError(f"Unknown observation_id: {observation_id}")

        self._validate_learning_link(learning, observation.observation)
        expected_learning = ValidationLearningEngine().evaluate(
            [observation.observation]
        )[0]

        if learning.to_dict() != expected_learning.to_dict():
            raise ValueError(
                "learning must be generated from the stored reviewer-attributed observation"
            )

        learning_id = _stable_id(
            "learning",
            {
                "observation_id": observation_id,
                "learning": learning.to_dict(),
            },
        )
        created_at = _timestamp()

        with _write_transaction(self._connection):
            existing = self.get_learning(learning_id)

            if existing is not None:
                return existing

            self._connection.execute(
                """
                INSERT INTO learning_records (
                    learning_id, observation_id, experiment_id,
                    experiment_title, observed_outcome, evidence_basis_json,
                    limitations_json, reviewer, learning, confidence,
                    next_step, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    learning_id,
                    observation_id,
                    learning.experiment_id,
                    learning.experiment_title,
                    learning.observed_outcome,
                    _dump_json(learning.evidence_basis),
                    _dump_json(learning.limitations),
                    learning.reviewer,
                    learning.learning,
                    learning.confidence,
                    learning.next_step,
                    created_at,
                ),
            )
            self._audit_events._record(
                event_type="learning_generated",
                entity_type="learning",
                entity_id=learning_id,
                description=(
                    "Exploratory learning was recorded from a "
                    "reviewer-attributed observation; it is not proof "
                    "of an intervention."
                ),
                metadata={
                    "experiment_id": learning.experiment_id,
                    "observation_id": observation_id,
                    "confidence": learning.confidence,
                    "review_status": "attributed_not_verified",
                },
            )

        return StoredLearning(
            learning_id=learning_id,
            observation_id=observation_id,
            learning=learning,
            created_at=created_at,
        )

    def get_observation(
        self,
        observation_id: str,
    ) -> Optional[StoredObservation]:
        """Load one observation by its persistent identifier."""

        row = self._connection.execute(
            "SELECT * FROM observations WHERE observation_id = ?",
            (observation_id,),
        ).fetchone()

        if row is None:
            return None

        return StoredObservation(
            observation_id=row["observation_id"],
            observation=ValidationObservation(
                experiment_id=row["experiment_id"],
                experiment_title=row["experiment_title"],
                outcome=row["outcome"],
                evidence_basis=_load_list(row["evidence_basis_json"]),
                limitations=_load_list(row["limitations_json"]),
                reviewer=row["reviewer"],
            ),
            created_at=row["created_at"],
        )

    def list_observations(
        self,
        experiment_id: Optional[str] = None,
    ) -> List[StoredObservation]:
        """Load observations, optionally restricted to an experiment."""

        if experiment_id is None:
            rows = self._connection.execute(
                "SELECT observation_id FROM observations "
                "ORDER BY created_at, observation_id"
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT observation_id FROM observations "
                "WHERE experiment_id = ? ORDER BY created_at, observation_id",
                (experiment_id,),
            ).fetchall()

        return [self.get_observation(row["observation_id"]) for row in rows]

    def get_learning(self, learning_id: str) -> Optional[StoredLearning]:
        """Load one learning record by its persistent identifier."""

        row = self._connection.execute(
            "SELECT * FROM learning_records WHERE learning_id = ?",
            (learning_id,),
        ).fetchone()

        if row is None:
            return None

        return StoredLearning(
            learning_id=row["learning_id"],
            observation_id=row["observation_id"],
            learning=ValidatedLearning(
                experiment_id=row["experiment_id"],
                experiment_title=row["experiment_title"],
                observed_outcome=row["observed_outcome"],
                evidence_basis=_load_list(row["evidence_basis_json"]),
                limitations=_load_list(row["limitations_json"]),
                reviewer=row["reviewer"],
                learning=row["learning"],
                confidence=row["confidence"],
                next_step=row["next_step"],
            ),
            created_at=row["created_at"],
        )

    def list_learning(
        self,
        experiment_id: Optional[str] = None,
    ) -> List[StoredLearning]:
        """Load learning records, optionally restricted to an experiment."""

        if experiment_id is None:
            rows = self._connection.execute(
                "SELECT learning_id FROM learning_records "
                "ORDER BY created_at, learning_id"
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT learning_id FROM learning_records "
                "WHERE experiment_id = ? ORDER BY created_at, learning_id",
                (experiment_id,),
            ).fetchall()

        return [self.get_learning(row["learning_id"]) for row in rows]

    @staticmethod
    def _validate_learning_link(
        learning: ValidatedLearning,
        observation: ValidationObservation,
    ) -> None:
        """Ensure a learning record faithfully traces to its observation."""

        if learning.experiment_id != observation.experiment_id:
            raise ValueError("learning experiment_id does not match observation")

        if learning.experiment_title != observation.experiment_title:
            raise ValueError("learning experiment_title does not match observation")

        if learning.observed_outcome != observation.outcome:
            raise ValueError("learning outcome does not match observation")

        if learning.evidence_basis != observation.evidence_basis:
            raise ValueError("learning evidence_basis does not match observation")

        if learning.reviewer != observation.reviewer:
            raise ValueError("learning reviewer does not match observation")


class SQLiteHistoricalRepository:
    """Main-store repository for historical programmes and mechanisms."""
    def __init__(self, connection, audit_events, learning):
        self._connection, self._audit_events, self._learning = connection, audit_events, learning
    def save_programme(self, programme):
        if not isinstance(programme, HistoricalProgramme): raise TypeError("programme must be HistoricalProgramme")
        payload=programme.to_dict(); programme_id=programme.programme_id or _stable_id("programme", payload); payload["programme_id"]=programme_id
        with _write_transaction(self._connection):
            row=self._connection.execute("SELECT payload_json, created_at FROM historical_programmes WHERE programme_id=?",(programme_id,)).fetchone()
            if row: return HistoricalProgramme(**_load_mapping(row["payload_json"]))
            self._connection.execute("INSERT INTO historical_programmes VALUES (?,?,?)",(programme_id,_dump_json(payload),_timestamp()))
            self._audit_events._record("historical_programme_imported","historical_programme",programme_id,"Historical programme metadata was stored; this does not establish effectiveness.",{"source_id":programme.provenance_source_id})
        return HistoricalProgramme(**payload)
    def get_programme(self, programme_id):
        row=self._connection.execute("SELECT payload_json FROM historical_programmes WHERE programme_id=?",(programme_id,)).fetchone()
        return HistoricalProgramme(**_load_mapping(row["payload_json"])) if row else None
    def list_programmes(self):
        return [self.get_programme(row["programme_id"]) for row in self._connection.execute("SELECT programme_id FROM historical_programmes ORDER BY created_at")]
    def save_mechanism(self, mechanism):
        if not isinstance(mechanism, MechanismRecord): raise TypeError("mechanism must be MechanismRecord")
        payload=mechanism.to_dict(); mechanism_id=mechanism.mechanism_id or _stable_id("mechanism", payload); payload["mechanism_id"]=mechanism_id
        with _write_transaction(self._connection):
            row=self._connection.execute("SELECT payload_json FROM mechanism_records WHERE mechanism_id=?",(mechanism_id,)).fetchone()
            if row: return MechanismRecord(**_load_mapping(row["payload_json"]))
            for programme_id in mechanism.source_programme_ids:
                if self.get_programme(programme_id) is None: raise ValueError(f"Unknown historical programme_id: {programme_id}")
            self._connection.execute("INSERT INTO mechanism_records VALUES (?,?,?)",(mechanism_id,_dump_json(payload),_timestamp()))
            for programme_id in mechanism.source_programme_ids: self._connection.execute("INSERT INTO programme_mechanisms VALUES (?,?)",(programme_id,mechanism_id))
            self._audit_events._record("mechanism_stored","mechanism",mechanism_id,"Mechanism metadata was stored as a candidate record.",{"programme_ids":mechanism.source_programme_ids})
        return MechanismRecord(**payload)
    def get_mechanism(self, mechanism_id):
        row=self._connection.execute("SELECT payload_json FROM mechanism_records WHERE mechanism_id=?",(mechanism_id,)).fetchone()
        return MechanismRecord(**_load_mapping(row["payload_json"])) if row else None
    def list_mechanisms(self): return [self.get_mechanism(row["mechanism_id"]) for row in self._connection.execute("SELECT mechanism_id FROM mechanism_records")]
    def link_learning(self, programme_id, mechanism_id, learning_id):
        if self.get_programme(programme_id) is None: raise ValueError("Unknown historical programme_id")
        if mechanism_id is not None and self.get_mechanism(mechanism_id) is None: raise ValueError("Unknown mechanism_id")
        if self._learning.get_learning(learning_id) is None: raise ValueError("Unknown learning_id")
        with _write_transaction(self._connection):
            self._connection.execute("INSERT OR IGNORE INTO historical_learning_links VALUES (?,?,?)",(programme_id,mechanism_id,learning_id))
            self._audit_events._record("historical_learning_linked","historical_programme",programme_id,"Exploratory learning was linked to a historical record.",{"mechanism_id":mechanism_id,"learning_id":learning_id})


class SQLiteOutcomeRepository:
    """Main-store repository for metric plans and reviewer-attributed outcomes."""
    def __init__(self, connection, experiments, audit_events):
        self._connection, self._experiments, self._audit_events = connection, experiments, audit_events

    def attach_metric(self, experiment_id, metric):
        if self._experiments.get(experiment_id) is None:
            raise ValueError("Unknown experiment_id")
        metric = metric.validated()
        with _write_transaction(self._connection):
            self._connection.execute("INSERT OR IGNORE INTO outcome_metrics VALUES (?, ?, ?, ?)",
                (metric.metric_id, _dump_json(metric.to_dict()), _timestamp(), metric.name))
            self._connection.execute("INSERT OR IGNORE INTO experiment_metrics VALUES (?, ?)",
                (experiment_id, metric.metric_id))
            self._audit_events._record("outcome_metric_created", "outcome_metric", metric.metric_id,
                "An outcome metric definition was stored; no outcome was inferred.", {})
            self._audit_events._record("metric_attached_to_experiment", "experiment", experiment_id,
                "An intended outcome metric was attached to an experiment.", {"metric_id": metric.metric_id})
        return metric

    def get_metric(self, metric_id):
        row = self._connection.execute("SELECT payload_json FROM outcome_metrics WHERE metric_id=?", (metric_id,)).fetchone()
        return OutcomeMetric(**_load_mapping(row["payload_json"])) if row else None

    def list_metrics(self, experiment_id):
        rows = self._connection.execute("SELECT metric_id FROM experiment_metrics WHERE experiment_id=?", (experiment_id,)).fetchall()
        return [self.get_metric(row["metric_id"]) for row in rows]

    def record_observation(self, observation):
        if self._experiments.get(observation.experiment_id) is None:
            raise ValueError("Unknown experiment_id")
        metric = self.get_metric(observation.metric_id)
        if metric is None:
            raise ValueError("Unknown metric_id")
        linked = self._connection.execute("SELECT 1 FROM experiment_metrics WHERE experiment_id=? AND metric_id=?", (observation.experiment_id, observation.metric_id)).fetchone()
        if linked is None:
            raise ValueError("metric_id is not attached to experiment_id")
        observation = observation.validated(metric)
        with _write_transaction(self._connection):
            self._connection.execute("INSERT OR IGNORE INTO outcome_observations VALUES (?, ?, ?, ?, ?)",
                (observation.observation_id, observation.experiment_id, observation.metric_id, _dump_json(observation.to_dict()), _timestamp()))
            self._audit_events._record("outcome_observation_recorded", "outcome_observation", observation.observation_id,
                "A reviewer-attributed outcome observation was recorded; it does not establish effectiveness.", {"metric_id": observation.metric_id})
            self._audit_events._record("outcome_observation_reviewed", "outcome_observation", observation.observation_id,
                "Reviewer attribution was recorded for an outcome observation.", {"reviewer": observation.reviewer})
        return observation

    def list_observations(self, experiment_id):
        rows = self._connection.execute("SELECT payload_json FROM outcome_observations WHERE experiment_id=? ORDER BY created_at", (experiment_id,)).fetchall()
        return [OutcomeObservation(**_load_mapping(row["payload_json"])) for row in rows]

    def compare(self, observation_a, observation_b):
        metric = self.get_metric(observation_a.metric_id)
        if metric is None or observation_a.metric_id != observation_b.metric_id:
            raise ValueError("outcome observations must reference the same known metric_id")
        comparison = ComparativeLearningEngine().compare(metric, observation_a, observation_b)
        self._audit_events.record("experiment_comparison_generated", "outcome_metric", metric.metric_id,
            "A transparent comparison of recorded observations was generated; no causal conclusion was made.", {})
        self._audit_events.record("comparative_learning_generated", "outcome_metric", metric.metric_id,
            "Comparative learning was generated as an exploratory summary, not an intervention ranking.", {})
        return comparison


class SQLitePersistenceStore(PersistenceStore):
    """Optional SQLite implementation of the persistence-store interface."""

    def __init__(
        self,
        database_path: Union[str, Path] = ":memory:",
    ) -> None:
        self._connection = sqlite3.connect(str(database_path))
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

        self.audit_events = SQLiteAuditRepository(self._connection)
        self.evidence = SQLiteEvidenceRepository(
            self._connection,
            self.audit_events,
        )
        self.experiments = SQLiteExperimentRepository(
            self._connection,
            self.audit_events,
            self.evidence,
        )
        self.learning = SQLiteLearningRepository(
            self._connection,
            self.experiments,
            self.audit_events,
        )
        self.historical = SQLiteHistoricalRepository(
            self._connection, self.audit_events, self.learning
        )
        self.outcomes = SQLiteOutcomeRepository(
            self._connection, self.experiments, self.audit_events
        )

    def save_evidence(
        self,
        evidence: EvidenceItem,
        provenance: Optional[EvidenceProvenance] = None,
    ) -> StoredEvidence:
        """Persist one evidence item through the storage interface."""

        return self.evidence.save(evidence, provenance)

    def save_experiment(
        self,
        experiment: ExperimentDesign,
    ) -> StoredExperiment:
        """Persist one experiment design through the storage interface."""

        saved = self.experiments.save(experiment)
        for metric in experiment.outcome_metrics:
            self.outcomes.attach_metric(experiment.experiment_id, metric)
        return saved

    def record_observation(
        self,
        observation: ValidationObservation,
    ) -> StoredObservation:
        """Persist a reviewer-attributed observation through the interface."""

        return self.learning.record_observation(observation)

    def save_learning(
        self,
        learning: ValidatedLearning,
        observation_id: str,
    ) -> StoredLearning:
        """Persist learning through the storage interface."""

        return self.learning.save_learning(learning, observation_id)

    def save_historical_programme(self, programme: HistoricalProgramme):
        return self.historical.save_programme(programme)

    def save_mechanism(self, mechanism: MechanismRecord):
        return self.historical.save_mechanism(mechanism)

    def attach_outcome_metric(self, experiment_id: str, metric: OutcomeMetric):
        return self.outcomes.attach_metric(experiment_id, metric)

    def record_outcome_observation(self, observation: OutcomeObservation):
        return self.outcomes.record_observation(observation)

    def compare_outcomes(self, observation_a: OutcomeObservation, observation_b: OutcomeObservation):
        return self.outcomes.compare(observation_a, observation_b)

    @contextmanager
    def transaction(self):
        """Make a related set of SQLite writes atomic."""

        if self._connection.in_transaction:
            savepoint = f"opensocial_{uuid.uuid4().hex}"
            self._connection.execute(f"SAVEPOINT {savepoint}")
            try:
                yield self
            except BaseException:
                self._connection.execute(
                    f"ROLLBACK TO SAVEPOINT {savepoint}"
                )
                self._connection.execute(f"RELEASE SAVEPOINT {savepoint}")
                raise
            else:
                self._connection.execute(f"RELEASE SAVEPOINT {savepoint}")
            return

        self._connection.execute("BEGIN IMMEDIATE")
        try:
            yield self
        except BaseException:
            self._connection.rollback()
            raise
        else:
            try:
                self._connection.commit()
            except BaseException:
                self._connection.rollback()
                raise

    def close(self) -> None:
        """Close the SQLite connection."""

        self._connection.close()

    def __enter__(self) -> "SQLitePersistenceStore":
        """Enter a context-managed storage session."""

        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Close the storage session when leaving the context."""

        self.close()

    def _create_schema(self) -> None:
        """Create the small, explicit SQLite schema if it is absent."""

        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS evidence_records (
                    evidence_id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    evidence_date TEXT,
                    location TEXT,
                    population TEXT,
                    metadata_json TEXT NOT NULL,
                    entry_method TEXT NOT NULL,
                    original_source_id TEXT,
                    source_reference TEXT,
                    import_format TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    hypothesis_title TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    intervention TEXT NOT NULL,
                    comparison TEXT NOT NULL,
                    measures_json TEXT NOT NULL,
                    evidence_basis_json TEXT NOT NULL,
                    uncertainty_json TEXT NOT NULL,
                    safeguards_json TEXT NOT NULL,
                    stop_conditions_json TEXT NOT NULL,
                    validation_question TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS observations (
                    observation_id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    experiment_title TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    evidence_basis_json TEXT NOT NULL,
                    limitations_json TEXT NOT NULL,
                    reviewer TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (experiment_id)
                        REFERENCES experiments(experiment_id)
                );

                CREATE TABLE IF NOT EXISTS experiment_evidence (
                    experiment_id TEXT NOT NULL,
                    evidence_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    PRIMARY KEY (experiment_id, evidence_id),
                    UNIQUE (experiment_id, position),
                    FOREIGN KEY (experiment_id)
                        REFERENCES experiments(experiment_id),
                    FOREIGN KEY (evidence_id)
                        REFERENCES evidence_records(evidence_id)
                );

                CREATE TABLE IF NOT EXISTS learning_records (
                    learning_id TEXT PRIMARY KEY,
                    observation_id TEXT NOT NULL,
                    experiment_id TEXT NOT NULL,
                    experiment_title TEXT NOT NULL,
                    observed_outcome TEXT NOT NULL,
                    evidence_basis_json TEXT NOT NULL,
                    limitations_json TEXT NOT NULL,
                    reviewer TEXT NOT NULL,
                    learning TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    next_step TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (observation_id)
                        REFERENCES observations(observation_id),
                    FOREIGN KEY (experiment_id)
                        REFERENCES experiments(experiment_id)
                );

                CREATE TABLE IF NOT EXISTS audit_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    event_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    description TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS historical_programmes (
                    programme_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS mechanism_records (
                    mechanism_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS programme_mechanisms (
                    programme_id TEXT NOT NULL, mechanism_id TEXT NOT NULL,
                    PRIMARY KEY (programme_id, mechanism_id),
                    FOREIGN KEY (programme_id) REFERENCES historical_programmes(programme_id),
                    FOREIGN KEY (mechanism_id) REFERENCES mechanism_records(mechanism_id)
                );
                CREATE TABLE IF NOT EXISTS historical_learning_links (
                    programme_id TEXT NOT NULL, mechanism_id TEXT, learning_id TEXT NOT NULL,
                    PRIMARY KEY (programme_id, mechanism_id, learning_id),
                    FOREIGN KEY (programme_id) REFERENCES historical_programmes(programme_id),
                    FOREIGN KEY (mechanism_id) REFERENCES mechanism_records(mechanism_id),
                    FOREIGN KEY (learning_id) REFERENCES learning_records(learning_id)
                );
                CREATE TABLE IF NOT EXISTS outcome_metrics (
                    metric_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL, name TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS experiment_metrics (
                    experiment_id TEXT NOT NULL, metric_id TEXT NOT NULL,
                    PRIMARY KEY (experiment_id, metric_id),
                    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id),
                    FOREIGN KEY (metric_id) REFERENCES outcome_metrics(metric_id)
                );
                CREATE TABLE IF NOT EXISTS outcome_observations (
                    observation_id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL,
                    metric_id TEXT NOT NULL, payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id),
                    FOREIGN KEY (metric_id) REFERENCES outcome_metrics(metric_id)
                );
                """
            )


def _timestamp() -> str:
    """Return a timezone-aware timestamp for a real storage event."""

    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _write_transaction(connection: sqlite3.Connection):
    """Open a write transaction only when no caller already owns one."""

    if connection.in_transaction:
        yield
        return

    connection.execute("BEGIN IMMEDIATE")
    try:
        yield
    except BaseException:
        connection.rollback()
        raise
    else:
        try:
            connection.commit()
        except BaseException:
            connection.rollback()
            raise


def _stable_id(prefix: str, payload: Dict) -> str:
    """Return a deterministic content identifier for a persistent record."""

    identity = _dump_json(payload)
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:24]}"


def _dump_json(value: Any) -> str:
    """Serialize structured fields deterministically for storage and IDs."""

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as error:
        raise ValueError("Structured fields must be JSON-serializable") from error


def _load_list(value: str) -> List:
    """Load a list-shaped JSON field from a repository row."""

    loaded = json.loads(value)
    if not isinstance(loaded, list):
        raise ValueError("Stored structured field is not a list")
    return loaded


def _load_mapping(value: str) -> Dict:
    """Load a mapping-shaped JSON field from a repository row."""

    loaded = json.loads(value)
    if not isinstance(loaded, dict):
        raise ValueError("Stored structured field is not a dictionary")
    return loaded


def _validated_evidence(evidence: EvidenceItem) -> EvidenceItem:
    """Validate and normalize evidence at the persistence boundary."""

    if not isinstance(evidence, EvidenceItem):
        raise TypeError("evidence must be an EvidenceItem")

    if not isinstance(evidence.metadata, dict):
        raise ValueError("evidence metadata must be a dictionary")

    for name in ("date", "location", "population"):
        value = getattr(evidence, name)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"evidence {name} must be a string or None")

    _dump_json(evidence.metadata)

    return create_evidence(
        source_type=evidence.source_type,
        content=evidence.content,
        date=evidence.date,
        location=evidence.location,
        population=evidence.population,
        metadata=evidence.metadata,
    )


def _validated_provenance(
    provenance: Optional[EvidenceProvenance],
) -> EvidenceProvenance:
    """Validate and normalize provenance without inventing absent values."""

    if provenance is None:
        return EvidenceProvenance()

    if not isinstance(provenance, EvidenceProvenance):
        raise TypeError("provenance must be an EvidenceProvenance")

    entry_method = provenance.entry_method
    if not isinstance(entry_method, str) or not entry_method.strip():
        raise ValueError("provenance entry_method cannot be empty")

    entry_method = entry_method.strip().lower()
    if entry_method not in {"manual", "imported"}:
        raise ValueError("provenance entry_method must be manual or imported")

    values = {}
    for name in (
        "original_source_id",
        "source_reference",
        "import_format",
    ):
        value = getattr(provenance, name)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"provenance {name} must be a string or None")
        values[name] = value.strip() if isinstance(value, str) and value.strip() else None

    if entry_method == "manual" and values["import_format"] is not None:
        raise ValueError("manual provenance cannot declare an import_format")

    return EvidenceProvenance(entry_method=entry_method, **values)


def _validate_experiment(experiment: ExperimentDesign) -> None:
    """Validate experiment fields before they enter persistent storage."""

    if not isinstance(experiment, ExperimentDesign):
        raise TypeError("experiment must be an ExperimentDesign")

    for name in (
        "experiment_id",
        "title",
        "hypothesis_title",
        "objective",
        "intervention",
        "comparison",
        "validation_question",
    ):
        value = getattr(experiment, name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"experiment {name} cannot be empty")

    for name in (
        "measures",
        "evidence_basis",
        "uncertainty",
        "safeguards",
        "stop_conditions",
    ):
        value = getattr(experiment, name)
        if not isinstance(value, list) or not value or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            raise ValueError(
                f"experiment {name} must contain non-empty strings"
            )

    if (
        not isinstance(experiment.analysis_evidence_ids, list)
        or not experiment.analysis_evidence_ids
        or not all(
            isinstance(evidence_id, str) and evidence_id.strip()
            for evidence_id in experiment.analysis_evidence_ids
        )
        or len(set(experiment.analysis_evidence_ids))
        != len(experiment.analysis_evidence_ids)
    ):
        raise ValueError(
            "experiment analysis_evidence_ids must contain unique non-empty identifiers"
        )

    if not any(
        "cannot establish" in item.lower()
        for item in experiment.uncertainty
    ):
        raise ValueError(
            "experiment uncertainty must preserve the non-generalization safeguard"
        )

    if not any("community" in item.lower() for item in experiment.safeguards):
        raise ValueError(
            "experiment safeguards must include community oversight"
        )

    if not any("affected people" in item.lower() for item in experiment.safeguards):
        raise ValueError(
            "experiment safeguards must include affected-person review"
        )

    if not any(
        "do not scale" in item.lower() and "human review" in item.lower()
        for item in experiment.stop_conditions
    ):
        raise ValueError(
            "experiment stop conditions must require human review before scaling"
        )


def _experiment_definition(experiment: ExperimentDesign) -> Dict:
    """Return the immutable experiment-design fields, excluding lineage links."""

    definition = experiment.to_dict()
    definition.pop("analysis_evidence_ids", None)
    definition.pop("outcome_metrics", None)
    return definition
