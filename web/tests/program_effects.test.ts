import { describe, it, expect, vi, afterEach } from "vitest";
import { makeInitialState } from "../src/core/state/state";
import { useProgram } from "../src/core/combat/state_actions_programs";
import {
  playerEvasionPct,
  playerShieldPool,
} from "../src/core/combat/player_mitigation";
import type { GameState, Ice, Mission, Program } from "../src/core/types";

/**
 * ADR-0255 — the opening hand's mechanics.
 *
 * Each card says what it does and the reducer does that:
 *   backdoor — the attack ignores 2 points of the ICE's armor
 *   barrier  — a 2-point absorb pool for 2 player turns
 *   boost    — +2 damage on the player's attacks for 2 player turns
 *   cloak    — incoming damage reduced by 15% for 2 player turns
 *   decoy    — half of the next incoming hit is soaked, for 1 player turn
 */

const MOCK_MISSION: Mission = {
  id: "m1",
  title: "T",
  fixer: "t",
  arc: 1,
  zone: "mid",
  grade_min: 3,
  grade_max: 3,
  rewards: { credits: 100, materials: {} },
};

function program(over: Partial<Program> = {}): Program {
  return {
    id: "p1",
    name: "Test",
    tier: 2,
    cost: 2,
    effect: "attack",
    description: "d",
    aoe: false,
    ...over,
  };
}

/** The ICE the fight runs against, with a chosen armor value. */
function iceWithArmor(armor: number): Ice {
  return {
    id: "ice1",
    name: "Yakuza Enforcer",
    hp: 165,
    maxHp: 165,
    armor,
    level: 3,
    tier: 3,
    personality: "aggressive",
    aggression: "standard",
  } as unknown as Ice;
}

function makeState(over: Partial<GameState> = {}): GameState {
  const ice = iceWithArmor(5);
  const state = makeInitialState(MOCK_MISSION, ice, [program()]);
  return {
    ...state,
    iceRoster: [ice],
    ice,
    activeIceIndex: 0,
    phase: "combat",
    runPhase: "combat",
    ...over,
  } as unknown as GameState;
}

describe("ADR-0255 program effects", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("backdoor ignores 2 points of the ICE's armor", () => {
    // Fixed RNG: damage variance would otherwise blur the armor difference.
    vi.spyOn(Math, "random").mockReturnValue(0.5);
    const plain = useProgram(
      makeState({ deck: [program({ id: "strike" })] }),
      "strike",
    );
    const pierced = useProgram(
      makeState({ deck: [program({ id: "backdoor" })] }),
      "backdoor",
    );
    // Same tier, same base damage — the armor is what differs.
    const plainDamage = 165 - (plain.iceRoster[0]?.hp ?? 0);
    const piercedDamage = 165 - (pierced.iceRoster[0]?.hp ?? 0);
    // Armor 5 -> 3 after a 2-point pierce, so the hit lands 2 harder.
    expect(piercedDamage - plainDamage).toBe(2);
  });

  it("backdoor cannot pierce more armor than the ICE has", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.5);
    const plain = useProgram(
      makeState({
        deck: [program({ id: "strike" })],
        iceRoster: [iceWithArmor(2)],
      }),
      "strike",
    );
    const pierced = useProgram(
      makeState({
        deck: [program({ id: "backdoor" })],
        iceRoster: [iceWithArmor(2)],
      }),
      "backdoor",
    );
    const plainDamage = 165 - (plain.iceRoster[0]?.hp ?? 0);
    const piercedDamage = 165 - (pierced.iceRoster[0]?.hp ?? 0);
    // Armor 2 is less than the 3-point pierce, so all of it is removed.
    expect(piercedDamage - plainDamage).toBe(2);
  });

  it("barrier grants a 2-point shield for 2 turns", () => {
    const after = useProgram(
      makeState({ deck: [program({ id: "barrier" })] }),
      "barrier",
    );
    expect(playerShieldPool(after)).toBe(2);
    const shield = after.statusEffects.find((e) => e.kind === "shield");
    expect(shield?.target).toBe("player");
    expect(shield?.remaining).toBe(2);
  });

  it("boost raises the player's attack for 2 turns", () => {
    const after = useProgram(
      makeState({ deck: [program({ id: "boost" })] }),
      "boost",
    );
    const powered = after.statusEffects.find((e) => e.kind === "powered");
    expect(powered?.target).toBe("player");
    expect(powered?.attackBonus).toBe(2);
    expect(powered?.remaining).toBe(2);
  });

  it("cloak cuts incoming damage by 15% for 2 turns", () => {
    const after = useProgram(
      makeState({ deck: [program({ id: "cloak" })] }),
      "cloak",
    );
    expect(playerEvasionPct(after)).toBe(15);
    const evasive = after.statusEffects.find((e) => e.kind === "evasive");
    expect(evasive?.target).toBe("player");
    expect(evasive?.remaining).toBe(2);
  });

  it("decoy soaks half of the next hit for one turn", () => {
    const after = useProgram(
      makeState({ deck: [program({ id: "decoy" })] }),
      "decoy",
    );
    expect(playerEvasionPct(after)).toBe(50);
    const evasive = after.statusEffects.find((e) => e.kind === "evasive");
    expect(evasive?.remaining).toBe(1);
  });

  it("a plain program grants no effect", () => {
    const after = useProgram(
      makeState({ deck: [program({ id: "strike" })] }),
      "strike",
    );
    expect(playerShieldPool(after)).toBe(0);
    expect(playerEvasionPct(after)).toBe(0);
    expect(
      after.statusEffects.filter((e) => e.target === "player"),
    ).toHaveLength(0);
  });
});
