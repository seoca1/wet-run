import { describe, it, expect } from "vitest";
import { DEFAULT_BOSS_PROFILE, checkPhaseTransition, getPhaseDamageMultiplier } from "../src/core/boss_phases";

describe("boss_phases: checkPhaseTransition", () => {
  it("stays in phase 1 when boss is at full HP", () => {
    const tracker = {
      bossProfile: DEFAULT_BOSS_PROFILE,
      currentPhase: 1,
      phaseChangeMs: 0,
      phaseChangeColor: "#ffffff",
    };
    const updated = checkPhaseTransition(tracker, 100, 100, 1000);
    expect(updated.currentPhase).toBe(1);
  });

  it("transitions to phase 2 when boss drops to 74% HP", () => {
    const tracker = {
      bossProfile: DEFAULT_BOSS_PROFILE,
      currentPhase: 1,
      phaseChangeMs: 0,
      phaseChangeColor: "#ffffff",
    };
    const updated = checkPhaseTransition(tracker, 74, 100, 1000);
    expect(updated.currentPhase).toBe(2);
    expect(updated.phaseChangeMs).toBe(1000);
  });

  it("transitions to phase 3 when boss drops to 50% HP", () => {
    const tracker = {
      bossProfile: DEFAULT_BOSS_PROFILE,
      currentPhase: 2,
      phaseChangeMs: 0,
      phaseChangeColor: "#ffffff",
    };
    const updated = checkPhaseTransition(tracker, 50, 100, 2000);
    expect(updated.currentPhase).toBe(3);
  });

  it("transitions to phase 4 (desperation) when boss drops to 25% HP", () => {
    const tracker = {
      bossProfile: DEFAULT_BOSS_PROFILE,
      currentPhase: 3,
      phaseChangeMs: 0,
      phaseChangeColor: "#ffffff",
    };
    const updated = checkPhaseTransition(tracker, 25, 100, 3000);
    expect(updated.currentPhase).toBe(4);
  });

  it("stays in phase 4 once reached (does not exceed 4)", () => {
    const tracker = {
      bossProfile: DEFAULT_BOSS_PROFILE,
      currentPhase: 4,
      phaseChangeMs: 0,
      phaseChangeColor: "#ffffff",
    };
    const updated = checkPhaseTransition(tracker, 10, 100, 4000);
    expect(updated.currentPhase).toBe(4);
  });

  it("does not transition backwards when HP rises (phase downgrade prevented)", () => {
    const tracker = {
      bossProfile: DEFAULT_BOSS_PROFILE,
      currentPhase: 3,
      phaseChangeMs: 0,
      phaseChangeColor: "#ffffff",
    };
    const updated = checkPhaseTransition(tracker, 100, 100, 5000);
    expect(updated.currentPhase).toBe(3);
  });

  it("returns tracker unchanged when bossProfile is null", () => {
    const tracker = {
      bossProfile: null,
      currentPhase: 2,
      phaseChangeMs: 100,
      phaseChangeColor: "#ff0000",
    };
    const updated = checkPhaseTransition(tracker, 10, 100, 2000);
    expect(updated).toEqual(tracker);
  });

  it("returns tracker unchanged when currentPhase >= 4", () => {
    const tracker = {
      bossProfile: DEFAULT_BOSS_PROFILE,
      currentPhase: 4,
      phaseChangeMs: 500,
      phaseChangeColor: "#00ff00",
    };
    const updated = checkPhaseTransition(tracker, 10, 100, 2000);
    expect(updated).toEqual(tracker);
  });
});

describe("boss_phases: getPhaseDamageMultiplier", () => {
  it("returns 1.0 for phase 0 (no boss)", () => {
    const tracker = {
      bossProfile: null,
      currentPhase: 0,
      phaseChangeMs: 0,
      phaseChangeColor: "#ffffff",
    };
    expect(getPhaseDamageMultiplier(tracker)).toBe(1.0);
  });

  it("returns the matching phase's damageMultiplier", () => {
    const tracker = {
      bossProfile: DEFAULT_BOSS_PROFILE,
      currentPhase: 3,
      phaseChangeMs: 0,
      phaseChangeColor: "#ffffff",
    };
    const mult = getPhaseDamageMultiplier(tracker);
    expect(mult).toBeGreaterThan(1.0);
  });
});
