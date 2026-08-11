import { defineConfig, devices } from "@playwright/test";

/** Config captures d'écran — réutilise le serveur Next.js déjà lancé sur :3101. */
export default defineConfig({
  testDir: "./e2e",
  testMatch: /(screenshots|verify|dashboard|live)\.spec\.ts/,
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:3101",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npx next start -p 3101",
    url: "http://127.0.0.1:3101",
    reuseExistingServer: true,
  },
});
