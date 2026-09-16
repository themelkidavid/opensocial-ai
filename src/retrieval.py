"""
OpenSocial AI – Inspiration Retrieval

Defines a small retrieval boundary for innovation inspirations. The
default KeywordRetriever keeps the existing deterministic keyword-overlap
behavior. SemanticRetriever is optional and depends only on a caller-
provided embedding interface, never on a particular model or service.
"""

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Dict, List, Optional, Sequence


@dataclass
class RetrievalMatch:
    """An explainable candidate-inspiration relevance result.

    A score indicates only potential relevance under the named strategy. It
    is not evidence of causal similarity, contextual equivalence, or likely
    intervention effectiveness.
    """

    inspiration: object
    strategy: str
    score: float
    source_type: str
    context: str
    transferability: str
    keyword_score: Optional[float] = None
    semantic_similarity: Optional[float] = None

    def to_dict(self) -> Dict:
        """Return transparent retrieval metadata for serialization."""

        result = asdict(self)
        result["inspiration"] = self.inspiration.to_dict()
        return result


class EmbeddingProvider:
    """Provider-neutral interface for producing a numeric text embedding."""

    def embed(self, text: str) -> Sequence[float]:
        """Return a numeric vector for one non-empty text input."""

        raise NotImplementedError


class DeterministicTestEmbeddingProvider(EmbeddingProvider):
    """A deterministic test/reference provider, not production semantics.

    It hashes tokens into a small signed vector so tests and local examples
    need no network, model, or external dependency. Hash collisions and its
    lexical nature make it unsuitable as a production semantic model.
    """

    def __init__(self, dimensions: int = 16) -> None:
        if not isinstance(dimensions, int) or dimensions <= 0:
            raise ValueError("dimensions must be a positive integer")
        self.dimensions = dimensions

    def embed(self, text: str) -> Sequence[float]:
        """Return a stable hashed-token vector for testing only."""

        if not isinstance(text, str) or not text.strip():
            raise ValueError("text cannot be empty")

        vector = [0.0] * self.dimensions
        for token in KeywordRetriever.normalise_terms(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0 if digest[4] % 2 else -1.0
        return vector


class RelevanceRetriever:
    """Interface for ranking potentially relevant inspiration records."""

    def retrieve(self, problem: str, inspirations: Optional[List] = None) -> List:
        """Return inspirations ranked for the supplied problem."""

        raise NotImplementedError

    def retrieve_matches(
        self,
        problem: str,
        inspirations: Optional[List] = None,
    ) -> List[RetrievalMatch]:
        """Return explainable matches while preserving legacy retrieve()."""

        retrieved = self.retrieve(problem, inspirations)
        if not isinstance(retrieved, list):
            raise TypeError("retriever must return a list of inspirations")
        return [
            _match(
                inspiration=inspiration,
                strategy=self.__class__.__name__,
                score=0.0,
            )
            for inspiration in retrieved
        ]


class KeywordRetriever(RelevanceRetriever):
    """Transparent deterministic retrieval based on keyword overlap."""

    def retrieve(self, problem: str, inspirations: Optional[List] = None) -> List:
        """Return matching inspirations ranked by overlap and transferability."""

        return [
            match.inspiration
            for match in self.retrieve_matches(problem, inspirations)
        ]

    def retrieve_matches(
        self,
        problem: str,
        inspirations: Optional[List] = None,
    ) -> List[RetrievalMatch]:
        """Return transparent keyword-overlap matches."""

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

        return [
            _match(
                inspiration=item[2],
                strategy="keyword",
                score=float(item[0]),
                keyword_score=float(item[0]),
            )
            for item in scored
        ]

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


class SemanticRetriever(RelevanceRetriever):
    """Optional cosine-similarity retrieval using a caller-owned provider."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        minimum_similarity: float = 0.0,
    ) -> None:
        if not callable(getattr(embedding_provider, "embed", None)):
            raise TypeError("embedding_provider must provide an embed method")
        if (
            not isinstance(minimum_similarity, (int, float))
            or isinstance(minimum_similarity, bool)
            or not math.isfinite(minimum_similarity)
            or minimum_similarity < -1.0
            or minimum_similarity > 1.0
        ):
            raise ValueError(
                "minimum_similarity must be a finite value from -1 to 1"
            )

        self.embedding_provider = embedding_provider
        self.minimum_similarity = float(minimum_similarity)

    def retrieve(self, problem: str, inspirations: Optional[List] = None) -> List:
        """Return candidates whose cosine similarity meets the threshold."""

        return [
            match.inspiration
            for match in self.retrieve_matches(problem, inspirations)
        ]

    def retrieve_matches(
        self,
        problem: str,
        inspirations: Optional[List] = None,
    ) -> List[RetrievalMatch]:
        """Rank candidate inspirations with transparent cosine similarity."""

        if not isinstance(problem, str) or not problem.strip():
            raise ValueError("problem cannot be empty")

        inspirations = inspirations or []
        if not inspirations:
            return []

        query_vector = _validated_embedding(
            self.embedding_provider.embed(problem),
        )
        if _is_zero_vector(query_vector):
            return []

        scored = []
        for index, inspiration in enumerate(inspirations):
            candidate_text = _inspiration_text(inspiration)
            candidate_vector = _validated_embedding(
                self.embedding_provider.embed(candidate_text),
            )

            if len(candidate_vector) != len(query_vector):
                raise ValueError("embedding dimensions must match")
            if _is_zero_vector(candidate_vector):
                continue

            similarity = _cosine_similarity(query_vector, candidate_vector)
            if similarity >= self.minimum_similarity:
                scored.append((similarity, index, inspiration))

        scored.sort(key=lambda item: (-item[0], item[1]))
        return [
            _match(
                inspiration=inspiration,
                strategy="semantic",
                score=similarity,
                semantic_similarity=similarity,
            )
            for similarity, _, inspiration in scored
        ]


class HybridRetriever(RelevanceRetriever):
    """Optional transparent combination of keyword and semantic scores."""

    def __init__(
        self,
        semantic_retriever: SemanticRetriever,
        keyword_retriever: Optional[KeywordRetriever] = None,
        keyword_weight: float = 1.0,
        semantic_weight: float = 1.0,
        minimum_score: float = 0.0,
    ) -> None:
        if not callable(getattr(semantic_retriever, "retrieve_matches", None)):
            raise TypeError("semantic_retriever must provide retrieve_matches")
        if not callable(
            getattr(keyword_retriever or KeywordRetriever(), "retrieve_matches", None)
        ):
            raise TypeError("keyword_retriever must provide retrieve_matches")
        for name, value in (
            ("keyword_weight", keyword_weight),
            ("semantic_weight", semantic_weight),
            ("minimum_score", minimum_score),
        ):
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
            ):
                raise ValueError(f"{name} must be a finite number")

        self.semantic_retriever = semantic_retriever
        self.keyword_retriever = keyword_retriever or KeywordRetriever()
        self.keyword_weight = float(keyword_weight)
        self.semantic_weight = float(semantic_weight)
        self.minimum_score = float(minimum_score)

    def retrieve(self, problem: str, inspirations: Optional[List] = None) -> List:
        """Return candidates ranked by the documented weighted score."""

        return [
            match.inspiration
            for match in self.retrieve_matches(problem, inspirations)
        ]

    def retrieve_matches(
        self,
        problem: str,
        inspirations: Optional[List] = None,
    ) -> List[RetrievalMatch]:
        """Combine independently computed keyword and semantic matches."""

        inspirations = inspirations or []
        if not inspirations:
            return []

        keyword_matches = self.keyword_retriever.retrieve_matches(
            problem,
            inspirations,
        )
        semantic_matches = self.semantic_retriever.retrieve_matches(
            problem,
            inspirations,
        )
        keyword_scores = {
            id(match.inspiration): match.keyword_score or match.score
            for match in keyword_matches
        }
        semantic_scores = {
            id(match.inspiration): match.semantic_similarity or match.score
            for match in semantic_matches
        }

        scored = []
        for index, inspiration in enumerate(inspirations):
            keyword_score = keyword_scores.get(id(inspiration), 0.0)
            semantic_score = semantic_scores.get(id(inspiration), 0.0)
            score = (
                self.keyword_weight * keyword_score
                + self.semantic_weight * semantic_score
            )
            if score >= self.minimum_score and (
                id(inspiration) in keyword_scores
                or id(inspiration) in semantic_scores
            ):
                scored.append(
                    (
                        score,
                        index,
                        inspiration,
                        keyword_score,
                        semantic_score,
                    )
                )

        scored.sort(key=lambda item: (-item[0], item[1]))
        return [
            _match(
                inspiration=inspiration,
                strategy="hybrid",
                score=score,
                keyword_score=keyword_score,
                semantic_similarity=semantic_score,
            )
            for score, _, inspiration, keyword_score, semantic_score in scored
        ]


def _match(
    inspiration: object,
    strategy: str,
    score: float,
    keyword_score: Optional[float] = None,
    semantic_similarity: Optional[float] = None,
) -> RetrievalMatch:
    """Create a match while retaining source metadata for later ranking work."""

    _inspiration_text(inspiration)
    return RetrievalMatch(
        inspiration=inspiration,
        strategy=strategy,
        score=score,
        source_type=inspiration.source_type,
        context=inspiration.context,
        transferability=inspiration.transferability,
        keyword_score=keyword_score,
        semantic_similarity=semantic_similarity,
    )


def _inspiration_text(inspiration: object) -> str:
    """Return the existing searchable fields or clearly reject invalid input."""

    try:
        values = [
            inspiration.title,
            inspiration.context,
            inspiration.mechanism,
            inspiration.observed_result,
            inspiration.adaptation_notes,
        ]
        inspiration.source_type
        inspiration.transferability
    except AttributeError as error:
        raise TypeError(
            "All inspirations must provide the expected fields."
        ) from error

    if not all(isinstance(value, str) for value in values):
        raise TypeError("Inspiration searchable fields must be text")
    return " ".join(values)


def _validated_embedding(value: object) -> List[float]:
    """Reject missing, non-numeric, non-finite, or empty provider outputs."""

    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(
            "embedding provider must return a non-empty sequence of numbers"
        )
    if not value:
        raise ValueError("embedding provider returned an empty vector")

    vector = []
    for component in value:
        if (
            not isinstance(component, (int, float))
            or isinstance(component, bool)
            or not math.isfinite(component)
        ):
            raise TypeError(
                "embedding provider must return finite numeric components"
            )
        vector.append(float(component))
    return vector


def _is_zero_vector(vector: Sequence[float]) -> bool:
    """Return whether a validated vector has no direction for cosine ranking."""

    return not any(component != 0.0 for component in vector)


def _cosine_similarity(
    first: Sequence[float],
    second: Sequence[float],
) -> float:
    """Return cosine similarity after non-zero dimension validation."""

    first_scale = max(abs(component) for component in first)
    second_scale = max(abs(component) for component in second)
    scaled_first = [component / first_scale for component in first]
    scaled_second = [component / second_scale for component in second]
    numerator = math.fsum(
        left * right for left, right in zip(scaled_first, scaled_second)
    )
    first_length = math.sqrt(
        math.fsum(component * component for component in scaled_first)
    )
    second_length = math.sqrt(
        math.fsum(component * component for component in scaled_second)
    )
    return numerator / (first_length * second_length)
