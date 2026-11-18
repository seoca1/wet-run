import { test, expect } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";

const SCREENSHOT_DIR = "/Users/emilio/projects/opencodework/Game/wet_run/web/demo-screenshots";

test.describe("Game Demo - Menu to Combat", () => {
  test.beforeEach(async ({ page }) => {
    // Create screenshot directory
    if (!fs.existsSync(SCREENSHOT_DIR)) {
      fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
    }
    
    await page.goto("./");
    await page.waitForLoadState("networkidle");
    
    // Pre-mark tutorial as completed
    await page.evaluate(() => {
      localStorage.setItem("wetrun_tutorial_completed", "true");
      localStorage.removeItem("wetrun_tutorial_step");
    });
    await page.reload();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
  });

  test("Full game flow: Menu -> Mission Select -> Matrix -> Approach -> Combat", async ({ page }) => {
    // 1. MAIN MENU
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "01-main-menu.png"), fullPage: true });
    console.log("📸 01-main-menu.png captured");
    
    // Verify main menu
    const screen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string } };
      return w.wetrun?.getScreen();
    });
    expect(screen).toBe("menu");
    
    // 2. MISSION SELECT - Press Enter
    await page.keyboard.press("Enter");
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "02-mission-select.png"), fullPage: true });
    console.log("📸 02-mission-select.png captured");
    
    // 3. LAUNCH MISSION - Press Enter
    await page.keyboard.press("Enter");
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "03-matrix.png"), fullPage: true });
    console.log("📸 03-matrix.png captured");
    
    // 4. APPROACH PHASE - Press Enter
    await page.keyboard.press("Enter");
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "04-approach.png"), fullPage: true });
    console.log("📸 04-approach.png captured");
    
    // 5. COMBAT PHASE - Press Enter
    await page.keyboard.press("Enter");
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "05-combat.png"), fullPage: true });
    console.log("📸 05-combat.png captured");
    
    // 6. USE PROGRAM - Press 1
    await page.keyboard.press("1");
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "06-combat-after-program.png"), fullPage: true });
    console.log("📸 06-combat-after-program.png captured");
    
    // 7. USE ANOTHER PROGRAM - Press 1 again
    await page.keyboard.press("1");
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "07-combat-continued.png"), fullPage: true });
    console.log("📸 07-combat-continued.png captured");
    
    // Verify combat phase
    const phase = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getPhase(): string | null } };
      return w.wetrun?.getPhase();
    });
    console.log("Final phase:", phase);
    expect(["combat", "victory", "approach"]).toContain(phase);
  });

  test("Settings Menu Demo", async ({ page }) => {
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "settings-01-menu.png"), fullPage: true });
    
    // Navigate to SETTINGS (3 down, enter)
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(200);
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(200);
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(200);
    await page.keyboard.press("Enter");
    await page.waitForTimeout(500);
    
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "settings-02-screen.png"), fullPage: true });
    console.log("📸 settings-02-screen.png captured");
    
    // Adjust BGM volume (right arrow)
    await page.keyboard.press("ArrowRight");
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "settings-03-bgm-adjusted.png"), fullPage: true });
    console.log("📸 settings-03-bgm-adjusted.png captured");
    
    // ESC to return
    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "settings-04-back-to-menu.png"), fullPage: true });
    console.log("📸 settings-04-back-to-menu.png captured");
  });

  test("Tutorial Demo", async ({ page }) => {
    // Reset tutorial first
    await page.evaluate(() => {
      localStorage.removeItem("wetrun_tutorial_completed");
      localStorage.removeItem("wetrun_tutorial_step");
    });
    await page.reload();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
    
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "tutorial-01-step1.png"), fullPage: true });
    console.log("📸 tutorial-01-step1.png captured");
    
    // Step through tutorial
    for (let i = 0; i < 6; i++) {
      await page.keyboard.press("Enter");
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `tutorial-02-step${i+2}.png`), fullPage: true });
      console.log(`📸 tutorial-02-step${i+2}.png captured`);
    }
  });
});