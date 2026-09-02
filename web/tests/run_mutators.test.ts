/** Unit tests for the run-mutators system.
 *
 * Run with: npx vitest run tests/run_mutators.test.ts
 *
 * Verifies mutator metadata, defaults, and the apply/clear lifecycle
 * for every mutator plus combinations. Mirrors the Python
 * `apply_mutators` / `clear_mutators` semantics on a `MutableRunState`.
 */

import { describe, it, expect } from "vitest";
import {
  ALL_MUTATORS,
  MUTATORS,
  applyMutators,
  clearMutators,
  getActiveMutators,
  getAlarmMultiplier,
  getEncounterMultiplier,
  getMutatorInfo,
  hpMultiplier,
  isHealDisabled,
  isMutatorActive,
  isStealthOnly,
  makeDefaultMutableRunState,
  type MutableRunState,
  type RunMutator,
} from "../src/core/run_mutators.ts";

describe("mutator catalog", () => {
  it("declares exactly 5 mutators", () => {
    expect(ALL_MUTATORS.length).toBe(5);
    expect(Object.keys(MUTATORS).length).toBe(5);
  });

  it("ALL_MUTATORS lists every documented mutator", () => {
    expect(new Set(ALL_MUTATORS)).toEqual(
      new Set<RunMutator>(["low_hp", "double_alarm", "ice_x2", "no_heal", "stealth_only"]),
    );
  });

  it("every mutator has a non-empty name, description, icon", () => {
    for (const id of ALL_MUTATORS) {
      const info = MUTATORS[id];
      expect(info.name.length).toBeGreaterThan(0);
      expect(info.description.length).toBeGreaterThan(0);
      expect(info.icon.length).toBeGreaterThan(0);
      expect(info.id).toBe(id);
    }
  });

  it("getMutatorInfo returns the matching catalog entry", () => {
    expect(getMutatorInfo("low_hp").name).toBe("FRAGILE WETWARE");
    expect(getMutatorInfo("stealth_only").icon).toBe("stealth_only");
  });
});

describe("hpMultiplier", () => {
  it("returns 0.5 for LOW_HP and 1.0 for everything else", () => {
    expect(hpMultiplier("low_hp")).toBe(0.5);
    expect(hpMultiplier("double_alarm")).toBe(1.0);
    expect(hpMultiplier("ice_x2")).toBe(1.0);
    expect(hpMultiplier("no_heal")).toBe(1.0);
    expect(hpMultiplier("stealth_only")).toBe(1.0);
  });
});

describe("default run state", () => {
  it("uses the documented baseline values", () => {
    const s = makeDefaultMutableRunState();
    expect(s.playerHp).toBe(100);
    expect(s.playerMaxHp).toBe(100);
    expect(s.alarmSpeedMultiplier).toBe(1.0);
    expect(s.encounterMultiplier).toBe(1);
    expect(s.healDisabled).toBe(false);
    expect(s.skillFilter).toBeNull();
    expect(s.activeMutators.length).toBe(0);
  });

  it("is the same as a hand-rolled baseline", () => {
    const hand: MutableRunState = {
      playerHp: 100,
      playerMaxHp: 100,
      alarmSpeedMultiplier: 1.0,
      encounterMultiplier: 1,
      healDisabled: false,
      skillFilter: null,
      activeMutators: [],
    };
    expect(makeDefaultMutableRunState()).toEqual(hand);
  });
});

describe("applyMutators", () => {
  it("LOW_HP halves max HP and clamps current HP", () => {
    const s: MutableRunState = { ...makeDefaultMutableRunState(), playerHp: 80 };
    applyMutators(s, ["low_hp"]);
    expect(s.playerMaxHp).toBe(50);
    expect(s.playerHp).toBe(50); // clamped from 80 to new max
    expect(s.activeMutators).toEqual(["low_hp"]);
  });

  it("LOW_HP on zero maxHp initializes to 100 baseline before halving (GA-003 parity)", () => {
    const s: MutableRunState = { ...makeDefaultMutableRunState(), playerHp: 0, playerMaxHp: 0 };
    applyMutators(s, ["low_hp"]);
    expect(s.playerMaxHp).toBe(50);
    expect(s.playerHp).toBe(0);
  });

  it("LOW_HP at full HP keeps HP at the new max", () => {
    const s = makeDefaultMutableRunState();
    applyMutators(s, ["low_hp"]);
    expect(s.playerHp).toBe(50);
    expect(s.playerMaxHp).toBe(50);
  });

  it("DOUBLE_ALARM sets alarm multiplier to 2.0", () => {
    const s = makeDefaultMutableRunState();
    applyMutators(s, ["double_alarm"]);
    expect(s.alarmSpeedMultiplier).toBe(2.0);
  });

  it("ICE_X2 sets encounter multiplier to 2", () => {
    const s = makeDefaultMutableRunState();
    applyMutators(s, ["ice_x2"]);
    expect(s.encounterMultiplier).toBe(2);
  });

  it("NO_HEAL disables HEAL salvage", () => {
    const s = makeDefaultMutableRunState();
    applyMutators(s, ["no_heal"]);
    expect(s.healDisabled).toBe(true);
  });

  it("STEALTH_ONLY sets skill filter to 'stealth_only'", () => {
    const s = makeDefaultMutableRunState();
    applyMutators(s, ["stealth_only"]);
    expect(s.skillFilter).toBe("stealth_only");
  });

  it("applies multiple mutators in one call", () => {
    const s = makeDefaultMutableRunState();
    applyMutators(s, ["low_hp", "ice_x2", "stealth_only"]);
    expect(s.playerMaxHp).toBe(50);
    expect(s.encounterMultiplier).toBe(2);
    expect(s.skillFilter).toBe("stealth_only");
    expect(s.activeMutators).toEqual(["low_hp", "ice_x2", "stealth_only"]);
  });

  it("applyMutators is idempotent (re-applies after clearing)", () => {
    const s = makeDefaultMutableRunState();
    applyMutators(s, ["low_hp"]);
    expect(s.playerMaxHp).toBe(50);
    applyMutators(s, ["low_hp"]);
    // Clear restored to 100, then halved again → 50 (not 25).
    expect(s.playerMaxHp).toBe(50);
    expect(s.activeMutators).toEqual(["low_hp"]);
  });

  it("applying a different mutator set clears the previous one first", () => {
    const s: MutableRunState = { ...makeDefaultMutableRunState(), playerHp: 100 };
    applyMutators(s, ["low_hp", "double_alarm"]);
    expect(s.playerMaxHp).toBe(50);
    expect(s.alarmSpeedMultiplier).toBe(2.0);
    // Re-apply without LOW_HP → maxHp should restore to 100.
    applyMutators(s, ["double_alarm"]);
    expect(s.playerMaxHp).toBe(100);
    expect(s.alarmSpeedMultiplier).toBe(2.0);
    expect(s.activeMutators).toEqual(["double_alarm"]);
  });

  it("empty mutator list clears everything and records empty active set", () => {
    const s = makeDefaultMutableRunState();
    applyMutators(s, ["low_hp", "ice_x2"]);
    applyMutators(s, []);
    expect(s.playerMaxHp).toBe(100);
    expect(s.encounterMultiplier).toBe(1);
    expect(s.activeMutators).toEqual([]);
  });
});

describe("clearMutators", () => {
  it("doubles max HP after LOW_HP (round-trip)", () => {
    const s = makeDefaultMutableRunState();
    applyMutators(s, ["low_hp"]);
    expect(s.playerMaxHp).toBe(50);
    clearMutators(s);
    expect(s.playerMaxHp).toBe(100);
    expect(s.activeMutators).toEqual([]);
  });

  it("resets alarm multiplier to 1.0", () => {
    const s = makeDefaultMutableRunState();
    applyMutators(s, ["double_alarm"]);
    clearMutators(s);
    expect(s.alarmSpeedMultiplier).toBe(1.0);
  });

  it("resets encounter multiplier to 1", () => {
    const s = makeDefaultMutableRunState();
    applyMutators(s, ["ice_x2"]);
    clearMutators(s);
    expect(s.encounterMultiplier).toBe(1);
  });

  it("re-enables HEAL", () => {
    const s = makeDefaultMutableRunState();
    applyMutators(s, ["no_heal"]);
    clearMutators(s);
    expect(s.healDisabled).toBe(false);
  });

  it("clears skill filter", () => {
    const s = makeDefaultMutableRunState();
    applyMutators(s, ["stealth_only"]);
    clearMutators(s);
    expect(s.skillFilter).toBeNull();
  });

  it("clearMutators on an empty state is a safe no-op", () => {
    const s = makeDefaultMutableRunState();
    clearMutators(s);
    expect(s.playerMaxHp).toBe(100);
    expect(s.alarmSpeedMultiplier).toBe(1.0);
    expect(s.activeMutators).toEqual([]);
  });

  it("LOW_HP clear skips doubling when maxHp is already 0 (no crash)", () => {
    const s: MutableRunState = {
      ...makeDefaultMutableRunState(),
      playerMaxHp: 0,
      activeMutators: ["low_hp"],
    };
    clearMutators(s);
    expect(s.playerMaxHp).toBe(0);
  });
});

describe("query helpers", () => {
  it("isMutatorActive reflects the active list", () => {
    const s = makeDefaultMutableRunState();
    expect(isMutatorActive(s, "low_hp")).toBe(false);
    applyMutators(s, ["low_hp", "ice_x2"]);
    expect(isMutatorActive(s, "low_hp")).toBe(true);
    expect(isMutatorActive(s, "ice_x2")).toBe(true);
    expect(isMutatorActive(s, "no_heal")).toBe(false);
  });

  it("getActiveMutators returns a defensive copy", () => {
    const s = makeDefaultMutableRunState();
    applyMutators(s, ["low_hp"]);
    const active = getActiveMutators(s);
    expect(active).toEqual(["low_hp"]);
    // Mutating the returned array must not change state.
    (active as RunMutator[]).push("ice_x2");
    expect(getActiveMutators(s)).toEqual(["low_hp"]);
  });

  it("getAlarmMultiplier reads the current alarm multiplier", () => {
    const s = makeDefaultMutableRunState();
    expect(getAlarmMultiplier(s)).toBe(1.0);
    applyMutators(s, ["double_alarm"]);
    expect(getAlarmMultiplier(s)).toBe(2.0);
  });

  it("getEncounterMultiplier reads the current encounter multiplier", () => {
    const s = makeDefaultMutableRunState();
    expect(getEncounterMultiplier(s)).toBe(1);
    applyMutators(s, ["ice_x2"]);
    expect(getEncounterMultiplier(s)).toBe(2);
  });

  it("isHealDisabled reflects NO_HEAL", () => {
    const s = makeDefaultMutableRunState();
    expect(isHealDisabled(s)).toBe(false);
    applyMutators(s, ["no_heal"]);
    expect(isHealDisabled(s)).toBe(true);
  });

  it("isStealthOnly reflects STEALTH_ONLY", () => {
    const s = makeDefaultMutableRunState();
    expect(isStealthOnly(s)).toBe(false);
    applyMutators(s, ["stealth_only"]);
    expect(isStealthOnly(s)).toBe(true);
  });
});

describe("end-to-end lifecycle", () => {
  it("apply → clear restores every mutator field to the baseline (playerHp may remain clamped by LOW_HP — Python parity)", () => {
    const combos: ReadonlyArray<ReadonlyArray<RunMutator>> = [
      ["double_alarm"],
      ["ice_x2"],
      ["no_heal"],
      ["stealth_only"],
      ["low_hp", "double_alarm"],
      ["low_hp", "ice_x2", "no_heal"],
      [...ALL_MUTATORS],
    ];
    for (const combo of combos) {
      const baseline = makeDefaultMutableRunState();
      const s = makeDefaultMutableRunState();
      applyMutators(s, combo);
      clearMutators(s);
      // playerMaxHp, alarmSpeedMultiplier, encounterMultiplier, healDisabled,
      // skillFilter, activeMutators must all restore. playerHp is left alone
      // on purpose (matches the Python `clear_mutators` semantics).
      expect(s.playerMaxHp).toBe(baseline.playerMaxHp);
      expect(s.alarmSpeedMultiplier).toBe(baseline.alarmSpeedMultiplier);
      expect(s.encounterMultiplier).toBe(baseline.encounterMultiplier);
      expect(s.healDisabled).toBe(baseline.healDisabled);
      expect(s.skillFilter).toBe(baseline.skillFilter);
      expect(s.activeMutators).toEqual(baseline.activeMutators);
    }
  });

  it("LOW_HP alone leaves playerHp clamped at the new max after clear", () => {
    const s = makeDefaultMutableRunState();
    applyMutators(s, ["low_hp"]);
    expect(s.playerHp).toBe(50);
    expect(s.playerMaxHp).toBe(50);
    clearMutators(s);
    expect(s.playerMaxHp).toBe(100);
    expect(s.playerHp).toBe(50); // unchanged — Python parity
  });

  it("two consecutive apply calls with the same list keep the same final state", () => {
    const a = makeDefaultMutableRunState();
    const b = makeDefaultMutableRunState();
    applyMutators(a, ["low_hp", "ice_x2"]);
    applyMutators(b, ["low_hp", "ice_x2"]);
    applyMutators(b, ["low_hp", "ice_x2"]); // idempotent (clears first)
    expect(a).toEqual(b);
  });
});
