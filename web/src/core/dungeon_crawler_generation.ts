/** Dungeon-crawler world generation: seeded RNG, state init, level layout,
 *  corridors, and stairs.
 *
 * Extracted from `dungeon_crawler.ts` (module-size policy, AGENTS.md §6).
 * Entity placement + field-of-view live in `dungeon_crawler_entities.ts`; this
 * module owns the RNG and the room/corridor/stairs layout. Every function is a
 * pure helper over an explicit `DungeonState`, so the `DungeonCrawler` facade
 * in `dungeon_crawler_core.ts` can delegate without changing behaviour.
 */

import type { Rng, RngInt } from "./dungeon.ts";
import { ProceduralDungeonGenerator, DungeonGraph } from "./dungeon.ts";
import type { Mission } from "./types.ts";
import { TileType } from "./dungeon_crawler_types.ts";
import type { DungeonState, DungeonTile } from "./dungeon_crawler_types.ts";
import { placeEntities, placePlayerAtEntry } from "./dungeon_crawler_entities.ts";

/** Create a seeded RNG (mirrors Python hash(id) % 7919) */
export function createRng(seed: number, missionId: string | null): Rng {
  let h = seed;
  if (missionId !== null) {
    for (let i = 0; i < missionId.length; i += 1) {
      h = (h * 31 + missionId.charCodeAt(i)) | 0;
    }
    h = h + (Math.abs(h) % 7919);
  }
  let a = h | 0;
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
  return (min: number, max: number): number => {
    if (max < min) {
      throw new RangeError(`rngInt: max (${max}) < min (${min})`);
    }
    return min + Math.floor(rng() * (max - min + 1));
  };
}

/** Initialize the dungeon state with empty values */
export function initializeDungeonState(mission: Mission | null): DungeonState {
  // Default size - will be resized during generation
  const width = 80;
  const height = 45;

  const tiles: DungeonTile[][] = Array.from({ length: height }, () =>
    Array.from({ length: width }, () => ({
      type: TileType.WALL,
      explored: false,
      visible: false,
    })),
  );

  const exploredMap: boolean[][] = Array.from({ length: height }, () =>
    Array.from({ length: width }, () => false),
  );

  return {
    width,
    height,
    tiles,
    entities: [],
    playerX: 1,
    playerY: 1,
    playerHp: 100,
    playerMaxHp: 100,
    playerAlarm: 0,
    turnCount: 0,
    missionId: mission?.id ?? "unknown",
    missionGrade: mission?.grade_max ?? 1,
    characterRef:
      (mission?.grade_max ?? 1 >= 4)
        ? "heretic"
        : (mission?.grade_max ?? 1 >= 2)
          ? "veteran"
          : "novice",
    exploredMap,
    stairsUpX: null,
    stairsUpY: null,
    stairsDownX: null,
    stairsDownY: null,
    level: 0,
    maxLevel: 0,
  };
}

/** Generate a dungeon level */
export function generateLevel(
  state: DungeonState,
  generator: ProceduralDungeonGenerator,
  rng: Rng,
  rngInt: RngInt,
  levelNum: number,
): void {
  // Generate dungeon graph using existing BSP system
  const graph: DungeonGraph = generator.generate(
    Date.now() + levelNum * 1000, // Different seed per level
    state.missionGrade,
    state.characterRef,
  );

  // Resize the dungeon to fit the generated graph
  state.width = graph.width;
  state.height = graph.height;

  // Initialize tiles as walls
  state.tiles = Array.from({ length: state.height }, () =>
    Array.from({ length: state.width }, () => ({
      type: TileType.WALL,
      explored: false,
      visible: false,
    })),
  );

  // Reset explored map for new level
  state.exploredMap = Array.from({ length: state.height }, () =>
    Array.from({ length: state.width }, () => false),
  );

  // Clear entities (except player who gets repositioned)
  state.entities = [];

  // Carry over player stats
  const playerHp = state.playerHp;
  const playerMaxHp = state.playerMaxHp;
  const playerAlarm = state.playerAlarm;

  // Convert rooms and corridors to tiles
  digRoomsAndCorridors(state, graph, rng);

  // Place entities (monsters, items, traps, stairs)
  placeEntities(state, rng, rngInt);

  // Place player at entry point
  placePlayerAtEntry(state, graph);

  // Restore player stats
  state.playerHp = playerHp;
  state.playerMaxHp = playerMaxHp;
  state.playerAlarm = playerAlarm;

  state.level = levelNum;
  state.maxLevel = Math.max(state.maxLevel, levelNum);

  // Place stairs
  placeStairs(state, graph);
}

/** Convert dungeon rooms and corridors to walkable tiles */
export function digRoomsAndCorridors(
  state: DungeonState,
  graph: DungeonGraph,
  rng: Rng,
): void {
  // Start with all walls
  for (let y = 0; y < state.height; y++) {
    for (let x = 0; x < state.width; x++) {
      state.tiles[y][x].type = TileType.WALL;
    }
  }

  // Dig out rooms
  for (const room of graph.rooms) {
    for (let y = room.y; y < room.y + room.h; y++) {
      for (let x = room.x; x < room.x + room.w; x++) {
        if (y >= 0 && y < state.height && x >= 0 && x < state.width) {
          // Room interiors are floors
          state.tiles[y][x].type = TileType.FLOOR;

          // Room walls (edges) - but we'll handle corridors separately for now
          if (
            y === room.y ||
            y === room.y + room.h - 1 ||
            x === room.x ||
            x === room.x + room.w - 1
          ) {
            // This is a wall of the room - might become a door or remain wall
            // For now, leave as wall - we'll add doors later
          }
        }
      }
    }
  }

  // Dig corridors (simplified - just connect room centers with L-shaped paths)
  // In a full implementation, we'd use the edges from the graph
  // For now, connect each room to the first room with a simple path
  if (graph.rooms.length >= 2) {
    const firstRoom = graph.rooms[0];
    for (let i = 1; i < graph.rooms.length; i++) {
      const room = graph.rooms[i];
      digCorridor(
        state,
        rng,
        firstRoom.x + Math.floor(firstRoom.w / 2),
        firstRoom.y + Math.floor(firstRoom.h / 2),
        room.x + Math.floor(room.w / 2),
        room.y + Math.floor(room.h / 2),
      );
    }
  }
}

/** Dig a corridor between two points (L-shaped path) */
export function digCorridor(
  state: DungeonState,
  rng: Rng,
  x1: number,
  y1: number,
  x2: number,
  y2: number,
): void {
  // Randomly choose whether to go horizontal first or vertical first
  const goHorizontalFirst = rng() < 0.5;

  if (goHorizontalFirst) {
    // Go horizontally, then vertically
    for (let x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) {
      if (x >= 0 && x < state.width && y1 >= 0 && y1 < state.height) {
        if (state.tiles[y1][x].type === TileType.WALL) {
          state.tiles[y1][x].type = TileType.FLOOR;
        }
      }
    }
    for (let y = Math.min(y1, y2); y <= Math.max(y1, y2); y++) {
      if (x2 >= 0 && x2 < state.width && y >= 0 && y < state.height) {
        if (state.tiles[y][x2].type === TileType.WALL) {
          state.tiles[y][x2].type = TileType.FLOOR;
        }
      }
    }
  } else {
    // Go vertically, then horizontally
    for (let y = Math.min(y1, y2); y <= Math.max(y1, y2); y++) {
      if (x1 >= 0 && x1 < state.width && y >= 0 && y < state.height) {
        if (state.tiles[y][x1].type === TileType.WALL) {
          state.tiles[y][x1].type = TileType.FLOOR;
        }
      }
    }
    for (let x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) {
      if (x >= 0 && x < state.width && y2 >= 0 && y2 < state.height) {
        if (state.tiles[y2][x].type === TileType.WALL) {
          state.tiles[y2][x].type = TileType.FLOOR;
        }
      }
    }
  }
}

/** Place stairs for level transitions */
export function placeStairs(state: DungeonState, graph: DungeonGraph): void {
  // Find rooms for up/down stairs
  const rooms = [...graph.rooms];

  // Sort rooms by distance from center to get good distribution
  const centerX = Math.floor(state.width / 2);
  const centerY = Math.floor(state.height / 2);
  rooms.sort((a, b) => {
    const distA =
      Math.abs(a.x + a.w / 2 - centerX) + Math.abs(a.y + a.h / 2 - centerY);
    const distB =
      Math.abs(b.x + b.w / 2 - centerX) + Math.abs(b.y + b.h / 2 - centerY);
    return distA - distB;
  });

  // Place up stairs in a room near the edge (if we have a previous level)
  if (state.level > 0 && rooms.length >= 2) {
    const upRoom = rooms[0]; // Closest to center
    state.stairsUpX = upRoom.x + Math.floor(upRoom.w / 2);
    state.stairsUpY = upRoom.y + Math.floor(upRoom.h / 2);
    state.tiles[state.stairsUpY][state.stairsUpX].type = TileType.STAIRS_UP;
  }

  // Place down stairs in a room farther from center
  if (rooms.length >= 2) {
    const downRoom = rooms[rooms.length - 1]; // Farthest from center
    state.stairsDownX = downRoom.x + Math.floor(downRoom.w / 2);
    state.stairsDownY = downRoom.y + Math.floor(downRoom.h / 2);
    state.tiles[state.stairsDownY][state.stairsDownX].type =
      TileType.STAIRS_DOWN;
  }
}
