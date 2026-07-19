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
            dataset_checksum: "sha256:test",
            data_profile: [
              {
                symbol: "SPY",
                vendor: "yahoo-finance-compatible",
                requested_start: "20240101",
                requested_end: "20241231",
                first_bar_date: "2024-01-02",
                last_bar_date: "2024-12-31",
                bar_count: 251,
                latest_close: 586.2
              }
            ],
            raw_bars: [
              {
                symbol: "SPY",
                date: "2024-01-02",
                open: 580,
                high: 588,
                low: 579,
                close: 586.2,
                volume: 1000000,
                vendor: "yahoo-finance-compatible"
              }
            ],
            steps: [
              {
                order: 1,
                name: "Fetch market data",
                input: "SPY from 20240101 to 20241231",
                method: "Try Stooq, then Yahoo-compatible.",
                output: "Daily OHLCV bars."
              },
              {
                order: 2,
                name: "Generate signals",
                input: "Close prices.",
                method: "Moving-average crossover.",
                output: "Binary exposure signal."
              }
            ],
            decisions: [
              {
                area: "Data vendor",
                decision: "Used yahoo-finance-compatible for this run.",
                rationale: "Fallback returned usable bars."
              }
            ],
            symbols_result: [
              {
                symbol: "SPY",
                vendor: "yahoo-finance-compatible",
                bar_count: 251,
                first_date: "2024-01-02",
                last_date: "2024-12-31",
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
    expect(screen.getByRole("heading", { name: "Data used" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Complete raw data used" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Steps followed" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Decisions made" })).toBeTruthy();
    expect(screen.getByText("Fetch market data")).toBeTruthy();
    expect(screen.getByText("Fallback returned usable bars.")).toBeTruthy();
    expect(screen.getAllByText("586.20").length).toBeGreaterThan(1);
    expect(screen.getByText("2024-01-02")).toBeTruthy();
    expect(screen.getByText("1,000,000")).toBeTruthy();
    expect(screen.getByText("100.00%")).toBeTruthy();
  });

  it("opens filters and runs the use case from the panel action", async () => {
    vi.mocked(globalThis.fetch)
      .mockRejectedValueOnce(new Error("API offline"))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data_vendors: ["yahoo-finance-compatible"],
            dataset_checksum: "sha256:test",
            data_profile: [],
            raw_bars: [],
            steps: [],
            decisions: [],
            symbols_result: [],
            allocations: [],
            cash_weight: 1
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

    render(<App />);
    await screen.findByText("Static fallback mode");
    fireEvent.click(screen.getByRole("button", { name: "Experiments" }));
    fireEvent.click(screen.getByTitle("Adjust filters"));

    const symbolsInput = screen.getByLabelText("Symbols");
    fireEvent.change(symbolsInput, { target: { value: "SPY,DIA" } });
    fireEvent.click(screen.getByTitle("Create research run"));

    expect(await screen.findByText("Vendor: yahoo-finance-compatible")).toBeTruthy();
    const request = JSON.parse(vi.mocked(globalThis.fetch).mock.calls[1][1]?.body as string);
    expect(request.symbols).toEqual(["SPY", "DIA"]);
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
