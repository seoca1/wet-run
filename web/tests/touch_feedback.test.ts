/** Touch program-button press feedback tests (proposal P12).
 *
 * The input path itself (`pointerdown` → `handleProgramButton`) was already
 * latency-free; what was missing was the *in-game* acknowledgement. These
 * assertions cover the pure state machine that owns it.
 */
import { describe, it, expect } from "vitest";
import {
  IDLE_PRESS_FEEDBACK,
  PRESS_FEEDBACK_MS,
  expirePressFeedback,
  hasPressFeedback,
  isPressFeedbackLive,
  pressFeedbackLabel,
  pressProgramButton,
} from "../src/core/touch_feedback.ts";

describe("P12 — press feedback state machine", () => {
  it("starts idle", () => {
    expect(hasPressFeedback(IDLE_PRESS_FEEDBACK)).toBe(false);
    expect(IDLE_PRESS_FEEDBACK.handIndex).toBeNull();
    expect(IDLE_PRESS_FEEDBACK.deadlineMs).toBeNull();
  });

  it("acknowledges a press on the program button", () => {
    const next = pressProgramButton(IDLE_PRESS_FEEDBACK, 3, 1000);
    expect(next.handIndex).toBe(3);
    expect(hasPressFeedback(next)).toBe(true);
  });

  it("sets the deadline to now + PRESS_FEEDBACK_MS", () => {
    const next = pressProgramButton(IDLE_PRESS_FEEDBACK, 1, 1000);
    expect(next.deadlineMs).toBe(1000 + PRESS_FEEDBACK_MS);
  });

  it("ignores a press on an invalid hand index", () => {
    const next = pressProgramButton(IDLE_PRESS_FEEDBACK, 0, 1000);
    expect(next).toBe(IDLE_PRESS_FEEDBACK);
    expect(hasPressFeedback(next)).toBe(false);
  });

  it("ignores a non-integer hand index", () => {
    const next = pressProgramButton(IDLE_PRESS_FEEDBACK, 2.5, 1000);
    expect(next).toBe(IDLE_PRESS_FEEDBACK);
  });

  it("keeps the acknowledgement alive before the deadline", () => {
    const pressed = pressProgramButton(IDLE_PRESS_FEEDBACK, 2, 1000);
    const still = expirePressFeedback(pressed, 1000 + PRESS_FEEDBACK_MS - 1);
    expect(hasPressFeedback(still)).toBe(true);
    expect(still.handIndex).toBe(2);
  });

  it("expires the acknowledgement at the deadline", () => {
    const pressed = pressProgramButton(IDLE_PRESS_FEEDBACK, 2, 1000);
    const expired = expirePressFeedback(pressed, 1000 + PRESS_FEEDBACK_MS);
    expect(hasPressFeedback(expired)).toBe(false);
    expect(expired.handIndex).toBeNull();
  });

  it("expires the acknowledgement when a frame arrives late", () => {
    const pressed = pressProgramButton(IDLE_PRESS_FEEDBACK, 2, 1000);
    const expired = expirePressFeedback(pressed, 1000 + PRESS_FEEDBACK_MS + 5000);
    expect(hasPressFeedback(expired)).toBe(false);
  });

  it("is a no-op to expire an already-idle state", () => {
    expect(expirePressFeedback(IDLE_PRESS_FEEDBACK, 99999)).toBe(
      IDLE_PRESS_FEEDBACK,
    );
  });

  it("re-acknowledges a second press on a different button", () => {
    const first = pressProgramButton(IDLE_PRESS_FEEDBACK, 1, 1000);
    const second = pressProgramButton(first, 5, 1100);
    expect(second.handIndex).toBe(5);
    expect(second.deadlineMs).toBe(1100 + PRESS_FEEDBACK_MS);
  });

  it("re-acknowledges a repeat press on the same button", () => {
    const first = pressProgramButton(IDLE_PRESS_FEEDBACK, 4, 1000);
    const second = pressProgramButton(first, 4, 1200);
    expect(second.handIndex).toBe(4);
    expect(second.deadlineMs).toBe(1200 + PRESS_FEEDBACK_MS);
  });

  it("reports liveness without rebuilding the state", () => {
    const pressed = pressProgramButton(IDLE_PRESS_FEEDBACK, 1, 1000);
    expect(isPressFeedbackLive(pressed, 1000)).toBe(true);
    expect(isPressFeedbackLive(pressed, 1000 + PRESS_FEEDBACK_MS)).toBe(false);
    expect(isPressFeedbackLive(IDLE_PRESS_FEEDBACK, 0)).toBe(false);
  });
});

describe("P12 — press feedback label", () => {
  it("is empty when idle", () => {
    expect(pressFeedbackLabel(IDLE_PRESS_FEEDBACK)).toBe("");
  });

  it("shows the hand index when acknowledged", () => {
    const pressed = pressProgramButton(IDLE_PRESS_FEEDBACK, 3, 0);
    expect(pressFeedbackLabel(pressed)).toBe("> 3");
  });

  it("includes the program label when supplied", () => {
    const pressed = pressProgramButton(IDLE_PRESS_FEEDBACK, 3, 0);
    expect(pressFeedbackLabel(pressed, "back")).toBe("> 3.back");
  });

  it("falls back to the index when the program label is empty", () => {
    const pressed = pressProgramButton(IDLE_PRESS_FEEDBACK, 3, 0);
    expect(pressFeedbackLabel(pressed, "")).toBe("> 3");
  });
});

describe("P12 — press feedback is RNG-neutral", () => {
  it("consumes no Math.random draws", () => {
    const original = Math.random;
    let draws = 0;
    Math.random = (): number => {
      draws += 1;
      return original();
    };
    try {
      let state = IDLE_PRESS_FEEDBACK;
      state = pressProgramButton(state, 1, 0);
      state = pressProgramButton(state, 2, 10);
      state = expirePressFeedback(state, 100000);
      state = pressProgramButton(state, 3, 200000);
    } finally {
      Math.random = original;
    }
    expect(draws).toBe(0);
  });
});
