/** HUD visibility helper.
 *
 * The former `renderHUD()` 1-line status bar was removed (UI triage X3): it
 * had no caller. The live combat HUD is `buildHudLines` in
 * `core/state/state.ts`.
 */
import type { GameState } from "../core/state/state";

/** Check if HUD should be rendered for the current screen state. */
export function shouldRenderHUD(
  screenKind: string,
  state: GameState | null,
): boolean {
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
