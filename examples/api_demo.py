"""Local, fictional API v1 demo; requires requirements-web.txt, no network."""
from fastapi.testclient import TestClient
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.api.app import create_app


def main():
    client = TestClient(create_app())
    project = client.post("/api/v1/projects", json={"name": "Fictional API demo"}).json()
    project_id = project["project_id"]
    client.post(f"/api/v1/projects/{project_id}/evidence", json={
        "source_type": "fictional_report", "content": "FICTIONAL: Members reported that peer meetings improved coordination.",
        "location": "Fictional region", "population": "fictional members"})
    analysis = client.post(f"/api/v1/projects/{project_id}/analysis", json={"problem": "Explore coordination barriers"}).json()
    retrieved = client.get(f"/api/v1/projects/{project_id}/analysis/{analysis['analysis_id']}").json()
    brief = client.post(f"/api/v1/projects/{project_id}/briefs", json={"analysis_id": analysis["analysis_id"]}).json()
    print({"project_id": project_id, "analysis_id": retrieved["analysis_id"], "brief_id": brief["brief_id"]})


if __name__ == "__main__":
    main()
