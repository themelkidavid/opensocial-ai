"""
OpenSocial AI – Pattern Discovery Layer

Version 3

Identifies observable patterns across structured EvidenceItems.

This layer is deliberately transparent and deterministic.
It does not claim that a pattern proves causation.

Its purpose is to identify signals that deserve further
investigation by humans, communities, researchers, or
future AI-assisted analysis.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple
import re

from src.evidence import EvidenceItem


@dataclass
class ObservedPattern:
    """A pattern observed across one or more evidence items."""

    pattern_type: str
    description: str
    evidence_count: int
    confidence: str = "exploratory"

    def to_dict(self) -> Dict:
        """Return the pattern as a dictionary."""

        return asdict(self)


class PatternDiscovery:
    """
    Deterministic baseline pattern-discovery engine.

    It looks for observable repetition across:
    - source types
    - locations
    - populations
    - dates
    - recurring terms
    - outcome-related language
    """

    STOP_WORDS = {
        "about",
        "after",
        "again",
        "also",
        "among",
        "been",
        "being",
        "between",
        "could",
        "from",
        "have",
        "into",
        "more",
        "most",
        "other",
        "over",
        "same",
        "some",
        "such",
        "than",
        "that",
        "their",
        "there",
        "these",
        "they",
        "this",
        "through",
        "under",
        "were",
        "which",
        "with",
        "would",
        "young",
    }

    OUTCOME_TERMS = {
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
        "access",
        "accessed",
        "engagement",
        "engaged",
        "outcome",
        "successful",
        "success",
        "failure",
        "failed",
        "dropout",
        "drop-off",
    }

    def discover(
        self,
        evidence: List[EvidenceItem],
    ) -> List[ObservedPattern]:
        """
        Discover observable patterns across evidence.

        Returns an empty list when no evidence is supplied.
        """

        if not evidence:
            return []

        self._validate_evidence(evidence)

        patterns: List[ObservedPattern] = []

        patterns.extend(self._source_type_patterns(evidence))
        patterns.extend(self._location_patterns(evidence))
        patterns.extend(self._population_patterns(evidence))
        patterns.extend(self._date_patterns(evidence))
        patterns.extend(self._term_patterns(evidence))
        patterns.extend(self._outcome_patterns(evidence))

        return patterns

    @staticmethod
    def _validate_evidence(
        evidence: List[EvidenceItem],
    ) -> None:
        """Validate evidence before pattern discovery."""

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
    def _source_type_patterns(
        evidence: List[EvidenceItem],
    ) -> List[ObservedPattern]:
        """Identify repeated evidence source types."""

        counts = PatternDiscovery._count_values(
            item.source_type.strip()
            for item in evidence
        )

        patterns = []

        for source_type, count in counts:
            if count >= 2:
                patterns.append(
                    ObservedPattern(
                        pattern_type="source_type",
                        description=(
                            f"'{source_type}' appears in {count} "
                            "evidence items."
                        ),
                        evidence_count=count,
                    )
                )

        return patterns

    @staticmethod
    def _location_patterns(
        evidence: List[EvidenceItem],
    ) -> List[ObservedPattern]:
        """Identify repeated locations."""

        counts = PatternDiscovery._count_values(
            item.location.strip()
            for item in evidence
            if item.location and item.location.strip()
        )

        patterns = []

        for location, count in counts:
            if count >= 2:
                patterns.append(
                    ObservedPattern(
                        pattern_type="location",
                        description=(
                            f"Evidence repeatedly refers to "
                            f"'{location}' ({count} items)."
                        ),
                        evidence_count=count,
                    )
                )

        return patterns

    @staticmethod
    def _population_patterns(
        evidence: List[EvidenceItem],
    ) -> List[ObservedPattern]:
        """Identify repeated populations."""

        counts = PatternDiscovery._count_values(
            item.population.strip()
            for item in evidence
            if item.population and item.population.strip()
        )

        patterns = []

        for population, count in counts:
            if count >= 2:
                patterns.append(
                    ObservedPattern(
                        pattern_type="population",
                        description=(
                            f"Evidence repeatedly refers to "
                            f"'{population}' ({count} items)."
                        ),
                        evidence_count=count,
                    )
                )

        return patterns

    @staticmethod
    def _date_patterns(
        evidence: List[EvidenceItem],
    ) -> List[ObservedPattern]:
        """Identify evidence spanning multiple dates."""

        dates = sorted(
            {
                item.date.strip()
                for item in evidence
                if item.date and item.date.strip()
            }
        )

        if len(dates) < 2:
            return []

        return [
            ObservedPattern(
                pattern_type="time_span",
                description=(
                    f"Evidence is available across {len(dates)} "
                    "distinct dates, allowing change over time "
                    "to be investigated."
                ),
                evidence_count=len(evidence),
            )
        ]

    def _term_patterns(
        self,
        evidence: List[EvidenceItem],
    ) -> List[ObservedPattern]:
        """Identify recurring meaningful terms across evidence."""

        term_counts: Dict[str, int] = {}

        for item in evidence:
            words = self._extract_terms(item.content)

            for word in words:
                term_counts[word] = term_counts.get(word, 0) + 1

        recurring = sorted(
            (
                (term, count)
                for term, count in term_counts.items()
                if count >= 2
            ),
            key=lambda item: (-item[1], item[0]),
        )

        patterns = []

        for term, count in recurring[:10]:
            patterns.append(
                ObservedPattern(
                    pattern_type="recurring_term",
                    description=(
                        f"The term '{term}' appears across "
                        f"{count} evidence items."
                    ),
                    evidence_count=count,
                )
            )

        return patterns

    def _outcome_patterns(
        self,
        evidence: List[EvidenceItem],
    ) -> List[ObservedPattern]:
        """Identify recurring outcome-related language."""

        matched_terms: Dict[str, int] = {}

        for item in evidence:
            terms = self._extract_terms(item.content)

            for term in terms:
                if term in self.OUTCOME_TERMS:
                    matched_terms[term] = (
                        matched_terms.get(term, 0) + 1
                    )

        recurring = sorted(
            (
                (term, count)
                for term, count in matched_terms.items()
                if count >= 2
            ),
            key=lambda item: (-item[1], item[0]),
        )

        patterns = []

        for term, count in recurring[:10]:
            patterns.append(
                ObservedPattern(
                    pattern_type="outcome_signal",
                    description=(
                        f"Outcome-related language '{term}' "
                        f"appears across {count} evidence items."
                    ),
                    evidence_count=count,
                )
            )

        return patterns

    @classmethod
    def _extract_terms(
        cls,
        text: str,
    ) -> List[str]:
        """Extract simple normalized terms from evidence text."""

        words = re.findall(
            r"[a-zA-Z][a-zA-Z'-]{2,}",
            text.lower(),
        )

        return [
            word
            for word in words
            if word not in cls.STOP_WORDS
        ]

    @staticmethod
    def _count_values(
        values,
    ) -> List[Tuple[str, int]]:
        """Count repeated non-empty values."""

        counts: Dict[str, int] = {}

        for value in values:
            if value:
                counts[value] = counts.get(value, 0) + 1

        return sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )


if __name__ == "__main__":
    from src.evidence import create_evidence

    evidence = [
        create_evidence(
            source_type="programme_report",
            content=(
                "Service uptake increased after peer support "
                "was introduced."
            ),
            date="2025-06-30",
            location="Madurai",
            population="Young people",
        ),
        create_evidence(
            source_type="community_feedback",
            content=(
                "Young people reported improved access and "
                "increased engagement after peer support."
            ),
            date="2025-09-15",
            location="Madurai",
            population="Young people",
        ),
    ]

    discovery = PatternDiscovery()
    patterns = discovery.discover(evidence)

    print("Observed Patterns:")

    for pattern in patterns:
        print(f"- [{pattern.pattern_type}] {pattern.description}")