import type { GameState } from "../core/types";
import { renderMatrix } from "./matrix";
import { renderEndingScreen, renderLootScreen } from "./ending";
import type { ScreenView } from "./screen_view";
import { renderGrid } from "./combat_grid";
import { groupStatusByTarget } from "./status_hud";
import { buildHudLines } from "../core/state/state";
import { composeCombatVfx } from "./combat_vfx";
import { composeFloatingDamage, overlayShake } from "./combat_overlay";
import type { ShakeState } from "./screen_shake";
import { renderEncounterDecision } from "./encounter";

/** The same full-grid dimensions used by matrix, loot, ending and combat views. */
export function runScreenLayout(cols: number, rows: number) {
  return { cols, rows } as const;
}

/** Compose non-combat run phases, retaining message-derived loot and HUD text. */
export function renderRunScreen(
  state: GameState,
  cols: number,
  rows: number,
): ScreenView | null {
  const layout = runScreenLayout(cols, rows);
  switch (state.runPhase) {
    case "matrix": {
      if (state.encounterDecision)
        return renderEncounterDecision(state, cols, rows);
      const matrix = state.matrix;
      if (!matrix) return null;
      return {
        grid: renderMatrix(
          matrix,
          state.currentNodeIndex,
          state.visitedNodes,
          layout.cols,
          layout.rows,
          state.clearedEncounterNodes?.includes(state.currentNodeIndex)
            ? (state.iceRoster[state.activeIceIndex] ?? null)
            : null,
          state.selectedMatrixNodeIndex ?? null,
        ),
        hud: [
          "MATRIX",
          "",
          `Node ${state.currentNodeIndex + 1}/${matrix.nodes.length}`,
        ],
      };
    }
    case "ending":
      return {
        grid: renderEndingScreen(state.endingChoice, layout.cols, layout.rows),
        hud: ["ENDING", "", `Choice: ${state.endingChoice ?? "?"}`],
      };
    case "loot": {
      const creditsMatch = state.message.match(/\+(\d[\d,]*)\s+credits/);
      const lootMatch = state.message.match(/Loot:\s*(.+)$/);
      const rewardCredits = creditsMatch
        ? parseInt((creditsMatch[1] ?? "").replace(/,/g, ""), 10)
        : 0;
      const lootText = lootMatch ? `Loot: ${lootMatch[1]}` : "";
      return {
        grid: renderLootScreen(
          state.player.hp,
          state.player.maxHp,
          layout.cols,
          layout.rows,
          rewardCredits,
          lootText,
        ),
        hud: ["LOOT", "", "↑↓: navigate | ENTER: continue | ESC: back"],
      };
    }
    default:
      return null;
  }
}

/** Build combat's base grid from HP deltas and target-specific status effects. */
export function renderCombatScreen(
  view: {
    readonly state: GameState;
    readonly iceDelta: number | null;
    readonly playerDelta: number | null;
  },
  cols: number,
  rows: number,
) {
  const statusGroups = groupStatusByTarget(
    view.state.statusEffects,
    view.state.activeIceIndex,
  );
  const layout = runScreenLayout(cols, rows);
  return renderGrid(
    view.state,
    view.iceDelta,
    view.playerDelta,
    statusGroups,
    layout.cols,
    layout.rows,
  );
}

/** Layer VFX, then damage numbers, leaving the stored base grid unchanged. */
export function composeCombatScreen(
  state: GameState,
  reducedMotion: boolean,
): ScreenView & { readonly shake?: ShakeState } {
  const hud = buildHudLines(state);
  if (state.vfxInstances.length === 0) return { grid: state.grid, hud };
  const layout = runScreenLayout(state.grid.width, state.grid.height);
  const composed = composeCombatVfx(
    state.grid,
    state.vfxInstances,
    layout.cols,
    layout.rows,
  );
  return {
    grid: composeFloatingDamage(
      composed,
      state.vfxInstances,
      layout.cols,
      layout.rows,
    ),
    hud,
    shake: overlayShake(state.vfxInstances, reducedMotion),
  };
}
