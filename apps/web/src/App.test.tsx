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
    expect(screen.getByRole("heading", { name: "Promotion gates" })).toBeTruthy();
    expect(screen.getByText("Two-person approval required")).toBeTruthy();
  });

  it("shows experiment comparison details", async () => {
    render(<App />);
    await screen.findByText("Static fallback mode");

    fireEvent.click(screen.getByRole("button", { name: "Experiments" }));

    expect(screen.getByRole("heading", { name: "Experiment comparison" })).toBeTruthy();
    expect(screen.getByText("Promote to paper review")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Equity/ETF live-data research" })).toBeTruthy();
  });

  it("runs the equity ETF use case from the experiments panel", async () => {
    vi.mocked(globalThis.fetch)
      .mockRejectedValueOnce(new Error("API offline"))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data_vendors: ["yahoo-finance-compatible"],
            symbols_result: [
              {
                symbol: "SPY",
                vendor: "yahoo-finance-compatible",
                bar_count: 251,
                latest_close: 586.2,
                latest_signal: 1,
                sharpe: 0.42,
                max_drawdown: -0.08,
                turnover: 3.0
              }
            ],
            allocations: [
              {
                symbol: "SPY",
                weight: 1,
                signal: 1,
                momentum_score: 0.2,
                volatility: 0.15
              }
            ],
            cash_weight: 0
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

    render(<App />);
    await screen.findByText("Static fallback mode");
    fireEvent.click(screen.getByRole("button", { name: "Experiments" }));
    fireEvent.click(screen.getByRole("button", { name: "Run SPY/QQQ/IWM" }));

    expect(await screen.findByText("Vendor: yahoo-finance-compatible")).toBeTruthy();
    expect(screen.getByText("586.20")).toBeTruthy();
    expect(screen.getByText("100.00%")).toBeTruthy();
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
