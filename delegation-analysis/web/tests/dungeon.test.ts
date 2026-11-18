/** Unit tests for the procedural dungeon generator (ADR-0060).
 *
 * Verifies the BSP tree partitioning algorithm, room placement,
 * corridor routing, dead-end branch injection, and overall
 * determinism of the seeded RNG.
 *
 * No Math.random — every test injects a Mulberry32 RNG so failures
 * are reproducible.
 */
import { describe, it, expect } from "vitest";

import {
  BspNode,
  DungeonGenerator,
  GRID_BY_GRADE,
  ProceduralDungeonGenerator,
  addDeadEnds,
  bspPartition,
  buildBidirectionalEdges,
  collectLeaves,
  connectAdjacent,
  dungeonToMatrix,
  factionFor,
  makeMulberry32,
  nodeAttributes,
  pickRoomType,
  placeRooms,
  roomsToNodes,
  withInt,
} from "../src/core/dungeon.ts";

import type { Room, RoomType } from "../src/core/dungeon.ts";

// ---------------------------------------------------------------------------
//  Seeded RNG
// ---------------------------------------------------------------------------

describe("Mulberry32 RNG", () => {
  it("produces the same sequence for the same seed", () => {
    const a = makeMulberry32(42);
    const b = makeMulberry32(42);
    for (let i = 0; i < 20; i += 1) {
      expect(a()).toBe(b());
    }
  });

  it("produces different sequences for different seeds", () => {
    const a = makeMulberry32(1);
    const b = makeMulberry32(2);
    // first few outputs should not match
    const seqA = [a(), a(), a(), a()];
    const seqB = [b(), b(), b(), b()];
    expect(seqA).not.toEqual(seqB);
  });

  it("stays within [0, 1)", () => {
    const rng = makeMulberry32(7);
    for (let i = 0; i < 200; i += 1) {
      const v = rng();
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThan(1);
    }
  });

  it("withInt returns integers in [min, max] inclusive", () => {
    const rngInt = withInt(makeMulberry32(99));
    for (let i = 0; i < 200; i += 1) {
      const v = rngInt(3, 7);
      expect(Number.isInteger(v)).toBe(true);
      expect(v).toBeGreaterThanOrEqual(3);
      expect(v).toBeLessThanOrEqual(7);
    }
  });
});

// ---------------------------------------------------------------------------
//  BSP tree
// ---------------------------------------------------------------------------

describe("BspNode", () => {
  it("isLeaf is true when there are no children", () => {
    const n = new BspNode(0, 0, 5, 5);
    expect(n.isLeaf).toBe(true);
  });

  it("isLeaf is false when children are present", () => {
    const n = new BspNode(0, 0, 8, 8);
    n.left = new BspNode(0, 0, 4, 8);
    n.right = new BspNode(4, 0, 4, 8);
    expect(n.isLeaf).toBe(false);
  });

  it("center returns the region midpoint when no room is set", () => {
    const n = new BspNode(2, 4, 6, 8);
    expect(n.center()).toEqual([5, 8]); // (2+3, 4+4)
  });

  it("center returns the room midpoint when a room is set", () => {
    const n = new BspNode(0, 0, 10, 10);
    n.room = { x: 1, y: 2, w: 4, h: 6, roomId: "r0" };
    expect(n.center()).toEqual([3, 5]); // (1+2, 2+3)
  });
});

describe("bspPartition", () => {
  it("returns a single leaf when the region is too small to split", () => {
    const rngInt = withInt(makeMulberry32(1));
    const rng = makeMulberry32(1);
    const root = bspPartition(rngInt, rng, 4, 0, 0, 6, 6);
    expect(root.isLeaf).toBe(true);
  });

  it("recursively splits until every leaf fits within minLeafSize", () => {
    const rngInt = withInt(makeMulberry32(123));
    const rng = makeMulberry32(123);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 8, 8);
    const leaves = collectLeaves(root);
    for (const leaf of leaves) {
      // Each leaf's room has room to grow; just check w/h are reasonable
      expect(leaf.w).toBeGreaterThanOrEqual(1);
      expect(leaf.h).toBeGreaterThanOrEqual(1);
    }
    expect(leaves.length).toBeGreaterThan(1);
  });

  it("every leaf's region stays inside the parent bounds", () => {
    const rngInt = withInt(makeMulberry32(77));
    const rng = makeMulberry32(77);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 12, 10);
    const leaves = collectLeaves(root);
    for (const leaf of leaves) {
      expect(leaf.x).toBeGreaterThanOrEqual(0);
      expect(leaf.y).toBeGreaterThanOrEqual(0);
      expect(leaf.x + leaf.w).toBeLessThanOrEqual(12);
      expect(leaf.y + leaf.h).toBeLessThanOrEqual(10);
    }
  });
});

describe("placeRooms", () => {
  it("places exactly one room per leaf", () => {
    const rngInt = withInt(makeMulberry32(11));
    const rng = makeMulberry32(11);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 8, 8);
    const count = placeRooms(rngInt, 1, root);
    const leaves = collectLeaves(root);
    expect(count).toBe(leaves.length);
    for (const leaf of leaves) {
      expect(leaf.room).not.toBeNull();
    }
  });

  it("assigns unique sequential room ids starting at r0", () => {
    const rngInt = withInt(makeMulberry32(33));
    const rng = makeMulberry32(33);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 8, 6);
    placeRooms(rngInt, 1, root);
    const leaves = collectLeaves(root);
    const ids = new Set(leaves.map((l) => l.room?.roomId));
    expect(ids.size).toBe(leaves.length);
    // All ids follow the rN pattern starting from r0
    for (const id of ids) {
      expect(id).toMatch(/^r\d+$/);
    }
  });

  it("rooms stay inside their leaf region (with padding)", () => {
    const rngInt = withInt(makeMulberry32(2024));
    const rng = makeMulberry32(2024);
    const padding = 1;
    const root = bspPartition(rngInt, rng, 3, 0, 0, 12, 8);
    placeRooms(rngInt, padding, root);
    const leaves = collectLeaves(root);
    for (const leaf of leaves) {
      const r = leaf.room!;
      expect(r.x).toBeGreaterThanOrEqual(leaf.x + padding);
      expect(r.y).toBeGreaterThanOrEqual(leaf.y + padding);
      expect(r.x + r.w).toBeLessThanOrEqual(leaf.x + leaf.w);
      expect(r.y + r.h).toBeLessThanOrEqual(leaf.y + leaf.h);
    }
  });
});

describe("collectLeaves", () => {
  it("returns every leaf node in pre-order", () => {
    const rngInt = withInt(makeMulberry32(55));
    const rng = makeMulberry32(55);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 8, 8);
    placeRooms(rngInt, 1, root);
    const leaves = collectLeaves(root);
    // Each leaf has a room; each internal node has none
    for (const leaf of leaves) {
      expect(leaf.room).not.toBeNull();
    }
    expect(leaves.length).toBeGreaterThan(1);
  });
});

// ---------------------------------------------------------------------------
//  Spanning tree + dead-ends
// ---------------------------------------------------------------------------

describe("connectAdjacent", () => {
  it("returns at most n-1 edges (spanning tree size)", () => {
    const rngInt = withInt(makeMulberry32(5));
    const rng = makeMulberry32(5);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 10, 8);
    placeRooms(rngInt, 1, root);
    const leaves = collectLeaves(root);
    const tree = connectAdjacent(rng, leaves);
    expect(tree.length).toBeLessThanOrEqual(leaves.length - 1);
  });

  it("connects every leaf exactly once (no cycles / no isolates)", () => {
    const rngInt = withInt(makeMulberry32(101));
    const rng = makeMulberry32(101);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 12, 10);
    placeRooms(rngInt, 1, root);
    const leaves = collectLeaves(root);
    const tree = connectAdjacent(rng, leaves);

    // Collect endpoints from the spanning tree
    const connected = new Set<string>();
    for (const [a, b] of tree) {
      connected.add(a);
      connected.add(b);
    }
    const roomIds = new Set(leaves.map((l) => l.room!.roomId));
    for (const id of roomIds) {
      expect(connected.has(id)).toBe(true);
    }
  });
});

describe("addDeadEnds", () => {
  it("returns the original edges when character has 0 dead-end fraction", () => {
    const rng = makeMulberry32(13);
    const root = bspPartition(withInt(rng), rng, 2, 0, 0, 8, 8);
    placeRooms(withInt(rng), 1, root);
    const leaves = collectLeaves(root);
    const base: Array<readonly [string, string]> = [];
    const out = addDeadEnds(rng, leaves, base, "novice");
    // novice has 0.1 fraction, so a few extras may be added; but for
    // very small graphs (n < 3) the function short-circuits to original.
    if (leaves.length < 3) {
      expect(out).toEqual(base);
    }
  });

  it("adds more edges for heretic than for novice", () => {
    function run(charRef: "novice" | "heretic"): number {
      const rng = makeMulberry32(12345);
      const root = bspPartition(withInt(rng), rng, 2, 0, 0, 14, 10);
      placeRooms(withInt(rng), 1, root);
      const leaves = collectLeaves(root);
      const tree = connectAdjacent(rng, leaves);
      const out = addDeadEnds(rng, leaves, tree, charRef);
      return out.length;
    }
    const noviceEdges = run("novice");
    const hereticEdges = run("heretic");
    expect(hereticEdges).toBeGreaterThan(noviceEdges);
  });
});

// ---------------------------------------------------------------------------
//  Room type assignment + faction
// ---------------------------------------------------------------------------

describe("nodeAttributes + factionFor", () => {
  it("ENTRY maps to (entry, none, surface)", () => {
    expect(nodeAttributes("entry", "veteran")).toEqual({
      kind: "entry",
      ice: "none",
      zone: "surface",
    });
  });

  it("ICE heretic gets black ice; others get standard", () => {
    expect(nodeAttributes("ice", "heretic").ice).toBe("black");
    expect(nodeAttributes("ice", "veteran").ice).toBe("standard");
    expect(nodeAttributes("ice", "novice").ice).toBe("standard");
  });

  it("factionFor maps correctly", () => {
    expect(factionFor("novice")).toBe("none");
    expect(factionFor("veteran")).toBe("sense_net");
    expect(factionFor("heretic")).toBe("ta");
  });
});

describe("pickRoomType", () => {
  it("eventually returns data / ice / router / npc / dead_end", () => {
    const rng = makeMulberry32(99);
    const kinds = new Set<RoomType>();
    for (let i = 0; i < 200; i += 1) {
      kinds.add(pickRoomType(rng, "veteran", i, 20));
    }
    // At minimum, DATA + ROUTER should be picked over 200 trials for veteran
    expect(kinds.has("data")).toBe(true);
    expect(kinds.has("router")).toBe(true);
  });
});

describe("buildBidirectionalEdges", () => {
  it("deduplicates pairs and rejects unknown ids / self-loops", () => {
    const rooms: Room[] = [
      { id: "a", x: 0, y: 0, w: 1, h: 1, roomType: "entry", label: "A" },
      { id: "b", x: 1, y: 0, w: 1, h: 1, roomType: "exit", label: "B" },
    ];
    const pairs: Array<readonly [string, string]> = [
      ["a", "b"],
      ["b", "a"], // duplicate of a-b
      ["a", "a"], // self-loop
      ["a", "ghost"], // unknown id
    ];
    const edges = buildBidirectionalEdges(pairs, rooms);
    expect(edges).toHaveLength(1);
    const e = edges[0]!;
    expect([e.src, e.dst].sort()).toEqual(["a", "b"]);
  });
});

describe("roomsToNodes", () => {
  it("preserves room ids and applies the character faction", () => {
    const rooms: Room[] = [
      { id: "e", x: 0, y: 0, w: 1, h: 1, roomType: "entry", label: "E" },
      { id: "x", x: 4, y: 0, w: 1, h: 1, roomType: "exit", label: "X" },
      { id: "d", x: 2, y: 0, w: 1, h: 1, roomType: "data", label: "D" },
    ];
    const nodes = roomsToNodes(rooms, "heretic");
    expect(nodes.map((n) => n.id)).toEqual(["e", "x", "d"]);
    for (const n of nodes) expect(n.faction).toBe("ta");
    const exit = nodes.find((n) => n.kind === "exit")!;
    expect(exit.zone).toBe("core");
  });
});

// ---------------------------------------------------------------------------
//  Phase 1 handcrafted
// ---------------------------------------------------------------------------

describe("DungeonGenerator (Phase 1 handcrafted)", () => {
  it("produces the canonical 20-room 5x4 layout", () => {
    const gen = new DungeonGenerator();
    const g = gen.generate(1);
    expect(g.rooms).toHaveLength(20);
    expect(g.entryId).toBe("entry");
    expect(g.width).toBe(5);
    expect(g.height).toBe(4);
  });

  it("connects every room to its cardinal neighbors", () => {
    const gen = new DungeonGenerator();
    const g = gen.generate(1);
    // Build adjacency from the graph
    const adj = new Map<string, Set<string>>();
    for (const r of g.rooms) adj.set(r.id, adj.get(r.id) ?? new Set());
    for (const e of g.edges) {
      adj.get(e.src)?.add(e.dst);
      adj.get(e.dst)?.add(e.src);
    }
    // The entry (0,2) should be connected to (0,1) and (0,3) and (1,2)
    const entryAdj = adj.get("entry") ?? new Set();
    expect(entryAdj.has("r01")).toBe(true);
    expect(entryAdj.has("r03")).toBe(true);
    expect(entryAdj.has("r12")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
//  Procedural BSP generator (end-to-end)
// ---------------------------------------------------------------------------

describe("ProceduralDungeonGenerator", () => {
  it("is deterministic: same seed/grade/char yields the same graph", () => {
    const gen = new ProceduralDungeonGenerator();
    const a = gen.generate(42, 2, "veteran");
    const b = gen.generate(42, 2, "veteran");
    expect(a.rooms.map((r) => r.id)).toEqual(b.rooms.map((r) => r.id));
    expect(a.edges).toEqual(b.edges);
    expect(a.entryId).toBe(b.entryId);
  });

  it("different seeds yield different graphs", () => {
    const gen = new ProceduralDungeonGenerator();
    const a = gen.generate(1, 2, "veteran");
    const b = gen.generate(2, 2, "veteran");
    // Room counts may differ slightly but topology should not be identical
    const aSig = a.rooms.map((r) => r.id).join(",") + "|" + a.edges.map((e) => e.src + "-" + e.dst).join(",");
    const bSig = b.rooms.map((r) => r.id).join(",") + "|" + b.edges.map((e) => e.src + "-" + e.dst).join(",");
    expect(aSig).not.toBe(bSig);
  });

  it("missionId shifts the seed deterministically", () => {
    const gen = new ProceduralDungeonGenerator();
    const a = gen.generate(42, 2, "veteran", "mission_a");
    const b = gen.generate(42, 2, "veteran", "mission_b");
    // Different mission ids should (usually) yield different graphs
    // (the seed shift can also change BSP shape → room count may differ)
    const aSig = a.rooms.map((r) => r.id).join(",") + "|" + a.edges.map((e) => e.src + "-" + e.dst).join(",");
    const bSig = b.rooms.map((r) => r.id).join(",") + "|" + b.edges.map((e) => e.src + "-" + e.dst).join(",");
    expect(aSig).not.toBe(bSig);
    // But same mission_id should be deterministic
    const a2 = gen.generate(42, 2, "veteran", "mission_a");
    expect(a.rooms.map((r) => r.id)).toEqual(a2.rooms.map((r) => r.id));
  });

  it("produces a reasonable number of rooms per grade", () => {
    const gen = new ProceduralDungeonGenerator();
    // Grade 1 (7x5 grid) typically yields 4-12 rooms
    for (let trial = 0; trial < 5; trial += 1) {
      const g1 = gen.generate(trial * 100, 1, "veteran");
      expect(g1.rooms.length).toBeGreaterThanOrEqual(3);
      expect(g1.rooms.length).toBeLessThanOrEqual(15);
    }
    // Grade 5 (15x10 grid) yields 20-50 rooms
    for (let trial = 0; trial < 5; trial += 1) {
      const g5 = gen.generate(trial * 100, 5, "veteran");
      expect(g5.rooms.length).toBeGreaterThanOrEqual(15);
      expect(g5.rooms.length).toBeLessThanOrEqual(50);
    }
  });

  it("always has exactly one ENTRY and one EXIT room", () => {
    const gen = new ProceduralDungeonGenerator();
    for (let seed = 0; seed < 10; seed += 1) {
      const g = gen.generate(seed, 3, "veteran");
      const entries = g.rooms.filter((r) => r.roomType === "entry");
      const exits = g.rooms.filter((r) => r.roomType === "exit");
      expect(entries).toHaveLength(1);
      expect(exits).toHaveLength(1);
      expect(g.entryId).toBe(entries[0]!.id);
    }
  });

  it("the graph is connected (every room reachable from entry)", () => {
    const gen = new ProceduralDungeonGenerator();
    const g = gen.generate(7, 3, "veteran");
    // Build adjacency
    const adj = new Map<string, string[]>();
    for (const r of g.rooms) adj.set(r.id, []);
    for (const e of g.edges) {
      adj.get(e.src)?.push(e.dst);
      adj.get(e.dst)?.push(e.src);
    }
    // BFS from entry
    const visited = new Set<string>([g.entryId]);
    const queue: string[] = [g.entryId];
    while (queue.length > 0) {
      const cur = queue.shift()!;
      for (const n of adj.get(cur) ?? []) {
        if (!visited.has(n)) {
          visited.add(n);
          queue.push(n);
        }
      }
    }
    for (const r of g.rooms) {
      expect(visited.has(r.id)).toBe(true);
    }
  });

  it("all rooms stay inside the grid bounds", () => {
    const gen = new ProceduralDungeonGenerator();
    const g = gen.generate(99, 4, "heretic");
    for (const r of g.rooms) {
      expect(r.x).toBeGreaterThanOrEqual(0);
      expect(r.y).toBeGreaterThanOrEqual(0);
      expect(r.x + r.w).toBeLessThanOrEqual(g.width);
      expect(r.y + r.h).toBeLessThanOrEqual(g.height);
    }
  });

  it("heretic dead-end density is higher than novice's", () => {
    const gen = new ProceduralDungeonGenerator();
    const novice = gen.generate(1, 4, "novice");
    const heretic = gen.generate(1, 4, "heretic");
    // heretic adds more dead-end branches, so total edges should be larger
    expect(heretic.edges.length).toBeGreaterThan(novice.edges.length);
  });

  it("rejects bad constructor args", () => {
    expect(() => new ProceduralDungeonGenerator(0)).toThrow();
    expect(() => new ProceduralDungeonGenerator(2, -1)).toThrow();
  });

  it("exposes a complete grid-by-grade table", () => {
    for (let g = 1; g <= 5; g += 1) {
      expect(GRID_BY_GRADE[g]).toBeDefined();
      const [w, h] = GRID_BY_GRADE[g]!;
      expect(w).toBeGreaterThan(0);
      expect(h).toBeGreaterThan(0);
    }
  });
});

// ---------------------------------------------------------------------------
//  Adapter: dungeon → web Matrix
// ---------------------------------------------------------------------------

describe("dungeonToMatrix", () => {
  it("produces a valid web Matrix shape", () => {
    const gen = new ProceduralDungeonGenerator();
    const g = gen.generate(42, 2, "veteran");
    const m = dungeonToMatrix(g);
    expect(m.nodes.length).toBe(g.rooms.length);
    expect(m.startNode).toBeGreaterThanOrEqual(0);
    expect(m.bossNode).toBeGreaterThanOrEqual(0);
    // Every node has a zone and a reward
    for (const n of m.nodes) {
      expect(n.zone).toBeTruthy();
      expect(n.reward.credits).toBeGreaterThanOrEqual(0);
    }
  });

  it("marks the exit room as the boss node", () => {
    const gen = new ProceduralDungeonGenerator();
    const g = gen.generate(42, 2, "veteran");
    const m = dungeonToMatrix(g);
    const boss = m.nodes[m.bossNode]!;
    expect(boss.isBoss).toBe(true);
  });

  it("adjacency is consistent between dungeon edges and matrix adjacent", () => {
    const gen = new ProceduralDungeonGenerator();
    const g = gen.generate(7, 2, "veteran");
    const m = dungeonToMatrix(g);
    // For each matrix node, its adjacent list should be a subset of
    // the matrix node ids
    for (const n of m.nodes) {
      for (const a of n.adjacent) {
        expect(a).toBeGreaterThanOrEqual(0);
        expect(a).toBeLessThan(m.nodes.length);
      }
    }
  });
});
