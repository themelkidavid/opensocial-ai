"""Small application-owned registries; deliberately not domain persistence."""
from datetime import datetime, timezone
import uuid
from src.persistence import APIProject

def create_project(name, description=None):
    return APIProject("project-" + uuid.uuid4().hex, name, description, datetime.now(timezone.utc).isoformat())

def create_analysis_id(): return "analysis-" + uuid.uuid4().hex
