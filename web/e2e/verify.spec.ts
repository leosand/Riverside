import { test, expect } from "@playwright/test";

/** Vérification du layout : graphique + tableau côte à côte, données API. */
test("graphique et tableau côte à côte avec données temps réel", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);

  // Les deux panneaux sont côte à côte dans .data-row
  const dataRow = page.locator(".data-row");
  await expect(dataRow).toBeVisible();
  const panels = await dataRow.locator("> section.panel").count();
  expect(panels).toBe(2);

  // Graphique (SVG recharts)
  await expect(page.locator(".data-row .recharts-wrapper svg")).toHaveCount(1);

  // Tableau avec lignes de données
  const rows = await page.locator(".ndvi-table tbody tr").count();
  expect(rows).toBeGreaterThanOrEqual(7);

  // Indicateur de mise à jour temps réel
  const caption = await page.locator(".ndvi-table ~ .chart-caption, .chart-caption").last().textContent();
  expect(caption).toContain("mise à jour");

  console.log("LAYOUT_OK:", { panneaux: panels, lignes: rows, caption: caption?.slice(0, 80) });
});
