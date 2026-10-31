/** Combat-entry presentation (proposal P15) — pure module.
 *
 * The `ice_intro` VFX ("INCOMING: <ICE>" banner + scanning line) already had
 * a complete renderer (`renderer/combat_vfx_render_scene.ts:19-52`) and a
 * canonical duration (`state_helpers.ts`), but **no spawn site** — combat
 * started as an instant cut from the approach screen. This module owns the
 * decision of *what* to spawn; the reducer owns *when*.
 *
 * The spawn is deliberately **RNG-neutral**: `import_vfx` draws its id from
 * `Math.random`, and the balance harness seeds `Math.random`, so a new
 * `import_vfx` call would silently shift the calibrated grade curve
 * (ADR-0229). `import_vfx_deterministic` draws nothing.
 */

/** The payload shown in the `ice_intro` banner — the ICE's display name. */
export function iceIntroPayload(iceName: string): string {
  const trimmed = iceName.trim();
  return trimmed === "" ? "ICE" : trimmed;
}

/** How long the `ice_intro` banner stays on screen (ticks). */
export const ICE_INTRO_DURATION_TICKS = 8;

/**
 * The band of grid rows the `ice_intro` banner paints.
 *
 * The renderer writes the banner on rows 1..3 and the scanning line on row 5
 * (`combat_vfx_render_scene.ts:19-52`). The combat-entry hint must stay
 * clear of this band, otherwise the hint and the banner overlap.
 */
export const ICE_INTRO_BANNER_ROWS: readonly number[] = [1, 2, 3, 5];
