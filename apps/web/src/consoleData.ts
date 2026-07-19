import {
  Archive,
  BarChart3,
  Database,
  FlaskConical,
  Gauge,
  ShieldCheck,
  Users
} from "lucide-react";

export type SectionKey =
  | "data"
  | "experiments"
  | "strategies"
  | "portfolios"
  | "risk"
  | "audit"
  | "users";

export type SectionMetric = {
  key: SectionKey;
  label: string;
  value: string;
  detail: string;
};

export type ConsolePanel = {
  key: SectionKey;
  title: string;
  description: string;
  action: string;
  rows: Array<Record<string, string>>;
};

export type ConsolePayload = {
  metrics: SectionMetric[];
  panels: ConsolePanel[];
  workspace_name: string;
  verification_state: string;
};

export const sectionIcons = {
  data: Database,
  experiments: FlaskConical,
  strategies: BarChart3,
  portfolios: Gauge,
  risk: ShieldCheck,
  audit: Archive,
  users: Users
};

export const fallbackConsolePayload: ConsolePayload = {
  workspace_name: "Default Research Workspace",
  verification_state: "Static fallback data loaded; API connection pending.",
  metrics: [
    { key: "data", label: "Data Health", value: "3", detail: "adapters ready" },
    { key: "experiments", label: "Experiments", value: "1", detail: "queued run" },
    { key: "strategies", label: "Strategies", value: "draft", detail: "lifecycle gated" },
    { key: "portfolios", label: "Portfolios", value: "paper", detail: "live disabled" },
    { key: "risk", label: "Risk", value: "clear", detail: "limits modeled" },
    { key: "audit", label: "Audit", value: "append-only", detail: "events tracked" },
    { key: "users", label: "Users", value: "RBAC", detail: "tenant scoped" }
  ],
  panels: [
    {
      key: "data",
      title: "Market data catalog",
      description: "Track free-first adapters, asset coverage, provenance, and entitlement status.",
      action: "Run ingestion check",
      rows: [
        { Source: "Stooq", Asset: "Equities/ETFs", State: "Ready", Provenance: "Required" },
        { Source: "CoinGecko", Asset: "Crypto", State: "Ready", Provenance: "Required" },
        { Source: "ECB FX", Asset: "FX", State: "Ready", Provenance: "Required" }
      ]
    },
    {
      key: "experiments",
      title: "Research runs",
      description: "Compare queued and draft experiments before they become strategy candidates.",
      action: "Create research run",
      rows: [
        { Run: "Momentum Baseline", Dataset: "US Equities Daily", State: "Queued", Gate: "No leak checks" },
        { Run: "Crypto Trend", Dataset: "Crypto Spot Daily", State: "Draft", Gate: "Needs costs" }
      ]
    },
    {
      key: "strategies",
      title: "Strategy lifecycle",
      description: "Promote strategies through research, paper approval, and live approval gates.",
      action: "Open promotion queue",
      rows: [
        { Strategy: "Cross-Asset Momentum", Lifecycle: "Draft", Approval: "Two-person", Live: "Disabled" },
        { Strategy: "Mean Reversion Template", Lifecycle: "Draft", Approval: "Owner", Live: "Disabled" }
      ]
    },
    {
      key: "portfolios",
      title: "Portfolio monitor",
      description: "Watch paper portfolios first; live execution remains blocked by design.",
      action: "Run reconciliation",
      rows: [
        { Portfolio: "Paper Multi-Asset", Mode: "Paper", Exposure: "$0", Reconcile: "Pending" },
        { Portfolio: "Live Sandbox", Mode: "Live", Exposure: "$0", Reconcile: "Blocked" }
      ]
    },
    {
      key: "risk",
      title: "Risk controls",
      description: "Centralize kill switches, notional limits, approval modes, and policy state.",
      action: "Review policies",
      rows: [
        { Policy: "Live Kill Switch", Status: "On", Limit: "All live orders blocked", Scope: "Platform" },
        { Policy: "Max Notional", Status: "Draft", Limit: "$0 until configured", Scope: "Tenant" }
      ]
    },
    {
      key: "audit",
      title: "Audit history",
      description: "Inspect append-only platform events for governance and reproducibility.",
      action: "Export audit view",
      rows: [
        { Event: "bootstrap.scaffold", Actor: "system", Target: "workspace", Immutability: "Modeled" },
        { Event: "ui.navigation.enabled", Actor: "system", Target: "web", Immutability: "Committed" }
      ]
    },
    {
      key: "users",
      title: "Users and workspaces",
      description: "Manage tenant-scoped roles for platform admins, researchers, traders, and viewers.",
      action: "Invite user",
      rows: [
        { User: "Platform Admin", Role: "platform_admin", Tenant: "default", Status: "Active" },
        { User: "Researcher", Role: "researcher", Tenant: "default", Status: "Template" }
      ]
    }
  ]
};
