/** P1 + P3 — combat overlay composition.
 *
 * Sits between the base combat grid and the canvas renderer. It owns two
 * presentational concerns that both need the *live* VFX instance list:
 *
 * - **P1 screen shake** — the canvas offset, derived from the `player_hit`
 *   VFX instance (the only shake trigger; proposal §R7 forbids a
 *   full-screen flash on every hit).
 * - **P3 floating damage numbers** — the rising `-N` number, derived from
 *   the damage-bearing VFX instances (`ice_hit` / `player_hit` /
 *   `critical_hit` / the skill kinds).
 *
 * Both are pure functions of the instance list — no RNG, no clock — so the
 * render layer can call them every frame without perturbing the seeded PRNG
 * the balance harness controls (ADR-0231).
 */
import type { Grid } from "../core/types.ts";
import type { CombatVfxInstance } from "./combat_vfx_core.ts";
import {
  floatingDamageKindFor,
  renderFloatingDamage,
} from "./floating_damage.js";
import { shakeStateFor, type ShakeState } from "./screen_shake.js";

/** Where a floating damage number is anchored on the grid. */
export interface DamageAnchor {
  readonly col: number;
  readonly row: number;
}

/**
 * Anchor for the damage the PLAYER took — next to the player's HP bar,
 * which `renderGrid` draws at column 2, row 5.
 */
export const PLAYER_DAMAGE_ANCHOR: DamageAnchor = Object.freeze({
  col: 2,
  row: 5,
});

/**
 * Anchor for the damage the ICE took — on the active ICE's name row, which
 * `renderGrid` draws at `iceCol - 2`.
 */
export function iceDamageAnchor(cols: number, rows: number): DamageAnchor {
  const iceCol = Math.max(20, Math.floor(cols * 0.45));
  const rosterStartRow = Math.floor(rows * 0.44);
  return { col: iceCol - 2, row: rosterStartRow };
}

/** The canvas shake for the current frame. */
export function overlayShake(
  instances: ReadonlyArray<CombatVfxInstance>,
): ShakeState {
  return shakeStateFor(instances);
}

/**
 * Draw the floating damage numbers for the live VFX instances onto the grid.
 *
 * Only the most recent instance per branch is drawn, so a multi-hit does
 * not stack three identical numbers on the same cell.
 */
export function composeFloatingDamage(
  grid: Grid,
  instances: ReadonlyArray<CombatVfxInstance>,
  cols: number,
  rows: number,
): Grid {
  if (instances.length === 0) return grid;

  const iceAnchor = iceDamageAnchor(cols, rows);
  let out = grid;
  let newestIceHit: CombatVfxInstance | null = null;
  let newestPlayerHit: CombatVfxInstance | null = null;
  let newestSkill: CombatVfxInstance | null = null;
  let newestCritical: CombatVfxInstance | null = null;

  for (const inst of instances) {
    const kind = floatingDamageKindFor(inst.kind);
    if (kind === null) continue;
    if (inst.duration <= 0 || inst.elapsedMs >= inst.durationMs) continue;
    const damage = damageOf(inst);
    if (damage <= 0) continue;

    // Later instances win — `composeCombatVfx` composites by array order,
    // so the last matching spawn is the one on screen.
    if (inst.kind === "player_hit") {
      newestPlayerHit = inst;
    } else if (kind === "critical") {
      newestCritical = inst;
    } else if (kind === "skill") {
      newestSkill = inst;
    } else {
      newestIceHit = inst;
    }
  }

  if (newestIceHit !== null) {
    out = renderFloatingDamage(
      out,
      "normal",
      damageOf(newestIceHit),
      progressOf(newestIceHit),
      iceAnchor.col,
      iceAnchor.row,
    );
  }
  if (newestSkill !== null) {
    out = renderFloatingDamage(
      out,
      "skill",
      damageOf(newestSkill),
      progressOf(newestSkill),
      iceAnchor.col,
      iceAnchor.row - 2,
    );
  }
  if (newestCritical !== null) {
    out = renderFloatingDamage(
      out,
      "critical",
      damageOf(newestCritical),
      progressOf(newestCritical),
      iceAnchor.col,
      iceAnchor.row - 4,
    );
  }
  if (newestPlayerHit !== null) {
    out = renderFloatingDamage(
      out,
      "normal",
      damageOf(newestPlayerHit),
      progressOf(newestPlayerHit),
      PLAYER_DAMAGE_ANCHOR.col,
      PLAYER_DAMAGE_ANCHOR.row,
    );
  }

  return out;
}

/** Damage carried by a VFX instance — `payloadNum` first, payload string next. */
function damageOf(instance: CombatVfxInstance): number {
  if (instance.payloadNum !== undefined && Number.isFinite(instance.payloadNum)) {
    return Math.abs(Math.trunc(instance.payloadNum));
  }
  const parsed = Number.parseInt(instance.payload, 10);
  if (Number.isFinite(parsed)) return Math.abs(parsed);
  return 0;
}

/** Frame progress of a VFX instance, 0 → 1. */
function progressOf(instance: CombatVfxInstance): number {
  if (instance.durationMs <= 0) return 0;
  return Math.min(1, instance.elapsedMs / instance.durationMs);
}
