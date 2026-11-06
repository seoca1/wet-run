/**
 * Balance simulation invariants.
 *
 * `balance_harness.ts` prints the difficulty curve for humans; this file pins
 * the properties the simulation itself must hold so a refactor of the harness
 * (or of the combat path it drives) cannot silently invalidate the numbers.
 */
import { describe, expect, it } from "vitest";

import {
  loadIceCatalog,
  loadMissionsCatalog,
  loadProgramsCatalog,
} from "../src/core/data_loaders";
import { iceHpForGrade } from "../src/core/combat/ice_scaling";
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
  it.each(["opening", "ppl"])(
    "ignores sub-threshold idle cadence for every mission (%s)",
    (mode) => {
      // Given
      for (const mission of missions) {
        const deck =
          mode === "ppl"
            ? deckForGrade(programs, mission.grade ?? 1)
            : openingDeck;
        // When
        const baseline = simulateCombat(mission, iceCatalog, deck, {
          seed: 42,
          idleMsPerTurn: 0,
        });
        const delayed = simulateCombat(mission, iceCatalog, deck, {
          seed: 42,
          idleMsPerTurn: 1000,
        });
        // Then
        expect(delayed, mission.id).toEqual(baseline);
      }
    },
  );

  it("replays the reducer idle path deterministically when opted in", () => {
    // Given
    const mission = missions[0];
    const config = { seed: 42, idleMsPerTurn: [10_000, 0] };
    // When
    const first = simulateCombat(mission, iceCatalog, openingDeck, config);
    const second = simulateCombat(mission, iceCatalog, openingDeck, config);
    // Then
    expect(second).toEqual(first);
    expect(first.peakAlarmLevel).toBe(1);
  });

  it("keeps alarm zero when idle simulation is disabled or below the threshold", () => {
    // Given
    const mission = missions[0];
    // When
    const outcomes = [undefined, 0, [9999, 0]].map((idleMsPerTurn) =>
      simulateCombat(mission, iceCatalog, openingDeck, {
        seed: 42,
        idleMsPerTurn,
      }),
    );
    // Then
    expect(outcomes.map((outcome) => outcome.peakAlarmLevel)).toEqual([
      0, 0, 0,
    ]);
    expect(outcomes[1]).toEqual(outcomes[0]);
  });

  it("samples all due ticks during a long idle hold, not just one", () => {
    // Given
    const mission = missions[0];
    // When
    const outcome = simulateCombat(mission, iceCatalog, openingDeck, {
      seed: 42,
      idleMsPerTurn: [60_000, 0],
    });
    // Then
    expect(outcome.peakAlarmLevel).toBe(5);
  });

  it("the same seed yields an identical outcome", () => {
    const mission = missions[0]!;
    const first = simulateCombat(mission, iceCatalog, openingDeck, {
      seed: 42,
    });
    const second = simulateCombat(mission, iceCatalog, openingDeck, {
      seed: 42,
    });
    expect(second).toEqual(first);
  });

  it("different seeds actually diverge (the RNG is not pinned)", () => {
    // Grade-scaled encounters make many missions decisive (always win or always
    // lose), so assert divergence holds for at least one contested mission
    // instead of assuming the first mission is a close fight.
    const diverged = missions.some((mission) => {
      const seen = new Set(
        Array.from({ length: 16 }, (_, i) =>
          JSON.stringify(
            simulateCombat(mission, iceCatalog, openingDeck, { seed: i }),
          ),
        ),
      );
      return seen.size > 1;
    });
    expect(diverged, "at least one mission must vary with the seed").toBe(true);
  });
});

describe("balance sim — grade scaling", () => {
  it.each([
    // ADR-0256 — the card effects moved the grade curve; this is the
    // re-baselined curve that ADR accepts. The shape still falls
    // monotonically and g6 stays lethal.
    //
    // ADR-0268 caps Dixie's combo synergy at the combo ceiling (6). This deck
    // is the alphabetical five, not the curated opening deck, so the cap only
    // shows up where a fight runs long enough to build combo: g3 97.5 -> 97.2.
    // The curated starting deck moves more (g3 81.4 -> 78.4, g4 42.6 -> 38.9,
    // g5 36.6 -> 33.4) — see `npm run balance`.
    //
    // ADR-0277 wires `exploit` (half the armor ignored). The alphabetical five
    // do not hold it, so this row is unchanged; PPL picks the strongest five
    // per grade, and `exploit` is in its grades 3-6 decks, so g4 84.1 -> 89.3
    // and g6 27.3 -> 28.3.
    // ADR-0280 re-baselines: the enemy phase moved off the wall clock onto the
    // turn, and the per-grade curve was re-tuned with the per-encounter rate
    // held monotonic non-increasing (g3 caps down so it is winnable, g4 keeps
    // its bite). The previous row was [100, 100, 97.2, 53.4, 44.1, 0.3].
    { mode: "opening", expected: [100.0, 100.0, 100.0, 58.4, 44.1, 0.3] },
    { mode: "ppl", expected: [100.0, 100.0, 100.0, 62.3, 44.4, 28.3] },
  ])(
    "reproduces the ADR-0256 baseline exactly with idle disabled ($mode)",
    ({ mode, expected }) => {
      // Given
      const grades = [1, 2, 3, 4, 5, 6];
      // When
      const rates = grades.map((grade) => {
        const bucket = missions.filter(
          (mission) => (mission.grade ?? 1) === grade,
        );
        const wins = bucket.reduce(
          (sum, mission) =>
            sum +
            runSuite(
              mission,
              iceCatalog,
              mode === "ppl" ? deckForGrade(programs, grade) : openingDeck,
              100,
              1,
            ).wins,
          0,
        );
        return Number((wins / bucket.length).toFixed(1));
      });
      // Then
      expect(rates).toEqual(expected);
      if (mode === "opening") {
        expect(
          rates.every((rate, index) => index === 0 || rate <= rates[index - 1]),
        ).toBe(true);
        expect(rates[5]).toBeLessThanOrEqual(5);
      }
    },
    60_000,
  );

  it("caps ICE HP at the per-grade encounter curve", () => {
    const standard = iceCatalog["standard"];
    expect(standard).toBeDefined();
    if (standard === undefined) return;
    const hp1 = iceHpForGrade(standard, 1);
    const hp4 = iceHpForGrade(standard, 4);
    expect(hp4).toBeGreaterThan(hp1);
    expect(hp1).toBeLessThanOrEqual(
      standard.hpBase ?? Number.POSITIVE_INFINITY,
    );
    expect(hp4).toBeLessThanOrEqual(
      (standard.hpBase ?? 0) + (standard.hpPerGrade ?? 0) * 3,
    );
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
    const maxTier = (deck: ReadonlyArray<{ tier: number }>) =>
      Math.max(...deck.map((p) => p.tier));
    expect(maxTier(g5)).toBeGreaterThanOrEqual(maxTier(g1));
  });
});

describe("balance sim — outcome sanity", () => {
  it("never reports NaN or negative HP", () => {
    for (const mission of missions.slice(0, 8)) {
      const outcome = simulateCombat(mission, iceCatalog, openingDeck, {
        seed: 1,
      });
      expect(Number.isFinite(outcome.hpStart), `${mission.id} hpStart`).toBe(
        true,
      );
      expect(Number.isFinite(outcome.hpEnd), `${mission.id} hpEnd`).toBe(true);
      expect(outcome.hpEnd, `${mission.id} hpEnd`).toBeGreaterThanOrEqual(0);
    }
  });

  it("resolves within the turn cap (the loop cannot run away)", () => {
    for (const mission of missions.slice(0, 12)) {
      const outcome = simulateCombat(mission, iceCatalog, openingDeck, {
        seed: 3,
      });
      expect(outcome.turns, `${mission.id} turns`).toBeLessThanOrEqual(100);
    }
  });

  it("a win and a loss are both reachable across the mission set", () => {
    const outcomes = missions.map((m) =>
      simulateCombat(m, iceCatalog, openingDeck, { seed: 5 }),
    );
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
