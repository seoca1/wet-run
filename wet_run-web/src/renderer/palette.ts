/** Gibson palette — neon-on-black color scheme.
 *
 * ADR-0199 §4.3 design goal: preserve cyberpunk tone via specific hex
 * colors. These values match wet_run's tcod color palette (combat/palette.py)
 * for visual parity between desktop and browser MVP.
 */
export const PALETTE = Object.freeze({
  BACKGROUND: "#000000",
  FOREGROUND: "#d0d0d0",
  GRAY_DARK: "#606060",
  GRAY_MID: "#909090",
  GRAY_LIGHT: "#c0c0c0",
  CYAN_LIGHT: "#00ffff",
  CYAN_DIM: "#00a0a0",
  GREEN_NEON: "#00ff41",
  GREEN_DIM: "#008020",
  RED_DEEP: "#a00020",
  RED_BRIGHT: "#ff2030",
  YELLOW_AMBER: "#ffa500",
  MAGENTA_NEON: "#ff00ff",
  ICE_BLUE: "#4080ff",
  ALARM_RED: "#ff4040",
  PLAYER_CYAN: "#40ffff",
} as const);

/** Phase-specific foreground color for the ICE itself. */
export function iceColor(tier: number): string {
  if (tier <= 1) return PALETTE.ICE_BLUE;
  if (tier <= 3) return PALETTE.YELLOW_AMBER;
  if (tier <= 5) return PALETTE.RED_DEEP;
  return PALETTE.MAGENTA_NEON;
}

/** HP bar color threshold — green > yellow > red. */
export function hpColor(ratio: number): string {
  if (ratio > 0.6) return PALETTE.GREEN_NEON;
  if (ratio > 0.3) return PALETTE.YELLOW_AMBER;
  return PALETTE.RED_BRIGHT;
}
