/** Shared types and enums for the NetHack-style tile-based dungeon crawler.
 *
 * Extracted from `dungeon_crawler.ts` (module-size policy, AGENTS.md §6).
 * This is the leaf module of the dungeon-crawler split: it has no internal
 * dependencies, so `dungeon_crawler_generation.ts`, `dungeon_crawler_actions.ts`
 * and `dungeon_crawler_core.ts` can all import from it without cycles.
 */

/** Tile types for the dungeon map */
export const enum TileType {
  WALL = "#",
  FLOOR = ".",
  DOOR = "+",
  STAIRS_UP = "<",
  STAIRS_DOWN = ">",
}

/** Entity types that can exist in the dungeon */
export const enum EntityType {
  PLAYER = "@",
  MONSTER = "M",
  ITEM = "!",
  TRAP = "^",
  STAIRS_UP = "<",
  STAIRS_DOWN = ">",
  DOOR_CLOSED = "+",
  DOOR_OPEN = "/",
}

/** Item types */
export const enum ItemType {
  HEALTH_POTION = "!",
  ENERGY_CELL = "e",
  DATA_CHIP = "d",
  WEAPON = "w",
  ARMOR = "a",
}

/** Monster types */
export const enum MonsterType {
  ICE_WATCHDOG = "w",
  ICE_SPIDER = "s",
  ICE_LOA_PRIEST = "l",
  ICE_GOLIATH = "g",
  ICE_BLACK = "B",
}

/** A single tile in the dungeon */
export interface DungeonTile {
  type: TileType;
  explored: boolean; // Has the player ever seen this tile?
  visible: boolean; // Is the tile currently in field of view?
}

/** An entity (player, monster, item, etc.) in the dungeon */
export interface DungeonEntity {
  id: string;
  x: number;
  y: number;
  type: EntityType;
  subtype?: ItemType | MonsterType; // More specific type
  hp: number;
  maxHp?: number;
  hostile?: boolean;
}

/** The dungeon game state */
export interface DungeonState {
  width: number;
  height: number;
  tiles: DungeonTile[][]; // [y][x] - row-major for easier access
  entities: DungeonEntity[];
  playerX: number;
  playerY: number;
  playerHp: number;
  playerMaxHp: number;
  playerAlarm: number; // 0-100
  turnCount: number;
  missionId: string;
  missionGrade: number;
  characterRef: "novice" | "veteran" | "heretic";
  // Fog of war / exploration
  exploredMap: boolean[][]; // What the player has seen
  // Stairs for level transitions
  stairsUpX: number | null;
  stairsUpY: number | null;
  stairsDownX: number | null;
  stairsDownY: number | null;
  // Current level
  level: number;
  maxLevel: number;
}
