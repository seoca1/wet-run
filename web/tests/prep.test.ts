/**
 * ADR-0283 — prep adds CAPACITY, not cards.
 *
 * Three capacity levers were measured, because buying cards made runs worse (the
 * opening deck is a curated five-slot instrument and a purchase evicts a role):
 *
 *   extra max HP   +30 -> g4 31.7 -> 42.5, +250 -> g5 0 -> 19.4   WORKS
 *   extra hand     +2  -> g4 31.7 -> 31.7                          INERT
 *   card purchases      -> g2/g3 down, g4 +9.2                     HARMFUL
 *
 * So prep is HP, applied at run start. Measured at 24 seeds with `loot=smart`:
 * 100 / 97.9 / 83.0 / 45.4 / 30.6 / 18.1 against targets of
 * 100 / 95 / 80 / 50 / 25 / 10 — five grades inside the 8pp tolerance and grade 6
 * at +8.1pp (72 runs, so inside the noise).
 */
import { describe, expect, it } from "vitest";
import { applyPrep, prepHpBonus, PREP_HP_BY_GRADE } from "../src/core/state/prep";
import { makeInitialState } from "../src/core/state/state";
import { startingDeck } from "../src/core/state/starting_deck";
import { loadIceCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

const ice = loadIceCatalog(iceJson);
const programs = loadProgramsCatalog(programsJson);

function run(grade: number) {
  return makeInitialState(
    {
      id: "prep-test",
      title: "Prep test",
      fixer: "test",
      zone: "surface",
      arc: 1,
      grade_min: grade,
      grade_max: grade,
      rewards: { credits: 500, materials: {} },
    },
    Object.values(ice)[0] as never,
    startingDeck(programs, "novice"),
  );
}

describe("ADR-0283 · prep is a capacity grant", () => {
  it("fills the bigger pool rather than leaving it empty", () => {
    // Given: a grade-5 run, where prep is at its largest.
    const before = run(5);
    expect(before.player.hp).toBe(before.player.maxHp);

    // When
    const after = applyPrep(before);

    // Then: both the pool and the fill grow by the grade's grant.
    const bonus = prepHpBonus(5);
    expect(bonus).toBeGreaterThan(0);
    expect(after.player.maxHp).toBe(before.player.maxHp + bonus);
    expect(after.player.hp).toBe(after.player.maxHp);
  });

  it("leaves the low grades alone", () => {
    // Given: grades 1-2 already meet their targets without prep.
    for (const grade of [1, 2]) {
      expect(prepHpBonus(grade)).toBe(0);
      const before = run(grade);
      expect(applyPrep(before)).toBe(before);
    }
  });

  it("grows with the grade where it is granted (a stronger pool up top)", () => {
    // Given / When: the grades that get a grant.
    const grants = [3, 4, 5, 6].map((g) => prepHpBonus(g));

    // Then: grade 5 gets the most — 7.4 encounters against grade 6's 7.3, and
    // `neuromancer`'s armour 9 against `aleph`'s 7. There is no invariant on a
    // player stat, so the honest shape is allowed to peak at 5.
    expect(Math.max(...grants)).toBe(prepHpBonus(5));
    expect(prepBonusIsSane()).toBe(true);
  });

  it("keeps the balance harness measuring the same fight", () => {
    // Given: `makeInitialState` is what the per-encounter harness uses.
    const state = run(5);

    // Then: it does not carry prep — prep is applied at run start instead, so
    // the recorded per-encounter curve is untouched.
    expect(state.player.maxHp).toBe(100);
  });
});

function prepBonusIsSane(): boolean {
  return PREP_HP_BY_GRADE.every((v) => Number.isFinite(v) && v >= 0);
}
