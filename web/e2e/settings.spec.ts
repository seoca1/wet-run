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
  });
  await page.reload();
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);
}

async function navigateToSettings(page: import("@playwright/test").Page): Promise<void> {
  // SETTINGS is at menu index 3 (0=NEW_RUN, 1=GRAPHIC_NOVEL, 2=CONTINUE, 3=SETTINGS).
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(300);
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
    (e) => !e.includes("AudioContext") && !e.includes("user gesture") && !e.includes("favicon"),
  );
  expect(criticalErrors).toEqual([]);
});

test("ArrowRight on settings increments BGM volume", async ({ page }) => {
  await setupTest(page);
  await navigateToSettings(page);

  // Default BGM = 0.4. ArrowRight should bump it to 0.5.
  await page.keyboard.press("ArrowRight");
  await page.waitForTimeout(150);

  const after = await page.evaluate(() => {
    return localStorage.getItem("wetrun_audio_bgm_volume");
  });

  expect(after).toBe("0.5");
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

