import unittest
import tempfile
from pathlib import Path
from src.portfolio_learning import PortfolioPattern
from src.strategic_scenarios import StrategicScenario, StrategicScenarioEngine
from src.historical_memory import HistoricalProgramme, MechanismRecord
from src.persistence import SQLitePersistenceStore

class TestStrategicScenarios(unittest.TestCase):
 def test_scenarios_are_deterministic_exploratory_and_comparable(self):
  pattern=PortfolioPattern("evidence_gap","Missing outcome evidence",["report"],programme_ids=["p"],mechanism_ids=["m"],uncertainty=["unknown"])
  engine=StrategicScenarioEngine(); scenarios=engine.generate(patterns=[pattern,pattern])
  self.assertEqual(len(scenarios),1); scenario=scenarios[0]
  self.assertEqual(scenario.scenario_type,"address_evidence_gap"); self.assertTrue(scenario.scenario_id.startswith("scenario-")); self.assertIn("required",scenario.potential_experiment)
  text=str(scenario.to_dict()).lower()
  for forbidden in ("best option","recommended intervention","guaranteed success","proven effectiveness","predicted outcome"): self.assertNotIn(forbidden,text)
  comparison=engine.compare(scenarios); self.assertFalse(hasattr(comparison,"winner")); self.assertEqual(comparison.scenario_ids,[scenario.scenario_id])
 def test_validation_and_review_states(self):
  base=StrategicScenario("T","adapt_existing_mechanism","p","q",assumptions=["Access is an unverified assumption."],expected_learning=["Learn feasibility."])
  self.assertEqual(base.validated().review_status,"exploratory")
  with self.assertRaisesRegex(ValueError,"review"): StrategicScenario("T","adapt_existing_mechanism","p","q",review_status="effective").validated()
  with self.assertRaisesRegex(ValueError,"scenario_type"): StrategicScenario("T","rank","p","q").validated()
 def test_sqlite_persistence_review_links_and_audits(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/"scenarios.sqlite"; store=SQLitePersistenceStore(path)
   programme=store.save_historical_programme(HistoricalProgramme("P","problem","mechanism"))
   mechanism=store.save_mechanism(MechanismRecord("M","mechanism",source_programme_ids=[programme.programme_id]))
   scenario=StrategicScenario("Test","adapt_existing_mechanism","problem","question",programme_ids=[programme.programme_id],mechanism_ids=[mechanism.mechanism_id],strategy_opportunity_id="strategy-external",provenance="report",potential_experiment="Human approval required.")
   saved=store.save_scenario(scenario); updated=store.scenarios.update_review_status(saved.scenario_id,"reviewed"); store.scenarios.record_comparison([saved.scenario_id])
   self.assertEqual(updated.review_status,"reviewed")
   events=[e.event_type for e in store.audit_events.list_events()]
   for event in ("scenario_generated","scenario_stored","scenario_review_status_changed","scenario_compared","scenario_linked_to_experiment_concept"): self.assertIn(event,events)
   store.close(); reopened=SQLitePersistenceStore(path); loaded=reopened.scenarios.get(saved.scenario_id); self.assertEqual(loaded.provenance,"report"); self.assertEqual(loaded.mechanism_ids,[mechanism.mechanism_id]); reopened.close()
 def test_sqlite_rejects_unknown_links(self):
  store=SQLitePersistenceStore()
  with self.assertRaisesRegex(ValueError,"programme"): store.save_scenario(StrategicScenario("T","adapt_existing_mechanism","p","q",programme_ids=["bad"]))
  store.close()
if __name__=="__main__": unittest.main()
