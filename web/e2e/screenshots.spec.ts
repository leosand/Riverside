import { test, expect } from "@playwright/test";

/** Capture d'écran du dashboard pour la documentation / README. */
test("captures du dashboard (desktop + mobile)", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await page.waitForTimeout(2500);

  // 1) Desktop — vue complète
  await page.setViewportSize({ width: 1440, height: 1700 });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: "../docs/screenshots/dashboard-desktop.png", fullPage: false });

  // 2) Header
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.waitForTimeout(1000);
  await page.locator(".dashboard-header").screenshot({ path: "../docs/screenshots/dashboard-header.png" });

  // 3) Alertes
  await page.locator(".side-column").screenshot({ path: "../docs/screenshots/dashboard-alertes.png" });

  // 4) Tableau d'évolution NDVI
  const tablePanel = page.locator(".panel").filter({ hasText: "Tableau d'évolution" });
  await expect(tablePanel).toBeVisible();
  await tablePanel.screenshot({ path: "../docs/screenshots/dashboard-tableau.png" });

  // 5) Bloc projet
  const projet = page.locator(".explainer").first();
  await expect(projet).toBeVisible();
  await projet.screenshot({ path: "../docs/screenshots/dashboard-projet.png" });

  // 6) Bloc pédagogique
  const expliquer = page.locator(".explainer").nth(1);
  await expect(expliquer).toBeVisible();
  await expliquer.screenshot({ path: "../docs/screenshots/dashboard-expliquer.png" });

  // 7) Mobile
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: "../docs/screenshots/dashboard-mobile.png", fullPage: true });

  expect(true).toBeTruthy();
});
