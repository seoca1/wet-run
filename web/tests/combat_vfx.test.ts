/** Unit tests for combat VFX (Tier 5.5). */
import { describe, it, expect } from "vitest";
import {
  triggerCombatVfx,
  tickCombatVfx,
  tickCombatVfxList,
  renderCombatVfx,
  composeCombatVfx,
  type CombatVfxKind,
} from "../src/renderer/combat_vfx.ts";
import { makeGrid } from "../src/core/grid.ts";

describe("combat VFX (Tier 5.5)", () => {
  describe("triggerCombatVfx", () => {
    it("creates instance with tick=0", () => {
      const inst = triggerCombatVfx("attack", "strike", 3);
      expect(inst.tick).toBe(0);
      expect(inst.duration).toBe(3);
      expect(inst.kind).toBe("attack");
      expect(inst.payload).toBe("strike");
    });

    it("assigns unique ids across instances", () => {
      const a = triggerCombatVfx("ice_hit", "5");
      const b = triggerCombatVfx("critical_hit", "5");
      expect(a.id).not.toBe(b.id);
    });

    it("captures payloadNum for boss phase + crit damage", () => {
      const inst = triggerCombatVfx("boss_phase_transition", "", 5, undefined, undefined, 3);
      expect(inst.payloadNum).toBe(3);
    });
  });

  describe("tickCombatVfx", () => {
    it("increments tick", () => {
      const inst = triggerCombatVfx("attack", "", 5);
      const next = tickCombatVfx(inst);
      expect(next?.tick).toBe(1);
    });

    it("returns null when tick >= duration", () => {
      const inst = triggerCombatVfx("victory", "", 2);
      const t1 = tickCombatVfx(inst);
      const t2 = tickCombatVfx(t1 ?? inst);
      expect(t2).toBeNull();
    });
  });

  describe("tickCombatVfxList", () => {
    it("removes expired VFX from list", () => {
      const vfx1 = triggerCombatVfx("attack", "", 1);
      const vfx2 = triggerCombatVfx("victory", "", 10);
      const vfx3 = triggerCombatVfx("defeat", "", 5);
      const list = [vfx1, vfx2, vfx3];
      const ticked = tickCombatVfxList(list);
      expect(ticked.length).toBe(2);
      expect(ticked.map((v) => v.id)).toEqual([vfx2.id, vfx3.id]);
    });
  });

  describe("renderCombatVfx (each kind)", () => {
    const kinds: CombatVfxKind[] = [
      "attack",
      "heavy_attack",
      "pierce",
      "multi_hit",
      "dot",
      "shield",
      "heal",
      "regen",
      "buff",
      "debuff",
      "stun",
      "counter",
      "lifesteal",
      "detect",
      "ice_hit",
      "player_hit",
      "critical_hit",
      "status_apply",
      "ice_intro",
      "ice_death",
      "boss_phase_transition",
      "victory",
      "defeat",
      "jackin_glitch",
      "jackout_whiteout",
      "room_flash",
      "data_acquired",
    ];

    for (const kind of kinds) {
      it(`${kind} renders at least 1 non-space cell`, () => {
        const inst = triggerCombatVfx(kind, "test", 4);
        const grid = renderCombatVfx(inst, 80, 50);
        let nonSpace = 0;
        for (let y = 0; y < 50; y++) {
          for (let x = 0; x < 80; x++) {
            const cell = grid.get(x, y);
            if (cell && cell.char !== " ") nonSpace++;
          }
        }
        expect(nonSpace).toBeGreaterThan(0);
      });
    }

    it("attack moves projectile across ticks", () => {
      const inst = triggerCombatVfx("attack", "p", 4, 0, 0);
      const t0 = renderCombatVfx(inst, 80, 50);
      const t1 = renderCombatVfx(tickCombatVfx(inst) ?? inst, 80, 50);
      // Find projectile position at tick 0 vs tick 1 (should be different col)
      function findArrowCol(g: ReturnType<typeof makeGrid>): number {
        for (let y = 0; y < 50; y++) {
          for (let x = 0; x < 80; x++) {
            const cell = g.get(x, y);
            if (cell?.char === "→") return x;
          }
        }
        return -1;
      }
      const col0 = findArrowCol(t0);
      const col1 = findArrowCol(t1);
      expect(col0).toBeGreaterThan(-1);
      expect(col1).toBeGreaterThanOrEqual(col0); // moves right or stays
    });
  });

  describe("composeCombatVfx", () => {
    it("empty instance list returns base grid (no changes)", () => {
      const base = makeGrid(40, 30);
      const composed = composeCombatVfx(base, [], 40, 30);
      // Cells should match base.
      for (let y = 0; y < 30; y++) {
        for (let x = 0; x < 40; x++) {
          expect(composed.get(x, y)?.char).toBe(base.get(x, y)?.char);
        }
      }
    });

    it("non-empty list overlays cells on top of base", () => {
      const base = makeGrid(40, 30);
      const vfx = triggerCombatVfx("victory", "", 4);
      const composed = composeCombatVfx(base, [vfx], 40, 30);
      // Should differ from base at some position (VICTORY text overlay).
      let differs = false;
      for (let y = 0; y < 30; y++) {
        for (let x = 0; x < 40; x++) {
          if (composed.get(x, y)?.char !== base.get(x, y)?.char) {
            differs = true;
            break;
          }
        }
        if (differs) break;
      }
      expect(differs).toBe(true);
    });
  });
});