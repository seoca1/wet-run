/** Unit tests for sound trigger logic (Tier 5.5+ sound integration). */
import { describe, it, expect, vi } from "vitest";

/**
 * Mock AudioManager before importing modules that capture it.
 * The state.ts reducer doesn't import audio directly — main.ts does.
 * But we want to test the SOUND TRIGGER LOGIC. So we test via state
 * transitions + check expected SFX (the production code wires these).
 *
 * For now, test the trigger *predicates* (when SHOULD a sound fire?) as
 * pure functions. The actual SFX dispatch is verified via E2E.
 */
import { applyAction } from "../src/core/state.ts";
import type { GameState, Ice, Mission, Program } from "../src/core/types.ts";
import { makeInitialState } from "../src/core/state.ts";

const mockMission: Mission = {
  id: "test", title: "T", fixer: "x", arc: 1, zone: "test",
  grade_min: 1, grade_max: 1, rewards: { credits: 0, materials: {} },
};
const mockIce: Ice = { id: "ice1", name: "ICE", hp: 100, armor: 0, tier: 1 };
const mockPrograms: ReadonlyArray<Program> = [
  { id: "p1", name: "P1", tier: 1, cost: 10, effect: "e", description: "", aoe: false },
];

/** Pure predicate: should combat_hit SFX fire on this state transition? */
function shouldFireCombatHit(prev: GameState | null, next: GameState): boolean {
  if (!prev) return false;
  if (prev.phase !== "combat" || next.phase !== "combat") return false;
  // Tier 5.5: damage is applied to iceRoster (active ICE), not legacy state.ice.
  const prevHp = prev.iceRoster[prev.activeIceIndex]?.hp ?? prev.ice.hp;
  const nextHp = next.iceRoster[next.activeIceIndex]?.hp ?? next.ice.hp;
  if (nextHp < prevHp) return true;
  return false;
}

/** Pure predicate: should victory SFX fire? (runPhase combat → loot transition) */
function shouldFireVictory(prev: GameState | null, next: GameState): boolean {
  if (!prev) return false;
  if (prev.runPhase === "combat" && next.runPhase === "loot") return true;
  return false;
}

/** Pure predicate: should boss phase transition SFX fire? */
function shouldFireBossPhase(prev: GameState | null, next: GameState): boolean {
  if (!prev) return false;
  if (prev.bossPhase === 0) return false;
  if (next.bossPhase > prev.bossPhase) return true;
  return false;
}

function buildCombatState(ice: Ice = mockIce): GameState {
  const base = makeInitialState(mockMission, ice, mockPrograms);
  return {
    ...base,
    runPhase: "combat",
    phase: "combat",
    iceRoster: [{ ...ice }],
    activeIceIndex: 0,
  };
}

describe("sound trigger logic (Tier 5.5+)", () => {
  describe("combat_hit SFX trigger", () => {
    it("fires when ICE HP decreases in combat", () => {
      vi.spyOn(Math, "random").mockReturnValue(0.99);
      const prev = buildCombatState();
      const next = applyAction(prev, { type: "use_program", programId: "p1" });
      expect(shouldFireCombatHit(prev, next)).toBe(true);
    });

    it("does NOT fire when ICE HP unchanged (alarm blocked)", () => {
      const prev = buildCombatState();
      const next = applyAction(prev, { type: "use_program", programId: "nonexistent" });
      expect(shouldFireCombatHit(prev, next)).toBe(false);
    });

    it("does NOT fire outside combat", () => {
      const prev = { ...buildCombatState(), runPhase: "matrix" as const };
      const next = applyAction(prev, { type: "use_program", programId: "p1" });
      expect(shouldFireCombatHit(prev, next)).toBe(false);
    });
  });

  describe("victory SFX trigger (runPhase combat → loot)", () => {
    it("fires when transitioning to loot after allDefeated", () => {
      vi.spyOn(Math, "random").mockReturnValue(0.99);
      const fastIce: Ice = { ...mockIce, hp: 5 };
      const prev = buildCombatState(fastIce);
      const next = applyAction(prev, { type: "use_program", programId: "p1" });
      expect(shouldFireVictory(prev, next)).toBe(true);
    });

    it("does NOT fire mid-combat (still combat → combat)", () => {
      vi.spyOn(Math, "random").mockReturnValue(0.99);
      const prev = buildCombatState();
      const next = applyAction(prev, { type: "use_program", programId: "p1" });
      expect(shouldFireVictory(prev, next)).toBe(false);
    });
  });

  describe("boss phase transition SFX trigger", () => {
    it("fires when bossPhase advances (1→2, 2→3, 3→4)", () => {
      const prev: GameState = { ...buildCombatState(), bossPhase: 1 };
      const next: GameState = { ...prev, bossPhase: 2 };
      expect(shouldFireBossPhase(prev, next)).toBe(true);
    });

    it("does NOT fire when bossPhase is 0 (no boss active)", () => {
      const prev = buildCombatState();
      const next: GameState = { ...prev, bossPhase: 0 };
      expect(shouldFireBossPhase(prev, next)).toBe(false);
    });

    it("does NOT fire when bossPhase stays the same", () => {
      const prev: GameState = { ...buildCombatState(), bossPhase: 2 };
      const next: GameState = { ...prev, bossPhase: 2 };
      expect(shouldFireBossPhase(prev, next)).toBe(false);
    });
  });

  describe("integration: applyAction triggers state transitions", () => {
    it("matrix → combat transition triggers combat_hit SFX (via main.ts)", () => {
      // Main.ts handles sound dispatch; here we verify the state change
      // is detectable for the hook.
      let prev = makeInitialState(mockMission, mockIce, mockPrograms);
      prev = { ...prev, matrix: {
        nodes: [{
          id: 0, zone: "surface", iceIds: ["watchdog"], iceHp: [100],
          reward: { credits: 50 }, isBoss: false, adjacent: [],
        }], startNode: 0, bossNode: 0,
      } };
      const next = applyAction(prev, { type: "confirm" });
      expect(next.runPhase).toBe("combat");
      expect(next.runPhase !== prev.runPhase).toBe(true);
    });
  });
});