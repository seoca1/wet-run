/** Dungeon-crawler entity placement and field-of-view.
 *
 * Extracted from `dungeon_crawler.ts` (module-size policy, AGENTS.md §6).
 * Owns monster/item/trap spawning, player entry placement, and the simple
 * circular FOV + Bresenham line-of-sight used by the renderer. Every function
 * is a pure helper over an explicit `DungeonState`.
 */

import type { Rng, RngInt } from "./dungeon.ts";
import { DungeonGraph } from "./dungeon.ts";
import {
  TileType,
  EntityType,
  ItemType,
  MonsterType,
} from "./dungeon_crawler_types.ts";
import type { DungeonState } from "./dungeon_crawler_types.ts";

/** Place entities (monsters, items, traps) in the dungeon */
export function placeEntities(
  state: DungeonState,
  rng: Rng,
  rngInt: RngInt,
): void {
  // Collect all floor tiles where we can place entities
  const floorPositions: { x: number; y: number }[] = [];
  for (let y = 0; y < state.height; y++) {
    for (let x = 0; x < state.width; x++) {
      if (state.tiles[y][x].type === TileType.FLOOR) {
        floorPositions.push({ x, y });
      }
    }
  }

  if (floorPositions.length === 0) return;

  // Place monsters based on character ref and level
  const monsterCount = getMonsterCount(state);
  for (let i = 0; i < Math.min(monsterCount, floorPositions.length); i++) {
    const pos = getRandomFloorPosition(rngInt, floorPositions);
    if (pos) {
      addMonster(state, rng, pos.x, pos.y);
      // Remove this position from available spots to avoid stacking
      const index = floorPositions.findIndex(
        (p) => p.x === pos.x && p.y === pos.y,
      );
      if (index !== -1) floorPositions.splice(index, 1);
    }
  }

  // Place items
  const itemCount = getItemCount(state);
  for (let i = 0; i < Math.min(itemCount, floorPositions.length); i++) {
    const pos = getRandomFloorPosition(rngInt, floorPositions);
    if (pos) {
      addItem(state, rng, pos.x, pos.y);
      const index = floorPositions.findIndex(
        (p) => p.x === pos.x && p.y === pos.y,
      );
      if (index !== -1) floorPositions.splice(index, 1);
    }
  }

  // Place traps (less common)
  const trapCount = Math.floor(state.level * 0.5) + 1;
  for (let i = 0; i < Math.min(trapCount, floorPositions.length); i++) {
    const pos = getRandomFloorPosition(rngInt, floorPositions);
    if (pos) {
      addTrap(state, pos.x, pos.y);
      const index = floorPositions.findIndex(
        (p) => p.x === pos.x && p.y === pos.y,
      );
      if (index !== -1) floorPositions.splice(index, 1);
    }
  }
}

/** Get a random floor position from the available positions */
export function getRandomFloorPosition(
  rngInt: RngInt,
  positions: { x: number; y: number }[],
): { x: number; y: number } | null {
  if (positions.length === 0) return null;
  const index = rngInt(0, positions.length - 1);
  return positions[index];
}

/** Get monster count based on level and character ref */
export function getMonsterCount(state: DungeonState): number {
  const baseCount = state.level + 2;
  const charMultiplier =
    state.characterRef === "novice"
      ? 0.5
      : state.characterRef === "veteran"
        ? 1.0
        : 1.5; // heretic
  return Math.floor(baseCount * charMultiplier);
}

/** Get item count based on level */
export function getItemCount(state: DungeonState): number {
  return Math.floor(state.level * 0.3) + 2;
}

/** Add a monster at the specified position */
export function addMonster(
  state: DungeonState,
  rng: Rng,
  x: number,
  y: number,
): void {
  // Determine monster type based on level and character ref
  let monsterType: MonsterType;
  const roll = rng();

  if (state.characterRef === "novice") {
    if (roll < 0.7) monsterType = MonsterType.ICE_WATCHDOG;
    else if (roll < 0.9) monsterType = MonsterType.ICE_SPIDER;
    else monsterType = MonsterType.ICE_LOA_PRIEST;
  } else if (state.characterRef === "veteran") {
    if (roll < 0.5) monsterType = MonsterType.ICE_WATCHDOG;
    else if (roll < 0.8) monsterType = MonsterType.ICE_SPIDER;
    else if (roll < 0.95) monsterType = MonsterType.ICE_LOA_PRIEST;
    else monsterType = MonsterType.ICE_GOLIATH;
  } else {
    // heretic
    if (roll < 0.3) monsterType = MonsterType.ICE_WATCHDOG;
    else if (roll < 0.6) monsterType = MonsterType.ICE_SPIDER;
    else if (roll < 0.8) monsterType = MonsterType.ICE_LOA_PRIEST;
    else if (roll < 0.95) monsterType = MonsterType.ICE_GOLIATH;
    else monsterType = MonsterType.ICE_BLACK;
  }

  const monsterHp = getMonsterHp(state, monsterType);

  state.entities.push({
    id: `monster_${state.entities.length}_${Date.now()}`,
    x,
    y,
    type: EntityType.MONSTER,
    subtype: monsterType,
    hp: monsterHp,
    maxHp: monsterHp,
    hostile: true,
  });
}

/** Get HP for a monster type */
export function getMonsterHp(state: DungeonState, type: MonsterType): number {
  switch (type) {
    case MonsterType.ICE_WATCHDOG:
      return 15 + state.level * 2;
    case MonsterType.ICE_SPIDER:
      return 12 + state.level * 2;
    case MonsterType.ICE_LOA_PRIEST:
      return 20 + state.level * 3;
    case MonsterType.ICE_GOLIATH:
      return 30 + state.level * 4;
    case MonsterType.ICE_BLACK:
      return 50 + state.level * 5;
    default:
      return 10;
  }
}

/** Add an item at the specified position */
export function addItem(
  state: DungeonState,
  rng: Rng,
  x: number,
  y: number,
): void {
  // Determine item type based on level
  let itemType: ItemType;
  const roll = rng();

  if (roll < 0.4) itemType = ItemType.HEALTH_POTION;
  else if (roll < 0.7) itemType = ItemType.ENERGY_CELL;
  else if (roll < 0.9) itemType = ItemType.DATA_CHIP;
  else if (roll < 0.95) itemType = ItemType.WEAPON;
  else itemType = ItemType.ARMOR;

  state.entities.push({
    id: `item_${state.entities.length}_${Date.now()}`,
    x,
    y,
    type: EntityType.ITEM,
    subtype: itemType,
    hp: 0,
  });
}

/** Add a trap at the specified position */
export function addTrap(state: DungeonState, x: number, y: number): void {
  state.entities.push({
    id: `trap_${state.entities.length}_${Date.now()}`,
    x,
    y,
    type: EntityType.TRAP,
    hp: 0,
  });
}

/** Place the player at the entry point */
export function placePlayerAtEntry(
  state: DungeonState,
  graph: DungeonGraph,
): void {
  // Find the entry room (marked as "entry" roomType)
  const entryRoom = graph.rooms.find((r) => r.roomType === "entry");
  if (entryRoom) {
    // Place player in the center of the entry room
    state.playerX = entryRoom.x + Math.floor(entryRoom.w / 2);
    state.playerY = entryRoom.y + Math.floor(entryRoom.h / 2);
  } else {
    // Fallback: place at first room center
    if (graph.rooms.length > 0) {
      const firstRoom = graph.rooms[0];
      state.playerX = firstRoom.x + Math.floor(firstRoom.w / 2);
      state.playerY = firstRoom.y + Math.floor(firstRoom.h / 2);
    } else {
      // Ultimate fallback: center of map
      state.playerX = Math.floor(state.width / 2);
      state.playerY = Math.floor(state.height / 2);
    }
  }
}

/** Update field of view and explored map */
export function updateFov(state: DungeonState): void {
  // Simple FOV: illuminate tiles in a radius around player
  // In a full implementation, we'd use proper shadowcasting
  const radius = 6 + Math.floor(state.level * 0.5); // Increase FOV with level

  // Reset visibility
  for (let y = 0; y < state.height; y++) {
    for (let x = 0; x < state.width; x++) {
      state.tiles[y][x].visible = false;
    }
  }

  // Calculate visible tiles (simple circular FOV for now)
  for (let y = -radius; y <= radius; y++) {
    for (let x = -radius; x <= radius; x++) {
      const worldX = state.playerX + x;
      const worldY = state.playerY + y;

      // Check bounds
      if (
        worldX < 0 ||
        worldX >= state.width ||
        worldY < 0 ||
        worldY >= state.height
      ) {
        continue;
      }

      // Check if within radius (circular)
      const distance = Math.sqrt(x * x + y * y);
      if (distance > radius) continue;

      // Check line of sight
      if (isTileVisibleFromPlayer(state, worldX, worldY)) {
        state.tiles[worldY][worldX].visible = true;
        state.exploredMap[worldY][worldX] = true; // Mark as explored
      }
    }
  }
}

/** Check if a tile is visible from player position (line-of-sight check) */
export function isTileVisibleFromPlayer(
  state: DungeonState,
  targetX: number,
  targetY: number,
): boolean {
  // Bresenham's line algorithm for line of sight
  let x0 = state.playerX;
  let y0 = state.playerY;
  const x1 = targetX;
  const y1 = targetY;

  const dx = Math.abs(x1 - x0);
  const dy = Math.abs(y1 - y0);
  const sx = x0 < x1 ? 1 : -1;
  const sy = y0 < y1 ? 1 : -1;
  let err = dx - dy;

  while (true) {
    // Check if current tile blocks vision
    if (state.tiles[y0][x0].type === TileType.WALL) {
      // Don't allow seeing through walls
      return false;
    }

    if (x0 === x1 && y0 === y1) {
      // Reached target
      break;
    }

    const e2 = 2 * err;
    if (e2 > -dy) {
      err -= dy;
      x0 += sx;
    }
    if (e2 < dx) {
      err += dx;
      y0 += sy;
    }
  }

  return true; // No blocking walls found
}
