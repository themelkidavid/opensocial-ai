import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.persistence import SQLitePersistenceStore


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.store = SQLitePersistenceStore()
        self.client = TestClient(create_app(store=self.store))

    def tearDown(self): self.store.close()

    def project(self):
        response = self.client.post("/api/v1/projects", json={"name": "Fictional project", "description": "Test only"})
        self.assertEqual(response.status_code, 201)
        return response.json()["project_id"]

    def evidence(self, project, content="Members reported that peer meetings improved coordination."):
        return self.client.post(f"/api/v1/projects/{project}/evidence", json={"source_type": "fictional_report", "content": content, "location": "North", "population": "members", "metadata": {"fictional": "true"}})

    def test_health_projects_and_safe_missing_project_error(self):
        self.assertEqual(self.client.get("/api/v1/health").json(), {"status": "ok", "service": "opensocial-ai", "api_version": "v1"})
        self.assertIn("/api/v1/projects", self.client.get("/openapi.json").json()["paths"])
        project = self.project()
        self.assertEqual(self.client.get("/api/v1/projects").json()[0]["project_id"], project)
        missing = self.client.get("/api/v1/projects/missing")
        self.assertEqual((missing.status_code, missing.json()["error"]["code"]), (404, "PROJECT_NOT_FOUND"))
        self.assertNotIn("traceback", missing.text.lower())

    def test_evidence_single_bulk_list_and_invalid_batch(self):
        project = self.project(); saved = self.evidence(project)
        self.assertEqual(saved.status_code, 201)
        evidence_id = saved.json()["evidence_id"]
        listed = self.client.get(f"/api/v1/projects/{project}/evidence").json()
        self.assertEqual(listed[0]["evidence_id"], evidence_id)
        self.assertNotIn("_api_project_id", str(listed))
        bulk = self.client.post(f"/api/v1/projects/{project}/evidence/bulk", json={"records": [
            {"source_type": "fictional", "content": "Access increased."}, {"source_type": "fictional", "content": "Access decreased."}]})
        self.assertEqual(bulk.status_code, 201)
        invalid = self.client.post(f"/api/v1/projects/{project}/evidence/bulk", json={"records": [{"source_type": "", "content": "bad"}]})
        self.assertEqual((invalid.status_code, invalid.json()["error"]["code"]), (422, "VALIDATION_ERROR"))

    def test_analysis_retrieval_narrative_and_assisted_unavailable(self):
        project = self.project(); self.evidence(project)
        analysis = self.client.post(f"/api/v1/projects/{project}/analysis", json={"problem": "Investigate coordination", "include_narrative": True})
        self.assertEqual(analysis.status_code, 200)
        payload = analysis.json(); self.assertTrue(payload["report"]["evidence_gaps"]); self.assertIsNotNone(payload["narrative_analysis"])
        self.assertEqual(self.client.get(f"/api/v1/projects/{project}/analysis/{payload['analysis_id']}").status_code, 200)
        unavailable = self.client.post(f"/api/v1/projects/{project}/analysis", json={"problem": "Investigate coordination", "interpretation_mode": "assisted"})
        self.assertEqual((unavailable.status_code, unavailable.json()["error"]["code"]), (503, "INTERPRETATION_UNAVAILABLE"))
        self.assertEqual(self.store.governance.list_decisions("strategic_scenario", "anything"), [])

    def test_brief_and_safe_rendering_endpoints(self):
        project = self.project(); self.evidence(project)
        analysis = self.client.post(f"/api/v1/projects/{project}/analysis", json={"problem": "Investigate coordination"}).json()
        created = self.client.post(f"/api/v1/projects/{project}/briefs", json={"analysis_id": analysis["analysis_id"]})
        self.assertEqual(created.status_code, 201)
        brief_id = created.json()["brief_id"]
        self.assertEqual(self.client.get(f"/api/v1/projects/{project}/briefs/{brief_id}").status_code, 200)
        self.assertIn("Exploratory", self.client.get(f"/api/v1/projects/{project}/briefs/{brief_id}/markdown").text)
        self.assertIn("html", self.client.get(f"/api/v1/projects/{project}/briefs/{brief_id}/html").text.lower())

    def test_core_does_not_need_fastapi_imports(self):
        from src.innovation_discovery import InnovationDiscoveryEngine
        self.assertTrue(InnovationDiscoveryEngine().analyse("Investigate access").reframed_problem)

    def test_workspace_survives_reopen_and_preserves_brief_relationships(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "workspace.sqlite3"
            first_store = SQLitePersistenceStore(database)
            first_client = TestClient(create_app(store=first_store))
            project = first_client.post("/api/v1/projects", json={"name": "Durable workspace"}).json()["project_id"]
            evidence = first_client.post(f"/api/v1/projects/{project}/evidence", json={"source_type": "fictional", "content": "Members report coordination barriers.", "location": "North", "population": "members"}).json()["evidence_id"]
            analysis = first_client.post(f"/api/v1/projects/{project}/analysis", json={"problem": "Investigate coordination"}).json()
            brief = first_client.post(f"/api/v1/projects/{project}/briefs", json={"analysis_id": analysis["analysis_id"]}).json()["brief_id"]
            first_store.close()

            second_store = SQLitePersistenceStore(database)
            second_client = TestClient(create_app(store=second_store))
            self.assertEqual(second_client.get(f"/api/v1/projects/{project}").json()["name"], "Durable workspace")
            self.assertEqual(second_client.get(f"/api/v1/projects/{project}/evidence").json()[0]["evidence_id"], evidence)
            self.assertEqual(second_client.get(f"/api/v1/projects/{project}/analyses").json()[0]["analysis_id"], analysis["analysis_id"])
            restored = second_client.get(f"/api/v1/projects/{project}/analysis/{analysis['analysis_id']}").json()
            self.assertEqual(restored["evidence_ids"], [evidence])
            self.assertEqual(second_client.get(f"/api/v1/projects/{project}/briefs/{brief}").status_code, 200)
            events = second_store.audit_events.list_events(entity_id=project)
            self.assertIn("project_created", [event.event_type for event in events])
            self.assertIn("project_evidence_linked", [event.event_type for event in events])
            self.assertIn("analysis_created", [event.event_type for event in second_store.audit_events.list_events(entity_id=analysis["analysis_id"])])
            second_store.close()

    def test_project_boundaries_and_configured_database_path(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "nested" / "api.sqlite3"
            with patch.dict("os.environ", {"OPENSOCIAL_DATABASE_PATH": str(database)}):
                app = create_app()
                with TestClient(app) as client:
                    project_a = client.post("/api/v1/projects", json={"name": "A"}).json()["project_id"]
                    project_b = client.post("/api/v1/projects", json={"name": "B"}).json()["project_id"]
                    evidence = client.post(f"/api/v1/projects/{project_a}/evidence", json={"source_type": "fictional", "content": "A only"}).json()["evidence_id"]
                    analysis = client.post(f"/api/v1/projects/{project_a}/analysis", json={"problem": "Investigate A"}).json()["analysis_id"]
                    brief = client.post(f"/api/v1/projects/{project_a}/briefs", json={"analysis_id": analysis}).json()["brief_id"]
                    self.assertEqual(client.get(f"/api/v1/projects/{project_b}/evidence").json(), [])
                    self.assertEqual(client.get(f"/api/v1/projects/{project_b}/analysis/{analysis}").status_code, 404)
                    self.assertEqual(client.get(f"/api/v1/projects/{project_b}/briefs/{brief}").status_code, 404)
                    self.assertEqual(client.get(f"/api/v1/projects/{project_a}/evidence/{evidence}").status_code, 200)
            self.assertTrue(database.exists())


if __name__ == "__main__": unittest.main()
