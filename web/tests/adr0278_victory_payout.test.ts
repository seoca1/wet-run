/**
 * ADR-0278 regression test — the payout of a won fight must not depend on who
 * landed the killing blow.
 *
 * The story trace showed two different victory paths with two different
 * payouts:
 *
 *   - `useProgram` — the player's card dropped the last ICE → loot rolled,
 *     `first_blood` unlocked, faction credit, "(no COST)" note.
 *   - `finishPlayerTurn` — Dixie (or a DoT) dropped the last ICE → credits
 *     only. No loot, no `first_blood`, no `boss_slayer` (worth 1,000), no
 *     faction credit, no log line.
 *
 * The player cannot choose which path fires, and letting the companion finish
 * a fight is the natural way to play. So the reward for winning cannot depend
 * on it. The one split that stays is ADR-0258's COST exemption: it belongs to
 * the card that dropped the last ICE, so a companion kill does not claim it.
 *
 * `Math.random` is pinned so the damage rolls and the loot rolls are fixed:
 * `0.3` gives boost 9 damage, no crit, no burn/slow proc, and a wisp loot roll
 * that drops.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  loadIceCatalog,
  loadMissionsCatalog,
  loadProgramsCatalog,
} from "../src/core/data_loaders";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { startingDeck } from "../src/core/state/starting_deck";
import type { GameState } from "../src/core/types";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import missionsJson from "../src/data/missions.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

const ice = loadIceCatalog(iceJson);
const programs = loadProgramsCatalog(programsJson);
const missions = loadMissionsCatalog(missionsJson);

/**
 * Enter a fight against one wisp.
 *
 * `iceHp` picks which path wins: a value the played card kills outright
 * (`strike` does 4-5, `boost` does 9) ends on the program path; a value the
 * card leaves alive but Dixie (11 damage) finishes ends on the companion
 * path.
 */
function fightAt(iceHp: number): GameState {
  const mission = Object.values(missions).find((m) => m.id === "first_jack");
  if (!mission) throw new Error("first_jack missing");
  const initial = makeInitialState(
    mission,
    Object.values(ice)[0] as never,
    startingDeck(programs, "novice"),
  );
  const nodes = [
    {
      id: 0,
      zone: "mid" as const,
      iceIds: ["wisp"],
      iceHp: [iceHp],
      reward: { credits: 75 },
      adjacent: [1],
      isBoss: false,
    },
    {
      id: 1,
      zone: "core" as const,
      iceIds: [] as string[],
      iceHp: [] as number[],
      reward: { credits: 0 },
      adjacent: [],
      isBoss: false,
    },
  ];
  let state: GameState = {
    ...initial,
    currentNodeIndex: 0,
    runPhase: "matrix",
    phase: "approach",
    matrix: {
      startNode: 0,
      bossNode: 1,
      grade: 1,
      nodes,
    },
  };
  state = applyAction(state, { type: "confirm" });
  for (let i = 0; i < 4; i += 1) {
    if (state.encounterDecision?.selectedVerb === "BREACH") break;
    state = applyAction(state, { type: "move_south" });
  }
  state = applyAction(state, { type: "confirm" });
  state = applyAction(state, { type: "confirm" });
  return state;
}

/** The wisp the card leaves alive; Dixie's 11 finishes it (boost does 9). */
const COMPANION_KILL_HP = 15;
/** The wisp the card kills outright (exploit does 13). */
const PROGRAM_KILL_HP = 10;

describe("ADR-0278 · winning a fight pays the same whoever lands the blow", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.3);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("takes the companion path when the card leaves the ICE alive", () => {
    // Given: boost (9 damage) on a 15 HP wisp.
    const result = applyAction(fightAt(COMPANION_KILL_HP), {
      type: "use_program",
      programId: "boost",
    });

    // Then: Dixie finished it — and the message does not claim "(no COST)".
    expect(result.runPhase).toBe("loot");
    expect(result.iceRoster[0]?.hp).toBe(0);
    expect(result.message).toContain("defeated!");
    expect(result.message).not.toContain("(no COST)");
  });

  it("takes the program path when the card lands the killing blow", () => {
    // Given: exploit (13 damage) on a 10 HP wisp.
    const result = applyAction(fightAt(PROGRAM_KILL_HP), {
      type: "use_program",
      programId: "exploit",
    });

    // Then: the card dropped it, so the COST exemption is claimed.
    expect(result.runPhase).toBe("loot");
    expect(result.message).toContain("(no COST)");
  });

  it("names the ICE that fell, not the run's base ICE", () => {
    // Given / When
    const companion = applyAction(fightAt(COMPANION_KILL_HP), {
      type: "use_program",
      programId: "boost",
    });
    const program = applyAction(fightAt(PROGRAM_KILL_HP), {
      type: "use_program",
      programId: "exploit",
    });

    // Then: both say the wisp, and neither says the mission's opening ICE.
    expect(companion.message).toContain("Wisp");
    expect(program.message).toContain("Wisp");
    expect(companion.message).not.toContain("Standard");
    expect(program.message).not.toContain("Standard");
  });

  it("a companion kill still unlocks first_blood and drops the ICE's loot", () => {
    // Given: the fight the card does not finish.
    const companion = applyAction(fightAt(COMPANION_KILL_HP), {
      type: "use_program",
      programId: "boost",
    });

    // Then: the kill owes the player the same reward a card kill would.
    expect(companion.unlockedAchievements).toContain("first_blood");
    expect(companion.achievementCredits).toBe(50);
    expect(companion.inventory.materials.ice_shard).toBeGreaterThan(0);
    expect(companion.message).toContain("Loot:");
  });

  it("both paths pay identical credits for an equivalent fight", () => {
    // Given: one fight the card finishes, one Dixie does.
    const companion = applyAction(fightAt(COMPANION_KILL_HP), {
      type: "use_program",
      programId: "boost",
    });
    const program = applyAction(fightAt(PROGRAM_KILL_HP), {
      type: "use_program",
      programId: "exploit",
    });

    // Then: the payout is a function of the fight, not of the reducer branch.
    expect(companion.player.credits).toBe(program.player.credits);
    expect(companion.achievementCredits).toBe(program.achievementCredits);
    expect(companion.unlockedAchievements).toEqual(
      program.unlockedAchievements,
    );
    expect(companion.inventory.materials).toEqual(program.inventory.materials);
  });
});
