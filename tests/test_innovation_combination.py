import unittest
from types import SimpleNamespace

from src.innovation_combination import (
    InnovationCombination,
    InnovationCombinationEngine,
)
from src.innovation_inspiration import (
    InnovationInspiration,
    InnovationInspirationEngine,
)


class TestInnovationCombinationEngine(unittest.TestCase):

    def setUp(self):
        self.engine = InnovationCombinationEngine()
        self.inspiration_engine = InnovationInspirationEngine()

    def _create_inspiration(
        self,
        source_type,
        title,
        context,
        mechanism,
        observed_result,
    ):
        return self.inspiration_engine.create(
            source_type=source_type,
            title=title,
            context=context,
            mechanism=mechanism,
            observed_result=observed_result,
            transferability="moderate",
        )

    def test_combination_engine_returns_combination(self):
        inspirations = [
            self._create_inspiration(
                source_type="cross_sector",
                title="Peer navigation model",
                context="Community health services",
                mechanism=(
                    "Trusted peers guide people through "
                    "services."
                ),
                observed_result=(
                    "Improved service engagement."
                ),
            ),
            self._create_inspiration(
                source_type="community",
                title="Mobile outreach model",
                context="Community service delivery",
                mechanism=(
                    "Services are brought closer to "
                    "communities."
                ),
                observed_result=(
                    "Improved access."
                ),
            ),
        ]

        opportunity = SimpleNamespace(
            opportunity_type="emerging_pattern",
            title="Service access pattern",
            description=(
                "Young people face barriers to accessing "
                "community services."
            ),
            evidence_basis=[
                "Programme report",
                "Community feedback",
            ],
            confidence="moderate",
            uncertainty=[
                "The pattern does not establish causation."
            ],
        )

        combinations = self.engine.combine(
            problem=(
                "Young people face barriers to "
                "service access."
            ),
            opportunity=opportunity,
            inspirations=inspirations,
        )

        self.assertGreater(
            len(combinations),
            0,
        )

        self.assertIsInstance(
            combinations[0],
            InnovationCombination,
        )

    def test_combination_contains_both_inspiration_sources(self):
        inspirations = [
            self._create_inspiration(
                source_type="cross_sector",
                title="Peer navigation model",
                context="Community health services",
                mechanism=(
                    "Trusted peers guide people through "
                    "services."
                ),
                observed_result=(
                    "Improved service engagement."
                ),
            ),
            self._create_inspiration(
                source_type="community",
                title="Mobile outreach model",
                context="Community service delivery",
                mechanism=(
                    "Services are brought closer to "
                    "communities."
                ),
                observed_result=(
                    "Improved access."
                ),
            ),
        ]

        combinations = self.engine.combine(
            problem=(
                "Young people face barriers to "
                "service access."
            ),
            opportunity=None,
            inspirations=inspirations,
        )

        self.assertGreater(
            len(combinations),
            0,
        )

        combination = combinations[0]

        combined_text = " ".join(
            [
                combination.title,
                combination.description,
                combination.mechanism_a,
                combination.mechanism_b,
                combination.combined_mechanism,
            ]
        ).lower()

        self.assertIn(
            "peer",
            combined_text,
        )

        self.assertIn(
            "mobile",
            combined_text,
        )

    def test_combination_creates_new_mechanism(self):
        inspirations = [
            self._create_inspiration(
                source_type="cross_sector",
                title="Peer navigation model",
                context="Community health services",
                mechanism=(
                    "Trusted peers guide people through "
                    "services."
                ),
                observed_result=(
                    "Improved service engagement."
                ),
            ),
            self._create_inspiration(
                source_type="community",
                title="Mobile outreach model",
                context="Community service delivery",
                mechanism=(
                    "Services are brought closer to "
                    "communities."
                ),
                observed_result=(
                    "Improved access."
                ),
            ),
        ]

        combinations = self.engine.combine(
            problem=(
                "Young people face barriers to "
                "service access."
            ),
            opportunity=None,
            inspirations=inspirations,
        )

        combined_mechanism = (
            combinations[0]
            .combined_mechanism
            .lower()
        )

        self.assertTrue(
            "peer" in combined_mechanism
        )

        self.assertTrue(
            "mobile" in combined_mechanism
            or "outreach" in combined_mechanism
        )

    def test_combination_preserves_uncertainty(self):
        inspirations = [
            self._create_inspiration(
                source_type="cross_sector",
                title="Peer navigation model",
                context="Community health services",
                mechanism=(
                    "Trusted peers guide people through "
                    "services."
                ),
                observed_result=(
                    "Improved service engagement."
                ),
            ),
            self._create_inspiration(
                source_type="community",
                title="Mobile outreach model",
                context="Community service delivery",
                mechanism=(
                    "Services are brought closer to "
                    "communities."
                ),
                observed_result=(
                    "Improved access."
                ),
            ),
        ]

        combinations = self.engine.combine(
            problem=(
                "Young people face barriers to "
                "service access."
            ),
            opportunity=None,
            inspirations=inspirations,
        )

        uncertainty = " ".join(
            combinations[0].uncertainty
        ).lower()

        self.assertTrue(
            "uncertain" in uncertainty
            or "not proven" in uncertainty
            or "test" in uncertainty
        )

    def test_combination_has_experiment(self):
        inspirations = [
            self._create_inspiration(
                source_type="cross_sector",
                title="Peer navigation model",
                context="Community health services",
                mechanism=(
                    "Trusted peers guide people through "
                    "services."
                ),
                observed_result=(
                    "Improved service engagement."
                ),
            ),
            self._create_inspiration(
                source_type="community",
                title="Mobile outreach model",
                context="Community service delivery",
                mechanism=(
                    "Services are brought closer to "
                    "communities."
                ),
                observed_result=(
                    "Improved access."
                ),
            ),
        ]

        combinations = self.engine.combine(
            problem=(
                "Young people face barriers to "
                "service access."
            ),
            opportunity=None,
            inspirations=inspirations,
        )

        self.assertTrue(
            combinations[0].experiment
        )

        self.assertTrue(
            len(combinations[0].experiment)
            > 20
        )

    def test_combination_requires_at_least_two_inspirations(self):
        inspirations = [
            self._create_inspiration(
                source_type="cross_sector",
                title="Peer navigation model",
                context="Community health services",
                mechanism=(
                    "Trusted peers guide people "
                    "through services."
                ),
                observed_result=(
                    "Improved service engagement."
                ),
            )
        ]

        combinations = self.engine.combine(
            problem=(
                "Young people face barriers to "
                "service access."
            ),
            opportunity=None,
            inspirations=inspirations,
        )

        self.assertEqual(
            combinations,
            [],
        )

    def test_empty_inspirations_return_no_combinations(self):
        combinations = self.engine.combine(
            problem=(
                "Young people face barriers to "
                "service access."
            ),
            opportunity=None,
            inspirations=[],
        )

        self.assertEqual(
            combinations,
            [],
        )

    def test_combination_rejects_empty_problem(self):
        inspirations = [
            self._create_inspiration(
                source_type="cross_sector",
                title="Peer navigation model",
                context="Community health services",
                mechanism=(
                    "Trusted peers guide people."
                ),
                observed_result=(
                    "Improved engagement."
                ),
            ),
            self._create_inspiration(
                source_type="community",
                title="Mobile outreach model",
                context="Community service delivery",
                mechanism=(
                    "Services are brought closer."
                ),
                observed_result=(
                    "Improved access."
                ),
            ),
        ]

        with self.assertRaises(ValueError):
            self.engine.combine(
                problem="",
                opportunity=None,
                inspirations=inspirations,
            )

    def test_combination_can_be_converted_to_dict(self):
        inspirations = [
            self._create_inspiration(
                source_type="cross_sector",
                title="Peer navigation model",
                context="Community health services",
                mechanism=(
                    "Trusted peers guide people."
                ),
                observed_result=(
                    "Improved engagement."
                ),
            ),
            self._create_inspiration(
                source_type="community",
                title="Mobile outreach model",
                context="Community service delivery",
                mechanism=(
                    "Services are brought closer."
                ),
                observed_result=(
                    "Improved access."
                ),
            ),
        ]

        combinations = self.engine.combine(
            problem=(
                "Young people face barriers to "
                "service access."
            ),
            opportunity=None,
            inspirations=inspirations,
        )

        result = combinations[0].to_dict()

        expected_fields = [
            "title",
            "problem",
            "description",
            "inspiration_a",
            "inspiration_b",
            "mechanism_a",
            "mechanism_b",
            "combined_mechanism",
            "rationale",
            "uncertainty",
            "experiment",
            "validation_question",
        ]

        for field in expected_fields:
            self.assertIn(
                field,
                result,
            )


if __name__ == "__main__":
    unittest.main()