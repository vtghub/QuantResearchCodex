import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

beforeEach(() => {
  vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("API offline"));
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("renders the platform shell with live trading disabled", async () => {
    render(<App />);

    expect(screen.getByText("QuantResearchCodex")).toBeTruthy();
    expect(screen.getByText("Live trading disabled")).toBeTruthy();
    expect(await screen.findByText("Static fallback mode")).toBeTruthy();
  });

  it("switches console panels from the nav", async () => {
    render(<App />);
    await screen.findByText("Static fallback mode");

    fireEvent.click(screen.getByRole("button", { name: "Strategies" }));

    expect(screen.getByRole("heading", { name: "Strategy lifecycle" })).toBeTruthy();
    expect(screen.getByText("Cross-Asset Momentum")).toBeTruthy();
  });

  it("hydrates console data from the API when available", async () => {
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          workspace_name: "API Workspace",
          verification_state: "API-backed console data loaded.",
          metrics: [
            { key: "data", label: "Data Health", value: "9", detail: "api adapters" },
            { key: "risk", label: "Risk", value: "clear", detail: "api limits" }
          ],
          panels: [
            {
              key: "data",
              title: "API market data catalog",
              description: "Loaded from FastAPI.",
              action: "Run ingestion check",
              rows: [{ Source: "FastAPI", Asset: "Equities", State: "Ready" }]
            },
            {
              key: "risk",
              title: "API risk controls",
              description: "Loaded from FastAPI.",
              action: "Review policies",
              rows: [{ Policy: "Kill Switch", Status: "On" }]
            }
          ]
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    render(<App />);

    expect(await screen.findByText("API Workspace")).toBeTruthy();
    expect(screen.getByText("FastAPI console endpoint")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "API market data catalog" })).toBeTruthy();
  });
});
