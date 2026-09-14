import unittest

from src.evidence import create_evidence
from src.pattern_discovery import PatternDiscovery, ObservedPattern


class TestPatternDiscovery(unittest.TestCase):

    def setUp(self):
        self.discovery = PatternDiscovery()

    def test_no_evidence_returns_no_patterns(self):
        patterns = self.discovery.discover([])

        self.assertEqual(patterns, [])

    def test_patterns_are_observed_pattern_objects(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
            ),
            create_evidence(
                source_type="programme_report",
                content="Service uptake improved.",
            ),
        ]

        patterns = self.discovery.discover(evidence)

        self.assertGreater(len(patterns), 0)

        for pattern in patterns:
            self.assertIsInstance(pattern, ObservedPattern)

    def test_repeated_source_type_is_detected(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service access was limited.",
            ),
            create_evidence(
                source_type="programme_report",
                content="Service access improved.",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Participants reported access difficulties.",
            ),
        ]

        patterns = self.discovery.discover(evidence)

        source_patterns = [
            pattern
            for pattern in patterns
            if pattern.pattern_type == "source_type"
        ]

        self.assertGreater(len(source_patterns), 0)
        self.assertIn(
            "programme_report",
            source_patterns[0].description,
        )

    def test_repeated_location_is_detected(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                location="Madurai",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Access improved.",
                location="Madurai",
            ),
        ]

        patterns = self.discovery.discover(evidence)

        location_patterns = [
            pattern
            for pattern in patterns
            if pattern.pattern_type == "location"
        ]

        self.assertEqual(len(location_patterns), 1)
        self.assertIn("Madurai", location_patterns[0].description)

    def test_repeated_population_is_detected(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Access improved.",
                population="Young people",
            ),
        ]

        patterns = self.discovery.discover(evidence)

        population_patterns = [
            pattern
            for pattern in patterns
            if pattern.pattern_type == "population"
        ]

        self.assertEqual(len(population_patterns), 1)
        self.assertIn(
            "Young people",
            population_patterns[0].description,
        )

    def test_multiple_dates_create_time_span_pattern(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                date="2025-01-01",
            ),
            create_evidence(
                source_type="programme_report",
                content="Service uptake improved.",
                date="2025-06-01",
            ),
        ]

        patterns = self.discovery.discover(evidence)

        time_patterns = [
            pattern
            for pattern in patterns
            if pattern.pattern_type == "time_span"
        ]

        self.assertEqual(len(time_patterns), 1)
        self.assertIn("2 distinct dates", time_patterns[0].description)

    def test_recurring_terms_are_detected(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service access improved for participants.",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Participants reported better service access.",
            ),
        ]

        patterns = self.discovery.discover(evidence)

        term_patterns = [
            pattern
            for pattern in patterns
            if pattern.pattern_type == "recurring_term"
        ]

        descriptions = " ".join(
            pattern.description
            for pattern in term_patterns
        )

        self.assertIn("service", descriptions)
        self.assertIn("access", descriptions)

    def test_outcome_signals_are_detected(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased significantly.",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Participants reported increased engagement.",
            ),
        ]

        patterns = self.discovery.discover(evidence)

        outcome_patterns = [
            pattern
            for pattern in patterns
            if pattern.pattern_type == "outcome_signal"
        ]

        descriptions = " ".join(
            pattern.description
            for pattern in outcome_patterns
        )

        self.assertIn("increased", descriptions)

    def test_pattern_to_dict(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
            ),
            create_evidence(
                source_type="programme_report",
                content="Service uptake improved.",
            ),
        ]

        patterns = self.discovery.discover(evidence)

        result = patterns[0].to_dict()

        self.assertIn("pattern_type", result)
        self.assertIn("description", result)
        self.assertIn("evidence_count", result)
        self.assertIn("confidence", result)


if __name__ == "__main__":
    unittest.main()