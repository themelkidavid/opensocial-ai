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
    from src.portfolio_learning import ProgrammePortfolio
    from src.strategic_scenarios import StrategicScenario
    from src.governance import GovernanceReview, DecisionRecord, ExperimentAuthorization
    from src.decision_briefs import EvidencePack, DecisionBrief
    from src.auth import User, Organisation, Membership, AuthSession, ROLES
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
    from portfolio_learning import ProgrammePortfolio
    from strategic_scenarios import StrategicScenario
    from governance import GovernanceReview, DecisionRecord, ExperimentAuthorization
    from decision_briefs import EvidencePack, DecisionBrief
    from auth import User, Organisation, Membership, AuthSession, ROLES


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


@dataclass(frozen=True)
class APIProject:
    """A durable, application-owned workspace; it is not an identity record."""

    project_id: str
    name: str
    description: Optional[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {"project_id": self.project_id, "name": self.name, "description": self.description, "created_at": self.created_at}


@dataclass(frozen=True)
class StoredAPIAnalysis:
    """A persisted API response snapshot, without hidden model reasoning."""

    analysis_id: str
    project_id: str
    created_at: str
    problem: str
    report: Dict[str, Any]
    evidence_ids: List[str]
    narrative_analysis: Optional[Dict[str, Any]]
    responsible_ai: str
    interpretation_mode: str

    def to_dict(self) -> Dict[str, Any]:
        return {"analysis_id": self.analysis_id, "project_id": self.project_id, "created_at": self.created_at, "report": self.report, "evidence_ids": self.evidence_ids, "narrative_analysis": self.narrative_analysis, "responsible_ai": self.responsible_ai}

    def summary_dict(self) -> Dict[str, Any]:
        return {"analysis_id": self.analysis_id, "project_id": self.project_id, "created_at": self.created_at, "problem": self.problem, "evidence_count": len(self.evidence_ids), "interpretation_mode": self.interpretation_mode}


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


class SQLitePortfolioRepository:
    """Persisted portfolio metadata using the main audit and SQLite boundary."""
    def __init__(self, connection, historical, experiments, audit_events):
        self._connection,self._historical,self._experiments,self._audit_events=connection,historical,experiments,audit_events
    def save(self, portfolio):
        portfolio=portfolio.validated()
        for programme_id in portfolio.programme_ids:
            if self._historical.get_programme(programme_id) is None: raise ValueError("Unknown programme_id")
        for experiment_id in portfolio.experiment_ids:
            if self._experiments.get(experiment_id) is None: raise ValueError("Unknown experiment_id")
        with _write_transaction(self._connection):
            row=self._connection.execute("SELECT payload_json FROM portfolios WHERE portfolio_id=?",(portfolio.portfolio_id,)).fetchone()
            if row: return ProgrammePortfolio(**_load_mapping(row["payload_json"]))
            self._connection.execute("INSERT INTO portfolios VALUES (?,?,?)",(portfolio.portfolio_id,_dump_json(portfolio.to_dict()),_timestamp()))
            self._audit_events._record("portfolio_created","portfolio",portfolio.portfolio_id,"Portfolio metadata was stored for exploratory analysis.",{})
        return portfolio
    def get(self, portfolio_id):
        row=self._connection.execute("SELECT payload_json FROM portfolios WHERE portfolio_id=?",(portfolio_id,)).fetchone()
        return ProgrammePortfolio(**_load_mapping(row["payload_json"])) if row else None
    def list(self):
        return [self.get(row["portfolio_id"]) for row in self._connection.execute("SELECT portfolio_id FROM portfolios ORDER BY created_at")]
    def record_analysis(self, portfolio_id, patterns, opportunities):
        self._audit_events.record("portfolio_analysis_performed","portfolio",portfolio_id,"Portfolio records were analysed descriptively; no causal conclusion was made.",{})
        for pattern in patterns: self._audit_events.record("portfolio_pattern_generated","portfolio",portfolio_id,"A descriptive portfolio pattern was generated.",{"pattern_type":pattern.pattern_type})
        for opportunity in opportunities: self._audit_events.record("strategy_opportunity_generated","portfolio",portfolio_id,"An exploratory strategy opportunity was generated; it is not a recommendation.",{"pattern_type":opportunity.pattern_type})

class SQLiteScenarioRepository:
    def __init__(self, connection, historical, audit_events): self._connection,self._historical,self._audit_events=connection,historical,audit_events
    def save(self, scenario):
        scenario=scenario.validated()
        for pid in scenario.programme_ids:
            if self._historical.get_programme(pid) is None: raise ValueError("Unknown programme_id")
        for mid in scenario.mechanism_ids:
            if self._historical.get_mechanism(mid) is None: raise ValueError("Unknown mechanism_id")
        with _write_transaction(self._connection):
            row=self._connection.execute("SELECT payload_json FROM strategic_scenarios WHERE scenario_id=?",(scenario.scenario_id,)).fetchone()
            if row: return StrategicScenario(**_load_mapping(row["payload_json"]))
            self._connection.execute("INSERT INTO strategic_scenarios VALUES (?,?,?)",(scenario.scenario_id,_dump_json(scenario.to_dict()),_timestamp()))
            self._audit_events._record("scenario_generated","scenario",scenario.scenario_id,"An exploratory scenario was generated; it is not a recommendation or prediction.",{})
            self._audit_events._record("scenario_stored","scenario",scenario.scenario_id,"Scenario metadata was stored.",{})
            if scenario.potential_experiment: self._audit_events._record("scenario_linked_to_experiment_concept","scenario",scenario.scenario_id,"An experiment concept was linked; human approval remains required.",{})
        return scenario
    def get(self, sid):
        row=self._connection.execute("SELECT payload_json FROM strategic_scenarios WHERE scenario_id=?",(sid,)).fetchone(); return StrategicScenario(**_load_mapping(row["payload_json"])) if row else None
    def list(self): return [self.get(r["scenario_id"]) for r in self._connection.execute("SELECT scenario_id FROM strategic_scenarios ORDER BY created_at")]
    def update_review_status(self,sid,status):
        scenario=self.get(sid)
        if scenario is None: raise ValueError("Unknown scenario_id")
        updated=StrategicScenario(**{**scenario.to_dict(),"review_status":status}).validated()
        with _write_transaction(self._connection):
            self._connection.execute("UPDATE strategic_scenarios SET payload_json=? WHERE scenario_id=?",(_dump_json(updated.to_dict()),sid)); self._audit_events._record("scenario_review_status_changed","scenario",sid,"Scenario review status changed as governance metadata; it does not establish effectiveness.",{"review_status":status})
        return updated
    def record_comparison(self, scenario_ids): self._audit_events.record("scenario_compared","scenario",scenario_ids[0] if scenario_ids else "none","Scenarios were compared descriptively; no ranking was produced.",{})

class SQLiteGovernanceRepository:
 def __init__(self,c,s,a): self._connection,self._scenarios,self._audit_events=c,s,a
 def save_review(self,review):
  review=review.validated()
  if review.subject_type=="strategic_scenario" and self._scenarios.get(review.subject_id) is None: raise ValueError("Unknown scenario subject")
  self._connection.execute("INSERT OR IGNORE INTO governance_reviews VALUES (?,?,?,?)",(review.review_id,review.subject_type,review.subject_id,_dump_json(review.to_dict()))); self._connection.commit(); self._audit_events.record("governance_review_created","governance_review",review.review_id,"Human governance review was recorded.",{"actor_id":review.reviewer_id}); return review
 def get_review(self,rid):
  r=self._connection.execute("SELECT payload_json FROM governance_reviews WHERE review_id=?",(rid,)).fetchone(); return GovernanceReview(**_load_mapping(r["payload_json"])) if r else None
 def list_reviews_by_subject(self,typ,sid): return [GovernanceReview(**_load_mapping(r["payload_json"])) for r in self._connection.execute("SELECT payload_json FROM governance_reviews WHERE subject_type=? AND subject_id=? ORDER BY review_id",(typ,sid))]
 def save_decision(self,decision):
  decision=decision.validated()
  if decision.subject_type=="strategic_scenario" and self._scenarios.get(decision.subject_id) is None: raise ValueError("Unknown scenario subject")
  for rid in decision.review_ids:
   if self._connection.execute("SELECT 1 FROM governance_reviews WHERE review_id=?",(rid,)).fetchone() is None: raise ValueError("Unknown review_id")
  if decision.supersedes_decision_id and self.get_decision(decision.supersedes_decision_id) is None: raise ValueError("Unknown superseded decision")
  if decision.supersedes_decision_id:
   prior=self.get_decision(decision.supersedes_decision_id)
   if prior.subject_type!=decision.subject_type or prior.subject_id!=decision.subject_id: raise ValueError("Superseded decision must have the same subject")
   if prior.decision_id==decision.decision_id: raise ValueError("Decision cannot supersede itself")
   if decision.decision_status!="recorded": raise ValueError("Superseding decision must be recorded")
   superseded=DecisionRecord(**{**prior.to_dict(),"decision_status":"superseded"})
   self._connection.execute("UPDATE governance_decisions SET payload_json=? WHERE decision_id=?",(_dump_json(superseded.to_dict()),prior.decision_id))
   self._audit_events._record("decision_superseded","decision",prior.decision_id,"A prior human decision was superseded and retained in history.",{"actor_id":decision.decision_maker_id})
  self._connection.execute("INSERT INTO governance_decisions VALUES (?,?,?,?)",(decision.decision_id,decision.subject_type,decision.subject_id,_dump_json(decision.to_dict()))); self._connection.commit(); self._audit_events.record("decision_recorded","decision",decision.decision_id,"Explicit human decision was recorded; it does not establish effectiveness.",{"actor_id":decision.decision_maker_id}); return decision
 def get_decision(self,did):
  r=self._connection.execute("SELECT payload_json FROM governance_decisions WHERE decision_id=?",(did,)).fetchone(); return DecisionRecord(**_load_mapping(r["payload_json"])) if r else None
 def list_decisions(self,typ,sid): return [DecisionRecord(**_load_mapping(r["payload_json"])) for r in self._connection.execute("SELECT payload_json FROM governance_decisions WHERE subject_type=? AND subject_id=?",(typ,sid))]
 list_decisions_by_subject=list_decisions
 def get_active_decision(self,typ,sid):
  decisions=self.list_decisions(typ,sid); superseded={d.supersedes_decision_id for d in decisions if d.supersedes_decision_id}; active=[d for d in decisions if d.decision_status=="recorded" and d.decision_id not in superseded]
  return sorted(active,key=lambda d:d.decision_id)[-1] if active else None
 def authorize(self,auth):
  d=self.get_decision(auth.decision_id)
  if d is None or d.decision_status!="recorded" or d.decision_type not in {"proceed_to_experiment_design","approve_experiment"} or not d.decision_maker_id: raise ValueError("Authorization requires an explicit recorded human decision permitting experiment progression")
  if self._scenarios.get(auth.scenario_id) is None: raise ValueError("Unknown scenario")
  aid=auth.authorization_id or _stable_id("authorization",auth.to_dict()); auth=ExperimentAuthorization(**{**auth.to_dict(),"authorization_id":aid}); self._connection.execute("INSERT INTO experiment_authorizations VALUES (?,?,?,?)",(aid,auth.decision_id,auth.scenario_id,_dump_json(auth.to_dict()))); self._connection.commit(); self._audit_events.record("experiment_authorization_created","authorization",aid,"Explicit human authorization was recorded; it is not evidence of success.",{"actor_id":auth.authorized_by}); return auth
 def get_authorization(self,aid):
  r=self._connection.execute("SELECT payload_json FROM experiment_authorizations WHERE authorization_id=?",(aid,)).fetchone(); return ExperimentAuthorization(**_load_mapping(r["payload_json"])) if r else None
 def list_authorizations_by_decision(self,did): return [ExperimentAuthorization(**_load_mapping(r["payload_json"])) for r in self._connection.execute("SELECT payload_json FROM experiment_authorizations WHERE decision_id=? ORDER BY authorization_id",(did,))]
 def list_authorizations_by_scenario(self,sid): return [ExperimentAuthorization(**_load_mapping(r["payload_json"])) for r in self._connection.execute("SELECT payload_json FROM experiment_authorizations WHERE scenario_id=? ORDER BY authorization_id",(sid,))]
 def timeline(self,typ,sid):
  events=[]
  for event in self._audit_events.list_events():
   if event.entity_id==sid or event.metadata.get("subject_id")==sid: events.append(event.to_dict())
  for review in self.list_reviews_by_subject(typ,sid): events.append({"event_type":"governance_review","entity_type":"governance_review","entity_id":review.review_id,"timestamp":review.reviewed_at or "","description":"Human governance review record.","actor_id":review.reviewer_id})
  for decision in self.list_decisions(typ,sid): events.append({"event_type":"decision","entity_type":"decision","entity_id":decision.decision_id,"timestamp":decision.decided_at or "","description":"Human decision record.","actor_id":decision.decision_maker_id})
  return sorted(events,key=lambda e:(e.get("timestamp") or "",e.get("entity_id") or ""))
 def summary(self,typ,sid):
  reviews=self.list_reviews_by_subject(typ,sid); decisions=self.list_decisions(typ,sid); active=self.get_active_decision(typ,sid); auths=self.list_authorizations_by_scenario(sid) if typ=="strategic_scenario" else []
  return {"subject_type":typ,"subject_id":sid,"evidence_references":[x for d in decisions for x in d.evidence_basis],"reviews":[r.to_dict() for r in reviews],"concerns":[x for r in reviews for x in r.concerns],"unresolved_questions":[x for r in reviews for x in r.unresolved_questions],"alternatives":[x for d in decisions for x in d.alternatives_considered],"dissent_or_reservations":[x for d in decisions for x in d.dissent_or_reservations],"decision_history":[d.to_dict() for d in decisions],"active_decision":active.to_dict() if active else None,"authorizations":[a.to_dict() for a in auths]}

class SQLiteDecisionBriefRepository:
 def __init__(self, connection, audit_events): self._connection,self._audit_events=connection,audit_events
 def save_pack(self, pack):
  pack=pack.finalized(); self._connection.execute("INSERT OR IGNORE INTO evidence_packs VALUES (?,?,?,?)",(pack.pack_id,pack.subject_type,pack.subject_id,_dump_json(pack.to_dict()))); self._connection.commit(); self._audit_events.record("evidence_pack_generated","evidence_pack",pack.pack_id,"Evidence pack snapshot was generated from supplied records.",{"subject_type":pack.subject_type,"subject_id":pack.subject_id}); self._audit_events.record("evidence_pack_stored","evidence_pack",pack.pack_id,"Evidence pack snapshot was stored.",{"subject_type":pack.subject_type,"subject_id":pack.subject_id}); return pack
 def get_pack(self, pack_id):
  row=self._connection.execute("SELECT payload_json FROM evidence_packs WHERE pack_id=?",(pack_id,)).fetchone(); return EvidencePack(**_load_mapping(row["payload_json"])) if row else None
 def list_packs(self, subject_type, subject_id): return [EvidencePack(**_load_mapping(r["payload_json"])) for r in self._connection.execute("SELECT payload_json FROM evidence_packs WHERE subject_type=? AND subject_id=? ORDER BY pack_id",(subject_type,subject_id))]
 def save_brief(self, brief):
  brief=brief.finalized()
  if self.get_brief(brief.brief_id): raise ValueError("brief_id already exists")
  version=self._connection.execute("SELECT COALESCE(MAX(brief_version),0)+1 AS version FROM decision_briefs WHERE subject_type=? AND subject_id=?",(brief.subject_type,brief.subject_id)).fetchone()["version"]
  if brief.brief_version not in (1,version): raise ValueError("brief_version must be next for subject")
  brief=DecisionBrief(**{**brief.to_dict(),"brief_version":version})
  self._connection.execute("INSERT INTO decision_briefs VALUES (?,?,?,?,?)",(brief.brief_id,brief.subject_type,brief.subject_id,version,_dump_json(brief.to_dict()))); self._connection.commit(); self._audit_events.record("decision_brief_generated","decision_brief",brief.brief_id,"Decision brief snapshot was generated; it is not a decision.",{"subject_type":brief.subject_type,"subject_id":brief.subject_id,"version":version}); self._audit_events.record("decision_brief_version_created","decision_brief",brief.brief_id,"Decision brief snapshot was stored; it is not a decision.",{"subject_type":brief.subject_type,"subject_id":brief.subject_id,"version":version}); return brief
 def get_brief(self, brief_id):
  row=self._connection.execute("SELECT payload_json FROM decision_briefs WHERE brief_id=?",(brief_id,)).fetchone(); return DecisionBrief(**_load_mapping(row["payload_json"])) if row else None
 def list_briefs(self, subject_type, subject_id): return [DecisionBrief(**_load_mapping(r["payload_json"])) for r in self._connection.execute("SELECT payload_json FROM decision_briefs WHERE subject_type=? AND subject_id=? ORDER BY brief_version",(subject_type,subject_id))]
 def latest(self, subject_type, subject_id):
  row=self._connection.execute("SELECT payload_json FROM decision_briefs WHERE subject_type=? AND subject_id=? ORDER BY brief_version DESC LIMIT 1",(subject_type,subject_id)).fetchone(); return DecisionBrief(**_load_mapping(row["payload_json"])) if row else None


class SQLiteAPIWorkspaceRepository:
    """Application workspace records and links, kept separate from core evidence."""

    def __init__(self, connection, evidence, audit_events):
        self._connection, self._evidence, self._audit_events = connection, evidence, audit_events

    def save_project(self, project: APIProject) -> APIProject:
        if not project.project_id or not project.name.strip() or not project.created_at:
            raise ValueError("project requires an identifier, name, and timestamp")
        with _write_transaction(self._connection):
            existing = self.get_project(project.project_id)
            if existing:
                if existing != project: raise ValueError("project_id already exists")
                return existing
            self._connection.execute("INSERT INTO api_projects (project_id, name, description, created_at) VALUES (?, ?, ?, ?)", (project.project_id, project.name, project.description, project.created_at))
            self._audit_events._record("project_created", "api_project", project.project_id, "Project workspace was created.", {"project_id": project.project_id})
        return project

    def get_project(self, project_id):
        row = self._connection.execute("SELECT project_id, name, description, created_at FROM api_projects WHERE project_id = ?", (project_id,)).fetchone()
        return APIProject(**dict(row)) if row else None

    def list_projects(self):
        rows = self._connection.execute("SELECT project_id, name, description, created_at FROM api_projects ORDER BY created_at, project_id").fetchall()
        return [APIProject(**dict(row)) for row in rows]

    def link_evidence(self, project_id, evidence_id):
        if not self.get_project(project_id): raise ValueError("unknown project_id")
        if not self._evidence.get(evidence_id): raise ValueError("unknown evidence_id")
        with _write_transaction(self._connection):
            existing = self._connection.execute("SELECT 1 FROM api_project_evidence WHERE project_id = ? AND evidence_id = ?", (project_id, evidence_id)).fetchone()
            if existing: return
            position = self._connection.execute("SELECT COUNT(*) AS count FROM api_project_evidence WHERE project_id = ?", (project_id,)).fetchone()["count"]
            self._connection.execute("INSERT INTO api_project_evidence (project_id, evidence_id, position, created_at) VALUES (?, ?, ?, ?)", (project_id, evidence_id, position, _timestamp()))
            self._audit_events._record("project_evidence_linked", "api_project", project_id, "Evidence was linked to a project workspace.", {"project_id": project_id, "evidence_id": evidence_id})

    def list_evidence(self, project_id):
        if not self.get_project(project_id): raise ValueError("unknown project_id")
        rows = self._connection.execute("SELECT evidence_id FROM api_project_evidence WHERE project_id = ? ORDER BY position, evidence_id", (project_id,)).fetchall()
        return [self._evidence.get(row["evidence_id"]) for row in rows]

    def save_analysis(self, analysis: StoredAPIAnalysis) -> StoredAPIAnalysis:
        if not self.get_project(analysis.project_id): raise ValueError("unknown project_id")
        for evidence_id in analysis.evidence_ids:
            if not self._connection.execute("SELECT 1 FROM api_project_evidence WHERE project_id = ? AND evidence_id = ?", (analysis.project_id, evidence_id)).fetchone():
                raise ValueError("analysis evidence is not linked to project")
        with _write_transaction(self._connection):
            if self.get_analysis(analysis.analysis_id): raise ValueError("analysis_id already exists")
            self._connection.execute("INSERT INTO api_analyses (analysis_id, project_id, created_at, problem, report_json, evidence_ids_json, narrative_json, responsible_ai, interpretation_mode) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (analysis.analysis_id, analysis.project_id, analysis.created_at, analysis.problem, _dump_json(analysis.report), _dump_json(analysis.evidence_ids), _dump_json(analysis.narrative_analysis) if analysis.narrative_analysis is not None else None, analysis.responsible_ai, analysis.interpretation_mode))
            self._audit_events._record("analysis_created", "api_analysis", analysis.analysis_id, "Exploratory analysis snapshot was stored; it is not a decision.", {"project_id": analysis.project_id, "evidence_count": len(analysis.evidence_ids), "interpretation_mode": analysis.interpretation_mode})
        return analysis

    def get_analysis(self, analysis_id, project_id=None):
        query, values = "SELECT * FROM api_analyses WHERE analysis_id = ?", [analysis_id]
        if project_id is not None: query += " AND project_id = ?"; values.append(project_id)
        row = self._connection.execute(query, values).fetchone()
        if not row: return None
        return StoredAPIAnalysis(row["analysis_id"], row["project_id"], row["created_at"], row["problem"], _load_mapping(row["report_json"]), _load_list(row["evidence_ids_json"]), _load_mapping(row["narrative_json"]) if row["narrative_json"] else None, row["responsible_ai"], row["interpretation_mode"])

    def list_analyses(self, project_id):
        if not self.get_project(project_id): raise ValueError("unknown project_id")
        rows = self._connection.execute("SELECT analysis_id FROM api_analyses WHERE project_id = ? ORDER BY created_at DESC, analysis_id DESC", (project_id,)).fetchall()
        return [self.get_analysis(row["analysis_id"], project_id) for row in rows]

    def list_briefs(self, project_id):
        if not self.get_project(project_id): raise ValueError("unknown project_id")
        rows = self._connection.execute("SELECT brief_id FROM decision_briefs WHERE subject_type = 'analysis' AND subject_id IN (SELECT analysis_id FROM api_analyses WHERE project_id = ?) ORDER BY brief_id", (project_id,)).fetchall()
        return [row["brief_id"] for row in rows]


class SQLiteAuthRepository:
    def __init__(self, connection, audit_events): self._connection,self._audit=connection,audit_events
    def audit(self,*args): self._audit.record(*args)
    def create_user(self,user):
        try:
            with _write_transaction(self._connection): self._connection.execute("INSERT INTO api_users VALUES (?,?,?,?,?,?,?)",(user.user_id,user.email,user.password_hash,user.display_name,int(user.is_active),user.created_at,user.last_login_at)); self._audit._record("user_created","user",user.user_id,"User account was created.",{})
        except sqlite3.IntegrityError as error: raise ValueError("email already exists") from error
        return user
    def _user(self,row): return User(row["user_id"],row["email"],row["password_hash"],row["display_name"],bool(row["is_active"]),row["created_at"],row["last_login_at"])
    def get_user_by_email(self,email):
        row=self._connection.execute("SELECT * FROM api_users WHERE email=?",(email,)).fetchone(); return self._user(row) if row else None
    def get_user(self,user_id):
        row=self._connection.execute("SELECT * FROM api_users WHERE user_id=?",(user_id,)).fetchone(); return self._user(row) if row else None
    def update_login(self,user_id): self._connection.execute("UPDATE api_users SET last_login_at=? WHERE user_id=?",(_timestamp(),user_id)); self._connection.commit()
    def update_password(self,user_id,password_hash): self._connection.execute("UPDATE api_users SET password_hash=? WHERE user_id=?",(password_hash,user_id)); self._connection.commit()
    def create_organisation(self,value): self._connection.execute("INSERT INTO api_organisations VALUES (?,?,?,?)",(value.organisation_id,value.name,value.description,value.created_at)); self._connection.commit(); return value
    def get_organisation(self,organisation_id):
        row=self._connection.execute("SELECT * FROM api_organisations WHERE organisation_id=?",(organisation_id,)).fetchone(); return Organisation(**dict(row)) if row else None
    def add_membership(self,value):
        if value.role not in ROLES: raise ValueError("unsupported role")
        self._connection.execute("INSERT INTO api_memberships VALUES (?,?,?,?)",(value.organisation_id,value.user_id,value.role,value.created_at)); self._connection.commit(); return value
    def list_memberships(self,organisation_id): return [Membership(**dict(row)) for row in self._connection.execute("SELECT * FROM api_memberships WHERE organisation_id=? ORDER BY user_id",(organisation_id,))]
    def has_owner(self): return bool(self._connection.execute("SELECT 1 FROM api_memberships WHERE role='owner' LIMIT 1").fetchone())
    def create_session(self,value): self._connection.execute("INSERT INTO api_sessions VALUES (?,?,?,?,?,?)",(value.session_id,value.user_id,value.token_hash,value.created_at,value.expires_at,value.revoked_at)); self._connection.commit()
    def resolve_session(self,digest):
        row=self._connection.execute("SELECT * FROM api_sessions WHERE token_hash=? AND revoked_at IS NULL AND expires_at>?",(digest,_timestamp())).fetchone(); return AuthSession(**dict(row)) if row else None
    def revoke_session(self,session_id): self._connection.execute("UPDATE api_sessions SET revoked_at=? WHERE session_id=?",(_timestamp(),session_id)); self._connection.commit()

class SQLitePersistenceStore(PersistenceStore):
    """Optional SQLite implementation of the persistence-store interface."""

    def __init__(
        self,
        database_path: Union[str, Path] = ":memory:",
    ) -> None:
        # FastAPI executes synchronous endpoints in worker threads; SQLite's
        # connection may therefore cross the application/request boundary.
        # Callers remain responsible for coordinating concurrent writes.
        self._connection = sqlite3.connect(str(database_path), check_same_thread=False)
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
        self.portfolios = SQLitePortfolioRepository(self._connection,self.historical,self.experiments,self.audit_events)
        self.scenarios = SQLiteScenarioRepository(self._connection,self.historical,self.audit_events)
        self.governance = SQLiteGovernanceRepository(self._connection,self.scenarios,self.audit_events)
        self.briefs = SQLiteDecisionBriefRepository(self._connection,self.audit_events)
        self.api_workspaces = SQLiteAPIWorkspaceRepository(self._connection, self.evidence, self.audit_events)
        self.auth = SQLiteAuthRepository(self._connection, self.audit_events)

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

    def save_portfolio(self, portfolio: ProgrammePortfolio): return self.portfolios.save(portfolio)
    def save_scenario(self, scenario: StrategicScenario): return self.scenarios.save(scenario)
    def save_evidence_pack(self, pack: EvidencePack): return self.briefs.save_pack(pack)
    def get_evidence_pack(self, pack_id): return self.briefs.get_pack(pack_id)
    def list_evidence_packs_by_subject(self, subject_type, subject_id): return self.briefs.list_packs(subject_type,subject_id)
    def save_decision_brief(self, brief: DecisionBrief): return self.briefs.save_brief(brief)
    def get_decision_brief(self, brief_id): return self.briefs.get_brief(brief_id)
    def list_decision_briefs_by_subject(self, subject_type, subject_id): return self.briefs.list_briefs(subject_type,subject_id)
    def list_decision_brief_versions(self, subject_type, subject_id): return self.briefs.list_briefs(subject_type,subject_id)
    def get_latest_decision_brief(self, subject_type, subject_id): return self.briefs.latest(subject_type,subject_id)
    def save_api_project(self, project): return self.api_workspaces.save_project(project)
    def get_api_project(self, project_id): return self.api_workspaces.get_project(project_id)
    def list_api_projects(self): return self.api_workspaces.list_projects()
    def link_api_project_evidence(self, project_id, evidence_id): return self.api_workspaces.link_evidence(project_id, evidence_id)
    def list_api_project_evidence(self, project_id): return self.api_workspaces.list_evidence(project_id)
    def save_api_analysis(self, analysis): return self.api_workspaces.save_analysis(analysis)
    def get_api_analysis(self, analysis_id, project_id=None): return self.api_workspaces.get_analysis(analysis_id, project_id)
    def list_api_analyses(self, project_id): return self.api_workspaces.list_analyses(project_id)
    def list_api_briefs(self, project_id): return self.api_workspaces.list_briefs(project_id)

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
                CREATE TABLE IF NOT EXISTS portfolios (
                    portfolio_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS strategic_scenarios (
                    scenario_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS governance_reviews (review_id TEXT PRIMARY KEY, subject_type TEXT NOT NULL, subject_id TEXT NOT NULL, payload_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS governance_decisions (decision_id TEXT PRIMARY KEY, subject_type TEXT NOT NULL, subject_id TEXT NOT NULL, payload_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS experiment_authorizations (authorization_id TEXT PRIMARY KEY, decision_id TEXT NOT NULL, scenario_id TEXT NOT NULL, payload_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS evidence_packs (pack_id TEXT PRIMARY KEY, subject_type TEXT NOT NULL, subject_id TEXT NOT NULL, payload_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS decision_briefs (brief_id TEXT PRIMARY KEY, subject_type TEXT NOT NULL, subject_id TEXT NOT NULL, brief_version INTEGER NOT NULL, payload_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS api_projects (
                    project_id TEXT PRIMARY KEY, name TEXT NOT NULL,
                    description TEXT, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS api_project_evidence (
                    project_id TEXT NOT NULL, evidence_id TEXT NOT NULL,
                    position INTEGER NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY (project_id, evidence_id), UNIQUE (project_id, position),
                    FOREIGN KEY (project_id) REFERENCES api_projects(project_id),
                    FOREIGN KEY (evidence_id) REFERENCES evidence_records(evidence_id)
                );
                CREATE TABLE IF NOT EXISTS api_analyses (
                    analysis_id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
                    created_at TEXT NOT NULL, problem TEXT NOT NULL, report_json TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL, narrative_json TEXT,
                    responsible_ai TEXT NOT NULL, interpretation_mode TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES api_projects(project_id)
                );
                CREATE TABLE IF NOT EXISTS api_users (user_id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, display_name TEXT NOT NULL, is_active INTEGER NOT NULL, created_at TEXT NOT NULL, last_login_at TEXT);
                CREATE TABLE IF NOT EXISTS api_organisations (organisation_id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS api_memberships (organisation_id TEXT NOT NULL, user_id TEXT NOT NULL, role TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY (organisation_id,user_id), FOREIGN KEY (organisation_id) REFERENCES api_organisations(organisation_id), FOREIGN KEY (user_id) REFERENCES api_users(user_id));
                CREATE TABLE IF NOT EXISTS api_sessions (session_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, token_hash TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL, expires_at TEXT NOT NULL, revoked_at TEXT, FOREIGN KEY (user_id) REFERENCES api_users(user_id));
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
