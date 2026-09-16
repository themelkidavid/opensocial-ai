import unittest
import tempfile
from pathlib import Path
from src.governance import DecisionRecord, ExperimentAuthorization, GovernanceReview, DecisionSupportSummary, GovernanceTimeline
from src.persistence import SQLitePersistenceStore
from src.strategic_scenarios import StrategicScenario
class TestGovernance(unittest.TestCase):
 def test_human_metadata_and_states_are_required(self):
  review=GovernanceReview("strategic_scenario","s","human",review_status="reviewed",evidence_considered=["e"]).validated(); self.assertTrue(review.review_id.startswith("review-"))
  with self.assertRaises(ValueError): GovernanceReview("strategic_scenario","s","").validated()
  with self.assertRaises(ValueError): GovernanceReview("strategic_scenario","s","human",review_status="approved").validated()
 def test_decision_is_explicit_and_never_claims_effectiveness(self):
  decision=DecisionRecord("strategic_scenario","s","approve_experiment","human",decision_status="recorded",rationale="Human decision",alternatives_considered=["defer"],dissent_or_reservations=["small sample"]).validated()
  self.assertTrue(decision.decision_id.startswith("decision-")); self.assertEqual(decision.alternatives_considered,["defer"])
  with self.assertRaises(ValueError): DecisionRecord("strategic_scenario","s","approve_experiment","").validated()
  text=str(decision.to_dict()).lower()
  for forbidden in ("proven effective","best scenario","predicted success"): self.assertNotIn(forbidden,text)
 def test_timeline_summary_and_authorization_are_descriptive(self):
  authorization=ExperimentAuthorization("d","s","human",experiment_concept_id="concept")
  timeline=GovernanceTimeline("strategic_scenario","s",[{"event_type":"review"}])
  summary=DecisionSupportSummary("strategic_scenario","s",["e"],["gap"],["uncertain"],["r"],["alternative"],["reservation"],["question"],"recorded")
  self.assertEqual(authorization.authorized_by,"human"); self.assertEqual(timeline.events[0]["event_type"],"review"); self.assertFalse(hasattr(summary,"recommended_option"))
 def test_persisted_supersession_timeline_summary_and_reopen(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/"governance.sqlite"; store=SQLitePersistenceStore(path)
   scenario=store.save_scenario(StrategicScenario("T","address_evidence_gap","p","q"))
   review=store.governance.save_review(GovernanceReview("strategic_scenario",scenario.scenario_id,"reviewer",review_status="concerns_raised",evidence_considered=["e"],concerns=["gap"],unresolved_questions=["question"]))
   first=store.governance.save_decision(DecisionRecord("strategic_scenario",scenario.scenario_id,"request_more_evidence","maker",decision_status="recorded",rationale="first",review_ids=[review.review_id],alternatives_considered=["defer"],dissent_or_reservations=["reservation"],evidence_basis=["e"]))
   second=store.governance.save_decision(DecisionRecord("strategic_scenario",scenario.scenario_id,"approve_experiment","maker",decision_status="recorded",rationale="second",supersedes_decision_id=first.decision_id))
   self.assertEqual(store.governance.get_decision(first.decision_id).decision_status,"superseded"); self.assertEqual(store.governance.get_active_decision("strategic_scenario",scenario.scenario_id).decision_id,second.decision_id)
   timeline=store.governance.timeline("strategic_scenario",scenario.scenario_id); self.assertTrue(any(e["entity_id"]==review.review_id for e in timeline)); self.assertTrue(any(e["entity_id"]==second.decision_id for e in timeline))
   summary=store.governance.summary("strategic_scenario",scenario.scenario_id); self.assertIn("defer",summary["alternatives"]); self.assertIn("reservation",summary["dissent_or_reservations"]); self.assertEqual(summary["active_decision"]["decision_id"],second.decision_id)
   store.close(); reopened=SQLitePersistenceStore(path); self.assertEqual(reopened.governance.get_active_decision("strategic_scenario",scenario.scenario_id).decision_id,second.decision_id); self.assertEqual(len(reopened.governance.summary("strategic_scenario",scenario.scenario_id)["decision_history"]),2); reopened.close()
if __name__=="__main__": unittest.main()
