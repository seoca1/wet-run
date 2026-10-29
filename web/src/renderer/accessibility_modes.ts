/** P10 — accessibility modes: reduced-motion gate, colorblind palette mode,
 * text scale.
 *
 * This module owns the *pure* accessibility logic so it can be tested without
 * a DOM-heavy runtime. `main.ts` wires it to the settings screen; the
 * renderers consume the resulting values.
 *
 * Provenance:
 *
 * - **ADR-0183** (Accessibility — Colorblind 3 Modes, Text Size, Input
 *   Remapping) defines the vocabulary: `colorblind_mode` is a *string* with
 *   the 4 values `"none"`, `"deuteranopia"`, `"protanopia"`, `"tritanopia"`,
 *   and `text_size` is `"small"` / `"medium"` / `"large"`.
 * - **ADR-0196** (Accessibility Colorblind State Alignment) inherits that
 *   4-mode vocabulary and fixes the *cycle order*
 *   (`none → deuteranopia → protanopia → tritanopia → none`). ADR-0196's
 *   implementation status is still "pending execution" — the web build had
 *   no implementation at all. This module is that implementation for the web
 *   tier.
 *
 * Nothing here reads or writes game state — no RNG, no clock, no reducer
 * coupling — so enabling an accessibility mode cannot perturb the balance
 * harness (ADR-0229 §A1).
 */
import { prefersHighContrast, prefersReducedMotion } from "../core/accessibility.ts";

/** The 4 colorblind palette modes (ADR-0196 §"Option A"). */
export type ColorblindMode =
  | "none"
  | "deuteranopia"
  | "protanopia"
  | "tritanopia";

/** Cycle order — ADR-0196 §"Option A": none → deuter → protan → tri → none. */
export const COLORBLIND_MODES: ReadonlyArray<ColorblindMode> = Object.freeze([
  "none",
  "deuteranopia",
  "protanopia",
  "tritanopia",
] as const);

/** The 3 text-scale steps (ADR-0183 `text_size`). */
export type TextScaleStep = "small" | "medium" | "large";

/** Text-scale steps in ascending order. */
export const TEXT_SCALE_STEPS: ReadonlyArray<TextScaleStep> = Object.freeze([
  "small",
  "medium",
  "large",
] as const);

/**
 * Cell/font multiplier per text-scale step.
 *
 * `medium` is exactly **1.0** — the default rendering is unchanged
 * (ADR-0110 discipline: the default path must be byte-identical).
 */
export const TEXT_SCALE_FACTORS: Readonly<Record<TextScaleStep, number>> =
  Object.freeze({
    small: 0.85,
    medium: 1.0,
    large: 1.25,
  });

/** localStorage key for the persisted colorblind palette mode. */
export const COLORBLIND_STORAGE_KEY = "wetrun_colorblind_mode";

/** localStorage key for the persisted text-scale step. */
export const TEXT_SCALE_STORAGE_KEY = "wetrun_text_scale";

/** localStorage key for the persisted reduced-motion override. */
export const REDUCED_MOTION_STORAGE_KEY = "wetrun_reduced_motion";

/** localStorage key for the persisted high-contrast override. */
export const HIGH_CONTRAST_STORAGE_KEY = "wetrun_high_contrast";

/** The kinds of motion the reduced-motion gate can suppress. */
export type MotionKind = "shake" | "hit_stop" | "flash" | "floating_damage";

/** Narrow a string to a `ColorblindMode`. */
export function isColorblindMode(value: string): value is ColorblindMode {
  return (COLORBLIND_MODES as ReadonlyArray<string>).includes(value);
}

/** Narrow a string to a `TextScaleStep`. */
export function isTextScaleStep(value: string): value is TextScaleStep {
  return (TEXT_SCALE_STEPS as ReadonlyArray<string>).includes(value);
}

/** The next colorblind mode in the ADR-0196 cycle. */
export function nextColorblindMode(current: ColorblindMode): ColorblindMode {
  const idx = COLORBLIND_MODES.indexOf(current);
  const next = COLORBLIND_MODES[(idx + 1) % COLORBLIND_MODES.length];
  return next ?? "none";
}

/** The next text-scale step in the ascending cycle. */
export function nextTextScale(current: TextScaleStep): TextScaleStep {
  const idx = TEXT_SCALE_STEPS.indexOf(current);
  const next = TEXT_SCALE_STEPS[(idx + 1) % TEXT_SCALE_STEPS.length];
  return next ?? "medium";
}

/** The previous text-scale step in the ascending cycle (wraps around). */
export function previousTextScale(current: TextScaleStep): TextScaleStep {
  const idx = TEXT_SCALE_STEPS.indexOf(current);
  const prev =
    TEXT_SCALE_STEPS[(idx - 1 + TEXT_SCALE_STEPS.length) % TEXT_SCALE_STEPS.length];
  return prev ?? "medium";
}

/** The cell/font multiplier for a text-scale step. */
export function textScaleFactor(step: TextScaleStep): number {
  return TEXT_SCALE_FACTORS[step];
}

/**
 * The reduced-motion gate.
 *
 * Pure and explicit: when `reducedMotion` is on, the named motion is
 * suppressed. When it is off, nothing changes — the default path is
 * byte-identical to the pre-P10 behaviour.
 */
export function suppressMotion(
  kind: MotionKind,
  reducedMotion: boolean,
): boolean {
  if (!reducedMotion) return false;
  return kind === "shake" || kind === "hit_stop" || kind === "flash" || kind === "floating_damage";
}

/**
 * Resolve the effective reduced-motion state.
 *
 * An explicit in-game override wins over the OS media query in BOTH
 * directions — a player who turned it off must not be forced into
 * reduced-motion just because their OS says so.
 */
export function resolveReducedMotion(override: boolean | null): boolean {
  if (override !== null) return override;
  return prefersReducedMotion();
}

/**
 * Resolve the effective high-contrast state.
 *
 * Mirrors `resolveReducedMotion`: the explicit in-game override wins over
 * the OS `prefers-contrast` media query in both directions.
 */
export function resolveHighContrast(override: boolean | null): boolean {
  if (override !== null) return override;
  return prefersHighContrast();
}

/** Read the persisted colorblind palette mode. Defaults to `"none"`. */
export function loadColorblindMode(): ColorblindMode {
  if (typeof localStorage === "undefined") return "none";
  const raw = localStorage.getItem(COLORBLIND_STORAGE_KEY);
  if (raw !== null && isColorblindMode(raw)) return raw;
  return "none";
}

/** Persist the colorblind palette mode. No-op without localStorage. */
export function persistColorblindMode(mode: ColorblindMode): void {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(COLORBLIND_STORAGE_KEY, mode);
}

/** Read the persisted text-scale step. Defaults to `"medium"` (1.0). */
export function loadTextScale(): TextScaleStep {
  if (typeof localStorage === "undefined") return "medium";
  const raw = localStorage.getItem(TEXT_SCALE_STORAGE_KEY);
  if (raw !== null && isTextScaleStep(raw)) return raw;
  return "medium";
}

/** Persist the text-scale step. No-op without localStorage. */
export function persistTextScale(step: TextScaleStep): void {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(TEXT_SCALE_STORAGE_KEY, step);
}

/**
 * Read the persisted reduced-motion override.
 *
 * `null` means "no explicit choice" — the OS media query decides.
 */
export function loadReducedMotionOverride(): boolean | null {
  if (typeof localStorage === "undefined") return null;
  const raw = localStorage.getItem(REDUCED_MOTION_STORAGE_KEY);
  if (raw === "1") return true;
  if (raw === "0") return false;
  return null;
}

/**
 * Persist the reduced-motion override.
 *
 * `null` clears the override (back to following the OS media query).
 */
export function persistReducedMotionOverride(value: boolean | null): void {
  if (typeof localStorage === "undefined") return;
  if (value === null) {
    localStorage.removeItem(REDUCED_MOTION_STORAGE_KEY);
    return;
  }
  localStorage.setItem(REDUCED_MOTION_STORAGE_KEY, value ? "1" : "0");
}

/**
 * Read the persisted high-contrast override.
 *
 * `null` means "no explicit choice" — the OS `prefers-contrast` media query
 * decides.
 */
export function loadHighContrastOverride(): boolean | null {
  if (typeof localStorage === "undefined") return null;
  const raw = localStorage.getItem(HIGH_CONTRAST_STORAGE_KEY);
  if (raw === "1") return true;
  if (raw === "0") return false;
  return null;
}

/** Persist the high-contrast override. `null` clears it. */
export function persistHighContrastOverride(value: boolean | null): void {
  if (typeof localStorage === "undefined") return;
  if (value === null) {
    localStorage.removeItem(HIGH_CONTRAST_STORAGE_KEY);
    return;
  }
  localStorage.setItem(HIGH_CONTRAST_STORAGE_KEY, value ? "1" : "0");
}
