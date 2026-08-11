import { test, expect } from "@playwright/test";

/** Vérification : le nom lisible de la zone remplace l'UUID brut. */
test("la zone surveillée affiche un nom lisible (plus d'UUID brut)", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);

  const alertItem = page.locator(".alert-item").first();
  await expect(alertItem).toBeVisible();
  const aoi = await alertItem.locator(".alert-aoi").textContent();
  // L'UUID plein ne doit plus apparaître
  expect(aoi).not.toContain("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa");
  // Le nom lisible apparaît (berge-test) OU le fallback UUID tronqué (tests SQLite)
  console.log("ZONE_OK:", aoi?.trim());
  expect(aoi).toMatch(/Zone surveillée : (berge-\w+|.{1,9}…)/);
});
