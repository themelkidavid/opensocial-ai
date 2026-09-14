"""
OpenSocial AI - Innovation Discovery Engine
Version 1.0

A model-independent framework for analysing social-sector problems
and generating structured, testable solution hypotheses.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict


@dataclass
class SolutionHypothesis:
    """A potential solution that requires human validation."""

    title: str
    rationale: str
    assumptions: List[str]
    risks: List[str]
    experiment: str


@dataclass
class InnovationReport:
    """Structured output from the Innovation Discovery Engine."""

    problem: str
    reframed_problem: str
    key_questions: List[str]
    possible_root_causes: List[str]
    solution_hypotheses: List[SolutionHypothesis]
    validation_questions: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


class InnovationDiscoveryEngine:
    """
    Core engine for structured social-sector innovation analysis.

    This first version is deliberately model-independent.
    An AI model can be connected later without changing the
    overall reasoning structure.
    """

    def analyse(self, problem: str) -> InnovationReport:
        if not problem or not problem.strip():
            raise ValueError("A problem description is required.")

        problem = problem.strip()

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
                    "The problem may be caused partly by friction between "
                    "initial engagement and successful completion."
                ),
                assumptions=[
                    "There are identifiable points where people disengage.",
                    "Some of these barriers can be redesigned."
                ],
                risks=[
                    "The assumed friction point may not be the real cause.",
                    "A redesign could unintentionally exclude some users."
                ],
                experiment=(
                    "Map the current user journey, identify the largest "
                    "drop-off point and test one targeted improvement."
                ),
            ),
            SolutionHypothesis(
                title="Peer-led support",
                rationale=(
                    "People may respond differently when support comes "
                    "from trusted peers rather than formal institutions."
                ),
                assumptions=[
                    "Relevant peer networks exist.",
                    "Participants value peer support."
                ],
                risks=[
                    "Confidentiality risks must be controlled.",
                    "Peer representatives may not reflect all groups."
                ],
                experiment=(
                    "Run a small, supervised peer-support pilot and "
                    "compare engagement with the existing approach."
                ),
            ),
            SolutionHypothesis(
                title="Flexible access model",
                rationale=(
                    "Timing, location or process requirements may prevent "
                    "people from accessing services consistently."
                ),
                assumptions=[
                    "Access constraints materially affect participation.",
                    "The organisation can modify selected service processes."
                ],
                risks=[
                    "Additional operational costs.",
                    "Greater flexibility may require additional safeguards."
                ],
                experiment=(
                    "Test one flexible access option in a limited setting "
                    "and measure uptake, retention and user experience."
                ),
            ),
        ]

        validation_questions = [
            "Do affected communities recognise these barriers?",
            "Which assumptions are supported by evidence?",
            "Which proposed solution would people actually use?",
            "Who could be unintentionally excluded?",
            "What could cause each solution to fail?",
            "What is the smallest safe experiment we can run?",
            "What evidence would justify scaling the intervention?",
        ]

        return InnovationReport(
            problem=problem,
            reframed_problem=reframed_problem,
            key_questions=key_questions,
            possible_root_causes=possible_root_causes,
            solution_hypotheses=solution_hypotheses,
            validation_questions=validation_questions,
        )


if __name__ == "__main__":
    engine = InnovationDiscoveryEngine()

    report = engine.analyse(
        "Young people are not consistently accessing an available service."
    )

    print("\nOPEN SOCIAL AI")
    print("Innovation Discovery Engine v1.0")
    print("=" * 50)

    print("\nPROBLEM")
    print(report.problem)

    print("\nREFRAMED PROBLEM")
    print(report.reframed_problem)

    print("\nKEY QUESTIONS")
    for question in report.key_questions:
        print(f"- {question}")

    print("\nPOSSIBLE ROOT CAUSES")
    for cause in report.possible_root_causes:
        print(f"- {cause}")

    print("\nSOLUTION HYPOTHESES")
    for index, solution in enumerate(report.solution_hypotheses, 1):
        print(f"\n{index}. {solution.title}")
        print(f"   Rationale: {solution.rationale}")
        print("   Experiment:")
        print(f"   {solution.experiment}")

    print("\nVALIDATION QUESTIONS")
    for question in report.validation_questions:
        print(f"- {question}")