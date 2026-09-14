import unittest

from src.evidence import create_evidence
from src.innovation_discovery import InnovationDiscoveryEngine


class TestInnovationDiscoveryEngine(unittest.TestCase):

    def setUp(self):
        self.engine = InnovationDiscoveryEngine()

    def test_report_generation(self):
        report = self.engine.analyse(
            "Young people are not consistently accessing an available service."
        )

        self.assertEqual(
            report.problem,
            "Young people are not consistently accessing an available service.",
        )

        self.assertTrue(report.reframed_problem)
        self.assertGreater(len(report.key_questions), 0)
        self.assertGreater(len(report.possible_root_causes), 0)
        self.assertGreater(len(report.solution_hypotheses), 0)
        self.assertGreater(len(report.validation_questions), 0)

    def test_empty_problem_is_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.analyse("")

    def test_solution_hypotheses_have_required_fields(self):
        report = self.engine.analyse(
            "People are not consistently accessing an available service."
        )

        for hypothesis in report.solution_hypotheses:
            self.assertTrue(hypothesis.title)
            self.assertTrue(hypothesis.rationale)
            self.assertTrue(hypothesis.experiment)

    def test_analysis_works_without_evidence(self):
        report = self.engine.analyse(
            "Community members are not using an available programme."
        )

        self.assertEqual(report.evidence_count, 0)
        self.assertGreater(len(report.evidence_profile), 0)
        self.assertGreater(len(report.evidence_gaps), 0)
        self.assertEqual(report.observed_patterns, [])

    def test_analysis_accepts_evidence(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased after peer support was introduced.",
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Participants reported that trusted peers made the service easier to approach.",
                date="2025-09-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people are not consistently accessing an available service.",
            evidence=evidence,
        )

        self.assertEqual(report.evidence_count, 2)
        self.assertGreater(len(report.evidence_profile), 0)
        self.assertEqual(len(report.evidence_gaps), 0)

    def test_engine_returns_observed_patterns(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service uptake increased.",
                date="2025-01-01",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Service uptake improved.",
                date="2025-06-01",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people are not consistently accessing a service.",
            evidence=evidence,
        )

        self.assertGreater(len(report.observed_patterns), 0)

        pattern_types = {
            pattern.pattern_type
            for pattern in report.observed_patterns
        }

        self.assertIn("location", pattern_types)
        self.assertIn("population", pattern_types)
        self.assertIn("time_span", pattern_types)

    def test_observed_patterns_are_evidence_based(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service access improved.",
                location="Chennai",
                population="Women",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Service access improved.",
                location="Chennai",
                population="Women",
            ),
        ]

        report = self.engine.analyse(
            "Service access is inconsistent.",
            evidence=evidence,
        )

        descriptions = " ".join(
            pattern.description
            for pattern in report.observed_patterns
        )

        self.assertIn("Chennai", descriptions)
        self.assertIn("Women", descriptions)

    def test_evidence_gaps_identify_missing_metadata(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content="Service access remains inconsistent.",
            )
        ]

        report = self.engine.analyse(
            "Service access remains inconsistent.",
            evidence=evidence,
        )

        gaps_text = " ".join(report.evidence_gaps)

        self.assertIn("location information", gaps_text)
        self.assertIn("population information", gaps_text)
        self.assertIn("dates", gaps_text)

    def test_report_can_be_converted_to_dict(self):
        report = self.engine.analyse(
            "Community members are not consistently using a service."
        )

        result = report.to_dict()

        self.assertIn("problem", result)
        self.assertIn("solution_hypotheses", result)
        self.assertIn("evidence_count", result)
        self.assertIn("evidence_profile", result)
        self.assertIn("evidence_gaps", result)
        self.assertIn("observed_patterns", result)


if __name__ == "__main__":
    unittest.main()