/** ms-precision timing tests (Tier 7).
 *
 * Verifies the advanceVfxBy / triggerCombatVfxMs APIs that replace the
 * legacy tick-based advancement. Backward-compat with the existing
 * duration field is also verified (legacy tick-based instances still
 * advance correctly when deltaMs=WEB_TICK_MS).
 */
import { describe, it, expect } from "vitest";
import {
  triggerCombatVfx,
  triggerCombatVfxMs,
  advanceVfxBy,
  advanceVfxListBy,
  tickCombatVfx,
  tickCombatVfxList,
  WEB_TICK_MS,
} from "../src/renderer/combat_vfx.js";

describe("triggerCombatVfxMs (canonical ms-precision spawn)", () => {
  it("creates instance with durationMs set and tick duration derived", () => {
    const inst = triggerCombatVfxMs("attack", "test", 240);
    expect(inst.durationMs).toBe(240);
    expect(inst.duration).toBe(15); // ceil(240 / 16)
    expect(inst.elapsedMs).toBe(0);
    expect(inst.tick).toBe(0);
  });

  it("clamps negative ms to 0", () => {
    const inst = triggerCombatVfxMs("attack", "", -10);
    expect(inst.durationMs).toBe(0);
    expect(inst.duration).toBe(0);
  });
});

describe("advanceVfxBy (ms-precision advance)", () => {
  it("increments elapsedMs by deltaMs", () => {
    const inst = triggerCombatVfxMs("attack", "", 240);
    const next = advanceVfxBy(inst, 50);
    expect(next?.elapsedMs).toBe(50);
    expect(next?.tick).toBe(3); // floor(50 / 16)
  });

  it("returns null when elapsedMs exceeds durationMs", () => {
    const inst = triggerCombatVfxMs("attack", "", 100);
    const next = advanceVfxBy(inst, 120);
    expect(next).toBeNull();
  });

  it("preserves payload + kind across advance", () => {
    const inst = triggerCombatVfxMs("attack", "strike", 100);
    const next = advanceVfxBy(inst, 30);
    expect(next?.kind).toBe("attack");
    expect(next?.payload).toBe("strike");
  });

  it("ignores negative deltaMs (returns instance unchanged)", () => {
    const inst = triggerCombatVfxMs("attack", "", 100);
    const next = advanceVfxBy(inst, -50);
    expect(next).toBe(inst);
  });

  it("supports sub-tick precision (5ms advance)", () => {
    const inst = triggerCombatVfxMs("attack", "", 100);
    const next = advanceVfxBy(inst, 5);
    // 5ms < 16ms (one tick) → tick stays at 0
    expect(next?.tick).toBe(0);
    expect(next?.elapsedMs).toBe(5);
  });

  it("rolls tick at exactly WEB_TICK_MS boundary", () => {
    const inst = triggerCombatVfxMs("attack", "", 100);
    const next = advanceVfxBy(inst, WEB_TICK_MS);
    expect(next?.tick).toBe(1);
  });

  it("rolls tick at fractional WEB_TICK_MS boundary (floor semantics)", () => {
    const inst = triggerCombatVfxMs("attack", "", 100);
    const next = advanceVfxBy(inst, WEB_TICK_MS + 0.9);
    // floor(16.9 / 16) = 1
    expect(next?.tick).toBe(1);
  });
});

describe("advanceVfxListBy (batch advance)", () => {
  it("removes expired VFX from list", () => {
    const vfx1 = triggerCombatVfxMs("attack", "", 50);
    const vfx2 = triggerCombatVfxMs("attack", "", 500);
    const vfx3 = triggerCombatVfxMs("attack", "", 200);
    const ticked = advanceVfxListBy([vfx1, vfx2, vfx3], 100);
    // vfx1 (50ms) expired after 100ms; vfx2 (500ms) and vfx3 (200ms) survive
    expect(ticked.length).toBe(2);
    expect(ticked.map((v) => v.id)).toEqual([vfx2.id, vfx3.id]);
  });

  it("handles empty list", () => {
    expect(advanceVfxListBy([], 100)).toEqual([]);
  });
});

describe("backward compatibility (Tier 7 dual-path)", () => {
  it("tickCombatVfx still works (legacy tick path)", () => {
    const inst = triggerCombatVfx("attack", "test", 5);
    const next = tickCombatVfx(inst);
    expect(next?.tick).toBe(1);
    expect(next?.elapsedMs).toBe(WEB_TICK_MS);
  });

  it("legacy instances expire via derived durationMs (proportional to ticks)", () => {
    // Spawn via triggerCombatVfx (tick-only API): duration=3 → durationMs=48.
    const inst = triggerCombatVfx("attack", "", 3);
    expect(inst.durationMs).toBe(48); // derived from tick duration * WEB_TICK_MS
    const next1 = advanceVfxBy(inst, WEB_TICK_MS);
    expect(next1?.tick).toBe(1);
    const next2 = advanceVfxBy(next1!, WEB_TICK_MS);
    expect(next2?.tick).toBe(2);
    // At 3rd advance, elapsedMs = 48 which equals durationMs → expiry fires.
    const next3 = advanceVfxBy(next2!, WEB_TICK_MS);
    expect(next3).toBeNull();
  });

  it("tickCombatVfxList keeps legacy semantics", () => {
    const vfx1 = triggerCombatVfx("attack", "", 1);
    const vfx2 = triggerCombatVfx("attack", "", 10);
    const ticked = tickCombatVfxList([vfx1, vfx2]);
    expect(ticked.length).toBe(1);
    expect(ticked[0]?.id).toBe(vfx2.id);
  });

  it("ms-precision spawns expire at durationMs (not duration)", () => {
    // spawn with durationMs=33 (just over 2 ticks)
    const inst = triggerCombatVfxMs("attack", "", 33);
    // duration = ceil(33/16) = 3 ticks, durationMs = 33
    const next1 = advanceVfxBy(inst, 16); // tick=1, elapsedMs=16
    expect(next1).not.toBeNull();
    const next2 = advanceVfxBy(next1!, 16); // tick=2, elapsedMs=32
    expect(next2).not.toBeNull();
    const next3 = advanceVfxBy(next2!, 2);  // tick=2 (still), elapsedMs=34
    expect(next3).toBeNull(); // ms-precise expiry fires at 34 > 33
  });
});

describe("WEB_TICK_MS constant", () => {
  it("is 16ms (60fps)", () => {
    expect(WEB_TICK_MS).toBe(16);
  });
});
