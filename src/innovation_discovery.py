"""
OpenSocial AI – Innovation Discovery Engine

Version 5.1

Combines:
- a problem description
- structured evidence
- evidence quality assessment
- observable patterns
- evidence gap analysis
- evidence conflict detection
- evidence-grounded insight generation
- innovation opportunity detection
- innovation inspiration
- innovation reasoning
- innovation combination
- experiment design
- validation and learning

The engine remains model-independent and transparent.

AI-assisted reasoning can be added later without changing
the evidence, quality, pattern, conflict, evidence-gap,
insight, opportunity, inspiration or reasoning interfaces.
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

    from src.innovation_inspiration import (
        InnovationInspiration,
    )

    from src.innovation_reasoning import (
        InnovationReasoningEngine,
        InnovationHypothesis,
    )

    from src.experiment_design import (
        ExperimentDesignEngine,
        ExperimentDesign,
    )

    from src.validation_learning import (
        ValidationLearningEngine,
        ValidationObservation,
        ValidatedLearning,
    )

    from src.persistence import (
        EvidenceProvenance,
        PersistenceStore,
    )

    from src.retrieval import RelevanceRetriever

    from src.narrative_reasoning import (
        NarrativeAnalysis,
        NarrativeReasoningEngine,
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

    from innovation_inspiration import (
        InnovationInspiration,
    )

    from innovation_reasoning import (
        InnovationReasoningEngine,
        InnovationHypothesis,
    )

    from experiment_design import (
        ExperimentDesignEngine,
        ExperimentDesign,
    )

    from validation_learning import (
        ValidationLearningEngine,
        ValidationObservation,
        ValidatedLearning,
    )

    from persistence import (
        EvidenceProvenance,
        PersistenceStore,
    )

    from retrieval import RelevanceRetriever

    from narrative_reasoning import (
        NarrativeAnalysis,
        NarrativeReasoningEngine,
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

    experiment_designs: List[ExperimentDesign] = field(
        default_factory=list
    )

    validated_learning: List[ValidatedLearning] = field(
        default_factory=list
    )

    narrative_analysis: Optional[NarrativeAnalysis] = None

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

    3. Evidence + inspiration mode:
       analyse(
           problem,
           evidence=[...],
           inspirations=[...],
       )

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
        Innovation Combination
           ↓
        Experiment Design
           ↓
        Validation and Learning
           ↓
        Innovation Report
    """

    def __init__(
        self,
        storage: Optional[PersistenceStore] = None,
        retriever: Optional[RelevanceRetriever] = None,
        narrative_reasoning_engine: Optional[NarrativeReasoningEngine] = None,
    ) -> None:
        """Initialise analytical components and optional persistence."""

        self.storage = storage

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

        self.narrative_reasoning_engine = (
            narrative_reasoning_engine or NarrativeReasoningEngine()
        )

        self.insight_generator = (
            InsightGenerator()
        )

        self.innovation_opportunity_detector = (
            InnovationOpportunityDetector()
        )

        self.innovation_reasoning_engine = (
            InnovationReasoningEngine(retriever=retriever)
        )

        self.experiment_design_engine = (
            ExperimentDesignEngine()
        )

        self.validation_learning_engine = (
            ValidationLearningEngine()
        )

    def analyse(
        self,
        problem: str,
        evidence: Optional[List[EvidenceItem]] = None,
        inspirations: Optional[
            List[InnovationInspiration]
        ] = None,
        evidence_provenance: Optional[
            List[EvidenceProvenance]
        ] = None,
        validation_observations: Optional[
            List[ValidationObservation]
        ] = None,
    ) -> InnovationReport:
        """Analyse a problem and atomically persist a storage-backed run."""

        if self.storage is None:
            return self._analyse(
                problem=problem,
                evidence=evidence,
                inspirations=inspirations,
                evidence_provenance=evidence_provenance,
                validation_observations=validation_observations,
            )

        with self.storage.transaction():
            return self._analyse(
                problem=problem,
                evidence=evidence,
                inspirations=inspirations,
                evidence_provenance=evidence_provenance,
                validation_observations=validation_observations,
            )

    def _analyse(
        self,
        problem: str,
        evidence: Optional[List[EvidenceItem]] = None,
        inspirations: Optional[
            List[InnovationInspiration]
        ] = None,
        evidence_provenance: Optional[
            List[EvidenceProvenance]
        ] = None,
        validation_observations: Optional[
            List[ValidationObservation]
        ] = None,
    ) -> InnovationReport:
        """
        Analyse a problem and optionally incorporate evidence
        and innovation inspiration.

        Evidence is validated, quality-assessed, profiled,
        patterns are discovered, potential conflicts are
        identified, evidence gaps are analysed, insights are
        generated, innovation opportunities are identified,
        and innovation hypotheses are generated.

        External inspiration can be supplied to help the
        reasoning layer identify mechanisms that may be
        adapted to the current problem.

        When an optional PersistenceStore is configured, validated
        evidence, generated experiment designs, reviewer-attributed
        observations, and exploratory learning are stored. The default
        remains a fully in-memory workflow.

        Reviewer-attributed validation observations can be supplied
        from prior experiments. They are recorded as exploratory
        learning rather than proof that an intervention works.
        """

        if not problem or not problem.strip():
            raise ValueError(
                "A problem description is required."
            )

        problem = problem.strip()

        evidence = evidence or []

        inspirations = inspirations or []

        validation_observations = (
            validation_observations or []
        )

        self._validate_evidence(
            evidence
        )

        self._validate_inspirations(
            inspirations
        )

        evidence_provenance = self._validate_evidence_provenance(
            evidence,
            evidence_provenance,
        )

        if self.storage is not None:
            stored_evidence = [
                self.storage.save_evidence(item, provenance)
                for item, provenance in zip(evidence, evidence_provenance)
            ]
        else:
            stored_evidence = []

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

        narrative_analysis = self.narrative_reasoning_engine.analyse(
            evidence,
            evidence_ids=(
                [item.evidence_id for item in stored_evidence]
                if stored_evidence else None
            ),
            evidence_provenance=evidence_provenance,
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
                    inspirations=inspirations,
                )
            )

        experiment_designs = (
            self.experiment_design_engine.design(
                innovation_hypotheses
            )
        )

        if self.storage is not None:
            analysis_evidence_ids = list(
                dict.fromkeys(
                    stored_record.evidence_id
                    for stored_record in stored_evidence
                )
            )
            experiment_designs = [
                experiment_design.with_analysis_evidence_ids(
                    analysis_evidence_ids
                )
                for experiment_design in experiment_designs
            ]
            experiment_designs = [
                self.storage.save_experiment(experiment_design).experiment
                for experiment_design in experiment_designs
            ]

            stored_observations = [
                self.storage.record_observation(observation)
                for observation in validation_observations
            ]
        else:
            stored_observations = []

        validated_learning = (
            self.validation_learning_engine.evaluate(
                validation_observations
            )
        )

        if self.storage is not None:
            for learning, stored_observation in zip(
                validated_learning,
                stored_observations,
            ):
                self.storage.save_learning(
                    learning,
                    stored_observation.observation_id,
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

        if experiment_designs:
            validation_questions.append(
                "Who will review the pilot evidence with affected "
                "communities before any decision to scale?"
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
            experiment_designs=experiment_designs,
            validated_learning=validated_learning,
            narrative_analysis=narrative_analysis,
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
    def _validate_inspirations(
        inspirations: List[InnovationInspiration],
    ) -> None:
        """Validate innovation inspiration before analysis."""

        for inspiration in inspirations:
            if not isinstance(
                inspiration,
                InnovationInspiration,
            ):
                raise TypeError(
                    "All inspirations must be instances "
                    "of InnovationInspiration."
                )

    @staticmethod
    def _validate_evidence_provenance(
        evidence: List[EvidenceItem],
        provenance: Optional[List[EvidenceProvenance]],
    ) -> List[Optional[EvidenceProvenance]]:
        """Keep optional provenance aligned with the supplied evidence."""

        if provenance is None:
            return [None] * len(evidence)

        if not isinstance(provenance, list):
            raise TypeError("evidence_provenance must be a list")

        if len(provenance) != len(evidence):
            raise ValueError(
                "evidence_provenance must align with every evidence item"
            )

        for item in provenance:
            if not isinstance(item, EvidenceProvenance):
                raise TypeError(
                    "All provenance records must be instances of "
                    "EvidenceProvenance."
                )

        return provenance

    @staticmethod
    def _build_evidence_profile(
        evidence: List[EvidenceItem],
    ) -> List[str]:
        """Build a transparent profile of the available evidence."""

        if not evidence:
            return [
                "No evidence items supplied. "
                "The engine is operating in baseline mode."
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
                f"Locations represented: "
                f"{', '.join(locations)}."
            )

        if populations:
            profile.append(
                f"Populations represented: "
                f"{', '.join(populations)}."
            )

        if dates:
            profile.append(
                f"Dates represented: "
                f"{', '.join(dates)}."
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
        "Young people are not consistently accessing "
        "an available service.",
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
            f"  Investigate: "
            f"{insight.investigation_question}"
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
            f"  Problem Connection: "
            f"{hypothesis.problem_connection}"
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
        print(
            "-",
            hypothesis.title,
        )
