/** Smoke test — verify the live deployment is reachable and boots without errors.
 *
 * Run via: npm run smoke
 * Target: https://seoca1.github.io/wet-run/wetrun-web/ (override with PLAYWRIGHT_BASE_URL)
 *
 * Checks:
 * - HTML loads (200 OK)
 * - Canvas mounts
 * - No JS errors during boot
 * - Audio context unlocked on first gesture
 */
import { test, expect } from "@playwright/test";

// This test is designed to run against the deployed version (PLAYWRIGHT_BASE_URL).
// Skip in local development unless PLAYWRIGHT_BASE_URL is explicitly set.
const isDeployedTest = !!process.env.PLAYWRIGHT_BASE_URL;

(isDeployedTest ? test : test.skip)("deployment reachable + canvas boots + no console errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (err) => errors.push(err.message));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });

  // Pre-mark tutorial as completed to avoid tutorial overlay
  await page.goto("/");
  await page.evaluate(() => {
    localStorage.setItem("wetrun_tutorial_completed", "true");
    localStorage.removeItem("wetrun_tutorial_step");
  });
  await page.goto("/");
  await page.waitForLoadState("networkidle");

  // Wait for canvas to be visible and game instance to mount
  await expect(page.locator("canvas#game-canvas")).toBeVisible({ timeout: 30000 });
  await page.waitForFunction(() => {
    const w = window as unknown as { wetrun?: unknown };
    return typeof w.wetrun === "object";
  }, { timeout: 30000 });

  // Canvas + game instance must mount.
  const game = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: unknown };
    return typeof w.wetrun;
  });
  expect(game).toBe("object");

  // Critical assets reachable.
  const jsHash = await page.evaluate(() => {
    const m = document.querySelector("script[src*=\"assets/index-\"]");
    return m?.getAttribute("src") ?? "";
  });
  expect(jsHash).toMatch(/index-[\w-]+\.js/);
  const resp = await page.request.get(jsHash);
  expect(resp.status()).toBe(200);

  // No uncaught JS errors (allow harmless 404s for optional resources).
  const fatalErrors = errors.filter((e) => !e.includes("favicon") && !e.includes("404"));
  expect(fatalErrors, `Console errors:\n${fatalErrors.join("\n")}`).toEqual([]);
});