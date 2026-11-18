/**
 * Design Conformance Tests.
 *
 * The rest of the suite verifies that the code behaves as *coded*. This file
 * verifies that the code matches what `docs/design/` *specifies*. Without it,
 * a design value can drift (or be violated) while every behavioural test stays
 * green — see the `design drift` block below for a live example.
 *
 * Sources:
 *  - docs/design/systems/combat.md            (damage, boss phases, Dixie)
 *  - docs/design/story_skeleton.md            (5 arcs, 29 endings)
 *  - docs/design/balance/ppl_zdr_balance.md   (PPL/ZDR — not ported, see drift)
 *  - ADR-0152                                 (HEAL 0.20 -> 0.15)
 */
import { describe, expect, it } from "vitest";

import {
  ALARM_MAX_LEVEL,
  COMBO_WINDOW_MS,
  CRIT_CHANCE,
  CRIT_MULTIPLIER,
  CRIT_MULTIPLIER_MAX,
  CRIT_MULTIPLIER_MIN,
  DAMAGE_VARIANCE_MAX,
  DAMAGE_VARIANCE_MIN,
  STAGGER_DURATION_MS,
} from "../src/core/combat_engine";
import { DEFAULT_BOSS_PROFILE } from "../src/core/boss_phases";
import { ENDINGS, getEndingCounts, resolveEnding } from "../src/core/ending_resolver";
import { TIER_MULTIPLIERS, TIER_THRESHOLDS } from "../src/core/faction_reputation";
import {
  DIXIE_ATTACK_INTERVAL_MS,
  DIXIE_BASE_DAMAGE,
  DIXIE_SYNERGY_BONUS,
} from "../src/core/state_actions";

describe("design conformance — combat constants (docs/design/systems/combat.md)", () => {
  it("damage variance band is 0.8x–1.2x", () => {
    expect(DAMAGE_VARIANCE_MIN).toBe(0.8);
    expect(DAMAGE_VARIANCE_MAX).toBe(1.2);
  });

  it("critical hit is 15% chance at 2.0x (band 1.8x–2.2x)", () => {
    expect(CRIT_CHANCE).toBe(0.15);
    expect(CRIT_MULTIPLIER).toBe(2.0);
    expect(CRIT_MULTIPLIER_MIN).toBe(1.8);
    expect(CRIT_MULTIPLIER_MAX).toBe(2.2);
  });

  it("stagger lasts 1500ms and combo window is 3500ms", () => {
    expect(STAGGER_DURATION_MS).toBe(1500);
    expect(COMBO_WINDOW_MS).toBe(3500);
  });

  it("alarm has 5 levels", () => {
    expect(ALARM_MAX_LEVEL).toBe(5);
  });
});

describe("design conformance — boss phases (docs/design/systems/combat.md)", () => {
  it("phase damage multipliers are 1.0 / 1.25 / 1.5 / 2.0", () => {
    const byPhase = new Map(
      DEFAULT_BOSS_PROFILE.phases.map((p) => [p.phase, p.damageMultiplier]),
    );
    expect(byPhase.get(1)).toBe(1.0);
    expect(byPhase.get(2)).toBe(1.25);
    expect(byPhase.get(3)).toBe(1.5);
    expect(byPhase.get(4)).toBe(2.0);
  });

  it("phase HP thresholds descend 0.75 / 0.5 / 0.25", () => {
    const byPhase = new Map(DEFAULT_BOSS_PROFILE.phases.map((p) => [p.phase, p.hpThreshold]));
    expect(byPhase.get(2)).toBe(0.75);
    expect(byPhase.get(3)).toBe(0.5);
    expect(byPhase.get(4)).toBe(0.25);
  });
});

describe("design conformance — faction reputation tiers", () => {
  it("tier thresholds match the designed ±100/±80/±50/±20 ladder", () => {
    const min = (tier: string) => TIER_THRESHOLDS.find((t) => t.tier === tier)?.min;
    expect(min("ALLIED")).toBe(80);
    expect(min("FRIENDLY")).toBe(50);
    expect(min("TRUSTED")).toBe(20);
    expect(min("NEUTRAL")).toBe(-19);
    expect(min("HOSTILE")).toBe(-49);
    expect(min("ENEMY")).toBe(-79);
    expect(min("OUTCAST")).toBe(-100);
  });

  it("defines a multiplier for all 7 tiers", () => {
    expect(Object.keys(TIER_MULTIPLIERS)).toHaveLength(7);
  });
});

describe("design conformance — ending catalog (docs/design/story_skeleton.md)", () => {
  it("ships 29 endings", () => {
    expect(ENDINGS).toHaveLength(29);
  });

  it("distributes endings across 5 arcs as 7 / 6 / 6 / 5 / 5", () => {
    expect(getEndingCounts()).toEqual({ 1: 7, 2: 6, 3: 6, 4: 5, 5: 5 });
  });

  it("every ending id is unique", () => {
    const ids = ENDINGS.map((e) => e.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("resolveEnding always returns a valid ending for every arc (never undefined)", () => {
    for (const arc of [1, 2, 3, 4, 5] as const) {
      const ending = resolveEnding({
        arc,
        hp: 100,
        maxHp: 100,
        credits: 0,
        missionsCompleted: 0,
        totalDeaths: 0,
        factionScores: {},
        choices: [],
      });
      expect(ending, `arc ${arc} resolved to undefined`).toBeDefined();
      expect(ending.arc, `arc ${arc} resolved to an ending from another arc`).toBe(arc);
    }
  });
});

/**
 * Tracked divergences. Each case asserts the design value, so it fails today
 * and `it.fails` records it as a known gap. When the code is brought in line,
 * the case flips to failing and forces this file to be updated.
 *
 * Only gaps that are *achievable in this tier* belong here. Deliberately
 * out-of-scope behaviour lives in the scope-boundary block below.
 */
describe("tracked divergences (expected failures)", () => {
  it.fails("Dixie attacks every 2000ms per combat.md L101 (code: 3000ms)", () => {
    expect(DIXIE_ATTACK_INTERVAL_MS).toBe(2000);
  });

  it.fails("Dixie deals fixed 5 damage per combat.md L102 (code: 8 base)", () => {
    expect(DIXIE_BASE_DAMAGE).toBe(5);
  });

  it.fails("Dixie has no combo bonus per combat.md L111 'fixed' (code: +3/combo)", () => {
    expect(DIXIE_SYNERGY_BONUS).toBe(0);
  });

  it.fails("at least one ending declares requiresFaction (faction scores are live in this tier)", () => {
    expect(ENDINGS.filter((e) => e.requiresFaction !== undefined).length).toBeGreaterThan(0);
  });
});

/**
 * Scope boundary. ADR-0199 scopes this tier to a single-mission-per-run MVP;
 * multi-mission arcs, meta-progression and a choice system belong to a later
 * milestone. These cases pin the boundary so it stays visible: they pass while
 * the tier is scoped as documented, and break if the scope changes without
 * updating this file.
 */
describe("scope boundary — deliberately out of this tier (ADR-0199)", () => {
  it("no ending declares requiresChoice — this tier has no choice system", () => {
    expect(ENDINGS.filter((e) => e.requiresChoice !== undefined)).toHaveLength(0);
  });

  it("the resolver's liberation branch needs missionsCompleted >= 3, unreachable in a one-mission run", () => {
    const base = {
      arc: 1 as const,
      hp: 100,
      maxHp: 100,
      credits: 0,
      totalDeaths: 0,
      factionScores: {},
      choices: [],
    };
    expect(resolveEnding({ ...base, missionsCompleted: 2 }).category).not.toBe("liberation");
    expect(resolveEnding({ ...base, missionsCompleted: 3 }).category).toBe("liberation");
  });
});
