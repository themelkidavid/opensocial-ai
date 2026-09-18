import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AnalysisView } from "./AnalysisView";

describe("AnalysisView", () => {
  it("renders structured exploratory analysis results rather than a score", () => {
    render(<AnalysisView analysis={{ analysis_id: "a1", project_id: "p1", created_at: "now", evidence_ids: ["e1"], responsible_ai: "Exploratory analysis only", report: { problem: "Funding continuity", evidence_gap_details: [{ evidence_id: "e1", description: "Missing outcome data" }], observed_patterns: [{ pattern: "donor concentration" }], innovation_hypotheses: [{ hypothesis: "Investigate peer learning" }] } }} />);
    expect(screen.getByText("Problem framing")).toBeInTheDocument();
    expect(screen.getByText("Evidence gaps")).toBeInTheDocument();
    expect(screen.getByText("Observed patterns")).toBeInTheDocument();
    expect(screen.getByText("Innovation hypotheses")).toBeInTheDocument();
    expect(screen.getAllByText("e1")).toHaveLength(2);
    expect(screen.queryByText(/success probability/i)).not.toBeInTheDocument();
  });
});
