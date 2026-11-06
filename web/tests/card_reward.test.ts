import { describe, it, expect } from "vitest";
import { makeInitialState } from "../src/core/state/state";
import { applyLootAction } from "../src/core/state/state_actions_phases";
import {
  offeredCardIds,
  CARD_REWARD_COUNT,
} from "../src/core/state/card_reward";
import type { GameState, Ice, Mission, Program } from "../src/core/types";
import { rewardAffordances } from "../src/core/combat/program_affordance";

/**
 * ADR-0259 — the card reward. Winning a non-terminal fight offers three
 * programs the runner does not already hold; taking one adds it to the draw
 * pile. It is the run's only growth (no shop, and loot drops materials).
 *
 * The offer is a pure function of the run, so a reload offers the same three
 * cards and no `Math.random` is consumed.
 */

const MISSION: Mission = {
  id: "m1",
  title: "Aleph Fragment",
  fixer: "t",
  arc: 1,
  zone: "mid",
  grade_min: 3,
  grade_max: 3,
  rewards: { credits: 4075, materials: {} },
};

function program(id: string): Program {
  return {
    id,
    name: id,
    tier: 2,
    cost: 2,
    effect: "attack",
    description: "d",
    aoe: false,
  };
}

function ice(): Ice {
  return {
    id: "yakuza_enforcer",
    name: "Yakuza Enforcer",
    hp: 0,
    maxHp: 165,
    armor: 0,
    level: 3,
    tier: 3,
    personality: "aggressive",
    aggression: "standard",
  } as unknown as Ice;
}

/** Loot at a node that still has a route (non-terminal) — a card is offered. */
function lootState(over: Partial<GameState> = {}): GameState {
  const deck = [program("backdoor"), program("barrier")];
  const base = makeInitialState(MISSION, ice(), deck);
  return {
    ...base,
    runPhase: "loot",
    phase: "victory",
    deck: [...deck],
    drawPile: [],
    discardPile: [],
    turnCount: 3,
    currentNodeIndex: 0,
    // Wounded, so the loot heal is observable.
    player: { ...base.player, hp: 60 },
    matrix: {
      nodes: [
        {
          id: "n1",
          zone: "mid",
          iceIds: [],
          adjacent: [1],
          reward: { credits: 0, materials: {} },
        },
        {
          id: "n2",
          zone: "mid",
          iceIds: [],
          adjacent: [0],
          reward: { credits: 0, materials: {} },
        },
      ],
    },
    ...over,
  } as unknown as GameState;
}

/** Loot at a node with no forward route (terminal) — the run ends, no card. */
function terminalLootState(): GameState {
  return lootState({
    matrix: {
      nodes: [
        {
          id: "n1",
          zone: "deep",
          iceIds: [],
          adjacent: [],
          reward: { credits: 0, materials: {} },
        },
      ],
    },
  } as unknown as Partial<GameState>);
}

describe("card reward — the offer", () => {
  it("offers three distinct programs the runner does not already hold", () => {
    const state = lootState();
    const offered = offeredCardIds(state);
    expect(offered).toHaveLength(CARD_REWARD_COUNT);
    expect(new Set(offered).size).toBe(CARD_REWARD_COUNT);
    const owned = new Set([...state.deck, ...state.drawPile].map((p) => p.id));
    for (const id of offered) expect(owned.has(id)).toBe(false);
  });

  it("is a pure function of the run, so a reload offers the same cards", () => {
    expect(offeredCardIds(lootState())).toEqual(offeredCardIds(lootState()));
  });

  it("changes with the node, so different fights offer different cards", () => {
    const a = offeredCardIds(lootState({ currentNodeIndex: 0 }));
    const b = offeredCardIds(lootState({ currentNodeIndex: 1 }));
    // Not guaranteed to differ for every pair, but the seed must depend on it.
    const c = offeredCardIds(lootState({ turnCount: 9 }));
    expect(
      [a, b, c].some((x, i, arr) =>
        arr.some((y, j) => i !== j && x.join() !== y.join()),
      ),
    ).toBe(true);
  });
});

describe("card reward — taking it (ADR-0261 beat)", () => {
  it("adds the chosen card to the draw pile and holds the moment", () => {
    const before = lootState();
    const offered = offeredCardIds(before);
    const after = applyLootAction(before, {
      type: "select_program",
      handIndex: 1,
    });
    // The card is in the deck...
    expect(after.drawPile.map((p) => p.id)).toContain(offered[0]);
    expect(after.inventory.programs.map((p) => p.id)).toContain(offered[0]);
    // ...and the screen stays put so the acquisition is visible.
    expect(after.runPhase).toBe("loot");
    expect(after.cardRewardTaken).toBe(offered[0]);
    expect(after.message).toContain("Acquired");
    // the cards it did NOT pick are not granted
    expect(after.drawPile.map((p) => p.id)).not.toContain(offered[1]);
  });

  it("keeps the offer steady after taking, so the set does not shuffle", () => {
    const before = lootState();
    const offered = offeredCardIds(before);
    const after = applyLootAction(before, {
      type: "select_program",
      handIndex: 1,
    });
    expect(offeredCardIds(after)).toEqual([...offered]);
  });

  it("refuses a second card: one fight, one reward", () => {
    const before = lootState();
    const once = applyLootAction(before, {
      type: "select_program",
      handIndex: 1,
    });
    const twice = applyLootAction(once, {
      type: "select_program",
      handIndex: 2,
    });
    expect(twice.cardRewardTaken).toBe(once.cardRewardTaken);
    expect(twice.drawPile).toHaveLength(once.drawPile.length);
    expect(twice.message).toContain("already taken");
  });

  it("ENTER carries on and clears the offer memory (no heal — ADR-0282)", () => {
    const taken = applyLootAction(lootState(), {
      type: "select_program",
      handIndex: 1,
    });
    const after = applyLootAction(taken, { type: "confirm" });
    expect(after.runPhase).toBe("matrix");
    expect(after.cardRewardTaken).toBeNull();
    // ADR-0282: recovery is the loot screen's repair option now, so ENTER takes
    // nothing. HP is unchanged, not increased.
    expect(after.player.hp).toBe(taken.player.hp);
    // the destination names the growth
    expect(after.message).toContain("Took ");
  });

  it("ENTER without taking still travels, and names no card", () => {
    const before = lootState();
    const after = applyLootAction(before, { type: "confirm" });
    expect(after.runPhase).toBe("matrix");
    expect(after.drawPile).toHaveLength(before.drawPile.length);
    expect(after.message).not.toContain("Took ");
  });

  it("rejects a slot that is not offered", () => {
    const before = lootState();
    const after = applyLootAction(before, {
      type: "select_program",
      handIndex: 9,
    });
    expect(after.runPhase).toBe("loot");
    expect(after.cardRewardTaken ?? null).toBeNull();
    expect(after.drawPile).toHaveLength(before.drawPile.length);
  });
});

describe("card reward — the touch row (ADR-0259)", () => {
  it("gives one tappable row per offered card, with its effect", () => {
    const state = lootState();
    const rows = rewardAffordances(state);
    expect(rows).toHaveLength(CARD_REWARD_COUNT);
    expect(rows.map((r) => r.slot)).toEqual([1, 2, 3]);
    expect(rows.map((r) => r.programId)).toEqual([...offeredCardIds(state)]);
    // a reward is never refused, so no row claims BLOCKED
    for (const row of rows) expect(row.blocked).toBe(false);
    // the effect the player will actually get is on the row
    expect(rows.every((r) => typeof r.effectTag === "string")).toBe(true);
  });
});

describe("card reward — the terminal node", () => {
  it("offers nothing, because the run ends there", () => {
    const terminal = terminalLootState();
    // digits are refused; ENTER is what ends the run
    const after = applyLootAction(terminal, {
      type: "select_program",
      handIndex: 1,
    });
    expect(after.runPhase).toBe("loot");
    expect(after.drawPile).toHaveLength(terminal.drawPile.length);
  });

  it("still ends the run on ENTER", () => {
    const after = applyLootAction(terminalLootState(), { type: "confirm" });
    expect(after.runPhase).toBe("ending");
  });
});
