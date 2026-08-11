import { test, expect } from "@playwright/test";

/** Vérification : alertes au format professionnel (jauge + AOI complet). */
test("les alertes affichent le format professionnel", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);

  const alertItem = page.locator(".alert-item").first();
  await expect(alertItem).toBeVisible();

  // Métrique avec séparateur seuil
  const metric = await alertItem.locator(".alert-metric-row").textContent();
  expect(metric).toContain("NDVI moyen");
  expect(metric).toContain("/ seuil");

  // Jauge de progression
  const gauge = alertItem.locator(".alert-gauge-fill");
  await expect(gauge).toBeVisible();
  const fillWidth = await gauge.getAttribute("style");
  expect(fillWidth).toContain("width");

  // Explication + zone complète (UUID entier)
  await expect(alertItem.locator(".alert-explain")).toContainText("Végétation très dégradée");
  const aoi = await alertItem.locator(".alert-aoi").textContent();
  expect(aoi).toContain("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa");

  console.log("ALERTES_PRO_OK:", { metrique: metric?.trim().slice(0, 40), jauge: fillWidth?.slice(0, 30) });
});
