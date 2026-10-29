/** P1 — canvas-level screen shake + hit-stop.
 *
 * The `player_hit` VFX renderer only ever moved grid *characters*; the canvas
 * itself never moved (`docs/design/combat-feel-and-interaction-proposal.md`
 * §1.3 M4). This module owns the renderer-level shake:
 *
 * - `shakeOffsetFor` — PURE. Decaying oscillation, no RNG and no clock, so
 *   it can be driven from the rAF render loop without touching the reducer
 *   and without perturbing the seeded PRNG the balance harness controls
 *   (see ADR-0231 §"VFX spawn 은 RNG-neutral 이 아니었고").
 * - `shakeStateFor` — derives the live shake offset from the *existing*
 *   `player_hit` VFX instances. No new spawn site, hence no new RNG draw.
 * - `hitStopMsFor` — the presentation-only freeze. Proposal §R3 ("히트스톱은
 *   연출 전용(50ms 이내)") forbids using hit-stop to delay an enemy turn,
 *   because that would be a balance change. This value is consumed by the
 *   render layer only.
 *
 * Magnitude / duration follow `docs/design/systems/animations.md:171-174`:
 * "1-2 픽셀, 100-200ms".
 */

/** Peak shake magnitude in CSS pixels (design spec: 1-2px). */
export const SHAKE_MAGNITUDE_PX = 2;

/** Shake duration in milliseconds (design spec: 100-200ms). */
export const SHAKE_DURATION_MS = 200;

/** Upper bound for the presentation-only hit-stop (proposal §R3: ≤50ms). */
export const HIT_STOP_MAX_MS = 50;

/** Milliseconds of hit-stop applied when a `player_hit` frame is born. */
export const HIT_STOP_MS = 40;

/** A pixel offset applied to the whole canvas. */
export interface ScreenOffset {
  readonly x: number;
  readonly y: number;
}

/** The live shake state: the offset plus the magnitude it was derived from. */
export interface ShakeState extends ScreenOffset {
  /** Peak magnitude of the shake that produced this offset (0 = no shake). */
  readonly magnitudePx: number;
}

const NO_SHAKE: ShakeState = Object.freeze({ x: 0, y: 0, magnitudePx: 0 });

/** The VFX kind that shakes the canvas. */
const SHAKE_VFX_KIND = "player_hit";

/** Phase offset so the first shake frame already carries a displacement. */
const SHAKE_START_PHASE = Math.PI / 3;

/**
 * Shake frequencies in radians per second. The design spec asks for a *fast*
 * vibration ("빠르게 진동", animations.md:174) — roughly 20Hz and 27Hz, which
 * read as a jitter rather than a swing.
 */
const SHAKE_FREQ_X = 126;
const SHAKE_FREQ_Y = 170;

/**
 * Pure decaying shake offset.
 *
 * The envelope is `1 - t/duration` (linear decay to exactly zero at the
 * end) and the oscillation is a pair of sines at different frequencies, so
 * the motion reads as a jitter rather than a drift. `phase` shifts the
 * oscillation so two concurrent shakes do not move in lockstep — it is
 * derived from the caller, never from `Math.random`.
 *
 * The result is rounded to whole pixels (the canvas can only translate by
 * whole pixels), but the *sign* of each axis is preserved: a rounded
 * magnitude of zero keeps the axis's direction, so the shake never reads as
 * a dead frame mid-vibration.
 */
export function shakeOffsetFor(
  elapsedMs: number,
  durationMs: number = SHAKE_DURATION_MS,
  magnitudePx: number = SHAKE_MAGNITUDE_PX,
  phase: number = 0,
  reducedMotion: boolean = false,
): ScreenOffset {
  if (reducedMotion) return { x: 0, y: 0 };
  if (durationMs <= 0 || elapsedMs < 0 || magnitudePx <= 0) {
    return { x: 0, y: 0 };
  }
  if (elapsedMs >= durationMs) return { x: 0, y: 0 };

  const envelope = 1 - elapsedMs / durationMs;
  const t = elapsedMs / 1000;
  // The sine terms are phase-shifted off zero so the very first frame of a
  // shake already carries a displacement — an impact does not begin at rest.
  const rawX = Math.sin(t * SHAKE_FREQ_X + phase + SHAKE_START_PHASE);
  const rawY = Math.sin(t * SHAKE_FREQ_Y + phase * 1.7 + SHAKE_START_PHASE * 1.3);
  const scaledX = rawX * magnitudePx * envelope;
  const scaledY = rawY * magnitudePx * envelope * 0.5;
  return {
    x: roundWithSign(scaledX),
    y: roundWithSign(scaledY),
  };
}

/** Round to the nearest pixel, keeping the sign so a rounded-down value
 * still shows which way the axis is moving. */
function roundWithSign(value: number): number {
  const rounded = Math.round(value);
  if (rounded !== 0) return rounded;
  return value > 0 ? 1 : value < 0 ? -1 : 0;
}

/**
 * Derive the canvas shake from the live VFX instance list.
 *
 * Only `player_hit` shakes the screen (the proposal's §R7 forbids a
 * full-screen flash on every hit). When several `player_hit` instances are
 * alive at once the last one wins — rendering composites by array order,
 * so the most recent spawn is the one on screen.
 */
export function shakeStateFor(
  instances: ReadonlyArray<{
    readonly kind: string;
    readonly elapsedMs: number;
    readonly durationMs: number;
  }>,
  reducedMotion: boolean = false,
): ShakeState {
  if (reducedMotion) return NO_SHAKE;

  let newest: {
    readonly elapsedMs: number;
    readonly durationMs: number;
  } | null = null;

  for (const inst of instances) {
    if (inst.kind !== SHAKE_VFX_KIND) continue;
    if (inst.durationMs <= 0 || inst.elapsedMs >= inst.durationMs) continue;
    newest = inst;
  }

  if (newest === null) return NO_SHAKE;

  // The phase is derived from the elapsed time — deterministic, RNG-free.
  const phase = (newest.elapsedMs % 7) * 0.9;
  const offset = shakeOffsetFor(
    newest.elapsedMs,
    newest.durationMs,
    SHAKE_MAGNITUDE_PX,
    phase,
    reducedMotion,
  );
  return { x: offset.x, y: offset.y, magnitudePx: SHAKE_MAGNITUDE_PX };
}

/** The VFX instance shape the hit-stop helpers read. */
export interface HitStopInstance {
  readonly kind: string;
  readonly elapsedMs: number;
  readonly durationMs: number;
  readonly id: number;
}

/**
 * Presentation-only hit-stop for the current frame.
 *
 * Returns the number of milliseconds the *animation* should hold, or 0.
 * The enemy turn is never delayed by this value (proposal §R3) — it only
 * holds the impact frame so the shake reads as an impact.
 *
 * NOTE: this is the *duration* of a hold, not its liveness. Use
 * `hitStopDeadlineFor` to decide whether a hold is still active — see the
 * deadlock note there.
 */
export function hitStopMsFor(
  instances: ReadonlyArray<HitStopInstance>,
  reducedMotion: boolean = false,
): number {
  if (reducedMotion) return 0;
  for (const inst of instances) {
    if (inst.kind !== SHAKE_VFX_KIND) continue;
    if (inst.durationMs <= 0 || inst.elapsedMs >= inst.durationMs) continue;
    // Only the first frame of a fresh hit is frozen.
    if (inst.elapsedMs < HIT_STOP_MS) return HIT_STOP_MS;
  }
  return 0;
}

/**
 * Wall-clock deadline for the next hit-stop hold.
 *
 * The hold MUST be bounded by wall clock, never by the VFX instance's own
 * `elapsedMs`. An earlier version derived the hold from `elapsedMs <
 * HIT_STOP_MS` while the hold itself is what freezes `elapsedMs` — a
 * self-locked condition. At any frame rate above 25fps the derived advance
 * (`deltaMs - HIT_STOP_MS`) floors at 0, so `elapsedMs` never moved, the
 * hold never released, and the VFX froze permanently.
 *
 * The deadline is therefore an absolute wall-clock timestamp:
 *
 * - a *newly appeared* `player_hit` — one whose `id` was not in the previous
 *   frame's list — arms the deadline at `nowMs + HIT_STOP_MS`;
 * - an already-running hold is NOT re-armed, so the deadline cannot be
 *   pushed forward indefinitely;
 * - a hold that has expired is not re-armed until another new hit appears.
 *
 * The trigger is *identity* (`id` not seen last frame), never `elapsedMs`:
 * during a hold the instance's `elapsedMs` stays at 0, so an elapsed-based
 * trigger would re-arm every frame and slide the deadline forward forever —
 * the same permanent freeze in a new shape.
 *
 * Pure: no RNG, no clock read, no mutation of the inputs.
 *
 * @param previousDeadlineMs the deadline currently in force (0 = none)
 * @param nowMs             the current wall-clock timestamp in ms
 * @param instances         the live VFX instance list
 * @param previousInstances the instance list from the previous frame
 */
export function hitStopDeadlineFor(
  previousDeadlineMs: number,
  nowMs: number,
  instances: ReadonlyArray<HitStopInstance>,
  previousInstances: ReadonlyArray<HitStopInstance> = [],
  reducedMotion: boolean = false,
): number {
  if (reducedMotion) return 0;

  // An in-flight hold keeps its original deadline — re-arming here would
  // let a long-lived instance push the deadline forward forever.
  if (previousDeadlineMs > 0 && nowMs < previousDeadlineMs) {
    return previousDeadlineMs;
  }

  const seenBefore = new Set(previousInstances.map((inst) => inst.id));
  for (const inst of instances) {
    if (inst.kind !== SHAKE_VFX_KIND) continue;
    if (inst.durationMs <= 0 || inst.elapsedMs >= inst.durationMs) continue;
    // A hit that was not present in the previous frame is new.
    if (!seenBefore.has(inst.id)) {
      return nowMs + HIT_STOP_MS;
    }
  }

  return 0;
}

/** Whether a hit-stop hold is still in force at `nowMs`. */
export function hitStopActiveAt(
  deadlineMs: number,
  nowMs: number,
): boolean {
  return deadlineMs > 0 && nowMs < deadlineMs;
}
