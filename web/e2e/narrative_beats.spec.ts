/**
 * ADR-0317 (3b) — the mid-run beats reach the player.
 *
 * The construct warns before the profile's first fight and speaks after the
 * first win. Both are full-screen cards that own the screen until a key, so the
 * shared run helpers pre-mark them as heard (a card would eat a keypress and
 * break every spec that counts keys). This is the one spec that leaves one
 * armed and checks it actually appears and is dismissed by a single key.
 */
import { test, expect, type Page } from "@playwright/test";
import {
  chooseEncounterVerb,
  gotoEncounterDecision,
  launchRun,
  openMissionSelect,
} from "./menu-nav";

/** The beat card on screen, or null. */
async function beatCard(page: Page) {
  return page.evaluate(() => {
    const w = window as unknown as {
      wetrun?: { getBeatCard?(): { title: string; lines: string[] } | null };
    };
    return w.wetrun?.getBeatCard?.() ?? null;
  });
}

test.describe.configure({ timeout: 90_000 });

test("the first fight gets one warning card, and one key dismisses it", async ({
  page,
}) => {
  await page.addInitScript(() =>
    localStorage.setItem("wetrun_tutorial_completed", "true"),
  );
  await page.goto("./");
  await page.waitForFunction(
    () => (window as unknown as { wetrun?: unknown }).wetrun !== undefined,
  );

  // The shared helpers pre-mark the beats; this spec wants one of them armed,
  // so it clears the flag after the run is launched and before the fight.
  await openMissionSelect(page);
  await launchRun(page);
  await page.evaluate(() => localStorage.removeItem("wetrun_beat_first_fight"));
  await gotoEncounterDecision(page);

  // Standing in front of the ICE, nothing has spoken yet.
  expect(await beatCard(page)).toBeNull();

  // BREACH opens the fight; the fight itself starts on the next key, and that
  // is the moment the construct speaks (runPhase combat, phase approach →
  // combat).
  await chooseEncounterVerb(page, "BREACH");
  await page.keyboard.press("Enter");
  await expect.poll(() => beatCard(page), { timeout: 5000 }).not.toBeNull();
  const card = await beatCard(page);
  expect(card?.title).toBe("ICE AHEAD");
  expect(card?.lines.join(" ")).toContain("already awake");

  // The next key dismisses it and never brings it back.
  await page.keyboard.press("Enter");
  await expect.poll(() => beatCard(page)).toBeNull();
});

test("a flatline gets the construct's last word", async ({ page }) => {
  await page.addInitScript(() =>
    localStorage.setItem("wetrun_tutorial_completed", "true"),
  );
  await page.goto("./");
  await page.waitForFunction(
    () => (window as unknown as { wetrun?: unknown }).wetrun !== undefined,
  );

  await openMissionSelect(page);
  await launchRun(page);
  await gotoEncounterDecision(page);
  await chooseEncounterVerb(page, "BREACH");
  await page.keyboard.press("Enter"); // approach -> combat
  await expect
    .poll(() =>
      page.evaluate(() =>
        (window as unknown as { wetrun: { getPhase(): string | null } }).wetrun.getPhase(),
      ),
    )
    .toBe("combat");

  // ADR-0317 3b: the construct warned that she can only watch. Make the death
  // certain — one point of HP, and an ICE that will not fall first.
  await page.evaluate(() => {
    const game = (
      window as unknown as {
        wetrun: {
          state: {
            player: Record<string, unknown>;
            iceRoster: Record<string, unknown>[];
          } | null;
        };
      }
    ).wetrun;
    const s = game.state;
    if (!s) return;
    game.state = {
      ...s,
      player: { ...s.player, hp: 1 },
      iceRoster: s.iceRoster.map((ice) => ({ ...ice, hp: 9999 })),
    };
  });
  for (let i = 0; i < 14; i += 1) {
    const phase = await page.evaluate(
      () =>
        (window as unknown as { wetrun: { state?: { runPhase?: string } | null } })
          .wetrun.state?.runPhase,
    );
    if (phase === "dead") break;
    // The enemy acts once per player action (ADR-0280), so this has to be a
    // real action — ENTER in combat is a no-op and the ICE never swings.
    await page.keyboard.press(String((i % 5) + 1));
    await page.waitForTimeout(150);
  }

  const card = await beatCard(page);
  expect(card?.title).toBe("FLATLINE");
  expect(card?.lines.join(" ")).toContain("I'm sorry");
});

