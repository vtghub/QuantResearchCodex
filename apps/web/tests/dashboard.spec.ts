import { expect, test } from "@playwright/test";

test("dashboard shell renders", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("QuantResearchCodex")).toBeVisible();
  await expect(page.getByText("Live trading disabled")).toBeVisible();
});
