import { useMemo, useState } from "react";
import {
  Activity,
  Archive,
  BarChart3,
  CheckCircle2,
  Database,
  FlaskConical,
  Gauge,
  Lock,
  Play,
  ShieldCheck,
  SlidersHorizontal,
  Users
} from "lucide-react";

type SectionKey =
  | "data"
  | "experiments"
  | "strategies"
  | "portfolios"
  | "risk"
  | "audit"
  | "users";

type Section = {
  key: SectionKey;
  label: string;
  value: string;
  detail: string;
  icon: typeof Database;
};

const sections: Section[] = [
  { key: "data", label: "Data Health", value: "3", detail: "adapters ready", icon: Database },
  { key: "experiments", label: "Experiments", value: "1", detail: "queued run", icon: FlaskConical },
  { key: "strategies", label: "Strategies", value: "draft", detail: "lifecycle gated", icon: BarChart3 },
  { key: "portfolios", label: "Portfolios", value: "paper", detail: "live disabled", icon: Gauge },
  { key: "risk", label: "Risk", value: "clear", detail: "limits modeled", icon: ShieldCheck },
  { key: "audit", label: "Audit", value: "append-only", detail: "events tracked", icon: Archive },
  { key: "users", label: "Users", value: "RBAC", detail: "tenant scoped", icon: Users }
];

const tableRows: Record<SectionKey, Array<Record<string, string>>> = {
  data: [
    { Source: "Stooq", Asset: "Equities/ETFs", State: "Ready", Provenance: "Required" },
    { Source: "CoinGecko", Asset: "Crypto", State: "Ready", Provenance: "Required" },
    { Source: "ECB FX", Asset: "FX", State: "Ready", Provenance: "Required" }
  ],
  experiments: [
    { Run: "Momentum Baseline", Dataset: "US Equities Daily", State: "Queued", Gate: "No leak checks" },
    { Run: "Crypto Trend", Dataset: "Crypto Spot Daily", State: "Draft", Gate: "Needs costs" }
  ],
  strategies: [
    { Strategy: "Cross-Asset Momentum", Lifecycle: "Draft", Approval: "Two-person", Live: "Disabled" },
    { Strategy: "Mean Reversion Template", Lifecycle: "Draft", Approval: "Owner", Live: "Disabled" }
  ],
  portfolios: [
    { Portfolio: "Paper Multi-Asset", Mode: "Paper", Exposure: "$0", Reconcile: "Pending" },
    { Portfolio: "Live Sandbox", Mode: "Live", Exposure: "$0", Reconcile: "Blocked" }
  ],
  risk: [
    { Policy: "Live Kill Switch", Status: "On", Limit: "All live orders blocked", Scope: "Platform" },
    { Policy: "Max Notional", Status: "Draft", Limit: "$0 until configured", Scope: "Tenant" }
  ],
  audit: [
    { Event: "bootstrap.scaffold", Actor: "system", Target: "workspace", Immutability: "Modeled" },
    { Event: "ui.navigation.enabled", Actor: "system", Target: "web", Immutability: "Pending commit" }
  ],
  users: [
    { User: "Platform Admin", Role: "platform_admin", Tenant: "default", Status: "Active" },
    { User: "Researcher", Role: "researcher", Tenant: "default", Status: "Template" }
  ]
};

const sectionCopy: Record<SectionKey, { title: string; description: string; action: string }> = {
  data: {
    title: "Market data catalog",
    description: "Track free-first adapters, asset coverage, provenance, and entitlement status.",
    action: "Run ingestion check"
  },
  experiments: {
    title: "Research runs",
    description: "Compare queued and draft experiments before they become strategy candidates.",
    action: "Create research run"
  },
  strategies: {
    title: "Strategy lifecycle",
    description: "Promote strategies through research, paper approval, and live approval gates.",
    action: "Open promotion queue"
  },
  portfolios: {
    title: "Portfolio monitor",
    description: "Watch paper portfolios first; live execution remains blocked by design.",
    action: "Run reconciliation"
  },
  risk: {
    title: "Risk controls",
    description: "Centralize kill switches, notional limits, approval modes, and policy state.",
    action: "Review policies"
  },
  audit: {
    title: "Audit history",
    description: "Inspect append-only platform events for governance and reproducibility.",
    action: "Export audit view"
  },
  users: {
    title: "Users and workspaces",
    description: "Manage tenant-scoped roles for platform admins, researchers, traders, and viewers.",
    action: "Invite user"
  }
};

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
  const activeSection = useMemo(
    () => sections.find((section) => section.key === activeKey) ?? sections[0],
    [activeKey]
  );
  const ActiveIcon = activeSection.icon;
  const activeCopy = sectionCopy[activeKey];

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Activity aria-hidden="true" />
          <span>QuantResearchCodex</span>
        </div>
        <nav aria-label="Primary">
          {sections.map((section) => (
            <button
              aria-current={section.key === activeKey ? "page" : undefined}
              key={section.key}
              onClick={() => setActiveKey(section.key)}
              title={section.detail}
              type="button"
            >
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
          <div className="status-pill">
            <Lock aria-hidden="true" />
            <span>Live trading disabled</span>
          </div>
        </header>

        <section className="metric-grid" aria-label="Platform status">
          {sections.map((section) => (
            <button
              className="metric-card"
              key={section.key}
              onClick={() => setActiveKey(section.key)}
              type="button"
            >
              <section.icon aria-hidden="true" />
              <div>
                <span>{section.label}</span>
                <strong>{section.value}</strong>
                <p>{section.detail}</p>
              </div>
            </button>
          ))}
        </section>

        <section className="panel" aria-labelledby="active-panel-title">
          <div className="panel-heading">
            <div className="panel-title">
              <ActiveIcon aria-hidden="true" />
              <div>
                <p>{activeSection.label}</p>
                <h2 id="active-panel-title">{activeCopy.title}</h2>
              </div>
            </div>
            <div className="panel-actions">
              <button type="button" title="Adjust filters">
                <SlidersHorizontal aria-hidden="true" />
              </button>
              <button type="button" title={activeCopy.action}>
                <Play aria-hidden="true" />
              </button>
            </div>
          </div>

          <p className="panel-description">{activeCopy.description}</p>
          <DataTable rows={tableRows[activeKey]} />
        </section>

        <section className="operations-band">
          <div>
            <h2>Current workspace</h2>
            <p>Default Research Workspace</p>
          </div>
          <div>
            <h2>Next gated milestone</h2>
            <p>Connect API data, migrations, generated OpenAPI client, and Compose integration tests.</p>
          </div>
          <div>
            <h2>Verification state</h2>
            <p>
              <CheckCircle2 aria-hidden="true" />
              Web navigation is local state; backend persistence comes next.
            </p>
          </div>
        </section>
      </section>
    </main>
  );
}
