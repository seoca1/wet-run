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
import {
  applyAction,
  makeInitialState,
  slotToGameState,
  stateToSaveSlot,
} from "../src/core/state/state";
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

  it("every arc defines a control ending (catalog presence, not reachability)", () => {
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

      // Then: the *catalog* has a control ending per arc.
      // Whether a real run reaches it is a different claim, answered by
      // `npm run endings` (ADR-0279 measures control at arcs 3-5 only).
      expect(ending.category).toBe("control");
      expect(ending.arc).toBe(arc);
    }
  });

  it("the terminal victory mentions 'mission complete' exactly once (idempotent display)", () => {
    // Given: a full clear of an 800cr mission.
    const first = winFight(twoFightMission());
    const won = winFight(walkToBoss(first));

    // Then: the mission reward is announced a single time, even though the
    // terminal fight could in principle re-enter the victory path.
    const mentions = (won.message.match(/mission complete/g) ?? []).length;
    expect(mentions).toBe(1);
    expect(won.player.credits).toBe(1975);
  });

  it("First Jack's mission reward is the 500 the select screen shows", () => {
    // Given / When: the mission the mission-select screen prints as 500cr.
    const mission = Object.values(missions).find((m) => m.id === "first_jack");

    // Then: the screen's number is the mission's own reward, and it is paid
    // by the win that ends the mission (see the tests above), not per fight.
    expect(mission?.rewards.credits).toBe(500);
  });
});

/**
 * The reviewers' residual risk: a path that re-runs the terminal win, or
 * restores a checkpoint taken after the payment, must not pay twice.
 *
 * The payment happens in `resolveVictory` — the transition that *wins* the
 * fight. The terminal loot screen's confirm only resolves the ending, so it
 * has nothing to pay. These tests pin that separation.
 */
describe("ADR-0279 · the mission reward survives replay and resume", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.3);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("confirming the terminal loot screen pays nothing again", () => {
    // Given: a completed mission sitting on its terminal loot screen.
    const first = winFight(twoFightMission());
    const won = winFight(walkToBoss(first));
    expect(won.runPhase).toBe("loot");
    const earned = won.player.credits;
    expect(earned).toBe(1975);

    // When: ENTER ends the run.
    const ended = applyAction(won, { type: "confirm" });

    // Then: the ending carries the same ledger — no second payout.
    expect(ended.runPhase).toBe("ending");
    expect(ended.player.credits).toBe(earned);
  });

  it("confirming the ending pays nothing again", () => {
    // Given: an ended run.
    const first = winFight(twoFightMission());
    const ended = applyAction(winFight(walkToBoss(first)), { type: "confirm" });
    const earned = ended.player.credits;

    // When: ENTER leaves the ending for the title.
    const back = applyAction(ended, { type: "confirm" });

    // Then
    expect(back.phase).toBe("menu");
    expect(back.player.credits).toBe(earned);
  });

  it("a save taken after the payment restores the same ledger", () => {
    // Given: a completed mission (reward paid) on its terminal loot screen.
    const first = winFight(twoFightMission());
    const won = winFight(walkToBoss(first));
    const earned = won.player.credits;

    // When: the autosave round-trips it. The mission has to exist in a real
    // catalog for the restore to resolve, so this uses `first_jack`.
    const real = Object.values(missions).find((m) => m.id === "first_jack");
    expect(real).toBeDefined();
    const slot = stateToSaveSlot({ ...won, mission: real as never });
    const restored = slotToGameState(
      slot,
      Object.values(missions),
      programs,
      Object.values(ice)[0] as never,
      ice,
    );

    // Then: the credits are the ones that were saved — the restore is not a
    // second payment and does not drop the payment either.
    expect(restored).not.toBeNull();
    expect(restored?.player.credits).toBe(earned);
  });

  it("a save taken before the win does not pay on reload", () => {
    // Given: a run saved mid-mission, before the terminal fight.
    const started = twoFightMission();
    const real = Object.values(missions).find((m) => m.id === "first_jack");
    const slot = stateToSaveSlot({ ...started, mission: real as never });
    const restored = slotToGameState(
      slot,
      Object.values(missions),
      programs,
      Object.values(ice)[0] as never,
      ice,
    );
    expect(restored).not.toBeNull();

    // Then: the resumed run starts with an empty ledger; the reward is still
    // ahead of it, not already paid.
    expect(restored?.player.credits).toBe(0);
  });
});
