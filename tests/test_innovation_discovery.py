import unittest

from src.innovation_discovery import InnovationDiscoveryEngine


class TestInnovationDiscoveryEngine(unittest.TestCase):

    def setUp(self):
        self.engine = InnovationDiscoveryEngine()

    def test_engine_generates_report(self):
        problem = "Young people are not consistently accessing an available service."

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
            "A community programme is experiencing high participant drop-off."
        )

        for solution in report.solution_hypotheses:
            self.assertTrue(solution.title)
            self.assertTrue(solution.rationale)
            self.assertTrue(solution.experiment)


if __name__ == "__main__":
    unittest.main()