"""Small application-owned registries; deliberately not domain persistence."""
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid
from typing import Optional

@dataclass
class Project:
    project_id: str; name: str; description: Optional[str]; created_at: str
    def to_dict(self): return self.__dict__.copy()

def create_project(name, description=None):
    return Project("project-" + uuid.uuid4().hex, name, description, datetime.now(timezone.utc).isoformat())

def create_analysis_id(): return "analysis-" + uuid.uuid4().hex
