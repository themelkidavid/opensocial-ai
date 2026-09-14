"""
OpenSocial AI – Evidence Conflict Detection

Version 1.0

Detects potential contradictions between evidence items.

The detector is intentionally transparent and model-independent.
It does not attempt to decide which evidence item is correct.

Instead, it identifies potentially conflicting outcome signals
within comparable evidence and asks for human investigation.

Examples:

- "service uptake increased"
  versus
  "service uptake decreased"

- "participants reported improved access"
  versus
  "participants reported worse access"

The purpose is to surface disagreement rather than hide it.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List

try:
    from src.evidence import EvidenceItem
except ModuleNotFoundError:
    from evidence import EvidenceItem


@dataclass
class EvidenceConflict:
    """A potential conflict between two evidence items."""

    first_index: int
    second_index: int
    first_source_type: str
    second_source_type: str
    description: str
    investigation_question: str

    def to_dict(self) -> Dict:
        """Return the conflict as a dictionary."""

        return asdict(self)


class EvidenceConflictDetector:
    """
    Detect potential contradictions between evidence items.

    The detector only flags conflicts when:

    1. Two evidence items describe comparable contexts.
    2. Their content contains opposing outcome signals.

    Comparable context is established through shared location or
    population information.

    The detector does not determine which source is correct.
    """

    POSITIVE_SIGNALS = (
        "increased",
        "increase",
        "improved",
        "improve",
        "higher",
        "better",
        "successful",
        "success",
        "effective",
        "effective",
        "grew",
        "growth",
        "more",
        "uptake increased",
        "access improved",
        "engagement increased",
    )

    NEGATIVE_SIGNALS = (
        "decreased",
        "decrease",
        "declined",
        "decline",
        "worsened",
        "worsen",
        "lower",
        "worse",
        "unsuccessful",
        "failure",
        "ineffective",
        "fell",
        "reduced",
        "reduction",
        "less",
        "uptake decreased",
        "access worsened",
        "engagement decreased",
    )

    def discover(
        self,
        evidence: List[EvidenceItem],
    ) -> List[EvidenceConflict]:
        """
        Discover potential conflicts in a collection of evidence.

        Returns:
            A list of potential evidence conflicts.
        """

        self._validate_evidence(evidence)

        conflicts: List[EvidenceConflict] = []

        for first_index in range(len(evidence)):
            for second_index in range(
                first_index + 1,
                len(evidence),
            ):
                first = evidence[first_index]
                second = evidence[second_index]

                if not self._comparable_context(first, second):
                    continue

                if not self._contains_opposing_signals(
                    first.content,
                    second.content,
                ):
                    continue

                conflicts.append(
                    self._build_conflict(
                        first_index,
                        second_index,
                        first,
                        second,
                    )
                )

        return conflicts

    @staticmethod
    def _validate_evidence(
        evidence: List[EvidenceItem],
    ) -> None:
        """Validate the evidence collection."""

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
    def _comparable_context(
        first: EvidenceItem,
        second: EvidenceItem,
    ) -> bool:
        """
        Determine whether two evidence items describe a comparable context.

        Evidence is considered comparable when it shares either:
        - the same location, or
        - the same population.
        """

        same_location = (
            bool(first.location)
            and bool(second.location)
            and first.location.strip().lower()
            == second.location.strip().lower()
        )

        same_population = (
            bool(first.population)
            and bool(second.population)
            and first.population.strip().lower()
            == second.population.strip().lower()
        )

        return same_location or same_population

    @classmethod
    def _contains_opposing_signals(
        cls,
        first_content: str,
        second_content: str,
    ) -> bool:
        """Check whether two texts contain opposing outcome signals."""

        first_text = first_content.lower()
        second_text = second_content.lower()

        first_positive = cls._contains_signal(
            first_text,
            cls.POSITIVE_SIGNALS,
        )

        first_negative = cls._contains_signal(
            first_text,
            cls.NEGATIVE_SIGNALS,
        )

        second_positive = cls._contains_signal(
            second_text,
            cls.POSITIVE_SIGNALS,
        )

        second_negative = cls._contains_signal(
            second_text,
            cls.NEGATIVE_SIGNALS,
        )

        return (
            (first_positive and second_negative)
            or
            (first_negative and second_positive)
        )

    @staticmethod
    def _contains_signal(
        text: str,
        signals: tuple,
    ) -> bool:
        """Return True when any signal appears in the text."""

        return any(
            signal in text
            for signal in signals
        )

    @staticmethod
    def _build_conflict(
        first_index: int,
        second_index: int,
        first: EvidenceItem,
        second: EvidenceItem,
    ) -> EvidenceConflict:
        """Create a transparent conflict description."""

        context_parts = []

        if first.location and second.location:
            if (
                first.location.strip().lower()
                == second.location.strip().lower()
            ):
                context_parts.append(
                    f"location '{first.location.strip()}'"
                )

        if first.population and second.population:
            if (
                first.population.strip().lower()
                == second.population.strip().lower()
            ):
                context_parts.append(
                    f"population '{first.population.strip()}'"
                )

        if context_parts:
            context = " and ".join(context_parts)
        else:
            context = "a comparable context"

        description = (
            "Potentially conflicting outcome signals were detected "
            f"between {first.source_type} and {second.source_type} "
            f"for {context}."
        )

        investigation_question = (
            "Why do these evidence sources report different outcomes? "
            "Check differences in timeframe, measurement method, "
            "implementation conditions, population, location, or "
            "data collection approach before drawing a conclusion."
        )

        return EvidenceConflict(
            first_index=first_index,
            second_index=second_index,
            first_source_type=first.source_type,
            second_source_type=second.source_type,
            description=description,
            investigation_question=investigation_question,
        )


if __name__ == "__main__":
    detector = EvidenceConflictDetector()

    evidence = [
        EvidenceItem(
            source_type="programme_report",
            content="Service uptake increased after peer support.",
            location="Madurai",
            population="Young people",
        ),
        EvidenceItem(
            source_type="community_feedback",
            content="Young people reported that service uptake decreased.",
            location="Madurai",
            population="Young people",
        ),
    ]

    conflicts = detector.discover(evidence)

    print("Evidence Conflicts")
    print("------------------")

    for conflict in conflicts:
        print("-", conflict.description)
        print(
            "  Investigate:",
            conflict.investigation_question,
        )