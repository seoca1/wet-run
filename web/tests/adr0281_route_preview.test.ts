/**
 * ADR-0281 — the route card prices the run's shape.
 *
 * The matrix always offered a real choice: in `first_jack` the start branches to
 * `0 -> 2 -> 5` (boss only) and `0 -> 1 -> 3 -> 5` (through the encounter at node
 * 1). Which you take decides how long the mission is, which decides how much the
 * deck grows and how likely the run is to finish. Measured with `npm run
 * survival --route long|short`, that choice is worth up to 25pp at grade 4.
 */
import { describe, expect, it } from "vitest";
import {
  fewestFightsNextHop,
  routePreview,
  routePreviewLine,
} from "../src/core/dungeon/route_preview";
import type { Matrix, MatrixNode } from "../src/core/types";

function node(
  id: number,
  adjacent: readonly number[],
  iceIds: readonly string[] = [],
  credits = 0,
): MatrixNode {
  return {
    id,
    zone: "mid",
    iceIds,
    iceHp: [],
    reward: { credits },
    isBoss: false,
    adjacent,
  };
}

/** Mirrors `first_jack`: the start branches to an ICE node (1) and to an empty
 * node (2) that reaches the boss directly, so the encounter is optional.
 * `id === index`, as `dungeonToMatrix` builds it. */
function branching(): Matrix {
  return {
    startNode: 0,
    bossNode: 5,
    grade: 3,
    nodes: [
      node(0, [1, 2]),
      node(1, [0, 3], ["wisp"], 75),
      node(2, [0, 4, 5]),
      node(3, [1, 5]),
      node(4, [2]),
      { ...node(5, [2, 3], ["wintermute"], 175), isBoss: true },
    ],
  };
}

describe("ADR-0281 · routePreview", () => {
  it("separates the shortest line from what is still on offer", () => {
    // Given: the branching graph, nothing resolved.
    const preview = routePreview(branching(), [], [], 2);

    // Then: the boss is one fight away (node 2 is empty), but two are available.
    expect(preview.fightsToBoss).toBe(1);
    expect(preview.fightsAvailable).toBe(2);
    expect(preview.creditsAvailable).toBe(250);
    expect(preview.destinationIsBoss).toBe(false);
  });

  it("counts the encounter when the route goes through it", () => {
    // Given: the route that lands on the ICE node.
    const preview = routePreview(branching(), [], [], 1);

    // Then: arriving at node 1 means fighting the wisp, then the boss.
    expect(preview.fightsToBoss).toBe(2);
    expect(preview.fightsAvailable).toBe(2);
  });

  it("drops a resolved encounter from the count", () => {
    // Given: the wisp already cleared.
    const preview = routePreview(branching(), [1], [], 1);

    // Then: only the boss is left to fight (the wisp is cleared).
    expect(preview.fightsToBoss).toBe(1);
    expect(preview.fightsAvailable).toBe(1);
    expect(preview.creditsAvailable).toBe(175);
  });

  it("drops a bypassed encounter too", () => {
    // Given: the wisp walked past.
    const preview = routePreview(branching(), [], [1], 0);

    // Then
    expect(preview.fightsAvailable).toBe(1);
  });

  it("reports a clear route when nothing is left", () => {
    // Given: everything resolved.
    const preview = routePreview(branching(), [1, 5], [], 2);

    // Then
    expect(preview.fightsAvailable).toBe(0);
    expect(routePreviewLine(preview)).toBe("route: clear — no ICE left");
  });

  it("fits the matrix card (36 columns)", () => {
    // Given / When: the branching case, which is the longest wording.
    const line = routePreviewLine(routePreview(branching(), [], [], 2));

    // Then
    expect(line.length).toBeLessThanOrEqual(36);
  });
});

describe("ADR-0281 · fewestFightsNextHop", () => {
  it("picks the hop that skips the encounter", () => {
    // Given / When: from the start, the empty node is one fight cheaper.
    const hop = fewestFightsNextHop(branching(), [], [], 0);

    // Then
    expect(hop).toBe(2);
  });

  it("walks toward the boss once the short line is taken", () => {
    // Given / When
    const hop = fewestFightsNextHop(branching(), [], [], 2);

    // Then
    expect(hop).toBe(5);
  });

  it("returns null at the boss", () => {
    expect(fewestFightsNextHop(branching(), [], [], 5)).toBeNull();
  });
});
