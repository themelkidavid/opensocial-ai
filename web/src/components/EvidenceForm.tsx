import { useState } from "react";
import type { EvidenceInput } from "../types/api";
import { Notice } from "./UI";

const blank: EvidenceInput = { source_type: "", content: "", date: "", location: "", population: "", metadata: {} };
export function EvidenceForm({ onSubmit }: { onSubmit: (value: EvidenceInput) => Promise<void> }) {
  const [value, setValue] = useState<EvidenceInput>(blank); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  async function submit(event: React.FormEvent) { event.preventDefault(); setBusy(true); setError(""); try { await onSubmit(value); setValue(blank); } catch (e) { setError(e instanceof Error ? e.message : "Evidence could not be saved."); } finally { setBusy(false); } }
  const field = (name: keyof EvidenceInput, label: string, required = false) => <label>{label}<input required={required} value={(value[name] as string) ?? ""} onChange={(e) => setValue({ ...value, [name]: e.target.value })} /></label>;
  return <form onSubmit={submit} className="form"><h2>Add evidence</h2>{error && <Notice kind="error">{error}</Notice>}{field("source_type", "Source type", true)}<label>Evidence content<textarea required value={value.content} onChange={(e) => setValue({ ...value, content: e.target.value })} /></label><div className="form-grid">{field("date", "Date")}{field("location", "Location")}{field("population", "Population")}</div><details><summary>Advanced metadata</summary><label>Metadata (JSON object)<textarea placeholder='{"collection_method":"interview"}' onChange={(e) => { try { setValue({ ...value, metadata: e.target.value ? JSON.parse(e.target.value) : {} }); setError(""); } catch { setError("Metadata must be a JSON object."); } }} /></label></details><button disabled={busy}>{busy ? "Saving…" : "Add evidence"}</button></form>;
}

export function BulkEvidence({ onSubmit }: { onSubmit: (records: EvidenceInput[]) => Promise<void> }) {
  const [raw, setRaw] = useState(""); const [message, setMessage] = useState("");
  async function submit() { try { const parsed = JSON.parse(raw); const records = Array.isArray(parsed) ? parsed : parsed.records; if (!Array.isArray(records)) throw new Error("Provide a JSON array of evidence records."); await onSubmit(records); setMessage(`${records.length} evidence records submitted.`); } catch (e) { setMessage(e instanceof Error ? e.message : "Invalid JSON."); } }
  return <details className="bulk"><summary>Bulk import JSON</summary><p>Paste a JSON array or select a local JSON file. Documents are not uploaded.</p><input aria-label="Select JSON evidence file" type="file" accept="application/json" onChange={(e) => e.target.files?.[0]?.text().then(setRaw)} /><textarea aria-label="Bulk evidence JSON" value={raw} onChange={(e) => setRaw(e.target.value)} placeholder='[{"source_type":"report","content":"…"}]' /><button type="button" onClick={submit}>Validate and import</button>{message && <Notice kind={message.includes("submitted") ? "success" : "error"}>{message}</Notice>}</details>;
}
