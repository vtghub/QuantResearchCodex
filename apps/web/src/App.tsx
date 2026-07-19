import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  CheckCircle2,
  Lock,
  Play,
  SlidersHorizontal,
} from "lucide-react";

import { fetchConsolePayload } from "./apiClient";
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
        </section>

        <section className="operations-band">
          <div>
            <h2>Current workspace</h2>
            <p>{consolePayload.workspace_name}</p>
          </div>
          <div>
            <h2>Next gated milestone</h2>
            <p>Connect API data, migrations, generated OpenAPI client, and Compose integration tests.</p>
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
