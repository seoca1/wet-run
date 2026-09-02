/** Spanning tree + room-type assignment + procedural generator
 *  (ADR-0110 split).
 *
 * Wires the BSP primitives from `dungeon_bsp.ts` into a complete
 * `DungeonGraph`:
 *  1. Kruskal MST over BSP leaves → spanning tree (L-corridors).
 *  2. Extra dead-end branches based on `characterRef`.
 *  3. Room-type assignment (ENTRY/EXIT/DATA/ICE/NPC/ROUTER).
 *  4. Conversion to typed `DungeonNode`s + deduplicated edges.
 *  5. Wrapping in a `DungeonGraph` for the public API.
 */
import type { ZoneDepth } from "./types.ts";
import {
  type CharacterRef,
  type DungeonGraph,
  type Edge,
  type Room,
  type RoomType,
  type Rng,
  type RngInt,
  makeMulberry32,
  withInt,
} from "./dungeon.ts";
import { type BspNode, collectLeaves, placeRooms, bspPartition } from "./dungeon_bsp.ts";

// ============================================================================
//  Spanning tree + dead-ends
// ============================================================================

function manhattan(ax: number, ay: number, bx: number, by: number): number {
  return Math.abs(bx - ax) + Math.abs(by - ay);
}

/** Build a spanning tree over `leaves` using Kruskal MST. */
export function connectAdjacent(
  _rng: Rng,
  leaves: ReadonlyArray<BspNode>,
): Array<readonly [string, string]> {
  if (leaves.length < 2) return [];

  const parent = leaves.map((_, i) => i);
  const find = (i: number): number => {
    let cur = i;
    while (parent[cur] !== cur) {
      const p = parent[cur] as number;
      parent[cur] = parent[p] as number;
      cur = parent[cur] as number;
    }
    return cur;
  };
  const union = (a: number, b: number): boolean => {
    const ra = find(a);
    const rb = find(b);
    if (ra === rb) return false;
    parent[rb] = ra;
    return true;
  };

  const candidates: Array<[number, number, number]> = [];
  for (let i = 0; i < leaves.length; i += 1) {
    const a = leaves[i] as BspNode;
    const [ax, ay] = a.center();
    for (let j = i + 1; j < leaves.length; j += 1) {
      const b = leaves[j] as BspNode;
      const [bx, by] = b.center();
      candidates.push([manhattan(ax, ay, bx, by), i, j]);
    }
  }
  candidates.sort((x, y) => x[0] - y[0]);

  const edges: Array<readonly [string, string]> = [];
  for (const [, i, j] of candidates) {
    if (union(i, j)) {
      const a = leaves[i] as BspNode;
      const b = leaves[j] as BspNode;
      if (a.room !== null && b.room !== null) {
        edges.push([a.room.roomId, b.room.roomId] as const);
      }
      if (edges.length >= leaves.length - 1) break;
    }
  }
  return edges;
}

/** Fraction of extra branch edges per character reference. */
export const DEADEND_BY_CHAR: Readonly<Record<CharacterRef, number>> = {
  novice: 0.1,
  veteran: 0.25,
  heretic: 0.4,
};

/** Add extra branch edges proportional to `characterRef`'s dead-end fraction. */
export function addDeadEnds(
  rng: Rng,
  leaves: ReadonlyArray<BspNode>,
  existingEdges: ReadonlyArray<readonly [string, string]>,
  characterRef: CharacterRef,
): Array<readonly [string, string]> {
  const fraction = DEADEND_BY_CHAR[characterRef];
  if (fraction <= 0 || leaves.length < 3) return [...existingEdges];

  const targetExtras = Math.round(fraction * (leaves.length - 1));
  if (targetExtras <= 0) return [...existingEdges];

  const existingSet = new Set<string>();
  for (const [a, b] of existingEdges) {
    existingSet.add([a, b].sort().join("\u0000"));
  }

  const out: Array<readonly [string, string]> = [...existingEdges];
  let added = 0;
  const maxTries = Math.max(1, targetExtras * 8);
  const idOf = (leaf: BspNode): string | null =>
    leaf.room !== null ? leaf.room.roomId : null;

  for (let t = 0; t < maxTries && added < targetExtras; t += 1) {
    const i = Math.floor(rng() * leaves.length);
    let j = Math.floor(rng() * leaves.length);
    if (j === i) j = (j + 1) % leaves.length;
    const a = leaves[i] as BspNode;
    const b = leaves[j] as BspNode;
    const aId = idOf(a);
    const bId = idOf(b);
    if (aId === null || bId === null) continue;
    const key = [aId, bId].sort().join("\u0000");
    if (existingSet.has(key)) continue;
    out.push([aId, bId] as const);
    existingSet.add(key);
    added += 1;
  }
  return out;
}

// ============================================================================
//  Room-type assignment
// ============================================================================

/** Faction for the matrix — derived from character reference. */
export type DungeonFaction = "none" | "hosaka" | "maas" | "sense_net" | "ta";

/** ICE category — used for combat display / ZDR calculation downstream. */
export type DungeonIceKind = "none" | "standard" | "watchdog" | "black";

/** Node kind for the resulting MatrixGraph. */
export type DungeonNodeKind =
  | "entry"
  | "data"
  | "system"
  | "ice"
  | "construct"
  | "router"
  | "core"
  | "exit";

/** A typed node produced by the procedural generator. */
export interface DungeonNode {
  readonly id: string;
  readonly kind: DungeonNodeKind;
  readonly label: string;
  readonly zone: ZoneDepth;
  readonly ice: DungeonIceKind;
  readonly faction: DungeonFaction;
  readonly roomType: RoomType;
  readonly x: number;
  readonly y: number;
}

/** Short label for a room by type. */
function labelFor(roomType: RoomType, index: number): string {
  const base: Record<RoomType, string> = {
    empty: "Empty",
    entry: "Jack-in Point",
    exit: "Extraction Gate",
    data: "Data Vault",
    ice: "ICE Barrier",
    npc: "Construct",
    router: "Router",
    core: "Core",
    dead_end: "Dead End",
  };
  const head = base[roomType];
  if (roomType === "entry" || roomType === "exit") return head;
  return `${head} ${index}`;
}

/** Fraction of rooms that contain ICE encounters. */
export const ICE_FRACTION_BY_CHAR: Readonly<Record<CharacterRef, number>> = {
  novice: 0.15,
  veteran: 0.2,
  heretic: 0.3,
};

/** Target number of NPC rooms per character reference. */
export const NPC_BIAS_BY_CHAR: Readonly<Record<CharacterRef, number>> = {
  novice: 0,
  veteran: 1,
  heretic: 2,
};

/** Pick a non-special room type weighted by character reference. */
export function pickRoomType(
  rng: Rng,
  characterRef: CharacterRef,
  _index: number,
  total: number,
): RoomType {
  const iceFraction = ICE_FRACTION_BY_CHAR[characterRef];
  const npcBias = NPC_BIAS_BY_CHAR[characterRef];

  const roll = rng();
  const dataThreshold = 1.0 - 1.0 / Math.max(3, total);
  if (roll < dataThreshold - iceFraction - 0.05 * npcBias) return "data";
  if (roll < dataThreshold - 0.05 * npcBias) return "ice";
  if (roll < dataThreshold) return "router";
  if (npcBias > 0 && rng() < 0.1 + 0.1 * npcBias) return "npc";
  if (rng() < 0.08) return "dead_end";
  return "router";
}

/** Map a room type to (NodeKind, IceKind, ZoneDepth). */
export function nodeAttributes(
  roomType: RoomType,
  characterRef: CharacterRef,
): { kind: DungeonNodeKind; ice: DungeonIceKind; zone: ZoneDepth } {
  switch (roomType) {
    case "entry":
      return { kind: "entry", ice: "none", zone: "surface" };
    case "exit":
      return { kind: "exit", ice: "none", zone: "core" };
    case "data":
      return { kind: "data", ice: "none", zone: "surface" };
    case "ice":
      return {
        kind: "ice",
        ice: characterRef === "heretic" ? "black" : "standard",
        zone: "mid",
      };
    case "npc":
      return { kind: "construct", ice: "none", zone: "mid" };
    case "dead_end":
      return { kind: "router", ice: "none", zone: "mid" };
    case "core":
      return { kind: "core", ice: "none", zone: "core" };
    case "router":
    case "empty":
    default:
      return { kind: "router", ice: "none", zone: "surface" };
  }
}

/** Map a character reference to its default dungeon faction. */
export function factionFor(characterRef: CharacterRef): DungeonFaction {
  switch (characterRef) {
    case "novice":
      return "none";
    case "veteran":
      return "sense_net";
    case "heretic":
      return "ta";
  }
}

/** Promote ENTRY/EXIT and decorate DATA / ICE / NPC rooms. */
export function assignRoomTypes(
  rng: Rng,
  leaves: ReadonlyArray<BspNode>,
  characterRef: CharacterRef,
): Room[] {
  if (leaves.length === 0) return [];

  const entryLeaf = leaves[0] as BspNode;
  const [ex, ey] = entryLeaf.center();

  let exitLeaf: BspNode = entryLeaf;
  let bestDist = -1;
  for (const leaf of leaves) {
    const [lx, ly] = leaf.center();
    const d = manhattan(lx, ly, ex, ey);
    if (d > bestDist) {
      bestDist = d;
      exitLeaf = leaf;
    }
  }

  const rooms: Room[] = [];
  for (let i = 0; i < leaves.length; i += 1) {
    const leaf = leaves[i] as BspNode;
    if (leaf.room === null) continue;
    const r = leaf.room;
    let roomType: RoomType;
    if (leaf === entryLeaf) {
      roomType = "entry";
    } else if (leaf === exitLeaf) {
      roomType = "exit";
    } else {
      roomType = pickRoomType(rng, characterRef, i, leaves.length);
    }
    rooms.push({
      id: r.roomId,
      x: r.x,
      y: r.y,
      w: r.w,
      h: r.h,
      roomType,
      label: labelFor(roomType, i),
    });
  }
  return rooms;
}

/** Convert placed rooms to typed `DungeonNode` records. */
export function roomsToNodes(
  rooms: ReadonlyArray<Room>,
  characterRef: CharacterRef,
): DungeonNode[] {
  const faction = factionFor(characterRef);
  const out: DungeonNode[] = [];
  for (const room of rooms) {
    const { kind, ice, zone } = nodeAttributes(room.roomType, characterRef);
    out.push({
      id: room.id,
      kind,
      label: room.label,
      zone,
      ice,
      faction,
      roomType: room.roomType,
      x: room.x,
      y: room.y,
    });
  }
  return out;
}

/** Deduplicate and emit bidirectional edges between known room ids. */
export function buildBidirectionalEdges(
  pairs: ReadonlyArray<readonly [string, string]>,
  rooms: ReadonlyArray<Room>,
): Edge[] {
  const ids = new Set(rooms.map((r) => r.id));
  const set = new Set<string>();
  for (const [a, b] of pairs) {
    if (!ids.has(a) || !ids.has(b) || a === b) continue;
    set.add([a, b].sort().join("\u0000"));
  }
  const result: Array<readonly [string, string]> = [];
  for (const key of set) {
    const parts = key.split("\u0000");
    const a = parts[0] as string;
    const b = parts[1] as string;
    result.push([a, b] as const);
  }
  result.sort((x, y) =>
    x[0] + x[1] < y[0] + y[1] ? -1 : x[0] + x[1] > y[0] + y[1] ? 1 : 0,
  );
  return result.map(([a, b]) => ({ src: a, dst: b }));
}

// ============================================================================
//  Procedural generator (Phase 2 BSP)
// ============================================================================

/** Grid size (cols x rows) per mission grade (1-5). */
export const GRID_BY_GRADE: Readonly<Record<number, readonly [number, number]>> = {
  1: [7, 5],
  2: [9, 6],
  3: [11, 7],
  4: [13, 8],
  5: [15, 10],
};

/** Build a minimal entry/exit fallback for degenerate BSP trees. */
function degenerateDungeonGraph(): DungeonGraph {
  const rooms: Room[] = [
    { id: "entry", x: 0, y: 0, w: 3, h: 3, roomType: "entry", label: "Jack-in Point" },
    { id: "exit", x: 4, y: 0, w: 3, h: 3, roomType: "exit", label: "Extraction Gate" },
  ];
  return {
    rooms,
    edges: [{ src: "entry", dst: "exit" }],
    entryId: "entry",
    width: 7,
    height: 5,
  };
}

/** Procedural BSP dungeon generator (Phase 2). */
export class ProceduralDungeonGenerator {
  readonly minLeafSize: number;
  readonly roomPadding: number;

  constructor(minLeafSize = 2, roomPadding = 1) {
    if (minLeafSize < 1) {
      throw new RangeError(`minLeafSize must be >= 1 (got ${minLeafSize})`);
    }
    if (roomPadding < 0) {
      throw new RangeError(`roomPadding must be >= 0 (got ${roomPadding})`);
    }
    this.minLeafSize = minLeafSize;
    this.roomPadding = roomPadding;
  }

  generate(
    seed: number,
    missionGrade = 1,
    characterRef: CharacterRef = "veteran",
    missionId: string | null = null,
  ): DungeonGraph {
    const rng: Rng = makeMulberry32(applyMissionIdSeed(seed, missionId));
    const rngInt: RngInt = withInt(rng);

    const grade = Math.max(1, Math.min(5, missionGrade));
    const [cols, rows] = GRID_BY_GRADE[grade] as readonly [number, number];

    const root = bspPartition(rngInt, rng, this.minLeafSize, 0, 0, cols, rows);
    placeRooms(rngInt, this.roomPadding, root);

    const leaves = collectLeaves(root);
    if (leaves.length < 2) return degenerateDungeonGraph();

    const treeEdges = connectAdjacent(rng, leaves);
    const branchEdges = addDeadEnds(rng, leaves, treeEdges, characterRef);
    const rooms = assignRoomTypes(rng, leaves, characterRef);
    const edges = buildBidirectionalEdges(branchEdges, rooms);

    const entryLeaf = leaves[0] as BspNode;
    const entryId = entryLeaf.room !== null ? entryLeaf.room.roomId : "entry";

    return { rooms, edges, entryId, width: cols, height: rows };
  }
}

/** Stable string-hash seed offset (mirrors Python `hash(id) % 7919`). */
function applyMissionIdSeed(seed: number, missionId: string | null): number {
  if (missionId === null) return seed;
  let h = 0;
  for (let i = 0; i < missionId.length; i += 1) {
    h = (h * 31 + missionId.charCodeAt(i)) | 0;
  }
  return seed + (Math.abs(h) % 7919);
}
