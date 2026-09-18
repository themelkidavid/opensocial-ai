import type { Analysis, ApiError, Brief, EvidenceInput, EvidenceRecord, Project } from "../types/api";

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export class ApiClient {
  async request<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${baseUrl}${path}`, { headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) }, ...options });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const error = body.error ?? { code: "INTERNAL_ERROR", message: "The request could not be completed." };
      throw error as ApiError;
    }
    return response.json() as Promise<T>;
  }
  listProjects() { return this.request<Project[]>("/projects"); }
  createProject(name: string, description?: string) { return this.request<Project>("/projects", { method: "POST", body: JSON.stringify({ name, description: description || null }) }); }
  getProject(id: string) { return this.request<Project>(`/projects/${id}`); }
  listEvidence(id: string) { return this.request<EvidenceRecord[]>(`/projects/${id}/evidence`); }
  addEvidence(id: string, evidence: EvidenceInput) { return this.request<{ evidence_id: string }>(`/projects/${id}/evidence`, { method: "POST", body: JSON.stringify(evidence) }); }
  addBulkEvidence(id: string, records: EvidenceInput[]) { return this.request<{ evidence: { evidence_id: string }[] }>(`/projects/${id}/evidence/bulk`, { method: "POST", body: JSON.stringify({ records }) }); }
  runAnalysis(id: string, problem: string, includeNarrative: boolean) { return this.request<Analysis>(`/projects/${id}/analysis`, { method: "POST", body: JSON.stringify({ problem, include_narrative: includeNarrative, interpretation_mode: "deterministic" }) }); }
  createBrief(id: string, analysisId: string, title: string) { return this.request<{ brief_id: string; version: number; brief: Brief }>(`/projects/${id}/briefs`, { method: "POST", body: JSON.stringify({ analysis_id: analysisId, title }) }); }
  getBrief(id: string, briefId: string) { return this.request<Brief>(`/projects/${id}/briefs/${briefId}`); }
  getBriefMarkdown(id: string, briefId: string) { return fetch(`${baseUrl}/projects/${id}/briefs/${briefId}/markdown`).then((r) => r.text()); }
  getBriefHtml(id: string, briefId: string) { return fetch(`${baseUrl}/projects/${id}/briefs/${briefId}/html`).then((r) => r.text()); }
}
export const api = new ApiClient();

export function errorMessage(error: unknown) {
  const apiError = error as ApiError;
  const messages: Record<string, string> = {
    PROJECT_NOT_FOUND: "This project is unavailable.", EVIDENCE_NOT_FOUND: "This evidence record is unavailable.",
    VALIDATION_ERROR: "Please check the supplied information and try again.", ANALYSIS_FAILED: "The analysis could not be completed.",
    INTERPRETATION_UNAVAILABLE: "Assisted interpretation is not configured.", INTERNAL_ERROR: "The service could not complete this request."
  };
  return messages[apiError?.code] ?? apiError?.message ?? "The request could not be completed.";
}
