/**
 * ADR-0319 — a won fight heals the body on its own.
 *
 * The measurement that motivated this: the same run, played twice, differing
 * only in what the loot stop is spent on, completes g5 26.9% of the time when
 * the runner repairs and 4.3% when it always takes the card. So whether a run
 * lived was mostly whether the player knew to spend growth on HP. That made the
 * recovery a hidden requirement rather than a choice, and the stop could not be
 * about growth while it was also the only way to stay alive.
 *
 * The recovery is a FLOOR, not a grant: the runner comes out of a fight at
 * least `VICTORY_HEAL_PCT_BY_GRADE` of the pool. A flat grant double-counted
 * with the repair slot and measured g4 at 99.7%.
 */
import { describe, expect, it } from "vitest";
import { loadIceCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import { makeInitialState } from "../src/core/state/state";
import { startingDeck } from "../src/core/state/starting_deck";
import { resolveVictory } from "../src/core/combat/victory";
import {
  VICTORY_HEAL_PCT_BY_GRADE,
  victoryHealAmount,
} from "../src/core/state/loot_choice";
import type { GameState } from "../src/core/types";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

const ice = loadIceCatalog(iceJson);
const programs = loadProgramsCatalog(programsJson);

/** A g4 state whose current node holds a defeated ICE. */
function wonFight(hp: number): GameState {
  const mission = {
    id: "adr0319-mission",
    title: "ADR 0319 mission",
    fixer: "test",
    zone: "surface",
    arc: 1,
    grade_min: 4,
    grade_max: 4,
    rewards: { credits: 100, materials: {} },
  } as const;
  const base = makeInitialState(
    mission,
    ice.goliath as never,
    startingDeck(programs, "novice"),
  );
  const foe = { ...(ice.goliath as never as object), tier: 4, hp: 0 } as never;
  return {
    ...base,
    runPhase: "combat",
    phase: "combat",
    currentNodeIndex: 0,
    iceRoster: [foe],
    player: { ...base.player, hp },
    matrix: {
      startNode: 0,
      bossNode: 1,
      grade: 4,
      nodes: [
        {
          id: 0,
          zone: "mid",
          iceIds: ["goliath"],
          iceHp: [40],
          reward: { credits: 0 },
          adjacent: [1],
          isBoss: false,
        },
        {
          id: 1,
          zone: "core-deep",
          iceIds: ["wisp"],
          iceHp: [4],
          reward: { credits: 0 },
          adjacent: [0],
          isBoss: true,
        },
      ],
    },
  } as GameState;
}

function win(state: GameState): GameState {
  return resolveVictory(state, {
    defeated: [state.iceRoster[0] as never],
    drops: [],
    kind: "program",
  });
}

describe("ADR-0319 · the fight's own recovery", () => {
  it("pays only up to the floor", () => {
    // A floor, not a grant: it stops paying once the body is at the floor.
    expect(victoryHealAmount(100, 20, 3)).toBe(30);
    expect(victoryHealAmount(100, 49, 3)).toBe(1);
    expect(victoryHealAmount(100, 50, 3)).toBe(0);
    expect(victoryHealAmount(100, 80, 3)).toBe(0);
  });

  it("scales with the pool, not the grade", () => {
    expect(victoryHealAmount(200, 10, 3)).toBe(90);
    expect(victoryHealAmount(60, 10, 3)).toBe(20);
  });

  it("never pushes past full", () => {
    expect(victoryHealAmount(100, 100, 3)).toBe(0);
    expect(victoryHealAmount(100, 0, 3)).toBe(50);
  });

  it("has a floor for every grade", () => {
    for (let grade = 1; grade <= 6; grade += 1) {
      expect(VICTORY_HEAL_PCT_BY_GRADE[grade - 1]).toBeGreaterThan(0);
    }
  });

  it("brings a hurt runner up to the floor after a won fight", () => {
    const healed = win(wonFight(12));
    // g4, so the floor is 50% of the pool.
    expect(healed.player.hp).toBe(Math.floor(healed.player.maxHp * 0.5));
  });

  it("never heals a runner past full", () => {
    const healed = win(wonFight(100));
    expect(healed.player.hp).toBeLessThanOrEqual(healed.player.maxHp);
    expect(healed.player.hp).toBeGreaterThanOrEqual(100);
  });

  it("says the recovery out loud", () => {
    // A number the player never sees is a number the player cannot learn from.
    expect(win(wonFight(12)).message).toContain("recovered +");
    expect(win(wonFight(100)).message).not.toContain("recovered +");
  });
});
