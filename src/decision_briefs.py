"""Traceable briefing objects for human decision support, never recommendations."""
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional
import hashlib,json
def _id(prefix,value): return prefix+"-"+hashlib.sha256(json.dumps(value,sort_keys=True,default=str).encode()).hexdigest()[:24]
@dataclass
class EvidencePack:
 title:str; subject_type:str; subject_id:str; evidence_records:List[Dict]=field(default_factory=list); evidence_quality_summary:List[Dict]=field(default_factory=list); evidence_gaps:List[Dict]=field(default_factory=list); conflicts:List[Dict]=field(default_factory=list); patterns:List[Dict]=field(default_factory=list); insights:List[Dict]=field(default_factory=list); programme_references:List[str]=field(default_factory=list); mechanism_references:List[str]=field(default_factory=list); outcome_metrics:List[Dict]=field(default_factory=list); observations:List[Dict]=field(default_factory=list); provenance:Optional[str]=None; known_limitations:List[str]=field(default_factory=list); generated_at:Optional[str]=None; pack_id:Optional[str]=None
 def to_dict(self): return asdict(self)
 def finalized(self): return EvidencePack(**{**self.to_dict(),"pack_id":self.pack_id or _id("evidence-pack",self.to_dict())})
@dataclass
class DecisionBrief:
 title:str; subject_type:str; subject_id:str; purpose:str; problem_summary:Optional[str]=None; evidence_pack_id:Optional[str]=None; scenarios_considered:List[Dict]=field(default_factory=list); alternatives_considered:List[str]=field(default_factory=list); reviews:List[Dict]=field(default_factory=list); concerns:List[str]=field(default_factory=list); dissent_or_reservations:List[str]=field(default_factory=list); unresolved_questions:List[str]=field(default_factory=list); active_decision:Optional[Dict]=None; authorization_state:List[Dict]=field(default_factory=list); expected_learning:List[str]=field(default_factory=list); key_uncertainties:List[str]=field(default_factory=list); provenance:Optional[str]=None; generated_at:Optional[str]=None; brief_version:int=1; brief_id:Optional[str]=None
 def to_dict(self): return asdict(self)
 def finalized(self): return DecisionBrief(**{**self.to_dict(),"brief_id":self.brief_id or _id("decision-brief",self.to_dict())})
class DecisionBriefBuilder:
 def build(self,title,subject_type,subject_id,purpose,governance_summary=None,scenarios=None,evidence_pack=None,problem_summary=None,provenance=None):
  g=governance_summary or {}; pack=evidence_pack.finalized() if evidence_pack else None
  return DecisionBrief(title,subject_type,subject_id,purpose,problem_summary,pack.pack_id if pack else None,list(scenarios or []),list(g.get("alternatives",[])),list(g.get("reviews",[])),list(g.get("concerns",[])),list(g.get("dissent_or_reservations",[])),list(g.get("unresolved_questions",[])),g.get("active_decision"),list(g.get("authorizations",[])),[],list((pack.known_limitations if pack else [])),provenance).finalized()
