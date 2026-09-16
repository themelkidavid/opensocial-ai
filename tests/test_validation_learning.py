import unittest

from src.validation_learning import (
    ValidatedLearning,
    ValidationLearningEngine,
    ValidationObservation,
)


class TestValidationLearningEngine(unittest.TestCase):

    def setUp(self):
        self.engine = ValidationLearningEngine()

    def _create_observation(self):
        return self.engine.create_observation(
            experiment_id="experiment-3f7b0c76fbc1d265",
            experiment_title="Pilot: Adapt peer navigation",
            outcome="Participants reported that peer navigation reduced confusion.",
            evidence_basis=["Pilot feedback from participating young people."],
            limitations=["The pilot involved one community group."],
            reviewer="Community programme lead",
        )

    def test_create_observation_requires_reviewer_and_evidence(self):
        with self.assertRaises(ValueError):
            self.engine.create_observation(
                experiment_id="experiment-3f7b0c76fbc1d265",
                experiment_title="Pilot",
                outcome="Access improved.",
                evidence_basis=[],
                reviewer="",
            )

    def test_create_observation_allows_empty_limitations(self):
        observation = self.engine.create_observation(
            experiment_id="experiment-3f7b0c76fbc1d265",
            experiment_title="Pilot: Adapt peer navigation",
            outcome="Participants reported fewer barriers.",
            evidence_basis=["Pilot feedback"],
            reviewer="Community programme lead",
        )

        self.assertEqual(observation.limitations, [])

    def test_evaluate_creates_exploratory_learning(self):
        learning = self.engine.evaluate([self._create_observation()])

        self.assertEqual(len(learning), 1)
        self.assertIsInstance(learning[0], ValidatedLearning)
        self.assertEqual(learning[0].confidence, "exploratory")
        self.assertEqual(learning[0].reviewer, "Community programme lead")
        self.assertIn(
            "does not establish",
            " ".join(learning[0].limitations).lower(),
        )

    def test_empty_observations_return_no_learning(self):
        self.assertEqual(self.engine.evaluate([]), [])

    def test_invalid_observation_is_rejected(self):
        with self.assertRaises(TypeError):
            self.engine.evaluate(["not an observation"])

    def test_directly_constructed_invalid_observations_are_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.evaluate(
                [
                    ValidationObservation(
                        experiment_id="",
                        experiment_title="Pilot: Adapt peer navigation",
                        outcome="Participants reported fewer barriers.",
                        evidence_basis=["Pilot feedback"],
                        limitations=[],
                        reviewer="Community programme lead",
                    )
                ]
            )

        with self.assertRaises(ValueError):
            self.engine.evaluate(
                [
                    ValidationObservation(
                        experiment_id="experiment-3f7b0c76fbc1d265",
                        experiment_title="Pilot: Adapt peer navigation",
                        outcome="Participants reported fewer barriers.",
                        evidence_basis=["Pilot feedback"],
                        limitations=[],
                        reviewer="",
                    )
                ]
            )

        with self.assertRaises(ValueError):
            self.engine.evaluate(
                [
                    ValidationObservation(
                        experiment_id="experiment-3f7b0c76fbc1d265",
                        experiment_title="Pilot: Adapt peer navigation",
                        outcome="Participants reported fewer barriers.",
                        evidence_basis=[],
                        limitations=[],
                        reviewer="Community programme lead",
                    )
                ]
            )

    def test_observation_and_learning_can_be_converted_to_dict(self):
        observation = self._create_observation()
        learning = self.engine.evaluate([observation])[0]

        self.assertIsInstance(observation, ValidationObservation)
        self.assertIn("experiment_id", observation.to_dict())
        self.assertEqual(
            learning.experiment_id,
            observation.experiment_id,
        )
        self.assertIn("experiment_id", learning.to_dict())
        self.assertIn("reviewer", observation.to_dict())
        self.assertIn("next_step", learning.to_dict())


if __name__ == "__main__":
    unittest.main()
