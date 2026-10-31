import { describe, expect, it } from "vitest";
import {
  composeCombatScreen,
  renderCombatScreen,
  renderRunScreen,
  runScreenLayout,
} from "../src/renderer/run_screen";
import { renderMatrix } from "../src/renderer/matrix";
import { renderEndingScreen, renderLootScreen } from "../src/renderer/ending";
import { renderGrid } from "../src/renderer/combat_grid";
import { groupStatusByTarget } from "../src/renderer/status_hud";
import { buildHudLines } from "../src/core/state/state";
import { triggerCombatVfx } from "../src/renderer/combat_vfx";
import { PALETTE } from "../src/renderer/palette";
import { rowText, runState } from "./view_fixtures";

describe("run screen composition", () => {
  it("preserves matrix frame, node HUD and active ICE inputs", () => {
    const state = runState({
      runPhase: "matrix",
      currentNodeIndex: 1,
      visitedNodes: [0, 1],
    });
    if (!state.matrix) throw new Error("fixture requires a matrix");
    const view = renderRunScreen(state, 80, 50);
    expect(runScreenLayout(80, 50)).toEqual({ cols: 80, rows: 50 });
    expect(view?.grid.cells).toEqual(
      renderMatrix(state.matrix, 1, [0, 1], 80, 50, state.iceRoster[0] ?? null)
        .cells,
    );
    expect(view?.hud).toEqual([
      "MATRIX",
      "",
      `Node 2/${state.matrix.nodes.length}`,
    ]);
  });

  it("does not draw a replacement when the matrix is absent", () => {
    const state = runState({ runPhase: "matrix", matrix: null });
    expect(renderRunScreen(state, 80, 50)).toBeNull();
  });

  it("preserves ending fallback and the literal question-mark HUD", () => {
    const state = runState({ runPhase: "ending", endingChoice: null });
    const view = renderRunScreen(state, 40, 30);
    expect(view?.grid.cells).toEqual(renderEndingScreen(null, 40, 30).cells);
    expect(view?.hud).toEqual(["ENDING", "", "Choice: ?"]);
  });

  it.each([
    ["Recovered +1,234 credits. Loot: shard x2", 1234, "Loot: shard x2"],
    ["No rewards", 0, ""],
  ] as const)("preserves parsed loot for %s", (message, credits, loot) => {
    const state = runState({ runPhase: "loot", message });
    const view = renderRunScreen(state, 80, 50);
    expect(view?.grid.cells).toEqual(
      renderLootScreen(
        state.player.hp,
        state.player.maxHp,
        80,
        50,
        credits,
        loot,
      ).cells,
    );
    expect(view?.hud).toEqual([
      "LOOT",
      "",
      "↑↓: navigate | ENTER: continue | ESC: back",
    ]);
  });

  it("leaves combat routing to the controller", () => {
    expect(renderRunScreen(runState(), 80, 50)).toBeNull();
  });

  it("preserves the full combat grid with HP deltas and grouped status effects", () => {
    const state = runState({
      statusEffects: [
        { kind: "burn", target: "player", remaining: 2, magnitude: 3 },
        {
          kind: "slow",
          target: "ice",
          iceIndex: 0,
          remaining: 3,
          magnitude: 1,
        },
        {
          kind: "silence",
          target: "ice",
          iceIndex: 1,
          remaining: 3,
          magnitude: 1,
        },
      ],
    });
    const grid = renderCombatScreen(
      { state, iceDelta: -7, playerDelta: -3 },
      80,
      50,
    );
    expect(grid.cells).toEqual(
      renderGrid(
        state,
        -7,
        -3,
        groupStatusByTarget(state.statusEffects, state.activeIceIndex),
        80,
        50,
      ).cells,
    );
    expect(grid.cells[1]?.[1]?.char).toBe("╔");
  });

  it("returns the untouched base grid and HUD when no VFX is active", () => {
    const state = runState();
    const view = composeCombatScreen(state, false);
    expect(view.grid).toBe(state.grid);
    expect(view.hud).toEqual(buildHudLines(state));
    expect(view.shake).toBeUndefined();
  });

  it("layers floating damage over VFX without changing the stored grid", () => {
    const state = runState({
      vfxInstances: [
        triggerCombatVfx("player_hit", "", 20, undefined, undefined, 17),
      ],
    });
    const baseCells = state.grid.cells;
    const view = composeCombatScreen(state, true);
    expect(rowText(view.grid, 5).slice(2, 5)).toBe("-17");
    expect(view.grid.cells[5]?.[2]?.fg).toBe(PALETTE.WHITE);
    expect(view.shake).toMatchObject({ x: 0, y: 0 });
    expect(state.grid.cells).toBe(baseCells);
    expect(rowText(state.grid, 5).trim()).toBe("");
  });
});
