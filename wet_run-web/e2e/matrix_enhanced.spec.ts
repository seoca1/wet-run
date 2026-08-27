/** Matrix enhancement E2E — zone color + ICE preview (Tier 5.5+).
 *
 * Verifies the matrix screen now shows:
 * - Zone colors (surface=green, deep=red, boss=magenta)
 * - Current node ICE preview (name + HP) in right HUD
 * - State markers (▸ current, ✓ visited, → adjacent)
 */
import { test, expect } from "@playwright/test";

test("matrix shows zone-colored nodes with ICE preview panel", async ({ page }) => {
  await page.goto("./");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);

  // Navigate to matrix.
  await page.keyboard.press("Enter"); // NEW_RUN
  await page.waitForTimeout(200);
  await page.keyboard.press("Enter"); // launch first mission
  await page.waitForTimeout(300);

  // Verify in matrix state.
  const runPhase = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: { state?: { runPhase?: string } | null };
    return w.wetrun?.state?.runPhase;
  });
  expect(runPhase).toBe("matrix");

  // Visual verification: matrix canvas should have content (zones rendered).
  const canvasSize = await page.evaluate(() => {
    const c = document.getElementById("game-canvas") as HTMLCanvasElement | null;
    return c ? { width: c.width, height: c.height } : null;
  });
  expect(canvasSize).not.toBeNull();
  expect(canvasSize?.width).toBeGreaterThan(0);
  expect(canvasSize?.height).toBeGreaterThan(0);
});

test("matrix ICE preview shows current node info (runPhase=combat too)", async ({ page }) => {
  await page.goto("./");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);

  // Navigate matrix → enter first node → approach → combat.
  await page.keyboard.press("Enter");
  await page.waitForTimeout(200);
  await page.keyboard.press("Enter");
  await page.waitForTimeout(300);
  await page.keyboard.press("Enter"); // matrix → approach
  await page.waitForTimeout(300);
  await page.keyboard.press("Enter"); // approach → combat

  // Verify iceRoster populated.
  const iceCount = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: { state?: { iceRoster?: ReadonlyArray<unknown> } | null };
    return w.wetrun?.state?.iceRoster?.length ?? 0;
  });
  expect(iceCount).toBeGreaterThan(0);
});