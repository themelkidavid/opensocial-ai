"""Conservative public request/response schemas for API v1."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=1000)

class EvidenceCreate(BaseModel):
    source_type: str = Field(..., min_length=1, max_length=80)
    content: str = Field(..., min_length=1, max_length=12000)
    date: Optional[str] = Field(None, max_length=80)
    location: Optional[str] = Field(None, max_length=160)
    population: Optional[str] = Field(None, max_length=160)
    metadata: Dict[str, str] = Field(default_factory=dict)
    @validator("metadata")
    def safe_metadata(cls, value):
        if len(value) > 20 or any(len(k) > 80 or len(v) > 400 for k, v in value.items()):
            raise ValueError("metadata is too large")
        return value

class BulkEvidenceCreate(BaseModel):
    records: List[EvidenceCreate] = Field(..., min_items=1, max_items=50)

class AnalysisCreate(BaseModel):
    problem: str = Field(..., min_length=1, max_length=4000)
    include_narrative: bool = False
    interpretation_mode: str = "deterministic"
    @validator("interpretation_mode")
    def mode(cls, value):
        if value not in {"deterministic", "assisted"}: raise ValueError("unsupported interpretation mode")
        return value

class BriefCreate(BaseModel):
    analysis_id: str = Field(..., min_length=1, max_length=120)
    title: str = Field("Exploratory analysis brief", min_length=1, max_length=160)
    purpose: str = Field("Present an exploratory evidence snapshot for human review; not a decision or recommendation.", min_length=1, max_length=500)

class APIErrorBody(BaseModel): code: str; message: str
class APIError(BaseModel): error: APIErrorBody
