import { test, expect } from "@playwright/test";

/** Vérification complète : graphique + tableau NDVI (données API) + alertes. */
test("rendu complet (graphique + tableau + alertes)", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await page.waitForTimeout(2500);

  // Graphique
  await expect(page.locator(".chart-wrap .recharts-wrapper svg")).toHaveCount(1);

  // Tableau d'évolution (données de l'API /api/v1/ndvi/series)
  const table = page.locator(".ndvi-table");
  await expect(table).toBeVisible();
  const rows = await table.locator("tbody tr").count();
  expect(rows).toBeGreaterThanOrEqual(7);
  const firstStatus = await table.locator("tbody tr").first().locator(".badge-status").textContent();
  expect(firstStatus).toContain("Conforme");

  // Alertes (panneau)
  await expect(page.locator(".alert-item").first()).toBeVisible();

  console.log("RENDU_OK:", { lignesTableau: rows, statut: firstStatus });
});
