/**
 * Balance simulation invariants.
 *
 * `balance_harness.ts` prints the difficulty curve for humans; this file pins
 * the properties the simulation itself must hold so a refactor of the harness
 * (or of the combat path it drives) cannot silently invalidate the numbers.
 */
import { describe, expect, it } from "vitest";

import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import { runSuite, simulateCombat } from "../scripts/balance_sim";
import type { Program } from "../src/core/types";

import missionsJson from "../src/data/missions.json";
import iceTypesJson from "../src/data/ice_types.json";
import programsJson from "../src/data/programs.json";

const missions = loadMissionsCatalog(missionsJson);
const iceCatalog = loadIceCatalog(iceTypesJson);
const programs = loadProgramsCatalog(programsJson);
const openingDeck: ReadonlyArray<Program> = Object.keys(programs)
  .sort()
  .slice(0, 5)
  .map((id) => programs[id])
  .filter((p): p is Program => p !== undefined);

describe("balance sim — determinism", () => {
  it("the same seed yields an identical outcome", () => {
    const mission = missions[0]!;
    const first = simulateCombat(mission, iceCatalog, openingDeck, { seed: 42 });
    const second = simulateCombat(mission, iceCatalog, openingDeck, { seed: 42 });
    expect(second).toEqual(first);
  });

  it("different seeds actually diverge (the RNG is not pinned)", () => {
    const mission = missions[0]!;
    const seen = new Set(
      Array.from({ length: 24 }, (_, i) =>
        JSON.stringify(simulateCombat(mission, iceCatalog, openingDeck, { seed: i })),
      ),
    );
    expect(seen.size).toBeGreaterThan(1);
  });
});

describe("balance sim — outcome sanity", () => {
  it("never reports NaN or negative HP", () => {
    for (const mission of missions.slice(0, 8)) {
      const outcome = simulateCombat(mission, iceCatalog, openingDeck, { seed: 1 });
      expect(Number.isFinite(outcome.hpStart), `${mission.id} hpStart`).toBe(true);
      expect(Number.isFinite(outcome.hpEnd), `${mission.id} hpEnd`).toBe(true);
      expect(outcome.hpEnd, `${mission.id} hpEnd`).toBeGreaterThanOrEqual(0);
    }
  });

  it("resolves within the opening hand (the loop cannot run away)", () => {
    for (const mission of missions.slice(0, 12)) {
      const outcome = simulateCombat(mission, iceCatalog, openingDeck, { seed: 3 });
      expect(outcome.turns, `${mission.id} turns`).toBeLessThanOrEqual(openingDeck.length + 1);
    }
  });

  it("a win and a loss are both reachable across the mission set", () => {
    const outcomes = missions.map((m) => simulateCombat(m, iceCatalog, openingDeck, { seed: 5 }));
    expect(outcomes.some((o) => o.won)).toBe(true);
    expect(outcomes.some((o) => !o.won)).toBe(true);
  });

  it("grade-1 missions are winnable with the opening deck", () => {
    const gradeOne = missions.filter((m) => (m.grade ?? 1) === 1);
    const wins = gradeOne.reduce(
      (acc, m) => acc + runSuite(m, iceCatalog, openingDeck, 40, 1).wins,
      0,
    );
    expect(wins).toBeGreaterThan(0);
  });
});
