import { expect, test } from "@playwright/test";
import { parseProgram } from "../src/core/data_loaders";
import programs from "../src/data/programs.json" with { type: "json" };
import {
  chooseEncounterVerb,
  enterForScreen,
  gotoEncounterDecision,
} from "./menu-nav";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() =>
    localStorage.setItem("wetrun_tutorial_completed", "true"),
  );
  await page.goto("./");
  await page.waitForFunction(() => window.wetrun !== undefined);
  await enterForScreen(page, "mission_select");
  await page.keyboard.press("Enter");
  await gotoEncounterDecision(page);
});

test("paid PROBE reveals intel, then BYPASS forgoes loot and permits travel", async ({
  page,
}, testInfo) => {
  // Given
  const initial = await page.evaluate(() => {
    const s = window.wetrun?.state;
    return {
      node: s?.currentNodeIndex,
      cost: s?.player.alarm,
      credits: s?.player.credits,
      inventory: s?.inventory,
      hp: s?.player.hp,
    };
  });
  await page.keyboard.press("Enter");
  expect(
    await page.evaluate(
      () => window.wetrun?.state?.encounterDecision?.selectedVerb,
    ),
  ).toBeNull();
  await page.screenshot({ path: testInfo.outputPath("encounter-hidden.png") });
  // When
  await chooseEncounterVerb(page, "PROBE");
  expect(
    await page.evaluate(() => window.wetrun?.state?.encounterDecision?.probed),
  ).toBe(true);
  expect(await page.evaluate(() => window.wetrun?.state?.player.alarm)).toBe(
    (initial.cost ?? 0) + 8,
  );
  await page.screenshot({ path: testInfo.outputPath("encounter-probed.png") });
  await chooseEncounterVerb(page, "BYPASS");
  // Then
  const bypassed = await page.evaluate(() => {
    const s = window.wetrun?.state;
    return {
      node: s?.currentNodeIndex,
      cost: s?.player.alarm,
      credits: s?.player.credits,
      inventory: s?.inventory,
      hp: s?.player.hp,
      runPhase: s?.runPhase,
      cleared: s?.clearedEncounterNodes ?? [],
      decision: s?.encounterDecision,
    };
  });
  expect(bypassed).toEqual({
    ...initial,
    cost: (initial.cost ?? 0) + 38,
    runPhase: "matrix",
    cleared: [],
    decision: null,
  });
  await page.keyboard.press("ArrowDown");
  const destination = await page.evaluate(
    () => window.wetrun?.state?.selectedMatrixNodeIndex,
  );
  expect(destination).not.toBeNull();
  await page.keyboard.press("Enter");
  expect(
    await page.evaluate(() => window.wetrun?.state?.currentNodeIndex),
  ).toBe(destination);
  expect(destination).not.toBe(initial.node);
});

test("arrows expose all four fixed verbs and JACK OUT abandons the run", async ({
  page,
}) => {
  // Given / When / Then
  for (const verb of ["PROBE", "BYPASS", "BREACH", "JACK OUT"]) {
    await page.keyboard.press("ArrowRight");
    expect(
      await page.evaluate(
        () => window.wetrun?.state?.encounterDecision?.selectedVerb,
      ),
    ).toBe(verb);
  }
  await page.keyboard.press("ArrowLeft");
  expect(
    await page.evaluate(
      () => window.wetrun?.state?.encounterDecision?.selectedVerb,
    ),
  ).toBe("BREACH");
  await page.keyboard.press("ArrowRight");
  await page.keyboard.press("Enter");
  expect(await page.evaluate(() => window.wetrun?.state?.phase)).toBe("menu");
  expect(await page.evaluate(() => window.wetrun?.state?.message)).toBe(
    "Jacked out — run abandoned",
  );
  expect(
    await page.evaluate(() => window.wetrun?.state?.encounterDecision),
  ).toBeNull();
});

test("utility SCAN spends a real combat card and preserves fixed choices", async ({
  page,
}, testInfo) => {
  // Given
  const card = parseProgram(programs.scan, "scan");
  await page.evaluate((program) => {
    const game = window.wetrun;
    if (!game?.state) throw new Error("No run state");
    game.state = { ...game.state, deck: [program, ...game.state.deck] };
  }, card);
  const initial = await page.evaluate(() => ({
    cost: window.wetrun?.state?.player.alarm,
    hand: window.wetrun?.state?.deck.map((p) => p.id),
    discarded: window.wetrun?.state?.discardPile.map((p) => p.id),
  }));
  // When
  await page.keyboard.press("ArrowUp");
  expect(
    await page.evaluate(
      () => window.wetrun?.state?.encounterDecision?.selectedVerb,
    ),
  ).toBe("SCAN");
  await page.screenshot({
    path: testInfo.outputPath("program-scan-payment.png"),
  });
  await page.keyboard.press("Enter");
  // Then
  expect(
    await page.evaluate(() => ({
      cost: window.wetrun?.state?.player.alarm,
      hand: window.wetrun?.state?.deck.map((p) => p.id),
      discarded: window.wetrun?.state?.discardPile.map((p) => p.id),
      revealed: window.wetrun?.state?.encounterDecision?.probed,
    })),
  ).toEqual({
    ...initial,
    hand: initial.hand?.slice(1),
    discarded: [...(initial.discarded ?? []), "scan"],
    revealed: true,
  });
  await page.screenshot({
    path: testInfo.outputPath("program-scan-revealed.png"),
  });
  await page.keyboard.press("ArrowDown");
  expect(
    await page.evaluate(
      () => window.wetrun?.state?.encounterDecision?.selectedVerb,
    ),
  ).toBe("PROBE");
  await page.keyboard.press("Enter");
  expect(await page.evaluate(() => window.wetrun?.state?.player.alarm)).toBe(
    initial.cost,
  );
  await chooseEncounterVerb(page, "BREACH");
  await page.keyboard.press("Enter");
  expect(await page.evaluate(() => window.wetrun?.state?.phase)).toBe("combat");
  expect(
    await page.evaluate(() =>
      window.wetrun?.state?.deck.some((p) => p.id === "scan"),
    ),
  ).toBe(false);
});
