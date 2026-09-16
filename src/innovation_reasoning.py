"""
OpenSocial AI – Innovation Reasoning Engine

Version 1.1

Generates innovation hypotheses from identified innovation
opportunities and relevant sources of inspiration.

Reasoning inputs may include:
- innovation opportunities
- cross-sector inspiration
- historical approaches
- community innovations
- research approaches
- international examples

The engine does not claim that generated ideas are proven.

Instead, it creates transparent hypotheses that connect:
    problem
        ↓
    opportunity
        ↓
    inspiration
        ↓
    mechanism
        ↓
    adaptation
        ↓
    experiment
        ↓
    human validation
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


try:
    from src.innovation_combination import (
        InnovationCombination,
        InnovationCombinationEngine,
    )
    from src.innovation_inspiration import (
        InnovationInspiration,
        InnovationInspirationEngine,
    )
    from src.retrieval import RelevanceRetriever
except ModuleNotFoundError:
    from innovation_combination import (
        InnovationCombination,
        InnovationCombinationEngine,
    )
    from innovation_inspiration import (
        InnovationInspiration,
        InnovationInspirationEngine,
    )
    from retrieval import RelevanceRetriever


@dataclass
class InnovationHypothesis:
    """A potential innovation idea requiring human validation."""

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
        """Return the hypothesis as a dictionary."""

        return asdict(self)


class InnovationReasoningEngine:
    """
    Generates transparent innovation hypotheses.

    The engine can reason from innovation opportunities alone,
    or combine opportunities with relevant inspiration sources.
    """

    def __init__(
        self,
        retriever: Optional[RelevanceRetriever] = None,
    ) -> None:
        """Initialise retrieval and combination components."""

        self.inspiration_engine = (
            InnovationInspirationEngine(retriever=retriever)
        )
        self.combination_engine = (
            InnovationCombinationEngine()
        )

    def generate(
        self,
        problem: str,
        opportunities: Optional[List] = None,
        inspirations: Optional[
            List[InnovationInspiration]
        ] = None,
    ) -> List[InnovationHypothesis]:
        """
        Generate innovation hypotheses.

        If inspiration sources are supplied, relevant sources
        are identified and incorporated into the reasoning.

        If no inspiration is supplied, the engine can still
        generate hypotheses directly from opportunities.
        """

        if not problem or not problem.strip():
            raise ValueError(
                "problem cannot be empty"
            )

        opportunities = opportunities or []
        inspirations = inspirations or []

        if not opportunities:
            return []

        self._validate_inspirations(
            inspirations
        )

        relevant_inspirations = []

        if inspirations:
            relevant_inspirations = (
                self.inspiration_engine.find_relevant(
                    problem=problem,
                    inspirations=inspirations,
                )
            )

        hypotheses = []

        for opportunity in opportunities:

            opportunity_type = getattr(
                opportunity,
                "opportunity_type",
                "unknown",
            )

            if self._can_combine(
                opportunity_type,
                opportunity,
                relevant_inspirations,
            ):
                combinations = self.combination_engine.combine(
                    problem=problem,
                    opportunity=opportunity,
                    inspirations=relevant_inspirations,
                )

                if combinations:
                    hypotheses.append(
                        self._generate_combination_hypothesis(
                            problem,
                            opportunity,
                            combinations[0],
                        )
                    )
                    continue

            if opportunity_type == "emerging_pattern":
                hypotheses.append(
                    self._generate_transfer_hypothesis(
                        problem,
                        opportunity,
                        relevant_inspirations,
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
                        relevant_inspirations,
                    )
                )

            elif opportunity_type == "unmet_need":
                hypotheses.append(
                    self._generate_need_hypothesis(
                        problem,
                        opportunity,
                        relevant_inspirations,
                    )
                )

        return hypotheses

    @staticmethod
    def _can_combine(
        opportunity_type: str,
        opportunity,
        relevant_inspirations: List[InnovationInspiration],
    ) -> bool:
        """Return whether the available basis supports a combination."""

        if opportunity_type not in {
            "emerging_pattern",
            "transfer_opportunity",
        }:
            return False

        evidence_basis = getattr(
            opportunity,
            "evidence_basis",
            [],
        )

        return (
            isinstance(evidence_basis, list)
            and len(evidence_basis) >= 2
            and len(relevant_inspirations) >= 2
        )

    def _generate_combination_hypothesis(
        self,
        problem: str,
        opportunity,
        combination: InnovationCombination,
    ) -> InnovationHypothesis:
        """Convert a combination-engine result into a hypothesis."""

        evidence_basis = list(
            getattr(
                opportunity,
                "evidence_basis",
                [],
            )
        )
        evidence_basis.extend(
            [
                f"Inspiration source: {combination.inspiration_a}",
                f"Inspiration source: {combination.inspiration_b}",
            ]
        )

        uncertainty = list(
            getattr(
                opportunity,
                "uncertainty",
                [],
            )
        )
        uncertainty.extend(combination.uncertainty)

        return InnovationHypothesis(
            title=combination.title,
            problem_connection=problem,
            inspiration_source=(
                f"combined inspirations: "
                f"{combination.inspiration_a}; "
                f"{combination.inspiration_b}"
            ),
            underlying_mechanism=combination.combined_mechanism,
            novel_combination=combination.description,
            why_it_might_work=combination.rationale,
            evidence_basis=evidence_basis,
            confidence=getattr(
                opportunity,
                "confidence",
                "exploratory",
            ),
            uncertainty=uncertainty,
            experiment=combination.experiment,
            validation_question=combination.validation_question,
        )

    def _generate_transfer_hypothesis(
        self,
        problem: str,
        opportunity,
        relevant_inspirations: Optional[
            List[InnovationInspiration]
        ] = None,
    ) -> InnovationHypothesis:
        """
        Generate a transfer-oriented hypothesis.

        When relevant inspiration exists, use its mechanism
        as an explicit source for adaptation.
        """

        relevant_inspirations = (
            relevant_inspirations or []
        )

        description = getattr(
            opportunity,
            "description",
            "A promising pattern was identified.",
        )

        evidence_basis = list(
            getattr(
                opportunity,
                "evidence_basis",
                [],
            )
        )

        uncertainty = list(
            getattr(
                opportunity,
                "uncertainty",
                [],
            )
        )

        if relevant_inspirations:

            inspiration = (
                relevant_inspirations[0]
            )

            inspiration_source = (
                f"{inspiration.source_type} inspiration: "
                f"{inspiration.title}"
            )

            underlying_mechanism = (
                f"Adapt the mechanism used in "
                f"'{inspiration.title}': "
                f"{inspiration.mechanism}"
            )

            novel_combination = (
                f"Combine the mechanism from "
                f"'{inspiration.title}' with the "
                f"needs, constraints and context of "
                f"the current problem."
            )

            why_it_might_work = (
                f"The observed opportunity suggests that "
                f"{description} The inspiration source reports "
                f"the following observed result: "
                f"{inspiration.observed_result}"
            )

            if inspiration.adaptation_notes:
                novel_combination += (
                    f" Adaptation consideration: "
                    f"{inspiration.adaptation_notes}"
                )

            evidence_basis.append(
                f"Inspiration source: {inspiration.title}"
            )

            evidence_basis.append(
                f"Observed result from inspiration: "
                f"{inspiration.observed_result}"
            )

            uncertainty.append(
                "The inspiration source may not transfer "
                "successfully to the target context."
            )

            uncertainty.append(
                "Observed results from another context "
                "do not establish effectiveness here."
            )

        else:

            inspiration_source = (
                "cross-domain transfer from an observed "
                "innovation opportunity"
            )

            underlying_mechanism = (
                "Use the mechanism behind the observed "
                "pattern rather than copying the original "
                "intervention exactly, and adapt it to the "
                "current context."
            )

            novel_combination = (
                "Combine the observed mechanism through cross-domain "
                "transfer with the "
                "needs and constraints of the current problem."
            )

            why_it_might_work = (
                f"The opportunity suggests that "
                f"{description} may contain a useful "
                "mechanism that could be adapted to this problem."
            )

            evidence_basis.append(
                "No external inspiration source was supplied."
            )

            uncertainty.append(
                "The transferred mechanism may not work "
                "under the same conditions as the original context."
            )

        return InnovationHypothesis(
            title=(
                "Adapt an existing mechanism "
                "to the current problem"
            ),
            problem_connection=problem,
            inspiration_source=inspiration_source,
            underlying_mechanism=underlying_mechanism,
            novel_combination=novel_combination,
            why_it_might_work=why_it_might_work,
            evidence_basis=evidence_basis,
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
        """Generate a hypothesis focused on strengthening evidence."""

        evidence_basis = list(
            getattr(
                opportunity,
                "evidence_basis",
                [],
            )
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
            title=(
                "Strengthen evidence before "
                "designing at scale"
            ),
            problem_connection=problem,
            inspiration_source=(
                "evidence-gap analysis"
            ),
            underlying_mechanism=(
                "Generate better innovation hypotheses through "
                "evidence collection about the missing "
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
            evidence_basis=evidence_basis,
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
        """Generate a hypothesis from contradictory evidence."""

        evidence_basis = list(
            getattr(
                opportunity,
                "evidence_basis",
                [],
            )
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
            title=(
                "Design for different "
                "implementation contexts"
            ),
            problem_connection=problem,
            inspiration_source=(
                "contradictory evidence across "
                "comparable contexts"
            ),
            underlying_mechanism=(
                "Identify the contextual conditions under which "
                "an intervention produces different outcomes, "
                "including population, measurement, location "
                "and implementation conditions."
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
            evidence_basis=evidence_basis,
            confidence="low",
            uncertainty=uncertainty,
            experiment=(
                "Compare a small pilot across two contrasting "
                "contexts while keeping the core intervention "
                "consistent."
            ),
            validation_question=(
                "Which contextual conditions explain the "
                "different outcomes, and can the intervention "
                "be adapted accordingly?"
            ),
        )

    def _generate_need_hypothesis(
        self,
        problem: str,
        opportunity,
        relevant_inspirations: Optional[
            List[InnovationInspiration]
        ] = None,
    ) -> InnovationHypothesis:
        """Generate a hypothesis from an identified unmet need."""

        relevant_inspirations = (
            relevant_inspirations or []
        )

        evidence_basis = list(
            getattr(
                opportunity,
                "evidence_basis",
                [],
            )
        )

        uncertainty = list(
            getattr(
                opportunity,
                "uncertainty",
                [],
            )
        )

        if relevant_inspirations:

            inspiration = (
                relevant_inspirations[0]
            )

            inspiration_source = (
                f"{inspiration.source_type} inspiration: "
                f"{inspiration.title}"
            )

            underlying_mechanism = (
                f"Use and adapt the mechanism from "
                f"'{inspiration.title}': "
                f"{inspiration.mechanism}"
            )

            novel_combination = (
                f"Combine the identified unmet need with "
                f"the mechanism from '{inspiration.title}' "
                "and adapt it to the local context."
            )

            evidence_basis.append(
                f"Inspiration source: {inspiration.title}"
            )

            uncertainty.append(
                "The inspiration may not transfer successfully "
                "to the target population."
            )

        else:

            inspiration_source = (
                "identified unmet need"
            )

            underlying_mechanism = (
                "Address the underlying need directly rather "
                "than assuming the existing service model is "
                "the only possible delivery approach."
            )

            novel_combination = (
                "Combine community knowledge with an "
                "alternative service-delivery mechanism."
            )

        uncertainty.append(
            "The unmet need may have multiple "
            "underlying causes."
        )

        return InnovationHypothesis(
            title=(
                "Design around the identified "
                "unmet need"
            ),
            problem_connection=problem,
            inspiration_source=inspiration_source,
            underlying_mechanism=underlying_mechanism,
            novel_combination=novel_combination,
            why_it_might_work=(
                "The opportunity suggests that the current "
                "approach may not fully address the needs of "
                "the affected population."
            ),
            evidence_basis=evidence_basis,
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

    @staticmethod
    def _validate_inspirations(
        inspirations: List[InnovationInspiration],
    ) -> None:
        """Validate supplied inspiration records."""

        for inspiration in inspirations:

            if not isinstance(
                inspiration,
                InnovationInspiration,
            ):
                raise TypeError(
                    "All inspirations must be instances "
                    "of InnovationInspiration."
                )
