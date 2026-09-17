import tempfile
import unittest
from pathlib import Path

from src.evidence import create_evidence
from src.governance import DecisionRecord
from src.persistence import SQLitePersistenceStore
from src.strategic_scenarios import StrategicScenario
from src.workflow import OpenSocialWorkflow


class TestOpenSocialWorkflow(unittest.TestCase):
    def test_identical_governance_rerun_reuses_decision_and_rejects_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SQLitePersistenceStore(Path(directory) / "workflow.sqlite3")
            scenario = store.save_scenario(StrategicScenario("T", "address_evidence_gap", "problem", "question"))
            decision = DecisionRecord("strategic_scenario", scenario.scenario_id, "proceed_to_experiment_design", "fictional-human", decision_status="recorded", rationale="Explicit fictional human decision.").validated()
            workflow = OpenSocialWorkflow(store)
            first = workflow.run("Fictional engagement problem", [create_evidence("report", "Engagement declined.")], decision=decision)
            second = workflow.run("Fictional engagement problem", [create_evidence("report", "Engagement declined.")], decision=decision)
            self.assertEqual(first.decision_ids, second.decision_ids)
            self.assertEqual(len(store.governance.list_decisions("strategic_scenario", scenario.scenario_id)), 1)
            changed = DecisionRecord(**{**decision.to_dict(), "rationale": "Changed content"})
            with self.assertRaisesRegex(ValueError, "Conflicting immutable decision_id"):
                workflow._same_or_save("decision", changed)
            store.close()
