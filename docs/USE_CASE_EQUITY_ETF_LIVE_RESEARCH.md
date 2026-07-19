# Use Case: Equity and ETF Live Data Research

## Goal

Run an end-to-end research workflow for equities and ETFs using free online market-data vendors:

1. Fetch daily OHLCV bars from free sources.
2. Normalize and mine close-price data.
3. Generate moving-average crossover signals.
4. Backtest each symbol with fees and slippage.
5. Construct a long-only portfolio from signal, momentum, and volatility scores.
6. Return a reproducible response with vendor provenance, checksum, metrics, and allocations.

This is live data mode, not live order execution. Live broker execution remains disabled.

## Data Vendor Fallback

The workflow uses `FallbackDailyBarClient`:

1. Stooq daily CSV endpoint.
2. Yahoo Finance-compatible chart endpoint.

If Stooq returns no usable rows or is unavailable, the client falls back to Yahoo-compatible data. Additional free vendors can be added behind the same client contract.

## API Endpoint

`POST /api/v1/research/use-cases/equity-etf/live-run`

Example request:

```json
{
  "symbols": ["SPY", "QQQ", "IWM"],
  "start": "20240101",
  "end": "20241231",
  "fast_window": 20,
  "slow_window": 50,
  "fee_bps": 1.0,
  "slippage_bps": 1.0
}
```

Required role: `researcher`, `trader`, `organization_admin`, or `platform_admin`.

Example local call:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8001/api/v1/research/use-cases/equity-etf/live-run `
  -Headers @{ "x-role" = "researcher" } `
  -ContentType "application/json" `
  -Body '{"symbols":["SPY","QQQ","IWM"],"start":"20240101","end":"20241231","fast_window":20,"slow_window":50}'
```

## Output Shape

The response includes:

- `data_vendors`: vendors used after fallback resolution.
- `dataset_checksum`: deterministic checksum over the request and resulting metrics.
- `mining_summary`: signal and optimization methods.
- `data_profile`: vendor, requested range, available range, bar count, and latest close per symbol.
- `raw_bars`: complete normalized OHLCV rows used by the experiment.
- `steps`: ordered workflow trail covering data fetch, mining, signal generation, backtest, and portfolio construction.
- `decisions`: human-readable decisions and rationales made during the run.
- `symbols_result`: per-symbol bar counts, latest close, signal, return, volatility, Sharpe, drawdown, and turnover.
- `allocations`: long-only portfolio weights.
- `cash_weight`: unallocated portfolio cash.

## UI Location

Open the web console, go to **Experiments**, and run **Equity/ETF live-data research**.

The **Adjust filters** toolbar button opens editable controls for symbols, date range, moving-average windows, fees, and slippage. The **Create research run** toolbar button runs the experiment with the current filters, and the use-case card button does the same.

After the run completes, the UI displays:

- **Data used**: symbols, vendors, requested date range, available bar range, bar counts, and latest close.
- **Complete raw data used**: every normalized OHLCV row returned to the experiment.
- **Steps followed**: each workflow step, input, method, and output.
- **Decisions made**: data-vendor, signal, portfolio, and cash decisions with rationales.
- **Backtest results**: per-symbol metrics.
- **Portfolio construction**: final weights and optimization diagnostics.

## Current Strategy Logic

- Signal: moving-average crossover.
- Backtest: vectorized daily returns with fee and slippage costs.
- Portfolio construction: long-only signal-filtered momentum score scaled by inverse volatility.

## Verification

Automated tests use deterministic CSV/JSON fixtures and a fake daily-bar client, so CI does not depend on external vendor uptime.

Live smoke result on 2026-07-19:

- Symbols: `SPY`, `QQQ`, `IWM`
- Date range: `20240101` to `20241231`
- Vendor used: `yahoo-finance-compatible`
- Bars per symbol: `251`
- Portfolio weights produced: `IWM`, `QQQ`, `SPY`

Stooq was unavailable during the smoke test, so the workflow successfully used the Yahoo-compatible fallback.

Current verification commands:

```powershell
.\.venv\Scripts\python.exe -m pytest apps/api/tests packages/quant_core/tests packages/quant_adapters/tests
.\.venv\Scripts\python.exe -m ruff check apps packages tools
pnpm --filter quantresearch-web build
pnpm --filter quantresearch-web test
```
