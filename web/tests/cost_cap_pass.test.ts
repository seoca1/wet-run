/** ADR-0266 — a COST-capped fight must not freeze.
 *
 * Before this, once every program in hand was over `COST_LIMIT` the turn could
 * never advance: a refused play leaves the hand unchanged, the hand only
 * refills when it is empty, and there was no pass. Measured live: Enter, Space,
 * the digits and the arrows all did nothing, twenty idle seconds brought no
 * enemy attack, and JACK OUT (which loses the run) was the only exit. The soak
 * found it in 16 of 159 cells, every one of them combat at COST 98-100.
 */
import { describe, expect, it } from "vitest";
import { applyAction, makeInitialState } from "../src/core/state/state";
import { everyProgramBlocked } from "../src/core/combat/program_affordance";
import {
  loadIceCatalog,
  loadMissionsCatalog,
  loadProgramsCatalog,
} from "../src/core/data_loaders";
import missionsData from "../src/data/missions.json";
import programsData from "../src/data/programs.json";
import iceTypesData from "../src/data/ice_types.json";
import type { GameState, Ice, Mission, Program } from "../src/core/types";

const MISSIONS = loadMissionsCatalog(missionsData);
const PROGRAMS = loadProgramsCatalog(programsData);
const ICE = loadIceCatalog(iceTypesData);
const MISSION = MISSIONS[0] as Mission;
const BASE_ICE = Object.values(ICE)[0] as Ice;
const DECK: Program[] = Object.keys(PROGRAMS)
  .sort()
  .slice(0, 5)
  .map((id) => ({ ...(PROGRAMS[id] as Program), id }));

/** A live combat state with the hand on the table. */
function fight(overrides: Partial<GameState> = {}): GameState {
  const initial = makeInitialState(MISSION, BASE_ICE, DECK);
  return {
    ...initial,
    runPhase: "combat",
    phase: "combat",
    iceRoster: [BASE_ICE],
    activeIceIndex: 0,
    currentNodeIndex: 0,
    deck: [...DECK],
    drawPile: [],
    discardPile: [],
    ...overrides,
  };
}

/** The same fight with COST at the cap. */
function capped(overrides: Partial<GameState> = {}): GameState {
  const base = fight();
  return { ...base, player: { ...base.player, alarm: 100 }, ...overrides };
}

describe("ADR-0266 — every program blocked is a state, not a dead end", () => {
  it("identifies the cap from the same affordances the hand shows", () => {
    expect(everyProgramBlocked(capped())).toBe(true);
    // One playable card is enough to be a normal turn.
    expect(
      everyProgramBlocked({
        ...fight(),
        player: { ...fight().player, alarm: 0 },
      }),
    ).toBe(false);
    // An empty hand is not "blocked" -- there is nothing to refuse.
    expect(everyProgramBlocked({ ...capped(), deck: [] })).toBe(false);
  });

  it("ENTER passes the turn instead of doing nothing", () => {
    const state = capped();
    const after = applyAction(state, { type: "confirm" });
    expect(after.runPhase).toBe("combat");
    expect(after.phase).toBe("combat");
    expect(after.message).toBe("COST capped — turn passed");
    // A pass is a real turn: the hand recycles rather than sitting on refused
    // cards, and the state is a new frame (the old one is untouched).
    expect(after).not.toBe(state);
    expect(after.deck.length).toBe(state.deck.length);
    expect(state.message).not.toBe(after.message);
  });

  it("does nothing when a program is still playable — no accidental pass", () => {
    const live = fight({ player: { ...fight().player, alarm: 0 } });
    expect(applyAction(live, { type: "confirm" })).toBe(live);
  });

  it("keeps charging nothing: COST stays at the cap across passes", () => {
    let s = capped();
    for (let i = 0; i < 3 && s.runPhase === "combat"; i += 1) {
      const next = applyAction(s, { type: "confirm" });
      if (next.runPhase !== "combat") break;
      expect(next.player.alarm).toBe(100);
      s = next;
    }
  });

  it("a pass is not free: the enemies still get their turn", () => {
    // A runner on 1 HP cannot survive being unable to act: passing is what
    // turns a frozen screen into a decided fight.
    let s = capped({ player: { ...capped().player, hp: 1 } });
    const hpStart = s.player.hp;
    let sawDamage = false;
    for (let i = 0; i < 8 && s.runPhase === "combat"; i += 1) {
      s = applyAction(s, { type: "confirm" });
      if (s.runPhase === "dead") break;
      if (s.player.hp < hpStart) sawDamage = true;
    }
    expect(s.runPhase === "dead" || sawDamage).toBe(true);
    if (s.runPhase === "dead") expect(s.phase).toBe("defeat");
  });
});
