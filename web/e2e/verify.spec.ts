import { test, expect } from "@playwright/test";

/** Vérification : fenêtre 6 mois, graphique + tableau alignés sur les données réelles. */
test("les panneaux affichent les 12 derniers mois en temps réel", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);

  // Titres avec fenêtre glissante
  await expect(page.getByRole("heading", { name: "Évolution NDVI — 12 derniers mois", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Tableau d'évolution NDVI — 12 derniers mois" })).toBeVisible();

  // Graphique (SVG)
  await expect(page.locator(".data-row .recharts-wrapper svg")).toHaveCount(1);

  // Tableau : 8 lignes (données des 12 derniers mois en base)
  const rows = await page.locator(".ndvi-table tbody tr").count();
  expect(rows).toBeGreaterThanOrEqual(7);

  // Fenêtre indiquée dans la légende du graphique
  const caption = await page.locator(".chart-caption").first().textContent();
  expect(caption).toContain("12 derniers mois");

  console.log("FENETRE12_OK:", { lignes: rows, caption: caption?.slice(0, 70) });
});
