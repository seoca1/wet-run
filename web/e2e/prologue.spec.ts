/**
 * ADR-0317 — the prologue opens the run.
 *
 * The graphic novel used to be a menu mode: the run began at the mission list
 * and the story was somewhere else. It is now the run's first beat — pick the
 * jockey, watch that jockey's story, then choose a mission. ESC skips the
 * STORY, not the run.
 */
import { test, expect } from "@playwright/test";
import { enterForScreen, gotoMenuOption } from "./menu-nav";

test("NEW RUN opens the jockey's prologue before the mission list", async ({
  page,
}) => {
  await page.goto("/");
  await page.waitForFunction(
    () => (window as unknown as { wetrun?: unknown }).wetrun !== undefined,
  );

  await gotoMenuOption(page, "new_run");
  await page.keyboard.press("Enter"); // → jockey select
  await enterForScreen(page, "jockey_select");

  await page.keyboard.press("Enter"); // → the run's prologue
  await enterForScreen(page, "graphic_novel");

  // ESC skips the story and hands over to the run.
  await page.keyboard.press("Escape");
  await enterForScreen(page, "mission_select");
});

test("the graphic novel menu entry still browses the story (validation)", async ({
  page,
}) => {
  await page.goto("/");
  await page.waitForFunction(
    () => (window as unknown as { wetrun?: unknown }).wetrun !== undefined,
  );

  await gotoMenuOption(page, "graphic_novel");
  await page.keyboard.press("Enter");
  await enterForScreen(page, "graphic_novel");

  // Browsing from the menu is NOT a run: ESC returns to the title.
  await page.keyboard.press("Escape");
  await expect
    .poll(() =>
      page.evaluate(
        () =>
          (window as unknown as { wetrun: { getScreen(): string } }).wetrun.getScreen(),
      ),
    )
    .toBe("menu");
});
