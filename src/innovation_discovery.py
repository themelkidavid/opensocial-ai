"""
OpenSocial AI – Innovation Discovery Engine

Version 5.0

Combines:
- a problem description
- structured evidence
- evidence quality assessment
- observable patterns
- evidence gap analysis
- evidence conflict detection
- evidence-grounded insight generation
- innovation opportunity detection
- innovation reasoning
- innovation hypothesis generation

The engine remains model-independent and transparent.

AI-assisted reasoning can be added later without changing
the evidence, quality, pattern, conflict, evidence-gap,
insight, or opportunity interfaces.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional


try:
    from src.evidence import EvidenceItem

    from src.pattern_discovery import (
        PatternDiscovery,
        ObservedPattern,
    )

    from src.evidence_gap import (
        EvidenceGapAnalysis,
        EvidenceGap,
    )

    from src.evidence_quality import (
        EvidenceQualityAssessor,
        EvidenceQuality,
    )

    from src.evidence_conflict import (
        EvidenceConflictDetector,
        EvidenceConflict,
    )

    from src.insight_generation import (
        InsightGenerator,
        InsightCandidate,
    )

    from src.innovation_opportunity import (
        InnovationOpportunityDetector,
        InnovationOpportunity,
    )

    from src.innovation_reasoning import (
        InnovationReasoningEngine,
        InnovationHypothesis,
    )

except ModuleNotFoundError:

    from evidence import EvidenceItem

    from pattern_discovery import (
        PatternDiscovery,
        ObservedPattern,
    )

    from evidence_gap import (
        EvidenceGapAnalysis,
        EvidenceGap,
    )

    from evidence_quality import (
        EvidenceQualityAssessor,
        EvidenceQuality,
    )

    from evidence_conflict import (
        EvidenceConflictDetector,
        EvidenceConflict,
    )

    from insight_generation import (
        InsightGenerator,
        InsightCandidate,
    )

    from innovation_opportunity import (
        InnovationOpportunityDetector,
        InnovationOpportunity,
    )

    from innovation_reasoning import (
        InnovationReasoningEngine,
        InnovationHypothesis,
    )


@dataclass
class SolutionHypothesis:
    """A possible solution that can be tested through an experiment."""

    title: str
    rationale: str
    assumptions: List[str]
    risks: List[str]
    experiment: str


@dataclass
class InnovationReport:
    """Structured output produced by the Innovation Discovery Engine."""

    problem: str
    reframed_problem: str
    key_questions: List[str]
    possible_root_causes: List[str]
    solution_hypotheses: List[SolutionHypothesis]
    validation_questions: List[str]

    evidence_count: int = 0

    evidence_profile: List[str] = field(
        default_factory=list
    )

    evidence_gaps: List[str] = field(
        default_factory=list
    )

    observed_patterns: List[ObservedPattern] = field(
        default_factory=list
    )

    evidence_gap_details: List[EvidenceGap] = field(
        default_factory=list
    )

    evidence_quality: List[EvidenceQuality] = field(
        default_factory=list
    )

    evidence_conflicts: List[EvidenceConflict] = field(
        default_factory=list
    )

    insights: List[InsightCandidate] = field(
        default_factory=list
    )

    innovation_opportunities: List[InnovationOpportunity] = field(
        default_factory=list
    )

    innovation_hypotheses: List[InnovationHypothesis] = field(
        default_factory=list
    )

    def to_dict(self) -> Dict:
        """Return the complete report as a dictionary."""

        return asdict(self)


class InnovationDiscoveryEngine:
    """
    Model-independent Innovation Discovery Engine.

    The engine can operate in two modes:

    1. Baseline mode:
       analyse(problem)

    2. Evidence-aware mode:
       analyse(problem, evidence=[...])

    Evidence-aware analysis runs:

        Evidence
           ↓
        Evidence Quality
           ↓
        Pattern Discovery
           ↓
        Conflict Detection
           ↓
        Evidence Gap Analysis
           ↓
        Insight Generation
           ↓
        Innovation Opportunity Detection
           ↓
        Innovation Reasoning
           ↓
        Innovation Hypotheses
           ↓
        Innovation Report
    """

    def __init__(self) -> None:
        """Initialise the analytical components."""

        self.pattern_discovery = PatternDiscovery()

        self.evidence_gap_analysis = (
            EvidenceGapAnalysis()
        )

        self.evidence_quality_assessor = (
            EvidenceQualityAssessor()
        )

        self.evidence_conflict_detector = (
            EvidenceConflictDetector()
        )

        self.insight_generator = (
            InsightGenerator()
        )

        self.innovation_opportunity_detector = (
            InnovationOpportunityDetector()
        )

        self.innovation_reasoning_engine = (
            InnovationReasoningEngine()
        )

    def analyse(
        self,
        problem: str,
        evidence: Optional[List[EvidenceItem]] = None,
    ) -> InnovationReport:
        """
        Analyse a problem and optionally incorporate evidence.

        Evidence is validated, quality-assessed, profiled,
        patterns are discovered, potential conflicts are
        identified, evidence gaps are analysed, insights are
        generated, innovation opportunities are identified,
        and innovation hypotheses are generated before the
        final report is created.
        """

        if not problem or not problem.strip():
            raise ValueError(
                "A problem description is required."
            )

        problem = problem.strip()

        evidence = evidence or []

        self._validate_evidence(
            evidence
        )

        evidence_profile = (
            self._build_evidence_profile(
                evidence
            )
        )

        evidence_quality = [
            self.evidence_quality_assessor.assess(
                item,
                all_evidence=evidence,
            )
            for item in evidence
        ]

        observed_patterns = (
            self.pattern_discovery.discover(
                evidence
            )
        )

        evidence_conflicts = (
            self.evidence_conflict_detector.discover(
                evidence
            )
        )

        evidence_gap_details = (
            self.evidence_gap_analysis.discover(
                evidence
            )
        )

        evidence_gaps = [
            gap.description
            for gap in evidence_gap_details
        ]

        insights = (
            self.insight_generator.generate(
                evidence=evidence,
                patterns=observed_patterns,
                conflicts=evidence_conflicts,
                evidence_gaps=evidence_gaps,
                evidence_quality=evidence_quality,
            )
        )

        reframed_problem = (
            f"Instead of assuming that '{problem}' has a single cause, "
            "investigate the underlying barriers, behaviours, systems "
            "and contextual factors contributing to the problem."
        )

        key_questions = [
            "Who is affected by the problem?",
            "Where and when does the problem occur?",
            "How has the problem changed over time?",
            "What has already been attempted?",
            "Where does the largest drop-off or failure occur?",
            "What evidence supports the current explanation?",
            "What information is still missing?",
        ]

        if evidence:
            key_questions.extend(
                [
                    "Which evidence items support or challenge the current explanation?",
                    "Where do different evidence sources agree or disagree?",
                    "Which observed patterns deserve further investigation?",
                    "Which evidence gaps are most important to address first?",
                    "What important information is still absent from the available evidence?",
                    "Which evidence items have the strongest quality signals?",
                    "Why do any conflicting evidence sources report different outcomes?",
                ]
            )

        else:
            key_questions.append(
                "What evidence should be collected before testing a solution?"
            )

        possible_root_causes = [
            "Access or geographic barriers",
            "Economic or resource constraints",
            "Trust, stigma or social barriers",
            "Service design or user-experience problems",
            "Institutional or organisational constraints",
            "Communication and information gaps",
            "Cultural or contextual factors",
        ]

        solution_hypotheses = [
            SolutionHypothesis(
                title="Redesign the user journey",
                rationale=(
                    "The problem may be partly caused by unnecessary "
                    "friction between the person and the service."
                ),
                assumptions=[
                    "There are identifiable points where people drop out.",
                    "Some barriers can be changed through service redesign.",
                ],
                risks=[
                    "Redesign may address symptoms rather than deeper causes.",
                    "Changes may unintentionally exclude some groups.",
                ],
                experiment=(
                    "Map the current user journey with community members, "
                    "identify the largest friction points, and test one "
                    "small redesign."
                ),
            ),
            SolutionHypothesis(
                title="Peer-led support",
                rationale=(
                    "People may respond differently when support comes from "
                    "trusted peers with relevant lived experience."
                ),
                assumptions=[
                    "Peers are trusted by the target population.",
                    "Peer supporters can be trained and supported.",
                ],
                risks=[
                    "Peer supporters may experience overload or burnout.",
                    "Peer support may not reach people who are highly isolated.",
                ],
                experiment=(
                    "Recruit and train a small group of peer supporters "
                    "and compare engagement with the existing approach."
                ),
            ),
            SolutionHypothesis(
                title="Flexible access model",
                rationale=(
                    "Fixed service models may not fit the schedules, "
                    "locations or circumstances of the people affected."
                ),
                assumptions=[
                    "Access constraints contribute meaningfully to the problem.",
                    "The organisation can test alternative access arrangements.",
                ],
                risks=[
                    "Flexible delivery may increase operational complexity.",
                    "Demand may exceed the capacity of the new model.",
                ],
                experiment=(
                    "Test one alternative access option, such as extended "
                    "hours, outreach, mobile delivery or digital support."
                ),
            ),
        ]

        innovation_opportunities = (
            self.innovation_opportunity_detector.detect(
                patterns=observed_patterns,
                evidence_gaps=evidence_gap_details,
                conflicts=evidence_conflicts,
                insights=insights,
                solution_hypotheses=solution_hypotheses,
            )
        )

        innovation_hypotheses = []

        if evidence:
            innovation_hypotheses = (
                self.innovation_reasoning_engine.generate(
                    problem=problem,
                    opportunities=innovation_opportunities,
                )
            )

        validation_questions = [
            "Do community members recognise this problem and its causes?",
            "What evidence supports each proposed explanation?",
            "Do the proposed solutions address a meaningful barrier?",
            "Would the intended users actually use the proposed solution?",
            "Could the intervention unintentionally exclude anyone?",
            "What is the smallest safe experiment that could test the idea?",
            "What evidence would indicate that the experiment worked?",
            "What evidence would indicate that the idea should be abandoned?",
            "What would need to be true before scaling the intervention?",
        ]

        if evidence_conflicts:
            validation_questions.extend(
                [
                    "What explains the disagreement between the conflicting evidence sources?",
                    "Are the conflicting sources measuring the same outcome in the same way?",
                    "Do differences in location, population or timeframe explain the conflict?",
                ]
            )

        if insights:
            validation_questions.append(
                "Which generated insights should be tested with affected communities before acting on them?"
            )

        if innovation_opportunities:
            validation_questions.extend(
                [
                    "Which innovation opportunity has the strongest evidence basis?",
                    "Which opportunity should be tested first?",
                    "What assumptions must be tested before investing significant resources?",
                    "What would make us stop, adapt or scale the experiment?",
                ]
            )

        if innovation_hypotheses:
            validation_questions.extend(
                [
                    "Which innovation hypothesis has the strongest evidence basis?",
                    "Which innovation hypothesis should be tested first?",
                    "What assumptions must be tested before investing resources?",
                    "What evidence would confirm or challenge the innovation hypothesis?",
                    "What would make us stop, adapt or scale the innovation experiment?",
                ]
            )

        return InnovationReport(
            problem=problem,
            reframed_problem=reframed_problem,
            key_questions=key_questions,
            possible_root_causes=possible_root_causes,
            solution_hypotheses=solution_hypotheses,
            validation_questions=validation_questions,
            evidence_count=len(evidence),
            evidence_profile=evidence_profile,
            evidence_gaps=evidence_gaps,
            observed_patterns=observed_patterns,
            evidence_gap_details=evidence_gap_details,
            evidence_quality=evidence_quality,
            evidence_conflicts=evidence_conflicts,
            insights=insights,
            innovation_opportunities=innovation_opportunities,
            innovation_hypotheses=innovation_hypotheses,
        )

    @staticmethod
    def _validate_evidence(
        evidence: List[EvidenceItem],
    ) -> None:
        """Validate evidence before analysis."""

        for item in evidence:
            if not isinstance(
                item,
                EvidenceItem,
            ):
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
    def _build_evidence_profile(
        evidence: List[EvidenceItem],
    ) -> List[str]:
        """Build a transparent profile of the available evidence."""

        if not evidence:
            return [
                "No evidence items supplied. The engine is operating in baseline mode."
            ]

        source_types = sorted(
            {
                item.source_type.strip()
                for item in evidence
                if item.source_type.strip()
            }
        )

        locations = sorted(
            {
                item.location.strip()
                for item in evidence
                if item.location
                and item.location.strip()
            }
        )

        populations = sorted(
            {
                item.population.strip()
                for item in evidence
                if item.population
                and item.population.strip()
            }
        )

        dates = sorted(
            {
                item.date.strip()
                for item in evidence
                if item.date
                and item.date.strip()
            }
        )

        profile = [
            f"{len(evidence)} evidence item(s) supplied.",
            (
                "Source types represented: "
                + ", ".join(source_types)
                + "."
            ),
        ]

        if len(source_types) > 1:
            profile.append(
                "Multiple evidence source types are represented, "
                "enabling cross-source comparison."
            )

        if locations:
            profile.append(
                f"Locations represented: {', '.join(locations)}."
            )

        if populations:
            profile.append(
                f"Populations represented: {', '.join(populations)}."
            )

        if dates:
            profile.append(
                f"Dates represented: {', '.join(dates)}."
            )

        return profile


if __name__ == "__main__":
    engine = InnovationDiscoveryEngine()

    evidence = [
        EvidenceItem(
            source_type="programme_report",
            content=(
                "Service uptake increased after peer support "
                "was introduced."
            ),
            date="2025-06-30",
            location="Madurai",
            population="Young people",
        ),
        EvidenceItem(
            source_type="community_feedback",
            content=(
                "Young people reported that service uptake "
                "decreased after peer support."
            ),
            date="2025-09-15",
            location="Madurai",
            population="Young people",
        ),
    ]

    report = engine.analyse(
        "Young people are not consistently accessing an available service.",
        evidence=evidence,
    )

    print("Problem:")
    print(report.problem)

    print("\nEvidence Profile:")
    for item in report.evidence_profile:
        print("-", item)

    print("\nEvidence Quality:")
    for quality in report.evidence_quality:
        print(
            f"- Score: {quality.score} "
            f"| Confidence: {quality.confidence}"
        )

    print("\nObserved Patterns:")
    for pattern in report.observed_patterns:
        print(
            f"- [{pattern.pattern_type}] "
            f"{pattern.description}"
        )

    print("\nEvidence Conflicts:")
    for conflict in report.evidence_conflicts:
        print("-", conflict.description)
        print(
            f"  Investigate: "
            f"{conflict.investigation_question}"
        )

    print("\nEvidence Gaps:")
    for gap in report.evidence_gap_details:
        print(
            f"- [{gap.priority}] "
            f"{gap.description}"
        )
        print(
            f"  Investigate: "
            f"{gap.investigation_question}"
        )

    print("\nGenerated Insights:")
    for insight in report.insights:
        print(
            f"- {insight.title}"
        )
        print(
            f"  Insight: {insight.insight}"
        )
        print(
            f"  Confidence: {insight.confidence}"
        )
        print(
            f"  Investigate: {insight.investigation_question}"
        )

    print("\nInnovation Opportunities:")
    for opportunity in report.innovation_opportunities:
        print(
            f"- [{opportunity.opportunity_type}] "
            f"{opportunity.title}"
        )
        print(
            f"  Confidence: {opportunity.confidence}"
        )
        print(
            f"  Description: {opportunity.description}"
        )
        print(
            f"  Investigate: "
            f"{opportunity.investigation_question}"
        )
        print(
            f"  Experiment: "
            f"{opportunity.suggested_experiment}"
        )

    print("\nInnovation Hypotheses:")
    for hypothesis in report.innovation_hypotheses:
        print(
            f"- {hypothesis.title}"
        )
        print(
            f"  Inspiration: "
            f"{hypothesis.inspiration_source}"
        )
        print(
            f"  Mechanism: "
            f"{hypothesis.underlying_mechanism}"
        )
        print(
            f"  Novel Combination: "
            f"{hypothesis.novel_combination}"
        )
        print(
            f"  Why It Might Work: "
            f"{hypothesis.why_it_might_work}"
        )
        print(
            f"  Confidence: "
            f"{hypothesis.confidence}"
        )
        print(
            f"  Experiment: "
            f"{hypothesis.experiment}"
        )
        print(
            f"  Validate: "
            f"{hypothesis.validation_question}"
        )

    print("\nSolution Hypotheses:")
    for hypothesis in report.solution_hypotheses:
        print("-", hypothesis.title)