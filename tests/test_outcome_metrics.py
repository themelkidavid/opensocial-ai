import tempfile
import unittest
from pathlib import Path

from src.evidence import create_evidence
from src.experiment_design import ExperimentDesignEngine
from src.historical_memory import HistoricalProgramme, MechanismRecord
from src.innovation_reasoning import InnovationHypothesis
from src.outcome_metrics import (
    ComparativeLearningEngine,
    OutcomeMetric,
    OutcomeObservation,
)
from src.persistence import SQLitePersistenceStore
from src.validation_learning import ValidationLearningEngine


class TestOutcomeMetrics(unittest.TestCase):
    def metric(self):
        return OutcomeMetric("Completion rate", "Share completing a service", "percentage", "%",
                             "Review completed records", baseline_value=40, limitations=["Small pilot"])

    def experiment(self, store):
        hypothesis = InnovationHypothesis("Peer support", "access", "source", "mechanism", "adapt",
            "may help", ["evidence"], "exploratory", ["uncertain"], "pilot", "question")
        design = ExperimentDesignEngine().design([hypothesis])[0]
        evidence = store.save_evidence(create_evidence("report", "Evidence"))
        design = design.with_analysis_evidence_ids([evidence.evidence_id]).with_outcome_metrics([self.metric()])
        store.save_experiment(design)
        return design

    def observation(self, experiment, metric, value=55, **kwargs):
        values = {"population": "adults", "measurement_period": "30 days",
                  "measurement_method": "Review completed records", "limitations": ["Small pilot"],
                  "provenance": "manual"}
        values.update(kwargs)
        return OutcomeObservation(experiment.experiment_id, metric.metric_id, value,
            "Pilot register", "reviewer", **values)

    def test_metric_validation_serialization_and_design_link(self):
        metric = self.metric().validated()
        self.assertTrue(metric.metric_id.startswith("metric-"))
        self.assertEqual(metric.to_dict()["baseline_value"], 40)
        with self.assertRaisesRegex(ValueError, "between 0 and 100"):
            OutcomeMetric("x", "x", "percentage", "%", "method", baseline_value=101).validated()

    def test_metric_types_round_trip_and_unknown_optional_values(self):
        values = {
            "count": 1, "percentage": 1, "rate": 1, "duration": 1,
            "score": -1, "boolean": True, "categorical": "reported",
        }
        for metric_type, value in values.items():
            metric = OutcomeMetric("Metric", "Description", metric_type, "unit", "method",
                                   baseline_value=value).validated()
            self.assertEqual(OutcomeMetric(**metric.to_dict()).validated().to_dict(), metric.to_dict())
        unknown = OutcomeMetric("Metric", "Description", "count", "people", "method").validated()
        self.assertIsNone(unknown.baseline_value)
        self.assertIsNone(unknown.target_value)
        self.assertIsNone(unknown.source)
        with self.assertRaisesRegex(ValueError, "unsupported"):
            OutcomeMetric("Metric", "Description", "ratio", "unit", "method").validated()

    def test_persistence_reopen_and_outcome_reference_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "outcomes.sqlite"
            store = SQLitePersistenceStore(path)
            experiment = self.experiment(store)
            metric = experiment.outcome_metrics[0]
            outcome = store.record_outcome_observation(self.observation(experiment, metric))
            self.assertEqual(outcome.metric_id, metric.metric_id)
            with self.assertRaisesRegex(ValueError, "Unknown experiment"):
                store.record_outcome_observation(OutcomeObservation("unknown", metric.metric_id, 50, "e", "r"))
            with self.assertRaisesRegex(ValueError, "Unknown metric"):
                store.record_outcome_observation(OutcomeObservation(experiment.experiment_id, "unknown", 50, "e", "r"))
            store.close()
            reopened = SQLitePersistenceStore(path)
            self.assertEqual(reopened.outcomes.list_metrics(experiment.experiment_id)[0].metric_id, metric.metric_id)
            self.assertEqual(reopened.outcomes.list_observations(experiment.experiment_id)[0].provenance, "manual")
            reopened.close()

    def test_observation_rejects_unlinked_metric_and_malformed_values(self):
        store = SQLitePersistenceStore()
        experiment = self.experiment(store)
        metric = experiment.outcome_metrics[0]
        second_metric = OutcomeMetric("Wait time", "Time waiting", "duration", "days", "records").validated()
        other_hypothesis = InnovationHypothesis("Different", "access", "source", "mechanism", "adapt",
            "may help", ["evidence"], "exploratory", ["uncertain"], "pilot", "question")
        other = ExperimentDesignEngine().design([other_hypothesis])[0]
        evidence = store.save_evidence(create_evidence("report", "Other evidence"))
        store.save_experiment(other.with_analysis_evidence_ids([evidence.evidence_id]))
        store.attach_outcome_metric(other.experiment_id, second_metric)
        with self.assertRaisesRegex(ValueError, "not attached"):
            store.record_outcome_observation(self.observation(experiment, second_metric, 2))
        with self.assertRaisesRegex(ValueError, "number"):
            store.record_outcome_observation(self.observation(experiment, metric, "fifty"))
        with self.assertRaisesRegex(ValueError, "between 0 and 100"):
            store.record_outcome_observation(self.observation(experiment, metric, 101))
        accepted = store.record_outcome_observation(self.observation(experiment, metric, 50))
        self.assertEqual(accepted.reviewer, "reviewer")
        self.assertEqual(accepted.provenance, "manual")
        store.close()

    def test_comparison_changes_warnings_and_non_causal_language(self):
        metric = self.metric().validated()
        a = OutcomeObservation("a", metric.metric_id, 55, "e", "r", population="adults", measurement_period="30 days", measurement_method="records", limitations=[])
        b = OutcomeObservation("b", metric.metric_id, 45, "e", "r", population="young people", measurement_period="60 days", measurement_method="survey", limitations=[])
        engine = ComparativeLearningEngine()
        comparison = engine.compare(metric, a, b)
        self.assertEqual(comparison.absolute_difference, 10)
        self.assertAlmostEqual(comparison.relative_difference, 10 / 45)
        self.assertIn("Different populations were measured.", comparison.warnings)
        self.assertIn("does not establish causality", " ".join(comparison.uncertainty))
        self.assertEqual(engine.change_from_baseline(metric, a)["absolute_change"], 15)
        learning = ValidationLearningEngine().evaluate_outcome(a, metric, "Pilot A")
        self.assertIn("recorded", learning.observed_outcome)
        self.assertIn("does not establish", " ".join(learning.limitations))
        zero = OutcomeMetric("x", "x", "count", "people", "records", baseline_value=0).validated()
        self.assertIsNone(engine.change_from_baseline(zero, OutcomeObservation("a", zero.metric_id, 2, "e", "r", limitations=[]))["percentage_change"])
        missing = OutcomeMetric("x", "x", "score", "points", "records").validated()
        self.assertEqual(engine.change_from_baseline(missing, OutcomeObservation("a", missing.metric_id, -2, "e", "r", limitations=[])), {"absolute_change": None, "percentage_change": None})

    def test_comparison_rejects_a_different_metric_or_unit(self):
        metric = self.metric().validated()
        incompatible = OutcomeMetric("Waiting time", "Time", "duration", "days", "records").validated()
        a = OutcomeObservation("a", metric.metric_id, 55, "e", "r", limitations=[])
        b = OutcomeObservation("b", incompatible.metric_id, 2, "e", "r", limitations=[])
        with self.assertRaisesRegex(ValueError, "metric_id"):
            ComparativeLearningEngine().compare(metric, a, b)

    def test_persistence_comparison_audits_and_historical_metric_fields(self):
        store = SQLitePersistenceStore()
        experiment = self.experiment(store); metric = experiment.outcome_metrics[0]
        a = store.record_outcome_observation(self.observation(experiment, metric, 55))
        b = store.record_outcome_observation(self.observation(experiment, metric, 45, population="other"))
        comparison = store.compare_outcomes(a, b)
        self.assertIn("does not establish", " ".join(comparison.uncertainty))
        events = [event.event_type for event in store.audit_events.list_events()]
        for event in ("outcome_metric_created", "metric_attached_to_experiment", "outcome_observation_recorded", "outcome_observation_reviewed", "experiment_comparison_generated", "comparative_learning_generated"):
            self.assertIn(event, events)
        programme = HistoricalProgramme("P", "problem", "mechanism", outcome_metrics=[metric.to_dict()])
        mechanism = MechanismRecord("M", "mechanism", outcome_metrics=[metric.to_dict()])
        self.assertEqual(programme.to_dict()["outcome_metrics"][0]["metric_id"], metric.metric_id)
        self.assertEqual(mechanism.to_dict()["outcome_metrics"][0]["metric_id"], metric.metric_id)
        store.close()


if __name__ == "__main__":
    unittest.main()
