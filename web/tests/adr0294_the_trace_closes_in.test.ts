/**
 * ADR-0294 — every kill leaves a trace.
 *
 * ADR-0293 gave the top grade a reward axis and the measurement then exposed the
 * shape of what was left: with no cost that scales with FIGHTING, "fight
 * everything" led on both completion and credits at g5/g6 (+6.3pp each), so the
 * top grades had an answer instead of a trade-off. Raising encounter strength did
 * not converge them — it widened the gap, because the runner who fights arrives
 * at the core with gear.
 *
 * The run's COST budget is the cost that already scales with fighting: programs
 * spend it, it never refills, and at 100 nothing can be cast. A kill now leaves a
 * trace worth its ICE's tier, so a fight is paid for twice: HP during it, and
 * capacity after it.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { TRACE_COST_PER_TIER, traceCostFor } from "../src/core/combat/victory";
import { COST_LIMIT } from "../src/core/combat/program_affordance";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { startingDeck } from "../src/core/state/starting_deck";
import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import type { GameState } from "../src/core/types";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import missionsJson from "../src/data/missions.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

const ice = loadIceCatalog(iceJson);
const programs = loadProgramsCatalog(programsJson);
const missions = loadMissionsCatalog(missionsJson);

function arena(): GameState {
  const mission = Object.values(missions).find((m) => m.id === "first_jack");
  const initial = makeInitialState(
    mission as never,
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
        { id: 0, zone: "mid", iceIds: ["wisp"], iceHp: [4], reward: { credits: 0 }, adjacent: [1], isBoss: false },
        { id: 1, zone: "core-deep", iceIds: ["wisp"], iceHp: [4], reward: { credits: 0 }, adjacent: [0], isBoss: true },
      ],
    },
  };
}

function winHere(state: GameState): GameState {
  let s = applyAction(state, { type: "confirm" });
  for (let i = 0; i < 8; i += 1) {
    if (s.encounterDecision?.selectedVerb === "BREACH") break;
    s = applyAction(s, { type: "move_south" });
  }
  s = applyAction(s, { type: "confirm" });
  s = applyAction(s, { type: "confirm" });
  return applyAction(s, { type: "use_program", programId: "exploit" });
}

describe("ADR-0294 · the trace closes in", () => {
  it("charges the ICE's tier, not a flat fee", () => {
    // Given / When / Then: a hard kill costs more capacity than a routine one.
    expect(traceCostFor({ tier: 1 })).toBe(TRACE_COST_PER_TIER);
    expect(traceCostFor({ tier: 6 })).toBe(6 * TRACE_COST_PER_TIER);
    expect(traceCostFor({ tier: 6 })).toBeGreaterThan(traceCostFor({ tier: 2 }));
  });

  it("charges nothing for ICE with no tier", () => {
    // Given / When / Then: hand-built ICE cannot mint a cost.
    expect(traceCostFor({})).toBe(0);
    expect(traceCostFor({ tier: 0 })).toBe(0);
    expect(traceCostFor({ tier: -2 })).toBe(0);
  });

  it("puts the cost on the run's budget when the kill lands", () => {
    // Given: a fight worth a wisp (tier 1).
    const before = arena();

    // When: it is won.
    const won = winHere(before);

    // Then: the run's COST rose by the trace, on top of whatever the cards cost.
    expect(won.runPhase).toBe("loot");
    expect(won.player.alarm).toBeGreaterThan(before.player.alarm);
    expect(won.player.alarm - before.player.alarm).toBeGreaterThanOrEqual(
      traceCostFor({ tier: 1 }),
    );
    expect(won.message).toContain("trace +");
  });
});

describe("ADR-0294 · the trace can exhaust the budget but never overflow it", () => {
  beforeEach(() => {
    vi.spyOn(Math, "random").mockReturnValue(0.3);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("caps at the run's COST ceiling", () => {
    // Given: a runner already at the ceiling.
    const spent = arena();
    const atCap: GameState = {
      ...spent,
      player: { ...spent.player, alarm: COST_LIMIT },
    };

    // When
    const won = winHere(atCap);

    // Then: the kill cannot push COST past what a program is allowed to cost.
    expect(won.player.alarm).toBeLessThanOrEqual(COST_LIMIT);
  });
});
