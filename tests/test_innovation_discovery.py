import unittest

from src.evidence import create_evidence
from src.innovation_discovery import InnovationDiscoveryEngine


class TestInnovationDiscoveryEngine(unittest.TestCase):

    def setUp(self):
        self.engine = InnovationDiscoveryEngine()

    def test_engine_generates_report(self):
        problem = (
            "Young people are not consistently accessing "
            "an available service."
        )

        report = self.engine.analyse(problem)

        self.assertEqual(report.problem, problem)
        self.assertTrue(report.reframed_problem)
        self.assertGreater(len(report.key_questions), 0)
        self.assertGreater(len(report.possible_root_causes), 0)
        self.assertGreater(len(report.solution_hypotheses), 0)
        self.assertGreater(len(report.validation_questions), 0)

    def test_empty_problem_is_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.analyse("")

    def test_solution_hypotheses_have_experiments(self):
        report = self.engine.analyse(
            "A community programme is experiencing "
            "high participant drop-off."
        )

        for solution in report.solution_hypotheses:
            self.assertTrue(solution.title)
            self.assertTrue(solution.rationale)
            self.assertTrue(solution.experiment)

    def test_evidence_quality_is_included_in_report(self):
        evidence = [
            create_evidence(
                source_type="community_feedback",
                content=(
                    "Young people reported improved access "
                    "to services."
                ),
                date="2025-09-15",
                location="Madurai",
                population="Young people",
            )
        ]

        report = self.engine.analyse(
            "Young people are not consistently accessing "
            "an available service.",
            evidence=evidence,
        )

        self.assertEqual(len(report.evidence_quality), 1)

        quality = report.evidence_quality[0]

        self.assertGreater(quality.score, 0)
        self.assertIn(
            quality.confidence,
            ["low", "moderate", "high"],
        )

    def test_each_evidence_item_gets_quality_assessment(self):
        evidence = [
            create_evidence(
                source_type="community_feedback",
                content=(
                    "Young people reported improved access "
                    "to services."
                ),
                date="2025-09-15",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="programme_report",
                content=(
                    "Programme records show increased "
                    "service uptake."
                ),
                date="2025-09-30",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people are not consistently accessing "
            "an available service.",
            evidence=evidence,
        )

        self.assertEqual(report.evidence_count, 2)
        self.assertEqual(len(report.evidence_quality), 2)

        for quality in report.evidence_quality:
            self.assertGreaterEqual(quality.score, 0)
            self.assertLessEqual(quality.score, 100)
            self.assertIn(
                quality.confidence,
                ["low", "moderate", "high"],
            )

    def test_evidence_quality_detects_corroboration(self):
        evidence = [
            create_evidence(
                source_type="community_feedback",
                content=(
                    "Young people reported improved access "
                    "to services after peer support."
                ),
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="programme_report",
                content=(
                    "Programme records indicate increased "
                    "service uptake."
                ),
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people are not consistently accessing "
            "an available service.",
            evidence=evidence,
        )

        self.assertEqual(len(report.evidence_quality), 2)

        for quality in report.evidence_quality:
            strengths = " ".join(
                quality.strengths
            ).lower()

            self.assertIn(
                "corroborated",
                strengths,
            )

    def test_conflicting_evidence_is_included_in_report(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content=(
                    "Service uptake increased after "
                    "peer support was introduced."
                ),
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content=(
                    "Young people reported that service "
                    "uptake decreased."
                ),
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people are not consistently accessing "
            "an available service.",
            evidence=evidence,
        )

        self.assertEqual(len(report.evidence_conflicts), 1)

        conflict = report.evidence_conflicts[0]

        self.assertEqual(conflict.first_index, 0)
        self.assertEqual(conflict.second_index, 1)

        self.assertIn(
            "conflicting",
            conflict.description.lower(),
        )

    def test_non_conflicting_evidence_produces_no_conflicts(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content=(
                    "Service uptake increased after "
                    "peer support was introduced."
                ),
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content=(
                    "Young people reported improved "
                    "access to the service."
                ),
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people are not consistently accessing "
            "an available service.",
            evidence=evidence,
        )

        self.assertEqual(
            report.evidence_conflicts,
            [],
        )

    def test_conflicts_add_validation_questions(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Service uptake decreased.",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people are not consistently accessing "
            "an available service.",
            evidence=evidence,
        )

        questions = " ".join(
            report.validation_questions
        ).lower()

        self.assertIn(
            "disagreement",
            questions,
        )

    def test_report_contains_all_evidence_analysis_layers(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content=(
                    "Service uptake increased after "
                    "peer support was introduced."
                ),
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content=(
                    "Young people reported that service "
                    "uptake decreased after peer support."
                ),
                date="2025-09-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people are not consistently accessing "
            "an available service.",
            evidence=evidence,
        )

        self.assertEqual(report.evidence_count, 2)
        self.assertEqual(len(report.evidence_quality), 2)
        self.assertGreater(
            len(report.observed_patterns),
            0,
        )
        self.assertEqual(
            len(report.evidence_conflicts),
            1,
        )

        self.assertIsInstance(
            report.evidence_gaps,
            list,
        )

    def test_report_can_be_converted_to_dict(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            )
        ]

        report = self.engine.analyse(
            "Community members are not consistently "
            "using a service.",
            evidence=evidence,
        )

        result = report.to_dict()

        self.assertIn("problem", result)
        self.assertIn("evidence_count", result)
        self.assertIn("evidence_quality", result)
        self.assertIn("evidence_conflicts", result)
        self.assertIn("observed_patterns", result)
        self.assertIn("evidence_gaps", result)
        self.assertIn("solution_hypotheses", result)


if __name__ == "__main__":
    unittest.main()