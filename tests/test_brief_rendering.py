import tempfile
import unittest
from pathlib import Path

from src.brief_rendering import DecisionBriefRenderer, EvidencePackRenderer, safe_filename
from src.decision_briefs import DecisionBrief, EvidencePack
from src.persistence import SQLitePersistenceStore


class TestBriefRendering(unittest.TestCase):
    def setUp(self):
        self.pack = EvidencePack(
            "Evidence snapshot", "scenario", "scenario-1", [{"evidence_id": "ev-1"}],
            evidence_gaps=[{"gap_id": "gap-1"}], conflicts=[{"conflict_id": "conflict-1"}],
            programme_references=["programme-1"], mechanism_references=["mechanism-1"],
            provenance="source-register", known_limitations=["Small sample"], generated_at="2026-01-01T00:00:00Z",
        ).finalized()
        self.brief = DecisionBrief(
            "Brief", "scenario", "scenario-1", "Support a human discussion", "Known problem", self.pack.pack_id,
            alternatives_considered=["Alternative A"], reviews=[{"review_id": "review-1"}], concerns=["Concern"],
            dissent_or_reservations=["Reservation"], unresolved_questions=["Question"],
            active_decision={"decision_id": "decision-1"}, authorization_state=[{"state": "exploratory"}],
            expected_learning=["Learn"], key_uncertainties=["Uncertain"], provenance="brief-source",
            generated_at="2026-01-02T00:00:00Z",
        ).finalized()

    def test_evidence_pack_renders_deterministically_with_traceability(self):
        renderer = EvidencePackRenderer()
        markdown = renderer.render_markdown(self.pack)
        self.assertEqual(markdown, renderer.render_markdown(self.pack))
        self.assertIn(self.pack.pack_id, markdown)
        self.assertIn("Evidence gaps", markdown)
        self.assertIn("Conflicts", markdown)
        self.assertIn("Known limitations", markdown)
        self.assertIn("not a recommendation", markdown)
        html = renderer.render_html(self.pack)
        self.assertIn(self.pack.pack_id, html)
        self.assertIn("Evidence gaps", html)

    def test_brief_renders_human_governance_without_claiming_success(self):
        renderer = DecisionBriefRenderer()
        markdown = renderer.render_markdown(self.brief)
        self.assertEqual(markdown, renderer.render_markdown(self.brief))
        for expected in (self.brief.brief_id, self.pack.pack_id, "Alternatives considered",
                         "Dissent or reservations", "Current human decision", "Authorization state",
                         "Key uncertainties"):
            self.assertIn(expected, markdown)
        self.assertNotIn("best option", markdown.lower())
        self.assertNotIn("proves effectiveness", markdown.lower())
        self.assertIn("Current human decision", renderer.render_html(self.brief))

    def test_safe_filename_write_and_audit_are_explicit(self):
        self.assertEqual(safe_filename("decision brief", "../../subject", "md"), "decision-brief-subject.md")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / safe_filename("decision_brief", self.brief.brief_id, "md")
            renderer = DecisionBriefRenderer()
            content = renderer.render_markdown(self.brief)
            record = renderer.write_markdown(self.brief, path)
            self.assertEqual(path.read_text(encoding="utf-8"), content)
            self.assertEqual(record.entity_id, self.brief.brief_id)
            self.assertEqual(record.checksum, renderer.write_markdown(self.brief, path, overwrite=True).checksum)
            with self.assertRaises(FileExistsError):
                renderer.write_markdown(self.brief, path)
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "audit.sqlite3"
            with SQLitePersistenceStore(db) as store:
                DecisionBriefRenderer().render_markdown(self.brief, audit_events=store.audit_events)
                events = store.audit_events.list_events(self.brief.brief_id)
                self.assertEqual(events[-1].event_type, "decision_brief_rendered")
                self.assertEqual(events[-1].metadata["subject_id"], "scenario-1")
