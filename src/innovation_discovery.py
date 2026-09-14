"""
OpenSocial AI – Innovation Discovery Engine

Version 2

The engine combines a problem description with structured evidence.

The evidence-aware layer is intentionally deterministic and transparent.
It does not claim to discover complex patterns from documents yet.

Its purpose is to establish a reliable interface between the
Evidence Layer and the Innovation Discovery Engine.

Future versions can add:
- pattern discovery
- statistical analysis
- document analysis
- AI-assisted reasoning
- cross-source synthesis
- solution generation based on evidence
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional

try:
    from src.evidence import EvidenceItem
except ModuleNotFoundError:
    from evidence import EvidenceItem


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

    # Evidence-aware fields.
    evidence_count: int = 0
    evidence_profile: List[str] = field(default_factory=list)
    evidence_gaps: List[str] = field(default_factory=list)

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

    Existing users of the engine can continue using the original
    analyse(problem) interface.
    """

    def analyse(
        self,
        problem: str,
        evidence: Optional[List[EvidenceItem]] = None,
    ) -> InnovationReport:
        """
        Analyse a problem and optionally incorporate structured evidence.

        Evidence is currently used to build a transparent evidence profile
        and identify important evidence gaps. Complex pattern discovery
        will be added in a later version.
        """

        if not problem or not problem.strip():
            raise ValueError("A problem description is required.")

        problem = problem.strip()
        evidence = evidence or []

        self._validate_evidence(evidence)

        evidence_profile, evidence_gaps = self._build_evidence_profile(
            evidence
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
                    "What important information is still absent from the available evidence?",
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
        )

    @staticmethod
    def _validate_evidence(evidence: List[EvidenceItem]) -> None:
        """Validate evidence before it enters the analysis layer."""

        for item in evidence:
            if not isinstance(item, EvidenceItem):
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
    ) -> tuple[List[str], List[str]]:
        """
        Build a transparent summary of the available evidence.

        This is deliberately descriptive rather than predictive.
        """

        if not evidence:
            profile = [
                "No evidence items supplied. The engine is operating in baseline mode."
            ]

            gaps = [
                "No evidence has been supplied.",
                "Historical change cannot be assessed without dated evidence.",
                "Differences across locations cannot be assessed without location data.",
                "Differences across populations cannot be assessed without population data.",
            ]

            return profile, gaps

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
                if item.location and item.location.strip()
            }
        )

        populations = sorted(
            {
                item.population.strip()
                for item in evidence
                if item.population and item.population.strip()
            }
        )

        dates = sorted(
            {
                item.date.strip()
                for item in evidence
                if item.date and item.date.strip()
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

        gaps: List[str] = []

        if len(source_types) > 1:
            profile.append(
                "Multiple evidence source types are represented, "
                "enabling cross-source comparison."
            )
        else:
            gaps.append(
                "Only one evidence source type is represented; "
                "cross-source comparison is limited."
            )

        if locations:
            profile.append(
                f"Locations represented: {', '.join(locations)}."
            )
        else:
            gaps.append(
                "No location information is available for the evidence."
            )

        if populations:
            profile.append(
                f"Populations represented: {', '.join(populations)}."
            )
        else:
            gaps.append(
                "No population information is available for the evidence."
            )

        if dates:
            profile.append(
                f"Dates represented: {', '.join(dates)}."
            )
        else:
            gaps.append(
                "No dates are available; change over time cannot yet be assessed."
            )

        return profile, gaps


if __name__ == "__main__":
    engine = InnovationDiscoveryEngine()

    report = engine.analyse(
        "Young people are not consistently accessing an available service."
    )

    print("Problem:")
    print(report.problem)

    print("\nReframed Problem:")
    print(report.reframed_problem)

    print("\nEvidence Profile:")
    for item in report.evidence_profile:
        print("-", item)

    print("\nEvidence Gaps:")
    for item in report.evidence_gaps:
        print("-", item)

    print("\nPossible Root Causes:")
    for cause in report.possible_root_causes:
        print("-", cause)

    print("\nSolution Hypotheses:")
    for hypothesis in report.solution_hypotheses:
        print("-", hypothesis.title)

    print("\nValidation Questions:")
    for question in report.validation_questions:
        print("-", question)