import { defineConfig, devices } from "@playwright/test";

/** Playwright config for wet_run-web E2E verification.
 *
 * Targets the live GitHub Pages deployment (post-deploy verification) by
 * default. Override with PLAYWRIGHT_BASE_URL env to point at a local server
 * (e.g., http://localhost:5173 from `npm run dev`).
 *
 * Only chromium is enabled — mobile-first project; chromium covers Android
 * (via webkit/safari emulation in playwright.config) and desktop Chrome.
 * Add webkit/firefox later if cross-browser regressions emerge.
 */
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "https://seoca1.github.io/wet-run/wetrun-web/";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false, // sequential: shared Pages rate limits + simpler debugging
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "desktop-chromium",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1280, height: 720 },
        baseURL,
      },
    },
    {
      name: "mobile-portrait-chromium",
      use: {
        ...devices["Pixel 5"],
        viewport: { width: 393, height: 851 },
        deviceScaleFactor: 2.75,
        isMobile: true,
        hasTouch: true,
        baseURL,
      },
    },
  ],
});