"""
OpenSocial AI – Innovation Opportunity Discovery

Version 1.0

Identifies potential innovation opportunities from:
- observed patterns
- evidence gaps
- evidence conflicts
- generated insights
- solution hypotheses

The module is intentionally transparent and model-independent.

It does not claim that an opportunity is proven.

Instead, it identifies promising areas for human investigation,
experimentation and innovation.

Potential opportunity types include:
- emerging_pattern
- unmet_need
- system_bottleneck
- contradiction
- evidence_gap
- transfer_opportunity
"""


from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class InnovationOpportunity:
    """
    Represents a potential innovation opportunity.

    An opportunity is a structured hypothesis that should be
    investigated rather than treated as a confirmed conclusion.
    """

    opportunity_type: str
    title: str
    description: str
    evidence_basis: List[str]
    confidence: str
    uncertainty: List[str]
    investigation_question: str
    suggested_experiment: str

    def to_dict(self) -> Dict:
        """Return the opportunity as a dictionary."""

        return asdict(self)


class InnovationOpportunityDetector:
    """
    Detects potential innovation opportunities from analytical outputs.

    The detector uses transparent rules rather than an AI model.
    This provides an explainable foundation for future AI-assisted
    innovation discovery.
    """

    def detect(
        self,
        patterns: Optional[List] = None,
        evidence_gaps: Optional[List] = None,
        conflicts: Optional[List] = None,
        insights: Optional[List] = None,
        solution_hypotheses: Optional[List] = None,
    ) -> List[InnovationOpportunity]:
        """
        Detect innovation opportunities from available analysis.

        Each analytical layer can contribute a different kind of
        innovation opportunity.
        """

        patterns = patterns or []
        evidence_gaps = evidence_gaps or []
        conflicts = conflicts or []
        insights = insights or []
        solution_hypotheses = solution_hypotheses or []

        opportunities = []

        opportunities.extend(
            self._detect_pattern_opportunities(
                patterns
            )
        )

        opportunities.extend(
            self._detect_gap_opportunities(
                evidence_gaps
            )
        )

        opportunities.extend(
            self._detect_conflict_opportunities(
                conflicts
            )
        )

        opportunities.extend(
            self._detect_transfer_opportunities(
                patterns,
                solution_hypotheses,
            )
        )

        if not opportunities and insights:
            opportunities.extend(
                self._detect_insight_opportunities(
                    insights
                )
            )

        return opportunities

    @staticmethod
    def _detect_pattern_opportunities(
        patterns: List,
    ) -> List[InnovationOpportunity]:
        """Convert recurring patterns into innovation opportunities."""

        opportunities = []

        for pattern in patterns:
            pattern_type = getattr(
                pattern,
                "pattern_type",
                "observed_pattern",
            )

            description = getattr(
                pattern,
                "description",
                str(pattern),
            )

            evidence_count = getattr(
                pattern,
                "evidence_count",
                0,
            )

            confidence = getattr(
                pattern,
                "confidence",
                "exploratory",
            )

            if evidence_count >= 3:
                opportunity_confidence = "moderate"
            else:
                opportunity_confidence = "low"

            opportunities.append(
                InnovationOpportunity(
                    opportunity_type="emerging_pattern",
                    title=(
                        f"Explore the {pattern_type} "
                        "as an innovation opportunity"
                    ),
                    description=(
                        "A recurring pattern has been observed: "
                        f"{description} "
                        "This may indicate an underlying behaviour, "
                        "need or mechanism that could be addressed "
                        "through a new intervention."
                    ),
                    evidence_basis=[
                        description,
                        (
                            f"The pattern appears in "
                            f"{evidence_count} evidence item(s)."
                        ),
                    ],
                    confidence=opportunity_confidence,
                    uncertainty=[
                        "The pattern does not establish causation.",
                        (
                            f"The source pattern confidence is "
                            f"'{confidence}'."
                        ),
                        (
                            "The pattern should be tested in "
                            "additional comparable contexts."
                        ),
                    ],
                    investigation_question=(
                        "What underlying need or mechanism could "
                        "explain this recurring pattern, and could "
                        "a new intervention address it?"
                    ),
                    suggested_experiment=(
                        "Select one comparable setting, investigate "
                        "the pattern with affected people, and test "
                        "a small intervention designed around the "
                        "identified mechanism."
                    ),
                )
            )

        return opportunities

    @staticmethod
    def _detect_gap_opportunities(
        evidence_gaps: List,
    ) -> List[InnovationOpportunity]:
        """Identify opportunities arising from important evidence gaps."""

        opportunities = []

        for gap in evidence_gaps:
            description = getattr(
                gap,
                "description",
                str(gap),
            )

            priority = getattr(
                gap,
                "priority",
                "medium",
            )

            investigation_question = getattr(
                gap,
                "investigation_question",
                (
                    "What additional evidence would help "
                    "understand this gap?"
                ),
            )

            opportunities.append(
                InnovationOpportunity(
                    opportunity_type="evidence_gap",
                    title="Investigate the evidence gap",
                    description=(
                        "An important area is insufficiently "
                        f"understood: {description} "
                        "Closing this gap may reveal an unmet "
                        "need, hidden barrier or new intervention "
                        "opportunity."
                    ),
                    evidence_basis=[
                        description,
                        f"Gap priority: {priority}.",
                    ],
                    confidence="low",
                    uncertainty=[
                        (
                            "The available evidence is insufficient "
                            "to establish the underlying cause."
                        ),
                        (
                            "The opportunity may change as "
                            "additional evidence becomes available."
                        ),
                    ],
                    investigation_question=(
                        investigation_question
                    ),
                    suggested_experiment=(
                        "Conduct a focused evidence-gathering "
                        "exercise with affected communities and "
                        "compare the findings with existing data."
                    ),
                )
            )

        return opportunities

    @staticmethod
    def _detect_conflict_opportunities(
        conflicts: List,
    ) -> List[InnovationOpportunity]:
        """
        Identify innovation opportunities from conflicting evidence.

        Contradictions are treated as potentially valuable signals
        about context rather than automatically treating one source
        as wrong.
        """

        opportunities = []

        for conflict in conflicts:
            description = getattr(
                conflict,
                "description",
                str(conflict),
            )

            investigation_question = getattr(
                conflict,
                "investigation_question",
                (
                    "What contextual differences explain "
                    "the conflicting outcomes?"
                ),
            )

            opportunities.append(
                InnovationOpportunity(
                    opportunity_type="contradiction",
                    title=(
                        "Explore the conditions behind "
                        "conflicting outcomes"
                    ),
                    description=(
                        "Conflicting evidence sources report "
                        "different outcomes. This contradiction "
                        "may reveal that an intervention works "
                        "under some conditions but not others."
                    ),
                    evidence_basis=[
                        description
                    ],
                    confidence="low",
                    uncertainty=[
                        (
                            "The conflicting evidence has not "
                            "yet been reconciled."
                        ),
                        (
                            "Differences in population, location, "
                            "timeframe, measurement or implementation "
                            "conditions may explain the conflict."
                        ),
                    ],
                    investigation_question=(
                        investigation_question
                    ),
                    suggested_experiment=(
                        "Compare the contexts represented by the "
                        "conflicting evidence and test whether a "
                        "context-specific intervention produces "
                        "different outcomes."
                    ),
                )
            )

        return opportunities

    @staticmethod
    def _detect_transfer_opportunities(
        patterns: List,
        solution_hypotheses: List,
    ) -> List[InnovationOpportunity]:
        """
        Identify potential transfer opportunities.

        A recurring pattern combined with an available solution
        hypothesis may indicate that an approach could be tested
        in another comparable context.
        """

        if not patterns or not solution_hypotheses:
            return []

        pattern = patterns[0]
        hypothesis = solution_hypotheses[0]

        pattern_description = getattr(
            pattern,
            "description",
            str(pattern),
        )

        hypothesis_title = getattr(
            hypothesis,
            "title",
            "existing intervention",
        )

        return [
            InnovationOpportunity(
                opportunity_type="transfer_opportunity",
                title=(
                    "Test whether a promising approach "
                    "can transfer across contexts"
                ),
                description=(
                    "A recurring pattern and a possible solution "
                    "hypothesis suggest an opportunity to test "
                    "whether an approach that appears promising "
                    "in one context could work in another "
                    "comparable context."
                ),
                evidence_basis=[
                    pattern_description,
                    (
                        "Solution hypothesis: "
                        f"{hypothesis_title}."
                    ),
                ],
                confidence="exploratory",
                uncertainty=[
                    (
                        "Success in one context does not guarantee "
                        "success in another."
                    ),
                    (
                        "Local implementation conditions may "
                        "substantially affect outcomes."
                    ),
                ],
                investigation_question=(
                    "Which conditions are essential for the "
                    "approach to work, and which can be adapted "
                    "for another context?"
                ),
                suggested_experiment=(
                    "Identify one comparable but different context "
                    "and run a small controlled adaptation of the "
                    "approach while documenting implementation "
                    "conditions."
                ),
            )
        ]

    @staticmethod
    def _detect_insight_opportunities(
        insights: List,
    ) -> List[InnovationOpportunity]:
        """
        Convert a generated insight into an opportunity when
        no stronger structural opportunity has already been found.
        """

        opportunities = []

        for insight in insights:
            title = getattr(
                insight,
                "title",
                "Investigate the generated insight",
            )

            description = getattr(
                insight,
                "insight",
                str(insight),
            )

            confidence = getattr(
                insight,
                "confidence",
                "low",
            )

            uncertainty = getattr(
                insight,
                "uncertainty",
                [],
            )

            investigation_question = getattr(
                insight,
                "investigation_question",
                (
                    "What further evidence would validate "
                    "this insight?"
                ),
            )

            opportunities.append(
                InnovationOpportunity(
                    opportunity_type="unmet_need",
                    title=title,
                    description=(
                        "The generated insight may point toward "
                        f"a potential innovation opportunity: "
                        f"{description}"
                    ),
                    evidence_basis=[
                        description
                    ],
                    confidence=confidence,
                    uncertainty=list(uncertainty),
                    investigation_question=(
                        investigation_question
                    ),
                    suggested_experiment=(
                        "Discuss the insight with affected "
                        "communities and design a small experiment "
                        "to test whether it represents a meaningful "
                        "opportunity."
                    ),
                )
            )

        return opportunities


if __name__ == "__main__":
    detector = InnovationOpportunityDetector()

    opportunities = detector.detect()

    print("Innovation Opportunities")
    print("------------------------")

    for opportunity in opportunities:
        print(
            "-",
            opportunity.title,
        )
        print(
            "  Type:",
            opportunity.opportunity_type,
        )
        print(
            "  Confidence:",
            opportunity.confidence,
        )
        print(
            "  Investigate:",
            opportunity.investigation_question,
        )