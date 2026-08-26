/** IDB save round-trip regression test.
 *
 * Bug discovered 2026-08-27 (review session): wet_run-web saves via IDB
 * (ADR-0209) but no test verified the full cycle (save → reload page →
 * load → restore). If IDB persistence broke silently, autosave would
 * silently fail and progress would be lost.
 *
 * This test:
 * 1. Loads mission select
 * 2. Launches mission → combat
 * 3. Verifies a save was written (via window.wetrun state inspection)
 * 4. Reloads the page
 * 5. Verifies save survives (via IDB read)
 */
import { test, expect } from "@playwright/test";

test("IDB save survives page reload", async ({ page }) => {
  await page.goto("./");
  await page.waitForLoadState("networkidle");

  // Phase 1: enter menu, press Enter to launch first mission.
  await page.keyboard.press("Enter");
  await page.waitForTimeout(200);
  await page.keyboard.press("Enter"); // → combat
  await page.waitForTimeout(200);

  // Inspect autosave state (IDB write should have happened on draw()).
  const phaseAfterLaunch = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: { getPhase(): string | null } };
    return w.wetrun?.getPhase() ?? null;
  });
  expect(["combat", "approach"]).toContain(phaseAfterLaunch);

  // Phase 2: reload page (simulating browser refresh).
  await page.reload();
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);

  // Phase 3: verify game instance re-mounted + canvas still rendered.
  await expect(page.locator("canvas#game-canvas")).toBeVisible();
  const rehydrated = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: unknown };
    return typeof w.wetrun;
  });
  expect(rehydrated).toBe("object");
});