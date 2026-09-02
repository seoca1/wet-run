import { describe, it, expect } from "vitest";
import { 
  import_vfx, 
  import_vfx_ms, 
  pickProgramVfxKind, 
  durationForKind, 
  durationMsForKind 
} from "../src/core/state_helpers.ts";

describe("import_vfx", () => {
  it("creates VFX instance with tick-based duration", () => {
    const vfx = import_vfx("attack", "test", 10);
    expect(vfx.kind).toBe("attack");
    expect(vfx.payload).toBe("test");
    expect(vfx.duration).toBe(10);
    expect(vfx.durationMs).toBe(160);
    expect(vfx.tick).toBe(0);
    expect(vfx.elapsedMs).toBe(0);
  });

  it("includes optional parameters when provided", () => {
    const vfx = import_vfx("pierce", "damage", 5, 1, 3, 42);
    expect(vfx.startRow).toBe(1);
    expect(vfx.targetRow).toBe(3);
    expect(vfx.payloadNum).toBe(42);
  });

  it("clamps negative duration to zero in durationMs", () => {
    const vfx = import_vfx("attack", "", -5);
    expect(vfx.duration).toBe(-5);
    expect(vfx.durationMs).toBe(0);
  });

  it("generates unique IDs for each instance", () => {
    const vfx1 = import_vfx("attack", "", 3);
    const vfx2 = import_vfx("attack", "", 3);
    expect(vfx1.id).not.toBe(vfx2.id);
  });
});

describe("import_vfx_ms", () => {
  it("creates VFX instance with millisecond-based duration", () => {
    const vfx = import_vfx_ms("heavy_attack", "test", 500);
    expect(vfx.kind).toBe("heavy_attack");
    expect(vfx.payload).toBe("test");
    expect(vfx.durationMs).toBe(500);
    expect(vfx.duration).toBe(Math.ceil(500 / 16));
  });

  it("converts milliseconds to ticks correctly", () => {
    const vfx = import_vfx_ms("attack", "", 240);
    expect(vfx.duration).toBe(15);
    expect(vfx.durationMs).toBe(240);
  });

  it("clamps negative duration to zero", () => {
    const vfx = import_vfx_ms("attack", "", -100);
    expect(vfx.durationMs).toBe(0);
    expect(vfx.duration).toBe(0);
  });

  it("includes optional parameters when provided", () => {
    const vfx = import_vfx_ms("multi_hit", "hit", 300, 2, 5, 100);
    expect(vfx.startRow).toBe(2);
    expect(vfx.targetRow).toBe(5);
    expect(vfx.payloadNum).toBe(100);
  });
});

describe("pickProgramVfxKind", () => {
  it("returns detect for noise_attraction effect", () => {
    const program = { tier: 1, effect: "noise_attraction" };
    const kind = pickProgramVfxKind(program, 10);
    expect(kind).toBe("detect");
  });

  it("returns buff for reset_ap effect", () => {
    const program = { tier: 2, effect: "reset_ap" };
    const kind = pickProgramVfxKind(program, 15);
    expect(kind).toBe("buff");
  });

  it("returns pierce for strike role", () => {
    const program = { tier: 3, role: "strike" };
    const kind = pickProgramVfxKind(program, 20);
    expect(kind).toBe("pierce");
  });

  it("returns heavy_attack for burst with damage >= 20", () => {
    const program = { tier: 3, role: "burst" };
    const kind = pickProgramVfxKind(program, 25);
    expect(kind).toBe("heavy_attack");
  });

  it("returns multi_hit for burst with damage >= 10 but < 20", () => {
    const program = { tier: 2, role: "burst" };
    const kind = pickProgramVfxKind(program, 15);
    expect(kind).toBe("multi_hit");
  });

  it("returns attack for burst with damage < 10", () => {
    const program = { tier: 1, role: "burst" };
    const kind = pickProgramVfxKind(program, 8);
    expect(kind).toBe("attack");
  });

  it("returns shield for guard role", () => {
    const program = { tier: 2, role: "guard" };
    const kind = pickProgramVfxKind(program, 5);
    expect(kind).toBe("shield");
  });

  it("returns regen for support role", () => {
    const program = { tier: 1, role: "support" };
    const kind = pickProgramVfxKind(program, 0);
    expect(kind).toBe("regen");
  });

  it("returns attack as default fallback", () => {
    const program = { tier: 1 };
    const kind = pickProgramVfxKind(program, 10);
    expect(kind).toBe("attack");
  });
});

describe("durationForKind", () => {
  it("returns correct duration for attack", () => {
    expect(durationForKind("attack")).toBe(3);
  });

  it("returns correct duration for heavy_attack", () => {
    expect(durationForKind("heavy_attack")).toBe(9);
  });

  it("returns correct duration for pierce", () => {
    expect(durationForKind("pierce")).toBe(4);
  });

  it("returns correct duration for dot", () => {
    expect(durationForKind("dot")).toBe(7);
  });

  it("returns correct duration for victory", () => {
    expect(durationForKind("victory")).toBe(5);
  });

  it("returns correct duration for jackin_glitch", () => {
    expect(durationForKind("jackin_glitch")).toBe(7);
  });

  it("returns correct duration for ice_hit", () => {
    expect(durationForKind("ice_hit")).toBe(2);
  });

  it("returns correct duration for boss_phase_transition", () => {
    expect(durationForKind("boss_phase_transition")).toBe(5);
  });
});

describe("durationMsForKind", () => {
  it("returns correct milliseconds for attack", () => {
    expect(durationMsForKind("attack")).toBe(240);
  });

  it("returns correct milliseconds for heavy_attack", () => {
    expect(durationMsForKind("heavy_attack")).toBe(900);
  });

  it("returns correct milliseconds for pierce", () => {
    expect(durationMsForKind("pierce")).toBe(310);
  });

  it("returns correct milliseconds for dot", () => {
    expect(durationMsForKind("dot")).toBe(550);
  });

  it("returns correct milliseconds for victory", () => {
    expect(durationMsForKind("victory")).toBe(800);
  });

  it("returns correct milliseconds for jackin_glitch", () => {
    expect(durationMsForKind("jackin_glitch")).toBe(500);
  });

  it("returns correct milliseconds for ice_hit", () => {
    expect(durationMsForKind("ice_hit")).toBe(160);
  });

  it("returns correct milliseconds for boss_phase_transition", () => {
    expect(durationMsForKind("boss_phase_transition")).toBe(800);
  });
});
