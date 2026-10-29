/** P3 — floating damage numbers (unit tests).
 *
 * Today the only damage readout is a fixed-position `HIT! -N` text line
 * (`src/renderer/combat_vfx_render_combat.ts`). The design spec
 * (`docs/design/systems/animations.md`) asks for a damage number that
 * *floats up* from the impact point and branches on colour + size:
 *
 * - normal attack  → small, white `-5`   (animations.md:38-39)
 * - skill attack   → large, yellow `-25` (animations.md:60-61)
 * - critical       → CRIT colour, largest (animations.md:108-112)
 *
 * These tests pin the geometry (start anchor → rising row), the colour
 * branching, and the size branching as pure functions so the ASCII/Canvas2D
 * aesthetic is preserved.
 */
import { describe, it, expect } from "vitest";
import {
  FLOATING_DAMAGE_KINDS,
  floatingDamageFor,
  floatingDamageKindFor,
  floatingDamageRows,
  renderFloatingDamage,
} from "../src/renderer/floating_damage.js";
import { PALETTE } from "../src/renderer/palette.js";
import { makeGrid } from "../src/core/grid.js";

describe("P3 floating damage — kind table", () => {
  it("covers the normal / skill / critical branches", () => {
    expect([...FLOATING_DAMAGE_KINDS].sort()).toEqual([
      "critical",
      "normal",
      "skill",
    ]);
  });
});

describe("P3 floatingDamageFor — geometry", () => {
  it("renders a signed negative number for the normal branch", () => {
    const f = floatingDamageFor("normal", 5, 0, 10, 20);
    expect(f.text).toBe("-5");
  });

  it("renders a signed negative number for the skill branch", () => {
    const f = floatingDamageFor("skill", 25, 0, 10, 20);
    expect(f.text).toBe("-25");
  });

  it("starts at the anchor row", () => {
    const f = floatingDamageFor("normal", 5, 0, 10, 20);
    expect(f.row).toBe(20);
  });

  it("rises as progress advances", () => {
    const start = floatingDamageFor("normal", 5, 0, 10, 20);
    const mid = floatingDamageFor("normal", 5, 0.5, 10, 20);
    const end = floatingDamageFor("normal", 5, 1, 10, 20);
    expect(mid.row).toBeLessThan(start.row);
    expect(end.row).toBeLessThan(mid.row);
  });

  it("never rises more than the declared rise distance", () => {
    const start = floatingDamageFor("skill", 25, 0, 10, 40);
    const end = floatingDamageFor("skill", 25, 1, 10, 40);
    expect(start.row - end.row).toBeLessThanOrEqual(4);
  });

  it("clamps the row to a non-negative value", () => {
    const f = floatingDamageFor("normal", 5, 1, 10, 0);
    expect(f.row).toBeGreaterThanOrEqual(0);
  });

  it("renders 0 damage as -0 rather than an empty string", () => {
    expect(floatingDamageFor("normal", 0, 0, 10, 20).text).toBe("-0");
  });

  it("handles a negative damage input by taking the absolute value", () => {
    expect(floatingDamageFor("normal", -7, 0, 10, 20).text).toBe("-7");
  });
});

describe("P3 floatingDamageFor — colour and size branching", () => {
  it("uses white for the normal branch (animations.md:38-39)", () => {
    expect(floatingDamageFor("normal", 5, 0, 10, 20).color).toBe(PALETTE.WHITE);
  });

  it("uses yellow for the skill branch (animations.md:60-61)", () => {
    expect(floatingDamageFor("skill", 25, 0, 10, 20).color).toBe(
      PALETTE.YELLOW,
    );
  });

  it("uses the CRIT colour for the critical branch", () => {
    expect(floatingDamageFor("critical", 50, 0, 10, 20).color).toBe(
      PALETTE.CRIT_COLOR,
    );
  });

  it("makes the skill branch larger than the normal branch", () => {
    expect(floatingDamageFor("skill", 25, 0, 10, 20).scale).toBeGreaterThan(
      floatingDamageFor("normal", 5, 0, 10, 20).scale,
    );
  });

  it("makes the critical branch at least as large as the skill branch", () => {
    expect(floatingDamageFor("critical", 50, 0, 10, 20).scale).toBeGreaterThanOrEqual(
      floatingDamageFor("skill", 25, 0, 10, 20).scale,
    );
  });

  it("uses a normal-branch scale of 1 (single cell height)", () => {
    expect(floatingDamageFor("normal", 5, 0, 10, 20).scale).toBe(1);
  });

  it("brackets the critical number with sparkles", () => {
    expect(floatingDamageFor("critical", 50, 0, 10, 20).text).toContain("-50");
  });
});

describe("P3 floatingDamageRows — the rise animation", () => {
  it("produces one entry per animation frame", () => {
    const rows = floatingDamageRows("normal", 5, 4, 10, 20);
    expect(rows).toHaveLength(4);
  });

  it("keeps the row strictly decreasing (a rising number)", () => {
    const rows = floatingDamageRows("normal", 5, 4, 10, 20);
    for (let i = 1; i < rows.length; i++) {
      expect(rows[i]!.row).toBeLessThan(rows[i - 1]!.row);
    }
  });

  it("keeps every row non-negative", () => {
    const rows = floatingDamageRows("skill", 25, 8, 10, 2);
    for (const r of rows) {
      expect(r.row).toBeGreaterThanOrEqual(0);
    }
  });
});

describe("P3 floatingDamageKindFor — VFX kind → branch", () => {
  it("maps critical_hit to the critical branch", () => {
    expect(floatingDamageKindFor("critical_hit")).toBe("critical");
  });

  it("maps the skill kinds to the skill branch", () => {
    for (const kind of [
      "heavy_attack",
      "pierce",
      "multi_hit",
      "dot",
      "counter",
      "lifesteal",
    ]) {
      expect(floatingDamageKindFor(kind)).toBe("skill");
    }
  });

  it("maps ice_hit and player_hit to the normal branch", () => {
    expect(floatingDamageKindFor("ice_hit")).toBe("normal");
    expect(floatingDamageKindFor("player_hit")).toBe("normal");
  });

  it("returns null for kinds that are not damage events", () => {
    expect(floatingDamageKindFor("victory")).toBeNull();
    expect(floatingDamageKindFor("heal")).toBeNull();
    expect(floatingDamageKindFor("shield")).toBeNull();
  });
});

describe("P3 renderFloatingDamage — grid overlay", () => {  it("writes the number into the grid at the computed position", () => {
    const grid = makeGrid(80, 50);
    const out = renderFloatingDamage(grid, "skill", 25, 0, 40, 30);
    const cell = out.get(40, 30);
    expect(cell?.char).toBe("-");
    expect(out.get(41, 30)?.char).toBe("2");
    expect(out.get(42, 30)?.char).toBe("5");
  });

  it("uses the branched colour for the written cells", () => {
    const grid = makeGrid(80, 50);
    const out = renderFloatingDamage(grid, "critical", 50, 0, 40, 30);
    expect(out.get(40, 30)?.fg).toBe(PALETTE.CRIT_COLOR);
  });

  it("renders nothing for zero damage", () => {
    const grid = makeGrid(80, 50);
    const out = renderFloatingDamage(grid, "normal", 0, 0, 40, 30);
    expect(out.get(40, 30)?.char).toBe(" ");
  });

  it("does not write outside the grid bounds", () => {
    const grid = makeGrid(80, 50);
    const out = renderFloatingDamage(grid, "skill", 25, 0, 79, 49);
    expect(out.get(79, 49)).not.toBeNull();
  });

  it("does not consume Math.random (RNG-neutral)", () => {
    const grid = makeGrid(80, 50);
    const original = Math.random;
    let calls = 0;
    Math.random = () => {
      calls += 1;
      return original();
    };
    try {
      renderFloatingDamage(grid, "skill", 25, 0, 40, 30);
    } finally {
      Math.random = original;
    }
    expect(calls).toBe(0);
  });
});
