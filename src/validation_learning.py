"""
OpenSocial AI – Validation and Learning

Records human-reviewed observations from experiments. This module does
not infer that an intervention is proven: each learning record remains
exploratory and must be interpreted in its local context.
"""

from dataclasses import asdict, dataclass
from typing import Dict, List, Optional


@dataclass
class ValidationObservation:
    """A human-reviewed observation from a completed or active pilot."""

    experiment_id: str
    experiment_title: str
    outcome: str
    evidence_basis: List[str]
    limitations: List[str]
    reviewer: str

    def to_dict(self) -> Dict:
        """Return the observation as a dictionary."""

        return asdict(self)


@dataclass
class ValidatedLearning:
    """A cautious learning record derived from a reviewed observation."""

    experiment_id: str
    experiment_title: str
    observed_outcome: str
    evidence_basis: List[str]
    limitations: List[str]
    reviewer: str
    learning: str
    confidence: str
    next_step: str

    def to_dict(self) -> Dict:
        """Return the learning record as a dictionary."""

        return asdict(self)


class ValidationLearningEngine:
    """Create auditable, exploratory learning from reviewed observations."""

    def create_observation(
        self,
        experiment_id: str,
        experiment_title: str,
        outcome: str,
        evidence_basis: Optional[List[str]] = None,
        limitations: Optional[List[str]] = None,
        reviewer: str = "",
    ) -> ValidationObservation:
        """Create a validated human-reviewed observation record."""

        evidence_basis = (
            evidence_basis
            if evidence_basis is not None
            else []
        )
        limitations = (
            limitations
            if limitations is not None
            else []
        )

        observation = ValidationObservation(
            experiment_id=experiment_id,
            experiment_title=experiment_title,
            outcome=outcome,
            evidence_basis=evidence_basis,
            limitations=limitations,
            reviewer=reviewer,
        )

        self._validate_observation(observation)

        return ValidationObservation(
            experiment_id=experiment_id.strip(),
            experiment_title=experiment_title.strip(),
            outcome=outcome.strip(),
            evidence_basis=[item.strip() for item in evidence_basis],
            limitations=[item.strip() for item in limitations],
            reviewer=reviewer.strip(),
        )

    def evaluate(
        self,
        observations: Optional[List[ValidationObservation]] = None,
    ) -> List[ValidatedLearning]:
        """Convert reviewed observations into cautious learning records."""

        observations = observations or []

        for observation in observations:
            self.validate_observation(observation)

        return [
            self._build_learning(observation)
            for observation in observations
        ]

    def evaluate_outcome(
        self,
        outcome_observation,
        metric,
        experiment_title: str,
    ) -> ValidatedLearning:
        """Turn one reviewed measurement into cautious, non-causal learning."""

        from src.outcome_metrics import OutcomeObservation, OutcomeMetric

        if not isinstance(outcome_observation, OutcomeObservation):
            raise TypeError("outcome_observation must be an OutcomeObservation")
        if not isinstance(metric, OutcomeMetric):
            raise TypeError("metric must be an OutcomeMetric")
        outcome_observation = outcome_observation.validated(metric.validated())
        observation = self.create_observation(
            outcome_observation.experiment_id,
            experiment_title,
            f"The pilot recorded {outcome_observation.value} {metric.unit} for {metric.name}.",
            [outcome_observation.evidence_source],
            limitations=list(outcome_observation.limitations) + [
                "A recorded metric change may warrant further testing but does not establish causality or effectiveness."
            ],
            reviewer=outcome_observation.reviewer,
        )
        return self.evaluate([observation])[0]

    @staticmethod
    def _build_learning(
        observation: ValidationObservation,
    ) -> ValidatedLearning:
        """Keep learning local, auditable, and explicitly non-conclusive."""

        limitations = list(observation.limitations)
        limitations.append(
            "This observation does not establish that the intervention "
            "will work in other settings or at larger scale."
        )

        return ValidatedLearning(
            experiment_id=observation.experiment_id,
            experiment_title=observation.experiment_title,
            observed_outcome=observation.outcome,
            evidence_basis=list(observation.evidence_basis),
            limitations=limitations,
            reviewer=observation.reviewer,
            learning=(
                "The reported outcome is a human-reviewed learning signal "
                "that should inform further investigation, adaptation, or "
                "a cautious follow-up test."
            ),
            confidence="exploratory",
            next_step=(
                "Review the observation with affected communities and "
                "decide whether to stop, adapt, gather more evidence, or "
                "run another bounded experiment."
            ),
        )

    @staticmethod
    def validate_observation(
        observation: ValidationObservation,
    ) -> None:
        """Validate every observation before it can become learning."""

        if not isinstance(observation, ValidationObservation):
            raise TypeError(
                "All observations must be instances of "
                "ValidationObservation."
            )

        for field_name in (
            "experiment_id",
            "experiment_title",
            "outcome",
            "reviewer",
        ):
            value = getattr(observation, field_name)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{field_name} cannot be empty"
                )

        if (
            not isinstance(observation.evidence_basis, list)
            or not observation.evidence_basis
            or not all(
                isinstance(item, str) and item.strip()
                for item in observation.evidence_basis
            )
        ):
            raise ValueError(
                "evidence_basis must contain non-empty strings"
            )

        if (
            not isinstance(observation.limitations, list)
            or not all(
                isinstance(item, str) and item.strip()
                for item in observation.limitations
            )
        ):
            raise ValueError(
                "limitations must contain non-empty strings"
            )

    @staticmethod
    def validate_learning(
        learning: ValidatedLearning,
    ) -> None:
        """Validate learning before it can be persisted as exploratory."""

        if not isinstance(learning, ValidatedLearning):
            raise TypeError(
                "All learning records must be instances of "
                "ValidatedLearning."
            )

        for field_name in (
            "experiment_id",
            "experiment_title",
            "observed_outcome",
            "reviewer",
            "learning",
            "confidence",
            "next_step",
        ):
            value = getattr(learning, field_name)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{field_name} cannot be empty"
                )

        if learning.confidence != "exploratory":
            raise ValueError(
                "learning confidence must remain exploratory"
            )

        if (
            not isinstance(learning.evidence_basis, list)
            or not learning.evidence_basis
            or not all(
                isinstance(item, str) and item.strip()
                for item in learning.evidence_basis
            )
        ):
            raise ValueError(
                "evidence_basis must contain non-empty strings"
            )

        if (
            not isinstance(learning.limitations, list)
            or not learning.limitations
            or not all(
                isinstance(item, str) and item.strip()
                for item in learning.limitations
            )
        ):
            raise ValueError(
                "limitations must contain non-empty strings"
            )

        if not any(
            "does not establish" in item.lower()
            for item in learning.limitations
        ):
            raise ValueError(
                "learning limitations must preserve the non-generalization safeguard"
            )

    _validate_observation = validate_observation
