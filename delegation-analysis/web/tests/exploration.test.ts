/** Unit tests for matrix exploration state + fog of war (ADR-0020).
 *
 * Validates the core state machine: visit, probe, visibility classes,
 * adjacency queries. Uses a synthetic linear graph as a fixture so
 * tests are independent of the procedural generator.
 */
import { describe, it, expect } from "vitest";

import {
  ExplorationState,
  graphViewFromEdges,
  isAlwaysVisibleKind,
  eventForRoomType,
  VISIBILITY_ORDER,
  type MatrixGraphView,
  type Visibility,
} from "../src/core/exploration.ts";

// ---------------------------------------------------------------------------
//  Fixtures
// ---------------------------------------------------------------------------

/** Linear 5-node graph: a - b - c - d - e */
const linear: MatrixGraphView = graphViewFromEdges([
  ["a", "b"],
  ["b", "c"],
  ["c", "d"],
  ["d", "e"],
]);

/** Branching graph:   a - b - c
 *                            \
 *                             d
 *                              \
 *                               e  */
const branching: MatrixGraphView = graphViewFromEdges([
  ["a", "b"],
  ["b", "c"],
  ["b", "d"],
  ["d", "e"],
]);

/** Empty graph (no edges, no nodes besides what the user adds). */
const empty: MatrixGraphView = graphViewFromEdges([]);

// ---------------------------------------------------------------------------
//  Construction
// ---------------------------------------------------------------------------

describe("ExplorationState construction", () => {
  it("seeds discovered + path with the current node", () => {
    const s = new ExplorationState("a");
    expect(s.current).toBe("a");
    expect(s.hasDiscovered("a")).toBe(true);
    expect(s.path).toEqual(["a"]);
  });

  it("accepts an empty initial node (no auto-seed)", () => {
    const s = new ExplorationState("");
    expect(s.current).toBe("");
    expect(s.discovered.size).toBe(0);
    expect(s.path).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
//  visit / probe
// ---------------------------------------------------------------------------

describe("visit", () => {
  it("moves to a new node and marks it discovered", () => {
    const s = new ExplorationState("a");
    s.visit("b");
    expect(s.current).toBe("b");
    expect(s.hasDiscovered("a")).toBe(true);
    expect(s.hasDiscovered("b")).toBe(true);
  });

  it("appends to path without duplicating the tail", () => {
    const s = new ExplorationState("a");
    s.visit("b");
    s.visit("c");
    expect(s.path).toEqual(["a", "b", "c"]);
  });

  it("does not duplicate the path when re-visiting current", () => {
    const s = new ExplorationState("a");
    s.visit("a");
    s.visit("a");
    expect(s.path).toEqual(["a"]);
  });
});

describe("probe", () => {
  it("marks a node as scanned", () => {
    const s = new ExplorationState("a");
    s.probe("c");
    expect(s.isScanned("c")).toBe(true);
    expect(s.isScanned("a")).toBe(false);
  });

  it("is independent of visit (can probe undiscovered nodes)", () => {
    const s = new ExplorationState("a");
    s.probe("z");
    expect(s.isScanned("z")).toBe(true);
    expect(s.hasDiscovered("z")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
//  Visibility
// ---------------------------------------------------------------------------

describe("visibility", () => {
  it("returns 'current' for the current node", () => {
    const s = new ExplorationState("b");
    expect(s.visibility(linear, "b")).toBe<Visibility>("current");
  });

  it("returns 'discovered' for nodes the player has visited", () => {
    const s = new ExplorationState("a");
    s.visit("b");
    s.visit("c");
    // 'a' was visited but is no longer current → discovered
    expect(s.hasDiscovered("a")).toBe(true);
    expect(s.visibility(linear, "a")).toBe<Visibility>("discovered");
    // 'b' was also visited but is not current → discovered
    expect(s.visibility(linear, "b")).toBe<Visibility>("discovered");
  });

  it("returns 'adjacent' for neighbors of the current node", () => {
    const s = new ExplorationState("c");
    expect(s.visibility(linear, "b")).toBe<Visibility>("adjacent");
    expect(s.visibility(linear, "d")).toBe<Visibility>("adjacent");
  });

  it("returns 'unknown' for nodes 2+ hops away", () => {
    const s = new ExplorationState("b");
    // c is adjacent, but a and d are not adjacent from b's perspective
    // Wait — a IS adjacent to b in the linear graph. Let me use a
    // 2-hop-away node instead: from b, d is 2 hops away (b->c->d).
    expect(s.visibility(linear, "d")).toBe<Visibility>("unknown");
    expect(s.visibility(linear, "e")).toBe<Visibility>("unknown");
  });

  it("isVisible is false for unknown nodes and true for everything else", () => {
    const s = new ExplorationState("b");
    expect(s.isVisible(linear, "a")).toBe(true); // adjacent
    expect(s.isVisible(linear, "d")).toBe(false); // unknown
  });

  it("works on branching graphs", () => {
    const s = new ExplorationState("b");
    expect(s.visibility(branching, "a")).toBe<Visibility>("adjacent");
    expect(s.visibility(branching, "c")).toBe<Visibility>("adjacent");
    expect(s.visibility(branching, "d")).toBe<Visibility>("adjacent");
    expect(s.visibility(branching, "e")).toBe<Visibility>("unknown");
  });

  it("handles empty graphs without crashing", () => {
    const s = new ExplorationState("a");
    expect(s.visibility(empty, "a")).toBe<Visibility>("current");
    expect(s.visibility(empty, "z")).toBe<Visibility>("unknown");
  });
});

// ---------------------------------------------------------------------------
//  Adjacency / discoverable
// ---------------------------------------------------------------------------

describe("adjacency", () => {
  it("adjacentToCurrent returns the direct neighbors", () => {
    const s = new ExplorationState("b");
    expect(s.adjacentToCurrent(linear).sort()).toEqual(["a", "c"]);
  });

  it("discoverableNow excludes the current node from neighbors", () => {
    // Build a graph that includes a self-edge to ensure the filter
    // actually does something.
    const selfEdge: MatrixGraphView = graphViewFromEdges([
      ["a", "b"],
      ["a", "a"],
    ]);
    const s = new ExplorationState("a");
    expect(s.discoverableNow(selfEdge)).toEqual(["b"]);
  });

  it("returns [] when there are no neighbors", () => {
    const isolated: MatrixGraphView = graphViewFromEdges([]);
    const s = new ExplorationState("x");
    expect(s.adjacentToCurrent(isolated)).toEqual([]);
    expect(s.discoverableNow(isolated)).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
//  Helpers
// ---------------------------------------------------------------------------

describe("isAlwaysVisibleKind", () => {
  it("entry and exit are always visible", () => {
    expect(isAlwaysVisibleKind("entry")).toBe(true);
    expect(isAlwaysVisibleKind("exit")).toBe(true);
  });

  it("other kinds are not always visible", () => {
    expect(isAlwaysVisibleKind("data")).toBe(false);
    expect(isAlwaysVisibleKind("ice")).toBe(false);
    expect(isAlwaysVisibleKind("router")).toBe(false);
    expect(isAlwaysVisibleKind("construct")).toBe(false);
  });
});

describe("VISIBILITY_ORDER", () => {
  it("orders unknown < discovered < adjacent < current", () => {
    expect(VISIBILITY_ORDER.unknown).toBeLessThan(VISIBILITY_ORDER.discovered);
    expect(VISIBILITY_ORDER.discovered).toBeLessThan(VISIBILITY_ORDER.adjacent);
    expect(VISIBILITY_ORDER.adjacent).toBeLessThan(VISIBILITY_ORDER.current);
  });
});

// ---------------------------------------------------------------------------
//  Node event picker
// ---------------------------------------------------------------------------

describe("eventForRoomType", () => {
  it("returns combat for ICE and NPC rooms", () => {
    expect(eventForRoomType("ice")).toBe("enter_combat");
    expect(eventForRoomType("npc")).toBe("enter_combat");
  });

  it("returns anomaly for data rooms", () => {
    expect(eventForRoomType("data")).toBe("discover_anomaly");
  });

  it("returns cache for dead ends", () => {
    expect(eventForRoomType("dead_end")).toBe("find_cache");
  });

  it("returns data event for entry / exit / router / core", () => {
    expect(eventForRoomType("entry")).toBe("enter_data");
    expect(eventForRoomType("exit")).toBe("enter_data");
    expect(eventForRoomType("router")).toBe("enter_data");
    expect(eventForRoomType("core")).toBe("enter_data");
  });

  it("returns enter_data for unknown room types", () => {
    expect(eventForRoomType("???")).toBe("enter_data");
  });
});

// ---------------------------------------------------------------------------
//  Reset
// ---------------------------------------------------------------------------

describe("reset", () => {
  it("clears discovered, scanned, and path but keeps current", () => {
    const s = new ExplorationState("a");
    s.visit("b");
    s.visit("c");
    s.probe("b");

    s.reset();
    // current stays at the most recent node ("c")
    expect(s.current).toBe("c");
    // only "c" remains discovered (current re-seeded)
    expect(s.discovered.size).toBe(1);
    expect(s.discovered.has("c")).toBe(true);
    expect(s.scanned.size).toBe(0);
    expect(s.path).toEqual(["c"]);
  });
});
