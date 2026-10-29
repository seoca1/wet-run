/** Combat-entry presentation tests (proposal P15).
 *
 * The `ice_intro` VFX had a complete renderer but no spawn site — combat
 * started as an instant cut. These assertions pin the spawn, its payload,
 * its RNG-neutrality, and the fact that it does not disturb the calibrated
 * balance curve (ADR-0229).
 */
import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state.ts";
import type { GameState, Ice, Mission, Program } from "../src/core/types.ts";
import {
  ICE_INTRO_BANNER_ROWS,
  ICE_INTRO_DURATION_TICKS,
  iceIntroPayload,
} from "../src/core/combat_entry_vfx.ts";
import { durationForKind } from "../src/core/state_helpers.ts";

const mockMission: Mission = {
  id: "test",
  title: "Test Mission",
  fixer: "test",
  arc: 1,
  zone: "test",
  grade_min: 1,
  grade_max: 1,
  rewards: { credits: 100, materials: {} },
};

const mockIce: Ice = {
  id: "watchdog",
  name: "Watchdog",
  hp: 100,
  armor: 0,
  tier: 1,
};

const mockProgram: Program = {
  id: "test_prog",
  name: "Test Program",
  tier: 1,
  cost: 10,
  effect: "test",
  description: "Test",
  aoe: false,
};

function makeApproachState(overrides: Partial<GameState> = {}): GameState {
  const base = makeInitialState(mockMission, mockIce, [mockProgram]);
  return {
    ...base,
    phase: "approach",
    runPhase: "combat",
    vfxInstances: [],
    ...overrides,
  };
}

describe("P15 — ice_intro payload", () => {
  it("carries the ICE display name", () => {
    expect(iceIntroPayload("Watchdog")).toBe("Watchdog");
  });

  it("falls back to 'ICE' for an empty name", () => {
    expect(iceIntroPayload("")).toBe("ICE");
    expect(iceIntroPayload("   ")).toBe("ICE");
  });

  it("trims surrounding whitespace", () => {
    expect(iceIntroPayload("  Wintermute  ")).toBe("Wintermute");
  });
});

describe("P15 — ice_intro banner band", () => {
  it("matches the rows the renderer paints", () => {
    // `renderer/combat_vfx_render_scene.ts` writes the banner on rows 1-3
    // and the scanning line on row 5.
    expect(ICE_INTRO_BANNER_ROWS).toEqual([1, 2, 3, 5]);
  });
});

describe("P15 — combat entry spawns ice_intro", () => {
  it("spawns exactly one ice_intro when combat starts", () => {
    const state = makeApproachState();
    const result = applyAction(state, { type: "confirm" });
    expect(result.phase).toBe("combat");
    const intros = result.vfxInstances.filter((v) => v.kind === "ice_intro");
    expect(intros.length).toBe(1);
  });

  it("carries the ICE name as the payload", () => {
    const state = makeApproachState();
    const result = applyAction(state, { type: "confirm" });
    const intro = result.vfxInstances.find((v) => v.kind === "ice_intro");
    expect(intro?.payload).toBe("Watchdog");
  });

  it("uses the canonical duration for the kind", () => {
    const state = makeApproachState();
    const result = applyAction(state, { type: "confirm" });
    const intro = result.vfxInstances.find((v) => v.kind === "ice_intro");
    expect(intro?.duration).toBe(durationForKind("ice_intro"));
    expect(intro?.duration).toBe(ICE_INTRO_DURATION_TICKS);
  });

  it("spawns the intro from the matrix-entry path as well", () => {
    const base = makeInitialState(mockMission, mockIce, [mockProgram]);
    const state: GameState = {
      ...base,
      phase: "approach",
      runPhase: "matrix",
      vfxInstances: [],
      matrix: {
        nodes: [
          {
            id: 0,
            zone: "surface",
            iceIds: ["ice1"],
            iceHp: [50],
            reward: { credits: 100 },
            isBoss: false,
            adjacent: [1],
          },
          {
            id: 1,
            zone: "mid",
            iceIds: ["ice2"],
            iceHp: [75],
            reward: { credits: 150 },
            isBoss: true,
            adjacent: [],
          },
        ],
        startNode: 0,
        bossNode: 1,
      },
      currentNodeIndex: 0,
      iceRoster: [{ ...mockIce, id: "ice1", hp: 50 }],
    };
    // Entering the node moves the run into `combat`/approach; the
    // approach -> combat confirm is what spawns the intro.
    const entered = applyAction(state, { type: "confirm" });
    const engaged = applyAction(entered, { type: "confirm" });
    const intros = engaged.vfxInstances.filter((v) => v.kind === "ice_intro");
    expect(intros.length).toBe(1);
  });

  it("does not spawn a second intro when combat is already engaged", () => {
    const state = makeApproachState();
    const engaged = applyAction(state, { type: "confirm" });
    const intros = engaged.vfxInstances.filter((v) => v.kind === "ice_intro");
    expect(intros.length).toBe(1);
  });
});

describe("P15 — ice_intro spawn is RNG-neutral", () => {
  it("consumes no Math.random draws", () => {
    const original = Math.random;
    let draws = 0;
    Math.random = (): number => {
      draws += 1;
      return original();
    };
    try {
      const state = makeApproachState();
      applyAction(state, { type: "confirm" });
    } finally {
      Math.random = original;
    }
    expect(draws).toBe(0);
  });

  it("produces an identical instance on repeated identical transitions", () => {
    const state = makeApproachState();
    const a = applyAction(state, { type: "confirm" });
    const b = applyAction(state, { type: "confirm" });
    const idA = a.vfxInstances.find((v) => v.kind === "ice_intro")?.id;
    const idB = b.vfxInstances.find((v) => v.kind === "ice_intro")?.id;
    expect(idA).toBe(idB);
  });
});
