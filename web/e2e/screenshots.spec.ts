import { test, expect } from "@playwright/test";

/**
 * Capture d'écran du dashboard pour la documentation / README.
 * EN: Dashboard screenshots for the README/docs.
 */

test("captures du dashboard (desktop + mobile)", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await page.waitForTimeout(2500); // laisser la carte MapLibre se charger

  // 1) Desktop — vue complète (dashboard + explainer)
  await page.setViewportSize({ width: 1440, height: 1400 });
  await page.waitForTimeout(1500);
  await page.screenshot({
    path: "../docs/screenshots/dashboard-desktop.png",
    fullPage: false,
  });

  // 2) Zone supérieure (header + carte + graphique)
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.waitForTimeout(1000);
  await page.locator(".dashboard-header").screenshot({ path: "../docs/screenshots/dashboard-header.png" });

  // 3) Panneau alertes (avec explication)
  await page.locator(".side-column").screenshot({ path: "../docs/screenshots/dashboard-alertes.png" });

  // 4) Bloc pédagogique (explainer)
  const explainer = page.locator(".explainer");
  await expect(explainer).toBeVisible();
  await explainer.screenshot({ path: "../docs/screenshots/dashboard-expliquer.png" });

  // 5) Mobile
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(1500);
  await page.screenshot({
    path: "../docs/screenshots/dashboard-mobile.png",
    fullPage: true,
  });

  expect(true).toBeTruthy();
});
