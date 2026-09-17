"""Thin optional orchestration for existing OpenSocial AI components."""
from dataclasses import dataclass, field
import hashlib
import json

from src.historical_memory import HistoricalDiscoveryEngine
from src.innovation_discovery import InnovationDiscoveryEngine
from src.innovation_reasoning import InnovationReasoningEngine
from src.portfolio_learning import PortfolioLearningEngine, StrategyDiscoveryEngine
from src.strategic_scenarios import StrategicScenarioEngine


def _id(value):
    return "hypothesis-" + hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()[:24]


@dataclass
class WorkflowResult:
    evidence_ids: list = field(default_factory=list)
    report: object = None
    innovation_opportunity_ids: list = field(default_factory=list)
    hypothesis_ids: list = field(default_factory=list)
    experiment_ids: list = field(default_factory=list)
    historical_candidate_ids: list = field(default_factory=list)
    portfolio_pattern_ids: list = field(default_factory=list)
    strategy_opportunity_ids: list = field(default_factory=list)
    scenario_ids: list = field(default_factory=list)
    governance_review_ids: list = field(default_factory=list)
    decision_ids: list = field(default_factory=list)
    authorization_ids: list = field(default_factory=list)
    evidence_pack_id: str = None
    decision_brief_id: str = None
    decision_brief_version: int = None


class OpenSocialWorkflow:
    """Coordinates supplied records; it never creates human governance actions."""

    def __init__(self, store):
        self.store = store

    @staticmethod
    def hypothesis_id(hypothesis):
        return _id(hypothesis.to_dict())

    def run(self, problem, evidence, evidence_provenance=None, historical_programmes=None,
            portfolio=None, review=None, decision=None, authorization=None,
            evidence_pack=None, decision_brief=None):
        report = InnovationDiscoveryEngine(storage=self.store).analyse(
            problem, evidence, evidence_provenance=evidence_provenance
        )
        result = WorkflowResult(
            evidence_ids=[item.evidence_id for item in self.store.evidence.list()], report=report,
            innovation_opportunity_ids=[getattr(item, "opportunity_id", None) for item in report.innovation_opportunities],
            hypothesis_ids=[self.hypothesis_id(item) for item in report.innovation_hypotheses],
            experiment_ids=[item.experiment_id for item in report.experiment_designs],
        )
        programmes = [self.store.save_historical_programme(item) for item in (historical_programmes or [])]
        if programmes:
            candidates = HistoricalDiscoveryEngine().discover(problem, programmes)
            historical_hypotheses = InnovationReasoningEngine().generate(
                problem, report.innovation_opportunities, historical_programme_candidates=candidates
            )
            result.historical_candidate_ids = [item.programme.programme_id for item in candidates]
            result.hypothesis_ids.extend(self.hypothesis_id(item) for item in historical_hypotheses)
        if portfolio is not None:
            portfolio = self.store.save_portfolio(portfolio)
            patterns = PortfolioLearningEngine().analyse_persisted(self.store, portfolio)
            opportunities = StrategyDiscoveryEngine().discover(patterns)
            self.store.portfolios.record_analysis(portfolio.portfolio_id, patterns, opportunities)
            scenarios = [self.store.save_scenario(item) for item in StrategicScenarioEngine().generate(patterns=patterns)]
            result.portfolio_pattern_ids = ["pattern-" + hashlib.sha256(json.dumps(item.to_dict(), sort_keys=True).encode()).hexdigest()[:12] for item in patterns]
            result.strategy_opportunity_ids = [item.opportunity_id for item in opportunities]
            result.scenario_ids = [item.scenario_id for item in scenarios]
        if review is not None:
            result.governance_review_ids = [self._same_or_save("review", review)]
        if decision is not None:
            result.decision_ids = [self._same_or_save("decision", decision)]
        if authorization is not None:
            result.authorization_ids = [self._same_or_save("authorization", authorization)]
        if evidence_pack is not None:
            result.evidence_pack_id = self.store.save_evidence_pack(evidence_pack).pack_id
        if decision_brief is not None:
            brief = self.store.save_decision_brief(decision_brief)
            result.decision_brief_id, result.decision_brief_version = brief.brief_id, brief.brief_version
        return result

    def _same_or_save(self, kind, item):
        repository = self.store.governance
        identifier = getattr(item, f"{kind}_id")
        existing = getattr(repository, f"get_{kind}")(identifier) if identifier else None
        if existing is not None:
            if existing.to_dict() != item.to_dict():
                raise ValueError(f"Conflicting immutable {kind}_id")
            return identifier
        saved = repository.save_review(item) if kind == "review" else repository.save_decision(item) if kind == "decision" else repository.authorize(item)
        return getattr(saved, f"{kind}_id")
