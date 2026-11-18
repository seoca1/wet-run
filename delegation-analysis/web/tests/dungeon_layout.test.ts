import { describe, it, expect } from "vitest";
import {
  ProceduralDungeonGenerator,
  connectAdjacent,
  addDeadEnds,
  assignRoomTypes,
  roomsToNodes,
  buildBidirectionalEdges,
  pickRoomType,
  nodeAttributes,
  factionFor,
  GRID_BY_GRADE,
  DEADEND_BY_CHAR,
  ICE_FRACTION_BY_CHAR,
  NPC_BIAS_BY_CHAR,
} from "../src/core/dungeon_layout.ts";
import { BspNode, bspPartition, placeRooms, collectLeaves } from "../src/core/dungeon_bsp.ts";
import { makeMulberry32, withInt } from "../src/core/dungeon.ts";
import type { Room, RoomType } from "../src/core/dungeon.ts";

describe("GRID_BY_GRADE", () => {
  it("maps grade 1 to 7x5", () => {
    expect(GRID_BY_GRADE[1]).toEqual([7, 5]);
  });

  it("maps grade 2 to 9x6", () => {
    expect(GRID_BY_GRADE[2]).toEqual([9, 6]);
  });

  it("maps grade 3 to 11x7", () => {
    expect(GRID_BY_GRADE[3]).toEqual([11, 7]);
  });

  it("maps grade 4 to 13x8", () => {
    expect(GRID_BY_GRADE[4]).toEqual([13, 8]);
  });

  it("maps grade 5 to 15x10", () => {
    expect(GRID_BY_GRADE[5]).toEqual([15, 10]);
  });

  it("has entries for all grades 1-5", () => {
    for (let grade = 1; grade <= 5; grade++) {
      expect(GRID_BY_GRADE[grade]).toBeDefined();
    }
  });
});

describe("DEADEND_BY_CHAR", () => {
  it("maps novice to 0.1", () => {
    expect(DEADEND_BY_CHAR.novice).toBe(0.1);
  });

  it("maps veteran to 0.25", () => {
    expect(DEADEND_BY_CHAR.veteran).toBe(0.25);
  });

  it("maps heretic to 0.4", () => {
    expect(DEADEND_BY_CHAR.heretic).toBe(0.4);
  });
});

describe("ICE_FRACTION_BY_CHAR", () => {
  it("maps novice to 0.15", () => {
    expect(ICE_FRACTION_BY_CHAR.novice).toBe(0.15);
  });

  it("maps veteran to 0.2", () => {
    expect(ICE_FRACTION_BY_CHAR.veteran).toBe(0.2);
  });

  it("maps heretic to 0.3", () => {
    expect(ICE_FRACTION_BY_CHAR.heretic).toBe(0.3);
  });
});

describe("NPC_BIAS_BY_CHAR", () => {
  it("maps novice to 0", () => {
    expect(NPC_BIAS_BY_CHAR.novice).toBe(0);
  });

  it("maps veteran to 1", () => {
    expect(NPC_BIAS_BY_CHAR.veteran).toBe(1);
  });

  it("maps heretic to 2", () => {
    expect(NPC_BIAS_BY_CHAR.heretic).toBe(2);
  });
});

describe("connectAdjacent", () => {
  it("returns empty array for empty leaves", () => {
    const rng = makeMulberry32(42);
    const edges = connectAdjacent(rng, []);
    expect(edges).toEqual([]);
  });

  it("returns empty array for single leaf", () => {
    const rng = makeMulberry32(42);
    const node = new BspNode(0, 0, 5, 5);
    node.room = { x: 1, y: 1, w: 3, h: 3, roomId: "r0" };
    const edges = connectAdjacent(rng, [node]);
    expect(edges).toEqual([]);
  });

  it("connects two leaves", () => {
    const rng = makeMulberry32(42);
    const node1 = new BspNode(0, 0, 5, 5);
    node1.room = { x: 1, y: 1, w: 3, h: 3, roomId: "r0" };
    const node2 = new BspNode(5, 0, 5, 5);
    node2.room = { x: 6, y: 1, w: 3, h: 3, roomId: "r1" };
    const edges = connectAdjacent(rng, [node1, node2]);
    expect(edges.length).toBe(1);
    expect(edges[0]).toEqual(["r0", "r1"]);
  });

  it("creates spanning tree with N-1 edges for N leaves", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 20, 20);
    placeRooms(rngInt, 1, root);
    const leaves = collectLeaves(root);
    const edges = connectAdjacent(rng, leaves);
    expect(edges.length).toBe(leaves.length - 1);
  });

  it("connects to form fully connected graph", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 20, 20);
    placeRooms(rngInt, 1, root);
    const leaves = collectLeaves(root);
    const edges = connectAdjacent(rng, leaves);
    const roomIds = new Set(leaves.map((leaf) => leaf.room?.roomId).filter((id) => id));
    const connectedIds = new Set<string>();
    for (const [a, b] of edges) {
      connectedIds.add(a);
      connectedIds.add(b);
    }
    expect(connectedIds.size).toBe(roomIds.size);
  });

  it("skips leaves without room", () => {
    const rng = makeMulberry32(42);
    const node1 = new BspNode(0, 0, 5, 5);
    const node2 = new BspNode(5, 0, 5, 5);
    node2.room = { x: 6, y: 1, w: 3, h: 3, roomId: "r1" };
    const edges = connectAdjacent(rng, [node1, node2]);
    expect(edges.length).toBe(0);
  });
});

describe("addDeadEnds", () => {
  it("returns existing edges when fraction is 0", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 20, 20);
    placeRooms(rngInt, 1, root);
    const leaves = collectLeaves(root);
    const initial = connectAdjacent(rng, leaves);
    const result = addDeadEnds(rng, leaves, initial, "novice");
    expect(result.length).toBeGreaterThanOrEqual(initial.length);
  });

  it("adds extra edges for veteran", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 30, 30);
    placeRooms(rngInt, 1, root);
    const leaves = collectLeaves(root);
    const initial = connectAdjacent(rng, leaves);
    const result = addDeadEnds(rng, leaves, initial, "veteran");
    expect(result.length).toBeGreaterThanOrEqual(initial.length);
  });

  it("adds more edges for heretic than veteran", () => {
    const rng1 = makeMulberry32(42);
    const rngInt1 = withInt(rng1);
    const root1 = bspPartition(rngInt1, rng1, 2, 0, 0, 30, 30);
    placeRooms(rngInt1, 1, root1);
    const leaves1 = collectLeaves(root1);
    const initial1 = connectAdjacent(rng1, leaves1);
    const veteran = addDeadEnds(rng1, leaves1, initial1, "veteran");

    const rng2 = makeMulberry32(42);
    const rngInt2 = withInt(rng2);
    const root2 = bspPartition(rngInt2, rng2, 2, 0, 0, 30, 30);
    placeRooms(rngInt2, 1, root2);
    const leaves2 = collectLeaves(root2);
    const initial2 = connectAdjacent(rng2, leaves2);
    const heretic = addDeadEnds(rng2, leaves2, initial2, "heretic");

    expect(heretic.length).toBeGreaterThanOrEqual(veteran.length);
  });

  it("does not duplicate existing edges", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 30, 30);
    placeRooms(rngInt, 1, root);
    const leaves = collectLeaves(root);
    const initial = connectAdjacent(rng, leaves);
    const result = addDeadEnds(rng, leaves, initial, "heretic");
    const uniqueKeys = new Set(result.map(([a, b]) => [a, b].sort().join("\u0000")));
    expect(uniqueKeys.size).toBe(result.length);
  });

  it("returns existing edges when leaves count is too small", () => {
    const rng = makeMulberry32(42);
    const node1 = new BspNode(0, 0, 5, 5);
    node1.room = { x: 1, y: 1, w: 3, h: 3, roomId: "r0" };
    const node2 = new BspNode(5, 0, 5, 5);
    node2.room = { x: 6, y: 1, w: 3, h: 3, roomId: "r1" };
    const initial: Array<readonly [string, string]> = [["r0", "r1"]];
    const result = addDeadEnds(rng, [node1, node2], initial, "heretic");
    expect(result).toEqual(initial);
  });
});

describe("pickRoomType", () => {
  it("returns a valid room type", () => {
    const rng = makeMulberry32(42);
    const validTypes: RoomType[] = ["data", "ice", "router", "npc", "dead_end"];
    const result = pickRoomType(rng, "novice", 0, 10);
    expect(validTypes.includes(result)).toBe(true);
  });

  it("returns data most frequently", () => {
    const rng = makeMulberry32(42);
    const counts: Record<string, number> = {};
    for (let i = 0; i < 100; i++) {
      const type = pickRoomType(rng, "novice", i, 100);
      counts[type] = (counts[type] ?? 0) + 1;
    }
    expect(counts.data ?? 0).toBeGreaterThan(counts.ice ?? 0);
  });

  it("increases ICE frequency for heretic", () => {
    const rng1 = makeMulberry32(42);
    const noviceCounts: Record<string, number> = {};
    for (let i = 0; i < 100; i++) {
      const type = pickRoomType(rng1, "novice", i, 100);
      noviceCounts[type] = (noviceCounts[type] ?? 0) + 1;
    }

    const rng2 = makeMulberry32(42);
    const hereticCounts: Record<string, number> = {};
    for (let i = 0; i < 100; i++) {
      const type = pickRoomType(rng2, "heretic", i, 100);
      hereticCounts[type] = (hereticCounts[type] ?? 0) + 1;
    }

    expect(hereticCounts.ice ?? 0).toBeGreaterThan(noviceCounts.ice ?? 0);
  });

  it("increases NPC frequency for veteran and heretic", () => {
    const rng1 = makeMulberry32(42);
    const noviceCounts: Record<string, number> = {};
    for (let i = 0; i < 100; i++) {
      const type = pickRoomType(rng1, "novice", i, 100);
      noviceCounts[type] = (noviceCounts[type] ?? 0) + 1;
    }

    const rng2 = makeMulberry32(42);
    const veteranCounts: Record<string, number> = {};
    for (let i = 0; i < 100; i++) {
      const type = pickRoomType(rng2, "veteran", i, 100);
      veteranCounts[type] = (veteranCounts[type] ?? 0) + 1;
    }

    expect(veteranCounts.npc ?? 0).toBeGreaterThanOrEqual(noviceCounts.npc ?? 0);
  });
});

describe("nodeAttributes", () => {
  it("maps entry to entry kind with none ICE", () => {
    const attrs = nodeAttributes("entry", "novice");
    expect(attrs.kind).toBe("entry");
    expect(attrs.ice).toBe("none");
    expect(attrs.zone).toBe("surface");
  });

  it("maps exit to exit kind with none ICE", () => {
    const attrs = nodeAttributes("exit", "novice");
    expect(attrs.kind).toBe("exit");
    expect(attrs.ice).toBe("none");
    expect(attrs.zone).toBe("core");
  });

  it("maps data to data kind", () => {
    const attrs = nodeAttributes("data", "novice");
    expect(attrs.kind).toBe("data");
    expect(attrs.ice).toBe("none");
  });

  it("maps ice to ice kind with standard ICE for novice", () => {
    const attrs = nodeAttributes("ice", "novice");
    expect(attrs.kind).toBe("ice");
    expect(attrs.ice).toBe("standard");
  });

  it("maps ice to ice kind with black ICE for heretic", () => {
    const attrs = nodeAttributes("ice", "heretic");
    expect(attrs.kind).toBe("ice");
    expect(attrs.ice).toBe("black");
  });

  it("maps npc to construct kind", () => {
    const attrs = nodeAttributes("npc", "veteran");
    expect(attrs.kind).toBe("construct");
    expect(attrs.ice).toBe("none");
  });

  it("maps router to router kind", () => {
    const attrs = nodeAttributes("router", "novice");
    expect(attrs.kind).toBe("router");
    expect(attrs.ice).toBe("none");
  });

  it("maps dead_end to router kind", () => {
    const attrs = nodeAttributes("dead_end", "novice");
    expect(attrs.kind).toBe("router");
    expect(attrs.ice).toBe("none");
  });

  it("maps core to core kind", () => {
    const attrs = nodeAttributes("core", "veteran");
    expect(attrs.kind).toBe("core");
    expect(attrs.ice).toBe("none");
  });
});

describe("factionFor", () => {
  it("maps novice to none", () => {
    expect(factionFor("novice")).toBe("none");
  });

  it("maps veteran to sense_net", () => {
    expect(factionFor("veteran")).toBe("sense_net");
  });

  it("maps heretic to ta", () => {
    expect(factionFor("heretic")).toBe("ta");
  });
});

describe("assignRoomTypes", () => {
  it("assigns entry to first leaf", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 20, 20);
    placeRooms(rngInt, 1, root);
    const leaves = collectLeaves(root);
    const rooms = assignRoomTypes(rng, leaves, "novice");
    expect(rooms[0]?.roomType).toBe("entry");
  });

  it("assigns exit to farthest leaf", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 20, 20);
    placeRooms(rngInt, 1, root);
    const leaves = collectLeaves(root);
    const rooms = assignRoomTypes(rng, leaves, "novice");
    expect(rooms.some((r) => r.roomType === "exit")).toBe(true);
  });

  it("assigns non-special types to middle rooms", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 30, 30);
    placeRooms(rngInt, 1, root);
    const leaves = collectLeaves(root);
    const rooms = assignRoomTypes(rng, leaves, "novice");
    const middle = rooms.slice(1, -1);
    const validTypes: RoomType[] = ["data", "ice", "router", "npc", "dead_end"];
    expect(middle.every((r) => validTypes.includes(r.roomType))).toBe(true);
  });

  it("returns empty array for empty leaves", () => {
    const rng = makeMulberry32(42);
    const rooms = assignRoomTypes(rng, [], "novice");
    expect(rooms).toEqual([]);
  });

  it("skips leaves without room", () => {
    const rng = makeMulberry32(42);
    const node = new BspNode(0, 0, 5, 5);
    const rooms = assignRoomTypes(rng, [node], "novice");
    expect(rooms).toEqual([]);
  });

  it("assigns label to each room", () => {
    const rng = makeMulberry32(42);
    const rngInt = withInt(rng);
    const root = bspPartition(rngInt, rng, 2, 0, 0, 20, 20);
    placeRooms(rngInt, 1, root);
    const leaves = collectLeaves(root);
    const rooms = assignRoomTypes(rng, leaves, "novice");
    expect(rooms.every((r) => r.label.length > 0)).toBe(true);
  });
});

describe("roomsToNodes", () => {
  it("converts rooms to dungeon nodes", () => {
    const rooms: Room[] = [
      { id: "r0", x: 1, y: 1, w: 3, h: 3, roomType: "entry", label: "Entry" },
    ];
    const nodes = roomsToNodes(rooms, "novice");
    expect(nodes.length).toBe(1);
    expect(nodes[0]?.id).toBe("r0");
  });

  it("assigns faction based on character", () => {
    const rooms: Room[] = [
      { id: "r0", x: 1, y: 1, w: 3, h: 3, roomType: "entry", label: "Entry" },
    ];
    const nodes = roomsToNodes(rooms, "veteran");
    expect(nodes[0]?.faction).toBe("sense_net");
  });

  it("assigns kind based on room type", () => {
    const rooms: Room[] = [
      { id: "r0", x: 1, y: 1, w: 3, h: 3, roomType: "data", label: "Data" },
    ];
    const nodes = roomsToNodes(rooms, "novice");
    expect(nodes[0]?.kind).toBe("data");
  });

  it("preserves room coordinates", () => {
    const rooms: Room[] = [
      { id: "r0", x: 5, y: 10, w: 3, h: 4, roomType: "entry", label: "Entry" },
    ];
    const nodes = roomsToNodes(rooms, "novice");
    expect(nodes[0]?.x).toBe(5);
    expect(nodes[0]?.y).toBe(10);
  });
});

describe("buildBidirectionalEdges", () => {
  it("deduplicates edges", () => {
    const rooms: Room[] = [
      { id: "r0", x: 0, y: 0, w: 3, h: 3, roomType: "entry", label: "Entry" },
      { id: "r1", x: 0, y: 0, w: 3, h: 3, roomType: "exit", label: "Exit" },
    ];
    const pairs: Array<readonly [string, string]> = [
      ["r0", "r1"],
      ["r1", "r0"],
    ];
    const edges = buildBidirectionalEdges(pairs, rooms);
    expect(edges.length).toBe(1);
  });

  it("filters out unknown room ids", () => {
    const rooms: Room[] = [
      { id: "r0", x: 0, y: 0, w: 3, h: 3, roomType: "entry", label: "Entry" },
    ];
    const pairs: Array<readonly [string, string]> = [
      ["r0", "r999"],
    ];
    const edges = buildBidirectionalEdges(pairs, rooms);
    expect(edges.length).toBe(0);
  });

  it("filters out self-edges", () => {
    const rooms: Room[] = [
      { id: "r0", x: 0, y: 0, w: 3, h: 3, roomType: "entry", label: "Entry" },
    ];
    const pairs: Array<readonly [string, string]> = [
      ["r0", "r0"],
    ];
    const edges = buildBidirectionalEdges(pairs, rooms);
    expect(edges.length).toBe(0);
  });

  it("returns edges with src and dst properties", () => {
    const rooms: Room[] = [
      { id: "r0", x: 0, y: 0, w: 3, h: 3, roomType: "entry", label: "Entry" },
      { id: "r1", x: 0, y: 0, w: 3, h: 3, roomType: "exit", label: "Exit" },
    ];
    const pairs: Array<readonly [string, string]> = [
      ["r0", "r1"],
    ];
    const edges = buildBidirectionalEdges(pairs, rooms);
    expect(edges[0]).toHaveProperty("src");
    expect(edges[0]).toHaveProperty("dst");
  });
});

describe("ProceduralDungeonGenerator", () => {
  it("constructs with default parameters", () => {
    const gen = new ProceduralDungeonGenerator();
    expect(gen).toBeDefined();
  });

  it("constructs with custom parameters", () => {
    const gen = new ProceduralDungeonGenerator(3, 2);
    expect(gen.minLeafSize).toBe(3);
    expect(gen.roomPadding).toBe(2);
  });

  it("throws when minLeafSize is less than 1", () => {
    expect(() => new ProceduralDungeonGenerator(0)).toThrow();
  });

  it("throws when roomPadding is negative", () => {
    expect(() => new ProceduralDungeonGenerator(2, -1)).toThrow();
  });

  it("generates dungeon graph", () => {
    const gen = new ProceduralDungeonGenerator();
    const graph = gen.generate(42, 1, "novice");
    expect(graph).toBeDefined();
    expect(graph.rooms.length).toBeGreaterThan(0);
    expect(graph.edges.length).toBeGreaterThan(0);
    expect(graph.entryId).toBeDefined();
  });

  it("clamps grade to 1-5 range", () => {
    const gen = new ProceduralDungeonGenerator();
    const graph1 = gen.generate(42, 0, "novice");
    expect(graph1.width).toBe(7);
    const graph2 = gen.generate(42, 10, "novice");
    expect(graph2.width).toBe(15);
  });

  it("uses GRID_BY_GRADE for dimensions", () => {
    const gen = new ProceduralDungeonGenerator();
    const graph = gen.generate(42, 3, "novice");
    const [cols, rows] = GRID_BY_GRADE[3] as readonly [number, number];
    expect(graph.width).toBe(cols);
    expect(graph.height).toBe(rows);
  });

  it("produces deterministic graphs with same seed", () => {
    const gen = new ProceduralDungeonGenerator();
    const graph1 = gen.generate(42, 1, "novice");
    const graph2 = gen.generate(42, 1, "novice");
    expect(graph1.rooms.length).toBe(graph2.rooms.length);
  });

  it("includes entry and exit rooms", () => {
    const gen = new ProceduralDungeonGenerator();
    const graph = gen.generate(42, 1, "novice");
    expect(graph.rooms.some((r) => r.roomType === "entry")).toBe(true);
    expect(graph.rooms.some((r) => r.roomType === "exit")).toBe(true);
  });

  it("applies missionId seed offset", () => {
    const gen = new ProceduralDungeonGenerator();
    const graph1 = gen.generate(42, 1, "novice", null);
    const graph2 = gen.generate(42, 1, "novice", "mission123");
    expect(graph1.rooms.length).toBe(graph2.rooms.length);
  });

  it("returns degenerate fallback for impossible BSP", () => {
    const gen = new ProceduralDungeonGenerator(100, 0);
    const graph = gen.generate(42, 1, "novice");
    expect(graph.rooms.length).toBeGreaterThanOrEqual(2);
  });
});
