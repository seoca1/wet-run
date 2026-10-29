/** P5 — combat SFX layering (unit tests).
 *
 * `SFX_IDS.DAMAGE` / `SFX_IDS.ATTACK` / `SFX_IDS.ICE_BREAK` are defined in
 * `src/audio/manager.ts` and their WAV files exist under
 * `web/public/sounds/sfx/`, but nothing ever played them (the "built but
 * unwired" class the proposal calls out as U13).
 *
 * The layering decision is a PURE function so it can be unit-tested without
 * an AudioContext: it maps a state transition (previous → next) to the list
 * of SFX ids that should sound.
 */
import { describe, it, expect } from "vitest";
import { pickCombatSfxLayers } from "../src/core/combat_sfx.ts";
import { SFX_IDS } from "../src/audio/manager.ts";
import type { GameState } from "../src/core/types.ts";
import { makeInitialState } from "../src/core/state.ts";

const mockMission = {
  id: "test",
  title: "T",
  fixer: "x",
  arc: 1,
  zone: "test",
  grade_min: 1,
  grade_max: 1,
  rewards: { credits: 0, materials: {} },
} as import("../src/core/types.ts").Mission;

const mockIce: import("../src/core/types.ts").Ice = {
  id: "ice1",
  name: "ICE",
  hp: 100,
  armor: 0,
  tier: 1,
};

function combatState(playerHp = 100, iceHp = 100): GameState {
  const base = makeInitialState(mockMission, mockIce, []);
  return {
    ...base,
    runPhase: "combat",
    phase: "combat",
    player: { ...base.player, hp: playerHp },
    iceRoster: [{ ...mockIce, hp: iceHp }],
    activeIceIndex: 0,
  };
}

describe("P5 pickCombatSfxLayers — player takes damage", () => {
  it("plays DAMAGE when the player's HP drops", () => {
    const layers = pickCombatSfxLayers(combatState(100), combatState(70));
    expect(layers).toContain(SFX_IDS.DAMAGE);
  });

  it("plays exactly one DAMAGE per HP drop", () => {
    const layers = pickCombatSfxLayers(combatState(100), combatState(70));
    expect(layers.filter((id) => id === SFX_IDS.DAMAGE)).toHaveLength(1);
  });

  it("does not play DAMAGE when the player's HP is unchanged", () => {
    const layers = pickCombatSfxLayers(combatState(100), combatState(100));
    expect(layers).not.toContain(SFX_IDS.DAMAGE);
  });

  it("does not play DAMAGE when the player's HP goes up", () => {
    const layers = pickCombatSfxLayers(combatState(70), combatState(100));
    expect(layers).not.toContain(SFX_IDS.DAMAGE);
  });

  it("does not play DAMAGE outside the combat phase", () => {
    const before = { ...combatState(100), phase: "approach" as const };
    const after = { ...combatState(70), phase: "approach" as const };
    expect(pickCombatSfxLayers(before, after)).not.toContain(SFX_IDS.DAMAGE);
  });
});

describe("P5 pickCombatSfxLayers — ICE takes damage", () => {
  it("plays ATTACK when the ICE's HP drops", () => {
    const layers = pickCombatSfxLayers(combatState(100, 100), combatState(100, 70));
    expect(layers).toContain(SFX_IDS.ATTACK);
  });

  it("layers ATTACK on top of COMBAT_HIT (two sounds, one impact)", () => {
    const layers = pickCombatSfxLayers(combatState(100, 100), combatState(100, 70));
    expect(layers).toContain(SFX_IDS.COMBAT_HIT);
    expect(layers).toContain(SFX_IDS.ATTACK);
  });

  it("plays exactly one ATTACK per ICE HP drop", () => {
    const layers = pickCombatSfxLayers(combatState(100, 100), combatState(100, 70));
    expect(layers.filter((id) => id === SFX_IDS.ATTACK)).toHaveLength(1);
  });

  it("does not play ATTACK when the ICE's HP is unchanged", () => {
    const layers = pickCombatSfxLayers(combatState(100, 100), combatState(100, 100));
    expect(layers).not.toContain(SFX_IDS.ATTACK);
  });
});

describe("P5 pickCombatSfxLayers — ICE defeated", () => {
  it("plays ICE_BREAK when the ICE's HP reaches 0", () => {
    const layers = pickCombatSfxLayers(combatState(100, 30), combatState(100, 0));
    expect(layers).toContain(SFX_IDS.ICE_BREAK);
  });

  it("does not play ICE_BREAK when the ICE survives", () => {
    const layers = pickCombatSfxLayers(combatState(100, 100), combatState(100, 30));
    expect(layers).not.toContain(SFX_IDS.ICE_BREAK);
  });
});

describe("P5 pickCombatSfxLayers — layering discipline", () => {
  it("never plays the same id twice in one transition", () => {
    const layers = pickCombatSfxLayers(combatState(100, 100), combatState(70, 0));
    expect(new Set(layers).size).toBe(layers.length);
  });

  it("returns an empty list for a no-op transition", () => {
    expect(pickCombatSfxLayers(combatState(100, 100), combatState(100, 100))).toEqual(
      [],
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
      pickCombatSfxLayers(combatState(100, 100), combatState(70, 0));
    } finally {
      Math.random = original;
    }
    expect(calls).toBe(0);
  });
});

describe("P5 SFX asset presence", () => {
  it("has the three unwired SFX files on disk", async () => {
    const { readFileSync } = await import("fs");
    const { join } = await import("path");
    const dir = join(import.meta.dirname, "../public/sounds/sfx");
    for (const id of [SFX_IDS.DAMAGE, SFX_IDS.ATTACK, SFX_IDS.ICE_BREAK]) {
      const file = join(dir, id.replace("sounds/sfx/", ""));
      const bytes = readFileSync(file);
      expect(bytes.length).toBeGreaterThan(0);
      // RIFF header check — the file is a real WAV.
      expect(bytes.subarray(0, 4).toString("ascii")).toBe("RIFF");
    }
  });
});
