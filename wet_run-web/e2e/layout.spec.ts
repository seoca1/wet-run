/** Responsive layout verification test.
 *
 * Verifies the canvas matches the viewport aspect ratio:
 * - portrait viewport (mobile) → canvas taller than wide (50×80 portrait grid)
 * - landscape viewport (desktop) → canvas wider than tall (80×50 landscape grid)
 *
 * Bug check: if layout.ts miscalculates cols/rows on mobile, mission text
 * could overflow the canvas (truncated or wrapped unexpectedly).
 */
import { test, expect } from "@playwright/test";

test("canvas aspect matches viewport aspect", async ({ page }) => {
  await page.goto("./");
  await page.waitForLoadState("networkidle");

  const vp = page.viewportSize();
  expect(vp).not.toBeNull();
  if (!vp) return;

  const canvasBox = await page.locator("canvas#game-canvas").boundingBox();
  expect(canvasBox).not.toBeNull();
  if (!canvasBox) return;

  const viewportPortrait = vp.height > vp.width;
  const canvasPortrait = canvasBox.height > canvasBox.width;
  expect(canvasPortrait).toBe(viewportPortrait);
});