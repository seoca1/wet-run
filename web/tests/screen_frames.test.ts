/** Green Grid frames on the main menu, mission select and combat screens
 * (ADR-0237 §2, triage V2). All three use `renderer/panel.ts`.
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

/** Assert the full-grid frame: corners, rails, and nothing but frame glyphs on the edge. */
function expectFullFrame(grid: Grid): void {
  const right = grid.width - 1;
  const bottom = grid.height - 1;
  expect(charAt(grid, 0, 0)).toBe("╔");
  expect(charAt(grid, right, 0)).toBe("╗");
  expect(charAt(grid, 0, bottom)).toBe("╚");
  expect(charAt(grid, right, bottom)).toBe("╝");
  for (let x = 0; x <= right; x++) {
    expect(FRAME_GLYPHS.has(charAt(grid, x, 0)), `top x=${x}`).toBe(true);
    expect(FRAME_GLYPHS.has(charAt(grid, x, bottom)), `bottom x=${x}`).toBe(
      true,
    );
  }
  for (let y = 0; y <= bottom; y++) {
    expect(FRAME_GLYPHS.has(charAt(grid, 0, y)), `left y=${y}`).toBe(true);
    expect(FRAME_GLYPHS.has(charAt(grid, right, y)), `right y=${y}`).toBe(true);
    expect(grid.cells[y]?.[right]?.fg).toBe(PALETTE.GREEN_NEON);
  }
}

describe("main menu frame", () => {
  it("draws a GREEN_NEON double-line frame around an 80x50 menu", () => {
    const grid = renderMainMenu(0, 80, 50);
    expectFullFrame(grid);
    expect(charAt(grid, 40, 0)).toBe("═");
    expect(charAt(grid, 0, 25)).toBe("║");
    expect(charAt(grid, 79, 25)).toBe("║");
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
    expectFullFrame(grid);
  });

  it("pins the footer to the last two inner rows", () => {
    const grid = renderMainMenu(0, 80, 50);
    const { footerY } = mainMenuLayout(grid);
    expect(footerY).toBe(47);
    expect(rowText(grid, 47)).toContain(
      "↑↓: navigate | ENTER: select | ESC: back",
    );
    expect(rowText(grid, 48)).toContain("Tier 4 · v0.1.0 · ADR-0209 IDB");
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
    expect(optionsX).toBe(1 + Math.floor((78 - widest) / 2));
    expect(rowText(grid, optionsY).slice(optionsX)).toMatch(/^▸ \[1\] NEW RUN/);
  });

  it("falls back to the original offsets on a short grid without losing the frame", () => {
    const grid = renderMainMenu(0, 30, 24);
    const layout = mainMenuLayout(grid);
    expect(layout.titleY).toBe(2);
    expect(layout.optionsY).toBe(8);
    expect(layout.optionsX).toBe(4);
    expectFullFrame(grid);
  });
});

describe("mission select frame", () => {
  const labels = Array.from(
    { length: 5 },
    (_, i) => `[${i + 1}] Mission ${i + 1}`,
  );

  it("frames the screen and rules off the header with ╠═╣", () => {
    const grid = renderMissionList(labels, 0, 80, 50);
    expectFullFrame(grid);
    expect(charAt(grid, 0, 4)).toBe("╠");
    expect(charAt(grid, 79, 4)).toBe("╣");
    expect(charAt(grid, 40, 4)).toBe("═");
  });

  it("keeps the header text and cells unchanged", () => {
    const grid = renderMissionList(labels, 0, 80, 50);
    expect(rowText(grid, 1).slice(2)).toMatch(/^WET RUN — Select Mission/);
    expect(rowText(grid, 3).slice(2)).toMatch(
      /^↑↓: navigate \| ENTER: launch \| ESC: back/,
    );
  });

  it("centres a short list in the body below the rule", () => {
    const grid = renderMissionList(labels, 1, 80, 50);
    const layout = missionListLayout(grid, labels);
    expect(layout.listY).toBe(6 + Math.floor((43 - 5) / 2));
    expect(rowText(grid, layout.listY + 1).slice(layout.listX)).toMatch(
      /^▸ \[2\] Mission 2/,
    );
  });

  it("starts a list that fills the body at the original row 6 and clips it at the rail", () => {
    const many = Array.from({ length: 60 }, (_, i) => `[${i + 1}] M${i + 1}`);
    const grid = renderMissionList(many, 0, 80, 50);
    const layout = missionListLayout(grid, many);
    expect(layout.listY).toBe(6);
    expect(layout.listBottom).toBe(48);
    expect(rowText(grid, 48)).toContain("[43] M43");
    expectFullFrame(grid);
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
    expectFullFrame(grid);
    for (let y = 1; y < 49; y++) {
      expect(FRAME_GLYPHS.has(charAt(grid, 79, y))).toBe(true);
    }
  });

  it("rules off the header (mission, message, player HP) from the ICE field", () => {
    const grid = renderGrid(combatState(), null, null, [], 80, 50);
    expect(combatHeaderRuleRow(50)).toBe(7);
    expect(charAt(grid, 0, 7)).toBe("╠");
    expect(charAt(grid, 79, 7)).toBe("╣");
    expect(rowText(grid, 1).slice(2)).toMatch(/^Mission: Test/);
    expect(rowText(grid, 5).slice(2)).toMatch(/^P /);
  });

  it("omits the header rule when the grid is too short for it", () => {
    expect(combatHeaderRuleRow(12)).toBeNull();
    const grid = renderGrid(combatState(), null, null, [], 40, 12);
    expect(charAt(grid, 0, 7)).toBe("║");
    expectFullFrame(grid);
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
    expect(charAt(grid, 79, 3)).toBe("║");
    expectFullFrame(grid);
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
    expectFullFrame(grid);
  });
});
