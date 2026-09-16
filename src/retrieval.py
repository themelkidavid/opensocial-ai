"""
OpenSocial AI – Inspiration Retrieval

Defines a small retrieval boundary for innovation inspirations. The
default KeywordRetriever keeps the existing deterministic keyword-overlap
behavior; future semantic retrieval can implement RelevanceRetriever
without changing InnovationReasoningEngine.
"""

from typing import List, Optional


class RelevanceRetriever:
    """Interface for ranking potentially relevant inspiration records."""

    def retrieve(self, problem: str, inspirations: Optional[List] = None) -> List:
        """Return inspirations ranked for the supplied problem."""

        raise NotImplementedError


class KeywordRetriever(RelevanceRetriever):
    """Transparent deterministic retrieval based on keyword overlap."""

    def retrieve(self, problem: str, inspirations: Optional[List] = None) -> List:
        """Return matching inspirations ranked by overlap and transferability."""

        if not isinstance(problem, str) or not problem.strip():
            raise ValueError("problem cannot be empty")

        inspirations = inspirations or []
        problem_terms = self.normalise_terms(problem)
        scored = []

        for inspiration in inspirations:
            try:
                searchable_text = " ".join(
                    [
                        inspiration.title,
                        inspiration.context,
                        inspiration.mechanism,
                        inspiration.observed_result,
                        inspiration.adaptation_notes,
                    ]
                )
                transferability = inspiration.transferability
            except AttributeError as error:
                raise TypeError(
                    "All inspirations must provide the expected fields."
                ) from error

            inspiration_terms = self.normalise_terms(searchable_text)
            score = len(problem_terms & inspiration_terms)

            if score > 0:
                scored.append(
                    (
                        score,
                        self.transferability_score(transferability),
                        inspiration,
                    )
                )

        scored.sort(
            key=lambda item: (item[0], item[1]),
            reverse=True,
        )

        return [item[2] for item in scored]

    @staticmethod
    def normalise_terms(text: str) -> set:
        """Convert text into the current transparent searchable terms."""

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
            if len(word) > 2 and word not in stop_words
        }

    @staticmethod
    def transferability_score(transferability: str) -> int:
        """Convert transferability into the existing ranking score."""

        scores = {
            "low": 1,
            "exploratory": 2,
            "moderate": 3,
            "high": 4,
        }
        return scores.get(transferability, 2)
