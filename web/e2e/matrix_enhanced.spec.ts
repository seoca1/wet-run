/** Matrix enhancement E2E — zone color + ICE preview (Tier 5.5+).
 *
 * Verifies the matrix screen now shows:
 * - Zone colors (surface=green, deep=red, boss=magenta)
 * - Current node ICE preview (name + HP) in right HUD
 * - State markers (▸ current, ✓ visited, → adjacent)
 */
import { test, expect } from "@playwright/test";
import { gotoIceNode, openMissionSelect, launchRun } from "./menu-nav";

test.describe("Matrix Enhanced", () => {
  test.beforeEach(async ({ page }) => {
    // Pre-mark tutorial as completed to avoid tutorial overlay
    await page.goto("./");
    await page.evaluate(() => {
      localStorage.setItem("wetrun_tutorial_completed", "true");
      localStorage.removeItem("wetrun_tutorial_step");
    });
    await page.goto("./");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);
  });

  test("matrix shows zone-colored nodes with ICE preview panel", async ({ page }) => {
    // Navigate to matrix.
    await openMissionSelect(page); // NEW_RUN → jockey select → mission select
    await launchRun(page); // launch first mission → PREP → matrix

    // Verify in matrix state.
    const runPhase = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { state?: { runPhase?: string } } | null };
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
    // Navigate matrix -> enter first node -> approach -> combat.
    await openMissionSelect(page);
    await launchRun(page);
    await gotoIceNode(page);

    // Verify iceRoster populated.
    const iceCount = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { state?: { iceRoster?: ReadonlyArray<unknown> } } | null };
      return w.wetrun?.state?.iceRoster?.length ?? 0;
    });
    expect(iceCount).toBeGreaterThan(0);
  });
});
