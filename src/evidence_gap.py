"""
OpenSocial AI – Evidence Gap Analysis Layer

Version 4

Identifies important information that is missing from the
available evidence.

Evidence gaps are not conclusions. They identify questions
that require further investigation, additional data, or
community validation.

This layer is deliberately transparent and deterministic.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List

from src.evidence import EvidenceItem


@dataclass
class EvidenceGap:
    """Represents an important gap in the available evidence."""

    gap_type: str
    description: str
    investigation_question: str
    priority: str = "medium"

    def to_dict(self) -> Dict:
        """Return the evidence gap as a dictionary."""

        return asdict(self)


class EvidenceGapAnalysis:
    """
    Deterministic baseline engine for identifying evidence gaps.

    It examines whether the available evidence provides enough
    information about:

    - source diversity
    - time
    - location
    - population
    - comparison
    - outcomes
    """

    def discover(
        self,
        evidence: List[EvidenceItem],
    ) -> List[EvidenceGap]:
        """
        Identify gaps in the available evidence.

        Returns an empty list when evidence is sufficiently
        represented across the basic dimensions checked here.
        """

        if not evidence:
            return [
                EvidenceGap(
                    gap_type="missing_evidence",
                    description=(
                        "No evidence has been supplied to investigate "
                        "the problem."
                    ),
                    investigation_question=(
                        "What evidence should be collected before "
                        "drawing conclusions?"
                    ),
                    priority="high",
                )
            ]

        self._validate_evidence(evidence)

        gaps: List[EvidenceGap] = []

        gaps.extend(self._check_source_diversity(evidence))
        gaps.extend(self._check_dates(evidence))
        gaps.extend(self._check_locations(evidence))
        gaps.extend(self._check_populations(evidence))
        gaps.extend(self._check_comparison(evidence))
        gaps.extend(self._check_outcomes(evidence))

        return gaps

    @staticmethod
    def _validate_evidence(
        evidence: List[EvidenceItem],
    ) -> None:
        """Validate evidence before gap analysis."""

        for item in evidence:
            if not isinstance(item, EvidenceItem):
                raise TypeError(
                    "All evidence items must be instances of EvidenceItem."
                )

            if not item.source_type.strip():
                raise ValueError(
                    "EvidenceItem source_type cannot be empty."
                )

            if not item.content.strip():
                raise ValueError(
                    "EvidenceItem content cannot be empty."
                )

    @staticmethod
    def _check_source_diversity(
        evidence: List[EvidenceItem],
    ) -> List[EvidenceGap]:
        """Check whether multiple evidence perspectives are available."""

        source_types = {
            item.source_type.strip()
            for item in evidence
            if item.source_type.strip()
        }

        if len(source_types) > 1:
            return []

        return [
            EvidenceGap(
                gap_type="source_diversity",
                description=(
                    "Only one evidence source type is represented. "
                    "The current explanation may not reflect different "
                    "perspectives."
                ),
                investigation_question=(
                    "What do other evidence sources, such as community "
                    "feedback, programme records, research or field "
                    "observations, indicate?"
                ),
                priority="medium",
            )
        ]

    @staticmethod
    def _check_dates(
        evidence: List[EvidenceItem],
    ) -> List[EvidenceGap]:
        """Check whether evidence has temporal information."""

        dated_items = [
            item
            for item in evidence
            if item.date and item.date.strip()
        ]

        if dated_items:
            return []

        return [
            EvidenceGap(
                gap_type="time",
                description=(
                    "The evidence does not contain dates, so changes "
                    "over time cannot be assessed."
                ),
                investigation_question=(
                    "How has the problem or outcome changed over time?"
                ),
                priority="medium",
            )
        ]

    @staticmethod
    def _check_locations(
        evidence: List[EvidenceItem],
    ) -> List[EvidenceGap]:
        """Check whether evidence contains location information."""

        locations = {
            item.location.strip()
            for item in evidence
            if item.location and item.location.strip()
        }

        if locations:
            return []

        return [
            EvidenceGap(
                gap_type="location",
                description=(
                    "The evidence does not contain location information, "
                    "so geographic differences cannot be assessed."
                ),
                investigation_question=(
                    "Does the problem occur differently across "
                    "locations or service areas?"
                ),
                priority="medium",
            )
        ]

    @staticmethod
    def _check_populations(
        evidence: List[EvidenceItem],
    ) -> List[EvidenceGap]:
        """Check whether evidence contains population information."""

        populations = {
            item.population.strip()
            for item in evidence
            if item.population and item.population.strip()
        }

        if populations:
            return []

        return [
            EvidenceGap(
                gap_type="population",
                description=(
                    "The evidence does not identify the populations "
                    "represented, limiting comparison between groups."
                ),
                investigation_question=(
                    "Which groups are most affected and which groups "
                    "are less affected by the problem?"
                ),
                priority="high",
            )
        ]

    @staticmethod
    def _check_comparison(
        evidence: List[EvidenceItem],
    ) -> List[EvidenceGap]:
        """
        Check whether the evidence provides more than one observation.

        A single observation cannot establish whether a finding is
        unusual, typical, improving or deteriorating.
        """

        if len(evidence) >= 2:
            return []

        return [
            EvidenceGap(
                gap_type="comparison",
                description=(
                    "Only one evidence item is available, limiting "
                    "the ability to compare observations."
                ),
                investigation_question=(
                    "Can additional observations, locations, periods "
                    "or groups be examined for comparison?"
                ),
                priority="high",
            )
        ]

    @staticmethod
    def _check_outcomes(
        evidence: List[EvidenceItem],
    ) -> List[EvidenceGap]:
        """Check whether evidence contains outcome-related signals."""

        outcome_terms = {
            "increase",
            "increased",
            "improved",
            "improvement",
            "decrease",
            "decreased",
            "decline",
            "declined",
            "reduced",
            "reduction",
            "uptake",
            "engagement",
            "outcome",
            "success",
            "successful",
            "failure",
            "failed",
            "dropout",
            "drop-off",
        }

        has_outcome_signal = False

        for item in evidence:
            words = {
                word.strip(".,:;!?()[]{}")
                for word in item.content.lower().split()
            }

            if words.intersection(outcome_terms):
                has_outcome_signal = True
                break

        if has_outcome_signal:
            return []

        return [
            EvidenceGap(
                gap_type="outcome",
                description=(
                    "The available evidence does not contain a clear "
                    "outcome-related signal."
                ),
                investigation_question=(
                    "What measurable change or outcome is associated "
                    "with the problem or intervention?"
                ),
                priority="high",
            )
        ]


if __name__ == "__main__":
    from src.evidence import create_evidence

    evidence = [
        create_evidence(
            source_type="programme_report",
            content="Service uptake increased after peer support.",
            date="2025-06-30",
            location="Madurai",
            population="Young people",
        ),
        create_evidence(
            source_type="community_feedback",
            content="Participants reported improved access.",
            date="2025-09-15",
            location="Madurai",
            population="Young people",
        ),
    ]

    analysis = EvidenceGapAnalysis()
    gaps = analysis.discover(evidence)

    print("Evidence Gaps:")

    for gap in gaps:
        print(f"- [{gap.priority}] {gap.description}")
        print(f"  Investigate: {gap.investigation_question}")