import { test, expect } from "@playwright/test";

/** Capture d'écran du dashboard pour la documentation / README. */
test("captures du dashboard (desktop + mobile)", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await page.waitForTimeout(2500);

  // 1) Desktop — vue complète (dashboard + projet + explainer)
  await page.setViewportSize({ width: 1440, height: 1600 });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: "../docs/screenshots/dashboard-desktop.png", fullPage: false });

  // 2) Header
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.waitForTimeout(1000);
  await page.locator(".dashboard-header").screenshot({ path: "../docs/screenshots/dashboard-header.png" });

  // 3) Alertes
  await page.locator(".side-column").screenshot({ path: "../docs/screenshots/dashboard-alertes.png" });

  // 4) Bloc projet
  const projet = page.locator(".explainer").first();
  await expect(projet).toBeVisible();
  await projet.screenshot({ path: "../docs/screenshots/dashboard-projet.png" });

  // 5) Bloc pédagogique
  const expliquer = page.locator(".explainer").nth(1);
  await expect(expliquer).toBeVisible();
  await expliquer.screenshot({ path: "../docs/screenshots/dashboard-expliquer.png" });

  // 6) Mobile
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: "../docs/screenshots/dashboard-mobile.png", fullPage: true });

  expect(true).toBeTruthy();
});
