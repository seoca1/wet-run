/** P1 — canvas-level screen shake + hit-stop (unit tests).
 *
 * The `player_hit` VFX only ever shook grid *characters*; the canvas itself
 * never moved. These tests pin the new renderer-level shake:
 *
 * - `shakeOffsetFor` is a PURE function (no RNG, no Date) so it can be
 *   driven from the rAF render loop without touching the reducer.
 * - The shake magnitude decays to 0 by the end of the VFX lifetime
 *   (`docs/design/systems/animations.md:171-174` — "1-2 픽셀, 100-200ms").
 * - `shakeStateFor` derives the offset from the live VFX instance list, so
 *   the shake is driven by the *existing* `player_hit` spawn (no new spawn
 *   site, hence no new RNG draw).
 * - `hitStopMsFor` is presentation-only and bounded well under the 50ms
 *   ceiling the proposal's §R3 (rejected ideas) imposes.
 */
import { describe, it, expect } from "vitest";
import {
  SHAKE_MAGNITUDE_PX,
  SHAKE_DURATION_MS,
  HIT_STOP_MAX_MS,
  HIT_STOP_MS,
  shakeOffsetFor,
  shakeStateFor,
  hitStopMsFor,
  hitStopDeadlineFor,
  hitStopActiveAt,
} from "../src/renderer/screen_shake.js";
import {
  triggerCombatVfxMs,
  advanceVfxListBy,
} from "../src/renderer/combat_vfx.js";

describe("P1 screen shake constants", () => {
  it("uses a 1-2px magnitude per the animation spec", () => {
    expect(SHAKE_MAGNITUDE_PX).toBeGreaterThanOrEqual(1);
    expect(SHAKE_MAGNITUDE_PX).toBeLessThanOrEqual(2);
  });

  it("uses a 100-200ms shake duration per the animation spec", () => {
    expect(SHAKE_DURATION_MS).toBeGreaterThanOrEqual(100);
    expect(SHAKE_DURATION_MS).toBeLessThanOrEqual(200);
  });

  it("bounds the hit-stop at 50ms or less (presentation-only)", () => {
    expect(HIT_STOP_MAX_MS).toBeLessThanOrEqual(50);
    expect(HIT_STOP_MAX_MS).toBeGreaterThan(0);
  });
});

describe("P1 shakeOffsetFor (pure, deterministic)", () => {
  it("returns zero offset before the shake starts", () => {
    expect(shakeOffsetFor(-1, SHAKE_DURATION_MS)).toEqual({ x: 0, y: 0 });
  });

  it("returns a non-zero offset at the start of the shake", () => {
    const offset = shakeOffsetFor(0, SHAKE_DURATION_MS);
    expect(offset.x !== 0 || offset.y !== 0).toBe(true);
  });

  it("decays to zero exactly at the end of the duration", () => {
    expect(shakeOffsetFor(SHAKE_DURATION_MS, SHAKE_DURATION_MS)).toEqual({
      x: 0,
      y: 0,
    });
  });

  it("decays monotonically in magnitude towards the end", () => {
    const early = Math.abs(shakeOffsetFor(0, SHAKE_DURATION_MS).x) +
      Math.abs(shakeOffsetFor(0, SHAKE_DURATION_MS).y);
    const late = Math.abs(shakeOffsetFor(SHAKE_DURATION_MS - 20, SHAKE_DURATION_MS).x) +
      Math.abs(shakeOffsetFor(SHAKE_DURATION_MS - 20, SHAKE_DURATION_MS).y);
    expect(late).toBeLessThanOrEqual(early);
  });

  it("never exceeds the declared magnitude in pixels", () => {
    for (let t = 0; t <= SHAKE_DURATION_MS; t += 5) {
      const o = shakeOffsetFor(t, SHAKE_DURATION_MS);
      expect(Math.abs(o.x)).toBeLessThanOrEqual(SHAKE_MAGNITUDE_PX);
      expect(Math.abs(o.y)).toBeLessThanOrEqual(SHAKE_MAGNITUDE_PX);
    }
  });

  it("never produces a dead frame before the shake ends", () => {
    for (let t = 0; t < SHAKE_DURATION_MS; t += 4) {
      const o = shakeOffsetFor(t, SHAKE_DURATION_MS);
      expect(o.x !== 0 || o.y !== 0).toBe(true);
    }
  });

  it("jitters in both directions over its lifetime", () => {
    let minX = 0;
    let maxX = 0;
    for (let t = 0; t < SHAKE_DURATION_MS; t += 4) {
      const o = shakeOffsetFor(t, SHAKE_DURATION_MS);
      minX = Math.min(minX, o.x);
      maxX = Math.max(maxX, o.x);
    }
    expect(minX).toBeLessThan(0);
    expect(maxX).toBeGreaterThan(0);
  });

  it("is deterministic — the same input yields the same output", () => {
    expect(shakeOffsetFor(37, SHAKE_DURATION_MS)).toEqual(
      shakeOffsetFor(37, SHAKE_DURATION_MS),
    );
  });

  it("does not consume Math.random (RNG-neutral)", () => {
    const original = Math.random;
    let calls = 0;
    Math.random = () => {
      calls += 1;
      return original();
    };
    try {
      shakeOffsetFor(10, SHAKE_DURATION_MS);
      shakeOffsetFor(20, SHAKE_DURATION_MS);
    } finally {
      Math.random = original;
    }
    expect(calls).toBe(0);
  });

  it("handles a zero duration without dividing by zero", () => {
    expect(shakeOffsetFor(0, 0)).toEqual({ x: 0, y: 0 });
  });
});

describe("P1 shakeStateFor (driven by the existing player_hit VFX)", () => {
  it("returns no shake when there are no VFX instances", () => {
    expect(shakeStateFor([])).toEqual({ x: 0, y: 0, magnitudePx: 0 });
  });

  it("returns no shake for a VFX instance that is not a player_hit", () => {
    const inst = triggerCombatVfxMs("ice_hit", "", 160);
    expect(shakeStateFor([inst])).toEqual({ x: 0, y: 0, magnitudePx: 0 });
  });

  it("shakes while a player_hit instance is alive", () => {
    const inst = triggerCombatVfxMs("player_hit", "", 200);
    const state = shakeStateFor([inst]);
    expect(state.magnitudePx).toBeGreaterThan(0);
    expect(state.x !== 0 || state.y !== 0).toBe(true);
  });

  it("stops shaking once the player_hit instance has expired", () => {
    const inst = triggerCombatVfxMs("player_hit", "", 200);
    const expired = { ...inst, elapsedMs: 200 };
    expect(shakeStateFor([expired])).toEqual({ x: 0, y: 0, magnitudePx: 0 });
  });

  it("does not consume Math.random (RNG-neutral)", () => {
    const inst = triggerCombatVfxMs("player_hit", "", 200);
    const original = Math.random;
    let calls = 0;
    Math.random = () => {
      calls += 1;
      return original();
    };
    try {
      shakeStateFor([inst]);
    } finally {
      Math.random = original;
    }
    expect(calls).toBe(0);
  });

  it("lets the last player_hit instance win when several are alive", () => {
    const first = { ...triggerCombatVfxMs("player_hit", "", 200), elapsedMs: 0 };
    const second = { ...triggerCombatVfxMs("player_hit", "", 200), elapsedMs: 100 };
    const state = shakeStateFor([first, second]);
    expect(state.x).toBe(
      shakeOffsetFor(100, 200, SHAKE_MAGNITUDE_PX, (100 % 7) * 0.9).x,
    );
  });
});

describe("P1 hitStopMsFor (presentation-only freeze)", () => {
  it("returns 0 when no player_hit instance is present", () => {
    expect(hitStopMsFor([])).toBe(0);
  });

  it("returns a bounded freeze while a player_hit is alive", () => {
    const inst = triggerCombatVfxMs("player_hit", "", 200);
    const stop = hitStopMsFor([inst]);
    expect(stop).toBeGreaterThan(0);
    expect(stop).toBeLessThanOrEqual(HIT_STOP_MAX_MS);
  });

  it("returns 0 once the player_hit has expired", () => {
    const inst = triggerCombatVfxMs("player_hit", "", 200);
    const expired = { ...inst, elapsedMs: 200 };
    expect(hitStopMsFor([expired])).toBe(0);
  });
});

describe("P1 hitStopDeadlineFor (wall-clock bounded hold)", () => {
  it("arms a deadline HIT_STOP_MS in the future for a newly appeared player_hit", () => {
    const inst = triggerCombatVfxMs("player_hit", "", 200);
    expect(hitStopDeadlineFor(0, 1000, [inst], [])).toBe(1000 + HIT_STOP_MS);
  });

  it("does not arm when there is no player_hit", () => {
    expect(hitStopDeadlineFor(0, 1000, [], [])).toBe(0);
  });

  it("does not arm for a player_hit that was already present last frame", () => {
    const inst = triggerCombatVfxMs("player_hit", "", 200);
    expect(hitStopDeadlineFor(0, 1000, [inst], [inst])).toBe(0);
  });

  it("does not arm for a player_hit whose elapsedMs is still 0 mid-hold", () => {
    const inst = triggerCombatVfxMs("player_hit", "", 200);
    // The instance is held at elapsedMs 0 for the whole hold — an
    // elapsed-based trigger would re-arm every frame and never release.
    expect(hitStopDeadlineFor(0, 1000, [inst], [inst])).toBe(0);
  });

  it("keeps an in-flight deadline instead of re-arming it", () => {
    const inst = triggerCombatVfxMs("player_hit", "", 200);
    expect(hitStopDeadlineFor(1500, 1000, [inst], [])).toBe(1500);
  });

  it("does not push an expired deadline forward", () => {
    const inst = triggerCombatVfxMs("player_hit", "", 200);
    // The deadline has passed (nowMs > deadlineMs) and the instance was
    // already present last frame, so no new hold is armed.
    expect(hitStopDeadlineFor(1500, 1600, [inst], [inst])).toBe(0);
  });

  it("arms again when a different player_hit appears", () => {
    const first = triggerCombatVfxMs("player_hit", "", 200);
    const second = {
      ...triggerCombatVfxMs("player_hit", "", 200),
      id: first.id + 1,
    };
    expect(hitStopDeadlineFor(0, 1000, [first, second], [first])).toBe(
      1000 + HIT_STOP_MS,
    );
  });

  it("does not consume Math.random (RNG-neutral)", () => {
    const inst = triggerCombatVfxMs("player_hit", "", 200);
    const original = Math.random;
    let calls = 0;
    Math.random = () => {
      calls += 1;
      return original();
    };
    try {
      hitStopDeadlineFor(0, 1000, [inst], []);
    } finally {
      Math.random = original;
    }
    expect(calls).toBe(0);
  });
});

describe("P1 hitStopActiveAt", () => {
  it("is active strictly before the deadline", () => {
    expect(hitStopActiveAt(1040, 1039)).toBe(true);
  });

  it("is inactive at and after the deadline", () => {
    expect(hitStopActiveAt(1040, 1040)).toBe(false);
    expect(hitStopActiveAt(1040, 1041)).toBe(false);
  });

  it("is inactive with no deadline", () => {
    expect(hitStopActiveAt(0, 0)).toBe(false);
    expect(hitStopActiveAt(0, 1000)).toBe(false);
  });
});

describe("P1 hit-stop regression — the loop must never freeze a VFX", () => {
  /**
   * Simulates `Game.loop`'s hit-stop block exactly, using the real helpers.
   * The regression: deriving the hold from the VFX's own `elapsedMs` while
   * the hold is what freezes `elapsedMs` deadlocked — at any frame rate
   * above 25fps `deltaMs - HIT_STOP_MS` floors at 0, so `elapsedMs` never
   * moved and the instance never expired.
   */
  function simulateLoopFrames(
    frameCount: number,
    frameDeltaMs: number,
  ): {
    readonly elapsedMs: number;
    readonly expired: boolean;
    readonly frames: number;
    readonly heldFrames: number;
  } {
    let instances = [
      triggerCombatVfxMs("player_hit", "", 200, undefined, undefined, 13),
    ];
    let previousInstances: ReadonlyArray<
      ReturnType<typeof triggerCombatVfxMs>
    > = [];
    let deadlineMs = 0;
    let nowMs = 0;
    let lastMs = 0;
    let heldFrames = 0;

    for (let i = 0; i < frameCount; i++) {
      nowMs += frameDeltaMs;
      const deltaMs = lastMs > 0 ? nowMs - lastMs : frameDeltaMs;
      lastMs = nowMs;

      deadlineMs = hitStopDeadlineFor(
        deadlineMs,
        nowMs,
        instances,
        previousInstances,
      );
      const holding = hitStopActiveAt(deadlineMs, nowMs);
      if (holding) heldFrames += 1;
      const advanceMs = holding ? 0 : deltaMs;
      const next = advanceVfxListBy(instances, advanceMs);
      previousInstances = instances;
      if (next.length === 0) {
        return {
          elapsedMs: instances[0]?.elapsedMs ?? 0,
          expired: true,
          frames: i + 1,
          heldFrames,
        };
      }
      instances = [...next];
    }
    return {
      elapsedMs: instances[0]?.elapsedMs ?? 0,
      expired: false,
      frames: frameCount,
      heldFrames,
    };
  }

  it("advances the player_hit past HIT_STOP_MS within a bounded frame count at 60fps", () => {
    const result = simulateLoopFrames(120, 1000 / 60);
    expect(result.expired).toBe(true);
    expect(result.elapsedMs).toBeGreaterThanOrEqual(HIT_STOP_MS);
    expect(result.frames).toBeLessThanOrEqual(60);
  });

  it("holds for a bounded number of frames, then releases", () => {
    const result = simulateLoopFrames(120, 1000 / 60);
    // The hold is 40ms of wall clock — at 60fps that is at most 3 frames.
    expect(result.heldFrames).toBeGreaterThan(0);
    expect(result.heldFrames).toBeLessThanOrEqual(6);
  });

  it("does not freeze the VFX at 60fps — elapsedMs advances every frame after the hold", () => {
    let instances = [
      triggerCombatVfxMs("player_hit", "", 200, undefined, undefined, 13),
    ];
    let previousInstances: ReadonlyArray<
      ReturnType<typeof triggerCombatVfxMs>
    > = [];
    let deadlineMs = 0;
    let nowMs = 0;
    let lastMs = 0;
    const observed: number[] = [];

    for (let i = 0; i < 12; i++) {
      nowMs += 1000 / 60;
      const deltaMs = lastMs > 0 ? nowMs - lastMs : 1000 / 60;
      lastMs = nowMs;
      deadlineMs = hitStopDeadlineFor(
        deadlineMs,
        nowMs,
        instances,
        previousInstances,
      );
      const holding = hitStopActiveAt(deadlineMs, nowMs);
      previousInstances = instances;
      instances = [...advanceVfxListBy(instances, holding ? 0 : deltaMs)];
      observed.push(instances[0]?.elapsedMs ?? -1);
    }

    // The value must strictly increase once the hold has elapsed.
    const afterHold = observed.slice(6);
    for (let i = 1; i < afterHold.length; i++) {
      expect(afterHold[i]!).toBeGreaterThan(afterHold[i - 1]!);
    }
    expect(observed[observed.length - 1]!).toBeGreaterThan(HIT_STOP_MS);
  });

  it("expires the player_hit within its 200ms lifetime at 60fps", () => {
    const result = simulateLoopFrames(120, 1000 / 60);
    expect(result.expired).toBe(true);
  });

  it("never freezes at any frame rate above 25fps", () => {
    for (const fps of [30, 40, 60, 120, 144]) {
      const result = simulateLoopFrames(300, 1000 / fps);
      expect(result.expired, `frozen at ${fps}fps`).toBe(true);
    }
  });

  it("still expires at very high frame rates", () => {
    const result = simulateLoopFrames(2000, 1000 / 240);
    expect(result.expired).toBe(true);
  });
});
