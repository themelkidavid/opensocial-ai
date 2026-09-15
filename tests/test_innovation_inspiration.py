import unittest

from src.innovation_inspiration import (
    InnovationInspiration,
    InnovationInspirationEngine,
)


class TestInnovationInspirationEngine(unittest.TestCase):

    def setUp(self):
        self.engine = InnovationInspirationEngine()

    def test_create_inspiration(self):
        inspiration = self.engine.create(
            source_type="cross_sector",
            title="Peer navigation model",
            context="Community health services",
            mechanism="Trusted peers guide people through services.",
            observed_result="Improved service engagement.",
        )

        self.assertIsInstance(
            inspiration,
            InnovationInspiration,
        )

        self.assertEqual(
            inspiration.source_type,
            "cross_sector",
        )

        self.assertEqual(
            inspiration.title,
            "Peer navigation model",
        )

    def test_inspiration_requires_source_type(self):
        with self.assertRaises(ValueError):
            self.engine.create(
                source_type="",
                title="Peer navigation model",
                context="Community health services",
                mechanism="Trusted peers guide people through services.",
                observed_result="Improved service engagement.",
            )

    def test_inspiration_requires_title(self):
        with self.assertRaises(ValueError):
            self.engine.create(
                source_type="cross_sector",
                title="",
                context="Community health services",
                mechanism="Trusted peers guide people through services.",
                observed_result="Improved service engagement.",
            )

    def test_inspiration_requires_mechanism(self):
        with self.assertRaises(ValueError):
            self.engine.create(
                source_type="cross_sector",
                title="Peer navigation model",
                context="Community health services",
                mechanism="",
                observed_result="Improved service engagement.",
            )

    def test_inspiration_can_be_converted_to_dict(self):
        inspiration = self.engine.create(
            source_type="historical",
            title="Community outreach model",
            context="Public health outreach",
            mechanism="Local volunteers connect people with services.",
            observed_result="Higher community participation.",
        )

        result = inspiration.to_dict()

        expected_fields = [
            "source_type",
            "title",
            "context",
            "mechanism",
            "observed_result",
            "transferability",
            "adaptation_notes",
        ]

        for field in expected_fields:
            self.assertIn(
                field,
                result,
            )

    def test_cross_domain_inspiration_is_identified(self):
        inspiration = self.engine.create(
            source_type="cross_sector",
            title="Peer navigation model",
            context="Community health services",
            mechanism="Trusted peers guide people through services.",
            observed_result="Improved service engagement.",
            transferability="moderate",
            adaptation_notes=(
                "Adapt the peer navigation mechanism "
                "to the target service."
            ),
        )

        self.assertEqual(
            inspiration.source_type,
            "cross_sector",
        )

        self.assertEqual(
            inspiration.transferability,
            "moderate",
        )

    def test_historical_inspiration_is_supported(self):
        inspiration = self.engine.create(
            source_type="historical",
            title="Community outreach model",
            context="Earlier community programme",
            mechanism="Local volunteers connect people with services.",
            observed_result="Higher community participation.",
            transferability="exploratory",
            adaptation_notes=(
                "Investigate whether the earlier mechanism "
                "can work under current conditions."
            ),
        )

        self.assertEqual(
            inspiration.source_type,
            "historical",
        )

        self.assertEqual(
            inspiration.transferability,
            "exploratory",
        )

    def test_community_innovation_is_supported(self):
        inspiration = self.engine.create(
            source_type="community",
            title="Peer-led local support",
            context="Community-based service access",
            mechanism="Community members support each other.",
            observed_result="Improved participation.",
            transferability="high",
            adaptation_notes=(
                "Co-design the model with the affected community."
            ),
        )

        self.assertEqual(
            inspiration.source_type,
            "community",
        )

        self.assertEqual(
            inspiration.transferability,
            "high",
        )

    def test_find_relevant_inspiration(self):
        inspirations = [
            self.engine.create(
                source_type="cross_sector",
                title="Peer navigation model",
                context="Community health services",
                mechanism="Trusted peers guide people through services.",
                observed_result="Improved service engagement.",
            ),
            self.engine.create(
                source_type="historical",
                title="Mobile outreach model",
                context="Rural service delivery",
                mechanism="Services are taken closer to communities.",
                observed_result="Improved access.",
            ),
        ]

        results = self.engine.find_relevant(
            problem="Young people face barriers to service access.",
            inspirations=inspirations,
        )

        self.assertGreater(
            len(results),
            0,
        )

    def test_relevant_inspiration_prioritises_matching_mechanism(self):
        inspirations = [
            self.engine.create(
                source_type="cross_sector",
                title="Peer navigation model",
                context="Community health services",
                mechanism="Trusted peers guide people through services.",
                observed_result="Improved service engagement.",
            ),
            self.engine.create(
                source_type="historical",
                title="Infrastructure programme",
                context="Road development",
                mechanism="Physical infrastructure expansion.",
                observed_result="Improved transport access.",
            ),
        ]

        results = self.engine.find_relevant(
            problem="Young people need better peer support "
                    "to access services.",
            inspirations=inspirations,
        )

        self.assertGreater(
            len(results),
            0,
        )

        self.assertEqual(
            results[0].title,
            "Peer navigation model",
        )

    def test_empty_inspiration_list_returns_empty(self):
        results = self.engine.find_relevant(
            problem="Young people face barriers to service access.",
            inspirations=[],
        )

        self.assertEqual(
            results,
            [],
        )

    def test_inspiration_requires_observed_result(self):
        with self.assertRaises(ValueError):
            self.engine.create(
                source_type="cross_sector",
                title="Peer navigation model",
                context="Community health services",
                mechanism="Trusted peers guide people through services.",
                observed_result="",
            )

    def test_transferability_defaults_to_exploratory(self):
        inspiration = self.engine.create(
            source_type="cross_sector",
            title="Peer navigation model",
            context="Community health services",
            mechanism="Trusted peers guide people through services.",
            observed_result="Improved service engagement.",
        )

        self.assertEqual(
            inspiration.transferability,
            "exploratory",
        )

    def test_adaptation_notes_can_be_empty(self):
        inspiration = self.engine.create(
            source_type="cross_sector",
            title="Peer navigation model",
            context="Community health services",
            mechanism="Trusted peers guide people through services.",
            observed_result="Improved service engagement.",
        )

        self.assertIsInstance(
            inspiration.adaptation_notes,
            str,
        )


if __name__ == "__main__":
    unittest.main()