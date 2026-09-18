import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { EvidenceForm } from "./EvidenceForm";

describe("EvidenceForm", () => {
  it("submits labelled structured evidence", async () => {
    const submit = vi.fn().mockResolvedValue(undefined);
    render(<EvidenceForm onSubmit={submit} />);
    fireEvent.change(screen.getByLabelText("Source type"), { target: { value: "community report" } });
    fireEvent.change(screen.getByLabelText("Evidence content"), { target: { value: "Members report funding uncertainty." } });
    fireEvent.change(screen.getByLabelText("Location"), { target: { value: "North region" } });
    fireEvent.click(screen.getByRole("button", { name: "Add evidence" }));
    await vi.waitFor(() => expect(submit).toHaveBeenCalledWith(expect.objectContaining({ source_type: "community report", location: "North region" })));
  });
});
