"""
OpenSocial AI – Innovation Inspiration Engine

Version 1.0

Stores and retrieves potential sources of innovation inspiration.

Inspiration may come from:
- cross-sector approaches
- historical programmes
- community innovations
- research or other documented approaches

The engine does not claim that an inspiration source is proven
to work in the target context.

Instead, it identifies potentially relevant mechanisms that
can be adapted and tested.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class InnovationInspiration:
    """A documented source of inspiration for innovation."""

    source_type: str
    title: str
    context: str
    mechanism: str
    observed_result: str
    transferability: str = "exploratory"
    adaptation_notes: str = ""

    def to_dict(self) -> Dict:
        """Return the inspiration as a dictionary."""

        return asdict(self)


class InnovationInspirationEngine:
    """Creates and identifies relevant innovation inspiration."""

    VALID_SOURCE_TYPES = {
        "cross_sector",
        "historical",
        "community",
        "research",
        "international",
    }

    VALID_TRANSFERABILITY = {
        "low",
        "moderate",
        "high",
        "exploratory",
    }

    def create(
        self,
        source_type: str,
        title: str,
        context: str,
        mechanism: str,
        observed_result: str,
        transferability: str = "exploratory",
        adaptation_notes: str = "",
    ) -> InnovationInspiration:
        """
        Create a validated innovation inspiration record.
        """

        if not source_type or not source_type.strip():
            raise ValueError(
                "source_type cannot be empty"
            )

        if not title or not title.strip():
            raise ValueError(
                "title cannot be empty"
            )

        if not context or not context.strip():
            raise ValueError(
                "context cannot be empty"
            )

        if not mechanism or not mechanism.strip():
            raise ValueError(
                "mechanism cannot be empty"
            )

        if not observed_result or not observed_result.strip():
            raise ValueError(
                "observed_result cannot be empty"
            )

        source_type = source_type.strip().lower()

        if source_type not in self.VALID_SOURCE_TYPES:
            raise ValueError(
                f"Unsupported source_type: {source_type}"
            )

        transferability = (
            transferability.strip().lower()
            if transferability
            else "exploratory"
        )

        if transferability not in self.VALID_TRANSFERABILITY:
            raise ValueError(
                f"Unsupported transferability: "
                f"{transferability}"
            )

        return InnovationInspiration(
            source_type=source_type,
            title=title.strip(),
            context=context.strip(),
            mechanism=mechanism.strip(),
            observed_result=observed_result.strip(),
            transferability=transferability,
            adaptation_notes=(
                adaptation_notes.strip()
                if adaptation_notes
                else ""
            ),
        )

    def find_relevant(
        self,
        problem: str,
        inspirations: Optional[
            List[InnovationInspiration]
        ] = None,
    ) -> List[InnovationInspiration]:
        """
        Identify inspiration records that appear relevant
        to a problem.

        Relevance is determined using transparent keyword
        overlap across the problem, context and mechanism.

        This is deliberately simple and model-independent.
        A future AI retrieval layer can replace or extend
        this ranking approach.
        """

        if not problem or not problem.strip():
            raise ValueError(
                "problem cannot be empty"
            )

        inspirations = inspirations or []

        if not inspirations:
            return []

        problem_terms = self._normalise_terms(
            problem
        )

        scored = []

        for inspiration in inspirations:

            if not isinstance(
                inspiration,
                InnovationInspiration,
            ):
                raise TypeError(
                    "All inspirations must be instances "
                    "of InnovationInspiration."
                )

            searchable_text = " ".join(
                [
                    inspiration.title,
                    inspiration.context,
                    inspiration.mechanism,
                    inspiration.observed_result,
                    inspiration.adaptation_notes,
                ]
            )

            inspiration_terms = self._normalise_terms(
                searchable_text
            )

            overlap = (
                problem_terms
                & inspiration_terms
            )

            score = len(overlap)

            if score > 0:
                scored.append(
                    (
                        score,
                        self._transferability_score(
                            inspiration.transferability
                        ),
                        inspiration,
                    )
                )

        scored.sort(
            key=lambda item: (
                item[0],
                item[1],
            ),
            reverse=True,
        )

        return [
            item[2]
            for item in scored
        ]

    @staticmethod
    def _normalise_terms(
        text: str,
    ) -> set:
        """
        Convert text into simple searchable terms.
        """

        stop_words = {
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "by",
            "for",
            "from",
            "has",
            "have",
            "in",
            "is",
            "it",
            "of",
            "on",
            "or",
            "that",
            "the",
            "their",
            "this",
            "to",
            "was",
            "were",
            "with",
            "young",
            "people",
        }

        words = (
            text.lower()
            .replace("-", " ")
            .replace(",", " ")
            .replace(".", " ")
            .replace(":", " ")
            .replace(";", " ")
            .split()
        )

        return {
            word
            for word in words
            if len(word) > 2
            and word not in stop_words
        }

    @staticmethod
    def _transferability_score(
        transferability: str,
    ) -> int:
        """Convert transferability into a ranking score."""

        scores = {
            "low": 1,
            "exploratory": 2,
            "moderate": 3,
            "high": 4,
        }

        return scores.get(
            transferability,
            2,
        )