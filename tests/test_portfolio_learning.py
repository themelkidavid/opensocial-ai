import unittest
import tempfile
from pathlib import Path
from src.historical_memory import HistoricalProgramme, MechanismRecord
from src.outcome_metrics import OutcomeObservation
from src.portfolio_learning import ProgrammePortfolio, PortfolioLearningEngine, StrategyDiscoveryEngine
from src.persistence import SQLitePersistenceStore

class TestPortfolioLearning(unittest.TestCase):
 def setUp(self):
  self.programmes=[HistoricalProgramme("A","p","m",programme_id="p1",sector="health"),HistoricalProgramme("B","p","m",programme_id="p2",sector="education")]
  self.mechanism=MechanismRecord("Peers","guide",mechanism_id="m1",source_programme_ids=["p1","p2"],sectors_seen=["health","education"],populations_seen=["adults"],contexts_seen=["urban"],provenance="report")
  self.portfolio=ProgrammePortfolio("Portfolio","description",["p1","p2"])
 def test_creation_recurrence_context_and_serialization(self):
  patterns=PortfolioLearningEngine().analyse(self.portfolio,self.programmes,[self.mechanism])
  self.assertIn("recurring_observation",[p.pattern_type for p in patterns]); self.assertIn("context_dependency",[p.pattern_type for p in patterns])
  recurrence=next(p for p in patterns if p.pattern_type=="recurring_observation")
  self.assertEqual(recurrence.provenance,["report"]); self.assertEqual(recurrence.to_dict(),recurrence.to_dict())
  self.assertNotIn("winner",str(recurrence.to_dict()).lower()); self.assertIn("not evidence of effectiveness",str(recurrence.to_dict()).lower())
 def test_invalid_reference_and_threshold_gap(self):
  with self.assertRaisesRegex(ValueError,"unknown") : PortfolioLearningEngine().analyse(ProgrammePortfolio("x","x",["missing"]),self.programmes)
  patterns=PortfolioLearningEngine(minimum_programmes=3,minimum_observations=2).analyse(self.portfolio,self.programmes,[self.mechanism])
  self.assertIn("evidence_gap",[p.pattern_type for p in patterns])
 def test_measurement_difference_and_strategy_are_exploratory(self):
  obs=[OutcomeObservation("e1","a",1,"source","reviewer",population="a",measurement_period="1",measurement_method="records"),OutcomeObservation("e2","b",2,"source","reviewer",population="b",measurement_period="2",measurement_method="survey")]
  patterns=PortfolioLearningEngine().analyse(self.portfolio,self.programmes,[self.mechanism],outcome_observations=obs)
  self.assertIn("measurement_inconsistency",[p.pattern_type for p in patterns]); opportunities=StrategyDiscoveryEngine().discover(patterns)
  self.assertTrue(opportunities); self.assertIn("not a recommendation",str(opportunities[0].to_dict()).lower())
 def test_portfolio_persists_reopens_and_audits_analysis(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/"portfolio.sqlite"; store=SQLitePersistenceStore(path)
   programmes=[store.save_historical_programme(p) for p in self.programmes]
   portfolio=store.save_portfolio(ProgrammePortfolio("Portfolio","description",[p.programme_id for p in programmes],provenance="register",limitations=["partial"]))
   patterns=PortfolioLearningEngine().analyse_persisted(store,portfolio)
   opportunities=StrategyDiscoveryEngine().discover(patterns); store.portfolios.record_analysis(portfolio.portfolio_id,patterns,opportunities)
   self.assertEqual(store.portfolios.get(portfolio.portfolio_id).provenance,"register")
   events=[e.event_type for e in store.audit_events.list_events()]
   for event in ("portfolio_created","portfolio_analysis_performed","portfolio_pattern_generated","strategy_opportunity_generated"): self.assertIn(event,events)
   store.close(); reopened=SQLitePersistenceStore(path); self.assertEqual(reopened.portfolios.get(portfolio.portfolio_id).limitations,["partial"]); reopened.close()
 def test_persistence_rejects_unknown_portfolio_references(self):
  store=SQLitePersistenceStore()
  with self.assertRaisesRegex(ValueError,"Unknown programme"): store.save_portfolio(ProgrammePortfolio("x","x",["missing"]))
  with self.assertRaisesRegex(ValueError,"Unknown experiment"): store.save_portfolio(ProgrammePortfolio("x","x",experiment_ids=["missing"]))
  store.close()
if __name__=="__main__": unittest.main()
