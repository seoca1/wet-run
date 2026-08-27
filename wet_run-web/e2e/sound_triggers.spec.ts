/** Sound integration E2E (Tier 5.5+).
 *
 * Verifies sound events fire at expected transitions. Since AudioManager
 * is browser-only and Howler.js is hard to mock in Playwright, we verify
 * that NO ERRORS are thrown during combat transitions + that the game
 * continues to function after SFX dispatch calls.
 */
import { test, expect } from "@playwright/test";

test("combat SFX events fire without errors during full run", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (err) => errors.push(`PAGE_ERROR: ${err.message}`));
  page.on("console", (msg) => {
    if (msg.type() === "error" && !msg.text().includes("favicon")) {
      errors.push(`${msg.type()}: ${msg.text()}`);
    }
  });

  await page.goto("./");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(500);

  // Navigate through full combat flow.
  await page.keyboard.press("Enter"); // NEW_RUN
  await page.waitForTimeout(200);
  await page.keyboard.press("Enter"); // launch
  await page.waitForTimeout(300);
  await page.keyboard.press("Enter"); // matrix → approach
  await page.waitForTimeout(300);
  await page.keyboard.press("Enter"); // approach → combat (matrix → combat SFX)
  await page.waitForTimeout(300);

  // Use a program (combat_hit SFX + possible burn proc + boss phase if applicable).
  await page.keyboard.press("1");
  await page.waitForTimeout(300);

  // Use another program.
  await page.keyboard.press("1");
  await page.waitForTimeout(300);

  // Check that game is still in a valid state.
  const phase = await page.evaluate(() => {
    const w = window as unknown as { wetrun?: { getPhase(): string | null } };
    return w.wetrun?.getPhase();
  });
  expect(["combat", "approach", "victory"]).toContain(phase);

  // No critical JS errors should have occurred.
  const criticalErrors = errors.filter(
    (e) => !e.includes("AudioContext") && !e.includes("user gesture") && !e.includes("favicon"),
  );
  expect(criticalErrors).toEqual([]);
});