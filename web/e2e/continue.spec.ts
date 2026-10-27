/** CONTINUE option E2E — autosave + reload + resume round-trip.
 *
 * Bug context (2026-08-27): main menu was added but CONTINUE option was a stub.
 * This test verifies the full round-trip:
 * 1. Boot → menu
 * 2. NEW_RUN → mission_select → launch → combat
 * 3. Trigger autosave via draw()
 * 4. Reload page (simulates browser close)
 * 5. Boot → menu → CONTINUE → resume → combat with saved HP/turn
 *
 * The autosave persists to IDB; the reload forces a fresh JS context.
 * If CONTINUE works, the player sees their previous HP/turn state.
 */
import { test, expect } from "@playwright/test";
import { enterForPhase, enterForScreen, gotoIceNode, enterForRunPhase } from "./menu-nav";

test.describe("CONTINUE Option", () => {
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

  test("CONTINUE option resumes saved state from IDB", async ({ page }) => {
    // Boot + launch mission -> walk to ICE -> combat (autosave fires on draw()).
    await enterForScreen(page, "mission_select");
    await enterForRunPhase(page, "matrix");
    await enterForPhase(page, "approach");
    await gotoIceNode(page);
    // Wait long enough for autosave IDB write to complete (async fire-and-forget).
    await page.waitForTimeout(2000);

    // Verify we're in combat with saved state.
    const phaseBeforeReload = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getPhase(): string | null; state?: { turnCount?: number } | null } };
      return { phase: w.wetrun?.getPhase() ?? null, turnCount: w.wetrun?.state?.turnCount ?? null };
    });
    expect(["combat", "approach"]).toContain(phaseBeforeReload.phase);

    // Verify save was actually written to IDB before reloading.
    const hasSaveAfterAutoplay = await page.evaluate(async () => {
      return new Promise<boolean>((resolve) => {
        const req = indexedDB.open("wetrun_save_v1");
        req.onsuccess = () => {
          const db = req.result;
          const tx = db.transaction("slots", "readonly");
          const store = tx.objectStore("slots");
          const getReq = store.get("slot_0");
          getReq.onsuccess = () => {
            resolve(getReq.result !== undefined);
            db.close();
          };
          getReq.onerror = () => {
            resolve(false);
            db.close();
          };
        };
        req.onerror = () => resolve(false);
      });
    });
    expect(hasSaveAfterAutoplay).toBe(true);

    // Reload the page (simulates browser close + reopen).
    await page.reload();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    // Verify we're back at main menu.
    const screenAfterReload = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(screenAfterReload).toBe("menu");

    // Navigate to CONTINUE by resolving its live menu index.
    const nav = await page.evaluate(() => {
      const w = window as unknown as {
        wetrun?: { getMenuOptionKeys(): string[]; getSelectedMenuIndex(): number };
      };
      const keys = w.wetrun?.getMenuOptionKeys?.() ?? [];
      const cur = w.wetrun?.getSelectedMenuIndex?.() ?? 0;
      return { idx: keys.indexOf("continue"), cur, len: keys.length };
    });
    const downs = (nav.idx - nav.cur + nav.len) % nav.len;
    for (let i = 0; i < downs; i += 1) {
      await page.keyboard.press("ArrowDown");
      await page.waitForTimeout(120);
    }
    await page.keyboard.press("Enter");
    await page.waitForTimeout(500);

    // Verify we're back in combat/approach with restored state.
    const phaseAfterContinue = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getPhase(): string | null; state?: { turnCount?: number } | null } };
      return { phase: w.wetrun?.getPhase() ?? null, turnCount: w.wetrun?.state?.turnCount ?? null };
    });
    expect(["combat", "approach"]).toContain(phaseAfterContinue.phase);

    // Turn count should be the same as before reload (state restored).
    expect(phaseAfterContinue.turnCount).toBe(phaseBeforeReload.turnCount);
  });

  /**
   * REGRESSION (severe): the post-CONTINUE assertion above used to accept
   * `["combat","approach"]`, which the DEAD restored state also reported
   * (its `phase` was literally "approach"). A restored run whose `matrix`
   * is null routes every input through `applyMatrixAction`, whose confirm
   * and movement branches are both gated on `state.matrix != null` — so
   * the player could neither confirm nor move.
   *
   * This test asserts PLAYABILITY: the restored state carries a real
   * matrix, sits on a valid node, and actually REACTS to a keypress.
   */
  test("CONTINUE restores a playable state (matrix present, input is actionable)", async ({ page }) => {
    // Boot + launch mission -> walk to ICE -> combat (autosave fires on draw()).
    await enterForScreen(page, "mission_select");
    await enterForRunPhase(page, "matrix");
    await enterForPhase(page, "approach");
    await gotoIceNode(page);
    await page.waitForTimeout(2000);

    const beforeReload = await page.evaluate(() => {
      const w = window as unknown as {
        wetrun?: {
          state?: {
            matrix?: { nodes?: Array<{ iceIds?: unknown[] }> } | null;
            currentNodeIndex?: number;
            turnCount?: number;
          } | null;
        };
      };
      const s = w.wetrun?.state;
      return {
        nodeCount: s?.matrix?.nodes?.length ?? 0,
        currentNodeIndex: s?.currentNodeIndex ?? -1,
        turnCount: s?.turnCount ?? null,
      };
    });
    expect(beforeReload.nodeCount).toBeGreaterThan(0);

    await page.reload();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    // Navigate to CONTINUE by resolving its live menu index.
    const nav = await page.evaluate(() => {
      const w = window as unknown as {
        wetrun?: { getMenuOptionKeys(): string[]; getSelectedMenuIndex(): number };
      };
      const keys = w.wetrun?.getMenuOptionKeys?.() ?? [];
      const cur = w.wetrun?.getSelectedMenuIndex?.() ?? 0;
      return { idx: keys.indexOf("continue"), cur, len: keys.length };
    });
    const downs = (nav.idx - nav.cur + nav.len) % nav.len;
    for (let i = 0; i < downs; i += 1) {
      await page.keyboard.press("ArrowDown");
      await page.waitForTimeout(120);
    }
    await page.keyboard.press("Enter");
    await page.waitForTimeout(500);

    // The restored state MUST carry a real matrix and a valid node index.
    const afterContinue = await page.evaluate(() => {
      const w = window as unknown as {
        wetrun?: {
          state?: {
            matrix?: { nodes?: Array<{ iceIds?: unknown[] }> } | null;
            currentNodeIndex?: number;
            runPhase?: string;
          } | null;
        };
      };
      const s = w.wetrun?.state;
      return {
        hasMatrix: (s?.matrix?.nodes?.length ?? 0) > 0,
        nodeCount: s?.matrix?.nodes?.length ?? 0,
        currentNodeIndex: s?.currentNodeIndex ?? -1,
        runPhase: s?.runPhase ?? null,
      };
    });
    expect(afterContinue.hasMatrix).toBe(true);
    expect(afterContinue.nodeCount).toBeGreaterThan(0);
    expect(afterContinue.currentNodeIndex).toBeGreaterThanOrEqual(0);
    expect(afterContinue.currentNodeIndex).toBeLessThan(afterContinue.nodeCount);

    // The restored state must REACT to input. A dead state (null matrix)
    // swallows every keypress, so the node index would not move.
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(300);
    const afterMove = await page.evaluate(() => {
      const w = window as unknown as {
        wetrun?: { state?: { currentNodeIndex?: number } | null };
      };
      return { currentNodeIndex: w.wetrun?.state?.currentNodeIndex ?? -1 };
    });
    expect(afterMove.currentNodeIndex).not.toBe(afterContinue.currentNodeIndex);
  });

  test("CONTINUE option is grayed out when no save exists", async ({ page }) => {
    // Clear any existing save first (via direct IDB access).
    // Manually clear IDB.
    await page.evaluate(async () => {
      return new Promise<void>((resolve) => {
        const req = indexedDB.deleteDatabase("wetrun_save_v1");
        req.onsuccess = () => resolve();
        req.onerror = () => resolve();
        req.onblocked = () => resolve();
      });
    });

    // Reload to refresh state.
    await page.reload();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // Navigate to CONTINUE via its live menu index (position-independent).
    const nav2 = await page.evaluate(() => {
      const w = window as unknown as {
        wetrun?: { getMenuOptionKeys(): string[]; getSelectedMenuIndex(): number };
      };
      const keys = w.wetrun?.getMenuOptionKeys?.() ?? [];
      const cur = w.wetrun?.getSelectedMenuIndex?.() ?? 0;
      return { idx: keys.indexOf("continue"), cur, len: keys.length };
    });
    const downs2 = (nav2.idx - nav2.cur + nav2.len) % nav2.len;
    for (let i = 0; i < downs2; i += 1) {
      await page.keyboard.press("ArrowDown");
      await page.waitForTimeout(120);
    }

    // Verify the grid contains "(no save)" suffix on CONTINUE.
    // We can't read the canvas pixels easily, so check via the menu option.
    // After Enter on a no-save CONTINUE, the screen should remain on the menu
    // (handleContinue returns silently).
    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);

    const screen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string; getPhase(): string | null } };
      return { screen: w.wetrun?.getScreen(), phase: w.wetrun?.getPhase() };
    });
    expect(screen.screen).toBe("menu");
    expect(screen.phase).toBeNull(); // No state -- we never loaded a save
  });
});