/** Combat grid integration — per-target status glyph placement (proposal P14).
 *
 * `renderGrid` used to live inside `main.ts` (untestable: the module
 * self-boots a canvas). It now lives in `renderer/combat_grid.ts` so the
 * status placement can be asserted on the real grid.
 */
import { describe, it, expect } from "vitest";
import { renderGrid } from "../src/renderer/combat_grid.ts";
import { groupStatusByTarget } from "../src/renderer/status_hud.ts";
import { makeInitialState } from "../src/core/state.ts";
import type { GameState, Ice, Mission, Program } from "../src/core/types.ts";

const MOCK_MISSION: Mission = {
  id: "test",
  title: "Test",
  fixer: "test",
  arc: 1,
  zone: "test",
  grade_min: 1,
  grade_max: 1,
  rewards: { credits: 10, materials: {} },
};

const MOCK_PROGRAM: Program = {
  id: "p1",
  name: "Atk",
  tier: 1,
  cost: 0,
  effect: "damage",
  description: "test",
  aoe: false,
};

function makeIce(name: string): Ice {
  return {
    id: name,
    name,
    tier: 2,
    hp: 50,
    maxHp: 50,
    armor: 0,
    personality: "aggressive",
    aggression: "standard",
  };
}

function makeState(overrides: Partial<GameState> = {}): GameState {
  const ice = makeIce("Caster");
  const state = makeInitialState(MOCK_MISSION, ice, [MOCK_PROGRAM]);
  return {
    ...state,
    iceRoster: [ice],
    activeIceIndex: 0,
    phase: "combat",
    runPhase: "combat",
    ...overrides,
  };
}

function rowText(grid: ReturnType<typeof renderGrid>, row: number): string {
  let out = "";
  for (let x = 0; x < grid.width; x++) {
    out += grid.cells[row]?.[x]?.char ?? " ";
  }
  return out;
}

describe("combat grid status glyph placement (P14)", () => {
  it("draws the player's own effect on the player HP row", () => {
    const state = makeState({
      statusEffects: [
        {
          kind: "burn",
          remaining: 2,
          magnitude: 3,
          target: "player",
        },
      ],
    });

    const grid = renderGrid(state, null, null, [], 80, 50);
    const groups = groupStatusByTarget(state.statusEffects, state.activeIceIndex);
    const withStatus = renderGrid(state, null, null, groups, 80, 50);

    expect(rowText(grid, 5)).not.toContain("[B2]");
    expect(rowText(withStatus, 5)).toContain("[B2]");
  });

  it("draws the active ICE's effect on the ICE name row", () => {
    const state = makeState({
      statusEffects: [
        {
          kind: "shield",
          remaining: 3,
          magnitude: 20,
          target: "ice",
          iceIndex: 0,
          tickSource: "enemy",
        },
      ],
    });

    const groups = groupStatusByTarget(state.statusEffects, state.activeIceIndex);
    const grid = renderGrid(state, null, null, groups, 80, 50);

    const rosterRow = Math.floor(50 * 0.44);
    expect(rowText(grid, rosterRow)).toContain("[D3]");
  });

  it("keeps the player's glyph and the ICE's glyph on separate rows (P14)", () => {
    const state = makeState({
      statusEffects: [
        {
          kind: "burn",
          remaining: 2,
          magnitude: 3,
          target: "player",
        },
        {
          kind: "shield",
          remaining: 3,
          magnitude: 20,
          target: "ice",
          iceIndex: 0,
          tickSource: "enemy",
        },
      ],
    });

    const groups = groupStatusByTarget(state.statusEffects, state.activeIceIndex);
    const grid = renderGrid(state, null, null, groups, 80, 50);

    const rosterRow = Math.floor(50 * 0.44);
    expect(rowText(grid, 5)).toContain("[B2]");
    expect(rowText(grid, 5)).not.toContain("[D3]");
    expect(rowText(grid, rosterRow)).toContain("[D3]");
    expect(rowText(grid, rosterRow)).not.toContain("[B2]");
  });

  it("shows a non-target ICE's effect on that ICE's own row", () => {
    const second = makeIce("Wraith");
    const state = makeState({
      iceRoster: [makeIce("Caster"), second],
      activeIceIndex: 0,
      statusEffects: [
        {
          kind: "regen",
          remaining: 4,
          magnitude: 4,
          target: "ice",
          iceIndex: 1,
          tickSource: "enemy",
          healPerTick: 4,
        },
      ],
    });

    const groups = groupStatusByTarget(state.statusEffects, state.activeIceIndex);
    const grid = renderGrid(state, null, null, groups, 80, 50);

    const firstRow = Math.floor(50 * 0.44);
    const secondRow = firstRow + 3;
    expect(rowText(grid, secondRow)).toContain("[R4]");
    expect(rowText(grid, firstRow)).not.toContain("[R4]");
  });

  it("does not overflow a narrow 40-column layout", () => {
    const state = makeState({
      statusEffects: [
        {
          kind: "burn",
          remaining: 2,
          magnitude: 3,
          target: "player",
        },
        {
          kind: "shield",
          remaining: 3,
          magnitude: 20,
          target: "ice",
          iceIndex: 0,
          tickSource: "enemy",
        },
        {
          kind: "powered",
          remaining: 2,
          magnitude: 6,
          target: "ice",
          iceIndex: 0,
          tickSource: "enemy",
        },
      ],
    });

    const groups = groupStatusByTarget(state.statusEffects, state.activeIceIndex);
    const grid = renderGrid(state, null, null, groups, 40, 60);

    expect(grid.width).toBe(40);
    for (const row of [5, Math.floor(60 * 0.44)]) {
      expect(rowText(grid, row).length).toBeLessThanOrEqual(40);
    }
  });
});
