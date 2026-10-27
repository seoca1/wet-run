/** Regression tests for graph-directed matrix navigation.
 *
 * Defect #3: the matrix walk could never reach the boss. The reducer
 * followed `adjacent[0]` for every forward move, which in all 53 missions
 * degenerates into the 2-cycle `0 ↔ 1` — the walk visited 2 of up to 28
 * nodes and no mission was completable.
 *
 * These tests pin the replacement contract: BFS over `MatrixNode.adjacent`
 * picks the neighbour on a shortest path to the objective, so repeatedly
 * pressing "forward" always terminates at the boss.
 */
import { describe, expect, it } from "vitest";

import { loadMissionsCatalog } from "../src/core/data_loaders";
import { generateProceduralMatrix } from "../src/core/matrix";
import {
  NO_HOP,
  nextHopToward,
  pathLengthBetween,
} from "../src/core/matrix_navigation";
import { applyAction, makeInitialState } from "../src/core/state";
import type { Ice, Matrix, Mission, Program } from "../src/core/types";

import missionsJson from "../src/data/missions.json";

const missions: ReadonlyArray<Mission> = loadMissionsCatalog(missionsJson);

const stubIce: Ice = {
  id: "watchdog",
  name: "Watchdog",
  hp: 50,
  armor: 0,
  tier: 1,
};

const stubDeck: ReadonlyArray<Program> = [
  {
    id: "strike",
    name: "Strike",
    tier: 1,
    cost: 1,
    effect: "attack",
    description: "Test card",
    aoe: false,
  },
];

/** Build the procedural matrix for a mission, mirroring `makeInitialState`. */
function matrixFor(mission: Mission): Matrix {
  const grade = mission.grade_max ?? mission.grade_min ?? mission.grade ?? 1;
  const seed = mission.seed ?? 42;
  return generateProceduralMatrix(grade, seed, mission.id);
}

/** All nodes reachable from `from`, following `adjacent` edges. */
function reachableFrom(matrix: Matrix, from: number): Set<number> {
  const seen = new Set<number>([from]);
  let frontier: number[] = [from];
  while (frontier.length > 0) {
    const next: number[] = [];
    for (const current of frontier) {
      const node = matrix.nodes[current];
      if (!node) continue;
      for (const neighbour of node.adjacent) {
        if (seen.has(neighbour)) continue;
        seen.add(neighbour);
        next.push(neighbour);
      }
    }
    frontier = next;
  }
  return seen;
}

/** The shortest path from `from` to `target`, as an ordered node list. */
function shortestPath(matrix: Matrix, from: number, target: number): number[] {
  const path: number[] = [from];
  let current = from;
  const guard = matrix.nodes.length + 1;
  for (let step = 0; step < guard; step += 1) {
    if (current === target) return path;
    const hop = nextHopToward(matrix, current, target);
    if (hop === NO_HOP) return [];
    path.push(hop);
    current = hop;
  }
  return [];
}

describe("matrix navigation — mission graph topology", () => {
  it("every mission matrix is fully connected", () => {
    for (const mission of missions) {
      const matrix = matrixFor(mission);
      const reachable = reachableFrom(matrix, matrix.startNode);
      expect(
        reachable.size,
        `mission '${mission.id}': only ${reachable.size} of ${matrix.nodes.length} nodes reachable from startNode`,
      ).toBe(matrix.nodes.length);
    }
  });

  it("every mission has a path from startNode to bossNode", () => {
    for (const mission of missions) {
      const matrix = matrixFor(mission);
      const length = pathLengthBetween(matrix, matrix.startNode, matrix.bossNode);
      expect(
        length,
        `mission '${mission.id}': no path from startNode to bossNode`,
      ).toBeGreaterThan(0);
    }
  });
});

describe("matrix navigation — forward walk reaches the boss", () => {
  it("forward walk reaches the boss from startNode on every mission", () => {
    for (const mission of missions) {
      const matrix = matrixFor(mission);
      let current = matrix.startNode;
      let hops = 0;
      while (current !== matrix.bossNode && hops <= matrix.nodes.length) {
        const hop = nextHopToward(matrix, current, matrix.bossNode);
        expect(
          hop,
          `mission '${mission.id}': no hop from node ${current} toward boss`,
        ).not.toBe(NO_HOP);
        expect(
          matrix.nodes[current]?.adjacent,
          `mission '${mission.id}': hop ${hop} is not adjacent to ${current}`,
        ).toContain(hop);
        current = hop;
        hops += 1;
      }
      expect(
        current,
        `mission '${mission.id}': forward walk did not reach the boss`,
      ).toBe(matrix.bossNode);
      expect(
        hops,
        `mission '${mission.id}': forward walk took ${hops} hops (max ${matrix.nodes.length})`,
      ).toBeLessThanOrEqual(matrix.nodes.length);
    }
  });

  it("the reducer's forward walk reaches the boss from startNode on every mission", () => {
    for (const mission of missions) {
      let state = makeInitialState(mission, stubIce, stubDeck);
      const matrix = state.matrix;
      expect(matrix, `mission '${mission.id}': run must have a matrix`).toBeTruthy();
      if (!matrix) continue;
      expect(
        state.currentNodeIndex,
        `mission '${mission.id}': run must start at startNode`,
      ).toBe(matrix.startNode);
      let current = state.currentNodeIndex;
      let hops = 0;
      while (current !== matrix.bossNode && hops <= matrix.nodes.length) {
        state = applyAction(state, { type: "move_south" });
        expect(
          state.currentNodeIndex,
          `mission '${mission.id}': forward move did not advance at node ${current}`,
        ).not.toBe(current);
        current = state.currentNodeIndex;
        hops += 1;
      }
      expect(
        current,
        `mission '${mission.id}': reducer forward walk did not reach the boss`,
      ).toBe(matrix.bossNode);
      expect(
        hops,
        `mission '${mission.id}': reducer forward walk took ${hops} hops (max ${matrix.nodes.length})`,
      ).toBeLessThanOrEqual(matrix.nodes.length);
    }
  });

  it("backward hop retreats toward the entry along a shortest path", () => {
    for (const mission of missions) {
      const matrix = matrixFor(mission);
      const path = shortestPath(matrix, matrix.startNode, matrix.bossNode);
      expect(
        path.length,
        `mission '${mission.id}': no start→boss path`,
      ).toBeGreaterThan(0);
      for (let i = path.length - 1; i > 0; i -= 1) {
        const forward = path[i - 1] as number;
        const backward = path[i] as number;
        expect(
          nextHopToward(matrix, forward, matrix.bossNode),
          `mission '${mission.id}': forward hop from ${forward} is wrong`,
        ).toBe(backward);
        const retreat = nextHopToward(matrix, backward, matrix.startNode);
        expect(
          retreat,
          `mission '${mission.id}': no backward hop from ${backward}`,
        ).not.toBe(NO_HOP);
        expect(
          matrix.nodes[backward]?.adjacent,
          `mission '${mission.id}': backward hop ${retreat} is not adjacent to ${backward}`,
        ).toContain(retreat);
        expect(
          pathLengthBetween(matrix, retreat, matrix.startNode),
          `mission '${mission.id}': backward hop from ${backward} does not shorten the path to the entry`,
        ).toBeLessThan(
          pathLengthBetween(matrix, backward, matrix.startNode),
        );
      }
    }
  });
});

describe("matrix navigation — determinism", () => {
  it("nextHopToward is deterministic for the same input", () => {
    for (const mission of missions) {
      const matrix = matrixFor(mission);
      for (let from = 0; from < matrix.nodes.length; from += 1) {
        const first = nextHopToward(matrix, from, matrix.bossNode);
        const second = nextHopToward(matrix, from, matrix.bossNode);
        expect(second, `mission '${mission.id}': hop from ${from} drifted`).toBe(first);
      }
    }
  });

  it("nextHopToward agrees across two matrices built from the same seed", () => {
    for (const mission of missions) {
      const a = matrixFor(mission);
      const b = matrixFor(mission);
      expect(a.nodes.length, `mission '${mission.id}': node count drifted`).toBe(
        b.nodes.length,
      );
      for (let from = 0; from < a.nodes.length; from += 1) {
        expect(
          nextHopToward(b, from, b.bossNode),
          `mission '${mission.id}': hop from ${from} differs across identical matrices`,
        ).toBe(nextHopToward(a, from, a.bossNode));
      }
    }
  });
});

describe("matrix navigation — unreachable target contract", () => {
  /** Two disjoint nodes: node 0 has no edge to node 1. */
  const isolatedMatrix: Matrix = {
    nodes: [
      {
        id: 0,
        zone: "surface",
        iceIds: [],
        iceHp: [],
        reward: { credits: 0 },
        isBoss: false,
        adjacent: [],
      },
      {
        id: 1,
        zone: "core-deep",
        iceIds: [],
        iceHp: [],
        reward: { credits: 0 },
        isBoss: true,
        adjacent: [],
      },
    ],
    startNode: 0,
    bossNode: 1,
  };

  it("nextHopToward returns -1 when the target is unreachable", () => {
    expect(nextHopToward(isolatedMatrix, 0, 1)).toBe(NO_HOP);
    expect(pathLengthBetween(isolatedMatrix, 0, 1)).toBe(NO_HOP);
  });

  it("nextHopToward returns -1 when from equals target", () => {
    expect(nextHopToward(isolatedMatrix, 0, 0)).toBe(NO_HOP);
    expect(pathLengthBetween(isolatedMatrix, 0, 0)).toBe(0);
  });

  it("the reducer's forward move is a no-op when the target is unreachable", () => {
    const mission = missions[0] as Mission;
    const state = makeInitialState(mission, stubIce, stubDeck);
    const isolated = { ...state, matrix: isolatedMatrix, currentNodeIndex: 0 };

    const moved = applyAction(isolated, { type: "move_south" });
    expect(moved.currentNodeIndex, "forward move must not change the node").toBe(
      isolated.currentNodeIndex,
    );
    expect(moved.message).toBe("No route to the objective");
    expect(moved.turnCount, "a blocked move must not consume a turn").toBe(
      isolated.turnCount,
    );
  });

  it("the reducer's backward move is a no-op when the entry is unreachable", () => {
    const mission = missions[0] as Mission;
    const state = makeInitialState(mission, stubIce, stubDeck);
    const isolated = { ...state, matrix: isolatedMatrix, currentNodeIndex: 1 };

    const moved = applyAction(isolated, { type: "move_north" });
    expect(moved.currentNodeIndex, "backward move must not change the node").toBe(
      isolated.currentNodeIndex,
    );
    expect(moved.message).toBe("No route back to the entry");
    expect(moved.turnCount, "a blocked move must not consume a turn").toBe(
      isolated.turnCount,
    );
  });
});

describe("ice_x2 mutator — the encounter roster must actually grow", () => {
  /** A node carrying a single ICE id, as the real matrices do. */
  const singleIceNode: Matrix = {
    nodes: [
      {
        id: 0,
        zone: "mid",
        iceIds: ["hellhound"],
        iceHp: [80],
        reward: { credits: 50 },
        isBoss: false,
        adjacent: [],
      },
    ],
    startNode: 0,
    bossNode: 0,
  };

  it("ice_x2 doubles the roster, without the mutator it stays at one ICE", () => {
    const mission = missions[0] as Mission;
    const base = makeInitialState(mission, stubIce, stubDeck);
    const onNode = { ...base, matrix: singleIceNode, currentNodeIndex: 0 };

    const plain = applyAction(onNode, { type: "confirm" });
    expect(
      plain.iceRoster.length,
      "without ice_x2 the roster must equal the node's ICE count",
    ).toBe(1);

    const mutated = {
      ...onNode,
      activeMutators: Object.freeze(["ice_x2"] as const),
    };
    const doubled = applyAction(mutated, { type: "confirm" });
    expect(
      doubled.iceRoster.length,
      "ice_x2 must double the encounter roster",
    ).toBe(2);
    expect(
      new Set(doubled.iceRoster).size,
      "each roster entry must be a distinct object",
    ).toBe(doubled.iceRoster.length);
    expect(doubled.iceRoster.map((ice) => ice.id)).toEqual([
      "hellhound",
      "hellhound",
    ]);
    expect(doubled.iceRoster.map((ice) => ice.hp)).toEqual([80, 80]);
  });
});
