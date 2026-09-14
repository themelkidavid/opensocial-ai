import unittest

from src.evidence import create_evidence
from src.innovation_discovery import InnovationDiscoveryEngine


class TestInnovationDiscoveryEngine(unittest.TestCase):

    def setUp(self):
        self.engine = InnovationDiscoveryEngine()

    def test_engine_generates_report(self):
        problem = (
            "Young people are not consistently "
            "accessing an available service."
        )

        report = self.engine.analyse(problem)

        self.assertEqual(
            report.problem,
            problem,
        )

        self.assertTrue(
            report.reframed_problem
        )

        self.assertGreater(
            len(report.key_questions),
            0,
        )

        self.assertGreater(
            len(report.possible_root_causes),
            0,
        )

        self.assertGreater(
            len(report.solution_hypotheses),
            0,
        )

        self.assertGreater(
            len(report.validation_questions),
            0,
        )

    def test_empty_problem_is_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.analyse("")

    def test_solution_hypotheses_have_experiments(self):
        report = self.engine.analyse(
            "A community programme is experiencing "
            "high participant drop-off."
        )

        for solution in report.solution_hypotheses:
            self.assertTrue(
                solution.title
            )

            self.assertTrue(
                solution.rationale
            )

            self.assertTrue(
                solution.experiment
            )

    def test_evidence_quality_is_included_in_report(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content=(
                    "Service uptake increased significantly "
                    "after peer support was introduced."
                ),
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            )
        ]

        report = self.engine.analyse(
            "Young people are not consistently "
            "accessing an available service.",
            evidence=evidence,
        )

        self.assertEqual(
            report.evidence_count,
            1,
        )

        self.assertEqual(
            len(report.evidence_quality),
            1,
        )

        self.assertGreater(
            report.evidence_quality[0].score,
            0,
        )

    def test_each_evidence_item_receives_quality_assessment(self):
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
                    "Young people reported better access "
                    "to the service."
                ),
                date="2025-07-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people face barriers to service access.",
            evidence=evidence,
        )

        self.assertEqual(
            len(report.evidence_quality),
            len(evidence),
        )

        for quality in report.evidence_quality:
            self.assertGreaterEqual(
                quality.score,
                0,
            )

    def test_quality_assessment_detects_corroboration(self):
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
                    "Young people reported improved "
                    "service access."
                ),
                date="2025-07-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people face barriers to service access.",
            evidence=evidence,
        )

        strengths = []

        for quality in report.evidence_quality:
            strengths.extend(
                quality.strengths
            )

        combined_strengths = " ".join(
            strengths
        ).lower()

        self.assertIn(
            "corroborated",
            combined_strengths,
        )

    def test_conflicting_evidence_is_included_in_report(self):
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
                date="2025-07-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people are not consistently "
            "accessing an available service.",
            evidence=evidence,
        )

        self.assertGreater(
            len(report.evidence_conflicts),
            0,
        )

    def test_non_conflicting_evidence_has_no_conflicts(self):
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
                    "Young people reported improved "
                    "service access."
                ),
                date="2025-07-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people face barriers to service access.",
            evidence=evidence,
        )

        self.assertEqual(
            len(report.evidence_conflicts),
            0,
        )

    def test_conflicts_add_validation_questions(self):
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
                date="2025-07-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people are not consistently "
            "accessing an available service.",
            evidence=evidence,
        )

        validation_questions = " ".join(
            report.validation_questions
        ).lower()

        self.assertIn(
            "disagreement",
            validation_questions,
        )

    def test_patterns_are_included_in_report(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content=(
                    "Peer support improved service "
                    "engagement among young people."
                ),
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content=(
                    "Young people described peer support "
                    "as helpful for accessing services."
                ),
                date="2025-07-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people face barriers to service access.",
            evidence=evidence,
        )

        self.assertGreaterEqual(
            len(report.observed_patterns),
            1,
        )

    def test_insights_are_generated_from_patterns(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content=(
                    "Peer support improved service "
                    "engagement among young people."
                ),
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content=(
                    "Young people described peer support "
                    "as helpful for accessing services."
                ),
                date="2025-07-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people face barriers to service access.",
            evidence=evidence,
        )

        self.assertGreater(
            len(report.insights),
            0,
        )

        for insight in report.insights:
            self.assertTrue(
                insight.title
            )

            self.assertTrue(
                insight.insight
            )

            self.assertTrue(
                insight.investigation_question
            )

            self.assertGreater(
                len(insight.uncertainty),
                0,
            )

    def test_conflicting_evidence_generates_insight(self):
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
                date="2025-07-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people are not consistently "
            "accessing an available service.",
            evidence=evidence,
        )

        self.assertGreater(
            len(report.insights),
            0,
        )

        titles = [
            insight.title
            for insight in report.insights
        ]

        self.assertIn(
            "Investigate the conflicting evidence",
            titles,
        )

    def test_insights_are_included_in_report_dictionary(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content=(
                    "Peer support improved service "
                    "engagement among young people."
                ),
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content=(
                    "Young people described peer support "
                    "as helpful for accessing services."
                ),
                date="2025-07-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people face barriers to service access.",
            evidence=evidence,
        )

        result = report.to_dict()

        self.assertIn(
            "insights",
            result,
        )

        self.assertIsInstance(
            result["insights"],
            list,
        )

        self.assertGreater(
            len(result["insights"]),
            0,
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
                date="2025-07-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people are not consistently "
            "accessing an available service.",
            evidence=evidence,
        )

        self.assertEqual(
            report.evidence_count,
            2,
        )

        self.assertTrue(
            report.evidence_profile
        )

        self.assertTrue(
            report.evidence_quality
        )

        self.assertTrue(
            report.observed_patterns
        )

        self.assertTrue(
            report.evidence_conflicts
        )

        self.assertTrue(
            report.insights
        )

        self.assertTrue(
            report.validation_questions
        )

    def test_no_evidence_produces_no_insights(self):
        report = self.engine.analyse(
            "A community programme is experiencing "
            "high participant drop-off."
        )

        self.assertEqual(
            report.insights,
            [],
        )

    def test_insight_uncertainty_is_explicit(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content=(
                    "Peer support improved service "
                    "engagement among young people."
                ),
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content=(
                    "Young people described peer support "
                    "as helpful for accessing services."
                ),
                date="2025-07-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people face barriers to service access.",
            evidence=evidence,
        )

        self.assertGreater(
            len(report.insights),
            0,
        )

        uncertainty = " ".join(
            report.insights[0].uncertainty
        ).lower()

        self.assertIn(
            "causation",
            uncertainty,
        )


if __name__ == "__main__":
    unittest.main()