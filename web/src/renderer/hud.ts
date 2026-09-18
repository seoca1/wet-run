/** HUD Renderer — minimal 1-line status bar for dungeon/matrix exploration.
 *
 * Displays only essential info: HP, Alarm, Credits, Combo, Boss Phase.
 * Designed to be rendered at the bottom of the screen (1 line height).
 */
import type { Grid, Cell } from "../core/types.ts";
import { makeGrid } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";
import type { GameState } from "../core/state.ts";

/** Render the minimal HUD bar at the bottom of the screen.
 *
 * Shows: HP, Alarm, Credits, Combo (if >1), Boss Phase (if active).
 * Designed for 1-line height at the bottom of the screen.
 */
export function renderHUD(
  state: GameState,
  cols: number,
): Grid {
  const parts: Array<{ text: string; color: string }> = [];

  // HP (always shown)
  parts.push({
    text: `HP: ${state.player.hp}/${state.player.maxHp}`,
    color: state.player.hp <= state.player.maxHp / 4 ? PALETTE.RED_BRIGHT : PALETTE.GREEN_NEON,
  });

  // Alarm (always shown)
  parts.push({
    text: `ALM: ${state.player.alarm}%`,
    color: state.player.alarm >= 75 ? PALETTE.RED_BRIGHT : state.player.alarm >= 50 ? PALETTE.YELLOW_AMBER : PALETTE.GREEN_NEON,
  });

  // Credits (always shown)
  parts.push({
    text: `CR: ${state.player.credits.toLocaleString()}`,
    color: PALETTE.CYAN_LIGHT,
  });

  // Combo (only if > 1)
  if (state.playerCombo > 1) {
    parts.push({
      text: `CB: x${state.playerCombo}`,
      color: PALETTE.YELLOW_AMBER,
    });
  }

  // Boss Phase (only if active)
  if (state.bossPhase > 0 && state.bossPhase <= 4) {
    const phaseLabels = ["", "STANDARD", "ALERT", "BERSERK", "TERMINAL"];
    parts.push({
      text: `★ BOSS PHASE ${state.bossPhase}/4 (${phaseLabels[state.bossPhase]})`,
      color: ["", "#ffffff", "#ffff00", "#ff8800", "#ff0000"][state.bossPhase] ?? PALETTE.WHITE,
    });
  }

  // Calculate positions first
  let x = 1;
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    const text = part.text;
    if (x + text.length >= cols - 1) break; // prevent overflow
    x += text.length + 3; // spacing between parts
  }

  // Create the final grid with all parts
  const grid = makeGrid(cols, 1);
  x = 1;
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    const text = part.text;
    if (x + text.length >= cols - 1) break;
    for (let j = 0; j < text.length; j++) {
      const idx = x + j;
      if (idx < cols - 1) {
        (grid[0] as Cell[])[idx] = { char: text[j], fg: part.color, bg: "transparent" };
      }
    }
    x += text.length + 3;
  }

  return grid;
}

/** Check if HUD should be rendered for the current screen state. */
export function shouldRenderHUD(screenKind: string, state: GameState | null): boolean {
  if (!state) return false;
  // Show HUD during dungeon/matrix exploration and overlay states
  const hudScreens = [
    "menu", // mission select shows HUD for context
    "mission_select",
    "briefing",
    "travel",
    "meet_npc",
    "extract_data",
    "matrix",
    "approach",
    "bypass_security",
    "black_market",
    "ghost_encounter",
    "death_restart",
  ];
  return hudScreens.includes(screenKind);
}