"""Fictional, non-clinical end-to-end OpenSocial AI pilot demonstration."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.brief_rendering import DecisionBriefRenderer
from src.decision_briefs import DecisionBrief, EvidencePack
from src.evidence_ingestion import EvidenceIngestionAdapter
from src.experiment_design import ExperimentDesign
from src.governance import DecisionRecord, ExperimentAuthorization, GovernanceReview
from src.historical_memory import HistoricalDiscoveryEngine, HistoricalProgrammeIngestion, MechanismRecord
from src.innovation_reasoning import InnovationReasoningEngine
from src.outcome_metrics import OutcomeMetric, OutcomeObservation
from src.persistence import SQLitePersistenceStore
from src.portfolio_learning import PortfolioLearningEngine, ProgrammePortfolio, StrategyDiscoveryEngine
from src.strategic_scenarios import StrategicScenario, StrategicScenarioEngine
from src.validation_learning import ValidationLearningEngine
from src.workflow import OpenSocialWorkflow

PROBLEM = "Young adults enrolled in a community health support programme show lower ongoing engagement and follow-up attendance than older participants."


def run_pilot(output_directory):
    """Run a fictional demonstration; returned data is descriptive, not a recommendation."""
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).parent
    imported = EvidenceIngestionAdapter().from_json((here / "evidence.json").read_text(), "fictional-pilot-01")
    historical = HistoricalProgrammeIngestion().from_json((here / "historical_programmes.json").read_text())
    with SQLitePersistenceStore(output / "pilot.sqlite3") as store:
        workflow = OpenSocialWorkflow(store)
        report = workflow.run(
            PROBLEM, [item.evidence for item in imported], evidence_provenance=[item.provenance for item in imported]
        ).report
        programmes = [store.save_historical_programme(item) for item in historical]
        historical_candidates = HistoricalDiscoveryEngine().discover(PROBLEM, programmes, target_sector="community health")
        historical_hypotheses = InnovationReasoningEngine().generate(
            PROBLEM, report.innovation_opportunities, historical_programme_candidates=historical_candidates
        )
        peer_programmes = [p.programme_id for p in programmes if p.mechanism in {"peer navigation", "appointment reminders"}]
        mechanism = store.save_mechanism(MechanismRecord(
            "Peer navigation with reminder support", "Fictional documented mechanisms retained for cautious investigation.",
            source_programme_ids=peer_programmes, sectors_seen=["community health"], populations_seen=["young adults"],
            contexts_seen=["Harbour District", "Riverside"], evidence_basis=["fictional-history-01", "fictional-history-02"],
            uncertainty=["Recurrence does not establish effectiveness."], provenance="fictional-pilot-01",
        ))
        store.save_mechanism(MechanismRecord(
            "Mobile follow-up", "A fictional single-programme record retained to expose an evidence-gap pattern.",
            source_programme_ids=[programmes[2].programme_id], sectors_seen=["community health"],
            populations_seen=["young adults"], contexts_seen=["Riverside"],
            evidence_basis=["fictional-history-03"], uncertainty=["One programme cannot support portfolio interpretation."],
            provenance="fictional-pilot-01",
        ))
        evidence_ids = [item.evidence_id for item in store.evidence.list()]
        experiment = store.save_experiment(ExperimentDesign(
            "experiment-pilot-01", "Fictional peer-navigation and reminder pilot", "Exploratory pilot concept",
            "Explore feasible, acceptable follow-up support; do not infer causality.",
            "Test an opt-in peer-navigation and reminder support concept with human approval.", "Documented baseline follow-up approach.",
            ["Attendance percentage", "Engagement rate", "Missed appointment rate"], evidence_ids,
            ["Mixed evidence and incomplete records require cautious interpretation.", "This pilot cannot establish effectiveness or generalize to other contexts."],
            ["Human approval is required.", "Include community oversight and affected people in review.", "Collect minimum necessary fictional demonstration data."],
            ["Stop if exclusion or credible harm is observed.", "Do not scale without human review."], "What can a bounded pilot learn about feasibility and follow-up engagement?", evidence_ids,
        )).experiment
        metrics = [store.attach_outcome_metric(experiment.experiment_id, metric) for metric in [
            OutcomeMetric("Follow-up attendance", "Fictional pilot attendance percentage.", "percentage", "%", "fictional attendance register", direction="increase", baseline_value=42, source="fictional-pilot-01", limitations=["Not a real-world measurement."]),
            OutcomeMetric("Programme engagement", "Fictional pilot engagement rate.", "rate", "%", "fictional engagement register", direction="increase", baseline_value=50, source="fictional-pilot-01", limitations=["Small fictional demonstration context."]),
            OutcomeMetric("Missed appointment rate", "Fictional pilot missed appointment rate.", "rate", "%", "fictional register", direction="decrease", baseline_value=35, source="fictional-pilot-01", limitations=["No causal interpretation."]),
        ]]
        outcome_observations = [store.record_outcome_observation(item) for item in [
            OutcomeObservation(experiment.experiment_id, metrics[0].metric_id, 47, "fictional pilot register", "pilot-reviewer-001", population="young adults", measurement_period="fictional month one", measurement_method="fictional attendance register", context="Harbour District", limitations=["No comparison group; observed improvement is not proof."], provenance="fictional-pilot-01"),
            OutcomeObservation(experiment.experiment_id, metrics[1].metric_id, 50, "fictional pilot register", "pilot-reviewer-001", population="young adults", measurement_period="fictional month one", measurement_method="fictional engagement register", context="Riverside", limitations=["Neutral result with incomplete follow-up information."], provenance="fictional-pilot-01"),
        ]]
        validation = ValidationLearningEngine()
        validation_observation = validation.create_observation(experiment.experiment_id, experiment.title, "Fictional pilot observation: 47% follow-up attendance was recorded.", ["fictional pilot register"], ["No comparison group; not proof of effectiveness."], "pilot-reviewer-001")
        stored_validation = store.record_observation(validation_observation)
        learning = validation.evaluate([validation_observation])[0]
        stored_learning = store.save_learning(learning, stored_validation.observation_id)
        portfolio = store.save_portfolio(ProgrammePortfolio("Fictional engagement portfolio", "Fictional records only; recurrence is descriptive.", [p.programme_id for p in programmes], [experiment.experiment_id], provenance="fictional-pilot-01", limitations=["No real-world evidence."]))
        patterns = PortfolioLearningEngine(minimum_programmes=2, minimum_observations=2).analyse_persisted(store, portfolio)
        opportunities = StrategyDiscoveryEngine().discover(patterns)
        store.portfolios.record_analysis(portfolio.portfolio_id, patterns, opportunities)
        scenarios = StrategicScenarioEngine().generate(opportunities=opportunities, patterns=patterns)
        source_hypothesis_ids = [workflow.hypothesis_id(report.innovation_hypotheses[0])] if report.innovation_hypotheses else []
        scenario = store.save_scenario(StrategicScenario(**{**scenarios[0].to_dict(), "source_hypothesis_ids": source_hypothesis_ids}))
        review = store.governance.save_review(GovernanceReview("strategic_scenario", scenario.scenario_id, "pilot-reviewer-001", reviewer_role="fictional demo reviewer", review_status="concerns_raised", evidence_considered=evidence_ids, concerns=["Evidence is mixed and fictional."], unresolved_questions=["Would affected young adults find the concept acceptable?"], provenance="fictional-pilot-01"))
        decision = store.governance.save_decision(DecisionRecord("strategic_scenario", scenario.scenario_id, "proceed_to_experiment_design", "pilot-decision-maker-001", decision_maker_role="fictional demo decision maker", rationale="Explicit fictional human decision to allow exploratory design discussion only.", decision_status="recorded", evidence_basis=evidence_ids, review_ids=[review.review_id], alternatives_considered=["Gather more fictional demonstration evidence", "Defer the concept"], dissent_or_reservations=["Conflicting source definitions remain unresolved."], conditions=["No implementation without separate real human approval."], provenance="fictional-pilot-01"))
        authorization = store.governance.authorize(ExperimentAuthorization(decision.decision_id, scenario.scenario_id, "pilot-decision-maker-001", experiment_id=experiment.experiment_id, experiment_concept_id=experiment.title, conditions=["Fictional demo only."], limitations=["Authorization is not scientific validation."], provenance="fictional-pilot-01"))
        pack = store.save_evidence_pack(EvidencePack("Fictional Pilot 01 Evidence Pack", "strategic_scenario", scenario.scenario_id, [item.evidence.to_dict() for item in imported], [quality.to_dict() for quality in report.evidence_quality], [gap.to_dict() for gap in report.evidence_gap_details], [conflict.to_dict() for conflict in report.evidence_conflicts], [pattern.to_dict() for pattern in report.observed_patterns], [insight.to_dict() for insight in report.insights], [p.programme_id for p in programmes], [mechanism.mechanism_id], [metric.to_dict() for metric in metrics], [item.to_dict() for item in outcome_observations], "fictional-pilot-01", ["All content is fictional demonstration data.", "Mixed evidence remains unresolved."], source_hypothesis_ids=source_hypothesis_ids))
        brief = store.save_decision_brief(DecisionBrief("Fictional Pilot 01 Decision Brief", "strategic_scenario", scenario.scenario_id, "Support explicit fictional human review; not a recommendation.", PROBLEM, pack.pack_id, [scenario.to_dict()], ["Gather more fictional demonstration evidence", "Defer the concept"], [review.to_dict()], review.concerns, decision.dissent_or_reservations, review.unresolved_questions, decision.to_dict(), [authorization.to_dict()], scenario.expected_learning, scenario.uncertainties + pack.known_limitations, "fictional-pilot-01", source_hypothesis_ids=source_hypothesis_ids))
        renderer = DecisionBriefRenderer()
        exports = {
            "markdown": renderer.write_markdown(brief, output / "pilot-decision-brief.md", overwrite=True, audit_events=store.audit_events).to_dict(),
            "html": renderer.write_html(brief, output / "pilot-decision-brief.html", overwrite=True, audit_events=store.audit_events).to_dict(),
            "docx": renderer.write_docx(brief, output / "pilot-decision-brief.docx", overwrite=True, audit_events=store.audit_events).to_dict(),
            "pdf": renderer.write_pdf(brief, output / "pilot-decision-brief.pdf", overwrite=True, audit_events=store.audit_events).to_dict(),
        }
        summary = {"fictional_demo": True, "problem": PROBLEM, "evidence_count": len(imported), "evidence_gaps": report.evidence_gaps + [p.description for p in patterns if p.pattern_type == "evidence_gap"], "conflict_count": len(report.evidence_conflicts), "opportunity_count": len(report.innovation_opportunities), "hypothesis_count": len(report.innovation_hypotheses), "historical_candidate_count": len(historical_candidates), "cross_sector_candidate_count": sum(p.programme.sector != "community health" for p in historical_candidates), "historical_hypothesis_count": len(historical_hypotheses), "programme_ids": [p.programme_id for p in programmes], "mechanism_id": mechanism.mechanism_id, "experiment_id": experiment.experiment_id, "metric_ids": [m.metric_id for m in metrics], "outcome_observation_ids": [o.observation_id for o in outcome_observations], "learning_id": stored_learning.learning_id, "scenario_id": scenario.scenario_id, "review_id": review.review_id, "decision_id": decision.decision_id, "authorization_id": authorization.authorization_id, "evidence_pack_id": pack.pack_id, "brief_id": brief.brief_id, "exports": exports, "integration_gaps": ["Portfolio/scenario/governance stages require explicit caller orchestration.", "The generated scenario follows portfolio patterns and is not automatically linked to an innovation hypothesis.", "Historical retrieval is an explicit call separate from the main discovery orchestration."], "responsible_ai": "All identities, observations, and data are fictional; no causal, clinical, recommendation, or success claim is made."}
        (output / "pilot_report.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        return summary


if __name__ == "__main__":
    print(json.dumps(run_pilot(Path(__file__).parent / "output"), indent=2, sort_keys=True))
