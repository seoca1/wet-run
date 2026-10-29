/** Per-target status-effect HUD (proposal P14) + ADR-0226 effect visibility (P6).
 *
 * The status glyphs used to be a flat, target-less list: every effect on the
 * roster was merged into one bracket drawn next to the *active* ICE only.
 * That made "who is burning?" unanswerable and hid the ADR-0226 ICE effects
 * (shield / regen / powered) entirely — they had no glyph at all.
 *
 * These tests pin the two properties the proposal asks for:
 *   (a) glyphs are grouped per target (player vs. each roster slot), and
 *   (b) each glyph carries its remaining-turn count.
 */
import { describe, it, expect } from "vitest";
import {
  groupStatusByTarget,
  statusGroupForTarget,
  formatStatusEntries,
  formatTargetStatus,
  drawTargetStatus,
  statusGlyphFor,
} from "../src/renderer/status_hud.ts";
import { makeGrid, setText } from "../src/core/grid.ts";
import type { StatusEffectInstance } from "../src/core/types.ts";

function effect(
  overrides: Partial<StatusEffectInstance> = {},
): StatusEffectInstance {
  return {
    kind: "burn",
    remaining: 2,
    magnitude: 3,
    target: "player",
    ...overrides,
  };
}

describe("statusGlyphFor", () => {
  it("resolves the five Tier-4 glyphs", () => {
    expect(statusGlyphFor("burn")).toBe("B");
    expect(statusGlyphFor("stun")).toBe("S");
    expect(statusGlyphFor("slow")).toBe("L");
    expect(statusGlyphFor("silence")).toBe("M");
    expect(statusGlyphFor("vulnerable")).toBe("V");
  });

  it("resolves the three ADR-0226 ICE effect glyphs (P6)", () => {
    // ADR-0226's shield / regen / buff are the ICE-side effects. `buff` is
    // stored as the `powered` status kind.
    expect(statusGlyphFor("shield")).toBe("D");
    expect(statusGlyphFor("regen")).toBe("R");
    expect(statusGlyphFor("powered")).toBe("P");
  });

  it("returns undefined for an unmapped kind", () => {
    expect(statusGlyphFor("not_an_effect")).toBeUndefined();
  });

  it("never maps two kinds to the same letter", () => {
    const kinds = [
      "burn",
      "stun",
      "slow",
      "silence",
      "vulnerable",
      "shield",
      "regen",
      "powered",
    ];
    const glyphs = kinds.map((k) => statusGlyphFor(k));
    expect(new Set(glyphs).size).toBe(glyphs.length);
  });
});

describe("groupStatusByTarget", () => {
  it("returns no groups for an empty effect list", () => {
    expect(groupStatusByTarget([], 0)).toHaveLength(0);
  });

  it("separates player effects from ICE effects", () => {
    const groups = groupStatusByTarget(
      [
        effect({ kind: "burn", target: "player" }),
        effect({ kind: "shield", target: "ice", iceIndex: 0 }),
      ],
      0,
    );

    const player = statusGroupForTarget(groups, "player");
    const ice = statusGroupForTarget(groups, "ice", 0);

    expect(player?.entries.map((e) => e.kind)).toEqual(["burn"]);
    expect(ice?.entries.map((e) => e.kind)).toEqual(["shield"]);
  });

  it("keeps two roster slots apart", () => {
    const groups = groupStatusByTarget(
      [
        effect({ kind: "shield", target: "ice", iceIndex: 0 }),
        effect({ kind: "regen", target: "ice", iceIndex: 1 }),
      ],
      0,
    );

    expect(statusGroupForTarget(groups, "ice", 0)?.entries.map((e) => e.kind)).toEqual([
      "shield",
    ]);
    expect(statusGroupForTarget(groups, "ice", 1)?.entries.map((e) => e.kind)).toEqual([
      "regen",
    ]);
  });

  it("assigns an ice-targeted effect without iceIndex to the active ICE", () => {
    // Player-side burn / slow use `target: "ice"` with no roster slot — per
    // `types.ts` that means "the active ICE".
    const groups = groupStatusByTarget(
      [effect({ kind: "burn", target: "ice" })],
      2,
    );

    expect(statusGroupForTarget(groups, "ice", 2)?.entries).toHaveLength(1);
    expect(statusGroupForTarget(groups, "ice", 0)).toBeUndefined();
  });

  it("drops effects whose kind has no glyph", () => {
    const groups = groupStatusByTarget(
      [effect({ kind: "confused", target: "player" })],
      0,
    );
    expect(groups).toHaveLength(0);
  });

  it("preserves the effect order inside a group", () => {
    const groups = groupStatusByTarget(
      [
        effect({ kind: "burn", target: "player" }),
        effect({ kind: "stun", target: "player" }),
        effect({ kind: "slow", target: "player" }),
      ],
      0,
    );
    expect(
      statusGroupForTarget(groups, "player")?.entries.map((e) => e.kind),
    ).toEqual(["burn", "stun", "slow"]);
  });

  it("exposes the remaining-turn count on every entry", () => {
    const groups = groupStatusByTarget(
      [effect({ kind: "burn", target: "player", remaining: 4 })],
      0,
    );
    expect(statusGroupForTarget(groups, "player")?.entries[0]?.remaining).toBe(4);
  });
});

describe("formatStatusEntries", () => {
  it("returns an empty string for no entries", () => {
    expect(formatStatusEntries([])).toBe("");
  });

  it("appends the remaining-turn count to the glyph", () => {
    expect(
      formatStatusEntries([
        { kind: "burn", glyph: "B", remaining: 2 },
      ]),
    ).toBe("[B2]");
  });

  it("concatenates several glyphs inside one bracket", () => {
    expect(
      formatStatusEntries([
        { kind: "burn", glyph: "B", remaining: 2 },
        { kind: "stun", glyph: "S", remaining: 1 },
      ]),
    ).toBe("[B2S1]");
  });

  it("skips entries without a glyph", () => {
    expect(
      formatStatusEntries([{ kind: "burn", glyph: "", remaining: 2 }]),
    ).toBe("");
  });
});

describe("formatTargetStatus", () => {
  it("returns an empty string when the target has no group", () => {
    expect(formatTargetStatus(undefined)).toBe("");
  });

  it("renders the grouped glyphs with their turn counts", () => {
    const groups = groupStatusByTarget(
      [
        effect({ kind: "shield", target: "ice", iceIndex: 0, remaining: 3 }),
        effect({ kind: "powered", target: "ice", iceIndex: 0, remaining: 2 }),
      ],
      0,
    );
    expect(formatTargetStatus(statusGroupForTarget(groups, "ice", 0))).toBe("[D3P2]");
  });
});

describe("drawTargetStatus", () => {
  it("writes the glyphs into the grid at the requested position", () => {
    const grid = makeGrid(40, 10);
    const groups = groupStatusByTarget(
      [effect({ kind: "burn", target: "player", remaining: 2 })],
      0,
    );

    const drawn = drawTargetStatus(
      grid,
      5,
      3,
      statusGroupForTarget(groups, "player"),
      "#ffffff",
    );

    let line = "";
    for (let x = 0; x < drawn.width; x++) {
      line += drawn.cells[3]?.[x]?.char ?? " ";
    }
    expect(line.trim()).toBe("[B2]");
    expect(line.slice(0, 5).trim()).toBe("");
  });

  it("returns the grid untouched when there is nothing to draw", () => {
    const grid = makeGrid(20, 5);
    const drawn = drawTargetStatus(grid, 2, 1, undefined, "#ffffff");
    expect(drawn).toBe(grid);
  });

  it("keeps the player glyphs and the ICE glyphs on different cells (P14)", () => {
    // The whole point of P14: the player's burn and the ICE's shield used to
    // be merged into one bracket next to the active ICE.
    let grid = makeGrid(60, 12);
    grid = setText(grid, 2, 5, "P [##########] 30/30", "#ffffff");
    grid = setText(grid, 20, 8, "> [1] Caster", "#ffffff");

    const groups = groupStatusByTarget(
      [
        effect({ kind: "burn", target: "player", remaining: 2 }),
        effect({ kind: "shield", target: "ice", iceIndex: 0, remaining: 3 }),
      ],
      0,
    );

    const withPlayer = drawTargetStatus(
      grid,
      25,
      5,
      statusGroupForTarget(groups, "player"),
      "#ffffff",
    );
    const withBoth = drawTargetStatus(
      withPlayer,
      32,
      8,
      statusGroupForTarget(groups, "ice", 0),
      "#ffffff",
    );

    const rowText = (row: number): string => {
      let out = "";
      for (let x = 0; x < withBoth.width; x++) {
        out += withBoth.cells[row]?.[x]?.char ?? " ";
      }
      return out;
    };

    expect(rowText(5)).toContain("[B2]");
    expect(rowText(8)).toContain("[D3]");
    // The player row must NOT carry the ICE's shield glyph.
    expect(rowText(5)).not.toContain("D3");
    // The ICE row must NOT carry the player's burn glyph.
    expect(rowText(8)).not.toContain("B2");
  });

  it("clips at the right edge instead of wrapping", () => {
    const grid = makeGrid(10, 3);
    const groups = groupStatusByTarget(
      [effect({ kind: "burn", target: "player", remaining: 2 })],
      0,
    );
    const drawn = drawTargetStatus(
      grid,
      8,
      1,
      statusGroupForTarget(groups, "player"),
      "#ffffff",
    );
    let line = "";
    for (let x = 0; x < drawn.width; x++) {
      line += drawn.cells[1]?.[x]?.char ?? " ";
    }
    expect(line).toBe("        [B");
  });
});
