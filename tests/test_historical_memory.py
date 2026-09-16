import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.evidence import create_evidence
from src.experiment_design import ExperimentDesignEngine
from src.historical_memory import (
    HistoricalDiscoveryEngine,
    HistoricalMemoryStore,
    HistoricalProgramme,
    HistoricalProgrammeIngestion,
    MechanismRecord,
)
from src.innovation_combination import InnovationCombinationEngine
from src.innovation_inspiration import InnovationInspiration
from src.innovation_reasoning import InnovationHypothesis, InnovationReasoningEngine
from src.persistence import SQLitePersistenceStore
from src.validation_learning import ValidationLearningEngine


class TestHistoricalMemory(unittest.TestCase):
    @staticmethod
    def _programme():
        return HistoricalProgramme(
            "Peer programme",
            "Access barriers",
            "Trusted peers guide people through services.",
            sector="health",
            provenance_source_id="programme-1",
            evidence_basis=["Pilot feedback"],
            limitations=["Small pilot"],
        )

    def _learning(self, store):
        hypothesis = InnovationHypothesis(
            "Peer idea", "Access barriers", "source", "Trusted peers",
            "adapt", "may help", ["evidence"], "exploratory",
            ["uncertain"], "pilot", "question",
        )
        experiment = ExperimentDesignEngine().design([hypothesis])[0]
        evidence = store.save_evidence(create_evidence("report", "evidence"))
        experiment = experiment.with_analysis_evidence_ids([evidence.evidence_id])
        store.save_experiment(experiment)
        observation = ValidationLearningEngine().create_observation(
            experiment.experiment_id,
            experiment.title,
            "reported outcome",
            ["pilot feedback"],
            reviewer="reviewer",
        )
        stored = store.record_observation(observation)
        learning = ValidationLearningEngine().evaluate([observation])[0]
        return store.save_learning(learning,stored.observation_id).learning_id

    def test_main_store_persists_history_links_audits_and_reopens(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "main.sqlite"
            store = SQLitePersistenceStore(path)
            programme = store.save_historical_programme(self._programme())
            mechanism = store.save_mechanism(MechanismRecord(
                "trusted peers", "Peer guidance",
                source_programme_ids=[programme.programme_id],
                provenance="programme-1",
            ))
            learning_id = self._learning(store)
            store.historical.link_learning(programme.programme_id,mechanism.mechanism_id,learning_id)
            events = [event.event_type for event in store.audit_events.list_events()]
            self.assertIn("historical_programme_imported", events)
            self.assertIn("mechanism_stored", events)
            self.assertIn("historical_learning_linked", events)
            store.close()
            reopened = SQLitePersistenceStore(path)
            self.assertEqual(
                reopened.historical.get_programme(
                    programme.programme_id
                ).provenance_source_id,
                "programme-1",
            )
            self.assertEqual(
                reopened.historical.get_mechanism(
                    mechanism.mechanism_id
                ).source_programme_ids,
                [programme.programme_id],
            )
            self.assertEqual(
                reopened.historical.get_mechanism(
                    mechanism.mechanism_id
                ).provenance,
                "programme-1",
            )
            programme_mechanism_link = reopened._connection.execute(
                "SELECT 1 FROM programme_mechanisms "
                "WHERE programme_id = ? AND mechanism_id = ?",
                (programme.programme_id, mechanism.mechanism_id),
            ).fetchone()
            learning_link = reopened._connection.execute(
                "SELECT 1 FROM historical_learning_links "
                "WHERE programme_id = ? AND mechanism_id = ? "
                "AND learning_id = ?",
                (programme.programme_id, mechanism.mechanism_id, learning_id),
            ).fetchone()
            self.assertIsNotNone(programme_mechanism_link)
            self.assertIsNotNone(learning_link)
            reopened.close()

    def test_main_store_rejects_invalid_historical_learning_links(self):
        store = SQLitePersistenceStore()
        programme = store.save_historical_programme(self._programme())
        mechanism = store.save_mechanism(MechanismRecord(
            "trusted peers", "Peer guidance",
            source_programme_ids=[programme.programme_id],
        ))
        with self.assertRaisesRegex(ValueError, "programme"):
            store.historical.link_learning("unknown", mechanism.mechanism_id, "unknown")
        with self.assertRaisesRegex(ValueError, "mechanism"):
            store.historical.link_learning(programme.programme_id, "unknown", "unknown")
        with self.assertRaisesRegex(ValueError, "learning"):
            store.historical.link_learning(
                programme.programme_id, mechanism.mechanism_id, "unknown"
            )
        store.close()

    def test_reasoning_historical_candidates_keep_attribution_and_safeguards(self):
        store = SQLitePersistenceStore()
        programme = store.save_historical_programme(self._programme())
        candidate = HistoricalDiscoveryEngine().discover(
            "peers access", [programme]
        )[0]
        transfer = SimpleNamespace(
            opportunity_type="transfer_opportunity", description="pattern",
            evidence_basis=["a", "b"], confidence="exploratory",
            uncertainty=["uncertain"],
        )
        gap = SimpleNamespace(
            opportunity_type="evidence_gap", description="gap",
            evidence_basis=["a"], confidence="low", uncertainty=["uncertain"],
        )
        contradiction = SimpleNamespace(
            opportunity_type="contradiction", description="conflict",
            evidence_basis=["a", "b"], confidence="low", uncertainty=["uncertain"],
        )
        hypotheses = InnovationReasoningEngine().generate(
            "peers access", [gap, contradiction, transfer],
            historical_programme_candidates=[candidate],
        )
        self.assertFalse(hypotheses[0].title.startswith("Combine"))
        self.assertFalse(hypotheses[1].title.startswith("Combine"))
        self.assertIn(programme.programme_id, hypotheses[2].inspiration_source)
        self.assertIn("provenance", " ".join(hypotheses[2].evidence_basis))
        store.close()

    def test_combination_preserves_historical_programme_and_mechanism_origin(self):
        historical = InnovationInspiration(
            "historical", "Peer programme", "past health programme",
            "Trusted peers guide people through services.", "Access changed",
            sector="health", provenance_source_id="programme-stable-id",
        )
        current = InnovationInspiration(
            "community", "Navigation team", "current local context",
            "Service navigators make warm referrals.", "Referrals completed",
            sector="community-services", provenance_source_id="current-source",
        )
        combination = InnovationCombinationEngine().combine(
            "Improve access", inspirations=[historical, current]
        )[0]
        self.assertEqual(combination.provenance_source_id_a, "programme-stable-id")
        self.assertEqual(combination.source_sector_a, "health")
        self.assertEqual(
            combination.mechanism_a,
            "Trusted peers guide people through services.",
        )
    def test_ingestion_persistence_duplicate_and_discovery(self):
        payload=json.dumps([{"title":"Peer programme","problem_addressed":"Access barriers","mechanism":"Trusted peers guide people through services.","sector":"health","provenance_source_id":"programme-1","observed_results":["Access changed"],"evidence_basis":["Pilot feedback"],"limitations":["Small pilot"]}])
        programme=HistoricalProgrammeIngestion().from_json(payload)[0]
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"history.sqlite"
            store=HistoricalMemoryStore(path); first=store.save_programme(programme); second=store.save_programme(programme)
            self.assertEqual(first.programme_id, second.programme_id)
            self.assertEqual(len(HistoricalMemoryStore(path).list_programmes()),1)
            candidates=HistoricalDiscoveryEngine().discover("People need peer access support",store.list_programmes(),target_sector="health")
        self.assertEqual(candidates[0].programme.provenance_source_id,"programme-1")
        self.assertIn("not establish", " ".join(candidates[0].uncertainty))
        self.assertTrue(all(question.endswith("?") for question in candidates[0].adaptation_questions))

    def test_malformed_import_and_unknown_metadata(self):
        with self.assertRaisesRegex(ValueError,"mechanism"):
            HistoricalProgrammeIngestion().from_json('[{"title":"x","problem_addressed":"y"}]')
        programme=HistoricalProgramme("Unknown record","Access barriers","Trusted peers")
        candidate=HistoricalDiscoveryEngine().discover("peers access",[programme])[0]
        self.assertIsNone(candidate.programme.sector)


if __name__ == "__main__": unittest.main()
