/** Dungeon-crawler player actions: movement, combat, traps, and doors.
 *
 * Extracted from `dungeon_crawler.ts` (module-size policy, AGENTS.md §6).
 * Monster AI lives in `dungeon_crawler_core.ts` (it drives the facade's turn
 * loop). Every function here is a pure helper over an explicit `DungeonState`
 * (plus the RNG / generator it needs), so the `DungeonCrawler` facade can
 * delegate without changing behaviour.
 */

import type { Rng, RngInt } from "./dungeon.ts";
import { ProceduralDungeonGenerator } from "./dungeon.ts";
import {
  TileType,
  EntityType,
  ItemType,
  MonsterType,
} from "./dungeon_crawler_types.ts";
import type { DungeonState, DungeonEntity } from "./dungeon_crawler_types.ts";
import { generateLevel } from "./dungeon_crawler_generation.ts";
import {
  addItem,
  addMonster,
  getRandomFloorPosition,
  updateFov,
} from "./dungeon_crawler_entities.ts";

/** Get damage for a monster type */
export function getMonsterDamage(
  state: DungeonState,
  type: MonsterType | undefined,
): number {
  if (!type) return 5;
  switch (type) {
    case MonsterType.ICE_WATCHDOG:
      return 3 + Math.floor(state.level * 0.3);
    case MonsterType.ICE_SPIDER:
      return 4 + Math.floor(state.level * 0.4);
    case MonsterType.ICE_LOA_PRIEST:
      return 2 + Math.floor(state.level * 0.2); // Low damage but special effects
    case MonsterType.ICE_GOLIATH:
      return 6 + Math.floor(state.level * 0.5);
    case MonsterType.ICE_BLACK:
      return 8 + Math.floor(state.level * 0.6);
    default:
      return 5;
  }
}

/** Handle player death */
export function handlePlayerDeath(state: DungeonState): void {
  // In a full implementation, this would trigger game over sequence
  // For now, just reset to entrance with penalty
  state.playerHp = Math.floor(state.playerMaxHp * 0.5); // Come back with half HP
  state.playerAlarm = Math.min(100, state.playerAlarm + 25); // Increase alarm

  // Optionally: send back to previous level or apply other penalties
}

/** Player takes damage */
export function playerTakeDamage(state: DungeonState, damage: number): void {
  state.playerHp = Math.max(0, state.playerHp - damage);

  // Check for player death
  if (state.playerHp <= 0) {
    handlePlayerDeath(state);
  }
}

/** Attack an entity (typically a monster) */
export function attackEntity(
  state: DungeonState,
  rng: Rng,
  entity: DungeonEntity,
): void {
  if (!entity.hostile) return;

  // Player attack damage (based on level and equipment)
  const damage = Math.max(1, 5 + Math.floor(state.level * 0.5));

  entity.hp -= damage;

  if (entity.hp <= 0) {
    // Monster defeated
    entity.hp = 0;
    // Chance to drop items
    if (rng() < 0.3) {
      addItem(state, rng, entity.x, entity.y);
    }
    // Remove dead entity after a short delay (for now, remove immediately)
    const index = state.entities.indexOf(entity);
    if (index !== -1) {
      state.entities.splice(index, 1);
    }
  }

  // Monster gets to attack back if still alive
  if (entity.hp > 0 && rng() < 0.5) {
    // 50% chance to retaliate
    playerTakeDamage(state, getMonsterDamage(state, entity.subtype as MonsterType));
  }
}

/** Pick up an item */
export function pickUpItem(state: DungeonState, item: DungeonEntity): void {
  switch (item.subtype) {
    case ItemType.HEALTH_POTION:
      state.playerHp = Math.min(state.playerMaxHp, state.playerHp + 25);
      break;
    case ItemType.ENERGY_CELL:
      state.playerAlarm = Math.max(0, state.playerAlarm - 15);
      break;
    case ItemType.DATA_CHIP:
      // Data chips give credits or special abilities
      state.playerHp = Math.min(state.playerMaxHp, state.playerHp + 10);
      break;
    case ItemType.WEAPON:
      // Temporary attack boost
      break;
    case ItemType.ARMOR:
      // Temporary defense boost
      break;
  }
}

/** Teleport player to a random safe location */
export function teleportPlayerRandomly(
  state: DungeonState,
  rngInt: RngInt,
): void {
  const floorPositions: { x: number; y: number }[] = [];
  for (let y = 0; y < state.height; y++) {
    for (let x = 0; x < state.width; x++) {
      if (state.tiles[y][x].type === TileType.FLOOR) {
        // Check if not occupied by hostile entity
        const occupied = state.entities.some(
          (e) => e.x === x && e.y === y && e.hostile === true,
        );
        if (!occupied) {
          floorPositions.push({ x, y });
        }
      }
    }
  }

  if (floorPositions.length > 0) {
    const pos = getRandomFloorPosition(rngInt, floorPositions);
    if (pos) {
      state.playerX = pos.x;
      state.playerY = pos.y;
    }
  }
}

/** Summon a monster near the player */
export function summonMonsterNearPlayer(state: DungeonState, rng: Rng): void {
  // Try to find a spot near the player
  for (let dy = -2; dy <= 2; dy++) {
    for (let dx = -2; dx <= 2; dx++) {
      const x = state.playerX + dx;
      const y = state.playerY + dy;

      if (x >= 0 && x < state.width && y >= 0 && y < state.height) {
        const tile = state.tiles[y][x];
        if (tile.type === TileType.FLOOR) {
          // Check if not occupied
          const occupied = state.entities.some((e) => e.x === x && e.y === y);
          if (!occupied) {
            addMonster(state, rng, x, y);
            return; // Only summon one monster
          }
        }
      }
    }
  }
}

/** Trigger a trap */
export function triggerTrap(
  state: DungeonState,
  rng: Rng,
  rngInt: RngInt,
  _trap: DungeonEntity,
): void {
  // Different trap types based on level
  const trapRoll = rng();

  if (trapRoll < 0.3) {
    // Damage trap
    const damage = 10 + state.level * 2;
    state.playerHp = Math.max(0, state.playerHp - damage);
  } else if (trapRoll < 0.6) {
    // Alarm trap
    state.playerAlarm = Math.min(100, state.playerAlarm + 20);
  } else if (trapRoll < 0.8) {
    // Teleport trap
    teleportPlayerRandomly(state, rngInt);
  } else {
    // Monster summon trap
    summonMonsterNearPlayer(state, rng);
  }
}

/** Check for entity interactions (pick up items, trigger traps) */
export function checkForEntityInteractions(
  state: DungeonState,
  rng: Rng,
  rngInt: RngInt,
): void {
  // Check for items at player position
  const itemIndex = state.entities.findIndex(
    (e) =>
      e.x === state.playerX &&
      e.y === state.playerY &&
      e.type === EntityType.ITEM,
  );

  if (itemIndex !== -1) {
    const item = state.entities[itemIndex];
    pickUpItem(state, item);
    state.entities.splice(itemIndex, 1);
  }

  // Check for traps at player position
  const trapIndex = state.entities.findIndex(
    (e) =>
      e.x === state.playerX &&
      e.y === state.playerY &&
      e.type === EntityType.TRAP,
  );

  if (trapIndex !== -1) {
    const trap = state.entities[trapIndex];
    triggerTrap(state, rng, rngInt, trap);
    state.entities.splice(trapIndex, 1);
  }
}

/** Change dungeon level */
export function changeLevel(
  state: DungeonState,
  generator: ProceduralDungeonGenerator,
  rng: Rng,
  rngInt: RngInt,
  delta: number,
): void {
  const newLevel = state.level + delta;

  // Prevent going below level 0
  if (newLevel < 0) return;

  // Generate new level
  generateLevel(state, generator, rng, rngInt, newLevel);

  // Position player on stairs
  if (delta > 0) {
    // Going down - place player on up stairs of new level
    if (state.stairsUpX !== null && state.stairsUpY !== null) {
      state.playerX = state.stairsUpX;
      state.playerY = state.stairsUpY;
    }
  } else {
    // Going up - place player on down stairs of new level
    if (state.stairsDownX !== null && state.stairsDownY !== null) {
      state.playerX = state.stairsDownX;
      state.playerY = state.stairsDownY;
    }
  }

  // Reset alarm when changing levels (slightly)
  state.playerAlarm = Math.max(0, state.playerAlarm - 10);
}

/** Check if player is on stairs */
export function checkForStairs(
  state: DungeonState,
  generator: ProceduralDungeonGenerator,
  rng: Rng,
  rngInt: RngInt,
): void {
  const tile = state.tiles[state.playerY][state.playerX];

  if (
    tile.type === TileType.STAIRS_UP &&
    state.stairsUpX !== null &&
    state.stairsUpY !== null
  ) {
    if (
      state.playerX === state.stairsUpX &&
      state.playerY === state.stairsUpY
    ) {
      // Go up a level
      changeLevel(state, generator, rng, rngInt, -1);
    }
  }

  if (
    tile.type === TileType.STAIRS_DOWN &&
    state.stairsDownX !== null &&
    state.stairsDownY !== null
  ) {
    if (
      state.playerX === state.stairsDownX &&
      state.playerY === state.stairsDownY
    ) {
      // Go down a level
      changeLevel(state, generator, rng, rngInt, 1);
    }
  }
}

/** Handle player movement */
export function tryMovePlayer(
  state: DungeonState,
  rng: Rng,
  rngInt: RngInt,
  generator: ProceduralDungeonGenerator,
  dx: number,
  dy: number,
): boolean {
  const newX = state.playerX + dx;
  const newY = state.playerY + dy;

  // Check bounds
  if (newX < 0 || newX >= state.width || newY < 0 || newY >= state.height) {
    return false;
  }

  // Check if tile is walkable
  const tile = state.tiles[newY][newX];
  if (tile.type === TileType.WALL) {
    return false;
  }

  // Check for entities blocking movement
  const blockingEntity = state.entities.find(
    (e) =>
      e.x === newX &&
      e.y === newY &&
      (e.type === EntityType.MONSTER || e.type === EntityType.DOOR_CLOSED),
  );

  if (blockingEntity) {
    // Try to attack if it's a monster
    if (blockingEntity.type === EntityType.MONSTER) {
      attackEntity(state, rng, blockingEntity);
      return false; // Don't move into the monster's space
    }
    // For closed doors, try to open them
    if (blockingEntity.type === EntityType.DOOR_CLOSED) {
      openDoor(blockingEntity);
      return false; // Don't move yet
    }
    return false; // Blocked by something else
  }

  // Move the player
  state.playerX = newX;
  state.playerY = newY;

  // Check for stairs
  checkForStairs(state, generator, rng, rngInt);

  // Check for entity interactions (items, traps)
  checkForEntityInteractions(state, rng, rngInt);

  // Increment turn
  state.turnCount++;

  // Update FOV
  updateFov(state);

  // Apply alarm increase for movement
  state.playerAlarm = Math.min(100, state.playerAlarm + 1);

  return true;
}

/** Open a door */
export function openDoor(entity: DungeonEntity): void {
  entity.type = EntityType.DOOR_OPEN;
  // Door stays open for a few turns then closes automatically
  // For simplicity, we'll just leave it open
}

/** Close a door after some time (called periodically) */
export function updateDoors(state: DungeonState, rng: Rng): void {
  // Simple door closing logic - in reality would have timers
  for (const entity of state.entities) {
    if (entity.type === EntityType.DOOR_OPEN) {
      // 10% chance per turn to close
      if (rng() < 0.1) {
        entity.type = EntityType.DOOR_CLOSED;
      }
    }
  }
}
