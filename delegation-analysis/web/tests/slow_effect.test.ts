/** Unit tests for slow effect damage reduction (Tier 5.5+). */
import { describe, it, expect, vi } from "vitest";
import { applyAction } from "../src/core/state.js";
import type { GameState, Ice, Mission, Program } from "../src/core/types.js";
import { makeInitialState } from "../src/core/state.js";
import { applyStatus } from "../src/core/status.js";

const mockMission: Mission = {
  id: "test", title: "T", fixer: "x", arc: 1, zone: "test",
  grade_min: 1, grade_max: 1, rewards: { credits: 0, materials: {} },
};
const mockIce: Ice = { id: "ice1", name: "ICE", hp: 100, armor: 0, tier: 1 };
const mockPrograms: ReadonlyArray<Program> = [
  { id: "p1", name: "P1", tier: 1, cost: 10, effect: "e", description: "", aoe: false },
];

function buildCombatState(): GameState {
  const base = makeInitialState(mockMission, mockIce, mockPrograms);
  return {
    ...base,
    runPhase: "combat",
    phase: "combat",
    iceRoster: [{ ...mockIce }],
    activeIceIndex: 0,
    dixieLastAttackMs: Date.now(),
  };
}

describe("slow effect damage reduction (Tier 5.5+)", () => {
  // Base damage formula: program.tier * 5. mockPrograms uses tier 1 → base dmg 5.
  it("reduces damage by slow magnitude% (50% slow = 2 damage instead of 5)", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.99); // suppress burn proc
    let state = buildCombatState();
    state = applyStatus(state, "ice", "slow", 3, 50); // 50% slow for 3 turns
    const next = applyAction(state, { type: "use_program", programId: "p1" });
    const activeIce = next.iceRoster[next.activeIceIndex];
    // Math.floor((5 * 50) / 100) = 2 reduction → damage = 5 - 2 = 3 → hp = 97.
    expect(activeIce?.hp).toBe(97);
  });

  it("slow only reduces damage taken by ICE (not player attacks)", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    let state = buildCombatState();
    state = applyStatus(state, "ice", "slow", 3, 80); // 80% slow
    const next = applyAction(state, { type: "use_program", programId: "p1" });
    const activeIce = next.iceRoster[next.activeIceIndex];
    // 100 - (5 * 0.2) = 99
    expect(activeIce?.hp).toBe(99);
  });

  it("slow consumed after one attack (one-shot)", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    let state = buildCombatState();
    state = applyStatus(state, "ice", "slow", 3, 50);
    // Before attack: slow present.
    expect(state.statusEffects.some((e) => e.kind === "slow")).toBe(true);
    state = applyAction(state, { type: "use_program", programId: "p1" });
    // After attack: slow consumed (one-shot behavior).
    const remainingSlow = state.statusEffects.filter((e) => e.kind === "slow").length;
    expect(remainingSlow).toBe(0);
  });

  it("slow on player (not ICE) does not affect ICE damage", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    let state = buildCombatState();
    state = applyStatus(state, "player", "slow", 3, 99); // slow on player (target mismatch)
    const next = applyAction(state, { type: "use_program", programId: "p1" });
    // Slow on player doesn't reduce ICE damage → ICE hp = 100 - 5 = 95.
    const activeIce = next.iceRoster[next.activeIceIndex];
    expect(activeIce?.hp).toBe(95);
  });

  it("slow with 0 magnitude has no effect (no division by zero)", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    let state = buildCombatState();
    state = applyStatus(state, "ice", "slow", 3, 0);
    const next = applyAction(state, { type: "use_program", programId: "p1" });
    const activeIce = next.iceRoster[next.activeIceIndex];
    // Full damage, slow 0% = no reduction → 100 - 5 = 95.
    expect(activeIce?.hp).toBe(95);
  });

  it("slow doesn't push damage below 1 (minimum damage)", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.99);
    let state = buildCombatState();
    state = applyStatus(state, "ice", "slow", 3, 100); // 100% slow
    const next = applyAction(state, { type: "use_program", programId: "p1" });
    const activeIce = next.iceRoster[next.activeIceIndex];
    // Math.max(1, 5 - 5) = 1 → 100 - 1 = 99
    expect(activeIce?.hp).toBe(99);
  });
});
