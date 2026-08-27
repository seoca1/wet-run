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

test("CONTINUE option resumes saved state from IDB", async ({ page }) => {
  // Boot + launch mission → combat (autosave fires on draw()).
  await page.goto("./");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);

  await page.keyboard.press("Enter"); // NEW_RUN
  await page.waitForTimeout(200);
  await page.keyboard.press("Enter"); // launch first mission
  await page.waitForTimeout(200);
  await page.keyboard.press("Enter"); // approach → combat
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

  // Navigate to CONTINUE (index 2 in MENU_OPTIONS).
  // Arrow keys: 0 → NEW_RUN (start), ArrowDown → GRAPHIC NOVEL, ArrowDown → CONTINUE.
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");
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

test("CONTINUE option is grayed out when no save exists", async ({ page }) => {
  await page.goto("./");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);

  // Clear any existing save first (via direct IDB access).
  await page.evaluate(async () => {
    const { clear } = await import("./assets/index-BQO76r9r.js").catch(() => ({ clear: null }));
    return clear;
  }).catch(() => {
    // Module import will fail in production build; fall back to manual IDB clear.
  });

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

  // Navigate to CONTINUE (index 2).
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");

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
  expect(screen.phase).toBeNull(); // No state — we never loaded a save
});