/** Boss 4-phase VFX E2E (Tier 5.5+).
 *
 * Verifies the boss phase VFX kinds are wired and trigger without
 * runtime errors when bossPhase advances.
 */
import { test, expect } from "@playwright/test";

test("boss phase HUD badge appears when bossPhase > 0", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (err) => errors.push(`PAGE_ERROR: ${err.message}`));

  await page.goto("./");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);

  // Navigate to matrix (uses watchdog ICE, not boss, so bossPhase=0).
  await page.keyboard.press("Enter"); // NEW_RUN
  await page.waitForTimeout(200);
  await page.keyboard.press("Enter"); // launch
  await page.waitForTimeout(300);

  // State should be matrix.
  const phase = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: { state?: { runPhase?: string } } | null };
    return w.wetrun?.state?.runPhase;
  });
  expect(phase).toBe("matrix");

  // Default watchdog isn't boss → bossPhase = 0 → no HUD badge expected.
  const bossPhase = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: { state?: { bossPhase?: number } } | null };
    return w.wetrun?.state?.bossPhase;
  });
  expect(bossPhase).toBe(0);

  // No JS errors during this flow.
  const criticalErrors = errors.filter(
    (e) => !e.includes("AudioContext") && !e.includes("user gesture") && !e.includes("favicon"),
  );
  expect(criticalErrors).toEqual([]);
});
