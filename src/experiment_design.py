"""
OpenSocial AI – Experiment Design

Turns innovation hypotheses into small, transparent pilot designs.

An experiment design is not an approval to implement an intervention.
It records the evidence, uncertainty, safeguards, and human questions
that should guide a decision to test a hypothesis.
"""

from dataclasses import asdict, dataclass, field, replace
import hashlib
import json
from typing import Dict, List, Optional


try:
    from src.innovation_reasoning import InnovationHypothesis
except ModuleNotFoundError:
    from innovation_reasoning import InnovationHypothesis


@dataclass
class ExperimentDesign:
    """A structured, small-scale design for testing a hypothesis."""

    experiment_id: str
    title: str
    hypothesis_title: str
    objective: str
    intervention: str
    comparison: str
    measures: List[str]
    evidence_basis: List[str]
    uncertainty: List[str]
    safeguards: List[str]
    stop_conditions: List[str]
    validation_question: str
    analysis_evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Return the experiment design as a dictionary."""

        return asdict(self)

    def with_analysis_evidence_ids(
        self,
        evidence_ids: List[str],
    ) -> "ExperimentDesign":
        """Return a copy linked to the persisted analysis evidence corpus."""

        return replace(
            self,
            analysis_evidence_ids=list(evidence_ids),
        )


class ExperimentDesignEngine:
    """Create cautious pilot designs from innovation hypotheses."""

    def design(
        self,
        hypotheses: Optional[List[InnovationHypothesis]] = None,
    ) -> List[ExperimentDesign]:
        """Create one small-scale experiment design per hypothesis."""

        hypotheses = hypotheses or []

        for hypothesis in hypotheses:
            if not isinstance(hypothesis, InnovationHypothesis):
                raise TypeError(
                    "All hypotheses must be instances of "
                    "InnovationHypothesis."
                )

        return [
            self._build_design(hypothesis)
            for hypothesis in hypotheses
        ]

    @staticmethod
    def _build_design(
        hypothesis: InnovationHypothesis,
    ) -> ExperimentDesign:
        """Build a transparent design without claiming effectiveness."""

        uncertainty = list(hypothesis.uncertainty)
        uncertainty.append(
            "A small pilot cannot establish long-term effectiveness "
            "or suitability in other contexts."
        )

        return ExperimentDesign(
            experiment_id=ExperimentDesignEngine._experiment_id(
                hypothesis
            ),
            title=f"Pilot: {hypothesis.title}",
            hypothesis_title=hypothesis.title,
            objective=(
                "Test whether the proposed mechanism can be delivered "
                "safely and appears useful in the target context."
            ),
            intervention=hypothesis.experiment,
            comparison=(
                "Compare the pilot with the current approach or a "
                "clearly documented baseline where this is appropriate."
            ),
            measures=[
                "A pre-defined engagement, access, or outcome measure.",
                "Participant and community feedback on feasibility and harm.",
                "Implementation fidelity and unexpected effects.",
            ],
            evidence_basis=list(hypothesis.evidence_basis),
            uncertainty=uncertainty,
            safeguards=[
                "Obtain appropriate organisational and community approval "
                "before starting.",
                "Involve affected people in reviewing the pilot design.",
                "Collect only the minimum information needed to learn safely.",
            ],
            stop_conditions=[
                "Stop or adapt the pilot if credible harm or exclusion is observed.",
                "Stop or adapt if implementation conditions make the results "
                "uninterpretable.",
                "Do not scale without human review of the observed results.",
            ],
            validation_question=hypothesis.validation_question,
        )

    @staticmethod
    def _experiment_id(
        hypothesis: InnovationHypothesis,
    ) -> str:
        """Create a stable identifier from the complete tested hypothesis."""

        identity = json.dumps(
            hypothesis.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()

        return f"experiment-{digest}"
