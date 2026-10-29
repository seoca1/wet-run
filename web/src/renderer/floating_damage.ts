/** P3 — floating damage numbers.
 *
 * The only damage readout today is a fixed-position `HIT! -N` text line
 * (`combat_vfx_render_combat.ts`). The design spec
 * (`docs/design/systems/animations.md`) asks for a damage number that
 * *floats up* from the impact point, branching on colour and size:
 *
 * | branch    | colour          | size  | spec                 |
 * | --------- | --------------- | ----- | -------------------- |
 * | `normal`  | white           | small | animations.md:38-39  |
 * | `skill`   | yellow          | large | animations.md:60-61  |
 * | `critical`| CRIT gold       | large | animations.md:108-112|
 *
 * Everything here is PURE — no RNG, no clock — so the number can be drawn
 * from the live VFX progress without perturbing the seeded PRNG the balance
 * harness controls (ADR-0231).
 *
 * The ASCII/Canvas2D aesthetic is preserved: the number is drawn *into the
 * grid*, not as a DOM overlay (proposal §R6 rejected sprite/DOM numbers).
 */
import type { Grid } from "../core/types.ts";
import { setText } from "../core/grid.ts";
import { PALETTE } from "./palette.ts";

/** The damage-number branches. */
export type FloatingDamageKind = "normal" | "skill" | "critical";

/** All branches, in ascending order of visual weight. */
export const FLOATING_DAMAGE_KINDS: ReadonlyArray<FloatingDamageKind> = [
  "normal",
  "skill",
  "critical",
];

/** How many rows the number rises over its whole lifetime. */
export const FLOATING_DAMAGE_RISE_ROWS = 4;

interface KindStyle {
  readonly color: string;
  /** 1 = single cell height, 2 = double height (spans two rows). */
  readonly scale: number;
  /** Whether the number is bracketed by sparkles. */
  readonly sparkles: boolean;
}

const KIND_STYLES: Readonly<Record<FloatingDamageKind, KindStyle>> = {
  normal: { color: PALETTE.WHITE, scale: 1, sparkles: false },
  skill: { color: PALETTE.YELLOW, scale: 2, sparkles: false },
  critical: { color: PALETTE.CRIT_COLOR, scale: 2, sparkles: true },
};

/** One rendered damage number. */
export interface FloatingDamage {
  readonly kind: FloatingDamageKind;
  /** The text as drawn (e.g. `-25`, `✦-50✦`). */
  readonly text: string;
  /** Column of the first character. */
  readonly col: number;
  /** Row of the first character. */
  readonly row: number;
  readonly color: string;
  readonly scale: number;
}

function clampProgress(progress: number): number {
  if (!Number.isFinite(progress)) return 0;
  if (progress < 0) return 0;
  if (progress > 1) return 1;
  return progress;
}

function styleFor(kind: FloatingDamageKind): KindStyle {
  return KIND_STYLES[kind] ?? KIND_STYLES.normal;
}

/**
 * Compute the floating damage number for a frame.
 *
 * @param kind      visual branch (colour + size)
 * @param damage    damage amount (absolute value is used)
 * @param progress  0 = freshly spawned, 1 = fully risen
 * @param col       anchor column (the impact point)
 * @param row       anchor row (the impact point) — the number rises from here
 */
export function floatingDamageFor(
  kind: FloatingDamageKind,
  damage: number,
  progress: number,
  col: number,
  row: number,
): FloatingDamage {
  const style = styleFor(kind);
  const p = clampProgress(progress);
  const amount = Math.abs(Math.trunc(Number.isFinite(damage) ? damage : 0));
  const body = `-${amount}`;
  const text = style.sparkles ? `✦${body}✦` : body;
  const risen = Math.round(p * FLOATING_DAMAGE_RISE_ROWS);
  return {
    kind,
    text,
    col: Math.max(0, Math.trunc(col)),
    row: Math.max(0, Math.trunc(row) - risen),
    color: style.color,
    scale: style.scale,
  };
}

/**
 * The full rise animation for a damage number — one entry per frame.
 *
 * Used by the renderer to sweep the number up the grid across the VFX's
 * lifetime.
 */
export function floatingDamageRows(
  kind: FloatingDamageKind,
  damage: number,
  frames: number,
  col: number,
  row: number,
): ReadonlyArray<FloatingDamage> {
  const count = Math.max(1, Math.trunc(frames));
  const out: FloatingDamage[] = [];
  for (let i = 0; i < count; i++) {
    out.push(
      floatingDamageFor(kind, damage, count === 1 ? 0 : i / (count - 1), col, row),
    );
  }
  return out;
}

/**
 * Draw a floating damage number into the grid.
 *
 * A zero damage value draws nothing (there is nothing to report).
 */
export function renderFloatingDamage(
  grid: Grid,
  kind: FloatingDamageKind,
  damage: number,
  progress: number,
  col: number,
  row: number,
): Grid {
  if (!Number.isFinite(damage) || Math.trunc(damage) === 0) return grid;
  const f = floatingDamageFor(kind, damage, progress, col, row);
  let out = setText(grid, f.col, f.row, f.text, f.color);
  if (f.scale >= 2) {
    // A "large" number gets a second row so it reads bigger than the
    // single-cell normal number.
    out = setText(out, f.col, f.row + 1, f.text, f.color);
  }
  return out;
}

/**
 * The branch a damage VFX belongs to.
 *
 * `critical_hit` → the largest, gold number; the skill kinds
 * (`heavy_attack` / `pierce` / `multi_hit` / `dot` / `counter` /
 * `lifesteal`) → the large yellow number; `ice_hit` → the small white
 * number (the "normal attack" case). `player_hit` is the damage the PLAYER
 * took, which reads as a hit on the player rather than on the ICE.
 */
export function floatingDamageKindFor(vfxKind: string): FloatingDamageKind | null {
  switch (vfxKind) {
    case "critical_hit":
      return "critical";
    case "heavy_attack":
    case "pierce":
    case "multi_hit":
    case "dot":
    case "counter":
    case "lifesteal":
      return "skill";
    case "ice_hit":
    case "player_hit":
      return "normal";
    default:
      return null;
  }
}
