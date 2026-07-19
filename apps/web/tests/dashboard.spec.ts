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
