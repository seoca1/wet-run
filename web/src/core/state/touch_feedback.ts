/** Touch program-button press feedback (proposal P12) — pure module.
 *
 * The virtual gamepad's program buttons already fire on `pointerdown`
 * (`input/touch.ts`), so there is no input latency to fix. What was missing
 * is **in-game feedback**: the only sign that a tap registered was the CSS
 * `:active` state of the button itself, which vanishes the moment the finger
 * lifts — and on a canvas-rendered game the player is looking at the canvas,
 * not at the HTML overlay.
 *
 * This module owns the small state machine that turns a button press into a
 * short-lived, visible acknowledgement:
 *
 *   idle ──press──▶ acknowledged ──expire──▶ idle
 *
 * The state is intentionally *pure*: a press produces a new immutable
 * snapshot, and expiry is driven by an explicit wall-clock deadline rather
 * than a timer, so the model can be tested deterministically and cannot
 * consume `Math.random` (the balance harness seeds it).
 */

/** How long a press acknowledgement stays visible (milliseconds). */
export const PRESS_FEEDBACK_MS = 400;

/** The visual state of the program-button acknowledgement. */
export interface PressFeedbackState {
  /** 1-based hand index that was pressed, or `null` when idle. */
  readonly handIndex: number | null;
  /** Wall-clock deadline (ms) after which the acknowledgement expires. */
  readonly deadlineMs: number | null;
}

/** The idle state — no acknowledgement is showing. */
export const IDLE_PRESS_FEEDBACK: PressFeedbackState = Object.freeze({
  handIndex: null,
  deadlineMs: null,
});

/** Whether an acknowledgement is currently showing. */
export function hasPressFeedback(
  state: PressFeedbackState,
): boolean {
  return state.handIndex !== null;
}

/**
 * Record a button press.
 *
 * `nowMs` is a wall-clock timestamp supplied by the caller — the module never
 * reads the clock itself, which keeps it pure and deterministic under test.
 * A press on an invalid hand index (below 1) is ignored and the state is
 * returned unchanged.
 */
export function pressProgramButton(
  _state: PressFeedbackState,
  handIndex: number,
  nowMs: number,
): PressFeedbackState {
  if (!Number.isInteger(handIndex) || handIndex < 1) {
    return _state;
  }
  return { handIndex, deadlineMs: nowMs + PRESS_FEEDBACK_MS };
}

/**
 * Drop the acknowledgement once its deadline has passed.
 *
 * The expiry is compared against the wall clock, so a frame that arrives late
 * clears the acknowledgement instead of leaving a stale one on screen.
 */
export function expirePressFeedback(
  state: PressFeedbackState,
  nowMs: number,
): PressFeedbackState {
  if (state.deadlineMs === null) return state;
  if (nowMs < state.deadlineMs) return state;
  return IDLE_PRESS_FEEDBACK;
}

/** The label shown for an acknowledged press (e.g. `> 3.prog`). */
export function pressFeedbackLabel(
  state: PressFeedbackState,
  programLabel?: string,
): string {
  if (state.handIndex === null) return "";
  if (programLabel === undefined || programLabel === "") {
    return `> ${state.handIndex}`;
  }
  return `> ${state.handIndex}.${programLabel}`;
}

/**
 * Whether the acknowledgement is still live at `nowMs`.
 *
 * Mirrors `expirePressFeedback` but as a predicate, so a render path can ask
 * "should I draw this?" without rebuilding the state.
 */
export function isPressFeedbackLive(
  state: PressFeedbackState,
  nowMs: number,
): boolean {
  if (state.deadlineMs === null) return false;
  return nowMs < state.deadlineMs;
}
