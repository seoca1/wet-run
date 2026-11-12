/**
 * ADR-0311 — the tier-6 unique is picked, not dealt.
 *
 * ADR-0309 made the axis reachable by handing over one unique on a tier-6 win,
 * but the runner never saw the three answers ADR-0303 designed: the first one in
 * the fight's offer was added automatically. The pick is now a free sub-phase of
 * the loot screen (Jev Choice: loot_subphase, p=1.0), so the stop is still fully
 * available afterwards.
 *
 * One per run: once a unique is owned there is nothing to re-offer, which also
 * makes a reload after the pick safe.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  loadIceCatalog,
  loadProgramsCatalog,
} from "../src/core/data_loaders";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { startingDeck } from "../src/core/state/starting_deck";
import { resolveVictory } from "../src/core/combat/victory";
import {
  UNIQUE_PROGRAMS,
  uniqueChoicesFor,
} from "../src/core/state/card_reward";
import type { GameState } from "../src/core/types";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

const ice = loadIceCatalog(iceJson);
const programs = loadProgramsCatalog(programsJson);

/** A state whose current node holds a defeated ICE of `tier`. */
function wonFight(tier: number, terminal: boolean): GameState {
  const mission = {
    id: "adr0311-mission",
    title: "ADR 0311 mission",
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

function win(state: GameState): GameState {
  return resolveVictory(state, {
    defeated: [state.iceRoster[0] as never],
    drops: [],
    kind: "program",
  });
}

function ownedUniques(state: GameState): number {
  return [...state.deck, ...state.drawPile, ...state.discardPile].filter((p) =>
    UNIQUE_PROGRAMS.has(p.id),
  ).length;
}

describe("ADR-0311 · the unique pick", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.3);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("offers all three answers on a tier-6 win and adds nothing yet", () => {
    // Given / When: a non-terminal tier-6 win.
    const won = win(wonFight(6, false));

    // Then: the pick is open over every unique, and victory itself granted none.
    expect(uniqueChoicesFor(won)).toEqual([...UNIQUE_PROGRAMS]);
    expect(ownedUniques(won)).toBe(0);
    expect(won.runPhase).toBe("loot");
    expect(won.cardRewardTaken).toBeFalsy();
  });

  it("taking one adds it and leaves the loot stop available", () => {
    // Given
    const won = win(wonFight(6, false));

    // When: slot 1 (ghost_key in catalog order).
    const picked = applyAction(won, { type: "select_program", handIndex: 1 });

    // Then: the card is owned, the pick is closed, and the stop is untouched.
    expect(ownedUniques(picked)).toBe(1);
    expect(picked.uniquePickDone).toBe(true);
    expect(picked.cardRewardTaken).toBeFalsy();
    expect(picked.runPhase).toBe("loot");
    expect(uniqueChoicesFor(picked)).toEqual([]);
  });

  it("ENTER skips the pick and grants nothing", () => {
    // Given
    const won = win(wonFight(6, false));

    // When
    const skipped = applyAction(won, { type: "confirm" });

    // Then
    expect(ownedUniques(skipped)).toBe(0);
    expect(skipped.uniquePickDone).toBe(true);
    expect(skipped.runPhase).toBe("loot");
  });

  it("does not open below the top band", () => {
    // Given / When: a tier-5 win.
    const won = win(wonFight(5, false));

    // Then
    expect(uniqueChoicesFor(won)).toEqual([]);
    expect(ownedUniques(won)).toBe(0);
  });

  it("does not open on the terminal win — the run is over", () => {
    // Given / When
    const won = win(wonFight(6, true));

    // Then
    expect(uniqueChoicesFor(won)).toEqual([]);
  });

  it("does not hand out a second unique in the same run", () => {
    // Given: a run that already took one.
    const picked = applyAction(win(wonFight(6, false)), {
      type: "select_program",
      handIndex: 1,
    });

    // When: it wins another tier-6 fight.
    const second = win({
      ...picked,
      runPhase: "combat",
      phase: "combat",
      iceRoster: [{ ...(picked.iceRoster[0] as never as object), tier: 6, hp: 0 } as never],
    });

    // Then: the pick re-opens only for a run with no answer yet.
    expect(selectedUniquePickDone(second)).toBe(false);
    expect(uniqueChoicesFor(second)).toEqual([]);
    expect(ownedUniques(second)).toBe(1);
  });
});

/** `uniquePickDone: false` is written by victory; read it without narrowing. */
function selectedUniquePickDone(state: GameState): boolean | undefined {
  return state.uniquePickDone;
}
