"""Evidence-aware strategic scenarios; never recommendations or predictions."""
from dataclasses import asdict, dataclass, field
import hashlib, json
from typing import Dict, List, Optional

_TYPES={"adapt_existing_mechanism","combine_mechanisms","test_context_difference","address_evidence_gap","test_underexplored_mechanism","compare_delivery_models","investigate_conflicting_results"}
_REVIEWS={"exploratory","reviewed","approved_for_experiment_design","rejected","archived"}

@dataclass
class StrategicScenario:
 title:str; scenario_type:str; problem:str; strategic_question:str
 strategy_opportunity_id:Optional[str]=None; portfolio_pattern_ids:List[str]=field(default_factory=list); programme_ids:List[str]=field(default_factory=list); mechanism_ids:List[str]=field(default_factory=list); inspiration_sources:List[str]=field(default_factory=list); evidence_basis:List[str]=field(default_factory=list); assumptions:List[str]=field(default_factory=list); uncertainties:List[str]=field(default_factory=list); evidence_gaps:List[str]=field(default_factory=list); expected_learning:List[str]=field(default_factory=list); potential_metric_ids:List[str]=field(default_factory=list); potential_experiment:Optional[str]=None; provenance:Optional[str]=None; review_status:str="exploratory"; created_at:Optional[str]=None; scenario_id:Optional[str]=None
 def to_dict(self): return asdict(self)
 def validated(self):
  if self.scenario_type not in _TYPES: raise ValueError("unsupported scenario_type")
  if self.review_status not in _REVIEWS: raise ValueError("unsupported review_status")
  for x in (self.title,self.problem,self.strategic_question):
   if not isinstance(x,str) or not x.strip(): raise ValueError("scenario text cannot be empty")
  payload=self.to_dict(); sid=self.scenario_id or "scenario-"+hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()[:24]
  return StrategicScenario(self.title.strip(),self.scenario_type,self.problem.strip(),self.strategic_question.strip(),self.strategy_opportunity_id,list(self.portfolio_pattern_ids),list(self.programme_ids),list(self.mechanism_ids),list(self.inspiration_sources),list(self.evidence_basis),list(self.assumptions),list(self.uncertainties),list(self.evidence_gaps),list(self.expected_learning),list(self.potential_metric_ids),self.potential_experiment,self.provenance,self.review_status,self.created_at,sid)

@dataclass
class ScenarioComparison:
 scenario_ids:List[str]; evidence_basis:Dict[str,List[str]]; assumptions:Dict[str,List[str]]; uncertainties:Dict[str,List[str]]; evidence_gaps:Dict[str,List[str]]; expected_learning:Dict[str,List[str]]; metric_ids:Dict[str,List[str]]
 def to_dict(self): return asdict(self)

class StrategicScenarioEngine:
 def generate(self, opportunities=None, patterns=None, mechanisms=None, inspirations=None):
  result=[]; seen=set()
  for pattern in patterns or []:
   kind={"evidence_gap":"address_evidence_gap","context_dependency":"test_context_difference","measurement_inconsistency":"test_context_difference","conflicting_observation":"investigate_conflicting_results","underexplored_mechanism":"test_underexplored_mechanism"}.get(pattern.pattern_type,"adapt_existing_mechanism")
   scenario=StrategicScenario("Explore portfolio pattern",kind,pattern.description,"What could a bounded investigation learn from this documented pattern?",portfolio_pattern_ids=["pattern-"+hashlib.sha256(json.dumps(pattern.to_dict(),sort_keys=True).encode()).hexdigest()[:12]],programme_ids=list(pattern.programme_ids),mechanism_ids=list(pattern.mechanism_ids),evidence_basis=list(pattern.evidence_basis),uncertainties=list(pattern.uncertainty),evidence_gaps=list(pattern.evidence_basis) if kind=="address_evidence_gap" else [],expected_learning=["Learn whether the documented uncertainty can be reduced in the stated context."],potential_experiment="Human approval is required before any experiment design.").validated()
   key=(scenario.scenario_type,tuple(scenario.mechanism_ids),tuple(scenario.programme_ids),tuple(scenario.evidence_gaps))
   if key not in seen: seen.add(key); result.append(scenario)
  return result
 def compare(self, scenarios):
  return ScenarioComparison([s.scenario_id for s in scenarios],{s.scenario_id:s.evidence_basis for s in scenarios},{s.scenario_id:s.assumptions for s in scenarios},{s.scenario_id:s.uncertainties for s in scenarios},{s.scenario_id:s.evidence_gaps for s in scenarios},{s.scenario_id:s.expected_learning for s in scenarios},{s.scenario_id:s.potential_metric_ids for s in scenarios})
