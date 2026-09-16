"""Mechanism-based, cautious discovery of cross-sector inspirations."""

from dataclasses import asdict, dataclass
from typing import Dict, List, Optional


try:
    from src.innovation_inspiration import (
        InnovationInspiration,
        InnovationInspirationEngine,
    )
    from src.retrieval import KeywordRetriever, RelevanceRetriever
except ModuleNotFoundError:
    from innovation_inspiration import (
        InnovationInspiration,
        InnovationInspirationEngine,
    )
    from retrieval import KeywordRetriever, RelevanceRetriever


@dataclass
class CrossSectorCandidate:
    """A candidate inspiration, never a recommendation or proven intervention."""

    inspiration: InnovationInspiration
    source_sector: Optional[str]
    target_sector: Optional[str]
    retrieval_strategy: str
    retrieval_score: float
    diversity_boost: float
    ranking_score: float
    is_cross_sector: bool
    why_it_may_be_relevant: str
    uncertainty: List[str]
    adaptation_questions: List[str]

    def to_dict(self) -> Dict:
        """Return a serializable, explicit candidate record."""

        result = asdict(self)
        result["inspiration"] = self.inspiration.to_dict()
        return result


class CrossSectorDiscoveryEngine:
    """Find potentially relevant mechanisms without presuming transferability."""

    def __init__(
        self,
        retriever: Optional[RelevanceRetriever] = None,
    ) -> None:
        self.inspiration_engine = InnovationInspirationEngine(
            retriever=retriever or KeywordRetriever()
        )

    def discover(
        self,
        problem: str,
        inspirations: Optional[List[InnovationInspiration]] = None,
        target_sector: Optional[str] = None,
        prefer_cross_sector: bool = False,
        cross_sector_boost: float = 0.0,
        minimum_score: Optional[float] = None,
    ) -> List[CrossSectorCandidate]:
        """Return ranked candidate mechanisms from the supplied corpus only."""

        target_sector = _optional_sector(target_sector, "target_sector")
        if not isinstance(prefer_cross_sector, bool):
            raise TypeError("prefer_cross_sector must be a boolean")
        if not isinstance(cross_sector_boost, (int, float)):
            raise TypeError("cross_sector_boost must be numeric")
        if minimum_score is not None and not isinstance(minimum_score, (int, float)):
            raise TypeError("minimum_score must be numeric or None")

        matches = self.inspiration_engine.find_relevant_matches(
            problem,
            inspirations,
        )
        candidates = []
        for position, match in enumerate(matches):
            if minimum_score is not None and match.score < minimum_score:
                continue
            inspiration = match.inspiration
            source_sector = inspiration.sector
            is_cross_sector = bool(
                source_sector and target_sector and source_sector != target_sector
            )
            diversity_boost = (
                float(cross_sector_boost)
                if prefer_cross_sector and is_cross_sector
                else 0.0
            )
            candidates.append(
                (
                    -match.score - diversity_boost,
                    position,
                    CrossSectorCandidate(
                        inspiration=inspiration,
                        source_sector=source_sector,
                        target_sector=target_sector,
                        retrieval_strategy=match.strategy,
                        retrieval_score=match.score,
                        diversity_boost=diversity_boost,
                        ranking_score=match.score + diversity_boost,
                        is_cross_sector=is_cross_sector,
                        why_it_may_be_relevant=_why_relevant(
                            inspiration,
                            match.strategy,
                            match.score,
                            source_sector,
                            target_sector,
                        ),
                        uncertainty=_uncertainty(
                            inspiration,
                            source_sector,
                            target_sector,
                        ),
                        adaptation_questions=_adaptation_questions(inspiration),
                    ),
                )
            )

        candidates.sort(key=lambda item: (item[0], item[1]))
        return [candidate for _, _, candidate in candidates]


def _optional_sector(value: Optional[str], name: str) -> Optional[str]:
    """Normalize optional sector metadata without creating a value."""

    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text or None")
    return value.strip().lower() or None


def _why_relevant(
    inspiration: InnovationInspiration,
    strategy: str,
    score: float,
    source_sector: Optional[str],
    target_sector: Optional[str],
) -> str:
    """Explain the candidate mechanism and ranking without an outcome claim."""

    sector_context = (
        f"The source sector is '{source_sector}' and the target sector is "
        f"'{target_sector}'."
        if source_sector and target_sector
        else "Source or target sector is unknown."
    )
    return (
        f"Candidate inspiration retrieved by {strategy} with score {score:.3f} "
        f"because its documented mechanism is: {inspiration.mechanism} "
        f"{sector_context} This indicates potential relevance only."
    )


def _uncertainty(
    inspiration: InnovationInspiration,
    source_sector: Optional[str],
    target_sector: Optional[str],
) -> List[str]:
    """State transfer uncertainty explicitly, including unknown metadata."""

    uncertainty = [
        "This is a candidate inspiration, not evidence of effectiveness or a recommendation.",
        "A retrieval score does not establish contextual equivalence or transferability.",
        f"Reported transferability status is '{inspiration.transferability}' and requires local review.",
    ]
    if source_sector and target_sector and source_sector != target_sector:
        uncertainty.append(
            "Sector difference does not establish that the mechanism will transfer."
        )
    if not source_sector or not target_sector:
        uncertainty.append(
            "Unknown sector metadata limits comparison and requires contextual investigation."
        )
    return uncertainty


def _adaptation_questions(inspiration: InnovationInspiration) -> List[str]:
    """Generate questions for human investigation, not transfer conclusions."""

    questions = [
        "What assumptions from the source context may not hold here?",
        "What infrastructure and resources does this mechanism depend on?",
        "What unintended effects or exclusions are plausible?",
        "Which evidence gaps should be resolved before considering a pilot?",
    ]
    if inspiration.target_population:
        questions.insert(
            1,
            f"How might the source population '{inspiration.target_population}' differ from the affected population here?",
        )
    if inspiration.geography:
        questions.insert(
            1,
            f"Which geographic or contextual assumptions from '{inspiration.geography}' require review?",
        )
    return questions
