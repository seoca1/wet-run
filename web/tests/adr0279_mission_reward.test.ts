/**
 * ADR-0279 regression tests — the mission reward is paid once, and the ending
 * resolver reads the number the ending screen prints.
 *
 * Two defects of the same family ("the screen promises one thing, the game does
 * another"):
 *
 *   1. `mission.rewards.credits` was added to **every** encounter win. A
 *      two-fight mission paid the mission's reward twice, while the mission
 *      select screen listed it once (`First Jack  [T1 | 500cr]`).
 *   2. The ending resolver read `inventory.credits`, the mission's base reward
 *      seeded for crafting, which combat never grows. The `control` branch
 *      (`credits > 5000`) was therefore reachable on only 2 of 53 missions —
 *      but the ending screen printed `player.credits`, the run's earnings, so a
 *      run could be told it ended "small time" while showing 6,000cr.
 *
 * `Math.random` is pinned so the combat rolls are fixed.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  loadIceCatalog,
  loadMissionsCatalog,
  loadProgramsCatalog,
} from "../src/core/data_loaders";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { startingDeck } from "../src/core/state/starting_deck";
import { resolveEnding } from "../src/core/combat/ending_resolver";
import type { GameState } from "../src/core/types";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import missionsJson from "../src/data/missions.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

const ice = loadIceCatalog(iceJson);
const programs = loadProgramsCatalog(programsJson);
const missions = loadMissionsCatalog(missionsJson);

/** A two-fight mission: node 0 is a mid ICE, node 1 is the boss. */
function twoFightMission(): GameState {
  const mission = {
    id: "adr0279-mission",
    title: "ADR 0279 mission",
    fixer: "test",
    zone: "surface",
    arc: 1,
    grade_min: 1,
    grade_max: 1,
    // The reward the mission-select screen shows.
    rewards: { credits: 800, materials: {} },
  } as const;
  const initial = makeInitialState(
    mission,
    Object.values(ice)[0] as never,
    startingDeck(programs, "novice"),
  );
  return {
    ...initial,
    currentNodeIndex: 0,
    runPhase: "matrix",
    phase: "approach",
    matrix: {
      startNode: 0,
      bossNode: 1,
      grade: 1,
      nodes: [
        {
          id: 0,
          zone: "mid",
          iceIds: ["wisp"],
          iceHp: [4],
          reward: { credits: 50 },
          adjacent: [1],
          isBoss: false,
        },
        {
          id: 1,
          zone: "core-deep",
          iceIds: ["wisp"],
          iceHp: [4],
          reward: { credits: 75 },
          adjacent: [0],
          isBoss: true,
        },
      ],
    },
  };
}

/** Breach the encounter standing on the current node and enter combat. */
function breachHere(state: GameState): GameState {
  let s = applyAction(state, { type: "confirm" });
  for (let i = 0; i < 8; i += 1) {
    if (s.encounterDecision?.selectedVerb === "BREACH") break;
    s = applyAction(s, { type: "move_south" });
  }
  s = applyAction(s, { type: "confirm" }); // decision → combat/approach
  return applyAction(s, { type: "confirm" }); // approach → combat/combat
}

/** Walk one fight to a program win. */
function winFight(state: GameState): GameState {
  return applyAction(breachHere(state), {
    type: "use_program",
    programId: "exploit",
  });
}

/** Loot → matrix, then step onto the boss node. */
function walkToBoss(state: GameState): GameState {
  let s = applyAction(state, { type: "confirm" }); // loot → matrix
  s = applyAction(s, { type: "move_south" }); // highlight node 1
  return applyAction(s, { type: "confirm" }); // travel; arrival gate opens
}

describe("ADR-0279 · the mission reward is paid once", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.3);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("a fight that does not end the mission pays the node reward only", () => {
    // Given: a mid ICE with a 50cr node reward on an 800cr mission.
    const won = winFight(twoFightMission());

    // Then: the mission's 800cr is NOT in this payout.
    expect(won.runPhase).toBe("loot");
    expect(won.message).toContain("+100 credits"); // 50 node + 50 first_blood
    expect(won.message).not.toContain("800");
    expect(won.message).not.toContain("mission complete");
  });

  it("the fight that ends the mission pays the mission reward, once", () => {
    // Given: the first fight won, then the boss.
    const first = winFight(twoFightMission());
    const won = winFight(walkToBoss(first));

    // Then: node 75 + mission 800 + boss_slayer 1000.
    expect(won.runPhase).toBe("loot");
    expect(won.message).toContain("+1875 credits");
    expect(won.message).toContain("(mission complete)");
  });

  it("a two-fight clear never pays the mission reward twice", () => {
    // Given: a full clear of a 800cr mission.
    const first = winFight(twoFightMission());
    const won = winFight(walkToBoss(first));

    // Then: earned = 100 (first) + 1875 (boss) = 1975, which counts the 800
    // exactly once. Paying it per fight would have counted it twice.
    expect(won.player.credits).toBe(1975);
  });
});

describe("ADR-0279 · the resolver reads what the run earned", () => {
  it("a rich run at full HP gets the arc's control ending", () => {
    // Given: the run earned 6,000cr and is at full HP.
    const ending = resolveEnding({
      arc: 4,
      hp: 100,
      maxHp: 100,
      credits: 6000,
      missionsCompleted: 1,
      totalDeaths: 0,
      factionScores: {},
      choices: [],
    });

    // Then: arc 4's control ending, not its status_quo fallback.
    expect(ending.id).toBe("arc4_new_order");
    expect(ending.category).toBe("control");
  });

  it("a poor run at full HP still gets status_quo", () => {
    // Given: the run earned 2,000cr.
    const ending = resolveEnding({
      arc: 4,
      hp: 100,
      maxHp: 100,
      credits: 2000,
      missionsCompleted: 1,
      totalDeaths: 0,
      factionScores: {},
      choices: [],
    });

    // Then
    expect(ending.id).toBe("arc4_status_quo");
    expect(ending.category).toBe("status_quo");
  });

  it("every arc has a control ending (the rich branch is never a fallback)", () => {
    // Given: a rich, healthy run in each arc.
    for (const arc of [1, 2, 3, 4, 5] as const) {
      const ending = resolveEnding({
        arc,
        hp: 100,
        maxHp: 100,
        credits: 9000,
        missionsCompleted: 1,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      });

      // Then
      expect(ending.category).toBe("control");
      expect(ending.arc).toBe(arc);
    }
  });

  it("First Jack's mission reward is the 500 the select screen shows", () => {
    // Given / When: the mission the mission-select screen prints as 500cr.
    const mission = Object.values(missions).find((m) => m.id === "first_jack");

    // Then: the screen's number is the mission's own reward, and it is paid
    // by the win that ends the mission (see the tests above), not per fight.
    expect(mission?.rewards.credits).toBe(500);
  });
});
