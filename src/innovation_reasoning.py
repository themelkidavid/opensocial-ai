"""
OpenSocial AI – Innovation Reasoning Engine

Version 1.0

Generates innovation hypotheses from identified innovation
opportunities.

The engine uses transparent reasoning strategies rather than
claiming that generated ideas are proven solutions.

Reasoning strategies include:
- cross-domain transfer
- historical solution revival
- novel combination
- constraint inversion
- pattern combination

The output is intended for human investigation and experimentation.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class InnovationHypothesis:
    title: str
    problem_connection: str
    inspiration_source: str
    underlying_mechanism: str
    novel_combination: str
    why_it_might_work: str
    evidence_basis: List[str]
    confidence: str
    uncertainty: List[str]
    experiment: str
    validation_question: str

    def to_dict(self) -> Dict:
        return asdict(self)


class InnovationReasoningEngine:

    def generate(
        self,
        problem: str,
        opportunities: Optional[List] = None,
    ) -> List[InnovationHypothesis]:

        if not problem or not problem.strip():
            raise ValueError(
                "problem cannot be empty"
            )

        opportunities = opportunities or []

        if not opportunities:
            return []

        hypotheses = []

        for opportunity in opportunities:

            opportunity_type = getattr(
                opportunity,
                "opportunity_type",
                "unknown",
            )

            if opportunity_type == "emerging_pattern":
                hypotheses.append(
                    self._generate_transfer_hypothesis(
                        problem,
                        opportunity,
                    )
                )

            elif opportunity_type == "evidence_gap":
                hypotheses.append(
                    self._generate_evidence_hypothesis(
                        problem,
                        opportunity,
                    )
                )

            elif opportunity_type == "contradiction":
                hypotheses.append(
                    self._generate_context_hypothesis(
                        problem,
                        opportunity,
                    )
                )

            elif opportunity_type == "transfer_opportunity":
                hypotheses.append(
                    self._generate_transfer_hypothesis(
                        problem,
                        opportunity,
                    )
                )

            elif opportunity_type == "unmet_need":
                hypotheses.append(
                    self._generate_need_hypothesis(
                        problem,
                        opportunity,
                    )
                )

        return hypotheses

    def _generate_transfer_hypothesis(
        self,
        problem: str,
        opportunity,
    ) -> InnovationHypothesis:

        description = getattr(
            opportunity,
            "description",
            "A promising pattern was identified.",
        )

        evidence_basis = getattr(
            opportunity,
            "evidence_basis",
            [],
        )

        uncertainty = list(
            getattr(
                opportunity,
                "uncertainty",
                [],
            )
        )

        uncertainty.append(
            "The transferred mechanism may not work "
            "under the same conditions as the original context."
        )

        return InnovationHypothesis(
            title="Adapt a proven mechanism to the current problem",
            problem_connection=problem,
            inspiration_source=(
                "cross-domain transfer from an observed "
                "innovation opportunity"
            ),
            underlying_mechanism=(
                "Use the mechanism behind the observed pattern "
                "rather than copying the original intervention "
                "exactly, and adapt it to the current context."
            ),
            novel_combination=(
                "Combine the observed mechanism with the "
                "needs and constraints of the current problem."
            ),
            why_it_might_work=(
                f"The opportunity suggests that {description} "
                "may contain a useful mechanism that could be "
                "adapted to this problem."
            ),
            evidence_basis=list(evidence_basis),
            confidence=getattr(
                opportunity,
                "confidence",
                "exploratory",
            ),
            uncertainty=uncertainty,
            experiment=(
                "Run a small, low-cost pilot adapting the "
                "identified mechanism to the target population "
                "and compare outcomes with the existing approach."
            ),
            validation_question=(
                "Does the underlying mechanism remain effective "
                "when adapted to this problem and context?"
            ),
        )

    def _generate_evidence_hypothesis(
        self,
        problem: str,
        opportunity,
    ) -> InnovationHypothesis:

        evidence_basis = getattr(
            opportunity,
            "evidence_basis",
            [],
        )

        uncertainty = list(
            getattr(
                opportunity,
                "uncertainty",
                [],
            )
        )

        uncertainty.append(
            "The innovation direction may change as the "
            "missing evidence becomes available."
        )

        return InnovationHypothesis(
            title="Strengthen evidence before designing at scale",
            problem_connection=problem,
            inspiration_source=(
                "evidence-gap analysis"
            ),
            underlying_mechanism=(
                "Generate better innovation hypotheses by "
                "collecting information about the missing "
                "population, context, outcomes or implementation "
                "conditions."
            ),
            novel_combination=(
                "Combine structured evidence collection with "
                "community insight to identify previously hidden "
                "needs or intervention possibilities."
            ),
            why_it_might_work=(
                "The identified evidence gap may be hiding an "
                "important barrier, unmet need or difference "
                "between population groups."
            ),
            evidence_basis=list(evidence_basis),
            confidence="low",
            uncertainty=uncertainty,
            experiment=(
                "Conduct a focused evidence-gathering exercise "
                "with affected communities and compare the "
                "findings with existing programme data."
            ),
            validation_question=(
                "What additional evidence would most change "
                "our understanding of the problem?"
            ),
        )

    def _generate_context_hypothesis(
        self,
        problem: str,
        opportunity,
    ) -> InnovationHypothesis:

        evidence_basis = getattr(
            opportunity,
            "evidence_basis",
            [],
        )

        uncertainty = list(
            getattr(
                opportunity,
                "uncertainty",
                [],
            )
        )

        uncertainty.append(
            "The disagreement may reflect differences in "
            "context rather than a universally different outcome."
        )

        return InnovationHypothesis(
            title="Design for different implementation contexts",
            problem_connection=problem,
            inspiration_source=(
                "contradictory evidence across comparable contexts"
            ),
            underlying_mechanism=(
                "Identify the contextual conditions under which "
                "an intervention produces different outcomes, "
                "including population, measurement, location and "
                "implementation conditions."
            ),
            novel_combination=(
                "Combine the intervention with context-specific "
                "delivery conditions instead of applying one "
                "standard model everywhere."
            ),
            why_it_might_work=(
                "Conflicting evidence may indicate that the "
                "intervention works differently under different "
                "conditions."
            ),
            evidence_basis=list(evidence_basis),
            confidence="low",
            uncertainty=uncertainty,
            experiment=(
                "Compare a small pilot across two contrasting "
                "contexts while keeping the core intervention "
                "consistent."
            ),
            validation_question=(
                "Which contextual conditions explain the different "
                "outcomes, and can the intervention be adapted "
                "accordingly?"
            ),
        )

    def _generate_need_hypothesis(
        self,
        problem: str,
        opportunity,
    ) -> InnovationHypothesis:

        evidence_basis = getattr(
            opportunity,
            "evidence_basis",
            [],
        )

        uncertainty = list(
            getattr(
                opportunity,
                "uncertainty",
                [],
            )
        )

        uncertainty.append(
            "The unmet need may have multiple underlying causes."
        )

        return InnovationHypothesis(
            title="Design around the identified unmet need",
            problem_connection=problem,
            inspiration_source=(
                "identified unmet need"
            ),
            underlying_mechanism=(
                "Address the underlying need directly rather "
                "than assuming the existing service model is "
                "the only possible delivery approach."
            ),
            novel_combination=(
                "Combine community knowledge with an alternative "
                "service-delivery mechanism."
            ),
            why_it_might_work=(
                "The opportunity suggests that the current "
                "approach may not fully address the needs of "
                "the affected population."
            ),
            evidence_basis=list(evidence_basis),
            confidence="exploratory",
            uncertainty=uncertainty,
            experiment=(
                "Co-design a small alternative intervention "
                "with affected community members and test it "
                "against the existing approach."
            ),
            validation_question=(
                "Does addressing the underlying need directly "
                "produce better engagement or outcomes?"
            ),
        )