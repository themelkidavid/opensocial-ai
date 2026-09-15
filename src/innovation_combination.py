"""
OpenSocial AI – Innovation Combination Engine

Version 1.0

Combines multiple innovation inspirations into a
potentially novel solution mechanism.

The engine does not claim that a combination will work.

Instead, it creates a transparent innovation hypothesis
that can be tested through a small experiment.
"""

from dataclasses import dataclass, asdict
from itertools import combinations
from typing import Dict, List, Optional

from src.innovation_inspiration import (
    InnovationInspiration,
)


@dataclass
class InnovationCombination:
    """A potential combination of two innovation inspirations."""

    title: str
    problem: str
    description: str
    inspiration_a: str
    inspiration_b: str
    mechanism_a: str
    mechanism_b: str
    combined_mechanism: str
    rationale: str
    uncertainty: List[str]
    experiment: str
    validation_question: str

    def to_dict(self) -> Dict:
        """Return the combination as a dictionary."""

        return asdict(self)


class InnovationCombinationEngine:
    """Combines innovation inspirations into new mechanisms."""

    def combine(
        self,
        problem: str,
        opportunity=None,
        inspirations: Optional[
            List[InnovationInspiration]
        ] = None,
    ) -> List[InnovationCombination]:
        """
        Generate potential combinations from multiple
        innovation inspirations.

        At least two inspirations are required.

        The engine uses transparent pairwise combinations
        rather than assuming that one inspiration alone
        represents innovation.
        """

        if not problem or not problem.strip():
            raise ValueError(
                "problem cannot be empty"
            )

        inspirations = inspirations or []

        if len(inspirations) < 2:
            return []

        for inspiration in inspirations:
            if not isinstance(
                inspiration,
                InnovationInspiration,
            ):
                raise TypeError(
                    "All inspirations must be instances "
                    "of InnovationInspiration."
                )

        combinations_found = []

        for inspiration_a, inspiration_b in combinations(
            inspirations,
            2,
        ):
            combination = self._build_combination(
                problem=problem.strip(),
                opportunity=opportunity,
                inspiration_a=inspiration_a,
                inspiration_b=inspiration_b,
            )

            combinations_found.append(
                combination
            )

        return combinations_found

    def _build_combination(
        self,
        problem: str,
        opportunity,
        inspiration_a: InnovationInspiration,
        inspiration_b: InnovationInspiration,
    ) -> InnovationCombination:
        """Build one transparent combination hypothesis."""

        title = (
            f"Combine {inspiration_a.title} "
            f"with {inspiration_b.title}"
        )

        description = (
            "A potential new approach combines two "
            "different mechanisms to address the "
            "identified problem. This is a design "
            "hypothesis rather than a proven intervention."
        )

        mechanism_a = inspiration_a.mechanism
        mechanism_b = inspiration_b.mechanism

        combined_mechanism = (
            f"Combine the mechanism from "
            f"{inspiration_a.title} "
            f"({mechanism_a}) with the mechanism from "
            f"{inspiration_b.title} "
            f"({mechanism_b}), creating an integrated "
            f"approach that uses both mechanisms together."
        )

        rationale = (
            f"The first inspiration reports: "
            f"{inspiration_a.observed_result} "
            f"The second inspiration reports: "
            f"{inspiration_b.observed_result} "
            f"Combining these mechanisms may address "
            f"the problem more effectively than either "
            f"mechanism alone."
        )

        if opportunity is not None:
            opportunity_description = getattr(
                opportunity,
                "description",
                "",
            )

            if opportunity_description:
                rationale += (
                    f" The combination is also connected "
                    f"to the identified opportunity: "
                    f"{opportunity_description}"
                )

        uncertainty = [
    "The combination is uncertain and not proven "
    "as an intervention.",
    "The two mechanisms may interact differently "
    "in the target context.",
    "The observed results from the source "
    "inspirations may not transfer directly.",
]

        experiment = (
            "Run a small, time-bound pilot combining both "
            "mechanisms with a defined target population. "
            "Compare engagement or access outcomes with "
            "the existing approach and document what "
            "changes, what does not change, and any "
            "unexpected effects."
        )

        validation_question = (
            "Does combining these two mechanisms produce "
            "better results for the identified problem "
            "than using the existing approach or either "
            "mechanism separately?"
        )

        return InnovationCombination(
            title=title,
            problem=problem,
            description=description,
            inspiration_a=inspiration_a.title,
            inspiration_b=inspiration_b.title,
            mechanism_a=mechanism_a,
            mechanism_b=mechanism_b,
            combined_mechanism=combined_mechanism,
            rationale=rationale,
            uncertainty=uncertainty,
            experiment=experiment,
            validation_question=validation_question,
        )
