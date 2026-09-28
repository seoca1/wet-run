/** Fuzz test: 1000 seeded combat simulations
 *  Verifies no NaN HP, no negative HP, alarm bounds, deck underflow
 *  ADR-0210 Tier 6 invariant test
 */
import { describe, it, expect } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state";
import missionsData from "../src/data/missions.json";
import iceTypesData from "../src/data/ice_types.json";
import programsData from "../src/data/programs.json";
import type { Program, Ice } from "../src/core/types";

function loadDeck(
  programs: Readonly<Record<string, Program>>,
  count = 5,
): ReadonlyArray<Program> {
  const ids = Object.keys(programs).sort().slice(0, count);
  return ids
    .map((id) => {
      const p = programs[id];
      if (!p) return undefined;
      const apCost = (p as { ap_cost?: number }).ap_cost;
      return {
        ...p,
        id,
        ...(apCost !== undefined && p.cost === undefined ? { cost: apCost } : {}),
      } as Program;
    })
    .filter((p): p is Program => p !== undefined);
}

// Deterministic PRNG for reproducibility (LCG)
class SeededRNG {
  private state: number;
  constructor(seed: number) { this.state = seed >>> 0; }
  next(): number {
    this.state = (this.state * 1664525 + 1013904223) >>> 0;
    return this.state / 0x100000000;
  }
  nextInt(max: number): number {
    return Math.floor(this.next() * max);
  }
  choice<T>(arr: readonly T[]): T {
    return arr[this.nextInt(arr.length)];
  }
}

describe("Fuzz: 1000 seeded combat simulations", () => {
  const mission = Object.values(missionsData)[0]!;
  const iceTypes = iceTypesData as unknown as Record<string, Ice>;
  const programs = programsData as unknown as Record<string, Program>;
  const ice = Object.values(iceTypes)[0]!;
  const baseDeck = loadDeck(programs, 5);

  const ITERATIONS = 1000;
  const SEED = 0xDEADBEEF;

  it(`runs ${ITERATIONS} combat simulations without invariant violations`, () => {
    const rng = new SeededRNG(SEED);
    let violations = 0;
    const violationDetails: string[] = [];

    for (let i = 0; i < ITERATIONS; i++) {
      // Randomize initial state slightly
      const deck = baseDeck.map(p => ({ ...p }));
      // Shuffle deck using seeded RNG
      for (let j = deck.length - 1; j > 0; j--) {
        const k = rng.nextInt(j + 1);
        [deck[j], deck[k]] = [deck[k], deck[j]];
      }

      let state = makeInitialState(mission as any, ice as any, deck);
      state = { ...state, currentNodeIndex: 1 };
      state = applyAction(state, { type: "confirm" });
      state = applyAction(state, { type: "confirm" });
      expect(state.runPhase).toBe("combat");

      let combatSteps = 0;
      const maxCombatSteps = 50;

      while (state.runPhase === "combat" && combatSteps < maxCombatSteps) {
        combatSteps++;

        // Invariant: player HP must be finite and >= 0
        if (!Number.isFinite(state.player.hp) || state.player.hp < 0) {
          violations++;
          violationDetails.push(`Iter ${i}: NaN/negative HP = ${state.player.hp}`);
          break;
        }

        // Invariant: alarm must be 0..100
        if (state.player.alarm < 0 || state.player.alarm > 100) {
          violations++;
          violationDetails.push(`Iter ${i}: alarm out of bounds = ${state.player.alarm}`);
          break;
        }

        // Invariant: deck/discard/drawPile sizes must be consistent (deck = hand in GameState)
        const totalCards = state.deck.length + (state.discardPile?.length ?? 0) + (state.drawPile?.length ?? 0);
        if (totalCards > 5) {
          violations++;
          violationDetails.push(`Iter ${i}: card count > 5 (${totalCards})`);
          break;
        }

        // Choose action: prefer use_program, occasionally select_program
        const actions = ["use_program", "select_program"];
        const action = rng.choice(actions);

        if (action === "use_program" && state.deck.length > 0) {
          const prog = state.deck[rng.nextInt(state.deck.length)];
          state = applyAction(state, { type: "use_program", programId: prog.id });
        } else if (action === "select_program" && state.deck.length > 0) {
          const handIndex = rng.nextInt(state.deck.length);
          state = applyAction(state, { type: "select_program", handIndex });
        } else {
          // Skip invalid action
          continue;
        }

        // Early exit if combat ended
        if (state.runPhase !== "combat") break;
      }

      // Post-combat invariants
      if (!Number.isFinite(state.player.hp) || state.player.hp < 0) {
        violations++;
        violationDetails.push(`Iter ${i}: final NaN/negative HP`);
      }
      if (state.player.alarm < 0 || state.player.alarm > 100) {
        violations++;
        violationDetails.push(`Iter ${i}: final alarm out of bounds`);
      }
    }

    // Report
    if (violations > 0) {
      console.error(`FUZZ VIOLATIONS: ${violations}/${ITERATIONS}`);
      violationDetails.slice(0, 10).forEach(d => console.error(d));
    }
    expect(violations).toBe(0);
  });

  it("deterministic: same action sequence on same mission/ice yields same HP", () => {
    // Use a fixed mission seed to ensure deterministic matrix
    const fixedMission = { ...mission, matrix_seed: 12345, seed: 12345, grade: 1 };
    const ice = Object.values(iceTypes)[0]!;
    const deck = loadDeck(programs, 5);

    const runCombat = () => {
      let state = makeInitialState(fixedMission as any, ice as any, deck);
      state = { ...state, currentNodeIndex: 1 };
      state = applyAction(state, { type: "confirm" });
      state = applyAction(state, { type: "confirm" });

      let steps = 0;
      while (state.runPhase === "combat" && steps < 20) {
        if (state.deck.length === 0) break;
        const prog = state.deck[0];
        state = applyAction(state, { type: "use_program", programId: prog.id });
        steps++;
      }
      return { hp: state.player.hp, alarm: state.player.alarm, phase: state.runPhase, steps };
    };

    const r1 = runCombat();
    const r2 = runCombat();
    // Same fixed mission seed + same action sequence = identical results
    expect(r1).toEqual(r2);
  });
});
