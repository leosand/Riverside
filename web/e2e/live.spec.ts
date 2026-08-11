import { test, expect } from "@playwright/test";

/** Preuve du temps réel : le tableau inclut la dernière observation insérée. */
test("le tableau inclut la dernière observation insérée en base", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);

  // Le 8e point (2026-08-10) inséré en base doit apparaître dans le tableau
  const rows = page.locator(".ndvi-table tbody tr");
  await expect(rows).toHaveCount(8);
  const lastDate = await rows.last().locator("td").first().textContent();
  expect(lastDate).toContain("10 août");
  console.log("LIVE_OK:", { lignes: 8, derniereLigne: lastDate });
});
