/** Settings screen E2E test (Tier 5).
 *
 * Verifies SETTINGS menu option navigates to the settings screen,
 * arrow keys adjust BGM/SFX volumes, and ESC returns to main menu.
 *
 * First-run tutorial overlay is dismissed via localStorage seed before
 * page load so the test starts directly on the main menu.
 */
import { test, expect } from "@playwright/test";

async function setupTest(page: import("@playwright/test").Page): Promise<void> {
  await page.goto("./");
  await page.evaluate(() => {
    localStorage.setItem("wetrun_tutorial_completed", "true");
    localStorage.removeItem("wetrun_tutorial_step");
  });
  await page.goto("./");
  await page.waitForLoadState("networkidle");
  // Wait for game to be fully initialized
  await page.waitForFunction(() => {
    const w = window as unknown as { wetrun?: { getScreen(): string } };
    return w.wetrun?.getScreen?.() === "menu";
  });
  await page.waitForTimeout(500);
}

async function navigateToSettings(page: import("@playwright/test").Page): Promise<void> {
  // SETTINGS is at menu index 3 (0=NEW_RUN, 1=GRAPHIC_NOVEL, 2=CONTINUE, 3=SETTINGS).
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(300);
  // Wait for settings screen to be active
  await page.waitForFunction(() => {
    const w = window as unknown as { wetrun?: { getScreen(): string } };
    return w.wetrun?.getScreen() === "settings";
  }, { timeout: 10000 });
}

test("SETTINGS menu option navigates to settings screen", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (err) => errors.push(`PAGE_ERROR: ${err.message}`));
  page.on("console", (msg) => {
    if (msg.type() === "error" && !msg.text().includes("favicon")) {
      errors.push(`${msg.type()}: ${msg.text()}`);
    }
  });

  await setupTest(page);
  await navigateToSettings(page);

  const screenInfo = await page.evaluate(() => {
    const w = window as unknown as {
      wetrun?: { screen?: string; state?: unknown };
    };
    return { screen: w.wetrun?.screen, stateNull: w.wetrun?.state === null };
  });
  expect(screenInfo.screen).toBe("settings");
  expect(screenInfo.stateNull).toBe(true);

  const criticalErrors = errors.filter(
    (e) => !e.includes("AudioContext") && !e.includes("user gesture") && !e.includes("favicon") && !e.includes("404"),
  );
  expect(criticalErrors).toEqual([]);
});

test("ArrowRight on settings increments BGM volume", async ({ page }) => {
  await setupTest(page);
  await navigateToSettings(page);

  // Verify settingsState is initialized via the getter
  const before = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: { getSettingsState(): unknown } };
    return w.wetrun?.getSettingsState?.() ?? null;
  });
  expect(before).not.toBeNull();
  expect((before as { bgmVolume: number }).bgmVolume).toBe(0.4);

  // Default BGM = 0.4. ArrowRight should bump it to 0.5.
  await page.keyboard.press("ArrowRight");

  // Wait for the async volume change to persist to localStorage
  await page.waitForTimeout(3000);

  // Verify localStorage was updated (AudioManager persists volumes)
  const afterLs = await page.evaluate(() => localStorage.getItem("wetrun_audio_bgm_volume"));
  expect(afterLs).toBe("0.5");
});

test("ESC from settings returns to main menu", async ({ page }) => {
  await setupTest(page);
  await navigateToSettings(page);

  await page.keyboard.press("Escape");
  await page.waitForTimeout(300);

  const screen = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: { screen?: string } };
    return w.wetrun?.screen;
  });
  expect(screen).toBe("menu");
});
