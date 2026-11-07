/**
 * ADR-0298 — a hot trace can be bled back into the body.
 *
 * ADR-0295 turned HP into COST; nothing turned the other way, so a runner who
 * banked capacity and then took a beating could only watch the budget go unused.
 * The mirror is a natural choice — and it is the one that nearly broke the trade.
 *
 * COST is surplus at the end of a fight-heavy run (55-74 of 100), so converting it
 * to HP is nearly free. Measured: at any price the reverse exchange made fighting
 * better, and a BIGGER heal made it better still (g5 47.5 -> 54.2 as the price
 * rose) — the tell that the "price" was not being paid. A once-per-run cap did not
 * fix it either (g6 9.0 against 13.9).
 *
 * What works is bounding it by the trace itself: the draw is only available when
 * the trace is hot enough to have spare pressure (COST >= 70). Then the trade
 * holds — g5 41.9 vs 43.3, g6 11.8 vs 13.9 — because the runner who still needs
 * the budget has not reached 70 in the first place.
 */
import { describe, expect, it } from "vitest";
import {
  LOOT_RECOVER_SLOT,
  RECOVER_COST,
  RECOVER_MIN_COST,
  recoverHpAmount,
} from "../src/core/state/loot_choice";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { startingDeck } from "../src/core/state/starting_deck";
import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import type { GameState } from "../src/core/types";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import missionsJson from "../src/data/missions.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

const ice = loadIceCatalog(iceJson);
const programs = loadProgramsCatalog(programsJson);
const missions = loadMissionsCatalog(missionsJson);

function atLoot(alarm: number, hp = 150): GameState {
  const mission = Object.values(missions).find((m) => m.id === "first_jack");
  const base = makeInitialState(
    mission as never,
    Object.values(ice)[0] as never,
    startingDeck(programs, "novice"),
  );
  return {
    ...base,
    runPhase: "loot",
    phase: "victory",
    message: "No rewards",
    currentNodeIndex: 0,
    player: { ...base.player, hp, maxHp: 300, alarm },
    clearedEncounterNodes: [0],
  };
}

function syphon(state: GameState): GameState {
  return applyAction(state, {
    type: "select_program",
    handIndex: LOOT_RECOVER_SLOT,
  });
}

describe("ADR-0298 · syphoning a hot trace", () => {
  it("returns body and spends capacity", () => {
    // Given: a hot trace and a beaten-up runner.
    const before = atLoot(80);

    // When
    const after = syphon(before);

    // Then
    expect(after.player.alarm).toBe(80 - RECOVER_COST);
    expect(after.player.hp).toBe(150 + recoverHpAmount(300));
  });

  it("refuses a cold trace — the runner who needs the budget keeps it", () => {
    // Given: plenty of COST but below the draw threshold.
    const before = atLoot(RECOVER_MIN_COST - 1);

    // When
    const after = syphon(before);

    // Then: nothing is spent, and the screen says why.
    expect(after.player.alarm).toBe(RECOVER_MIN_COST - 1);
    expect(after.player.hp).toBe(150);
    expect(after.message).toContain("too cold");
  });

  it("refuses when there is nothing to heal", () => {
    // Given: a full body and a hot trace.
    const before = atLoot(90, 300);

    // When
    const after = syphon(before);

    // Then: no point spending capacity on nothing.
    expect(after.player.alarm).toBe(90);
  });

  it("stays on the loot screen", () => {
    // Given / When
    const after = syphon(atLoot(80));

    // Then: it is a purchase, not the loot pick.
    expect(after.runPhase).toBe("loot");
    expect(after.cardRewardTaken ?? null).toBeNull();
  });

  it("cannot be cycled with the vent", () => {
    // Given: the two directions.
    // Then: venting 10 COST costs 40% HP and drawing 10 COST gives 25% back, so a
    // round trip always loses body — the exchange cannot be farmed.
    expect(recoverHpAmount(100)).toBeLessThan(40);
  });
});
