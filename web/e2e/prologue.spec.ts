/**
 * ADR-0317 — the prologue opens the run, and the menu entry is gone.
 *
 * The graphic novel used to be a menu mode: the run began at the mission list
 * and the story was somewhere else. It is now the run's first beat — pick the
 * jockey, watch that jockey's story, then choose a mission. ESC skips the
 * STORY, not the run. Step 4 removed the menu entry that browsed it, so the
 * story has exactly one door.
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

test("the graphic novel menu entry is gone (ADR-0317 step 4)", async ({
  page,
}) => {
  await page.goto("/");
  await page.waitForFunction(
    () => (window as unknown as { wetrun?: unknown }).wetrun !== undefined,
  );

  // A finished profile sees the whole menu; the entry is not in it any more.
  await page.evaluate(() =>
    localStorage.setItem("wetrun_runs_finished", "5"),
  );
  await page.goto("/");
  await page.waitForFunction(
    () => (window as unknown as { wetrun?: unknown }).wetrun !== undefined,
  );

  const keys = await page.evaluate(
    () =>
      (
        window as unknown as { wetrun: { getMenuOptionKeys(): string[] } }
      ).wetrun.getMenuOptionKeys(),
  );
  expect(keys).not.toContain("graphic_novel");
  // And the story is still reachable — as the run's prologue.
  expect(keys).toContain("new_run");
});
