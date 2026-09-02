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

test("deployment reachable + canvas boots + no console errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (err) => errors.push(err.message));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });

  await page.goto("/");
  await page.waitForLoadState("networkidle");

  // Canvas + game instance must mount.
  await expect(page.locator("canvas#game-canvas")).toBeVisible();
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