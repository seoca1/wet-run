/**
 * ADR-0278 regression tests — the play-through defect batch.
 *
 * Each test pins a defect found by playing the game in the browser:
 *
 *   1. `encounterRoster` cloned the mission's opening ICE and only swapped the
 *      id, so the boss room was fought as a 35 HP "Wisp" wearing the mission
 *      ICE's armor and skills. The roster now resolves the node's `iceIds`
 *      against the ICE catalog.
 *   2. The hand was not refilled between fights, so a card taken at the loot
 *      screen never reached the hand and a short run ended with the reward
 *      unseen. The hand is refilled when the loot screen closes.
 *   3. Two ICE rooms in one mission were the same ICE type, which made a
 *      mission read as one fight repeated.
 */
import { describe, expect, it } from "vitest";
import { parseProgram } from "../src/core/data_loaders";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { encounterRoster } from "../src/core/state/encounter_verbs";
import { refillHand } from "../src/core/combat/hand";
import { generateProceduralMatrix } from "../src/core/dungeon/matrix";
import type { GameState, Program } from "../src/core/types";
import programs from "../src/data/programs.json";
import { breachEncounter } from "./encounter_test_helpers";

const strike = parseProgram(programs.strike, "strike");
const scan = parseProgram(programs.scan, "scan");

const mission = {
  id: "adr0278-mission",
  title: "ADR 0278 mission",
  fixer: "test",
  zone: "surface",
  arc: 1,
  grade_min: 1,
  grade_max: 1,
  rewards: { credits: 0, materials: {} },
} as const;

/** A state parked on `nodeIndex` with the given matrix nodes. */
function stateAt(
  nodes: ReadonlyArray<{
    id: number;
    zone: string;
    iceIds: ReadonlyArray<string>;
    iceHp: ReadonlyArray<number>;
    reward: { credits: number };
    adjacent: ReadonlyArray<number>;
    isBoss: boolean;
  }>,
  nodeIndex: number,
  hand: ReadonlyArray<Program> = [strike],
): GameState {
  const initial = makeInitialState(mission, strike as never, hand);
  return {
    ...initial,
    currentNodeIndex: nodeIndex,
    matrix: {
      startNode: 0,
      bossNode: nodes.length - 1,
      grade: 1,
      nodes: nodes as never,
    },
  };
}

describe("ADR-0278 · encounter roster resolves the catalog", () => {
  it("gives the boss node the wintermute's own armor and tier", () => {
    // Given: a boss node that names `wintermute`.
    const state = stateAt(
      [
        {
          id: 0,
          zone: "core-deep",
          iceIds: ["wintermute"],
          iceHp: [],
          reward: { credits: 0 },
          adjacent: [],
          isBoss: true,
        },
      ],
      0,
    );

    // When
    const roster = encounterRoster(state);

    // Then: the catalog row's stats, not the mission ICE's.
    expect(roster).toHaveLength(1);
    expect(roster[0]?.id).toBe("wintermute");
    expect(roster[0]?.name).toContain("Wintermute");
    expect(roster[0]?.armor).toBe(8);
    expect(roster[0]?.tier).toBe(4);
  });

  it("keeps the node's authored HP over the catalog's base HP", () => {
    // Given
    const state = stateAt(
      [
        {
          id: 0,
          zone: "mid",
          iceIds: ["wisp"],
          iceHp: [17],
          reward: { credits: 0 },
          adjacent: [],
          isBoss: false,
        },
      ],
      0,
    );

    // When
    const roster = encounterRoster(state);

    // Then
    expect(roster[0]?.hp).toBe(17);
    expect(roster[0]?.maxHp).toBe(17);
    // ...but the armor comes from the catalog row (wisp has none).
    expect(roster[0]?.armor).toBe(0);
  });

  it("falls back to the active ICE for an id that is not in the catalog", () => {
    // Given: a hand-built state naming an unknown ICE.
    const state = stateAt(
      [
        {
          id: 0,
          zone: "mid",
          iceIds: ["not_in_catalog"],
          iceHp: [12],
          reward: { credits: 0 },
          adjacent: [],
          isBoss: false,
        },
      ],
      0,
    );

    // When
    const roster = encounterRoster(state);

    // Then: playable, not a crash.
    expect(roster).toHaveLength(1);
    expect(roster[0]?.hp).toBe(12);
  });
});

describe("ADR-0278 · the hand is refilled between fights", () => {
  it("tops the hand back up to handSize from the draw pile", () => {
    // Given: a hand with one card and a draw pile with four.
    const state = stateAt(
      [
        {
          id: 0,
          zone: "mid",
          iceIds: [],
          iceHp: [],
          reward: { credits: 0 },
          adjacent: [],
          isBoss: false,
        },
      ],
      0,
      [strike],
    );
    const stocked: GameState = {
      ...state,
      deck: [strike],
      drawPile: [scan, scan, scan, scan],
      discardPile: [],
    };

    // When
    const refilled = refillHand(stocked);

    // Then
    expect(refilled.deck).toHaveLength(5);
    expect(refilled.deck[0]).toBe(strike);
    expect(refilled.drawPile).toHaveLength(0);
    expect(refilled.discardPile).toHaveLength(0);
  });

  it("recycles the discard pile when the draw pile runs out", () => {
    // Given
    const state = stateAt(
      [
        {
          id: 0,
          zone: "mid",
          iceIds: [],
          iceHp: [],
          reward: { credits: 0 },
          adjacent: [],
          isBoss: false,
        },
      ],
      0,
      [strike],
    );
    const stocked: GameState = {
      ...state,
      deck: [strike],
      drawPile: [],
      discardPile: [scan, scan, scan, scan],
    };

    // When
    const refilled = refillHand(stocked);

    // Then
    expect(refilled.deck).toHaveLength(5);
    expect(refilled.discardPile).toHaveLength(0);
  });

  it("leaves a full hand untouched", () => {
    // Given
    const state = stateAt(
      [
        {
          id: 0,
          zone: "mid",
          iceIds: [],
          iceHp: [],
          reward: { credits: 0 },
          adjacent: [],
          isBoss: false,
        },
      ],
      0,
      [strike, scan],
    );

    // When
    const refilled = refillHand(state);

    // Then
    expect(refilled).toBe(state);
  });

  it("deals a card taken at the loot screen into the next fight's hand", () => {
    // Given: a won fight whose loot screen offered a card.
    const state = stateAt(
      [
        {
          id: 0,
          zone: "mid",
          iceIds: ["wisp"],
          iceHp: [1],
          reward: { credits: 10 },
          adjacent: [1],
          isBoss: false,
        },
        {
          id: 1,
          zone: "core",
          iceIds: [],
          iceHp: [],
          reward: { credits: 0 },
          adjacent: [],
          isBoss: false,
        },
      ],
      0,
      [strike],
    );
    const fighting = applyAction(breachEncounter(state), { type: "confirm" });
    expect(fighting.runPhase).toBe("combat");
    const won = applyAction(fighting, {
      type: "use_program",
      programId: "strike",
    });
    expect(won.runPhase).toBe("loot");

    // When: the card is taken, then the loot screen closes.
    const taken = applyAction(won, { type: "select_program", handIndex: 1 });
    expect(taken.cardRewardTaken).not.toBeNull();
    const back = applyAction(taken, { type: "confirm" });

    // Then: the reward is in the hand the next fight opens with.
    expect(back.runPhase).toBe("matrix");
    // The run only holds two cards, so the hand is two cards — but it is
    // topped up from the piles instead of staying empty.
    expect(back.deck).toHaveLength(2);
    expect(back.deck.map((p) => p.id)).toContain(taken.cardRewardTaken);
    expect(back.cardRewardTaken).toBeNull();
    expect(back.drawPile).toHaveLength(0);
    expect(back.discardPile).toHaveLength(0);
  });
});

describe("ADR-0278 · two ICE rooms are not the same ICE", () => {
  it("gives two ICE rooms of one mission different ICE ids", () => {
    // Given: a generated matrix with at least two ICE rooms.
    const matrix = generateProceduralMatrix(1, 42, "adr0278-variety");
    const iceRooms = matrix.nodes.filter((n) => n.iceIds.length > 0);

    // Then
    expect(iceRooms.length).toBeGreaterThan(1);
    const ids = iceRooms.map((n) => n.iceIds[0]);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("keeps the seed deterministic — the same seed gives the same ICE", () => {
    // Given
    const a = generateProceduralMatrix(1, 42, "adr0278-variety");
    const b = generateProceduralMatrix(1, 42, "adr0278-variety");

    // Then
    expect(a.nodes.map((n) => n.iceIds)).toEqual(b.nodes.map((n) => n.iceIds));
  });

  it("pins the boss room to wintermute", () => {
    // Given
    const matrix = generateProceduralMatrix(1, 42, "adr0278-variety");

    // Then
    const boss = matrix.nodes[matrix.bossNode];
    expect(boss?.isBoss).toBe(true);
    expect(boss?.iceIds).toEqual(["wintermute"]);
  });
});
