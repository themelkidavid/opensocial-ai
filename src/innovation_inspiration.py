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


try:
    from src.retrieval import (
        KeywordRetriever,
        RelevanceRetriever,
        RetrievalMatch,
    )
except ModuleNotFoundError:
    from retrieval import (
        KeywordRetriever,
        RelevanceRetriever,
        RetrievalMatch,
    )


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

    def __init__(
        self,
        retriever: Optional[RelevanceRetriever] = None,
    ) -> None:
        """Use the supplied retriever or deterministic keyword retrieval."""

        self.retriever = (
            retriever if retriever is not None else KeywordRetriever()
        )

        if not callable(getattr(self.retriever, "retrieve", None)):
            raise TypeError("retriever must provide a retrieve method")

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

        Relevance is determined by the configured retriever.
        The default uses transparent keyword overlap; optional
        strategies can return candidate inspirations with
        explainable relevance metadata.
        """

        return [
            match.inspiration
            for match in self.find_relevant_matches(problem, inspirations)
        ]

    def find_relevant_matches(
        self,
        problem: str,
        inspirations: Optional[
            List[InnovationInspiration]
        ] = None,
    ) -> List[RetrievalMatch]:
        """Return validated retrieval metadata for candidate inspirations."""

        if not problem or not problem.strip():
            raise ValueError(
                "problem cannot be empty"
            )

        inspirations = inspirations or []

        if not inspirations:
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

        retrieve_matches = getattr(self.retriever, "retrieve_matches", None)
        if callable(retrieve_matches):
            matches = retrieve_matches(
                problem=problem,
                inspirations=inspirations,
            )
        else:
            retrieved = self.retriever.retrieve(
                problem=problem,
                inspirations=inspirations,
            )
            if not isinstance(retrieved, list):
                raise TypeError("retriever must return a list of inspirations")
            matches = []
            for inspiration in retrieved:
                if not isinstance(inspiration, InnovationInspiration):
                    raise TypeError(
                        "retriever results must be InnovationInspiration instances"
                    )
                matches.append(
                    RetrievalMatch(
                        inspiration=inspiration,
                        strategy=self.retriever.__class__.__name__,
                        score=0.0,
                        source_type=inspiration.source_type,
                        context=inspiration.context,
                        transferability=inspiration.transferability,
                    )
                )

        if not isinstance(matches, list):
            raise TypeError("retriever must return a list of retrieval matches")

        unique_matches = []
        seen_inspirations = set()

        for match in matches:
            if not isinstance(match, RetrievalMatch):
                raise TypeError("retriever matches must be RetrievalMatch instances")

            inspiration = match.inspiration
            if not isinstance(inspiration, InnovationInspiration):
                raise TypeError(
                    "retriever results must be InnovationInspiration instances"
                )

            if not any(inspiration is candidate for candidate in inspirations):
                raise ValueError(
                    "retriever results must come from the supplied inspiration corpus"
                )

            if id(inspiration) not in seen_inspirations:
                unique_matches.append(match)
                seen_inspirations.add(id(inspiration))

        return unique_matches

    @staticmethod
    def _normalise_terms(
        text: str,
    ) -> set:
        """
        Convert text into simple searchable terms.
        """

        return KeywordRetriever.normalise_terms(text)

    @staticmethod
    def _transferability_score(
        transferability: str,
    ) -> int:
        """Convert transferability into a ranking score."""

        return KeywordRetriever.transferability_score(transferability)
