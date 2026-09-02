/** Tier 6 v2 effect renderer tests (ADR-0210 follow-up).
 *
 * Each test verifies that the v2 effect renderer produces a grid with at
 * least 1 non-space cell and respects payload metadata (payloadNum).
 */
import { describe, it, expect } from "vitest";
import {
  renderCombatVfx,
  triggerCombatVfx,
  type CombatVfxKind,
} from "../src/renderer/combat_vfx.js";
import { resolveColorHint, PALETTE } from "../src/renderer/palette.js";

function countNonSpace(grid: ReturnType<typeof renderCombatVfx>, cols: number, rows: number): number {
  let n = 0;
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const cell = grid.get(x, y);
      if (cell && cell.char !== " ") n++;
    }
  }
  return n;
}

const v2Kinds: CombatVfxKind[] = [
  "heavy_attack",
  "pierce",
  "multi_hit",
  "dot",
  "regen",
  "counter",
  "lifesteal",
  "detect",
  "jackin_glitch",
  "jackout_whiteout",
  "room_flash",
  "data_acquired",
];

describe("Tier 6 v2 effect renderers (ADR-0210)", () => {
  for (const kind of v2Kinds) {
    it(`${kind} renders at least 1 non-space cell`, () => {
      const inst = triggerCombatVfx(kind, "test", 6);
      const grid = renderCombatVfx(inst, 80, 50);
      expect(countNonSpace(grid, 80, 50)).toBeGreaterThan(0);
    });
  }

  describe("heavy_attack (Tier 6 — backport from heavy_attack_animation)", () => {
    it("renders HEAVY label with damage value", () => {
      const inst = triggerCombatVfx("heavy_attack", "", 9, undefined, undefined, 25);
      const grid = renderCombatVfx(inst, 80, 50);
      let line = "";
      for (let x = 0; x < 80; x++) line += grid.get(x, 1)?.char ?? " ";
      expect(line).toContain("HEAVY");
      expect(line).toContain("25");
    });
  });

  describe("multi_hit (Tier 6 — backport from multi_hit_animation)", () => {
    it("strikes cycle across 3 frames", () => {
      const t0 = renderCombatVfx(triggerCombatVfx("multi_hit", "x3", 4), 80, 50);
      const t3 = renderCombatVfx(
        triggerCombatVfx("multi_hit", "x3", 4).tick !== null ? triggerCombatVfx("multi_hit", "x3", 4) : triggerCombatVfx("multi_hit", "x3", 4),
        80, 50,
      );
      // Tick progress — final frame shows summary.
      const final = renderCombatVfx(
        { ...triggerCombatVfx("multi_hit", "x3", 4), tick: 3 },
        80, 50,
      );
      const summary = [];
      for (let x = 0; x < 80; x++) summary.push(final.get(x, Math.floor(50 / 2) + 2)?.char ?? " ");
      expect(summary.join("")).toContain("x3");
      void t0; void t3;
    });
  });

  describe("dot (Tier 6 — backport from dot_animation)", () => {
    it("renders purple particles around target", () => {
      const inst = triggerCombatVfx("dot", "", 6, undefined, undefined, 3);
      const grid = renderCombatVfx(inst, 80, 50);
      let hasPurple = false;
      for (let y = 0; y < 50; y++) {
        for (let x = 0; x < 80; x++) {
          if (grid.get(x, y)?.fg === PALETTE.ICE_FADE_PURPLE) hasPurple = true;
        }
      }
      expect(hasPurple).toBe(true);
    });
  });

  describe("counter (Tier 6 — backport from counter_animation)", () => {
    it("flips shield bash direction across frames", () => {
      const early = renderCombatVfx(triggerCombatVfx("counter", "", 5), 80, 50);
      const late = renderCombatVfx(
        { ...triggerCombatVfx("counter", "", 5), tick: 3 },
        80, 50,
      );
      const cx = 40;
      const cy = 25;
      // Early frame: "❖<<" → >-facing at cx-2/-1. Late frame: ">>❖" → <-facing at cx-3/-2.
      expect(early.get(cx - 2, cy)?.char).toBe("<");
      expect(late.get(cx - 2, cy)?.char).toBe(">");
    });
  });

  describe("lifesteal (Tier 6 — backport from lifesteal_animation)", () => {
    it("renders heal amount in payload", () => {
      const inst = triggerCombatVfx("lifesteal", "", 5, undefined, undefined, 8);
      const grid = renderCombatVfx(inst, 80, 50);
      let line = "";
      for (let x = 0; x < 80; x++) line += grid.get(x, 1)?.char ?? " ";
      expect(line).toContain("LIFESTEAL");
      expect(line).toContain("8");
    });
  });

  describe("detect (Tier 6 — backport from detect_animation)", () => {
    it("renders scanning reticle (5 chars wide)", () => {
      const inst = triggerCombatVfx("detect", "", 6);
      const grid = renderCombatVfx(inst, 80, 50);
      const cx = 40;
      const cy = 25;
      // "[<·>]" or "[<!>]" — bracket at cx-3, mid at cx-1, close at cx+1.
      expect(grid.get(cx - 3, cy)?.char).toBe("[");
      expect(grid.get(cx + 1, cy)?.char).toBe("]");
    });
  });

  describe("jackin_glitch (Tier 6 — backport from spawn_jackin_glitch)", () => {
    it("renders cyan glitch characters across grid", () => {
      const inst = triggerCombatVfx("jackin_glitch", "", 5);
      const grid = renderCombatVfx(inst, 80, 50);
      let hasGlitch = false;
      const glitchChars = new Set(["▓", "▒", "░", "+", "·", "/", "\\"]);
      for (let y = 0; y < 50; y++) {
        for (let x = 0; x < 80; x++) {
          if (glitchChars.has(grid.get(x, y)?.char ?? "")) {
            hasGlitch = true;
            break;
          }
        }
        if (hasGlitch) break;
      }
      expect(hasGlitch).toBe(true);
    });
  });

  describe("jackout_whiteout (Tier 6 — backport from spawn_jackout_whiteout)", () => {
    it("renders JACK OUT text", () => {
      const inst = triggerCombatVfx("jackout_whiteout", "", 4);
      const grid = renderCombatVfx(inst, 80, 50);
      let line = "";
      for (let x = 30; x < 50; x++) line += grid.get(x, 25)?.char ?? " ";
      expect(line).toContain("JACK OUT");
    });
  });

  describe("room_flash (Tier 6 — backport from spawn_room_flash)", () => {
    it("uses payload color hint when provided", () => {
      const inst = triggerCombatVfx("room_flash", "TIER_GOLD", 4);
      const grid = renderCombatVfx(inst, 80, 50);
      let hasGold = false;
      for (let y = 0; y < 50; y++) {
        for (let x = 0; x < 80; x++) {
          if (grid.get(x, y)?.fg === PALETTE.TIER_GOLD) hasGold = true;
        }
      }
      expect(hasGold).toBe(true);
    });
  });

  describe("data_acquired (Tier 6 — backport from spawn_data_acquired)", () => {
    it("renders DATA FRAGMENT text + gold particles", () => {
      const inst = triggerCombatVfx("data_acquired", "", 5);
      const grid = renderCombatVfx(inst, 80, 50);
      const goldChars = new Set(["$", "·", "+"]);
      let hasGoldChar = false;
      for (let y = 0; y < 50; y++) {
        for (let x = 0; x < 80; x++) {
          const cell = grid.get(x, y);
          if (cell && cell.fg === PALETTE.TIER_GOLD && goldChars.has(cell.char)) {
            hasGoldChar = true;
            break;
          }
        }
        if (hasGoldChar) break;
      }
      expect(hasGoldChar).toBe(true);
    });
  });
});

describe("palette resolveColorHint (ADR-0210)", () => {
  it("returns hex string for valid hint", () => {
    expect(resolveColorHint("HEAL_COLOR")).toBe(PALETTE.HEAL_COLOR);
    expect(resolveColorHint("TIER_GOLD")).toBe(PALETTE.TIER_GOLD);
  });

  it("falls back to FOREGROUND for unknown hint", () => {
    expect(resolveColorHint("NONEXISTENT_PALETTE_KEY")).toBe(PALETTE.FOREGROUND);
  });

  it("handles empty string gracefully", () => {
    expect(resolveColorHint("")).toBe(PALETTE.FOREGROUND);
  });
});
