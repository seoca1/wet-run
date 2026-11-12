/**
 * ADR-0309 — the tier-6 unique is handed over outside the loot stop.
 *
 * ADR-0307 (a) measured the g6 growth axis as unreachable rather than saturated:
 * the unique was offered at every tier-6 fight (65 of 65) and taken in 1 of 96
 * runs, because the single loot stop belongs to the repair (ADR-0305/0306).
 *
 * The rule now grants one unique on a non-terminal tier-6 win, deterministically
 * (the first unique the fight's own offer names), with no `Math.random` consumed
 * and no cost to the stop. Measured effect: g6 completion 11.5% -> 34.9% at 64
 * seeds, g1-g5 within 0.9pp.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  loadIceCatalog,
  loadProgramsCatalog,
} from "../src/core/data_loaders";
import { makeInitialState } from "../src/core/state/state";
import { startingDeck } from "../src/core/state/starting_deck";
import { resolveVictory } from "../src/core/combat/victory";
import { UNIQUE_PROGRAMS } from "../src/core/state/card_reward";
import type { GameState } from "../src/core/types";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

const ice = loadIceCatalog(iceJson);
const programs = loadProgramsCatalog(programsJson);

/** A state whose current node holds a defeated ICE of `tier` at `nodeIndex`. */
function wonFight(tier: number, terminal: boolean, turn = 0): GameState {
  const mission = {
    id: "adr0309-mission",
    title: "ADR 0309 mission",
    fixer: "test",
    zone: "surface",
    arc: 1,
    grade_min: 6,
    grade_max: 6,
    rewards: { credits: 100, materials: {} },
  } as const;
  const base = makeInitialState(
    mission,
    ice.aleph as never,
    startingDeck(programs, "novice"),
  );
  const foe = { ...(ice.aleph as never as object), tier, hp: 0 } as never;
  return {
    ...base,
    runPhase: "combat",
    phase: "combat",
    currentNodeIndex: 0,
    turnCount: turn,
    iceRoster: [foe],
    matrix: {
      startNode: 0,
      bossNode: terminal ? 0 : 1,
      grade: 6,
      nodes: [
        {
          id: 0,
          zone: "mid",
          iceIds: ["aleph"],
          iceHp: [40],
          reward: { credits: 0 },
          adjacent: [1],
          isBoss: terminal,
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

/** Win the fight at the current node. */
function win(state: GameState): GameState {
  return resolveVictory(state, {
    defeated: [state.iceRoster[0] as never],
    drops: [],
    kind: "program",
  });
}

describe("ADR-0309 · the g6 unique is outside the loot stop", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.3);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("grants a unique when a tier-6 fight is won", () => {
    // Given: a non-terminal win over a tier-6 ICE whose offer names a unique
    // (the grant follows the fight's own find — ADR-0303's "a find, not a flood").
    let won: GameState | null = null;
    for (let turn = 0; turn < 80 && won === null; turn += 1) {
      const candidate = win(wonFight(6, false, turn));
      if (candidate.drawPile.some((p) => UNIQUE_PROGRAMS.has(p.id))) {
        won = candidate;
      }
    }
    expect(won).not.toBeNull();

    // Then: the unique is in the draw pile and the inventory, and the run still
    // stands on the loot screen — the stop was not spent on it.
    const granted = won!.drawPile.find((p) => UNIQUE_PROGRAMS.has(p.id));
    expect(granted).toBeDefined();
    expect(won!.inventory.programs.some((p) => p.id === granted?.id)).toBe(true);
    expect(won!.runPhase).toBe("loot");
    expect(won!.cardRewardTaken).toBeFalsy();
  });

  it("grants nothing below the top band", () => {
    // Given: a tier-5 win — every g1-g5 fight.
    const before = wonFight(5, false);
    const won = win(before);

    // Then: the draw pile is untouched and nothing is announced.
    expect(won.drawPile.some((p) => UNIQUE_PROGRAMS.has(p.id))).toBe(false);
    expect(won.inventory.programs).toEqual(before.inventory.programs);
    expect(won.message).not.toContain("unique");
  });

  it("grants nothing on the terminal win — the run is over", () => {
    // Given: the exit room.
    const won = win(wonFight(6, true));

    // Then
    expect(won.drawPile.some((p) => UNIQUE_PROGRAMS.has(p.id))).toBe(false);
  });

  it("names the same unique on a reload — no extra randomness", () => {
    // Given / When: the same fight twice, at the turn whose offer names one.
    let turn = 0;
    while (
      turn < 80 &&
      !win(wonFight(6, false, turn)).drawPile.some((p) =>
        UNIQUE_PROGRAMS.has(p.id),
      )
    ) {
      turn += 1;
    }
    const a = win(wonFight(6, false, turn));
    const b = win(wonFight(6, false, turn));

    // Then: the grant is a pure function of the fight.
    expect(a.drawPile.map((p) => p.id)).toEqual(b.drawPile.map((p) => p.id));
  });
});
