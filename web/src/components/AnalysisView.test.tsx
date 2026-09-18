import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AnalysisView } from "./AnalysisView";

describe("AnalysisView", () => {
  it("uses factual overview counts, collapsed detail, and compact evidence chips", () => {
    render(<AnalysisView analysis={{ analysis_id: "a1", project_id: "p1", created_at: "now", evidence_ids: ["e1", "e2"], responsible_ai: "Exploratory analysis only", report: { problem: "Funding continuity", evidence_gap_details: [{ evidence_id: "e1", description: "Missing outcome data" }], observed_patterns: [{ pattern: "donor concentration" }], innovation_hypotheses: [{ hypothesis: "Investigate peer learning" }] } }} />);
    expect(screen.getByText("Analysis overview")).toBeInTheDocument();
    expect(screen.getByText("Evidence records").parentElement).toHaveTextContent("2");
    expect(screen.getAllByText("Evidence gaps")[0].parentElement).toHaveTextContent("1");
    const gapDetails = document.querySelector("#gaps details")!;
    expect(gapDetails).not.toHaveAttribute("open");
    expect(screen.getAllByText("Missing outcome data")).toHaveLength(2);
    fireEvent.click(gapDetails.querySelector("summary")!);
    expect(gapDetails).toHaveAttribute("open");
    expect(screen.getAllByLabelText("Source IDs")[0]).toHaveTextContent("e1");
    expect(screen.getByLabelText("Analysis evidence IDs")).toHaveTextContent("e1");
    expect(screen.queryByText(/success probability/i)).not.toBeInTheDocument();
    expect(screen.queryByText("Evidence quality")).not.toBeInTheDocument();
  });
});
