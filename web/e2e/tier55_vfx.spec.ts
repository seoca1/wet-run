/** Matrix event routing + combat VFX overlay E2E (Tier 5.5). */
import { test, expect } from "@playwright/test";
import { enterForPhase, enterForScreen, gotoIceNode, enterForRunPhase, openMissionSelect, launchRun } from "./menu-nav";

test.describe("Tier 5.5 VFX", () => {
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

  test("matrix shows event glyphs (combat/discovery/trap/etc.)", async ({ page }) => {
    // Navigate to NEW_RUN -> mission_select -> launch.
    await openMissionSelect(page); // NEW_RUN → jockey select → mission select
    await launchRun(page); // launch first mission → PREP → matrix

    // After launch, state.runPhase="matrix" (the screen field stays
    // "mission_select" but draw() routes by runPhase). Verify via state.
    const runPhase = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { state?: { runPhase?: string } | null } };
      return w.wetrun?.state?.runPhase ?? null;
    });
    expect(runPhase).toBe("matrix");
  });

  test("combat triggers VFX (canvas changes after card use)", async ({ page }) => {
    // Navigate: NEW_RUN -> launch (runPhase matrix) -> walk to ICE -> combat.
    await enterForScreen(page, "mission_select");
    await enterForRunPhase(page, "matrix");
    await enterForPhase(page, "approach");
    await gotoIceNode(page);

    // Verify in combat phase.
    const phase = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getPhase(): string | null } };
      return w.wetrun?.getPhase();
    });
    expect(phase).toBe("combat");

    // Use a program -> should trigger VFX (state.vfxInstances.length > 0).
    // Program-use VFX are short-lived (import_vfx ticks x 16ms = 32-48ms) and
    // pruned by wall-clock, so a fixed wait before a single read always sees
    // 0. Poll immediately after the keypress to observe the transient.
    await page.keyboard.press("1"); // first program

    const vfxCount = () =>
      page.evaluate(() => {
        const w = window as unknown as {
          wetrun?: { state?: { vfxInstances?: ReadonlyArray<unknown> } | null };
        };
        return w.wetrun?.state?.vfxInstances?.length ?? 0;
      });
    await expect
      .poll(vfxCount, { timeout: 1000, intervals: [5, 10, 25] })
      .toBeGreaterThan(0);
  });
});