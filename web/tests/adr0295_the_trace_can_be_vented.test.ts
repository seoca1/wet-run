/**
 * ADR-0295 — the trace can be vented, at a price that cannot buy the answer.
 *
 * ADR-0294 made every kill leave a trace worth its ICE's tier, which turned "how
 * much do I fight" into a trade. A cost with no way out is a trap, though: once
 * the budget is gone the runner can only watch. So the trace can be vented.
 *
 * The first design sold it for credits and the measurement killed it twice: cheap
 * (40cr/COST) it reopened the fight/skip lead at +5.5pp because money minted
 * capacity; expensive (190cr) it was never affordable, so it was dead weight. No
 * price balanced both g5 and g6.
 *
 * Paying in HP cannot inflate anything — it is a reallocation, body into capacity,
 * at a loss. 40% of max HP is measured: 15% reopens the lead (g6 31.7 vs 13.3),
 * 30% is +5.0, and 40% is +2.5 — an emergency valve, not a discount.
 *
 * The vent is a PURCHASE, not a loot pick: it stays on the screen, so it does not
 * also cost the card.
 */
import { describe, expect, it } from "vitest";
import {
  LOOT_VENT_SLOT,
  VENT_COST,
  VENT_HP_PCT,
  ventHpPrice,
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

function atLoot(alarm: number, hp = 300): GameState {
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
    player: { ...base.player, hp, maxHp: 300, alarm, credits: 0 },
    clearedEncounterNodes: [0],
  };
}

function vent(state: GameState): GameState {
  return applyAction(state, {
    type: "select_program",
    handIndex: LOOT_VENT_SLOT,
  });
}

describe("ADR-0295 · venting the trace", () => {
  it("clears COST and charges HP", () => {
    // Given: a runner at 70 COST with a full body.
    const before = atLoot(70);

    // When
    const after = vent(before);

    // Then: capacity comes back, paid for in HP.
    expect(after.player.alarm).toBe(70 - VENT_COST);
    expect(after.player.hp).toBe(
      before.player.hp - ventHpPrice(before.player.maxHp),
    );
  });

  it("stays on the loot screen, so it does not also cost the card", () => {
    // Given / When: a vent at a loot stop that still owes a card.
    const after = vent(atLoot(80));

    // Then: the stop is not spent — the card offer is still there.
    expect(after.runPhase).toBe("loot");
    expect(after.cardRewardTaken ?? null).toBeNull();
  });

  it("refuses to vent the body it needs to survive", () => {
    // Given: a runner whose HP is at or below the price.
    const price = ventHpPrice(300);
    const before = atLoot(90, price);

    // When
    const after = vent(before);

    // Then: nothing happens, and the screen says why.
    expect(after.player.alarm).toBe(90);
    expect(after.player.hp).toBe(price);
    expect(after.message).toContain("Venting costs");
  });

  it("never clears more COST than the runner carries", () => {
    // Given: a small trace.
    const before = atLoot(4);

    // When
    const after = vent(before);

    // Then: it floors at zero instead of going negative.
    expect(after.player.alarm).toBe(0);
  });

  it("prices the vent as a fraction of the body, not a flat sum", () => {
    // Given / When / Then: a bigger pool pays more for the same capacity, so the
    // vent does not get cheaper as the runner gets tougher.
    expect(ventHpPrice(100)).toBeLessThan(ventHpPrice(400));
    expect(VENT_HP_PCT).toBeGreaterThanOrEqual(40);
  });
});
