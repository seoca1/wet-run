/** E2E tests for wet_run game — complete flow from launch to combat.
 *
 * Verifies: game launch, menu navigation with keyboard/arrows, mission
 * selection, combat flow, and ESC key functionality. Exercises the full
 * player journey from boot to combat victory.
 */
import { test, expect } from "@playwright/test";

test.describe("Wet Run Game", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("./");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);
  });

  test("loads the game page", async ({ page }) => {
    await expect(page).toHaveTitle(/Wet Run/);
    const canvas = page.locator("canvas#game-canvas");
    await expect(canvas).toBeVisible();
  });

  test("displays main menu on boot", async ({ page }) => {
    const screen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(screen).toBe("menu");

    const canvasInfo = await page.evaluate(() => {
      const c = document.getElementById("game-canvas") as HTMLCanvasElement | null;
      if (!c) return null;
      return { width: c.width, height: c.height };
    });
    expect(canvasInfo).not.toBeNull();
    expect(canvasInfo?.width).toBeGreaterThan(0);
    expect(canvasInfo?.height).toBeGreaterThan(0);
  });

  test("game canvas exists and is visible", async ({ page }) => {
    const canvas = page.locator("canvas#game-canvas");
    await expect(canvas).toBeVisible();

    const dimensions = await page.evaluate(() => {
      const c = document.getElementById("game-canvas") as HTMLCanvasElement | null;
      return c ? { w: c.width, h: c.height } : null;
    });
    expect(dimensions).not.toBeNull();
  });

  test("can start new run with keyboard", async ({ page }) => {
    const initialScreen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(initialScreen).toBe("menu");

    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);

    const newScreen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(newScreen).toBe("mission_select");

    const canvas = page.locator("canvas#game-canvas");
    await expect(canvas).toBeVisible();
  });

  test("can navigate menu with arrow keys", async ({ page }) => {
    const initialScreen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(initialScreen).toBe("menu");

    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(200);

    await page.keyboard.press("ArrowUp");
    await page.waitForTimeout(200);

    const screen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(screen).toBe("menu");

    const canvas = page.locator("canvas#game-canvas");
    await expect(canvas).toBeVisible();
  });

  test("settings menu accessible", async ({ page }) => {
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(100);
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(100);
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(100);

    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);

    const screen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(screen).toBe("settings");

    const canvas = page.locator("canvas#game-canvas");
    await expect(canvas).toBeVisible();
  });

  test("ESC key returns from settings to menu", async ({ page }) => {
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);

    const settingsScreen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(settingsScreen).toBe("settings");

    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);

    const menuScreen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(menuScreen).toBe("menu");

    const canvas = page.locator("canvas#game-canvas");
    await expect(canvas).toBeVisible();
  });

  test("full flow: menu → mission select → approach → combat", async ({ page }) => {
    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);

    const missionScreen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(missionScreen).toBe("mission_select");

    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);

    const phase = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getPhase(): string | null } };
      return w.wetrun?.getPhase() ?? null;
    });
    expect(["approach", "combat"]).toContain(phase);

    const canvas = page.locator("canvas#game-canvas");
    await expect(canvas).toBeVisible();
  });

  test("can progress through approach to combat", async ({ page }) => {
    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);

    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);

    const approachPhase = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getPhase(): string | null } };
      return w.wetrun?.getPhase() ?? null;
    });
    expect(approachPhase).toBe("approach");

    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);

    const combatPhase = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getPhase(): string | null } };
      return w.wetrun?.getPhase() ?? null;
    });
    expect(combatPhase).toBe("combat");
  });

  test("can use program in combat via digit key", async ({ page }) => {
    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);
    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);
    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);

    const initialPhase = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getPhase(): string | null } };
      return w.wetrun?.getPhase() ?? null;
    });
    expect(initialPhase).toBe("combat");

    await page.keyboard.press("1");
    await page.waitForTimeout(300);

    const afterAction = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getPhase(): string | null } };
      return w.wetrun?.getPhase() ?? null;
    });
    expect(["combat", "victory"]).toContain(afterAction);
  });

  test("navigation between mission select options", async ({ page }) => {
    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);

    const screen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(screen).toBe("mission_select");

    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(200);
    await page.keyboard.press("ArrowUp");
    await page.waitForTimeout(200);

    const stillMissionSelect = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(stillMissionSelect).toBe("mission_select");
  });

  test("ESC from mission select returns to menu", async ({ page }) => {
    await page.keyboard.press("Enter");
    await page.waitForTimeout(300);

    const missionScreen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(missionScreen).toBe("mission_select");

    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);

    const menuScreen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(menuScreen).toBe("menu");
  });
});
