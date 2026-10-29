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
 *
 * P10 / ADR-0236: the palette is now *mode-aware*. `PALETTE` itself stays
 * the default ("none") palette — byte-identical to the pre-P10 values — and
 * `applyPaletteMode` re-points its properties at a variant. Every renderer
 * reads `PALETTE.X` at call time (never destructured at module scope), so
 * switching modes needs no call-site changes.
 */
import type { ColorblindMode } from "./accessibility_modes.ts";
import { getHighContrastColors } from "../core/accessibility.ts";

/** The palette token set — one entry per colour the renderer can emit. */
export type PaletteToken =
  | "BACKGROUND"
  | "FOREGROUND"
  | "GRAY_DARK"
  | "GRAY_MID"
  | "GRAY_LIGHT"
  | "GRAY"
  | "CYAN_LIGHT"
  | "CYAN_DIM"
  | "GREEN_NEON"
  | "GREEN_DIM"
  | "RED_DEEP"
  | "RED_BRIGHT"
  | "YELLOW_AMBER"
  | "YELLOW"
  | "MAGENTA_NEON"
  | "MAGENTA_LIGHT"
  | "BLUE_BRIGHT"
  | "ICE_BLUE"
  | "ALARM_RED"
  | "PLAYER_CYAN"
  | "HEAL_COLOR"
  | "SHIELD_COLOR"
  | "BUFF_COLOR"
  | "DEBUFF_COLOR"
  | "CRIT_COLOR"
  | "DAMAGE_COLOR"
  | "ICE_CYAN_DIM"
  | "ICE_FADE_PURPLE"
  | "ICE_GREEN_BRIGHT"
  | "HIT_FLASH_COLOR"
  | "ORANGE"
  | "WARM"
  | "OLIVE"
  | "TIER_GOLD"
  | "WHITE";

/** The canonical Gibson palette — the default ("none") mode. */
export const PALETTE: Record<PaletteToken, string> = {
  BACKGROUND: "#000000",
  FOREGROUND: "#d0d0d0",
  GRAY_DARK: "#606060",
  GRAY_MID: "#909090",
  GRAY_LIGHT: "#c0c0c0",
  GRAY: "#808080",
  CYAN_LIGHT: "#00ffff",
  CYAN_DIM: "#00a0a0",
  GREEN_NEON: "#00ff41",
  GREEN_DIM: "#008020",
  RED_DEEP: "#a00020",
  RED_BRIGHT: "#ff2030",
  YELLOW_AMBER: "#ffa500",
  YELLOW: "#ffff00",
  MAGENTA_NEON: "#ff00ff",
  MAGENTA_LIGHT: "#ff80ff",
  BLUE_BRIGHT: "#4080ff",
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
  WHITE: "#ffffff",
};

/** The immutable snapshot of the default ("none") palette. */
const DEFAULT_PALETTE: Readonly<Record<PaletteToken, string>> = Object.freeze({
  ...PALETTE,
});

/**
 * Per-mode colour overrides — pure data (ADR-0183 §"Colorblind palettes",
 * ADR-0196 §"Option A").
 *
 * The default mode has NO overrides: `paletteFor("none")` is byte-identical
 * to the pre-P10 palette, so the default rendering is unchanged.
 *
 * Each variant re-hues only the tokens whose *meaning* is carried by hue
 * (health, damage, ICE tier, alarm). The greys — foreground, background and
 * the gray ramp — are deliberately left alone: they carry no semantic hue,
 * so shifting them would only reduce contrast.
 */
export const PALETTE_VARIANTS: Readonly<
  Record<ColorblindMode, Readonly<Partial<Record<PaletteToken, string>>>>
> = Object.freeze({
  none: Object.freeze({}),
  // Deuteranopia — red/green confusion. Red reads dark; green reads yellow.
  deuteranopia: Object.freeze({
    GREEN_NEON: "#e8d44d",
    GREEN_DIM: "#8a7420",
    RED_BRIGHT: "#7a4fd0",
    RED_DEEP: "#3a2070",
    ALARM_RED: "#8a5ce0",
    DAMAGE_COLOR: "#9a6fe8",
    HIT_FLASH_COLOR: "#e0d8f4",
    ICE_GREEN_BRIGHT: "#d8cf78",
    HEAL_COLOR: "#cfd84d",
  }),
  // Protanopia — red weakness. Red darkens toward brown/black; green stays.
  protanopia: Object.freeze({
    RED_BRIGHT: "#a05a30",
    RED_DEEP: "#5a2c14",
    ALARM_RED: "#b06838",
    DAMAGE_COLOR: "#c08050",
    HIT_FLASH_COLOR: "#f0d8c0",
    CRIT_COLOR: "#ffe680",
  }),
  // Tritanopia — blue/yellow confusion. Blue reads teal; yellow reads pink.
  tritanopia: Object.freeze({
    BLUE_BRIGHT: "#00a0a0",
    ICE_BLUE: "#00a0a0",
    CYAN_LIGHT: "#00d0d0",
    CYAN_DIM: "#007878",
    ICE_CYAN_DIM: "#007878",
    PLAYER_CYAN: "#00c0c0",
    SHIELD_COLOR: "#ffb0c0",
    YELLOW_AMBER: "#ff90d0",
    YELLOW: "#ff80e0",
    BUFF_COLOR: "#ffa0e0",
    CRIT_COLOR: "#ff90ff",
    TIER_GOLD: "#ff9fe0",
  }),
});

/**
 * The high-contrast override — pure data.
 *
 * Sourced from `core/accessibility.ts`'s `getHighContrastColors()` (the
 * canonical high-contrast colour set, previously a consumer-0 helper) and
 * mapped onto the palette tokens that carry meaning. Applied *after* the
 * colorblind overrides, so a player who wants both gets both.
 */
const HIGH_CONTRAST_OVERRIDES: Readonly<Partial<Record<PaletteToken, string>>> =
  Object.freeze({
    FOREGROUND: getHighContrastColors().text,
    BACKGROUND: getHighContrastColors().background,
    GRAY_DARK: "#a0a0a0",
    GRAY: "#c0c0c0",
    GRAY_MID: "#d0d0d0",
    GRAY_LIGHT: "#e0e0e0",
    GREEN_NEON: getHighContrastColors().success,
    RED_BRIGHT: getHighContrastColors().error,
    ALARM_RED: getHighContrastColors().error,
    YELLOW_AMBER: getHighContrastColors().secondary,
    YELLOW: getHighContrastColors().secondary,
    CYAN_LIGHT: getHighContrastColors().primary,
    HEAL_COLOR: getHighContrastColors().success,
  });

/**
 * The palette for a colorblind mode — pure.
 *
 * Returns the default palette with the mode's overrides applied. The
 * returned object is a fresh frozen copy; the exported `PALETTE` is not
 * mutated by this call.
 */
export function paletteFor(
  mode: ColorblindMode,
  highContrast: boolean = false,
): Readonly<Record<PaletteToken, string>> {
  const overrides = PALETTE_VARIANTS[mode];
  return Object.freeze({
    ...DEFAULT_PALETTE,
    ...overrides,
    ...(highContrast ? HIGH_CONTRAST_OVERRIDES : {}),
  });
}

let currentPaletteMode: ColorblindMode = "none";
let currentHighContrast = false;

/** The colorblind palette mode currently applied to `PALETTE`. */
export function activePaletteMode(): ColorblindMode {
  return currentPaletteMode;
}

/** Whether the high-contrast overrides are currently applied to `PALETTE`. */
export function activeHighContrast(): boolean {
  return currentHighContrast;
}

/**
 * Apply a colorblind palette mode to the exported `PALETTE`.
 *
 * Every renderer reads `PALETTE.X` at call time, so re-pointing the
 * properties is enough to switch the whole game's colours — no renderer
 * call site changes. Passing `"none"` restores the byte-identical default.
 */
export function applyPaletteMode(
  mode: ColorblindMode,
  highContrast: boolean = false,
): void {
  const next = paletteFor(mode, highContrast);
  for (const key of Object.keys(DEFAULT_PALETTE) as PaletteToken[]) {
    PALETTE[key] = next[key];
  }
  currentPaletteMode = mode;
  currentHighContrast = highContrast;
}

/** Resolve a Python palette key to the closest web palette token.
 *
 * Per ADR-0210: web maps `color_hint` strings from the schema to its
 * own PALETTE.* constants; falls back to FOREGROUND for missing keys.
 */
export function resolveColorHint(hint: string): string {
  if (hint in PALETTE) {
    return (
      (PALETTE as Readonly<Record<string, string>>)[hint] ?? PALETTE.FOREGROUND
    );
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
