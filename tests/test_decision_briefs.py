import tempfile, unittest
from pathlib import Path
from src.decision_briefs import EvidencePack, DecisionBrief
from src.persistence import SQLitePersistenceStore
class TestDecisionBriefs(unittest.TestCase):
 def test_packs_briefs_versions_and_reopen(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"briefs.sqlite"; store=SQLitePersistenceStore(path)
   pack=store.save_evidence_pack(EvidencePack("Pack","strategic_scenario","s",evidence_records=[{"evidence_id":"e"}],evidence_gaps=[{"gap":"missing"}],conflicts=[{"id":"c"}],programme_references=["p"],mechanism_references=["m"],provenance="report",known_limitations=["limited"]))
   first=store.save_decision_brief(DecisionBrief("Brief","strategic_scenario","s","review",evidence_pack_id=pack.pack_id,alternatives_considered=["defer"],dissent_or_reservations=["reservation"]))
   second=store.save_decision_brief(DecisionBrief("Brief 2","strategic_scenario","s","review",evidence_pack_id="later"))
   self.assertEqual([b.brief_version for b in store.list_decision_brief_versions("strategic_scenario","s")],[1,2]); self.assertEqual(store.get_decision_brief(first.brief_id).evidence_pack_id,pack.pack_id); self.assertEqual(store.get_latest_decision_brief("strategic_scenario","s").brief_id,second.brief_id)
   events=store.audit_events.list_events(); event_types=[event.event_type for event in events]
   for event_type in ("evidence_pack_generated","evidence_pack_stored","decision_brief_generated","decision_brief_version_created"): self.assertIn(event_type,event_types)
   self.assertTrue(any(event.entity_id==pack.pack_id and event.metadata["subject_id"]=="s" for event in events))
   store.close(); reopened=SQLitePersistenceStore(path); self.assertEqual(reopened.get_evidence_pack(pack.pack_id).provenance,"report"); self.assertEqual(reopened.get_latest_decision_brief("strategic_scenario","s").brief_version,2); reopened.close()
if __name__=="__main__": unittest.main()
