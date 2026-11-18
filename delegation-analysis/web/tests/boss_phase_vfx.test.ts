/** Unit tests for boss 4-phase VFX (Tier 5.6, ADR-0210 schema).
 *
 * Boss phase VFX is now a single kind `boss_phase_transition` with the
 * phase number passed via `payloadNum`. This matches the Python prototype
 * (single `boss_phase_transition_sequence(ice_type, phase)` factory).
 */
import { describe, it, expect } from "vitest";
import { renderCombatVfx, triggerCombatVfx } from "../src/renderer/combat_vfx.js";

function findLine(grid: ReturnType<typeof renderCombatVfx>, cols: number, y: number): string {
  let line = "";
  for (let x = 0; x < cols; x++) {
    line += grid.get(x, y)?.char ?? " ";
  }
  return line.trim();
}

describe("boss phase 4-phase VFX (Tier 5.6 unified schema)", () => {
  describe("renderCombatVfx boss_phase_transition phase=1", () => {
    it("header contains PHASE 1", () => {
      const inst = triggerCombatVfx("boss_phase_transition", "", 5, undefined, undefined, 1);
      const grid = renderCombatVfx(inst, 80, 50);
      const header = findLine(grid, 80, 1);
      expect(header).toContain("PHASE 1");
    });
    it("renders Sentinel scanning message", () => {
      const inst = triggerCombatVfx("boss_phase_transition", "", 5, undefined, undefined, 1);
      const grid = renderCombatVfx(inst, 80, 50);
      const lines: string[] = [];
      for (let y = 0; y < 50; y++) lines.push(findLine(grid, 80, y));
      expect(lines.some((l) => l.includes("Sentinel scanning"))).toBe(true);
    });
  });

  describe("renderCombatVfx boss_phase_transition phase=2", () => {
    it("contains PHASE 2 + alert message", () => {
      const inst = triggerCombatVfx("boss_phase_transition", "", 5, undefined, undefined, 2);
      const grid = renderCombatVfx(inst, 80, 50);
      const header = findLine(grid, 80, 1);
      expect(header).toContain("PHASE 2");
      const lines: string[] = [];
      for (let y = 0; y < 50; y++) lines.push(findLine(grid, 80, y));
      expect(lines.some((l) => l.includes("ICE alert"))).toBe(true);
    });
  });

  describe("renderCombatVfx boss_phase_transition phase=3", () => {
    it("contains PHASE 3 + enrage message", () => {
      const inst = triggerCombatVfx("boss_phase_transition", "", 5, undefined, undefined, 3);
      const grid = renderCombatVfx(inst, 80, 50);
      const header = findLine(grid, 80, 1);
      expect(header).toContain("PHASE 3");
      const lines: string[] = [];
      for (let y = 0; y < 50; y++) lines.push(findLine(grid, 80, y));
      expect(lines.some((l) => l.includes("ICE enrages"))).toBe(true);
    });
    it("renders red flicker row (Phase 3 special effect)", () => {
      const inst = triggerCombatVfx("boss_phase_transition", "", 5, undefined, undefined, 3);
      const grid = renderCombatVfx(inst, 80, 50);
      let hasEnrage = false;
      for (let x = 0; x < 80; x++) {
        if (grid.get(x, 7)?.char === "✶") hasEnrage = true;
      }
      expect(hasEnrage).toBe(true);
    });
  });

  describe("renderCombatVfx boss_phase_transition phase=4", () => {
    it("contains PHASE 4 + desperation message", () => {
      const inst = triggerCombatVfx("boss_phase_transition", "", 5, undefined, undefined, 4);
      const grid = renderCombatVfx(inst, 80, 50);
      const header = findLine(grid, 80, 1);
      expect(header).toContain("PHASE 4");
      const lines: string[] = [];
      for (let y = 0; y < 50; y++) lines.push(findLine(grid, 80, y));
      expect(lines.some((l) => l.includes("Desperation"))).toBe(true);
    });
    it("renders magenta pulse (Phase 4 special effect)", () => {
      const inst = triggerCombatVfx("boss_phase_transition", "", 5, undefined, undefined, 4);
      const grid = renderCombatVfx(inst, 80, 50);
      let hasPulse = false;
      for (let x = 0; x < 80; x++) {
        if (grid.get(x, 7)?.char === "★") hasPulse = true;
      }
      expect(hasPulse).toBe(true);
    });
  });

  describe("phase color differentiation", () => {
    it("phase 1 and 4 use different colors (cyan vs magenta)", () => {
      const inst1 = triggerCombatVfx("boss_phase_transition", "", 5, undefined, undefined, 1);
      const inst4 = triggerCombatVfx("boss_phase_transition", "", 5, undefined, undefined, 4);
      const grid1 = renderCombatVfx(inst1, 80, 50);
      const grid4 = renderCombatVfx(inst4, 80, 50);
      const cx = 40;
      const cell1 = grid1.get(cx, 1);
      const cell4 = grid4.get(cx, 1);
      expect(cell1?.fg).not.toBe(cell4?.fg);
    });
  });

  describe("payloadNum defaults", () => {
    it("falls back to phase 1 when payloadNum is undefined", () => {
      const inst = triggerCombatVfx("boss_phase_transition", "", 5);
      const grid = renderCombatVfx(inst, 80, 50);
      const header = findLine(grid, 80, 1);
      expect(header).toContain("PHASE 1");
    });
  });
});
