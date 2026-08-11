import { defineConfig, devices } from "@playwright/test";

/**
 * Config Playwright — frontend Riverside (MapLibre).
 * EN: Playwright config — Riverside frontend (MapLibre).
 * Le webServer démarre Next.js en mode production pour tester le rendu SSR.
 */
export default defineConfig({
  testDir: "./e2e",
  // Tests de démonstration locale (dépendent de l'API + données en base) :
  // exclus de la CI, exécutés via playwright.screenshots.config.ts
  testIgnore: /(live|verify|screenshots)\.spec\.ts/,
  fullyParallel: true,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:3101",
    trace: "on-first-retry",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: {
    command: "npm run build && npm run start -- -p 3101",
    url: "http://127.0.0.1:3101",
    reuseExistingServer: false,
    timeout: 180_000,
  },
});
