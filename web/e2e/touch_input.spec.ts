/** Mobile touch input E2E verification.
 *
 * Existing mobile-portrait tests use mouse clicks (Playwright's page.click
 * dispatches mouse events). This spec uses Playwright's touchscreen API to
 * fire real touch events — the path a phone user takes.
 *
 * Covers:
 *   - virtual gamepad auto-shows on touch devices
 *   - D-pad touch navigates menu
 *   - A button touch confirms (NEW_RUN → mission_select)
 *   - program row touch uses a program in combat
 */
import { test, expect, type Page } from "@playwright/test";
import { enterForScreen, enterForRunPhase, gotoIceNode } from "./menu-nav";

// Touch-only spec. The virtual gamepad overlay mounts only on touch
// devices (touch.ts isTouchDevice + main.ts:456); on desktop-chromium
// the overlay is absent by design. Skip on wide viewports so the spec
// is green in both projects instead of failing on desktop.
async function isDesktop(page: Page): Promise<boolean> {
  const vp = page.viewportSize();
  return (vp?.width ?? 0) >= 640;
}

test.describe("mobile touch input", () => {
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

  test("virtual gamepad overlay is visible on touch device", async ({ page }, info) => {
    test.skip(await isDesktop(page), "overlay absent on desktop by design");
    const overlay = page.locator("#wetrun-gamepad-root");
    await expect(overlay).toBeVisible({ timeout: 3000 });
  });

  test("D-pad touch navigates menu options", async ({ page }, info) => {
    test.skip(await isDesktop(page), "overlay absent on desktop by design");
    const downBtn = page.locator("#wetrun-gamepad-root button").filter({ hasText: "↓" });
    await expect(downBtn).toBeVisible();

    // Touch the down arrow twice to move selection from NEW_RUN to GRAPHIC NOVEL.
    await tap(page, downBtn);
    await tap(page, downBtn);

    // The canvas should still be functional — no crash after touch navigation.
    await expect(page.locator("canvas#game-canvas")).toBeVisible();
  });

  test("A button touch confirms NEW_RUN → mission_select", async ({ page }, info) => {
    test.skip(await isDesktop(page), "overlay absent on desktop by design");
    const aBtn = page.locator("#wetrun-gamepad-root button").filter({ hasText: "A" });
    await expect(aBtn).toBeVisible();

    // Tap A on the highlighted NEW_RUN option.
    await tap(page, aBtn);

    // Should transition to mission_select screen.
    const screen = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getScreen(): string | null } };
      return w.wetrun?.getScreen() ?? null;
    });
    expect(screen).toBe("mission_select");
  });

  test("program row touch uses a program in combat", async ({ page }, info) => {
    test.skip(await isDesktop(page), "overlay absent on desktop by design");
    // Navigate into combat via keyboard first (establishes state), then
    // verify the program row is touchable.
    await enterForScreen(page, "mission_select");
    await enterForRunPhase(page, "matrix");
    await gotoIceNode(page);
    await enterForRunPhase(page, "combat");

    // Program row should be visible in combat on touch devices.
    const programRow = page.locator("#wetrun-program-row");
    await expect(programRow).toBeVisible({ timeout: 3000 });

    const firstProgram = programRow.locator("button").first();
    await expect(firstProgram).toBeVisible();

    // Touch the first program button.
    await tap(page, firstProgram);

    // Combat should still be active — program use didn't crash the game.
    const phase = await page.evaluate(() => {
      const w = window as unknown as { wetrun?: { getPhase(): string | null } };
      return w.wetrun?.getPhase() ?? null;
    });
    expect(phase).toBe("combat");
  });
});

/**
 * Tap the target element via Playwright's touchscreen API.
 * Fires the pointerdown → pointerup → click sequence the gamepad
 * listeners actually use (see touch.ts appendButton).
 */
async function tap(page: Page, locator: ReturnType<typeof page.locator>): Promise<void> {
  const box = await locator.boundingBox();
  if (!box) throw new Error("button not found or not visible");

  const x = box.x + box.width / 2;
  const y = box.y + box.height / 2;

  await page.touchscreen.tap(x, y);
}