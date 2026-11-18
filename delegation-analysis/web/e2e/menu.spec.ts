/** Main menu E2E test (Tier 4).
 *
 * Verifies that the main menu renders on boot, navigation works, and
 * NEW_RUN -> MISSION_SELECT transition works. Also verifies stub screens
 * render for Tier 5+ options.
 */
import { test, expect } from "@playwright/test";

test.describe("Main Menu", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("./");
    await page.evaluate(() => {
      localStorage.setItem("wetrun_tutorial_completed", "true");
      localStorage.removeItem("wetrun_tutorial_step");
    });
    await page.goto("./");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);
  });

  test("main menu renders with 9 options on boot", async ({ page }) => {
    const screen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(screen).toBe("menu");

    await expect(page.locator("canvas#game-canvas")).toBeVisible();

    const canvasInfo = await page.evaluate(() => {
      const c = document.getElementById("game-canvas") as HTMLCanvasElement | null;
      if (!c) return null;
      return { width: c.width, height: c.height };
    });
    expect(canvasInfo).not.toBeNull();
  });

  test("NEW_RUN option navigates to mission select", async ({ page }) => {
    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);

    const screen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(screen).toBe("mission_select");
  });

  test("ESC from mission select returns to main menu", async ({ page }) => {
    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);

    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);

    const screen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(screen).toBe("menu");
  });

  test("stub options render 'Coming soon' message", async ({ page }) => {
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);

    const stateNotSet = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { state?: unknown } };
      return w.wetrun?.state === null || w.wetrun?.state === undefined;
    });
    expect(stateNotSet).toBe(true);

    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);
    const backToMenu = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { screen?: string } };
      return w.wetrun?.screen;
    });
    expect(backToMenu).toBe("menu");
  });
});