import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "examples" / "pilot_02" / "run_pilot.py"
SPEC = importlib.util.spec_from_file_location("pilot_02", SCRIPT)
PILOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PILOT)


class TestEndToEndPilot02(unittest.TestCase):
    def test_fictional_federation_strategy_pipeline_preserves_lineage(self):
        with tempfile.TemporaryDirectory() as directory:
            result = PILOT.run_pilot(Path(directory))
            self.assertTrue(result["fictional_demo"])
            self.assertEqual(len(result["evidence_ids"]), 16)
            self.assertTrue(all(item.startswith("evidence-") for item in result["evidence_ids"]))
            self.assertTrue(result["patterns"])
            self.assertTrue(result["evidence_gaps"])
            self.assertTrue(result["historical_candidates"])
            self.assertTrue(result["cross_sector_candidates"])
            for candidate in result["cross_sector_candidates"]:
                self.assertTrue(candidate["is_cross_sector"])
                self.assertTrue(candidate["inspiration"]["provenance_source_id"])
                self.assertTrue(candidate["adaptation_questions"])
            self.assertTrue(result["hypotheses"])
            hypothesis_ids = {item["hypothesis_id"] for item in result["hypotheses"]}
            self.assertTrue(all(item.startswith("hypothesis-") for item in hypothesis_ids))
            self.assertTrue(result["strategy_opportunities"])
            self.assertTrue(result["scenarios"])
            for scenario in result["scenarios"]:
                self.assertTrue(scenario["scenario_id"].startswith("scenario-"))
                self.assertTrue(set(scenario["source_hypothesis_ids"]).issubset(hypothesis_ids))
                self.assertTrue(scenario["provenance"] == "fictional-pilot-02")
            governance = result["governance"]
            self.assertTrue(governance["review_id"].startswith("review-"))
            self.assertTrue(governance["decision_id"].startswith("decision-"))
            self.assertTrue(governance["authorization_id"].startswith("authorization-"))
            self.assertEqual(result["human_selection"]["selected_scenario_id"], result["experiment"]["source_scenario_id"])
            self.assertEqual(len(result["metrics"]), 2)
            self.assertEqual(len(result["observations"]), 2)
            self.assertEqual(result["learning"]["learning"]["experiment_id"], result["experiment"]["experiment_id"])
            repeat = PILOT.run_pilot(Path(directory))
            self.assertEqual(repeat["governance"], governance)
            self.assertEqual(repeat["experiment"]["experiment_id"], result["experiment"]["experiment_id"])
            pack = result["evidence_pack"]
            brief = result["decision_brief"]
            self.assertTrue(pack["pack_id"].startswith("evidence-pack-"))
            self.assertEqual(brief["evidence_pack_id"], pack["pack_id"])
            self.assertEqual(brief["brief_version"], 1)
            self.assertEqual(repeat["decision_brief"]["brief_id"], brief["brief_id"])
            self.assertEqual(repeat["decision_brief"]["brief_version"], 1)
            self.assertTrue(set(brief["source_hypothesis_ids"]).issubset(hypothesis_ids))
            for export in result["exports"].values():
                self.assertEqual(export["source_snapshot_id"], brief["brief_id"])
                self.assertEqual(export["version"], 1)
                self.assertTrue(export["checksum"])
            markdown = Path(result["exports"]["markdown"]["path"]).read_text(encoding="utf-8").lower()
            for expected in ("responsible-ai notice", "dissent or reservations", "key uncertainties", "current human decision"):
                self.assertIn(expected, markdown)
            text = str(result).lower()
            for forbidden in ("best strategy", "recommended adoption", "predicted success", "proven effective"):
                self.assertNotIn(forbidden, text)
