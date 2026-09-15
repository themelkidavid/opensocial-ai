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

        titles = [
            insight.title
            for insight in report.insights
        ]

        self.assertIn(
            "Investigate the conflicting evidence",
            titles,
        )

    def test_pattern_creates_innovation_opportunity(self):
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
            len(report.innovation_opportunities),
            0,
        )

        opportunity_types = [
            opportunity.opportunity_type
            for opportunity in report.innovation_opportunities
        ]

        self.assertIn(
            "emerging_pattern",
            opportunity_types,
        )

    def test_evidence_gap_creates_innovation_opportunity(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content=(
                    "Service uptake increased after "
                    "peer support was introduced."
                ),
                date="2025-06-30",
                location="Madurai",
            )
        ]

        report = self.engine.analyse(
            "Young people face barriers to service access.",
            evidence=evidence,
        )

        opportunity_types = [
            opportunity.opportunity_type
            for opportunity in report.innovation_opportunities
        ]

        self.assertIn(
            "evidence_gap",
            opportunity_types,
        )

    def test_no_evidence_creates_evidence_gap_opportunity(self):
        report = self.engine.analyse(
            "A community programme is experiencing "
            "high participant drop-off."
        )

        self.assertTrue(
            report.evidence_gaps
        )

        opportunity_types = [
            opportunity.opportunity_type
            for opportunity in report.innovation_opportunities
        ]

        self.assertIn(
            "evidence_gap",
            opportunity_types,
        )

    def test_conflict_creates_contradiction_opportunity(self):
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

        opportunity_types = [
            opportunity.opportunity_type
            for opportunity in report.innovation_opportunities
        ]

        self.assertIn(
            "contradiction",
            opportunity_types,
        )

    def test_transfer_opportunity_is_generated(self):
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
                    "Peer support was helpful for "
                    "accessing services."
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

        opportunity_types = [
            opportunity.opportunity_type
            for opportunity in report.innovation_opportunities
        ]

        self.assertIn(
            "transfer_opportunity",
            opportunity_types,
        )

    def test_innovation_opportunities_are_in_report_dictionary(self):
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
            "innovation_opportunities",
            result,
        )

        self.assertIsInstance(
            result["innovation_opportunities"],
            list,
        )

        self.assertGreater(
            len(result["innovation_opportunities"]),
            0,
        )

    def test_opportunity_validation_questions_are_added(self):
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

        validation_questions = " ".join(
            report.validation_questions
        ).lower()

        self.assertIn(
            "innovation opportunity",
            validation_questions,
        )

    def test_innovation_hypotheses_are_generated(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content=(
                    "Peer support improved service engagement "
                    "among young people."
                ),
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content=(
                    "Young people described peer support as "
                    "helpful for accessing services."
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
            len(report.innovation_hypotheses),
            0,
        )

    def test_innovation_hypotheses_have_required_fields(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content=(
                    "Peer support improved service engagement "
                    "among young people."
                ),
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content=(
                    "Young people described peer support as "
                    "helpful for accessing services."
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
            len(report.innovation_hypotheses),
            0,
        )

        for hypothesis in report.innovation_hypotheses:
            self.assertTrue(hypothesis.title)
            self.assertTrue(hypothesis.problem_connection)
            self.assertTrue(hypothesis.inspiration_source)
            self.assertTrue(hypothesis.underlying_mechanism)
            self.assertTrue(hypothesis.novel_combination)
            self.assertTrue(hypothesis.why_it_might_work)
            self.assertTrue(hypothesis.evidence_basis)
            self.assertTrue(hypothesis.confidence)
            self.assertTrue(hypothesis.uncertainty)
            self.assertTrue(hypothesis.experiment)
            self.assertTrue(hypothesis.validation_question)

    def test_innovation_hypotheses_are_in_report_dictionary(self):
        evidence = [
            create_evidence(
                source_type="programme_report",
                content=(
                    "Peer support improved service engagement "
                    "among young people."
                ),
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content=(
                    "Young people described peer support as "
                    "helpful for accessing services."
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
            "innovation_hypotheses",
            result,
        )

        self.assertIsInstance(
            result["innovation_hypotheses"],
            list,
        )

        self.assertGreater(
            len(result["innovation_hypotheses"]),
            0,
        )

    def test_no_evidence_produces_no_innovation_hypotheses(self):
        report = self.engine.analyse(
            "A community programme is experiencing "
            "high participant drop-off."
        )

        self.assertEqual(
            report.innovation_hypotheses,
            [],
        )

    def test_report_contains_all_analysis_layers(self):
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
            create_evidence(
                source_type="community_survey",
                content=(
                    "Young people reported that peer support "
                    "made services easier to access."
                ),
                date="2025-08-15",
                location="Madurai",
                population="Young people",
            ),
        ]

        report = self.engine.analyse(
            "Young people face barriers to service access.",
            evidence=evidence,
        )

        self.assertTrue(
            report.evidence_quality
        )

        self.assertTrue(
            report.observed_patterns
        )

        self.assertTrue(
            report.evidence_gap_details
            or report.evidence_gaps == []
        )

        self.assertTrue(
            report.insights
        )

        self.assertTrue(
            report.innovation_opportunities
        )

        self.assertTrue(
            report.innovation_hypotheses
        )

        self.assertTrue(
            report.solution_hypotheses
        )

        self.assertTrue(
            report.validation_questions
        )


if __name__ == "__main__":
    unittest.main()