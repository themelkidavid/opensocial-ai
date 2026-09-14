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


if __name__ == "__main__":
    unittest.main()