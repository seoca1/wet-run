/**
 * ADR-0320 — the effective damage is on screen, and the armor is a number.
 *
 * The problem this answers: a card's damage is `tier * 5` MINUS the ICE's flat
 * armor, so the same card is worth wildly different amounts depending on what it
 * hits — `strike` is 4-5 against bare ICE and 1 against armor 9. None of that was
 * visible, so the deck's growth was invisible and armor was a rule the player
 * could not see. The hand now states the range, the ICE shows its armor, and a
 * play the armor ate renders as a clang rather than as a hit.
 */
import { afterEach, describe, expect, it } from "vitest";
import { loadIceCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import { makeInitialState } from "../src/core/state/state";
import { startingDeck } from "../src/core/state/starting_deck";
import { useProgram } from "../src/core/combat/state_actions_programs";
import {
  effectiveDamageFor,
  formatDamageRange,
} from "../src/core/combat/damage_preview";
import {
  formatAffordanceRow,
  programAffordances,
} from "../src/core/combat/program_affordance";
import { renderGrid } from "../src/renderer/combat_grid";
import { pickProgramVfxKind } from "../src/core/state/state_helpers";
import { shakeStateFor } from "../src/renderer/screen_shake";
import { composeCombatScreen, renderCombatScreen } from "../src/renderer/run_screen";
import { triggerCombatVfxMs } from "../src/renderer/combat_vfx_core";
import type { GameState, Ice, Program } from "../src/core/types";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

const ice = loadIceCatalog(iceJson);
const programs = loadProgramsCatalog(programsJson);

const originalRandom = Math.random;
afterEach(() => {
  Math.random = originalRandom;
});

/** A combat state whose hand is `ids`, pointed at an ICE with `armor`. */
function combatState(ids: readonly string[], armor: number): GameState {
  const mission = {
    id: "adr0320",
    title: "ADR 0320",
    fixer: "test",
    zone: "surface",
    arc: 1,
    grade_min: 5,
    grade_max: 5,
    rewards: { credits: 0, materials: {} },
  } as const;
  const base = makeInitialState(
    mission,
    ice.neuromancer as never,
    startingDeck(programs, "novice"),
  );
  const foe = {
    ...(ice.neuromancer as never as object),
    id: "foe",
    name: "FOE",
    tier: 5,
    hp: 900,
    maxHp: 900,
    armor,
  } as never;
  return {
    ...base,
    runPhase: "combat",
    phase: "combat",
    currentNodeIndex: 0,
    playerCombo: 0,
    iceRoster: [foe],
    ice: foe,
    deck: ids.map((id) => programs[id] as Program),
  } as GameState;
}

/** Play the first card with the roll pinned, and return the HP the ICE lost. */
function dealtDamage(state: GameState, roll: number): number {
  let calls = 0;
  // First draw = the variance roll; everything after (crit, status procs) is
  // pinned high so nothing else fires.
  Math.random = () => {
    calls += 1;
    return calls === 1 ? roll : 0.999;
  };
  const before = state.iceRoster[0]?.hp ?? 0;
  const after = useProgram(state, state.deck[0]!.id);
  return before - (after.iceRoster[0]?.hp ?? 0);
}

describe("ADR-0320 · effective damage is after armor", () => {
  const state = combatState(["strike"], 0);

  it("shows the tier-1 card falling to the floor against heavy armor", () => {
    const bare = effectiveDamageFor(state, programs.strike as Program, {
      armor: 0,
    } as Ice);
    const plated = effectiveDamageFor(state, programs.strike as Program, {
      armor: 9,
    } as Ice);
    expect(formatDamageRange(bare)).toBe("4-6");
    // The floor is 1, not 0: `calculateDamage` clamps there. The point is that
    // it is a WASTED play, and the row says so.
    expect(formatDamageRange(plated)).toBe("1");
    expect(plated.blocked).toBe(true);
  });

  it("ranks the deck by what it does to the same target", () => {
    const foe = { armor: 9 } as Ice;
    const strike = effectiveDamageFor(state, programs.strike as Program, foe);
    const goliath = effectiveDamageFor(state, programs.goliath as Program, foe);
    const kraken = effectiveDamageFor(state, programs.kraken as Program, foe);
    const unique = effectiveDamageFor(
      state,
      programs.ghost_key as Program,
      foe,
    );
    expect(strike.max).toBeLessThan(goliath.min);
    expect(goliath.max).toBeLessThan(kraken.min);
    expect(kraken.max).toBeLessThan(unique.min);
  });

  it("gives exploit the armor answer (half of it ignored)", () => {
    const foe = { armor: 9 } as Ice;
    const exploit = effectiveDamageFor(state, programs.exploit as Program, foe);
    expect(exploit.armor).toBe(9);
    expect(exploit.effectiveArmor).toBe(4);
    expect(exploit.blocked).toBe(false);
    // It beats the same-tier plain attack, which is the whole point of the card.
    const goliath = effectiveDamageFor(state, programs.goliath as Program, foe);
    expect(exploit.min).toBeGreaterThan(goliath.min);
  });

  it("counts the combo the play will make", () => {
    const foe = { armor: 9 } as Ice;
    const solo = effectiveDamageFor(state, programs.kraken as Program, foe);
    const chained = effectiveDamageFor(
      { ...state, playerCombo: 5 },
      programs.kraken as Program,
      foe,
    );
    // COMBO_BONUSES: 1 -> 1.0, 6 -> 3.0.
    expect(chained.min).toBeGreaterThan(solo.max);
  });
});

describe("ADR-0320 · the range is not a guess", () => {
  it("contains every roll the reducer can produce", () => {
    for (const armor of [0, 4, 7, 9]) {
      for (const id of ["strike", "exploit", "goliath", "kraken"]) {
        const state = combatState([id], armor);
        const preview = effectiveDamageFor(
          state,
          programs[id] as Program,
          state.iceRoster[0] as Ice,
        );
        for (const roll of [0, 0.5, 0.999]) {
          const dealt = dealtDamage(state, roll);
          expect(dealt, `${id} @armor ${armor} roll ${roll}`).toBeGreaterThanOrEqual(
            preview.min,
          );
          expect(dealt, `${id} @armor ${armor} roll ${roll}`).toBeLessThanOrEqual(
            preview.max,
          );
        }
      }
    }
  });
});

describe("ADR-0320 · the screen shows it", () => {
  it("puts the damage in the hand row", () => {
    const state = combatState(["strike", "kraken"], 9);
    const rows = programAffordances(state, state.iceRoster[0] as Ice);
    expect(formatAffordanceRow(rows[0]!)).toContain(" 1 ");
    expect(formatAffordanceRow(rows[0]!)).toContain("TARGET ICE");
    expect(formatAffordanceRow(rows[1]!)).toMatch(/1[1-9]-\d\d/);
  });

  it("leaves the row alone when there is no target (the loot offer)", () => {
    const state = combatState(["strike"], 9);
    expect(formatAffordanceRow(programAffordances(state)[0]!)).toBe(
      "1 STRIKE    COST +1             TARGET ICE",
    );
  });

  it("puts the armor on the ICE's name line", () => {
    const grid = renderGrid(combatState(["strike"], 9), null, null, [], 80, 50);
    const text = grid.cells.map((r) => r.map((c) => c.char).join("")).join("\n");
    expect(text).toContain("A9");
  });
});

describe("ADR-0320 · the hit is felt", () => {
  it("renders a blocked play as a clang, not as a hit", () => {
    const blocked = pickProgramVfxKind(
      { tier: 1, role: "strike" },
      1,
    );
    const landed = pickProgramVfxKind({ tier: 1, role: "strike" }, 4);
    expect(blocked).toBe("armor_block");
    expect(landed).not.toBe("armor_block");
  });

  it("does not call a defensive card blocked", () => {
    expect(pickProgramVfxKind({ tier: 3, role: "guard" }, 1)).not.toBe(
      "armor_block",
    );
    expect(pickProgramVfxKind({ tier: 2, role: "support" }, 1)).not.toBe(
      "armor_block",
    );
  });

  it("puts the clang on the screen", () => {
    const state = combatState(["strike"], 9);
    const base = renderCombatScreen(
      { state, iceDelta: null, playerDelta: null },
      80,
      50,
    );
    const withVfx = {
      ...state,
      grid: base,
      vfxInstances: [
        triggerCombatVfxMs("armor_block", "STRIKE", 140, undefined, undefined, 1),
      ],
    };
    const view = composeCombatScreen(withVfx as never, false);
    const text = view.grid.cells
      .map((r) => r.map((c) => c.char).join(""))
      .join("\n");
    expect(text).toContain("ARMOR");
  });

  it("shakes the canvas for a big hit the player landed", () => {
    const big = triggerCombatVfxMs("ice_hit", "", 160, undefined, undefined, 41);
    expect(shakeStateFor([big]).magnitudePx).toBeGreaterThan(0);
    const small = triggerCombatVfxMs("ice_hit", "", 160, undefined, undefined, 6);
    expect(shakeStateFor([small])).toEqual({ x: 0, y: 0, magnitudePx: 0 });
  });

  it("does not shake on a blocked play", () => {
    const blocked = triggerCombatVfxMs(
      "armor_block",
      "STRIKE",
      140,
      undefined,
      undefined,
      1,
    );
    expect(shakeStateFor([blocked])).toEqual({ x: 0, y: 0, magnitudePx: 0 });
  });
});
