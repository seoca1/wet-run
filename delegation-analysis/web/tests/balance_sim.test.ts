/**
 * Balance simulation invariants.
 *
 * `balance_harness.ts` prints the difficulty curve for humans; this file pins
 * the properties the simulation itself must hold so a refactor of the harness
 * (or of the combat path it drives) cannot silently invalidate the numbers.
 */
import { describe, expect, it } from "vitest";

import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import { iceHpForGrade } from "../src/core/ice_scaling";
import { deckForGrade, runSuite, simulateCombat } from "../scripts/balance_sim";
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
    // Grade-scaled encounters make many missions decisive (always win or always
    // lose), so assert divergence holds for at least one contested mission
    // instead of assuming the first mission is a close fight.
    const diverged = missions.some((mission) => {
      const seen = new Set(
        Array.from({ length: 16 }, (_, i) =>
          JSON.stringify(simulateCombat(mission, iceCatalog, openingDeck, { seed: i })),
        ),
      );
      return seen.size > 1;
    });
    expect(diverged, "at least one mission must vary with the seed").toBe(true);
  });
});

describe("balance sim — grade scaling", () => {
  it("caps ICE HP at the per-grade encounter curve", () => {
    const standard = iceCatalog["standard"];
    expect(standard).toBeDefined();
    if (standard === undefined) return;
    const hp1 = iceHpForGrade(standard, 1);
    const hp4 = iceHpForGrade(standard, 4);
    expect(hp4).toBeGreaterThan(hp1);
    expect(hp1).toBeLessThanOrEqual(standard.hpBase ?? Number.POSITIVE_INFINITY);
    expect(hp4).toBeLessThanOrEqual((standard.hpBase ?? 0) + (standard.hpPerGrade ?? 0) * 3);
  });

  it("falls back to ice.hp when grade data is missing", () => {
    const noGrade = { id: "x", name: "X", hp: 77, armor: 0, tier: 1 };
    expect(iceHpForGrade(noGrade, 5)).toBe(77);
  });
});

describe("balance sim — PPL deck", () => {
  it("scales the deck tier with grade and always fields 5 cards", () => {
    const g1 = deckForGrade(programs, 1);
    const g5 = deckForGrade(programs, 5);
    expect(g1.length).toBe(5);
    expect(g5.length).toBe(5);
    expect(g1.every((p) => p.tier <= 1)).toBe(true);
    const maxTier = (deck: ReadonlyArray<{ tier: number }>) => Math.max(...deck.map((p) => p.tier));
    expect(maxTier(g5)).toBeGreaterThanOrEqual(maxTier(g1));
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

  it("resolves within the turn cap (the loop cannot run away)", () => {
    for (const mission of missions.slice(0, 12)) {
      const outcome = simulateCombat(mission, iceCatalog, openingDeck, { seed: 3 });
      expect(outcome.turns, `${mission.id} turns`).toBeLessThanOrEqual(100);
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
