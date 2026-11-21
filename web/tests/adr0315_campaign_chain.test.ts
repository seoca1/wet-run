/** ADR-0315 slice 2 — the run is a contract of missions, not one.
 *
 * Before this, `missionsCompleted` was hardcoded to 1 and the `liberation`
 * ending (`missionsCompleted >= 3`) could never fire. A contract is the chosen
 * mission plus the rest of its arc, and finishing it is what opens liberation
 * (ADR-0318 puts that branch ahead of wealth).
 *
 * A run without a contract — a test fixture, an older save — must behave
 * exactly as it did. That is the first thing asserted here, because the whole
 * change is opt-in.
 */
import { describe, expect, it } from "vitest";
import { applyAction, makeInitialState, slotToGameState, stateToSaveSlot } from "../src/core/state/state";
import {
  CONTRACT_LENGTH,
  campaignContinues,
  campaignLength,
  contractFor,
} from "../src/core/state/campaign";
import { missionIce } from "../src/core/state/mission_ice";
import { loadIceCatalog, loadMissionsCatalog } from "../src/core/data_loaders";
import { resolveEnding } from "../src/core/combat/ending_resolver";
import missionsData from "../src/data/missions.json" with { type: "json" };
import iceTypesData from "../src/data/ice_types.json" with { type: "json" };
import type { GameState, Ice, Mission, Program } from "../src/core/types";

const MISSIONS = loadMissionsCatalog(missionsData);
const ICE = loadIceCatalog(iceTypesData) as Readonly<Record<string, Ice>>;
const iceFor = (m: Mission): Ice => missionIce(m, ICE);
const byId = (id: string): Mission => {
  const m = MISSIONS.find((x) => x.id === id);
  if (!m) throw new Error(`no mission ${id}`);
  return m;
};

const PROGRAM: Program = {
  id: "strike",
  name: "Strike",
  tier: 1,
  cost: 0,
  effect: "damage",
  description: "",
  aoe: false,
};

/** A run standing on its last node's loot screen: the next ENTER ends it. */
function terminalLoot(campaign?: GameState["campaign"]): GameState {
  const base = makeInitialState(byId("first_jack"), iceFor(byId("first_jack")), [PROGRAM]);
  const boss = base.matrix?.bossNode ?? 0;
  return {
    ...base,
    runPhase: "loot",
    phase: "victory",
    currentNodeIndex: boss,
    ...(campaign !== undefined ? { campaign } : {}),
  };
}

describe("ADR-0315 slice 2 — the contract", () => {
  it("is the chosen mission, then the rest of its arc in grade order", () => {
    const contract = contractFor(byId("first_jack"), MISSIONS, iceFor);
    expect(contract.legs).toHaveLength(CONTRACT_LENGTH);
    expect(contract.legs[0]?.mission.id).toBe("first_jack");
    for (const leg of contract.legs) expect(leg.mission.arc).toBe(1);
    // Grade order: a chain never spikes from the player's pick.
    const grades = contract.legs.map((l) => l.mission.grade_max);
    expect(grades).toEqual([...grades].sort((a, b) => a - b));
  });

  it("wraps so a contract always fills, and never leaves the arc", () => {
    // ice_run is the last arc-1 mission in grade order, so the chain wraps.
    const contract = contractFor(byId("ice_run"), MISSIONS, iceFor);
    expect(contract.legs).toHaveLength(CONTRACT_LENGTH);
    expect(contract.legs[0]?.mission.id).toBe("ice_run");
    for (const leg of contract.legs) expect(leg.mission.arc).toBe(1);
  });

  it("never pulls in Far Grid (a separate universe, ADR-0213)", () => {
    const contract = contractFor(byId("first_jack"), MISSIONS, iceFor);
    for (const leg of contract.legs) {
      expect(leg.mission.source_universe).not.toBe("far-grid");
    }
  });

  it("continues until the last leg, and knows its own length", () => {
    const contract = contractFor(byId("first_jack"), MISSIONS, iceFor);
    expect(campaignLength(contract)).toBe(CONTRACT_LENGTH);
    expect(campaignContinues(contract)).toBe(true);
    expect(
      campaignContinues({ legs: contract.legs, completed: CONTRACT_LENGTH - 1 }),
    ).toBe(false);
    expect(campaignContinues(undefined)).toBe(false);
    expect(campaignLength(undefined)).toBe(0);
  });
});

describe("ADR-0315 slice 2 — the chain", () => {
  it("starts the next leg instead of the ending, carrying credits and the deck", () => {
    const contract = contractFor(byId("first_jack"), MISSIONS, iceFor);
    const start = { ...terminalLoot(contract), player: { ...terminalLoot(contract).player, credits: 1234 } };
    const next = applyAction(start, { type: "confirm" });

    expect(next.runPhase).toBe("matrix");
    expect(next.campaign?.completed).toBe(1);
    expect(next.mission.id).toBe(contract.legs[1]?.mission.id);
    // Credits accumulate — ADR-0314's condition only means something if they do.
    expect(next.player.credits).toBe(1234);
    // HP resets per mission (Q3), and the board is the new mission's.
    expect(next.player.hp).toBe(next.player.maxHp);
    expect(next.turnCount).toBe(0);
    expect(next.endingChoice).toBeNull();
  });

  it("ends the run after the last leg", () => {
    const contract = contractFor(byId("first_jack"), MISSIONS, iceFor);
    const start = terminalLoot({
      legs: contract.legs,
      completed: CONTRACT_LENGTH - 1,
    });
    const next = applyAction(start, { type: "confirm" });
    expect(next.runPhase).toBe("ending");
    expect(next.endingChoice).not.toBeNull();
  });

  it("carries the contract's materials into the next leg (ADR-0338)", () => {
    const contract = contractFor(byId("first_jack"), MISSIONS, iceFor);
    const base = terminalLoot(contract);
    // What leg 1 picked up before the leg boundary.
    const start: GameState = {
      ...base,
      inventory: { ...base.inventory, materials: { data_fragment: 7, ice_shard: 3 } },
    };
    const next = applyAction(start, { type: "confirm" });
    const reward = contract.legs[1]?.mission.rewards.materials ?? {};
    // Nothing evaporates at the boundary; the next leg's reward is added on top.
    expect(next.inventory.materials.data_fragment).toBe(7 + (reward.data_fragment ?? 0));
    expect(next.inventory.materials.ice_shard).toBe(3 + (reward.ice_shard ?? 0));
  });

  it("leaves a run with no contract exactly as it was", () => {
    const next = applyAction(terminalLoot(), { type: "confirm" });
    expect(next.runPhase).toBe("ending");
    expect(next.campaign).toBeUndefined();
  });
});

describe("ADR-0318 — a finished contract outranks wealth", () => {
  const ctx = {
    arc: 1 as const,
    hp: 90,
    maxHp: 100,
    credits: 9999,
    totalDeaths: 0,
    factionScores: {},
    choices: [],
  };

  it("gives liberation to a completed contract even when rich", () => {
    const ending = resolveEnding({ ...ctx, missionsCompleted: 3 });
    expect(ending.category).toBe("liberation");
  });

  it("still gives control to a rich run that did not finish a contract", () => {
    const ending = resolveEnding({ ...ctx, missionsCompleted: 1 });
    expect(ending.category).toBe("control");
  });

  it("keeps sacrifice ahead of both", () => {
    const ending = resolveEnding({ ...ctx, hp: 0, missionsCompleted: 3 });
    expect(ending.category).toBe("sacrifice");
  });
});

describe("ADR-0315 slice 2 — the contract survives a save", () => {
  it("keeps ids only, and rebuilds the legs on restore", () => {
    const contract = contractFor(byId("first_jack"), MISSIONS, iceFor);
    const state = { ...terminalLoot(contract), player: { ...terminalLoot(contract).player, credits: 700 } };
    const slot = stateToSaveSlot(state);
    expect(slot.campaignMissionIds).toEqual(
      contract.legs.map((l) => l.mission.id),
    );
    expect(slot.campaignCompleted).toBe(0);

    const restored = slotToGameState(slot, MISSIONS, { strike: PROGRAM }, state.ice, ICE);
    expect(restored?.campaign?.completed).toBe(0);
    expect(restored?.campaign?.legs.map((l) => l.mission.id)).toEqual(
      contract.legs.map((l) => l.mission.id),
    );
  });

  it("drops a contract whose leg does not match the saved mission", () => {
    const contract = contractFor(byId("first_jack"), MISSIONS, iceFor);
    const slot = {
      ...stateToSaveSlot(terminalLoot(contract)),
      missionId: byId("mollys_market").id,
    };
    const restored = slotToGameState(slot, MISSIONS, { strike: PROGRAM }, terminalLoot(contract).ice, ICE);
    expect(restored?.campaign).toBeUndefined();
  });

  it("restores an older slot (no campaign fields) as a single mission", () => {
    const slot = stateToSaveSlot(terminalLoot());
    expect(slot.campaignMissionIds).toBeUndefined();
    const restored = slotToGameState(slot, MISSIONS, { strike: PROGRAM }, terminalLoot().ice, ICE);
    expect(restored?.campaign).toBeUndefined();
  });
});
