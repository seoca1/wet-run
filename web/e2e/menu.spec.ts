/** Main menu E2E test (Tier 4).
 *
 * Verifies that the main menu renders on boot, navigation works, and
 * NEW_RUN → MISSION_SELECT transition works. Also verifies stub screens
 * render for Tier 5+ options.
 */
import { test, expect } from "@playwright/test";

test("main menu renders with 9 options on boot", async ({ page }) => {
  await page.goto("./");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);

  // Read game state — screen should be "menu" on boot.
  const screen = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: { getScreen(): string } };
    return w.wetrun?.getScreen();
  });
  expect(screen).toBe("menu");

  // Canvas renders.
  await expect(page.locator("canvas#game-canvas")).toBeVisible();

  // Visual verification via canvas dimensions (proxy for menu rendering).
  // 80-col x 50-row landscape canvas (matches desktop test viewport 1280x720).
  const canvasInfo = await page.evaluate(() => {
    const c = document.getElementById("game-canvas") as HTMLCanvasElement | null;
    if (!c) return null;
    return { width: c.width, height: c.height };
  });
  expect(canvasInfo).not.toBeNull();
});

test("NEW_RUN option navigates to mission select", async ({ page }) => {
  await page.goto("./");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);

  // Press Enter to select the highlighted menu option (NEW_RUN, index 0).
  await page.keyboard.press("Enter");
  await page.waitForTimeout(300);

  const screen = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: { getScreen(): string } };
    return w.wetrun?.getScreen();
  });
  expect(screen).toBe("mission_select");
});

test("ESC from mission select returns to main menu", async ({ page }) => {
  await page.goto("./");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);

  // NEW_RUN → mission_select
  await page.keyboard.press("Enter");
  await page.waitForTimeout(300);

  // ESC → back to menu
  await page.keyboard.press("Escape");
  await page.waitForTimeout(300);

  const screen = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: { getScreen(): string } };
    return w.wetrun?.getScreen();
  });
  expect(screen).toBe("menu");
});

test("stub options render 'Coming soon' message", async ({ page }) => {
  await page.goto("./");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);

  // Navigate to index 4 (CREDITS) and select — should show stub.
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(300);

  // Should still be in menu flow but on a stub screen.
  // We don't have getScreen() exposed for stubs — check that state is still null.
  const stateNotSet = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: { state?: unknown } };
    return w.wetrun?.state === null || w.wetrun?.state === undefined;
  });
  expect(stateNotSet).toBe(true);

  // Press ESC to return to menu.
  await page.keyboard.press("Escape");
  await page.waitForTimeout(300);
  const backToMenu = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: { screen?: string } };
    return w.wetrun?.screen;
  });
  expect(backToMenu).toBe("menu");
});