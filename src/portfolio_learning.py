"""Portfolio-level, non-causal learning across documented records."""
from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Dict, List, Optional


@dataclass
class ProgrammePortfolio:
    title: str
    description: str
    programme_ids: List[str] = field(default_factory=list)
    experiment_ids: List[str] = field(default_factory=list)
    portfolio_id: Optional[str] = None
    sector: Optional[str] = None
    geography: Optional[str] = None
    population: Optional[str] = None
    time_period: Optional[str] = None
    provenance: Optional[str] = None
    limitations: List[str] = field(default_factory=list)
    def to_dict(self): return asdict(self)
    def validated(self):
        if not isinstance(self.title, str) or not self.title.strip(): raise ValueError("portfolio title cannot be empty")
        if not isinstance(self.description, str) or not self.description.strip(): raise ValueError("portfolio description cannot be empty")
        for ids in (self.programme_ids, self.experiment_ids):
            if not isinstance(ids, list) or not all(isinstance(x, str) and x.strip() for x in ids): raise ValueError("portfolio identifiers must be non-empty strings")
        payload=self.to_dict(); pid=self.portfolio_id or "portfolio-"+hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()[:24]
        return ProgrammePortfolio(self.title.strip(),self.description.strip(),list(self.programme_ids),list(self.experiment_ids),pid,self.sector,self.geography,self.population,self.time_period,self.provenance,list(self.limitations))


@dataclass
class PortfolioPattern:
    pattern_type: str; description: str; evidence_basis: List[str]
    programme_ids: List[str] = field(default_factory=list); mechanism_ids: List[str] = field(default_factory=list)
    metric_ids: List[str] = field(default_factory=list); uncertainty: List[str] = field(default_factory=list)
    context: Dict = field(default_factory=dict); provenance: List[str] = field(default_factory=list)
    def to_dict(self): return asdict(self)


@dataclass
class StrategyOpportunity:
    title: str; pattern_type: str; description: str; evidence_basis: List[str]
    programme_ids: List[str]; mechanism_ids: List[str]; metric_ids: List[str]
    uncertainty: List[str]; investigation_questions: List[str]; potential_experiment: Optional[str] = None
    opportunity_id: Optional[str] = None
    def to_dict(self): return asdict(self)


class PortfolioLearningEngine:
    """Describes recurrence and differences; never ranks or infers effectiveness."""
    def __init__(self, minimum_programmes=2, minimum_observations=2):
        if minimum_programmes < 1 or minimum_observations < 1: raise ValueError("minimum evidence thresholds must be positive")
        self.minimum_programmes,self.minimum_observations=minimum_programmes,minimum_observations
    def analyse(self, portfolio, programmes=None, mechanisms=None, experiments=None, outcome_metrics=None, outcome_observations=None, learning_records=None):
        portfolio=portfolio.validated(); programmes=programmes or []; mechanisms=mechanisms or []; observations=outcome_observations or []
        known={p.programme_id for p in programmes}
        if any(x not in known for x in portfolio.programme_ids): raise ValueError("portfolio references unknown programme_id")
        patterns=[]
        for mechanism in mechanisms:
            ids=[x for x in mechanism.source_programme_ids if x in portfolio.programme_ids]
            sectors=list(mechanism.sectors_seen); populations=list(mechanism.populations_seen); contexts=list(mechanism.contexts_seen)
            basis=[f"Mechanism {mechanism.name} recurs across {len(ids)} documented programmes."]
            base=dict(programme_ids=ids,mechanism_ids=[mechanism.mechanism_id] if mechanism.mechanism_id else [], evidence_basis=basis, context={"sectors":sectors,"populations":populations,"contexts":contexts}, provenance=[mechanism.provenance] if mechanism.provenance else [])
            if len(ids)<self.minimum_programmes: patterns.append(PortfolioPattern("evidence_gap","Mechanism has insufficient programme coverage for portfolio-level interpretation.",uncertainty=["Frequency is descriptive and does not establish effectiveness."],**base)); continue
            patterns.append(PortfolioPattern("recurring_observation","Mechanism recurs across documented programmes and may warrant comparative investigation.",uncertainty=["Recurrence is not evidence of effectiveness or causality.",*mechanism.uncertainty],**base))
            if len(set(sectors+populations+contexts))>1: patterns.append(PortfolioPattern("context_dependency","The documented mechanism appears across differing contexts; observations must not be pooled.",uncertainty=["Context differences may explain variation."],**base))
        if len(observations)<self.minimum_observations: patterns.append(PortfolioPattern("evidence_gap","Insufficient outcome observations for comparative portfolio interpretation.",["Outcome observation count is below the configured threshold."],uncertainty=["No effectiveness conclusion can be drawn."]))
        else:
            metrics={o.metric_id for o in observations}; contexts={(o.population,o.measurement_period,o.measurement_method) for o in observations}
            if len(metrics)>1: patterns.append(PortfolioPattern("measurement_inconsistency","Different metrics were recorded and were not pooled.",["Multiple metric identifiers were observed."],metric_ids=list(metrics),uncertainty=["Incompatible metrics cannot support a single score."]))
            if len(contexts)>1: patterns.append(PortfolioPattern("context_dependency","Outcome observations differ by population, period, or method.",["Context metadata differs across observations."],metric_ids=list(metrics),uncertainty=["Differences are descriptive, not causal."]))
        return patterns
    def analyse_persisted(self, store, portfolio):
        """Retrieve through repository interfaces while retaining direct-input support."""
        programmes=[store.historical.get_programme(pid) for pid in portfolio.programme_ids]
        mechanisms=[mechanism for mechanism in store.historical.list_mechanisms() if set(mechanism.source_programme_ids)&set(portfolio.programme_ids)]
        experiments=[store.experiments.get(eid).experiment for eid in portfolio.experiment_ids]
        observations=[]
        for experiment in experiments: observations.extend(store.outcomes.list_observations(experiment.experiment_id))
        return self.analyse(portfolio,programmes,mechanisms,experiments,outcome_observations=observations)


class StrategyDiscoveryEngine:
    def discover(self, patterns):
        result=[]
        for pattern in patterns:
            ident="strategy-"+hashlib.sha256(json.dumps(pattern.to_dict(),sort_keys=True).encode()).hexdigest()[:24]
            result.append(StrategyOpportunity("Investigate portfolio pattern",pattern.pattern_type,pattern.description,list(pattern.evidence_basis),list(pattern.programme_ids),list(pattern.mechanism_ids),list(pattern.metric_ids),list(pattern.uncertainty)+["This is an exploratory opportunity, not a recommendation."],["What contextual evidence is needed before a bounded test?"],"Consider a human-approved, comparable measurement design." if pattern.pattern_type in {"context_dependency","measurement_inconsistency"} else None,ident))
        return result
