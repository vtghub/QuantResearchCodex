import { expect, test } from "@playwright/test";

test("dashboard shell renders", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("QuantResearchCodex")).toBeVisible();
  await expect(page.getByText("Live trading disabled")).toBeVisible();
});

test("primary navigation changes the active console panel", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("navigation", { name: "Primary" }).getByRole("button", { name: "Risk" }).click();

  await expect(page.getByRole("heading", { name: "Risk controls" })).toBeVisible();
  await expect(page.getByText("Live Kill Switch")).toBeVisible();
});

test("dashboard can hydrate from the console API", async ({ page }) => {
  await page.route("**/api/v1/console", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
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
      }
    });
  });

  await page.goto("/");

  await expect(page.getByText("API Workspace")).toBeVisible();
  await expect(page.getByText("FastAPI console endpoint")).toBeVisible();
});
