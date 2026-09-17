"""Fictional federation strategy-discovery pilot: Part 1 only."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cross_sector_discovery import CrossSectorDiscoveryEngine
from src.brief_rendering import DecisionBriefRenderer
from src.decision_briefs import DecisionBrief, EvidencePack
from src.experiment_design import ExperimentDesign
from src.evidence_ingestion import EvidenceIngestionAdapter
from src.governance import DecisionRecord, ExperimentAuthorization, GovernanceReview
from src.historical_memory import HistoricalDiscoveryEngine, HistoricalProgrammeIngestion, MechanismRecord
from src.innovation_combination import InnovationCombinationEngine
from src.innovation_inspiration import InnovationInspiration
from src.innovation_reasoning import InnovationReasoningEngine
from src.persistence import SQLitePersistenceStore, _stable_id
from src.portfolio_learning import PortfolioLearningEngine, ProgrammePortfolio, StrategyDiscoveryEngine
from src.strategic_scenarios import StrategicScenario, StrategicScenarioEngine
from src.outcome_metrics import OutcomeMetric, OutcomeObservation
from src.validation_learning import ValidationLearningEngine
from src.workflow import OpenSocialWorkflow

PROBLEM = "A regional federation of community-based organisations is struggling to remain sustainable because member organisations depend heavily on a small number of donors, organisational capacity varies significantly across members, programme knowledge is fragmented, and successful local innovations are rarely transferred between organisations."


def _hypothesis_id(hypothesis):
    return OpenSocialWorkflow.hypothesis_id(hypothesis)


def _novelty(kind):
    if kind in {"context_dependency", "measurement_inconsistency"}:
        return {"classification": "cross_context_adaptation", "reason": "It preserves documented context differences rather than assuming transfer."}
    if kind == "recurring_observation":
        return {"classification": "directly_evident", "reason": "It describes recurrence already present in supplied records."}
    if kind == "evidence_gap":
        return {"classification": "directly_evident", "reason": "It makes missing or partial evidence visible; it is not a novel intervention."}
    return {"classification": "useful_recombination", "reason": "It connects existing documented mechanisms without claiming effectiveness."}


def run_pilot(output_directory):
    """Run fictional strategy discovery only; no governance or intervention is created."""
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).parent
    imported = EvidenceIngestionAdapter().from_json((here / "evidence.json").read_text(), "fictional-pilot-02")
    historical_input = HistoricalProgrammeIngestion().from_json((here / "historical_programmes.json").read_text())
    with SQLitePersistenceStore(output / "pilot_02.sqlite3") as store:
        workflow = OpenSocialWorkflow(store)
        workflow_result = workflow.run(PROBLEM, [item.evidence for item in imported], [item.provenance for item in imported])
        report = workflow_result.report
        programmes = [store.save_historical_programme(item) for item in historical_input]
        historical = HistoricalDiscoveryEngine().discover(PROBLEM, programmes, target_sector="community organisations")
        inspirations = [InnovationInspiration("historical", p.title, p.geography or "unknown", p.mechanism,
            "; ".join(p.observed_results) or "No observed result recorded.", p.transferability, sector=p.sector,
            target_population=p.target_population, provenance_source_id=p.programme_id,
            provenance_reference=p.provenance_reference) for p in programmes]
        cross_sector = CrossSectorDiscoveryEngine().discover(PROBLEM, inspirations, target_sector="community organisations", prefer_cross_sector=True, cross_sector_boost=0.1)
        hypotheses = InnovationReasoningEngine().generate(PROBLEM, report.innovation_opportunities,
            historical_programme_candidates=historical, cross_sector_candidates=cross_sector)
        combinations = InnovationCombinationEngine().combine(PROBLEM, inspirations=inspirations[:2]) if len(inspirations) > 1 else []
        mechanisms = []
        for programme in programmes:
            mechanisms.append(store.save_mechanism(MechanismRecord(programme.mechanism, "Fictional historical mechanism.",
                source_programme_ids=[programme.programme_id], sectors_seen=[programme.sector] if programme.sector else [],
                populations_seen=[programme.target_population] if programme.target_population else [],
                contexts_seen=[programme.geography] if programme.geography else [], evidence_basis=list(programme.evidence_basis),
                uncertainty=list(programme.limitations), provenance=programme.provenance_source_id)))
        recurring = store.save_mechanism(MechanismRecord("peer learning and knowledge exchange", "Fictional recurrent knowledge-transfer mechanisms.",
            source_programme_ids=[programmes[0].programme_id, programmes[4].programme_id, programmes[5].programme_id],
            sectors_seen=["community organisations", "open-source communities", "startup accelerators"],
            populations_seen=["member organisations", "programme staff"], contexts_seen=["North region", "Central region", "Coastal region"],
            evidence_basis=["pilot2-h1", "pilot2-h5", "pilot2-h6"], uncertainty=["Recurrence does not establish effectiveness."], provenance="fictional-pilot-02"))
        portfolio = store.save_portfolio(ProgrammePortfolio("Fictional federation portfolio", "Fictional member and historical records; no effectiveness ranking.",
            [p.programme_id for p in programmes], provenance="fictional-pilot-02", limitations=["Organisational maturity and measures differ."]))
        patterns = PortfolioLearningEngine(minimum_programmes=2, minimum_observations=2).analyse_persisted(store, portfolio)
        opportunities = StrategyDiscoveryEngine().discover(patterns)
        store.portfolios.record_analysis(portfolio.portfolio_id, patterns, opportunities)
        source_hypothesis_ids = [_hypothesis_id(item) for item in hypotheses[:2]]
        scenarios = [store.save_scenario(StrategicScenario(**{**item.to_dict(), "source_hypothesis_ids": source_hypothesis_ids,
            "provenance": "fictional-pilot-02"})) for item in StrategicScenarioEngine().generate(patterns=patterns)]
        # Explicit fictional human selection by the pilot author; no score or ranking is used.
        selected = scenarios[0]
        alternatives = [item.scenario_id for item in scenarios[1:3]]
        review = GovernanceReview("strategic_scenario", selected.scenario_id, "pilot2-reviewer-001",
            reviewer_role="fictional federation reviewer", review_status="concerns_raised",
            evidence_considered=workflow_result.evidence_ids,
            concerns=list(selected.uncertainties[:1]) or ["Outcome evidence remains incomplete."],
            unresolved_questions=["Which member contexts can support a bounded learning exercise?"],
            comments="Fictional human review; sector transferability and member readiness require investigation.",
            provenance="fictional-pilot-02").validated()
        review_id = workflow._same_or_save("review", review)
        decision = DecisionRecord("strategic_scenario", selected.scenario_id, "proceed_to_experiment_design",
            "pilot2-decision-maker-001", decision_maker_role="fictional pilot author and decision maker",
            rationale="The fictional human selected this scenario for bounded investigation, not adoption.",
            decision_status="recorded", evidence_basis=workflow_result.evidence_ids, review_ids=[review_id],
            alternatives_considered=alternatives, dissent_or_reservations=["Member readiness and transferability remain uncertain."],
            conditions=["No implementation or scaling without separate human review."], provenance="fictional-pilot-02").validated()
        decision_id = workflow._same_or_save("decision", decision)
        evidence_ids = workflow_result.evidence_ids
        experiment = ExperimentDesign("experiment-pilot-02", "Fictional federation knowledge-transfer learning exercise",
            f"Scenario {selected.scenario_id}", "Explore delivery and learning signals without inferring organisational effectiveness.",
            selected.potential_experiment or "Test a bounded knowledge-transfer exchange.", "Document current member-specific practice.",
            ["Shared documentation adoption", "Knowledge-resource reuse"], evidence_ids,
            list(selected.uncertainties) + ["A bounded exercise cannot establish sustainability or effectiveness."],
            ["Include affected people from member organisations and community oversight.", "Human authorization is required."],
            ["Do not scale without human review.", "Stop if participation burdens or exclusion are observed."],
            "What can this fictional bounded exercise learn about contextual feasibility?", evidence_ids)
        experiment = store.save_experiment(experiment).experiment
        auth = ExperimentAuthorization(decision_id, selected.scenario_id, "pilot2-decision-maker-001", experiment_id=experiment.experiment_id,
            experiment_concept_id=experiment.title, conditions=["Fictional demonstration only."],
            limitations=["Authorization is not evidence of effectiveness."], provenance="fictional-pilot-02")
        auth = ExperimentAuthorization(**{**auth.to_dict(), "authorization_id": _stable_id("authorization", auth.to_dict())})
        authorization_id = workflow._same_or_save("authorization", auth)
        authorization = store.governance.get_authorization(authorization_id)
        metrics = [store.attach_outcome_metric(experiment.experiment_id, metric) for metric in [
            OutcomeMetric("Shared documentation adoption", "Fictional percentage of participating members using a shared standard.", "percentage", "%", "fictional pilot check-in", direction="increase", baseline_value=20, source="fictional-pilot-02", limitations=["Not a real measurement."]),
            OutcomeMetric("Knowledge-resource reuse", "Fictional recorded reuse rate.", "rate", "%", "fictional activity log", direction="increase", baseline_value=10, source="fictional-pilot-02", limitations=["Context and participation differ."]),
        ]]
        observations = [store.record_outcome_observation(item) for item in [
            OutcomeObservation(experiment.experiment_id, metrics[0].metric_id, 35, "fictional pilot check-in", "pilot2-reviewer-001", measurement_period="fictional month one", measurement_method="fictional check-in", context="regional federation", limitations=["Positive recorded change has no causal comparison."], provenance="fictional-pilot-02"),
            OutcomeObservation(experiment.experiment_id, metrics[1].metric_id, 10, "fictional activity log", "pilot2-reviewer-001", measurement_period="fictional month one", measurement_method="fictional activity log", context="regional federation", limitations=["Neutral reuse result; uneven digital access remained an issue."], provenance="fictional-pilot-02"),
        ]]
        validation = ValidationLearningEngine()
        learning_observation = validation.create_observation(experiment.experiment_id, experiment.title, "The fictional pilot recorded 35% shared documentation adoption.", ["fictional pilot check-in"], ["No comparison group; uneven digital access remains."], "pilot2-reviewer-001")
        stored_observation = store.record_observation(learning_observation)
        learning = store.save_learning(validation.evaluate([learning_observation])[0], stored_observation.observation_id)
        store.historical.link_learning(programmes[0].programme_id, mechanisms[0].mechanism_id, learning.learning_id)
        pack = store.save_evidence_pack(EvidencePack("Fictional Pilot 02 Evidence Pack", "strategic_scenario", selected.scenario_id,
            evidence_records=[{"evidence_id": evidence_id, "evidence": item.evidence.to_dict(), "provenance": item.provenance.to_dict()} for evidence_id, item in zip(workflow_result.evidence_ids, imported)],
            evidence_quality_summary=[item.to_dict() for item in report.evidence_quality],
            evidence_gaps=[item.to_dict() for item in report.evidence_gap_details] + [item.to_dict() for item in patterns if item.pattern_type == "evidence_gap"],
            conflicts=[item.to_dict() for item in report.evidence_conflicts], patterns=[item.to_dict() for item in report.observed_patterns] + [item.to_dict() for item in patterns],
            insights=[item.to_dict() for item in report.insights] + [{"learning_id": learning.learning_id, "learning": learning.learning.to_dict()}],
            programme_references=[item.programme_id for item in programmes], mechanism_references=[item.mechanism_id for item in mechanisms],
            outcome_metrics=[item.to_dict() for item in metrics], observations=[item.to_dict() for item in observations],
            provenance="fictional-pilot-02", known_limitations=["All content is fictional demonstration data.", "Narrative disagreement was not converted into a formal conflict.", "Observed values do not establish causality or effectiveness."],
            source_hypothesis_ids=selected.source_hypothesis_ids))
        brief = DecisionBrief("Fictional Pilot 02 Strategic Decision Brief", "strategic_scenario", selected.scenario_id,
            "Support explicit fictional human review of a bounded learning exercise; not a recommendation.", PROBLEM,
            evidence_pack_id=pack.pack_id, scenarios_considered=[item.to_dict() for item in scenarios], alternatives_considered=alternatives,
            reviews=[store.governance.get_review(review_id).to_dict()], concerns=review.concerns,
            dissent_or_reservations=decision.dissent_or_reservations, unresolved_questions=review.unresolved_questions,
            active_decision=store.governance.get_decision(decision_id).to_dict(), authorization_state=[authorization.to_dict()],
            expected_learning=list(selected.expected_learning) + [learning.learning.learning],
            key_uncertainties=list(selected.uncertainties) + pack.known_limitations,
            provenance="fictional-pilot-02", source_hypothesis_ids=selected.source_hypothesis_ids).finalized()
        existing_brief = store.get_decision_brief(brief.brief_id)
        if existing_brief is not None and existing_brief.to_dict() != brief.to_dict():
            raise ValueError("Conflicting immutable pilot decision brief")
        brief = existing_brief or store.save_decision_brief(brief)
        renderer = DecisionBriefRenderer()
        exports = {
            "markdown": renderer.write_markdown(brief, output / "pilot_02_decision_brief.md", overwrite=True, audit_events=store.audit_events).to_dict(),
            "html": renderer.write_html(brief, output / "pilot_02_decision_brief.html", overwrite=True, audit_events=store.audit_events).to_dict(),
            "docx": renderer.write_docx(brief, output / "pilot_02_decision_brief.docx", overwrite=True, audit_events=store.audit_events).to_dict(),
            "pdf": renderer.write_pdf(brief, output / "pilot_02_decision_brief.pdf", overwrite=True, audit_events=store.audit_events).to_dict(),
        }
        summary = {
            "fictional_demo": True, "problem": PROBLEM,
            "evidence_ids": workflow_result.evidence_ids,
            "evidence_quality": [item.to_dict() for item in report.evidence_quality],
            "evidence_gaps": [item.to_dict() for item in report.evidence_gap_details],
            "conflicts": [item.to_dict() for item in report.evidence_conflicts],
            "patterns": [item.to_dict() for item in report.observed_patterns],
            "opportunity_ids": [_hypothesis_id(item) for item in report.innovation_hypotheses],
            "historical_candidates": [item.to_dict() for item in historical],
            "cross_sector_candidates": [item.to_dict() for item in cross_sector if item.is_cross_sector],
            "hypotheses": [{"hypothesis_id": _hypothesis_id(item), **item.to_dict()} for item in hypotheses],
            "combinations": [item.to_dict() for item in combinations],
            "portfolio_patterns": [item.to_dict() for item in patterns],
            "strategy_opportunities": [item.to_dict() for item in opportunities],
            "scenarios": [item.to_dict() for item in scenarios],
            "novelty": [{"entity_id": item.opportunity_id, **_novelty(item.pattern_type)} for item in opportunities] +
                       [{"entity_id": item.scenario_id, **_novelty(item.scenario_type)} for item in scenarios],
            "responsible_ai": "Fictional demonstration only. No ranking, recommendation, transferability claim, causal claim, approval, or success prediction is made.",
            "human_selection": {"selected_scenario_id": selected.scenario_id, "selected_by": "pilot2-decision-maker-001", "alternatives_considered": alternatives},
            "governance": {"review_id": review_id, "decision_id": decision_id, "authorization_id": authorization.authorization_id},
            "experiment": {"experiment_id": experiment.experiment_id, "source_scenario_id": selected.scenario_id, "source_hypothesis_ids": selected.source_hypothesis_ids},
            "metrics": [item.to_dict() for item in metrics], "observations": [item.to_dict() for item in observations],
            "learning": learning.to_dict(),
            "evidence_pack": pack.to_dict(), "decision_brief": brief.to_dict(), "exports": exports,
        }
        (output / "pilot_02_part_1_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        return summary


if __name__ == "__main__":
    print(json.dumps(run_pilot(Path(__file__).parent / "output"), indent=2, sort_keys=True))
