"""
OpenSocial AI – Evidence Quality Assessment

Version 1.0

Provides a transparent, model-independent assessment of evidence quality.

The assessment considers:
- completeness of metadata
- specificity of the evidence
- recency information
- source characteristics
- corroboration across evidence items

The module does not claim that an evidence item is objectively
"true". Instead, it provides a transparent quality signal that
helps human decision-makers understand the strength and limitations
of the available evidence.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

try:
    from src.evidence import EvidenceItem
except ModuleNotFoundError:
    from evidence import EvidenceItem


@dataclass
class EvidenceQuality:
    """Quality assessment for an individual evidence item."""

    score: int
    confidence: str
    strengths: List[str]
    limitations: List[str]

    def to_dict(self) -> Dict:
        """Return the assessment as a dictionary."""
        return asdict(self)


class EvidenceQualityAssessor:
    """
    Assess evidence quality using transparent, deterministic rules.

    The assessor does not determine whether evidence is factually true.
    It evaluates observable characteristics of the supplied evidence.
    """

    def assess(
        self,
        evidence: EvidenceItem,
        all_evidence: Optional[List[EvidenceItem]] = None,
    ) -> EvidenceQuality:
        """
        Assess the quality of one evidence item.

        Parameters:
            evidence:
                The evidence item being assessed.

            all_evidence:
                Optional collection of evidence items used to identify
                corroboration across sources.
        """

        if not isinstance(evidence, EvidenceItem):
            raise TypeError(
                "evidence must be an instance of EvidenceItem."
            )

        self._validate_evidence(evidence)

        score = 0
        strengths = []
        limitations = []

        content = evidence.content.strip()

        # 1. Content specificity
        if len(content) >= 100:
            score += 30
            strengths.append(
                "Evidence contains a reasonably detailed description."
            )
        elif len(content) >= 40:
            score += 20
            strengths.append(
                "Evidence contains some descriptive detail."
            )
        else:
            score += 10
            limitations.append(
                "Evidence content is brief and may lack context."
            )

        # 2. Source information
        if evidence.source_type.strip():
            score += 20
            strengths.append(
                "Evidence source type is identified."
            )
        else:
            limitations.append(
                "Source type is missing."
            )

        # 3. Date information
        if evidence.date and evidence.date.strip():
            score += 15
            strengths.append(
                "Evidence includes date information."
            )
        else:
            limitations.append(
                "Date information is missing, limiting assessment of recency."
            )

        # 4. Location information
        if evidence.location and evidence.location.strip():
            score += 15
            strengths.append(
                "Evidence includes location information."
            )
        else:
            limitations.append(
                "Location information is missing."
            )

        # 5. Population information
        if evidence.population and evidence.population.strip():
            score += 10
            strengths.append(
                "Evidence identifies the population represented."
            )
        else:
            limitations.append(
                "Population information is missing."
            )

        # 6. Corroboration
        evidence_set = all_evidence or [evidence]

        if self._has_corroboration(evidence, evidence_set):
            score += 10
            strengths.append(
                "The evidence is corroborated by another evidence item."
            )
        else:
            limitations.append(
                "No corroborating evidence item was supplied."
            )

        score = min(score, 100)

        confidence = self._confidence_label(score)

        if not limitations:
            strengths.append(
                "No major structural limitations were identified."
            )

        return EvidenceQuality(
            score=score,
            confidence=confidence,
            strengths=strengths,
            limitations=limitations,
        )

    @staticmethod
    def _validate_evidence(evidence: EvidenceItem) -> None:
        """Validate the basic structure of an evidence item."""

        if not evidence.source_type.strip():
            raise ValueError(
                "EvidenceItem source_type cannot be empty."
            )

        if not evidence.content.strip():
            raise ValueError(
                "EvidenceItem content cannot be empty."
            )

    @staticmethod
    def _confidence_label(score: int) -> str:
        """Convert a numerical score into a transparent confidence label."""

        if score >= 80:
            return "high"

        if score >= 60:
            return "moderate"

        return "low"

    @staticmethod
    def _has_corroboration(
        evidence: EvidenceItem,
        all_evidence: List[EvidenceItem],
    ) -> bool:
        """
        Determine whether another evidence item provides potential
        corroboration.

        Corroboration here means that another evidence item exists
        with a different source type and overlapping location or
        population information.
        """

        for other in all_evidence:
            if other is evidence:
                continue

            if not isinstance(other, EvidenceItem):
                continue

            different_source = (
                other.source_type.strip()
                != evidence.source_type.strip()
            )

            same_location = (
                bool(evidence.location)
                and bool(other.location)
                and evidence.location.strip()
                == other.location.strip()
            )

            same_population = (
                bool(evidence.population)
                and bool(other.population)
                and evidence.population.strip()
                == other.population.strip()
            )

            if different_source and (
                same_location or same_population
            ):
                return True

        return False


if __name__ == "__main__":
    assessor = EvidenceQualityAssessor()

    evidence = EvidenceItem(
        source_type="community_feedback",
        content=(
            "Young people reported improved access to services "
            "after peer support was introduced in the programme."
        ),
        date="2025-09-15",
        location="Madurai",
        population="Young people",
    )

    quality = assessor.assess(evidence)

    print("Evidence Quality")
    print("----------------")
    print(f"Score: {quality.score}")
    print(f"Confidence: {quality.confidence}")

    print("\nStrengths:")
    for strength in quality.strengths:
        print("-", strength)

    print("\nLimitations:")
    for limitation in quality.limitations:
        print("-", limitation)