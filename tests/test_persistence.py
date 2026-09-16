import tempfile
import unittest
from pathlib import Path
import sqlite3

from src.evidence import create_evidence
from src.experiment_design import ExperimentDesignEngine
from src.innovation_discovery import InnovationDiscoveryEngine
from src.innovation_reasoning import InnovationHypothesis
from src.persistence import EvidenceProvenance, SQLitePersistenceStore
from src.validation_learning import (
    ValidationLearningEngine,
    ValidationObservation,
)


class TestSQLitePersistenceStore(unittest.TestCase):

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "opensocial.db"
        self.store = SQLitePersistenceStore(self.database_path)
        self.validation_engine = ValidationLearningEngine()

    def tearDown(self):
        self.store.close()
        self.temporary_directory.cleanup()

    @staticmethod
    def _hypothesis():
        return InnovationHypothesis(
            title="Adapt peer navigation",
            problem_connection="Young people face service barriers.",
            inspiration_source="community inspiration: Peer navigation",
            underlying_mechanism="Trusted peers guide people through services.",
            novel_combination="Adapt peer navigation locally.",
            why_it_might_work="Community feedback suggests access barriers.",
            evidence_basis=["Community feedback", "Programme report"],
            confidence="exploratory",
            uncertainty=["The mechanism may not transfer."],
            experiment="Pilot peer navigation with one community group.",
            validation_question="Does peer navigation improve access?",
        )

    def _experiment(self):
        return ExperimentDesignEngine().design([self._hypothesis()])[0]

    def _save_experiment(self, experiment=None):
        experiment = experiment or self._experiment()

        if not experiment.analysis_evidence_ids:
            stored_evidence = [
                self.store.save_evidence(
                    create_evidence(
                        source_type="community_feedback",
                        content="Community feedback about navigation barriers.",
                    )
                ),
                self.store.save_evidence(
                    create_evidence(
                        source_type="programme_report",
                        content="Programme report about navigation support.",
                    )
                )
            ]
            experiment.analysis_evidence_ids = [
                record.evidence_id for record in stored_evidence
            ]

        return self.store.save_experiment(experiment)

    def _observation(self, experiment=None, outcome=None):
        experiment = experiment or self._experiment()
        return self.validation_engine.create_observation(
            experiment_id=experiment.experiment_id,
            experiment_title=experiment.title,
            outcome=outcome or "Participants reported fewer navigation barriers.",
            evidence_basis=["Pilot feedback from participants."],
            limitations=["The pilot involved one community group."],
            reviewer="Community programme lead",
        )

    def test_database_initializes_empty_repositories(self):
        self.assertTrue(self.database_path.exists())
        self.assertEqual(self.store.evidence.list(), [])
        self.assertEqual(self.store.experiments.list(), [])
        self.assertEqual(self.store.learning.list_observations(), [])
        self.assertEqual(self.store.learning.list_learning(), [])
        self.assertEqual(self.store.audit_events.list_events(), [])

    def test_save_and_load_evidence_preserves_provenance_and_timestamp(self):
        evidence = create_evidence(
            source_type="community_feedback",
            content="Participants reported difficulties reaching the service.",
            date="2026-01-15",
            location="Madurai",
            population="Young people",
            metadata={"method": "focus_group"},
        )
        provenance = EvidenceProvenance(
            entry_method="imported",
            original_source_id="feedback-17",
            source_reference="community-feedback.json",
            import_format="json",
        )

        stored = self.store.save_evidence(evidence, provenance)
        loaded = self.store.evidence.get(stored.evidence_id)

        self.assertTrue(stored.evidence_id.startswith("evidence-"))
        self.assertIsNotNone(stored.created_at)
        self.assertEqual(loaded.evidence.to_dict(), evidence.to_dict())
        self.assertEqual(loaded.provenance.to_dict(), provenance.to_dict())
        self.assertEqual(loaded.to_dict()["provenance"]["original_source_id"], "feedback-17")

    def test_duplicate_evidence_is_idempotent_and_audited_once(self):
        evidence = create_evidence(
            source_type="research",
            content="Peer support improved service access in a local pilot.",
        )

        first = self.store.save_evidence(evidence)
        second = self.store.save_evidence(evidence)

        self.assertEqual(first.evidence_id, second.evidence_id)
        self.assertEqual(len(self.store.evidence.list()), 1)
        events = self.store.audit_events.list_events(first.evidence_id)
        self.assertEqual([event.event_type for event in events], ["evidence_created"])

    def test_failed_locked_commit_rolls_back_the_write(self):
        reader = sqlite3.connect(str(self.database_path))
        writer = SQLitePersistenceStore(self.database_path)

        try:
            reader.execute("BEGIN")
            reader.execute("SELECT * FROM evidence_records").fetchall()
            writer._connection.execute("PRAGMA busy_timeout = 100")

            with self.assertRaises(sqlite3.OperationalError):
                writer.save_evidence(
                    create_evidence(
                        source_type="research",
                        content="Evidence written while a reader holds a lock.",
                    )
                )

            self.assertFalse(writer._connection.in_transaction)
        finally:
            reader.rollback()
            reader.close()
            writer.close()

        self.assertEqual(self.store.evidence.list(), [])
        self.assertEqual(self.store.audit_events.list_events(), [])

    def test_failed_locked_outer_transaction_rolls_back_the_write(self):
        reader = sqlite3.connect(str(self.database_path))
        writer = SQLitePersistenceStore(self.database_path)

        try:
            reader.execute("BEGIN")
            reader.execute("SELECT * FROM evidence_records").fetchall()
            writer._connection.execute("PRAGMA busy_timeout = 100")

            with self.assertRaises(sqlite3.OperationalError):
                with writer.transaction():
                    writer.save_evidence(
                        create_evidence(
                            source_type="research",
                            content="Evidence in a locked outer transaction.",
                        )
                    )

            self.assertFalse(writer._connection.in_transaction)
        finally:
            reader.rollback()
            reader.close()
            writer.close()

        self.assertEqual(self.store.evidence.list(), [])
        self.assertEqual(self.store.audit_events.list_events(), [])

    def test_save_and_load_experiment_preserves_structured_fields(self):
        experiment = self._experiment()

        stored = self._save_experiment(experiment)
        loaded = self.store.experiments.get(experiment.experiment_id)

        self.assertEqual(stored.experiment_id, experiment.experiment_id)
        self.assertEqual(loaded.experiment.to_dict(), experiment.to_dict())
        self.assertTrue(loaded.created_at)
        self.assertEqual(len(self.store.experiments.list()), 1)

    def test_observation_for_unknown_experiment_is_rejected(self):
        observation = self.validation_engine.create_observation(
            experiment_id="experiment-unknown",
            experiment_title="Pilot: Unknown",
            outcome="Participants reported fewer barriers.",
            evidence_basis=["Pilot feedback"],
            reviewer="Community programme lead",
        )

        with self.assertRaisesRegex(ValueError, "Unknown experiment_id"):
            self.store.record_observation(observation)

        self.assertEqual(self.store.learning.list_observations(), [])

    def test_directly_constructed_invalid_observation_is_rejected_at_storage_boundary(self):
        experiment = self._experiment()
        self._save_experiment(experiment)
        invalid = ValidationObservation(
            experiment_id=experiment.experiment_id,
            experiment_title=experiment.title,
            outcome="Participants reported fewer barriers.",
            evidence_basis=[],
            limitations=[],
            reviewer="",
        )

        with self.assertRaises(ValueError):
            self.store.record_observation(invalid)

        self.assertEqual(self.store.learning.list_observations(), [])

    def test_traceability_links_experiment_observation_and_learning(self):
        experiment = self._experiment()
        self._save_experiment(experiment)
        observation = self._observation(experiment)
        stored_observation = self.store.record_observation(observation)
        learning = self.validation_engine.evaluate([observation])[0]
        stored_learning = self.store.save_learning(
            learning,
            stored_observation.observation_id,
        )

        loaded_learning = self.store.learning.get_learning(stored_learning.learning_id)

        self.assertEqual(
            stored_observation.observation.experiment_id,
            experiment.experiment_id,
        )
        self.assertEqual(loaded_learning.observation_id, stored_observation.observation_id)
        self.assertEqual(loaded_learning.learning.experiment_id, experiment.experiment_id)
        self.assertEqual(
            loaded_learning.to_dict()["learning"]["confidence"],
            "exploratory",
        )

    def test_learning_requires_a_known_matching_observation(self):
        experiment = self._experiment()
        self._save_experiment(experiment)
        observation = self._observation(experiment)
        learning = self.validation_engine.evaluate([observation])[0]

        with self.assertRaisesRegex(ValueError, "Unknown observation_id"):
            self.store.save_learning(learning, "observation-unknown")

    def test_conclusory_direct_learning_cannot_be_persisted(self):
        experiment = self._experiment()
        self._save_experiment(experiment)
        observation = self._observation(experiment)
        stored_observation = self.store.record_observation(observation)
        invalid_learning = self.validation_engine.evaluate([observation])[0]
        invalid_learning.learning = "The outcome proves the intervention works."

        with self.assertRaisesRegex(
            ValueError,
            "generated from the stored reviewer-attributed observation",
        ):
            self.store.save_learning(
                invalid_learning,
                stored_observation.observation_id,
            )

    def test_direct_experiment_without_required_safeguards_is_rejected(self):
        stored_evidence = self.store.save_evidence(
            create_evidence(
                source_type="programme_report",
                content="A report describing a bounded pilot.",
            )
        )
        unsafe_experiment = self._experiment()
        unsafe_experiment.analysis_evidence_ids = [
            stored_evidence.evidence_id
        ]
        unsafe_experiment.safeguards = [
            "Obtain appropriate organisational approval before starting.",
            "Collect only the minimum information needed to learn safely.",
        ]

        with self.assertRaisesRegex(ValueError, "community oversight"):
            self.store.save_experiment(unsafe_experiment)

        self.assertEqual(self.store.experiments.list(), [])

    def test_experiment_rejects_unknown_analysis_evidence(self):
        experiment = self._experiment()
        experiment.analysis_evidence_ids = ["evidence-unknown"]

        with self.assertRaisesRegex(ValueError, "Unknown evidence_id"):
            self.store.save_experiment(experiment)

        self.assertEqual(self.store.experiments.list(), [])

    def test_experiment_analysis_lineage_survives_reopen_and_can_expand(self):
        experiment = self._experiment()
        first = self.store.save_evidence(
            create_evidence(
                source_type="community_feedback",
                content="Community members described navigation barriers.",
            )
        )
        second = self.store.save_evidence(
            create_evidence(
                source_type="programme_report",
                content="A programme report described peer navigation.",
            )
        )
        experiment.analysis_evidence_ids = [
            first.evidence_id,
            second.evidence_id,
        ]
        self.store.save_experiment(experiment)

        third = self.store.save_evidence(
            create_evidence(
                source_type="research",
                content="A study described limits of peer navigation transfer.",
            )
        )
        expanded = experiment.with_analysis_evidence_ids(
            [first.evidence_id, second.evidence_id, third.evidence_id]
        )
        stored = self.store.save_experiment(expanded)

        self.store.close()
        self.store = SQLitePersistenceStore(self.database_path)
        loaded = self.store.experiments.get(experiment.experiment_id)

        self.assertEqual(
            stored.experiment.analysis_evidence_ids,
            [first.evidence_id, second.evidence_id, third.evidence_id],
        )
        self.assertEqual(
            loaded.experiment.analysis_evidence_ids,
            [first.evidence_id, second.evidence_id, third.evidence_id],
        )
        self.assertEqual(
            [
                self.store.evidence.get(evidence_id).evidence.content
                for evidence_id in loaded.experiment.analysis_evidence_ids
            ],
            [
                "Community members described navigation barriers.",
                "A programme report described peer navigation.",
                "A study described limits of peer navigation transfer.",
            ],
        )
        event_types = [
            event.event_type
            for event in self.store.audit_events.list_events(
                experiment.experiment_id,
                "experiment",
            )
        ]
        self.assertEqual(
            event_types,
            ["experiment_created", "experiment_evidence_linked"],
        )

    def test_existing_experiment_lineage_preserves_its_first_recorded_order(self):
        experiment = self._experiment()
        first = self.store.save_evidence(
            create_evidence(
                source_type="community_feedback",
                content="Community feedback about navigation barriers.",
            )
        )
        second = self.store.save_evidence(
            create_evidence(
                source_type="programme_report",
                content="Programme evidence about navigation support.",
            )
        )
        third = self.store.save_evidence(
            create_evidence(
                source_type="research",
                content="Research evidence about local adaptation.",
            )
        )
        experiment.analysis_evidence_ids = [
            first.evidence_id,
            second.evidence_id,
        ]
        self.store.save_experiment(experiment)

        reordered = experiment.with_analysis_evidence_ids(
            [second.evidence_id, first.evidence_id, third.evidence_id]
        )

        stored = self.store.save_experiment(reordered)

        self.assertEqual(
            stored.experiment.analysis_evidence_ids,
            [first.evidence_id, second.evidence_id, third.evidence_id],
        )
        self.assertEqual(
            self.store.experiments.get(
                experiment.experiment_id
            ).experiment.analysis_evidence_ids,
            [first.evidence_id, second.evidence_id, third.evidence_id],
        )

    def test_conflicting_observations_are_preserved(self):
        experiment = self._experiment()
        self._save_experiment(experiment)
        first = self.store.record_observation(
            self._observation(
                experiment,
                "Participants reported fewer navigation barriers.",
            )
        )
        second = self.store.record_observation(
            self._observation(
                experiment,
                "Participants reported more navigation barriers.",
            )
        )

        observations = self.store.learning.list_observations(experiment.experiment_id)

        self.assertNotEqual(first.observation_id, second.observation_id)
        self.assertEqual(len(observations), 2)
        self.assertEqual(
            {item.observation.outcome for item in observations},
            {
                "Participants reported fewer navigation barriers.",
                "Participants reported more navigation barriers.",
            },
        )

    def test_audit_events_record_state_transitions_without_claiming_approval(self):
        experiment = self._experiment()
        stored_experiment = self._save_experiment(experiment)
        stored_observation = self.store.record_observation(
            self._observation(experiment)
        )
        learning = self.validation_engine.evaluate(
            [stored_observation.observation]
        )[0]
        self.store.save_learning(learning, stored_observation.observation_id)

        events = self.store.audit_events.list_events()
        event_types = [event.event_type for event in events]

        self.assertIn("experiment_created", event_types)
        self.assertIn("observation_recorded", event_types)
        self.assertIn("reviewer_attributed", event_types)
        self.assertIn("learning_generated", event_types)
        self.assertTrue(all(event.timestamp for event in events))
        experiment_event = self.store.audit_events.list_events(
            stored_experiment.experiment_id,
            "experiment",
        )[0]
        self.assertIn("not authorization", experiment_event.description)
        reviewer_event = next(
            event
            for event in events
            if event.event_type == "reviewer_attributed"
        )
        self.assertEqual(
            reviewer_event.metadata["review_status"],
            "attributed_not_verified",
        )
        learning_event = next(
            event
            for event in events
            if event.event_type == "learning_generated"
        )
        self.assertIn("reviewer-attributed", learning_event.description)
        self.assertEqual(
            learning_event.metadata["review_status"],
            "attributed_not_verified",
        )

    def test_records_survive_a_reopened_database_connection(self):
        evidence = create_evidence(
            source_type="programme_report",
            content="Peer support improved reported access.",
        )
        stored_evidence = self.store.save_evidence(evidence)
        experiment = self._experiment()
        self._save_experiment(experiment)
        stored_observation = self.store.record_observation(
            self._observation(experiment)
        )
        learning = self.validation_engine.evaluate(
            [stored_observation.observation]
        )[0]
        stored_learning = self.store.save_learning(
            learning,
            stored_observation.observation_id,
        )

        self.store.close()
        self.store = SQLitePersistenceStore(self.database_path)

        self.assertEqual(
            self.store.evidence.get(stored_evidence.evidence_id).evidence.content,
            evidence.content,
        )
        self.assertEqual(
            self.store.experiments.get(experiment.experiment_id).experiment.title,
            experiment.title,
        )
        self.assertEqual(
            self.store.learning.get_observation(
                stored_observation.observation_id
            ).observation.reviewer,
            "Community programme lead",
        )
        self.assertEqual(
            self.store.learning.get_learning(
                stored_learning.learning_id
            ).learning.confidence,
            "exploratory",
        )


class TestPersistenceIntegration(unittest.TestCase):

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "integration.db"
        self.store = SQLitePersistenceStore(database_path)

    def tearDown(self):
        self.store.close()
        self.temporary_directory.cleanup()

    @staticmethod
    def _evidence():
        return [
            create_evidence(
                source_type="programme_report",
                content="Peer support improved service engagement.",
                date="2025-06-30",
                location="Madurai",
                population="Young people",
            ),
            create_evidence(
                source_type="community_feedback",
                content="Peer support was helpful for accessing services.",
                date="2025-07-15",
                location="Madurai",
                population="Young people",
            ),
        ]

    def test_discovery_optionally_persists_the_full_traceable_workflow(self):
        problem = "Young people face barriers to service access."
        evidence = self._evidence()
        engine = InnovationDiscoveryEngine(storage=self.store)
        initial_report = engine.analyse(problem, evidence=evidence)
        experiment = initial_report.experiment_designs[0]
        observation = ValidationLearningEngine().create_observation(
            experiment_id=experiment.experiment_id,
            experiment_title=experiment.title,
            outcome="Participants reported fewer navigation barriers.",
            evidence_basis=["Pilot feedback"],
            reviewer="Programme and community review group",
        )

        report = engine.analyse(
            problem,
            evidence=evidence,
            validation_observations=[observation],
        )

        self.assertEqual(len(self.store.evidence.list()), 2)
        self.assertEqual(
            len(self.store.experiments.list()),
            len(report.experiment_designs),
        )
        self.assertEqual(len(self.store.learning.list_observations()), 1)
        self.assertEqual(len(self.store.learning.list_learning()), 1)

    def test_in_memory_discovery_remains_available_without_storage(self):
        engine = InnovationDiscoveryEngine()
        report = engine.analyse(
            "Young people face barriers to service access.",
            evidence=self._evidence(),
        )

        self.assertIsNone(engine.storage)
        self.assertTrue(report.experiment_designs)

    def test_discovery_persists_supplied_evidence_provenance(self):
        evidence = self._evidence()
        provenance = [
            EvidenceProvenance(
                entry_method="imported",
                original_source_id="programme-1",
                source_reference="programme-export.json",
                import_format="json",
            ),
            EvidenceProvenance(
                entry_method="imported",
                original_source_id="community-2",
                source_reference="community-export.json",
                import_format="json",
            ),
        ]
        engine = InnovationDiscoveryEngine(storage=self.store)

        engine.analyse(
            "Young people face barriers to service access.",
            evidence=evidence,
            evidence_provenance=provenance,
        )

        stored = self.store.evidence.list()
        self.assertEqual(
            {record.provenance.original_source_id for record in stored},
            {"programme-1", "community-2"},
        )
        self.assertEqual(
            {record.provenance.import_format for record in stored},
            {"json"},
        )

    def test_discovery_persists_duplicate_evidence_without_duplicate_lineage(self):
        evidence = self._evidence()[0]
        engine = InnovationDiscoveryEngine(storage=self.store)

        report = engine.analyse(
            "Young people face barriers to service access.",
            evidence=[evidence, evidence],
        )

        stored_evidence = self.store.evidence.list()
        self.assertEqual(len(stored_evidence), 1)
        self.assertTrue(report.experiment_designs)
        self.assertTrue(
            all(
                design.analysis_evidence_ids == [
                    stored_evidence[0].evidence_id
                ]
                for design in report.experiment_designs
            )
        )

    def test_discovery_uses_stable_lineage_for_reordered_evidence(self):
        evidence = self._evidence()
        engine = InnovationDiscoveryEngine(storage=self.store)

        first_report = engine.analyse(
            "Young people face barriers to service access.",
            evidence=evidence,
        )
        second_report = engine.analyse(
            "Young people face barriers to service access.",
            evidence=list(reversed(evidence)),
        )

        expected_ids = first_report.experiment_designs[0].analysis_evidence_ids
        self.assertTrue(first_report.experiment_designs)
        self.assertTrue(second_report.experiment_designs)
        self.assertTrue(
            all(
                design.analysis_evidence_ids == expected_ids
                for design in first_report.experiment_designs
            )
        )
        self.assertTrue(
            all(
                design.analysis_evidence_ids == expected_ids
                for design in second_report.experiment_designs
            )
        )

    def test_failed_discovery_rolls_back_partial_persistence(self):
        invalid_observation = ValidationObservation(
            experiment_id="experiment-unknown",
            experiment_title="Pilot: Unknown",
            outcome="Participants reported fewer barriers.",
            evidence_basis=["Pilot feedback"],
            limitations=["The pilot was small."],
            reviewer="Community programme lead",
        )
        engine = InnovationDiscoveryEngine(storage=self.store)

        with self.assertRaisesRegex(ValueError, "Unknown experiment_id"):
            engine.analyse(
                "Young people face barriers to service access.",
                evidence=self._evidence(),
                validation_observations=[invalid_observation],
            )

        self.assertEqual(self.store.evidence.list(), [])
        self.assertEqual(self.store.experiments.list(), [])
        self.assertEqual(self.store.learning.list_observations(), [])
        self.assertEqual(self.store.learning.list_learning(), [])
        self.assertEqual(self.store.audit_events.list_events(), [])

    def test_failed_discovery_uses_a_savepoint_inside_an_outer_transaction(self):
        retained_evidence = create_evidence(
            source_type="programme_report",
            content="Evidence that was stored before the failed analysis.",
        )
        invalid_observation = ValidationObservation(
            experiment_id="experiment-unknown",
            experiment_title="Pilot: Unknown",
            outcome="Participants reported fewer barriers.",
            evidence_basis=["Pilot feedback"],
            limitations=["The pilot was small."],
            reviewer="Community programme lead",
        )
        engine = InnovationDiscoveryEngine(storage=self.store)

        with self.store.transaction():
            retained = self.store.save_evidence(retained_evidence)

            with self.assertRaisesRegex(ValueError, "Unknown experiment_id"):
                engine.analyse(
                    "Young people face barriers to service access.",
                    evidence=self._evidence(),
                    validation_observations=[invalid_observation],
                )

            self.assertEqual(
                [record.evidence_id for record in self.store.evidence.list()],
                [retained.evidence_id],
            )
            self.assertEqual(self.store.experiments.list(), [])
            self.assertEqual(self.store.learning.list_observations(), [])

        self.assertEqual(
            [record.evidence_id for record in self.store.evidence.list()],
            [retained.evidence_id],
        )
        self.assertEqual(self.store.experiments.list(), [])


if __name__ == "__main__":
    unittest.main()
