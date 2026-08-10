import { test, expect } from "@playwright/test";

/**
 * Tests E2E frontend — Riverside dashboard (Next.js SSR + MapLibre).
 * EN: Frontend E2E — dashboard loads, degrades gracefully when the API is
 * down, and renders the map. Tous les tests sont déterministes et offline
 * (aucun appel au backend — l'API est volontairement absente).
 */

test("le tableau de bord se charge et affiche le titre", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Surveillance des berges" })).toBeVisible();
  await expect(page.getByText("Lac Ontario · NDVI Sentinel-2")).toBeVisible();
});

test("état API indisponible affiché sans planter", async ({ page }) => {
  await page.goto("/");
  // L'API n'est pas démarrée en e2e → message d'erreur explicite (role=alert)
  // NB : getByRole("alert") matche aussi l'alert implicite de la carte MapLibre —
  // on cible le message exact.
  await expect(
    page.getByRole("alert").filter({ hasText: "API indisponible" }),
  ).toBeVisible();
});

test("la carte MapLibre est rendue", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.locator('[role="application"][aria-label="Carte des berges surveillées (lac Ontario)"]'),
  ).toBeVisible();
});

test("le panneau des alertes réglementaires est présent", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Alertes réglementaires" }),
  ).toBeVisible();
});

test("le bloc pédagogique explique le projet", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Comprendre ce que vous voyez" }),
  ).toBeVisible();
  await expect(page.getByText("C'est quoi le NDVI")).toBeVisible();
});

test("la description du projet est complète", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Le projet en bref" }),
  ).toBeVisible();
  await expect(page.getByText("La solution Riverside")).toBeVisible();
  await expect(page.getByText("Le pipeline de bout en bout")).toBeVisible();
  await expect(page.getByText("Prédiction", { exact: false })).toBeVisible();
});
