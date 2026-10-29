/** P10 — reduced-motion suppresses the P1 canvas shake (ADR-0232).
 *
 * The gate is explicit and pure: `shakeStateFor` / `shakeOffsetFor` take a
 * `reducedMotion` flag, and the shake offset becomes exactly zero when it
 * is on. This is the testable seam — `main.ts` cannot be imported under
 * vitest (it self-boots), so the wiring there is verified by reading.
 */
import { describe, it, expect } from "vitest";
import {
  SHAKE_MAGNITUDE_PX,
  SHAKE_DURATION_MS,
  shakeOffsetFor,
  shakeStateFor,
  hitStopMsFor,
  hitStopDeadlineFor,
  hitStopActiveAt,
} from "../src/renderer/screen_shake.ts";

const PLAYER_HIT = Object.freeze({
  kind: "player_hit",
  elapsedMs: 40,
  durationMs: 200,
});

describe("shakeOffsetFor with reduced motion", () => {
  it("returns a zero offset when reduced motion is on", () => {
    expect(shakeOffsetFor(40, SHAKE_DURATION_MS, SHAKE_MAGNITUDE_PX, 0, true)).toEqual(
      { x: 0, y: 0 },
    );
  });

  it("returns a zero offset at every point in the envelope", () => {
    for (let t = 0; t <= SHAKE_DURATION_MS; t += 10) {
      expect(
        shakeOffsetFor(t, SHAKE_DURATION_MS, SHAKE_MAGNITUDE_PX, 0, true),
      ).toEqual({ x: 0, y: 0 });
    }
  });

  it("still shakes when reduced motion is off", () => {
    const offset = shakeOffsetFor(
      40,
      SHAKE_DURATION_MS,
      SHAKE_MAGNITUDE_PX,
      0,
      false,
    );
    expect(offset.x !== 0 || offset.y !== 0).toBe(true);
  });

  it("defaults to shaking (reduced motion off) for backwards compatibility", () => {
    const withDefault = shakeOffsetFor(
      40,
      SHAKE_DURATION_MS,
      SHAKE_MAGNITUDE_PX,
      0,
    );
    const explicitOff = shakeOffsetFor(
      40,
      SHAKE_DURATION_MS,
      SHAKE_MAGNITUDE_PX,
      0,
      false,
    );
    expect(withDefault).toEqual(explicitOff);
  });
});

describe("shakeStateFor with reduced motion", () => {
  it("returns the zero shake state when reduced motion is on", () => {
    expect(shakeStateFor([PLAYER_HIT], true)).toEqual({
      x: 0,
      y: 0,
      magnitudePx: 0,
    });
  });

  it("returns a live shake when reduced motion is off", () => {
    const state = shakeStateFor([PLAYER_HIT], false);
    expect(state.magnitudePx).toBe(SHAKE_MAGNITUDE_PX);
  });

  it("defaults to a live shake (reduced motion off)", () => {
    expect(shakeStateFor([PLAYER_HIT]).magnitudePx).toBe(SHAKE_MAGNITUDE_PX);
  });
});

describe("hit-stop with reduced motion", () => {
  const INSTANCE = Object.freeze({
    kind: "player_hit",
    elapsedMs: 0,
    durationMs: 200,
    id: 1,
  });

  it("arms no hold when reduced motion is on", () => {
    expect(hitStopDeadlineFor(0, 1000, [INSTANCE], [], true)).toBe(0);
  });

  it("arms a hold when reduced motion is off", () => {
    expect(hitStopDeadlineFor(0, 1000, [INSTANCE], [], false)).toBe(1000 + 40);
  });

  it("hitStopMsFor reports no hold when reduced motion is on", () => {
    expect(hitStopMsFor([INSTANCE], true)).toBe(0);
  });

  it("hitStopMsFor reports the hold when reduced motion is off", () => {
    expect(hitStopMsFor([INSTANCE], false)).toBe(40);
  });

  it("an armed deadline is still honoured by hitStopActiveAt", () => {
    const deadline = hitStopDeadlineFor(0, 1000, [INSTANCE], [], false);
    expect(hitStopActiveAt(deadline, 1010)).toBe(true);
  });
});
