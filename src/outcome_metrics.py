"""Structured outcome measurement and cautious experiment comparison."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
import json


_TYPES = {"count", "percentage", "rate", "duration", "score", "boolean", "categorical"}


@dataclass
class OutcomeMetric:
    name: str
    description: str
    metric_type: str
    unit: str
    measurement_method: str
    metric_id: Optional[str] = None
    direction: Optional[str] = None
    baseline_value: Optional[Any] = None
    target_value: Optional[Any] = None
    source: Optional[str] = None
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

    def validated(self) -> "OutcomeMetric":
        for name in ("name", "description", "metric_type", "unit", "measurement_method"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"metric {name} cannot be empty")
        if self.metric_type not in _TYPES:
            raise ValueError("unsupported metric_type")
        if self.direction is not None and self.direction not in {"increase", "decrease", "neutral"}:
            raise ValueError("metric direction must be increase, decrease, neutral, or None")
        if not isinstance(self.limitations, list) or not all(isinstance(x, str) and x.strip() for x in self.limitations):
            raise ValueError("metric limitations must contain non-empty strings")
        for value in (self.baseline_value, self.target_value):
            if value is not None:
                _validate_value(self.metric_type, value)
        payload = self.to_dict()
        metric_id = self.metric_id or _stable_id("metric", payload)
        return OutcomeMetric(self.name.strip(), self.description.strip(), self.metric_type,
                             self.unit.strip(), self.measurement_method.strip(), metric_id,
                             self.direction, self.baseline_value, self.target_value,
                             self.source.strip() if isinstance(self.source, str) and self.source.strip() else None,
                             [x.strip() for x in self.limitations])


@dataclass
class OutcomeObservation:
    experiment_id: str
    metric_id: str
    value: Any
    evidence_source: str
    reviewer: str
    observation_id: Optional[str] = None
    measured_at: Optional[str] = None
    population: Optional[str] = None
    sample_information: Optional[str] = None
    measurement_period: Optional[str] = None
    measurement_method: Optional[str] = None
    context: Optional[str] = None
    limitations: List[str] = field(default_factory=list)
    provenance: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    def validated(self, metric: OutcomeMetric) -> "OutcomeObservation":
        for name in ("experiment_id", "metric_id", "evidence_source", "reviewer"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"outcome observation {name} cannot be empty")
        _validate_value(metric.metric_type, self.value)
        if not isinstance(self.limitations, list) or not all(isinstance(x, str) and x.strip() for x in self.limitations):
            raise ValueError("outcome observation limitations must contain non-empty strings")
        if self.measured_at is not None:
            try:
                datetime.fromisoformat(self.measured_at.replace("Z", "+00:00"))
            except (TypeError, ValueError) as error:
                raise ValueError("measured_at must be an ISO timestamp") from error
        payload = self.to_dict()
        observation_id = self.observation_id or _stable_id("outcome-observation", payload)
        return OutcomeObservation(self.experiment_id.strip(), self.metric_id.strip(), self.value,
            self.evidence_source.strip(), self.reviewer.strip(), observation_id, self.measured_at,
            _clean(self.population), _clean(self.sample_information), _clean(self.measurement_period),
            _clean(self.measurement_method), _clean(self.context), [x.strip() for x in self.limitations], _clean(self.provenance))


@dataclass
class ExperimentComparison:
    experiment_a_id: str
    experiment_b_id: str
    metric_id: str
    value_a: Any
    value_b: Any
    unit: str
    absolute_difference: Optional[float]
    relative_difference: Optional[float]
    warnings: List[str]
    uncertainty: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


class ComparativeLearningEngine:
    """Compare supplied measurements; never ranks interventions or infers causality."""

    def compare(self, metric: OutcomeMetric, observation_a: OutcomeObservation,
                observation_b: OutcomeObservation) -> ExperimentComparison:
        metric = metric.validated()
        a, b = observation_a.validated(metric), observation_b.validated(metric)
        if a.metric_id != metric.metric_id or b.metric_id != metric.metric_id:
            raise ValueError("outcome observations must reference the comparison metric_id")
        warnings = []
        for field, warning in (("population", "Different populations were measured."),
                               ("measurement_period", "Measurement periods differ."),
                               ("measurement_method", "Measurement methods differ."),
                               ("context", "Contexts differ.")):
            left, right = getattr(a, field), getattr(b, field)
            if left and right and left != right:
                warnings.append(warning)
        if metric.baseline_value is None:
            warnings.append("Baseline values are unavailable.")
        absolute = relative = None
        if _numeric(metric.metric_type):
            absolute = float(a.value) - float(b.value)
            if float(b.value) != 0:
                relative = absolute / float(b.value)
            else:
                warnings.append("Relative difference is unavailable because the comparison value is zero.")
        else:
            warnings.append("Values are not mathematically comparable for this metric type.")
        return ExperimentComparison(a.experiment_id, b.experiment_id, metric.metric_id,
            a.value, b.value, metric.unit, absolute, relative, warnings,
            ["Comparison describes recorded observations only; it does not establish causality, effectiveness, or a best intervention."])

    @staticmethod
    def change_from_baseline(metric: OutcomeMetric, observation: OutcomeObservation) -> Dict[str, Optional[float]]:
        metric = metric.validated(); observation.validated(metric)
        if not _numeric(metric.metric_type) or metric.baseline_value is None:
            return {"absolute_change": None, "percentage_change": None}
        absolute = float(observation.value) - float(metric.baseline_value)
        return {"absolute_change": absolute, "percentage_change": absolute / float(metric.baseline_value) if float(metric.baseline_value) else None}


def _validate_value(metric_type: str, value: Any) -> None:
    if metric_type in {"count", "percentage", "rate", "duration", "score"}:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("numeric metric value must be a number")
        if metric_type in {"count", "duration"} and value < 0:
            raise ValueError(f"{metric_type} value cannot be negative")
        if metric_type in {"percentage", "rate"} and not 0 <= value <= 100:
            raise ValueError(f"{metric_type} value must be between 0 and 100")
    elif metric_type == "boolean" and not isinstance(value, bool):
        raise ValueError("boolean metric value must be true or false")
    elif metric_type == "categorical" and (not isinstance(value, str) or not value.strip()):
        raise ValueError("categorical metric value must be non-empty text")


def _numeric(metric_type: str) -> bool:
    return metric_type in {"count", "percentage", "rate", "duration", "score"}


def _stable_id(prefix: str, value: Dict) -> str:
    return f"{prefix}-{hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()[:24]}"


def _clean(value: Optional[str]) -> Optional[str]:
    return value.strip() if isinstance(value, str) and value.strip() else None
