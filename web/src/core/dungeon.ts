/** Public types + seeded RNG + Phase 1 handcrafted generator
 *  + web-Matrix adapter (ADR-0060).
 *
 * The actual BSP partitioning lives in `dungeon_bsp.ts`; spanning
 * tree, room-type assignment, and the procedural generator live in
 * `dungeon_layout.ts`. This module stays slim so it can serve as the
 * stable public entry point for the dungeon system.
 */
import type { Matrix, MatrixNode, ZoneDepth } from "./types.ts";

// ============================================================================
//  Public type definitions
// ============================================================================

/** Visual type of room (mirrors Python `RoomType` StrEnum). */
export type RoomType =
  | "empty"
  | "entry"
  | "exit"
  | "data"
  | "ice"
  | "npc"
  | "router"
  | "core"
  | "dead_end";

/** A placed room in the dungeon grid. */
export interface Room {
  readonly id: string;
  readonly x: number;
  readonly y: number;
  readonly w: number;
  readonly h: number;
  readonly roomType: RoomType;
  readonly label: string;
}

/** A graph edge (undirected: stored as one pair). */
export interface Edge {
  readonly src: string;
  readonly dst: string;
}

/** The generated dungeon graph — rooms + corridor edges + entry id. */
export interface DungeonGraph {
  readonly rooms: ReadonlyArray<Room>;
  readonly edges: ReadonlyArray<Edge>;
  readonly entryId: string;
  readonly width: number;
  readonly height: number;
}

/** Character archetype — drives dead-end density + ICE/NPC ratio. */
export type CharacterRef = "novice" | "veteran" | "heretic";

// ============================================================================
//  Seeded RNG
// ============================================================================

/** A function returning a float in [0, 1). */
export type Rng = () => number;

/** A function returning an int in [min, max] (inclusive). */
export type RngInt = (min: number, max: number) => number;

/** Mulberry32 — small, fast, deterministic 32-bit RNG. */
export function makeMulberry32(seed: number): Rng {
  let a = seed | 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Build a paired (rng, int) helper from a base rng. */
export function withInt(rng: Rng): RngInt {
  return (min, max) => {
    if (max < min) {
      throw new RangeError(`rngInt: max (${max}) < min (${min})`);
    }
    return min + Math.floor(rng() * (max - min + 1));
  };
}

// ============================================================================
//  Phase 1 handcrafted generator (ADR-0060 Phase 1)
// ============================================================================

/** Phase 1 hand-crafted 5x4 dungeon layout. Kept for tests that pin
 *  the exact 20-room topology. */
export class DungeonGenerator {
  generate(seed: number, _missionGrade = 1): DungeonGraph {
    void seed;

    const layout: ReadonlyArray<readonly [string, number, number, RoomType, string]> = [
      ["r00", 0, 0, "router", "Comms Relay"],
      ["r10", 1, 0, "router", "Router"],
      ["ice", 2, 0, "ice", "ICE Barrier"],
      ["r30", 3, 0, "router", "Junction"],
      ["r40", 4, 0, "router", "Gateway"],
      ["r01", 0, 1, "router", "Buffer"],
      ["r11", 1, 1, "router", "Hub"],
      ["npc_dixie", 2, 1, "npc", "Dixie Flatline"],
      ["data", 3, 1, "data", "Data Vault"],
      ["r41", 4, 1, "router", "Node"],
      ["entry", 0, 2, "entry", "Entry"],
      ["r12", 1, 2, "router", "Corridor"],
      ["r22", 2, 2, "router", "Intersect"],
      ["r32", 3, 2, "router", "Access Point"],
      ["exit", 4, 2, "exit", "Exit"],
      ["r03", 0, 3, "router", "Sublevel"],
      ["r13", 1, 3, "router", "Underpass"],
      ["r23", 2, 3, "router", "Deep Core"],
      ["r33", 3, 3, "router", "Archive"],
      ["r43", 4, 3, "router", "Terminal"],
    ];

    const rooms: Room[] = layout.map(([id, x, y, roomType, label]) => ({
      id,
      x,
      y,
      w: 1,
      h: 1,
      roomType,
      label,
    }));

    const idsAt = new Map<string, Room>();
    for (const r of rooms) idsAt.set(`${r.x},${r.y}`, r);

    const seen = new Set<string>();
    const pairs: Array<readonly [string, string]> = [];
    for (const r of rooms) {
      for (const [dx, dy] of [
        [1, 0],
        [0, 1],
      ] as const) {
        const n = idsAt.get(`${r.x + dx},${r.y + dy}`);
        if (n !== undefined) {
          const key = [r.id, n.id].sort().join("\u0000");
          if (!seen.has(key)) {
            seen.add(key);
            pairs.push([r.id, n.id] as const);
          }
        }
      }
    }

    const edgeSet = new Set<string>();
    const ids = new Set(rooms.map((r) => r.id));
    for (const [a, b] of pairs) {
      if (!ids.has(a) || !ids.has(b) || a === b) continue;
      edgeSet.add([a, b].sort().join("\u0000"));
    }
    const sortedPairs: Array<readonly [string, string]> = [];
    for (const key of edgeSet) {
      const parts = key.split("\u0000");
      sortedPairs.push([parts[0] as string, parts[1] as string] as const);
    }
    const edges: Edge[] = sortedPairs.map(([a, b]) => ({ src: a, dst: b }));

    return { rooms, edges, entryId: "entry", width: 5, height: 4 };
  }
}

// ============================================================================
//  Re-exports for backwards compatibility
// ============================================================================

// BSP primitives
export { BspNode, bspPartition, collectLeaves, placeRooms } from "./dungeon_bsp.ts";
export type { BspRoom } from "./dungeon_bsp.ts";

// Layout helpers + procedural generator
export {
  DEADEND_BY_CHAR,
  GRID_BY_GRADE,
  ICE_FRACTION_BY_CHAR,
  NPC_BIAS_BY_CHAR,
  ProceduralDungeonGenerator,
  addDeadEnds,
  assignRoomTypes,
  buildBidirectionalEdges,
  connectAdjacent,
  factionFor,
  nodeAttributes,
  pickRoomType,
  roomsToNodes,
} from "./dungeon_layout.ts";
export type { DungeonFaction, DungeonIceKind, DungeonNode, DungeonNodeKind } from "./dungeon_layout.ts";

// ============================================================================
//  Adapter: DungeonGraph → web Matrix shape
// ============================================================================

/** Convert a `DungeonGraph` to the web project's `Matrix` shape. */
export function dungeonToMatrix(graph: DungeonGraph): Matrix {
  const sorted = [...graph.rooms].sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  const idToIndex = new Map<string, number>();
  for (let i = 0; i < sorted.length; i += 1) {
    const r = sorted[i] as Room;
    idToIndex.set(r.id, i);
  }

  const bossRoom = sorted.find((r) => r.roomType === "exit") ?? sorted[sorted.length - 1];
  const bossIndex = bossRoom !== undefined ? (idToIndex.get(bossRoom.id) ?? 0) : 0;

  const nodes: MatrixNode[] = sorted.map((room, idx) => {
    const adjacent = graph.edges
      .filter((e) => e.src === room.id || e.dst === room.id)
      .map((e) => (e.src === room.id ? e.dst : e.src))
      .map((nid) => idToIndex.get(nid) ?? -1)
      .filter((i) => i >= 0);
    const isBoss = room.roomType === "exit";
    return {
      id: idx,
      zone: roomZone(room.roomType),
      iceIds: room.roomType === "ice" ? ["watchdog"] : [],
      iceHp: room.roomType === "ice" ? [100] : [],
      reward: { credits: 50 + idx * 25 },
      isBoss,
      adjacent,
    } satisfies MatrixNode;
  });

  return {
    nodes,
    startNode: idToIndex.get(graph.entryId) ?? 0,
    bossNode: bossIndex,
  };
}

/** Map a `RoomType` to the corresponding `ZoneDepth` for the web Matrix. */
function roomZone(roomType: RoomType): ZoneDepth {
  switch (roomType) {
    case "entry":
    case "data":
    case "router":
    case "empty":
      return "surface";
    case "ice":
    case "npc":
    case "dead_end":
      return "mid";
    case "core":
      return "core";
    case "exit":
      return "core-deep";
  }
}
