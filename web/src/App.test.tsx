import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import App from "./App";

const response = (body: unknown, ok = true) => Promise.resolve({ ok, json: () => Promise.resolve(body), text: () => Promise.resolve("# Brief") } as Response);
function mockFetch(handlers: Record<string, unknown>) {
  globalThis.fetch = vi.fn((url: string, options?: RequestInit) => {
    const body = handlers[`${options?.method ?? "GET"} ${url}`] ?? handlers[url];
    return response(body ?? { error: { code: "INTERNAL_ERROR" } }, body !== undefined);
  }) as unknown as typeof fetch;
}
function app() { return render(<BrowserRouter><App /></BrowserRouter>); }
describe("web MVP", () => {
  it("shows the responsible-AI label and project empty state", async () => { mockFetch({ "GET /api/v1/projects": [] }); app(); expect(await screen.findByText(/Human review is required/i)).toBeInTheDocument(); fireEvent.click(screen.getByRole("link", { name: "Projects" })); expect(await screen.findByText(/Create your first project/i)).toBeInTheDocument(); expect(screen.queryByText(/Best strategy/i)).not.toBeInTheDocument(); });
  it("lists projects", async () => { mockFetch({ "GET /api/v1/projects": [{ project_id: "p1", name: "Community network", created_at: "2026-01-01T00:00:00Z" }] }); app(); expect(await screen.findByText("Community network")).toBeInTheDocument(); });
  it("creates a project", async () => { mockFetch({ "GET /api/v1/projects": [], "POST /api/v1/projects": { project_id: "p1", name: "New project", created_at: "2026-01-01T00:00:00Z" } }); app(); fireEvent.click(await screen.findByRole("link", { name: "Projects" })); fireEvent.change(screen.getByLabelText("Project name"), { target: { value: "New project" } }); fireEvent.click(screen.getByRole("button", { name: "Create project" })); await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/v1/projects", expect.objectContaining({ method: "POST" }))); });
  it("renders a helpful API error", async () => { mockFetch({ "GET /api/v1/projects": [] }); app(); fireEvent.click(await screen.findByRole("link", { name: "Projects" })); fireEvent.change(screen.getByLabelText("Project name"), { target: { value: "Broken" } }); (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ ok: false, json: () => Promise.resolve({ error: { code: "VALIDATION_ERROR" } }) }); fireEvent.click(screen.getByRole("button", { name: "Create project" })); expect(await screen.findByText(/Please check the supplied information/i)).toBeInTheDocument(); });
});
