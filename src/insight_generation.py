"""
OpenSocial AI – Insight Generation

Version 1.0

Generates evidence-grounded insight candidates from:
- evidence quality
- observed patterns
- evidence conflicts
- evidence gaps

This module does not claim that an insight is proven.

It produces hypotheses that should be investigated by humans.

The design is intentionally model-independent so that an AI
reasoning layer can be added later without changing the core
evidence interfaces.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class InsightCandidate:
    """A hypothesis generated from available evidence."""

    title: str
    insight: str
    evidence_basis: List[str]
    confidence: str
    uncertainty: List[str]
    investigation_question: str

    def to_dict(self) -> Dict:
        """Return the insight as a dictionary."""

        return asdict(self)


class InsightGenerator:
    """
    Generate transparent, evidence-grounded insight candidates.

    The generator does not determine whether an insight is true.
    It identifies relationships or questions that deserve further
    investigation.

    Inputs are deliberately generic so that the module can work
    with the existing evidence, pattern, quality, conflict and
    evidence-gap components.
    """

    def generate(
        self,
        evidence: Optional[List] = None,
        patterns: Optional[List] = None,
        conflicts: Optional[List] = None,
        evidence_gaps: Optional[List] = None,
        evidence_quality: Optional[List] = None,
    ) -> List[InsightCandidate]:
        """
        Generate insight candidates from available analytical signals.

        The generator prioritises:
        1. recurring patterns
        2. corroborated evidence
        3. conflicting evidence
        4. evidence limitations

        No insight is presented as a confirmed causal conclusion.
        """

        evidence = evidence or []
        patterns = patterns or []
        conflicts = conflicts or []
        evidence_gaps = evidence_gaps or []
        evidence_quality = evidence_quality or []

        insights: List[InsightCandidate] = []

        if patterns:
            insights.extend(
                self._generate_pattern_insights(
                    patterns=patterns,
                    evidence=evidence,
                    evidence_quality=evidence_quality,
                    evidence_gaps=evidence_gaps,
                )
            )

        if conflicts:
            insights.append(
                self._generate_conflict_insight(
                    conflicts=conflicts,
                    evidence_gaps=evidence_gaps,
                )
            )

        if not insights and evidence:
            insights.append(
                self._generate_evidence_review_insight(
                    evidence=evidence,
                    evidence_quality=evidence_quality,
                    evidence_gaps=evidence_gaps,
                )
            )

        return insights

    def _generate_pattern_insights(
        self,
        patterns: List,
        evidence: List,
        evidence_quality: List,
        evidence_gaps: List,
    ) -> List[InsightCandidate]:
        """Generate candidates from observed patterns."""

        insights: List[InsightCandidate] = []

        for pattern in patterns:
            pattern_type = getattr(
                pattern,
                "pattern_type",
                "unknown",
            )

            description = getattr(
                pattern,
                "description",
                str(pattern),
            )

            confidence = self._estimate_confidence(
                evidence_quality
            )

            uncertainty = [
                "The observed pattern does not by itself establish causation.",
            ]

            if evidence_gaps:
                uncertainty.append(
                    "Important evidence gaps remain and may affect interpretation."
                )

            if len(evidence) < 3:
                uncertainty.append(
                    "The available evidence base is relatively small."
                )

            title = (
                f"Investigate the {pattern_type} pattern"
            )

            insight = (
                f"The observed pattern — {description} — "
                "may indicate a meaningful relationship that "
                "deserves further investigation."
            )

            investigation_question = (
                "What underlying mechanism could explain this pattern, "
                "and does the same pattern appear in other comparable "
                "contexts?"
            )

            insights.append(
                InsightCandidate(
                    title=title,
                    insight=insight,
                    evidence_basis=[
                        description,
                    ],
                    confidence=confidence,
                    uncertainty=uncertainty,
                    investigation_question=investigation_question,
                )
            )

        return insights

    @staticmethod
    def _generate_conflict_insight(
        conflicts: List,
        evidence_gaps: List,
    ) -> InsightCandidate:
        """Generate an insight candidate from conflicting evidence."""

        evidence_basis = []

        for conflict in conflicts:
            description = getattr(
                conflict,
                "description",
                str(conflict),
            )

            evidence_basis.append(description)

        uncertainty = [
            "Available evidence sources disagree on an outcome.",
            "The disagreement may reflect differences in measurement, "
            "timeframe, population, location or implementation conditions.",
        ]

        if evidence_gaps:
            uncertainty.append(
                "Existing evidence gaps make it difficult to explain "
                "the disagreement confidently."
            )

        return InsightCandidate(
            title="Investigate the conflicting evidence",
            insight=(
                "The disagreement between evidence sources may reveal "
                "an important contextual difference rather than simply "
                "an error in one source."
            ),
            evidence_basis=evidence_basis,
            confidence="low",
            uncertainty=uncertainty,
            investigation_question=(
                "What explains the disagreement between the evidence "
                "sources, and are there different conditions under "
                "which each reported outcome occurs?"
            ),
        )

    @staticmethod
    def _generate_evidence_review_insight(
        evidence: List,
        evidence_quality: List,
        evidence_gaps: List,
    ) -> InsightCandidate:
        """Generate a cautious insight when evidence exists but patterns are limited."""

        uncertainty = [
            "No strong recurring pattern has been identified yet.",
            "The available evidence should be strengthened before "
            "drawing a substantive conclusion.",
        ]

        if evidence_gaps:
            uncertainty.append(
                "Important evidence gaps remain."
            )

        return InsightCandidate(
            title="Strengthen the evidence base",
            insight=(
                "The current evidence may be insufficient to identify "
                "a reliable innovation opportunity. Strengthening the "
                "evidence base could reveal patterns that are not yet visible."
            ),
            evidence_basis=[
                f"{len(evidence)} evidence item(s) are currently available."
            ],
            confidence="low",
            uncertainty=uncertainty,
            investigation_question=(
                "What additional evidence would most improve our ability "
                "to understand the problem and identify a promising intervention?"
            ),
        )

    @staticmethod
    def _estimate_confidence(
        evidence_quality: List,
    ) -> str:
        """
        Estimate insight confidence from available evidence quality.

        This is deliberately conservative.
        """

        if not evidence_quality:
            return "low"

        scores = []

        for quality in evidence_quality:
            score = getattr(
                quality,
                "score",
                0,
            )

            if isinstance(score, (int, float)):
                scores.append(score)

        if not scores:
            return "low"

        average_score = sum(scores) / len(scores)

        if average_score >= 80:
            return "high"

        if average_score >= 60:
            return "moderate"

        return "low"


if __name__ == "__main__":
    generator = InsightGenerator()

    insight_candidates = generator.generate()

    print("Insight Candidates")
    print("------------------")

    for candidate in insight_candidates:
        print("-", candidate.title)
        print(" ", candidate.insight)
        print("  Confidence:", candidate.confidence)
        print(
            "  Investigate:",
            candidate.investigation_question,
        )