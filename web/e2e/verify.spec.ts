import { test, expect } from "@playwright/test";

/**
 * Vérification du rendu : le tableau d'évolution NDVI est présent.
 * EN: Rendering check — NDVI table present. Résilient : tolère l'absence
 * d'API (en CI, le tableau affiche l'état vide documenté au lieu de crasher).
 */
test("le tableau d'évolution NDVI est présent", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await page.waitForTimeout(2500);

  // Le panneau du tableau existe toujours
  const panel = page.locator(".panel").filter({ hasText: "Tableau d'évolution" });
  await expect(panel).toBeVisible();
  await expect(
    panel.getByRole("heading", { name: "Tableau d'évolution NDVI" }),
  ).toBeVisible();

  // Soit des lignes de données (API up), soit un état vide documenté (API down)
  const rows = await panel.locator(".ndvi-table tbody tr").count();
  const emptyState = await panel.locator(".empty-state").count();
  expect(rows >= 1 || emptyState >= 1).toBeTruthy();
});
