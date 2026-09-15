import unittest
from types import SimpleNamespace

from src.innovation_inspiration import InnovationInspirationEngine
from src.innovation_reasoning import (
    InnovationHypothesis,
    InnovationReasoningEngine,
)


class TestInnovationReasoningEngine(unittest.TestCase):

    def setUp(self):
        self.engine = InnovationReasoningEngine()
        self.inspiration_engine = InnovationInspirationEngine()

    def test_engine_returns_innovation_hypotheses(self):
        opportunities = [
            SimpleNamespace(
                opportunity_type="emerging_pattern",
                title="Investigate the repeated peer-support pattern",
                description=(
                    "Peer support appears repeatedly in evidence "
                    "about service engagement."
                ),
                evidence_basis=[
                    "Programme report",
                    "Community feedback",
                ],
                confidence="moderate",
                uncertainty=[
                    "The pattern does not establish causation."
                ],
                investigation_question=(
                    "Does peer support consistently improve engagement?"
                ),
                suggested_experiment=(
                    "Pilot peer support with a small group."
                ),
            )
        ]

        hypotheses = self.engine.generate(
            problem="Young people face barriers to service access.",
            opportunities=opportunities,
        )

        self.assertGreater(
            len(hypotheses),
            0,
        )

        self.assertIsInstance(
            hypotheses[0],
            InnovationHypothesis,
        )

    def test_hypothesis_contains_required_fields(self):
        opportunities = [
            SimpleNamespace(
                opportunity_type="emerging_pattern",
                title="Peer support pattern",
                description="Peer support appears repeatedly.",
                evidence_basis=["Programme report"],
                confidence="moderate",
                uncertainty=["Causation is uncertain."],
                investigation_question="Does peer support improve access?",
                suggested_experiment="Run a small pilot.",
            )
        ]

        hypotheses = self.engine.generate(
            problem="Young people face barriers to service access.",
            opportunities=opportunities,
        )

        hypothesis = hypotheses[0]

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

    def test_pattern_opportunity_generates_transfer_hypothesis(self):
        opportunities = [
            SimpleNamespace(
                opportunity_type="emerging_pattern",
                title="Peer support pattern",
                description=(
                    "Peer support repeatedly appears to improve "
                    "service engagement."
                ),
                evidence_basis=[
                    "Programme report",
                    "Community feedback",
                ],
                confidence="moderate",
                uncertainty=[
                    "The pattern does not establish causation."
                ],
                investigation_question="Does peer support improve access?",
                suggested_experiment="Run a small pilot.",
            )
        ]

        hypotheses = self.engine.generate(
            problem="Young people face barriers to service access.",
            opportunities=opportunities,
        )

        sources = [
            hypothesis.inspiration_source
            for hypothesis in hypotheses
        ]

        self.assertTrue(
            any(
                "transfer" in source.lower()
                for source in sources
            )
        )

    def test_evidence_gap_generates_evidence_strengthening_hypothesis(self):
        opportunities = [
            SimpleNamespace(
                opportunity_type="evidence_gap",
                title="Investigate the evidence gap",
                description=(
                    "Population information is missing from the evidence."
                ),
                evidence_basis=[
                    "Population information is missing."
                ],
                confidence="low",
                uncertainty=[
                    "Additional evidence is required."
                ],
                investigation_question=(
                    "What additional evidence should be collected?"
                ),
                suggested_experiment=(
                    "Conduct structured community data collection."
                ),
            )
        ]

        hypotheses = self.engine.generate(
            problem="Young people face barriers to service access.",
            opportunities=opportunities,
        )

        self.assertGreater(
            len(hypotheses),
            0,
        )

        combined = " ".join(
            hypothesis.title
            for hypothesis in hypotheses
        ).lower()

        self.assertTrue(
            "evidence" in combined
            or "information" in combined
        )

    def test_contradiction_generates_context_hypothesis(self):
        opportunities = [
            SimpleNamespace(
                opportunity_type="contradiction",
                title="Investigate conflicting evidence",
                description=(
                    "Conflicting evidence sources report different outcomes."
                ),
                evidence_basis=[
                    "Programme report",
                    "Community feedback",
                ],
                confidence="low",
                uncertainty=[
                    "Measurement and population differences may explain "
                    "the disagreement."
                ],
                investigation_question=(
                    "What explains the disagreement?"
                ),
                suggested_experiment=(
                    "Compare measurement methods and implementation contexts."
                ),
            )
        ]

        hypotheses = self.engine.generate(
            problem="Young people face barriers to service access.",
            opportunities=opportunities,
        )

        self.assertGreater(
            len(hypotheses),
            0,
        )

        combined = " ".join(
            hypothesis.underlying_mechanism
            for hypothesis in hypotheses
        ).lower()

        self.assertTrue(
            "context" in combined
            or "condition" in combined
            or "measurement" in combined
        )

    def test_hypothesis_preserves_uncertainty(self):
        opportunities = [
            SimpleNamespace(
                opportunity_type="emerging_pattern",
                title="Repeated pattern",
                description="A repeated pattern was observed.",
                evidence_basis=["Community feedback"],
                confidence="moderate",
                uncertainty=[
                    "The pattern does not establish causation."
                ],
                investigation_question="Does the pattern persist?",
                suggested_experiment="Run a small pilot.",
            )
        ]

        hypotheses = self.engine.generate(
            problem="A community programme has low engagement.",
            opportunities=opportunities,
        )

        uncertainty = " ".join(
            hypotheses[0].uncertainty
        ).lower()

        self.assertTrue(
            "uncertain" in uncertainty
            or "causation" in uncertainty
            or "not proven" in uncertainty
        )

    def test_empty_problem_is_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.generate(
                problem="",
                opportunities=[],
            )

    def test_no_opportunities_returns_no_hypotheses(self):
        hypotheses = self.engine.generate(
            problem="Young people face barriers to service access.",
            opportunities=[],
        )

        self.assertEqual(
            hypotheses,
            [],
        )

    def test_hypothesis_can_be_converted_to_dict(self):
        opportunities = [
            SimpleNamespace(
                opportunity_type="emerging_pattern",
                title="Repeated pattern",
                description="A repeated pattern was observed.",
                evidence_basis=["Community feedback"],
                confidence="moderate",
                uncertainty=["Causation is uncertain."],
                investigation_question="Does the pattern persist?",
                suggested_experiment="Run a small pilot.",
            )
        ]

        hypotheses = self.engine.generate(
            problem="Young people face barriers to service access.",
            opportunities=opportunities,
        )

        result = hypotheses[0].to_dict()

        expected_fields = [
            "title",
            "problem_connection",
            "inspiration_source",
            "underlying_mechanism",
            "novel_combination",
            "why_it_might_work",
            "evidence_basis",
            "confidence",
            "uncertainty",
            "experiment",
            "validation_question",
        ]

        for field in expected_fields:
            self.assertIn(
                field,
                result,
            )

    def test_relevant_inspiration_can_influence_hypothesis(self):
        opportunities = [
            SimpleNamespace(
                opportunity_type="emerging_pattern",
                title="Peer support pattern",
                description=(
                    "Peer support appears repeatedly to improve "
                    "service engagement."
                ),
                evidence_basis=[
                    "Programme report",
                    "Community feedback",
                ],
                confidence="moderate",
                uncertainty=[
                    "The pattern does not establish causation."
                ],
                investigation_question="Does peer support improve access?",
                suggested_experiment="Run a small pilot.",
            )
        ]

        inspirations = [
            self.inspiration_engine.create(
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
                transferability="moderate",
                adaptation_notes=(
                    "Adapt peer navigation to young people "
                    "accessing community services."
                ),
            )
        ]

        hypotheses = self.engine.generate(
            problem="Young people face barriers to service access.",
            opportunities=opportunities,
            inspirations=inspirations,
        )

        self.assertGreater(
            len(hypotheses),
            0,
        )

        combined = " ".join(
            [
                hypotheses[0].inspiration_source,
                hypotheses[0].novel_combination,
                hypotheses[0].why_it_might_work,
            ]
        ).lower()

        self.assertTrue(
            "peer navigation" in combined
            or "trusted peers" in combined
            or "inspiration" in combined
        )

    def test_inspiration_is_preserved_in_evidence_basis(self):
        opportunities = [
            SimpleNamespace(
                opportunity_type="emerging_pattern",
                title="Peer support pattern",
                description=(
                    "Peer support appears repeatedly to improve "
                    "service engagement."
                ),
                evidence_basis=[
                    "Programme report",
                ],
                confidence="moderate",
                uncertainty=[
                    "The pattern does not establish causation."
                ],
                investigation_question="Does peer support improve access?",
                suggested_experiment="Run a small pilot.",
            )
        ]

        inspirations = [
            self.inspiration_engine.create(
                source_type="community",
                title="Community peer navigator model",
                context="Community service access",
                mechanism=(
                    "Trusted community members help people "
                    "navigate services."
                ),
                observed_result=(
                    "Improved participation."
                ),
                transferability="high",
                adaptation_notes=(
                    "Co-design with local community members."
                ),
            )
        ]

        hypotheses = self.engine.generate(
            problem="Young people face barriers to service access.",
            opportunities=opportunities,
            inspirations=inspirations,
        )

        evidence_basis = " ".join(
            hypotheses[0].evidence_basis
        ).lower()

        self.assertTrue(
            "peer" in evidence_basis
            or "community" in evidence_basis
        )

    def test_multiple_inspirations_can_be_used(self):
        opportunities = [
            SimpleNamespace(
                opportunity_type="emerging_pattern",
                title="Service engagement pattern",
                description=(
                    "Community-based support appears to improve "
                    "service engagement."
                ),
                evidence_basis=[
                    "Programme report",
                ],
                confidence="moderate",
                uncertainty=[
                    "The pattern does not establish causation."
                ],
                investigation_question=(
                    "Does community support improve engagement?"
                ),
                suggested_experiment="Run a small pilot.",
            )
        ]

        inspirations = [
            self.inspiration_engine.create(
                source_type="cross_sector",
                title="Peer navigation model",
                context="Community health services",
                mechanism=(
                    "Trusted peers guide people through services."
                ),
                observed_result="Improved engagement.",
            ),
            self.inspiration_engine.create(
                source_type="community",
                title="Mobile outreach model",
                context="Community service delivery",
                mechanism=(
                    "Services are brought closer to communities."
                ),
                observed_result="Improved access.",
            ),
        ]

        hypotheses = self.engine.generate(
            problem="Young people need better community "
                    "access to services.",
            opportunities=opportunities,
            inspirations=inspirations,
        )

        self.assertGreater(
            len(hypotheses),
            0,
        )

    def test_no_inspiration_still_generates_hypothesis(self):
        opportunities = [
            SimpleNamespace(
                opportunity_type="emerging_pattern",
                title="Observed pattern",
                description="A useful pattern was observed.",
                evidence_basis=["Programme report"],
                confidence="moderate",
                uncertainty=["Causation is uncertain."],
                investigation_question="Does the pattern persist?",
                suggested_experiment="Run a small pilot.",
            )
        ]

        hypotheses = self.engine.generate(
            problem="A community programme has low engagement.",
            opportunities=opportunities,
            inspirations=[],
        )

        self.assertGreater(
            len(hypotheses),
            0,
        )

    def test_no_evidence_and_no_opportunities_returns_no_hypotheses(self):
        hypotheses = self.engine.generate(
            problem="A community programme has low engagement.",
            opportunities=[],
            inspirations=[],
        )

        self.assertEqual(
            hypotheses,
            [],
        )

    def test_multiple_inspirations_create_combined_innovation_hypothesis(self):
        inspiration_engine = InnovationInspirationEngine()

        inspirations = [
            inspiration_engine.create(
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
                transferability="moderate",
            ),
            inspiration_engine.create(
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
                transferability="moderate",
            ),
        ]

        opportunity = SimpleNamespace(
            opportunity_type="emerging_pattern",
            title="Young people face service access barriers",
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

        hypotheses = self.engine.generate(
            problem=(
                "Young people face barriers to "
                "community service access."
            ),
            opportunities=[opportunity],
            inspirations=inspirations,
        )

        self.assertGreater(
            len(hypotheses),
            0,
        )

        hypothesis = hypotheses[0]

        combined_text = " ".join(
            [
                hypothesis.title,
                hypothesis.novel_combination,
                hypothesis.underlying_mechanism,
                hypothesis.evidence_basis,
            ]
            if isinstance(
                hypothesis.evidence_basis,
                list,
            )
            else [
                hypothesis.title,
                hypothesis.novel_combination,
                hypothesis.underlying_mechanism,
                hypothesis.evidence_basis,
            ]
        ).lower()

        self.assertIn(
            "peer",
            combined_text,
        )

        self.assertTrue(
            "mobile" in combined_text
            or "outreach" in combined_text
        )
if __name__ == "__main__":
    unittest.main()
