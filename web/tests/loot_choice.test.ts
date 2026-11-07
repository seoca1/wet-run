/**
 * ADR-0282 — recovery is a choice on the loot screen, not a tax on the clock.
 *
 * Before this the loot screen gave a card offer AND healed automatically, so
 * ENTER skipped a card and the runner healed anyway. The screen is now a spend:
 * slots 1-3 take a program, 4 repairs, 5 takes the credits, and ENTER takes
 * nothing and travels on.
 *
 * The two tests below used to pin the automatic heal; they now pin the choice.
 */
import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { breachEncounter } from "./encounter_test_helpers";
import missionsData from "../src/data/missions.json";
import iceTypesData from "../src/data/ice_types.json";
import programsData from "../src/data/programs.json";
import type { Program, Ice, GameState } from "../src/core/types";
import {
  LOOT_REPAIR_SLOT,
  lootRepairAmount,
  lootSlotChoice,
} from "../src/core/state/loot_choice";
import { missionGradeOf } from "../src/core/combat/ice_scaling";

function loadDeck(programs: Record<string, Program>): Program[] {
  const ids = Object.keys(programs).sort().slice(0, 5);
  return ids
    .map((id) => {
      const p = programs[id];
      if (!p) return undefined;
      const apCost = (p as unknown as { ap_cost?: number }).ap_cost;
      return {
        ...p,
        id,
        ...(apCost !== undefined && p.cost === undefined ? { cost: apCost } : {}),
      } as Program;
    })
    .filter((p): p is Program => p !== undefined);
}

/** A run parked on a non-terminal loot screen, at `hp`. */
function atLoot(hp: number): GameState {
  const mission = Object.values(missionsData)[0]!;
  const ice = Object.values(iceTypesData as unknown as Record<string, Ice>)[0]!;
  const programs = programsData as unknown as Record<string, Program>;
  let state = makeInitialState(mission as never, ice as never, loadDeck(programs));
  state = { ...state, currentNodeIndex: 1 };
  state = breachEncounter(state);
  state = applyAction(state, { type: "confirm" });
  state = {
    ...state,
    iceRoster: state.iceRoster.map((i) => ({ ...i, hp: 0 })),
    player: { ...state.player, hp },
  };
  state = applyAction(state, {
    type: "use_program",
    programId: state.deck[0]?.id ?? "strike",
  });
  if (state.runPhase !== "loot") throw new Error("fixture did not reach loot");
  return state;
}

const MISSION = Object.values(missionsData)[0]!;
const GRADE = missionGradeOf(MISSION as never);

describe("ADR-0282 — the loot screen is a spend", () => {
  it("ENTER takes nothing: no card, no heal", () => {
    // Given: a hurt runner on a loot screen.
    const loot = atLoot(50);
    expect(loot.player.hp).toBe(50);

    // When: ENTER travels on.
    const moved = applyAction(loot, { type: "confirm" });

    // Then: the HP is untouched — recovery is not automatic any more.
    expect(moved.runPhase).toBe("matrix");
    expect(moved.player.hp).toBe(50);
    expect(moved.cardRewardTaken).toBeNull();
  });

  it("slot 4 spends the stop on a repair, sized by the grade", () => {
    // Given
    const loot = atLoot(50);

    // When
    const moved = applyAction(loot, {
      type: "select_program",
      handIndex: LOOT_REPAIR_SLOT,
    });

    // Then
    const expected = Math.min(
      loot.player.maxHp,
      50 + lootRepairAmount(loot.player.maxHp, GRADE),
    );
    expect(moved.runPhase).toBe("matrix");
    expect(moved.player.hp).toBe(expected);
    // A repair is not a card.
    expect(moved.cardRewardTaken).toBeNull();
    expect(moved.inventory.programs).toHaveLength(loot.inventory.programs.length);
  });

  it("repair is capped at maxHp", () => {
    // Given: a nearly full runner.
    const loot = atLoot(Math.floor(loot0MaxHp() * 0.95));

    // When
    const moved = applyAction(loot, {
      type: "select_program",
      handIndex: LOOT_REPAIR_SLOT,
    });

    // Then
    expect(moved.player.hp).toBe(loot.player.maxHp);
  });

  it("has no fifth option: a third stop was measured and removed (ADR-0285)", () => {
    // The slot that once paid credits, then patched, is gone — three cards and a
    // repair only, because a third stop could not be made competitive.

    // Then: the fifth key is not a loot option, so it falls through to
    // `takeCardReward` and simply finds no offer there.
    expect(lootSlotChoice(5)).toBeNull();
    expect(lootSlotChoice(4)).toBe("repair");
    expect(lootSlotChoice(3)).toBe("program");
  });

  it("slots 1-3 still take a program and hold the screen (ADR-0261)", () => {
    // Given
    const loot = atLoot(50);

    // When
    const taken = applyAction(loot, { type: "select_program", handIndex: 1 });

    // Then: still on the loot screen with the card recorded, as before.
    expect(taken.runPhase).toBe("loot");
    expect(taken.cardRewardTaken).not.toBeNull();
    expect(taken.inventory.programs).toHaveLength(
      loot.inventory.programs.length + 1,
    );
  });
});

function loot0MaxHp(): number {
  return atLoot(50).player.maxHp;
}
