import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "examples" / "pilot_01" / "run_pilot.py"
SPEC = importlib.util.spec_from_file_location("pilot_01", SCRIPT)
PILOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PILOT)


class TestEndToEndPilot(unittest.TestCase):
    def test_fictional_pilot_preserves_traceability_and_human_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            result = PILOT.run_pilot(Path(directory))
            self.assertTrue(result["fictional_demo"])
            self.assertEqual(result["evidence_count"], 12)
            for key in ("mechanism_id", "experiment_id", "learning_id", "scenario_id", "review_id",
                        "decision_id", "authorization_id", "evidence_pack_id", "brief_id"):
                self.assertTrue(result[key], key)
            self.assertTrue(result["evidence_gaps"])
            self.assertGreater(result["conflict_count"], 0)
            self.assertEqual(len(result["metric_ids"]), 3)
            self.assertEqual(len(result["outcome_observation_ids"]), 2)
            self.assertGreater(result["historical_candidate_count"], 0)
            self.assertGreater(result["cross_sector_candidate_count"], 0)
            self.assertIn("Portfolio/scenario/governance", result["integration_gaps"][0])
            for name, export in result["exports"].items():
                path = Path(export["path"])
                self.assertTrue(path.is_file(), name)
                self.assertEqual(export["source_snapshot_id"], result["brief_id"])
                self.assertTrue(export["checksum"])
            markdown = Path(result["exports"]["markdown"]["path"]).read_text(encoding="utf-8").lower()
            for required in ("evidence pack id", "dissent or reservations", "key uncertainties", "not a recommendation"):
                self.assertIn(required, markdown)
            for forbidden in ("guaranteed success", "best option", "predicted success", "proves effectiveness"):
                self.assertNotIn(forbidden, markdown)
