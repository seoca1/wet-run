import { expect, test } from "@playwright/test";
import { enterForScreen, gotoIceNode } from "./menu-nav";
import type { GameState } from "../src/core/types";

declare global {
  interface Window {
    readonly wetrun?: { readonly state: GameState | null };
  }
}

test.beforeEach(async ({ page }) => {
  await page.clock.install({ time: new Date("2026-11-01T00:00:00Z") });
  await page.addInitScript(() =>
    localStorage.setItem("wetrun_tutorial_completed", "true"),
  );
  await page.goto("./");
  await page.waitForFunction(() => window.wetrun !== undefined);
  await page.clock.pauseAt(new Date("2026-11-01T00:01:00Z"));
  await enterForScreen(page, "mission_select");
  await page.keyboard.press("Enter");
  await gotoIceNode(page);
});

test("idle rAF dispatch raises alarm without directly attacking", async ({
  page,
}) => {
  // Given
  const before = await page.evaluate(() => ({
    alarm: window.wetrun?.state?.alarmLevel,
    hp: window.wetrun?.state?.player.hp,
    cards: window.wetrun?.state?.deck.length,
  }));
  expect(before.alarm).toBe(0);
  // When
  await page.clock.runFor(20_050);
  // Then
  const after = await page.evaluate(() => ({
    alarm: window.wetrun?.state?.alarmLevel,
    hp: window.wetrun?.state?.player.hp,
    cards: window.wetrun?.state?.deck.length,
  }));
  expect(after).toEqual({ ...before, alarm: 2 });
  expect(await page.evaluate(() => window.wetrun?.state?.message)).toBe(
    "TRACE 2/5",
  );
});

test("real input prevents alarm growth despite elapsed combat time", async ({
  page,
}) => {
  // Given
  expect(await page.evaluate(() => window.wetrun?.state?.alarmLevel)).toBe(0);
  // When
  for (let index = 0; index < 5; index++) {
    await page.clock.runFor(9000);
    await page.keyboard.press("Shift");
  }
  // Then
  expect(await page.evaluate(() => window.wetrun?.state?.alarmLevel)).toBe(0);
});
