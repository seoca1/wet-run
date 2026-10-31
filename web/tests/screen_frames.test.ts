/** Green Grid frames on the main menu, mission select and combat screens
 * (ADR-0237 §2, triage V2). All three use `renderer/panel.ts` and inset the
 * frame one cell from the grid edge (`screenFrameRect`).
 */
import { describe, expect, it } from "vitest";
import type { Grid } from "../src/core/types";
import { makeGrid } from "../src/core/grid";
import { mainMenuLayout, renderMainMenu } from "../src/renderer/menu_main";
import {
  missionListLayout,
  renderMissionList,
} from "../src/renderer/mission_select";
import { combatHeaderRuleRow, renderGrid } from "../src/renderer/combat_grid";
import { makeInitialState } from "../src/core/state/state";
import { PALETTE } from "../src/renderer/palette";
import type { GameState, Ice, Mission, Program } from "../src/core/types";

const FRAME_GLYPHS = new Set(["╔", "╗", "╚", "╝", "═", "║", "╠", "╣"]);

function charAt(grid: Grid, x: number, y: number): string {
  return grid.cells[y]?.[x]?.char ?? "";
}

function rowText(grid: Grid, y: number): string {
  return (grid.cells[y] ?? []).map((c) => c.char).join("");
}

/** Assert the inset frame: corners one cell in from each grid edge, unbroken
 * rails between them, and a blank one-cell gutter outside them. */
function expectInsetFrame(grid: Grid): void {
  const left = 1;
  const top = 1;
  const right = grid.width - 2;
  const bottom = grid.height - 2;
  expect(charAt(grid, left, top)).toBe("╔");
  expect(charAt(grid, right, top)).toBe("╗");
  expect(charAt(grid, left, bottom)).toBe("╚");
  expect(charAt(grid, right, bottom)).toBe("╝");
  for (let x = left; x <= right; x++) {
    expect(FRAME_GLYPHS.has(charAt(grid, x, top)), `top x=${x}`).toBe(true);
    expect(FRAME_GLYPHS.has(charAt(grid, x, bottom)), `bottom x=${x}`).toBe(
      true,
    );
  }
  for (let y = top; y <= bottom; y++) {
    expect(FRAME_GLYPHS.has(charAt(grid, left, y)), `left y=${y}`).toBe(true);
    expect(FRAME_GLYPHS.has(charAt(grid, right, y)), `right y=${y}`).toBe(true);
    expect(grid.cells[y]?.[right]?.fg).toBe(PALETTE.GREEN_NEON);
  }
  expectBlankGutter(grid);
}

/** Assert the outermost row/column on every side holds only blank cells. */
function expectBlankGutter(grid: Grid): void {
  const lastX = grid.width - 1;
  const lastY = grid.height - 1;
  for (let x = 0; x <= lastX; x++) {
    expect(charAt(grid, x, 0), `gutter top x=${x}`).toBe(" ");
    expect(charAt(grid, x, lastY), `gutter bottom x=${x}`).toBe(" ");
  }
  for (let y = 0; y <= lastY; y++) {
    expect(charAt(grid, 0, y), `gutter left y=${y}`).toBe(" ");
    expect(charAt(grid, lastX, y), `gutter right y=${y}`).toBe(" ");
  }
}

describe("main menu frame", () => {
  it("draws a GREEN_NEON double-line frame around an 80x50 menu", () => {
    const grid = renderMainMenu(0, 80, 50);
    expectInsetFrame(grid);
    expect(charAt(grid, 40, 1)).toBe("═");
    expect(charAt(grid, 1, 25)).toBe("║");
    expect(charAt(grid, 78, 25)).toBe("║");
    expect(mainMenuLayout(grid).frame).toEqual({
      x: 1,
      y: 1,
      width: 78,
      height: 48,
    });
  });

  it("keeps the frame intact with a save hint and an overlong status line", () => {
    const grid = renderMainMenu(
      4,
      80,
      50,
      true,
      { missionId: "aleph_fragment", turnCount: 3 },
      "x".repeat(200),
    );
    expectInsetFrame(grid);
  });

  it("pins the footer to the last two inner rows", () => {
    const grid = renderMainMenu(0, 80, 50);
    const { footerY } = mainMenuLayout(grid);
    expect(footerY).toBe(46);
    expect(rowText(grid, 46)).toContain(
      "↑↓: navigate | ENTER: select | ESC: back",
    );
    expect(rowText(grid, 47)).toContain("Tier 4 · v0.1.0 · ADR-0209 IDB");
  });

  it("centres the title-to-status block instead of clustering it at the top", () => {
    const layout = mainMenuLayout(makeGrid(80, 50));
    const gapAbove = layout.titleY - layout.inner.y;
    const statusRow = layout.optionsY + 14 + 2;
    const gapBelow = layout.footerY - 1 - statusRow;
    expect(layout.optionsY).toBeGreaterThan(8);
    expect(Math.abs(gapAbove - gapBelow)).toBeLessThanOrEqual(1);
  });

  it("centres the option column on the widest gated row", () => {
    const grid = renderMainMenu(0, 80, 50, false, null, "", false);
    const { optionsX, optionsY } = mainMenuLayout(grid);
    const widest = "▸ [5] CONTINUE    (no save)".length;
    expect(optionsX).toBe(2 + Math.floor((76 - widest) / 2));
    expect(rowText(grid, optionsY).slice(optionsX)).toMatch(/^▸ \[1\] NEW RUN/);
  });

  it("falls back to the original inner offsets on a short grid without losing the frame", () => {
    const grid = renderMainMenu(0, 30, 24);
    const layout = mainMenuLayout(grid);
    expect(layout.titleY).toBe(layout.inner.y + 1);
    expect(layout.titleY).toBe(3);
    expect(layout.optionsY).toBe(9);
    expect(layout.optionsX).toBe(layout.inner.x + 3);
    expect(layout.optionsX).toBe(5);
    expectInsetFrame(grid);
  });
});

describe("mission select frame", () => {
  const labels = Array.from(
    { length: 5 },
    (_, i) => `[${i + 1}] Mission ${i + 1}`,
  );

  it("frames the screen and rules off the header with ╠═╣", () => {
    const grid = renderMissionList(labels, 0, 80, 50);
    expectInsetFrame(grid);
    expect(charAt(grid, 1, 5)).toBe("╠");
    expect(charAt(grid, 78, 5)).toBe("╣");
    expect(charAt(grid, 40, 5)).toBe("═");
    expect(charAt(grid, 0, 5)).toBe(" ");
    expect(charAt(grid, 79, 5)).toBe(" ");
  });

  it("keeps the header at its offsets inside the inset frame", () => {
    const grid = renderMissionList(labels, 0, 80, 50);
    expect(rowText(grid, 2).slice(3)).toMatch(/^WET RUN — Select Mission/);
    expect(rowText(grid, 4).slice(3)).toMatch(
      /^↑↓: navigate \| ENTER: launch \| ESC: back/,
    );
  });

  it("centres a short list in the body below the rule", () => {
    const grid = renderMissionList(labels, 1, 80, 50);
    const layout = missionListLayout(grid, labels);
    expect(layout.listY).toBe(7 + Math.floor((41 - 5) / 2));
    expect(rowText(grid, layout.listY + 1).slice(layout.listX)).toMatch(
      /^▸ \[2\] Mission 2/,
    );
  });

  it("starts a list that fills the body two rows below the rule and clips it at the rail", () => {
    const many = Array.from({ length: 60 }, (_, i) => `[${i + 1}] M${i + 1}`);
    const grid = renderMissionList(many, 0, 80, 50);
    const layout = missionListLayout(grid, many);
    expect(layout.listY).toBe(7);
    expect(layout.listBottom).toBe(47);
    expect(rowText(grid, 47)).toContain("[41] M41");
    expect(rowText(grid, 48)).not.toContain("M42");
    expectInsetFrame(grid);
  });

  it("clips an overlong row at the right rail instead of the gutter", () => {
    const grid = renderMissionList(["z".repeat(200)], 0, 80, 50);
    const { listX, listY } = missionListLayout(grid, ["z".repeat(200)]);
    expect(charAt(grid, 77, listY)).toBe("z");
    expect(charAt(grid, 78, listY)).toBe("║");
    expect(listX).toBe(5);
    expectInsetFrame(grid);
  });
});

describe("combat frame", () => {
  const mission: Mission = {
    id: "test",
    title: "Test",
    fixer: "test",
    arc: 1,
    zone: "test",
    grade_min: 1,
    grade_max: 1,
    rewards: { credits: 10, materials: {} },
  };
  const program: Program = {
    id: "p1",
    name: "Atk",
    tier: 1,
    cost: 0,
    effect: "damage",
    description: "test",
    aoe: false,
  };
  const ice: Ice = {
    id: "caster",
    name: "Caster",
    tier: 2,
    hp: 50,
    maxHp: 50,
    armor: 0,
    personality: "aggressive",
    aggression: "standard",
  };

  function combatState(overrides: Partial<GameState> = {}): GameState {
    return {
      ...makeInitialState(mission, ice, [program]),
      iceRoster: [ice],
      activeIceIndex: 0,
      phase: "combat",
      runPhase: "combat",
      ...overrides,
    };
  }

  it("frames the combat grid; the right rail divides it from the HUD column", () => {
    const grid = renderGrid(combatState(), null, null, [], 80, 50);
    expectInsetFrame(grid);
    for (let y = 2; y < 48; y++) {
      expect(FRAME_GLYPHS.has(charAt(grid, 78, y))).toBe(true);
    }
  });

  it("rules off the header (mission, message, player HP) from the ICE field", () => {
    const grid = renderGrid(combatState(), null, null, [], 80, 50);
    expect(combatHeaderRuleRow(50)).toBe(8);
    expect(charAt(grid, 1, 8)).toBe("╠");
    expect(charAt(grid, 78, 8)).toBe("╣");
    expect(rowText(grid, 2).slice(3)).toMatch(/^Mission: Test/);
    expect(rowText(grid, 6).slice(3)).toMatch(/^P /);
  });

  it("omits the header rule when the grid is too short for it", () => {
    expect(combatHeaderRuleRow(12)).toBeNull();
    const grid = renderGrid(combatState(), null, null, [], 40, 12);
    expect(charAt(grid, 1, 8)).toBe("║");
    expectInsetFrame(grid);
  });

  it("never lets an overlong message erase the right rail", () => {
    const grid = renderGrid(
      combatState({ message: "y".repeat(200) }),
      null,
      null,
      [],
      80,
      50,
    );
    expect(charAt(grid, 78, 4)).toBe("║");
    expect(rowText(grid, 4).slice(3, 78)).toBe("y".repeat(75));
    expectInsetFrame(grid);
  });

  it("keeps victory art off the bottom rail", () => {
    const grid = renderGrid(
      combatState({ phase: "victory" }),
      null,
      null,
      [],
      80,
      30,
    );
    expectInsetFrame(grid);
  });
});
