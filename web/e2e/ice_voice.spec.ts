/**
 * ADR-0317 (3b) — probing an ICE remembers its tagline for the profile.
 *
 * The tagline is spoken once. The moment that makes it "heard" is the reveal
 * (PROBE/SCAN), because that is when the runner sees what the ICE is — the
 * screen only speaks it after that, so the identity is never given away free.
 * This spec pins the remembering, which is the part the unit tests cannot see.
 */
import { test, expect } from "@playwright/test";
import { chooseEncounterVerb, gotoEncounterDecision, launchRun, openMissionSelect } from "./menu-nav";

test.describe.configure({ timeout: 90_000 });

const SEEN_KEY = "wetrun_ice_intro_seen";

test("the reveal is what remembers the ICE tagline", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("wetrun_tutorial_completed", "true");
    localStorage.removeItem("wetrun_ice_intro_seen");
  });
  await page.goto("./");
  await page.waitForFunction(
    () => (window as unknown as { wetrun?: unknown }).wetrun !== undefined,
  );

  await openMissionSelect(page);
  await launchRun(page);
  await gotoEncounterDecision(page);

  // Standing in front of the ICE, nothing has been heard yet.
  expect(await page.evaluate((k) => localStorage.getItem(k), SEEN_KEY)).toBeNull();

  // PROBE reveals the ICE, and the reveal is what records its tagline.
  await chooseEncounterVerb(page, "PROBE");
  await expect
    .poll(() => page.evaluate((k) => localStorage.getItem(k), SEEN_KEY))
    .not.toBeNull();

  const seen = await page.evaluate(
    (k) => JSON.parse(localStorage.getItem(k) ?? "[]") as string[],
    SEEN_KEY,
  );
  expect(seen.length).toBeGreaterThan(0);
});
