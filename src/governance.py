"""Human-recorded governance; this module never makes decisions."""
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional
import hashlib, json

_SUBJECTS={"strategic_scenario","strategy_opportunity","experiment_design","learning_record","portfolio_pattern"}; _REVIEWS={"pending","reviewed","concerns_raised","needs_revision","completed"}; _TYPES={"proceed_to_experiment_design","approve_experiment","request_more_evidence","revise","defer","reject","archive","continue_monitoring"}; _STATUSES={"proposed","recorded","superseded","withdrawn"}
def _id(prefix,obj): return prefix+"-"+hashlib.sha256(json.dumps(obj,sort_keys=True,default=str).encode()).hexdigest()[:24]
@dataclass
class GovernanceReview:
 subject_type:str; subject_id:str; reviewer_id:str; reviewer_role:Optional[str]=None; review_status:str="pending"; evidence_considered:List[str]=field(default_factory=list); concerns:List[str]=field(default_factory=list); unresolved_questions:List[str]=field(default_factory=list); comments:Optional[str]=None; reviewed_at:Optional[str]=None; provenance:Optional[str]=None; review_id:Optional[str]=None
 def to_dict(self): return asdict(self)
 def validated(self):
  if self.subject_type not in _SUBJECTS or not self.subject_id or not self.reviewer_id: raise ValueError("subject and explicit reviewer identity are required")
  if self.review_status not in _REVIEWS: raise ValueError("unsupported review_status")
  return GovernanceReview(**{**self.to_dict(),"review_id":self.review_id or _id("review",self.to_dict())})
@dataclass
class DecisionRecord:
 subject_type:str; subject_id:str; decision_type:str; decision_maker_id:str; decision_maker_role:Optional[str]=None; rationale:str=""; decision_status:str="proposed"; evidence_basis:List[str]=field(default_factory=list); review_ids:List[str]=field(default_factory=list); alternatives_considered:List[str]=field(default_factory=list); dissent_or_reservations:List[str]=field(default_factory=list); conditions:List[str]=field(default_factory=list); follow_up_actions:List[str]=field(default_factory=list); supersedes_decision_id:Optional[str]=None; decided_at:Optional[str]=None; provenance:Optional[str]=None; decision_id:Optional[str]=None
 def to_dict(self): return asdict(self)
 def validated(self):
  if self.subject_type not in _SUBJECTS or not self.subject_id or not self.decision_maker_id: raise ValueError("subject and explicit decision maker are required")
  if self.decision_type not in _TYPES or self.decision_status not in _STATUSES: raise ValueError("unsupported decision type or status")
  return DecisionRecord(**{**self.to_dict(),"decision_id":self.decision_id or _id("decision",self.to_dict())})
@dataclass
class ExperimentAuthorization:
 decision_id:str; scenario_id:str; authorized_by:str; experiment_id:Optional[str]=None; experiment_concept_id:Optional[str]=None; conditions:List[str]=field(default_factory=list); limitations:List[str]=field(default_factory=list); provenance:Optional[str]=None; status:str="recorded"; authorized_at:Optional[str]=None; authorization_id:Optional[str]=None
 def to_dict(self): return asdict(self)
@dataclass
class GovernanceTimeline:
 subject_type:str; subject_id:str; events:List[Dict]
 def to_dict(self): return asdict(self)
@dataclass
class DecisionSupportSummary:
 subject_type:str; subject_id:str; evidence_available:List[str]; known_gaps:List[str]; uncertainties:List[str]; reviews:List[str]; alternatives:List[str]; dissent_or_reservations:List[str]; unresolved_questions:List[str]; current_governance_status:Optional[str]
 def to_dict(self): return asdict(self)
