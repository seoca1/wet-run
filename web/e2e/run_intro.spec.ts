/**
 * ADR-0317 (3b) — the run's opening card speaks the authored dialogue.
 *
 * `docs/design/story/event_dialogues.json` held the companion's first words for
 * the whole time the graphic novel carried the story, and the run never spoke
 * them. Now the construct introduces herself on the first jack-in, and only
 * then — a profile that has finished a run has already met her.
 */
import { test, expect, type Page } from "@playwright/test";
import { enterForScreen, openMissionSelect } from "./menu-nav";

/** The companion's beat while the opening card is up, or null. */
async function readBeat(page: Page) {
  return page.evaluate(() => {
    const w = window as unknown as {
      wetrun?: { getRunIntroBeat?(): { speaker: string; lines: string[] } | null };
    };
    return w.wetrun?.getRunIntroBeat?.() ?? null;
  });
}

/** Walk a fresh run to the moment the opening card is up: mission list →
 *  briefing → prep → ENTER (launch). The card owns the screen until a key. */
async function reachOpeningCard(page: Page): Promise<void> {
  await openMissionSelect(page);
  await enterForScreen(page, "briefing");
  await page.keyboard.press("Enter"); // briefing → prep
  await enterForScreen(page, "prep");
  await page.keyboard.press("Enter"); // prep → launch (the card is now up)
}

test("the construct speaks on the first jack-in", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("wetrun_tutorial_completed", "true");
    localStorage.removeItem("wetrun_runs_finished");
  });
  await page.goto("./");
  await page.waitForFunction(
    () => (window as unknown as { wetrun?: unknown }).wetrun !== undefined,
  );

  await reachOpeningCard(page);

  const beat = await readBeat(page);
  expect(beat).not.toBeNull();
  expect(beat?.speaker).toBe("Dixie Flatline");
  expect(beat?.lines.length).toBeGreaterThan(0);

  // The card is display-only: the next key dismisses it and never returns.
  await page.keyboard.press("Enter");
  await expect.poll(() => readBeat(page)).toBeNull();
});

test("a profile that has finished a run does not hear it again", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("wetrun_tutorial_completed", "true");
    localStorage.setItem("wetrun_runs_finished", "1");
  });
  await page.goto("./");
  await page.waitForFunction(
    () => (window as unknown as { wetrun?: unknown }).wetrun !== undefined,
  );

  await reachOpeningCard(page);

  expect(await readBeat(page)).toBeNull();
});
