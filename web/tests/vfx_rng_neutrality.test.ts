/** ADR-0239 — VFX spawns must consume ZERO `Math.random` draws.
 *
 * The balance harness seeds `Math.random` with a PRNG, so a single extra (or
 * missing) draw in the display layer shifts every later crit / proc / skill
 * roll and moves the ADR-0229 grade curve. ADR-0231 / ADR-0232 guarded this by
 * comparing draw counts by hand; this file pins it mechanically.
 *
 * Two layers are pinned:
 *  1. The spawn helpers themselves (`import_vfx`, `import_vfx_ms`) draw 0.
 *  2. A scripted `use_program` that spawns five VFX (program, ice_hit, the
 *     role VFX, dot, critical_hit) consumes exactly the gameplay draws and
 *     nothing more. The pinned count is the gameplay budget only — damage
 *     variance + crit check (`calculateDamage`), the burn / slow status proc
 *     rolls (`rollStatusProc`) and the ICE auto-attack crit roll of the enemy
 *     turn (`rollIceCrit`). Any VFX draw raises it (pre-ADR-0239: 10).
 */
import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { applyStatus } from "../src/core/status";
import { import_vfx, import_vfx_ms } from "../src/core/state/state_helpers";
import type { GameState, Ice, Mission, Program } from "../src/core/types";

/** Run `fn` with `Math.random` replaced by a counting constant stub. */
function countDraws(fn: () => void, value = 0.99): number {
  const original = Math.random;
  let calls = 0;
  Math.random = () => {
    calls += 1;
    return value;
  };
  try {
    fn();
  } finally {
    Math.random = original;
  }
  return calls;
}

const mission: Mission = {
  id: "test",
  title: "T",
  fixer: "x",
  arc: 1,
  zone: "test",
  grade_min: 1,
  grade_max: 1,
  rewards: { credits: 0, materials: {} },
};
const ice: Ice = { id: "ice1", name: "ICE", hp: 500, armor: 0, tier: 1 };
// Tier 3 burst → base damage 15: spawns the role VFX (multi_hit) and, because
// damage >= 10, the `import_vfx_ms` critical_hit flash.
const burst = {
  id: "burst3",
  name: "BURST",
  tier: 3,
  cost: 10,
  effect: "e",
  description: "",
  aoe: false,
  role: "burst",
} as Program;

function combatState(): GameState {
  const base = makeInitialState(mission, ice, [burst]);
  const state: GameState = {
    ...base,
    runPhase: "combat",
    phase: "combat",
    iceRoster: [{ ...ice }],
    activeIceIndex: 0,
    dixieLastAttackMs: Date.now(),
  };
  // A burn on the ICE makes the tick spawn the `dot` VFX as well.
  return applyStatus(state, "ice", "burn", 3, 2);
}

/** Gameplay draws of one non-crit, non-lethal `use_program`: damage variance +
 *  crit check (2) + burn proc + slow proc (2) + ICE auto-attack crit roll (1). */
const USE_PROGRAM_GAMEPLAY_DRAWS = 5;

describe("ADR-0239 VFX spawn RNG neutrality", () => {
  it("import_vfx consumes no Math.random draw", () => {
    const calls = countDraws(() => {
      import_vfx("attack", "", 3);
      import_vfx("victory", "", 5);
      import_vfx("dot", "", 7, undefined, undefined, 4);
    });
    expect(calls).toBe(0);
  });

  it("import_vfx_ms consumes no Math.random draw", () => {
    const calls = countDraws(() => {
      import_vfx_ms("critical_hit", "", 320, undefined, undefined, 15);
      import_vfx_ms("boss_phase_transition", "", 800, undefined, undefined, 2);
    });
    expect(calls).toBe(0);
  });

  it("use_program spawning 5 VFX consumes only the gameplay draw budget", () => {
    const state = combatState();
    let next: GameState = state;
    const calls = countDraws(() => {
      next = applyAction(state, { type: "use_program", programId: "burst3" });
    });
    // Guard the scenario: the five spawns this test relies on really happened.
    const kinds = next.vfxInstances.map((v) => v.kind);
    expect(kinds).toEqual(
      expect.arrayContaining(["multi_hit", "ice_hit", "dot", "critical_hit"]),
    );
    expect(kinds.filter((k) => k === "multi_hit")).toHaveLength(2);
    expect(calls).toBe(USE_PROGRAM_GAMEPLAY_DRAWS);
  });

  it("identical spawns share a content-derived id (identity key only)", () => {
    expect(import_vfx("ice_hit", "15", 2).id).toBe(
      import_vfx("ice_hit", "15", 2).id,
    );
    expect(import_vfx_ms("critical_hit", "", 320).id).toBe(
      import_vfx_ms("critical_hit", "", 320).id,
    );
    expect(import_vfx("ice_hit", "15", 2).id).not.toBe(
      import_vfx("ice_hit", "16", 2).id,
    );
  });
});
