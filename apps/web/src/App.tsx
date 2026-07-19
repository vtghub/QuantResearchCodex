import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  CheckCircle2,
  FlaskConical,
  GitCompareArrows,
  GitPullRequestArrow,
  Lock,
  Play,
  SlidersHorizontal,
} from "lucide-react";

import { fetchConsolePayload, runEquityEtfResearch, type EquityEtfResearchResult } from "./apiClient";
import {
  fallbackConsolePayload,
  sectionIcons,
  type ConsolePayload,
  type SectionKey
} from "./consoleData";

function DataTable({ rows }: { rows: Array<Record<string, string>> }) {
  const columns = Object.keys(rows[0] ?? {});

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={Object.values(row).join(":")}>
              {columns.map((column) => (
                <td key={column}>{row[column]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const experimentComparisons = [
  {
    name: "Momentum Baseline",
    sharpe: "1.18",
    drawdown: "-8.1%",
    turnover: "42%",
    gate: "Promote to paper review"
  },
  {
    name: "Crypto Trend",
    sharpe: "0.74",
    drawdown: "-18.4%",
    turnover: "91%",
    gate: "Needs cost model"
  },
  {
    name: "Mean Reversion Template",
    sharpe: "0.31",
    drawdown: "-11.9%",
    turnover: "128%",
    gate: "Reject for now"
  }
];

const promotionGates = [
  { label: "Research validation", state: "Complete", detail: "Backtest artifact v1.0.0" },
  { label: "Paper approval", state: "Pending", detail: "Two-person approval required" },
  { label: "Live approval", state: "Blocked", detail: "Live trading disabled" }
];

function EquityEtfUseCase() {
  const [status, setStatus] = useState<"idle" | "running" | "complete" | "error">("idle");
  const [result, setResult] = useState<EquityEtfResearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  function runUseCase() {
    setStatus("running");
    setError(null);
    runEquityEtfResearch()
      .then((payload) => {
        setResult(payload);
        setStatus("complete");
      })
      .catch((exc: Error) => {
        setError(exc.message);
        setStatus("error");
      });
  }

  return (
    <section className="insight-panel" aria-label="Equity ETF live research use case">
      <div className="insight-heading">
        <FlaskConical aria-hidden="true" />
        <h3>Equity/ETF live-data research</h3>
        <button className="run-use-case" disabled={status === "running"} onClick={runUseCase} type="button">
          {status === "running" ? "Running" : "Run SPY/QQQ/IWM"}
        </button>
      </div>
      {status === "idle" && (
        <p className="use-case-note">Fetches free online bars, generates signals, backtests, and builds weights.</p>
      )}
      {status === "error" && <p className="use-case-error">{error}</p>}
      {result && (
        <div className="use-case-results">
          <p className="use-case-note">Vendor: {result.data_vendors.join(", ")}</p>
          <DataTable
            rows={result.symbols_result.map((row) => ({
              Symbol: row.symbol,
              Vendor: row.vendor,
              Bars: String(row.bar_count),
              Close: row.latest_close.toFixed(2),
              Signal: row.latest_signal.toFixed(0),
              Sharpe: row.sharpe.toFixed(3),
              Drawdown: `${(row.max_drawdown * 100).toFixed(1)}%`
            }))}
          />
          <DataTable
            rows={result.allocations.map((row) => ({
              Symbol: row.symbol,
              Weight: `${(row.weight * 100).toFixed(2)}%`,
              Signal: row.signal.toFixed(0),
              Momentum: row.momentum_score.toFixed(3),
              Volatility: `${(row.volatility * 100).toFixed(1)}%`
            }))}
          />
        </div>
      )}
    </section>
  );
}

function PanelDetail({ activeKey }: { activeKey: SectionKey }) {
  if (activeKey === "experiments") {
    return (
      <>
        <section className="insight-panel" aria-label="Experiment comparison">
          <div className="insight-heading">
            <GitCompareArrows aria-hidden="true" />
            <h3>Experiment comparison</h3>
          </div>
          <div className="comparison-grid">
            {experimentComparisons.map((experiment) => (
              <div className="comparison-row" key={experiment.name}>
                <strong>{experiment.name}</strong>
                <span>Sharpe {experiment.sharpe}</span>
                <span>Max DD {experiment.drawdown}</span>
                <span>Turnover {experiment.turnover}</span>
                <em>{experiment.gate}</em>
              </div>
            ))}
          </div>
        </section>
        <EquityEtfUseCase />
      </>
    );
  }

  if (activeKey === "strategies") {
    return (
      <section className="insight-panel" aria-label="Promotion gates">
        <div className="insight-heading">
          <GitPullRequestArrow aria-hidden="true" />
          <h3>Promotion gates</h3>
        </div>
        <div className="gate-list">
          {promotionGates.map((gate) => (
            <div className="gate-item" key={gate.label}>
              <span>{gate.label}</span>
              <strong>{gate.state}</strong>
              <p>{gate.detail}</p>
            </div>
          ))}
        </div>
      </section>
    );
  }

  return null;
}

export function App() {
  const [activeKey, setActiveKey] = useState<SectionKey>("data");
  const [consolePayload, setConsolePayload] = useState<ConsolePayload>(fallbackConsolePayload);
  const [dataSource, setDataSource] = useState<"api" | "fallback">("fallback");

  useEffect(() => {
    const controller = new AbortController();

    fetchConsolePayload(controller.signal)
      .then((payload) => {
        setConsolePayload(payload);
        setDataSource("api");
      })
      .catch(() => {
        setConsolePayload(fallbackConsolePayload);
        setDataSource("fallback");
      });

    return () => controller.abort();
  }, []);

  const activeMetric = useMemo(
    () => consolePayload.metrics.find((metric) => metric.key === activeKey) ?? consolePayload.metrics[0],
    [activeKey, consolePayload.metrics]
  );
  const activePanel = useMemo(
    () => consolePayload.panels.find((panel) => panel.key === activeKey) ?? consolePayload.panels[0],
    [activeKey, consolePayload.panels]
  );
  const ActiveIcon = sectionIcons[activeMetric.key];

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Activity aria-hidden="true" />
          <span>QuantResearchCodex</span>
        </div>
        <nav aria-label="Primary">
          {consolePayload.metrics.map((section) => {
            const SectionIcon = sectionIcons[section.key];
            return (
            <button
              aria-current={section.key === activeKey ? "page" : undefined}
              key={section.key}
              onClick={() => setActiveKey(section.key)}
              title={section.detail}
              type="button"
            >
              <SectionIcon aria-hidden="true" />
              <span>{section.label}</span>
            </button>
            );
          })}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p>Multi-tenant research platform</p>
            <h1>Research, validate, and govern trading strategies</h1>
          </div>
          <div className="status-pill">
            <Lock aria-hidden="true" />
            <span>Live trading disabled</span>
          </div>
        </header>

        <section className="metric-grid" aria-label="Platform status">
          {consolePayload.metrics.map((section) => {
            const SectionIcon = sectionIcons[section.key];
            return (
            <button
              className="metric-card"
              key={section.key}
              onClick={() => setActiveKey(section.key)}
              type="button"
            >
              <SectionIcon aria-hidden="true" />
              <div>
                <span>{section.label}</span>
                <strong>{section.value}</strong>
                <p>{section.detail}</p>
              </div>
            </button>
            );
          })}
        </section>

        <section className="panel" aria-labelledby="active-panel-title">
          <div className="panel-heading">
            <div className="panel-title">
              <ActiveIcon aria-hidden="true" />
              <div>
                <p>{activeMetric.label}</p>
                <h2 id="active-panel-title">{activePanel.title}</h2>
              </div>
            </div>
            <div className="panel-actions">
              <button type="button" title="Adjust filters">
                <SlidersHorizontal aria-hidden="true" />
              </button>
              <button type="button" title={activePanel.action}>
                <Play aria-hidden="true" />
              </button>
            </div>
          </div>

          <p className="panel-description">{activePanel.description}</p>
          <DataTable rows={activePanel.rows} />
          <PanelDetail activeKey={activeKey} />
        </section>

        <section className="operations-band">
          <div>
            <h2>Current workspace</h2>
            <p>{consolePayload.workspace_name}</p>
          </div>
          <div>
            <h2>Next gated milestone</h2>
            <p>Harden persistence, secret stores, production auth, and Docker/Helm validation.</p>
          </div>
          <div>
            <h2>Verification state</h2>
            <p>
              <CheckCircle2 aria-hidden="true" />
              {consolePayload.verification_state}
            </p>
          </div>
          <div>
            <h2>Data source</h2>
            <p className={dataSource === "api" ? "source-api" : "source-fallback"}>
              {dataSource === "api" ? "FastAPI console endpoint" : "Static fallback mode"}
            </p>
          </div>
        </section>
      </section>
    </main>
  );
}
