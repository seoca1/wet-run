/** Combat VFX system (Tier 5.5 + Tier 5.6 + Tier 6 effect schema).
 *
 * Per-event VFX instances with tick-based animation. Each instance has a
 * kind, a tick counter, a duration, and a payload (text). Instances are
 * ticked per draw() and expired when duration reaches 0.
 *
 * Effect kinds are the canonical taxonomy from ADR-0210, declared in
 * src/data/effects.d.ts.
 *
 * Tier 6 (this commit) adds 12 v2 effects (8 skill + 4 matrix) backported
 * from Python's effects_vfx_animations.py + effects_vfx_compose.py.
 *
 * Visual effects (all ASCII, ASCII art embedded):
 * - attack:                projectile line → target (Tier 5.5)
 * - heavy_attack:          charge→slam→shockwave (Tier 6)
 * - pierce:                arrow passes through target (Tier 6)
 * - multi_hit:             3 quick strikes (Tier 6)
 * - dot:                   toxic particles around target (Tier 6)
 * - shield:                shield block glyph + bracket (Tier 5.6)
 * - heal:                  +HP rising text + green particle (Tier 5.6)
 * - regen:                 gentle pulse of + signs (Tier 6)
 * - buff / debuff:         up/down arrow + label (Tier 5.6)
 * - stun:                  status glyph + stars (Tier 5.6)
 * - counter:               shield bash returning damage (Tier 6)
 * - lifesteal:             red line target→self + heal (Tier 6)
 * - detect:                scanning reticle (Tier 6)
 * - ice_hit:               full-row red flash (Tier 5.5)
 * - player_hit:            screen shake (canvas offset) (Tier 5.5)
 * - critical_hit:          larger damage + CRIT tag (Tier 5.6)
 * - status_apply:          status glyph + label (Tier 5.5)
 * - ice_intro:             ICE-typed ASCII banner (Tier 5.6)
 * - ice_death:             ICE-typed ASCII defeat banner (Tier 5.6)
 * - boss_phase_transition: payload-driven phase 1..4 VFX (Tier 5.6)
 * - victory:               ice defeat art + rotating stars (Tier 5.5)
 * - defeat:                player defeat art + red flash (Tier 5.5)
 * - jackin_glitch:         cyan glitch particles (Tier 6 matrix)
 * - jackout_whiteout:      whiteout flash + particles (Tier 6 matrix)
 * - room_flash:            brief color flash on room entry (Tier 6 matrix)
 * - data_acquired:         gold particle burst + flash (Tier 6 matrix)
 *
 * Module layout (ADR-0110 module-size split):
 * - combat_vfx_core.ts          — taxonomy, instance model, lifecycle
 * - combat_vfx_render_combat.ts — combat / damage / status renderers
 * - combat_vfx_render_scene.ts  — ICE / boss / outcome / matrix renderers
 * This file is the public entry point: a thin re-export barrel plus the
 * render dispatcher and grid compositor.
 */
import type { Grid } from "../core/types.ts";
import { makeGrid, setText } from "../core/grid.ts";
import type { CombatVfxInstance } from "./combat_vfx_core.ts";
import { renderCombatHitVfx } from "./combat_vfx_render_combat.ts";
import { renderSceneVfx } from "./combat_vfx_render_scene.ts";

export * from "./combat_vfx_core.ts";

/** Render a single VFX frame into a grid overlay.
 *
 * The function writes the effect's visual at its current tick. The caller
 * is responsible for compositing this over the base combat grid.
 */
export function renderCombatVfx(
  instance: CombatVfxInstance,
  cols: number,
  rows: number,
): Grid {
  const grid = makeGrid(cols, rows);
  const t = instance.tick;
  const dur = instance.duration;
  const progress = dur > 0 ? t / dur : 0;
  const ctx = { instance, cols, rows, t, dur, progress };
  return renderCombatHitVfx(ctx, grid) ?? renderSceneVfx(ctx, grid) ?? grid;
}

/** Composite multiple VFX instances over a base grid (later instances override earlier).
 * Note: this returns a NEW grid (immutable).
 */
export function composeCombatVfx(
  baseGrid: Grid,
  instances: ReadonlyArray<CombatVfxInstance>,
  cols: number,
  rows: number,
): Grid {
  let out = baseGrid;
  for (const inst of instances) {
    const overlay = renderCombatVfx(inst, cols, rows);
    out = compositeGrid(out, overlay, cols, rows);
  }
  return out;
}

/** Overlay `overlay` onto `base` (overlay takes precedence where set). */
function compositeGrid(
  base: Grid,
  overlay: Grid,
  cols: number,
  rows: number,
): Grid {
  let result = base;
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const overlayCell = overlay.get(x, y);
      if (!overlayCell || overlayCell.char === " ") continue;
      const baseCell = base.get(x, y);
      if (
        baseCell &&
        baseCell.char === overlayCell.char &&
        baseCell.fg === overlayCell.fg
      ) {
        continue;
      }
      result = setText(result, x, y, overlayCell.char, overlayCell.fg);
    }
  }
  return result;
}
