import { getConsole } from "./generated/apiClient";

export function fetchConsolePayload(signal?: AbortSignal) {
  return getConsole({}, signal);
}

const defaultBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type EquityEtfResearchResult = {
  data_vendors: string[];
  symbols_result: Array<{
    symbol: string;
    vendor: string;
    bar_count: number;
    latest_close: number;
    latest_signal: number;
    sharpe: number;
    max_drawdown: number;
    turnover: number;
  }>;
  allocations: Array<{
    symbol: string;
    weight: number;
    signal: number;
    momentum_score: number;
    volatility: number;
  }>;
  cash_weight: number;
};

export async function runEquityEtfResearch(signal?: AbortSignal): Promise<EquityEtfResearchResult> {
  const response = await fetch(
    `${defaultBaseUrl}/api/v1/research/use-cases/equity-etf/live-run`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-role": "researcher"
      },
      body: JSON.stringify({
        symbols: ["SPY", "QQQ", "IWM"],
        start: "20240101",
        end: "20241231",
        fast_window: 20,
        slow_window: 50,
        fee_bps: 1,
        slippage_bps: 1
      }),
      signal
    }
  );

  if (!response.ok) {
    throw new Error(`Equity/ETF research API returned ${response.status}`);
  }

  return response.json() as Promise<EquityEtfResearchResult>;
}
