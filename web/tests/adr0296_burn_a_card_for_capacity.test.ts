/**
 * ADR-0296 — the trace can also be paid for with growth.
 *
 * ADR-0295 gave the trace an exit paid in HP, and measured that a CHEAP exit
 * undoes ADR-0294's trade. A card costs something the fitted curve never reads —
 * growth — so burning one is a third currency, and the most game-shaped price of
 * the three: you give up a program that would have helped later for capacity now.
 *
 * Both the target and the amount came out of measurement, and the intuitive choice
 * was wrong twice:
 *   - burning the WEAKEST card is a free lunch (g5 50.5 vs 43.3, g6 20.8 vs 13.9)
 *     because the weakest program was never going to be played;
 *   - at the vent's full 10 COST, even burning the strongest left fighting ahead
 *     by 4.2pp at g6.
 * Burning the STRONGEST for 7 lands the trade (g5 44.7/43.3, g6 11.8/13.9).
 */
import { describe, expect, it } from "vitest";
import { BURN_COST, LOOT_BURN_SLOT } from "../src/core/state/loot_choice";
import { burnTarget } from "../src/core/state/state_actions_phases";
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

function atLoot(alarm: number, deckSize = 5): GameState {
  const mission = Object.values(missions).find((m) => m.id === "first_jack");
  const base = makeInitialState(
    mission as never,
    Object.values(ice)[0] as never,
    startingDeck(programs, "novice"),
  );
  const kept = base.deck.slice(0, deckSize);
  return {
    ...base,
    runPhase: "loot",
    phase: "victory",
    message: "No rewards",
    currentNodeIndex: 0,
    deck: kept,
    drawPile: [],
    discardPile: [],
    player: { ...base.player, alarm, credits: 0 },
    clearedEncounterNodes: [0],
  };
}

function burn(state: GameState): GameState {
  return applyAction(state, {
    type: "select_program",
    handIndex: LOOT_BURN_SLOT,
  });
}

describe("ADR-0296 · burning a card for capacity", () => {
  it("takes the card the run would miss, not the one it would not", () => {
    // Given: a deck of mixed tiers.
    const state = atLoot(80);
    const target = burnTarget(state);
    expect(target).not.toBeNull();
    if (!target) return;
    const highest = Math.max(...state.deck.map((c) => c.tier));

    // Then: the target is one of the strongest programs, so the price is real.
    expect(target.tier).toBe(highest);
  });

  it("removes it from the run and clears COST", () => {
    // Given
    const before = atLoot(80);
    const target = burnTarget(before)!;

    // When
    const after = burn(before);

    // Then: the card is gone and capacity came back.
    const ids = [...after.deck, ...after.drawPile, ...after.discardPile].map(
      (c) => c.id,
    );
    expect(ids).not.toContain(target.id);
    expect(after.player.alarm).toBe(80 - BURN_COST);
  });

  it("stays on the loot screen, so it does not also cost the card offer", () => {
    // Given / When
    const after = burn(atLoot(80));

    // Then: the stop is still open.
    expect(after.runPhase).toBe("loot");
    expect(after.cardRewardTaken ?? null).toBeNull();
  });

  it("refuses to burn the last program", () => {
    // Given: a one-card deck.
    const before = atLoot(90, 1);

    // When
    const after = burn(before);

    // Then: nothing is spent — a run with no cards cannot play.
    expect(after.deck).toHaveLength(1);
    expect(after.player.alarm).toBe(90);
    expect(after.message).toContain("Nothing to burn");
  });

  it("never clears more COST than the runner carries", () => {
    // Given: a small trace.
    const after = burn(atLoot(3));

    // Then
    expect(after.player.alarm).toBe(0);
  });
});
