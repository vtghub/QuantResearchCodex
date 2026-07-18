import {
  Activity,
  Archive,
  BarChart3,
  Database,
  FlaskConical,
  Gauge,
  Lock,
  ShieldCheck,
  Users
} from "lucide-react";

const sections = [
  { label: "Data Health", value: "3", detail: "free-first adapters scaffolded", icon: Database },
  { label: "Experiments", value: "1", detail: "research run queue placeholder", icon: FlaskConical },
  { label: "Strategies", value: "draft", detail: "lifecycle gates enabled", icon: BarChart3 },
  { label: "Portfolios", value: "paper", detail: "live execution disabled", icon: Gauge },
  { label: "Risk", value: "clear", detail: "kill-switch contract ready", icon: ShieldCheck },
  { label: "Audit", value: "append-only", detail: "immutability modeled", icon: Archive },
  { label: "Users", value: "RBAC", detail: "tenant context headers", icon: Users },
  { label: "Controls", value: "locked", detail: "broker secrets not configured", icon: Lock }
];

export function App() {
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Activity aria-hidden="true" />
          <span>QuantResearchCodex</span>
        </div>
        <nav aria-label="Primary">
          {sections.slice(0, 7).map((section) => (
            <button key={section.label} type="button" title={section.detail}>
              <section.icon aria-hidden="true" />
              <span>{section.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p>Multi-tenant research platform</p>
            <h1>Research, validate, and govern trading strategies</h1>
          </div>
          <div className="status-pill">Live trading disabled</div>
        </header>

        <section className="metric-grid" aria-label="Platform status">
          {sections.map((section) => (
            <article className="metric-card" key={section.label}>
              <section.icon aria-hidden="true" />
              <div>
                <span>{section.label}</span>
                <strong>{section.value}</strong>
                <p>{section.detail}</p>
              </div>
            </article>
          ))}
        </section>

        <section className="operations-band">
          <div>
            <h2>Current workspace</h2>
            <p>Default Research Workspace</p>
          </div>
          <div>
            <h2>Next gated milestone</h2>
            <p>Connect migrations, generated OpenAPI client, and Compose integration tests.</p>
          </div>
        </section>
      </section>
    </main>
  );
}
