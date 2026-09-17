"""Optional FastAPI application factory; core domain modules remain framework-free."""
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse

from src.api.dependencies import create_analysis_id, create_project
from src.api.schemas import AnalysisCreate, BriefCreate, BulkEvidenceCreate, EvidenceCreate, ProjectCreate
from src.brief_rendering import DecisionBriefRenderer
from src.decision_briefs import DecisionBrief, EvidencePack
from src.evidence import create_evidence
from src.innovation_discovery import InnovationDiscoveryEngine
from src.narrative_reasoning import NarrativeReasoningEngine
from src.persistence import EvidenceProvenance, SQLitePersistenceStore

API_PREFIX = "/api/v1"

def _error(code, message, status): return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})

def create_app(store=None, interpretation_provider=None):
    app = FastAPI(title="OpenSocial AI API", version="1.0.0", description="Exploratory evidence analysis only; human review is required and no decision authority is automated.")
    app.state.store = store or SQLitePersistenceStore()
    app.state.projects, app.state.analyses = {}, {}
    app.state.interpretation_provider = interpretation_provider

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError):
        return _error("VALIDATION_ERROR", "Request validation failed", 422)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        return _error("INTERNAL_ERROR", "The request could not be completed", 500)

    def project_or_error(project_id):
        project = app.state.projects.get(project_id)
        if not project: return None
        return project

    def scoped_evidence(project_id):
        return [item for item in app.state.store.evidence.list() if item.evidence.metadata.get("_api_project_id") == project_id]

    @app.get(API_PREFIX + "/health", summary="Service health")
    def health(): return {"status": "ok", "service": "opensocial-ai", "api_version": "v1"}

    @app.post(API_PREFIX + "/projects", status_code=201, summary="Create an analysis workspace")
    def create_project_endpoint(payload: ProjectCreate):
        project = create_project(payload.name.strip(), payload.description)
        app.state.projects[project.project_id] = project
        return project.to_dict()

    @app.get(API_PREFIX + "/projects", summary="List current-process workspaces")
    def list_projects(): return [item.to_dict() for item in sorted(app.state.projects.values(), key=lambda x: (x.created_at, x.project_id))]

    @app.get(API_PREFIX + "/projects/{project_id}", summary="Get a workspace")
    def get_project(project_id: str):
        project = project_or_error(project_id)
        return project.to_dict() if project else _error("PROJECT_NOT_FOUND", "Project not found", 404)

    def save_evidence(project_id, payload):
        project = project_or_error(project_id)
        if not project: return _error("PROJECT_NOT_FOUND", "Project not found", 404)
        metadata = dict(payload.metadata); metadata["_api_project_id"] = project_id
        try:
            item = create_evidence(payload.source_type, payload.content, payload.date, payload.location, payload.population, metadata)
            stored = app.state.store.save_evidence(item, EvidenceProvenance(entry_method="manual"))
        except (TypeError, ValueError): return _error("VALIDATION_ERROR", "Evidence validation failed", 422)
        return {"evidence_id": stored.evidence_id, "project_id": project_id, "validation_status": "accepted"}

    @app.post(API_PREFIX + "/projects/{project_id}/evidence", status_code=201, summary="Add structured evidence")
    def add_evidence(project_id: str, payload: EvidenceCreate): return save_evidence(project_id, payload)

    @app.post(API_PREFIX + "/projects/{project_id}/evidence/bulk", status_code=201, summary="Atomically validate and add up to fifty evidence records")
    def add_bulk_evidence(project_id: str, payload: BulkEvidenceCreate):
        if not project_or_error(project_id): return _error("PROJECT_NOT_FOUND", "Project not found", 404)
        try:
            items = [create_evidence(x.source_type, x.content, x.date, x.location, x.population, {**x.metadata, "_api_project_id": project_id}) for x in payload.records]
        except (TypeError, ValueError): return _error("VALIDATION_ERROR", "Evidence validation failed; no records were stored", 422)
        with app.state.store.transaction():
            stored = [app.state.store.save_evidence(item, EvidenceProvenance(entry_method="manual")) for item in items]
        return {"project_id": project_id, "evidence": [{"evidence_id": x.evidence_id, "validation_status": "accepted"} for x in stored]}

    @app.get(API_PREFIX + "/projects/{project_id}/evidence", summary="List workspace evidence")
    def list_evidence(project_id: str):
        if not project_or_error(project_id): return _error("PROJECT_NOT_FOUND", "Project not found", 404)
        return [{"evidence_id": x.evidence_id, "project_id": project_id,
                 "evidence": {**x.evidence.to_dict(), "metadata": {k: v for k, v in x.evidence.metadata.items() if k != "_api_project_id"},
                              "provenance": x.provenance.to_dict()}}
                for x in scoped_evidence(project_id)]

    @app.get(API_PREFIX + "/projects/{project_id}/evidence/{evidence_id}", summary="Get workspace evidence")
    def get_evidence(project_id: str, evidence_id: str):
        if not project_or_error(project_id): return _error("PROJECT_NOT_FOUND", "Project not found", 404)
        item = next((x for x in scoped_evidence(project_id) if x.evidence_id == evidence_id), None)
        if not item: return _error("EVIDENCE_NOT_FOUND", "Evidence not found", 404)
        return {"evidence_id": item.evidence_id, "project_id": project_id,
                "evidence": {**item.evidence.to_dict(), "metadata": {k: v for k, v in item.evidence.metadata.items() if k != "_api_project_id"}},
                "provenance": item.provenance.to_dict()}

    def analyse(project_id, payload):
        if not project_or_error(project_id): return _error("PROJECT_NOT_FOUND", "Project not found", 404)
        records = scoped_evidence(project_id)
        if not records: return _error("VALIDATION_ERROR", "At least one evidence record is required", 422)
        if payload.interpretation_mode == "assisted" and app.state.interpretation_provider is None:
            return _error("INTERPRETATION_UNAVAILABLE", "Assisted interpretation is not configured", 503)
        evidence = [x.evidence for x in records]; provenance = [x.provenance for x in records]
        try: report = InnovationDiscoveryEngine(storage=app.state.store).analyse(payload.problem, evidence, evidence_provenance=provenance)
        except (TypeError, ValueError): return _error("ANALYSIS_FAILED", "Analysis could not be completed", 422)
        narrative = None
        if payload.include_narrative or payload.interpretation_mode == "assisted":
            narrative = NarrativeReasoningEngine(interpretation_provider=app.state.interpretation_provider if payload.interpretation_mode == "assisted" else None).analyse(evidence, [x.evidence_id for x in records], provenance)
        analysis_id = create_analysis_id(); result = {"analysis_id": analysis_id, "project_id": project_id, "created_at": datetime.now(timezone.utc).isoformat(), "report": report.to_dict(), "evidence_ids": [x.evidence_id for x in records], "narrative_analysis": narrative.to_dict() if narrative else None, "responsible_ai": "Exploratory analysis only; no recommendation, authorization, effectiveness, or governance decision is created."}
        app.state.analyses[analysis_id] = result
        return result

    @app.post(API_PREFIX + "/projects/{project_id}/analysis", summary="Run exploratory evidence analysis; does not create governance actions")
    def run_analysis(project_id: str, payload: AnalysisCreate): return analyse(project_id, payload)

    @app.post(API_PREFIX + "/projects/{project_id}/narrative-analysis", summary="Run local deterministic narrative analysis")
    def narrative_analysis(project_id: str, payload: AnalysisCreate):
        payload.include_narrative = True; payload.interpretation_mode = "deterministic"; return analyse(project_id, payload)

    @app.get(API_PREFIX + "/projects/{project_id}/analysis/{analysis_id}", summary="Get a current-process analysis snapshot")
    def get_analysis(project_id: str, analysis_id: str):
        result = app.state.analyses.get(analysis_id)
        if not project_or_error(project_id): return _error("PROJECT_NOT_FOUND", "Project not found", 404)
        if not result or result["project_id"] != project_id: return _error("ANALYSIS_NOT_FOUND", "Analysis not found", 404)
        return result

    @app.post(API_PREFIX + "/projects/{project_id}/briefs", status_code=201, summary="Build an immutable exploratory brief from an explicit analysis snapshot")
    def create_brief(project_id: str, payload: BriefCreate):
        analysis = app.state.analyses.get(payload.analysis_id)
        if not project_or_error(project_id): return _error("PROJECT_NOT_FOUND", "Project not found", 404)
        if not analysis or analysis["project_id"] != project_id: return _error("ANALYSIS_NOT_FOUND", "Analysis not found", 404)
        report = analysis["report"]
        pack = EvidencePack(payload.title + " evidence", "analysis", payload.analysis_id, evidence_records=[{"evidence_id": x} for x in analysis["evidence_ids"]], evidence_quality_summary=report.get("evidence_quality", []), evidence_gaps=report.get("evidence_gap_details", []), conflicts=report.get("evidence_conflicts", []), patterns=report.get("observed_patterns", []), insights=report.get("insights", []), provenance="api", known_limitations=["API brief is an exploratory snapshot; governance content is not invented."]).finalized()
        pack = app.state.store.save_evidence_pack(pack)
        brief = DecisionBrief(payload.title, "analysis", payload.analysis_id, payload.purpose, report.get("problem"), evidence_pack_id=pack.pack_id, key_uncertainties=report.get("evidence_gaps", []), provenance="api").finalized()
        brief = app.state.store.save_decision_brief(brief)
        return {"brief_id": brief.brief_id, "version": brief.brief_version, "brief": brief.to_dict()}

    def brief_or_error(project_id, brief_id):
        if not project_or_error(project_id): return None, _error("PROJECT_NOT_FOUND", "Project not found", 404)
        brief = app.state.store.get_decision_brief(brief_id)
        analysis = app.state.analyses.get(getattr(brief, "subject_id", None)) if brief else None
        if not brief or brief.provenance != "api" or not analysis or analysis["project_id"] != project_id:
            return None, _error("BRIEF_NOT_FOUND", "Brief not found", 404)
        return brief, None
    @app.get(API_PREFIX + "/projects/{project_id}/briefs/{brief_id}", summary="Get an immutable decision-support brief")
    def get_brief(project_id: str, brief_id: str):
        brief, error = brief_or_error(project_id, brief_id); return error or brief.to_dict()
    @app.get(API_PREFIX + "/projects/{project_id}/briefs/{brief_id}/markdown", response_class=PlainTextResponse, summary="Render a brief as Markdown")
    def brief_markdown(project_id: str, brief_id: str):
        brief, error = brief_or_error(project_id, brief_id); return error or DecisionBriefRenderer().render_markdown(brief)
    @app.get(API_PREFIX + "/projects/{project_id}/briefs/{brief_id}/html", response_class=HTMLResponse, summary="Render a brief as HTML")
    def brief_html(project_id: str, brief_id: str):
        brief, error = brief_or_error(project_id, brief_id); return error or DecisionBriefRenderer().render_html(brief)
    return app

app = create_app()
