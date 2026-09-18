import { test, expect } from "@playwright/test";

test.describe("Debug Window", () => {
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

  test("debug window.wetrun", async ({ page }) => {
    await page.waitForTimeout(2000);

    const wetrun = await page.evaluate(() => window.wetrun);
    const mainModuleStarted = await page.evaluate(() => window.__MAIN_MODULE_STARTED);
    const mainModuleLoading = await page.evaluate(() => window.__MAIN_MODULE_LOADING);
    const moduleLoaded = await page.evaluate(() => window.__MODULE_LOADED);
    const wetrunSetupError = await page.evaluate(() => window.__WETRUN_SETUP_ERROR);
    console.log("window.wetrun:", wetrun);
    console.log("__MAIN_MODULE_STARTED:", mainModuleStarted);
    console.log("__MAIN_MODULE_LOADING:", mainModuleLoading);
    console.log("__MODULE_LOADED:", moduleLoaded);
    console.log("__WETRUN_SETUP_ERROR:", wetrunSetupError);

    if (wetrun) {
      const screen = await page.evaluate(() => window.wetrun?.getScreen());
      console.log("getScreen():", screen);
    }

    expect(true).toBe(true);
  });
});