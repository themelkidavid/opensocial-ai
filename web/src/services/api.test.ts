import { describe, expect, it, vi } from "vitest";
import { ApiClient, errorMessage } from "./api";

function json(body: unknown, ok = true) { return Promise.resolve({ ok, json: () => Promise.resolve(body) } as Response); }
describe("typed API client", () => {
  it("submits structured evidence to the project endpoint", async () => {
    globalThis.fetch = vi.fn(() => json({ evidence_id: "e1" })) as unknown as typeof fetch;
    await new ApiClient().addEvidence("p1", { source_type: "report", content: "A source-stated observation" });
    expect(fetch).toHaveBeenCalledWith("/api/v1/projects/p1/evidence", expect.objectContaining({ method: "POST" }));
  });
  it("submits deterministic analysis and retains the structured response", async () => {
    globalThis.fetch = vi.fn(() => json({ analysis_id: "a1", project_id: "p1", created_at: "now", report: {}, evidence_ids: ["e1"], responsible_ai: "Exploratory" })) as unknown as typeof fetch;
    const analysis = await new ApiClient().runAnalysis("p1", "What needs investigation?", true);
    expect(analysis.analysis_id).toBe("a1");
    expect(fetch).toHaveBeenCalledWith("/api/v1/projects/p1/analysis", expect.objectContaining({ method: "POST", body: expect.stringContaining('"interpretation_mode":"deterministic"') }));
  });
  it("maps stable API errors to safe user messages", () => {
    expect(errorMessage({ code: "PROJECT_NOT_FOUND" })).toMatch(/unavailable/i);
    expect(errorMessage({ code: "INTERNAL_ERROR" })).not.toMatch(/stack/i);
  });
});
