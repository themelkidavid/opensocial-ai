export interface Project { project_id: string; name: string; description?: string | null; created_at: string; }
export interface EvidenceInput { source_type: string; content: string; date?: string; location?: string; population?: string; metadata?: Record<string, string>; }
export interface EvidenceRecord { evidence_id: string; project_id: string; evidence: EvidenceInput & { evidence_id?: string }; provenance: Record<string, unknown>; }
export interface Analysis { analysis_id: string; project_id: string; created_at: string; report: Record<string, unknown>; evidence_ids: string[]; narrative_analysis?: Record<string, unknown> | null; responsible_ai: string; }
export interface AnalysisSummary { analysis_id: string; project_id: string; created_at: string; problem: string; evidence_count: number; interpretation_mode: string; }
export interface Brief { brief_id: string; brief_version: number; title: string; subject_id: string; [key: string]: unknown; }
export interface ApiError { code: string; message: string; }
