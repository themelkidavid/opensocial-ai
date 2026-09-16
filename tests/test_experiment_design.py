import unittest

from src.experiment_design import (
    ExperimentDesign,
    ExperimentDesignEngine,
)
from src.innovation_reasoning import InnovationHypothesis


class TestExperimentDesignEngine(unittest.TestCase):

    def setUp(self):
        self.engine = ExperimentDesignEngine()

    @staticmethod
    def _create_hypothesis():
        return InnovationHypothesis(
            title="Adapt peer navigation",
            problem_connection="Young people face service barriers.",
            inspiration_source="community inspiration: Peer navigation",
            underlying_mechanism="Trusted peers guide people through services.",
            novel_combination="Adapt peer navigation locally.",
            why_it_might_work="Community members reported access barriers.",
            evidence_basis=["Community feedback"],
            confidence="exploratory",
            uncertainty=["The mechanism may not transfer."],
            experiment="Pilot peer navigation with one community group.",
            validation_question="Does peer navigation improve access?",
        )

    def test_design_creates_structured_experiment(self):
        designs = self.engine.design([self._create_hypothesis()])

        self.assertEqual(len(designs), 1)
        self.assertIsInstance(designs[0], ExperimentDesign)
        self.assertEqual(designs[0].hypothesis_title, "Adapt peer navigation")
        self.assertIn("Community feedback", designs[0].evidence_basis)
        self.assertTrue(designs[0].safeguards)
        self.assertTrue(designs[0].stop_conditions)

    def test_design_preserves_uncertainty(self):
        design = self.engine.design([self._create_hypothesis()])[0]

        uncertainty = " ".join(design.uncertainty).lower()

        self.assertIn("may not transfer", uncertainty)
        self.assertIn("cannot establish", uncertainty)

    def test_design_has_a_stable_experiment_identifier(self):
        hypothesis = self._create_hypothesis()

        first_design = self.engine.design([hypothesis])[0]
        second_design = self.engine.design([hypothesis])[0]

        self.assertTrue(first_design.experiment_id.startswith("experiment-"))
        self.assertEqual(
            first_design.experiment_id,
            second_design.experiment_id,
        )

    def test_empty_hypotheses_return_no_designs(self):
        self.assertEqual(self.engine.design([]), [])

    def test_invalid_hypothesis_is_rejected(self):
        with self.assertRaises(TypeError):
            self.engine.design(["not a hypothesis"])

    def test_design_can_be_converted_to_dict(self):
        result = self.engine.design([self._create_hypothesis()])[0].to_dict()

        expected_fields = [
            "experiment_id",
            "title",
            "hypothesis_title",
            "objective",
            "intervention",
            "comparison",
            "measures",
            "evidence_basis",
            "uncertainty",
            "safeguards",
            "stop_conditions",
            "validation_question",
        ]

        for field in expected_fields:
            self.assertIn(field, result)


if __name__ == "__main__":
    unittest.main()
