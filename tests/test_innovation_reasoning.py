import unittest
from types import SimpleNamespace

from src.innovation_inspiration import (
    InnovationInspirationEngine,
)
from src.innovation_reasoning import (
    InnovationHypothesis,
    InnovationReasoningEngine,
)


class TestInnovationReasoningEngine(unittest.TestCase):

    def setUp(self):
        self.engine = InnovationReasoningEngine()
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

    def test_generate_hypothesis_from_opportunity(self):
        opportunity = SimpleNamespace(
            opportunity_type="emerging_pattern",
            title="Youth service access pattern",
            description=(
                "Young people are experiencing repeated "
                "barriers to service access."
            ),
            evidence_basis=[
                "Programme records",
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
                "service access."
            ),
            opportunities=[opportunity],
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
        opportunity = SimpleNamespace(
            opportunity_type="emerging_pattern",
            title="Service access pattern",
            description=(
                "Young people face barriers to "
                "community services."
            ),
            evidence_basis=[
                "Programme report",
            ],
            confidence="moderate",
            uncertainty=[
                "Causation is not established."
            ],
        )

        hypotheses = self.engine.generate(
            problem=(
                "Young people face barriers to "
                "community services."
            ),
            opportunities=[opportunity],
        )

        hypothesis = hypotheses[0]

        self.assertTrue(
            hypothesis.title
        )
        self.assertTrue(
            hypothesis.problem_connection
        )
        self.assertTrue(
            hypothesis.underlying_mechanism
        )
        self.assertTrue(
            hypothesis.why_it_might_work
        )
        self.assertTrue(
            hypothesis.evidence_basis
        )
        self.assertTrue(
            hypothesis.confidence
        )
        self.assertTrue(
            hypothesis.uncertainty
        )
        self.assertTrue(
            hypothesis.experiment
        )
        self.assertTrue(
            hypothesis.validation_question
        )

    def test_transfer_opportunity_generates_hypothesis(self):
        opportunity = SimpleNamespace(
            opportunity_type="transfer_opportunity",
            title="Peer navigation transfer",
            description=(
                "A peer navigation mechanism may be "
                "adapted to the target context."
            ),
            evidence_basis=[
                "Cross-sector programme",
            ],
            confidence="moderate",
            uncertainty=[
                "Transferability is uncertain."
            ],
        )

        hypotheses = self.engine.generate(
            problem=(
                "Community members face barriers to "
                "accessing services."
            ),
            opportunities=[opportunity],
        )

        self.assertGreater(
            len(hypotheses),
            0,
        )

        self.assertIn(
            "transfer",
            hypotheses[0].novel_combination.lower(),
        )

    def test_evidence_gap_generates_hypothesis(self):
        opportunity = SimpleNamespace(
            opportunity_type="evidence_gap",
            title="Missing outcome evidence",
            description=(
                "There is insufficient evidence about "
                "long-term service outcomes."
            ),
            evidence_basis=[
                "Programme documentation",
            ],
            confidence="low",
            uncertainty=[
                "Outcome evidence is incomplete."
            ],
        )

        hypotheses = self.engine.generate(
            problem=(
                "The programme lacks evidence about "
                "long-term outcomes."
            ),
            opportunities=[opportunity],
        )

        self.assertGreater(
            len(hypotheses),
            0,
        )

        self.assertIn(
            "evidence",
            hypotheses[0].underlying_mechanism.lower(),
        )

    def test_contradiction_generates_hypothesis(self):
        opportunity = SimpleNamespace(
            opportunity_type="contradiction",
            title="Conflicting service outcomes",
            description=(
                "Different evidence sources report "
                "different outcomes."
            ),
            evidence_basis=[
                "Programme report",
                "Community feedback",
            ],
            confidence="moderate",
            uncertainty=[
                "The reasons for the contradiction "
                "are unclear."
            ],
        )

        hypotheses = self.engine.generate(
            problem=(
                "Evidence shows conflicting outcomes "
                "for the same service."
            ),
            opportunities=[opportunity],
        )

        self.assertGreater(
            len(hypotheses),
            0,
        )

        self.assertTrue(
            "context"
            in hypotheses[0].underlying_mechanism.lower()
            or "different"
            in hypotheses[0].why_it_might_work.lower()
        )

    def test_hypothesis_contains_uncertainty(self):
        opportunity = SimpleNamespace(
            opportunity_type="emerging_pattern",
            title="Emerging pattern",
            description=(
                "A recurring pattern has been observed."
            ),
            evidence_basis=[
                "Programme records",
            ],
            confidence="moderate",
            uncertainty=[
                "The pattern may have other explanations."
            ],
        )

        hypotheses = self.engine.generate(
            problem=(
                "A recurring service pattern has been "
                "observed."
            ),
            opportunities=[opportunity],
        )

        self.assertGreater(
            len(hypotheses[0].uncertainty),
            0,
        )

    def test_empty_problem_raises_error(self):
        with self.assertRaises(ValueError):
            self.engine.generate(
                problem="",
                opportunities=[],
            )

    def test_no_opportunities_returns_empty(self):
        hypotheses = self.engine.generate(
            problem=(
                "Young people face service barriers."
            ),
            opportunities=[],
        )

        self.assertEqual(
            hypotheses,
            [],
        )

    def test_hypothesis_can_be_converted_to_dict(self):
        opportunity = SimpleNamespace(
            opportunity_type="emerging_pattern",
            title="Service pattern",
            description=(
                "A recurring service pattern exists."
            ),
            evidence_basis=[
                "Programme records",
            ],
            confidence="moderate",
            uncertainty=[
                "The pattern requires validation."
            ],
        )

        hypotheses = self.engine.generate(
            problem=(
                "A recurring service pattern exists."
            ),
            opportunities=[opportunity],
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

    def test_relevant_inspiration_influences_hypothesis(self):
        inspiration = self._create_inspiration(
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
        )

        opportunity = SimpleNamespace(
            opportunity_type="transfer_opportunity",
            title="Peer navigation transfer",
            description=(
                "A peer navigation approach may help "
                "address service access barriers."
            ),
            evidence_basis=[
                "Cross-sector programme",
            ],
            confidence="moderate",
            uncertainty=[
                "Transferability to the target context "
                "is uncertain."
            ],
        )

        hypotheses = self.engine.generate(
            problem=(
                "Young people face barriers to "
                "community health services."
            ),
            opportunities=[opportunity],
            inspirations=[inspiration],
        )

        self.assertGreater(
            len(hypotheses),
            0,
        )

        combined_text = " ".join(
            [
                str(hypotheses[0].title),
                str(hypotheses[0].novel_combination),
                str(hypotheses[0].underlying_mechanism),
            ]
        ).lower()

        self.assertIn(
            "peer",
            combined_text,
        )

    def test_inspiration_is_preserved_in_evidence_basis(self):
        inspiration = self._create_inspiration(
            source_type="historical",
            title="Historical outreach programme",
            context="Community services",
            mechanism=(
                "Outreach workers connect "
                "underserved communities with services."
            ),
            observed_result=(
                "Improved service reach."
            ),
        )

        opportunity = SimpleNamespace(
            opportunity_type="transfer_opportunity",
            title="Outreach transfer",
            description=(
                "An outreach mechanism may be "
                "adapted."
            ),
            evidence_basis=[
                "Historical programme",
            ],
            confidence="moderate",
            uncertainty=[
                "Historical context differs."
            ],
        )

        hypotheses = self.engine.generate(
            problem=(
                "Underserved communities face "
                "service access barriers."
            ),
            opportunities=[opportunity],
            inspirations=[inspiration],
        )

        self.assertGreater(
            len(hypotheses),
            0,
        )

        evidence_basis = str(
            hypotheses[0].evidence_basis
        ).lower()

        self.assertIn(
            "historical outreach programme",
            evidence_basis,
        )

    def test_multiple_inspirations_can_be_used(self):
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
            opportunity_type="transfer_opportunity",
            title="Combined access approach",
            description=(
                "Multiple mechanisms may help "
                "address service access barriers."
            ),
            evidence_basis=[
                "Community feedback",
            ],
            confidence="moderate",
            uncertainty=[
                "The mechanisms have not been "
                "tested together."
            ],
        )

        hypotheses = self.engine.generate(
            problem=(
                "Young people face barriers to "
                "service access."
            ),
            opportunities=[opportunity],
            inspirations=inspirations,
        )

        self.assertGreater(
            len(hypotheses),
            0,
        )

    def test_no_inspiration_still_generates_hypothesis(self):
        opportunity = SimpleNamespace(
            opportunity_type="emerging_pattern",
            title="Service access pattern",
            description=(
                "Young people face repeated "
                "service access barriers."
            ),
            evidence_basis=[
                "Programme records",
            ],
            confidence="moderate",
            uncertainty=[
                "The pattern needs further validation."
            ],
        )

        hypotheses = self.engine.generate(
            problem=(
                "Young people face service "
                "access barriers."
            ),
            opportunities=[opportunity],
            inspirations=[],
        )

        self.assertGreater(
            len(hypotheses),
            0,
        )

    def test_no_evidence_no_opportunities_returns_empty(self):
        hypotheses = self.engine.generate(
            problem=(
                "Young people face service barriers."
            ),
            opportunities=[],
            inspirations=[],
        )

        self.assertEqual(
            hypotheses,
            [],
        )

    def test_multiple_inspirations_create_combined_innovation_hypothesis(
        self,
    ):
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

        combined_parts = [
            str(hypothesis.title),
            str(hypothesis.novel_combination),
            str(hypothesis.underlying_mechanism),
            str(hypothesis.evidence_basis),
        ]

        combined_text = " ".join(
            combined_parts
        ).lower()

        self.assertIn(
            "peer",
            combined_text,
        )

        self.assertTrue(
            hypothesis.title.startswith("Combine")
        )

        self.assertIn(
            "combined inspirations",
            hypothesis.inspiration_source,
        )

        self.assertTrue(
            "mobile" in combined_text
            or "outreach" in combined_text
        )

    def test_evidence_gap_is_not_replaced_by_a_combination(self):
        inspirations = [
            self._create_inspiration(
                source_type="cross_sector",
                title="Peer navigation model",
                context="Community health services",
                mechanism="Trusted peers guide people through services.",
                observed_result="Improved service engagement.",
            ),
            self._create_inspiration(
                source_type="community",
                title="Mobile outreach model",
                context="Community service delivery",
                mechanism="Services are brought closer to communities.",
                observed_result="Improved access.",
            ),
        ]

        opportunity = SimpleNamespace(
            opportunity_type="evidence_gap",
            title="Missing population evidence",
            description="Population evidence is incomplete.",
            evidence_basis=["Programme report", "Community feedback"],
            confidence="low",
            uncertainty=["The affected population is unclear."],
        )

        hypothesis = self.engine.generate(
            problem="Young people face service access barriers.",
            opportunities=[opportunity],
            inspirations=inspirations,
        )[0]

        self.assertEqual(
            hypothesis.title,
            "Strengthen evidence before designing at scale",
        )
        self.assertEqual(
            hypothesis.inspiration_source,
            "evidence-gap analysis",
        )

    def test_contradiction_is_not_replaced_by_a_combination(self):
        inspirations = [
            self._create_inspiration(
                source_type="cross_sector",
                title="Peer navigation model",
                context="Community health services",
                mechanism="Trusted peers guide people through services.",
                observed_result="Improved service engagement.",
            ),
            self._create_inspiration(
                source_type="community",
                title="Mobile outreach model",
                context="Community service delivery",
                mechanism="Services are brought closer to communities.",
                observed_result="Improved access.",
            ),
        ]

        opportunity = SimpleNamespace(
            opportunity_type="contradiction",
            title="Conflicting access outcomes",
            description="Evidence sources report different access outcomes.",
            evidence_basis=["Programme report", "Community feedback"],
            confidence="low",
            uncertainty=["The contexts may differ."],
        )

        hypothesis = self.engine.generate(
            problem="Young people face service access barriers.",
            opportunities=[opportunity],
            inspirations=inspirations,
        )[0]

        self.assertEqual(
            hypothesis.title,
            "Design for different implementation contexts",
        )
        self.assertIn(
            "contradictory evidence",
            hypothesis.inspiration_source,
        )


if __name__ == "__main__":
    unittest.main()
