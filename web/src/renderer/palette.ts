/** Gibson palette — neon-on-black color scheme.
 *
 * ADR-0199 §4.3 design goal: preserve cyberpunk tone via specific hex
 * colors. These values match wet_run's tcod color palette (combat/palette.py)
 * for visual parity between desktop and browser MVP.
 *
 * ADR-0210: extended with combat VFX palette tokens (HEAL_COLOR,
 * SHIELD_COLOR, BUFF_COLOR, DEBUFF_COLOR, CRIT_COLOR, etc.) referenced
 * by the canonical effect schema's `color_hint` field. Python has the
 * full set; web maps missing tokens to close semantic equivalents.
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
  HEAL_COLOR: "#80ff80",
  SHIELD_COLOR: "#a0e0ff",
  BUFF_COLOR: "#ffe080",
  DEBUFF_COLOR: "#e080ff",
  CRIT_COLOR: "#ffd700",
  DAMAGE_COLOR: "#ff8060",
  ICE_CYAN_DIM: "#00a0a0",
  ICE_FADE_PURPLE: "#a050c0",
  ICE_GREEN_BRIGHT: "#80ffa0",
  HIT_FLASH_COLOR: "#ffe0e0",
  ORANGE: "#ff8040",
  WARM: "#e0a060",
  OLIVE: "#a0a040",
  TIER_GOLD: "#ffd040",
} as const);

/** Resolve a Python palette key to the closest web palette token.
 *
 * Per ADR-0210: web maps `color_hint` strings from the schema to its
 * own PALETTE.* constants; falls back to FOREGROUND for missing keys.
 */
export function resolveColorHint(hint: string): string {
  if (hint in PALETTE) {
    return (PALETTE as Readonly<Record<string, string>>)[hint] ?? PALETTE.FOREGROUND;
  }
  return PALETTE.FOREGROUND;
}

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
