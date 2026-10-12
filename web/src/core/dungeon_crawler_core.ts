/** NetHack-style tile-based dungeon crawler mode — public facade + factory.
 *
 * The world-generation helpers live in `dungeon_crawler_generation.ts`, entity
 * placement + FOV in `dungeon_crawler_entities.ts`, and player actions in
 * `dungeon_crawler_actions.ts`. This module keeps the public `DungeonCrawler`
 * class, the simple monster AI that drives its turn loop, and the mission
 * factory, so the original import path (`dungeon_crawler.ts`) can re-export
 * them unchanged.
 *
 * Implements a true roguelike dungeon experience with:
 * - Tile-based grid movement (not node-based)
 * - Procedural BSP dungeon generation with rooms and corridors
 * - Fog of war / exploration system
 * - Entity system (monsters, items, traps, stairs)
 * - Turn-based combat and action system
 * - Integration with existing game flow and state
 */

import type { Rng, RngInt } from "./dungeon.ts";
import { ProceduralDungeonGenerator } from "./dungeon.ts";
import type { Mission } from "./types.ts";
import { TileType, EntityType, MonsterType } from "./dungeon_crawler_types.ts";
import type { DungeonState, DungeonEntity } from "./dungeon_crawler_types.ts";
import {
  createRng,
  withInt,
  initializeDungeonState,
  generateLevel,
} from "./dungeon_crawler_generation.ts";
import { updateFov } from "./dungeon_crawler_entities.ts";
import {
  tryMovePlayer,
  updateDoors,
  playerTakeDamage,
  getMonsterDamage,
} from "./dungeon_crawler_actions.ts";

/** String hashCode function for mission-based seeding (mirrors Python's hash) */
function stringHashCode(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
}

/** Try to move a monster */
export function tryMoveMonster(
  state: DungeonState,
  entity: DungeonEntity,
  dx: number,
  dy: number,
): boolean {
  const newX = entity.x + dx;
  const newY = entity.y + dy;

  // Check bounds
  if (newX < 0 || newX >= state.width || newY < 0 || newY >= state.height) {
    return false;
  }

  // Check if tile is walkable
  const tile = state.tiles[newY][newX];
  if (tile.type === TileType.WALL) {
    return false;
  }

  // Check if tile is occupied by another entity
  const occupied = state.entities.some(
    (e) => e !== entity && e.x === newX && e.y === newY,
  );

  if (occupied) {
    return false;
  }

  // Move the monster
  entity.x = newX;
  entity.y = newY;
  return true;
}

/** Simple monster AI */
export function processMonsterAi(state: DungeonState, rng: Rng): void {
  for (const entity of state.entities) {
    if (
      entity.type === EntityType.MONSTER &&
      entity.hostile &&
      entity.hp > 0
    ) {
      // Simple AI: if player is adjacent, attack; otherwise move toward player
      const dx = Math.abs(entity.x - state.playerX);
      const dy = Math.abs(entity.y - state.playerY);

      if (dx <= 1 && dy <= 1) {
        // Adjacent - attack player
        playerTakeDamage(
          state,
          getMonsterDamage(state, entity.subtype as MonsterType),
        );
      } else if (dx + dy > 1) {
        // Not adjacent - try to move toward player
        const moveX =
          state.playerX > entity.x
            ? 1
            : state.playerX < entity.x
              ? -1
              : 0;
        const moveY =
          state.playerY > entity.y
            ? 1
            : state.playerY < entity.y
              ? -1
              : 0;

        // Try to move diagonally first if both axes need movement
        if (moveX !== 0 && moveY !== 0 && rng() < 0.7) {
          // Try diagonal move
          if (tryMoveMonster(state, entity, moveX, moveY)) {
            continue; // Moved successfully
          }
        }

        // Try horizontal move
        if (moveX !== 0 && tryMoveMonster(state, entity, moveX, 0)) {
          continue;
        }

        // Try vertical move
        if (moveY !== 0 && tryMoveMonster(state, entity, 0, moveY)) {
          continue;
        }
      }
    }
  }
}

/** Create a new dungeon crawler instance */
export class DungeonCrawler {
  private _state: DungeonState;
  private rng: Rng;
  private rngInt: RngInt;
  private generator: ProceduralDungeonGenerator;
  private mission: Mission | null = null;

  constructor(seed: number, mission: Mission | null = null) {
    this.mission = mission;
    this.rng = createRng(seed, mission?.id ?? null);
    this.rngInt = withInt(this.rng);
    this.generator = new ProceduralDungeonGenerator(2, 1); // minLeafSize=2, roomPadding=1
    this._state = initializeDungeonState(mission);
    generateLevel(this._state, this.generator, this.rng, this.rngInt, 0);
    // Reveal the player's starting tile + apply initial FOV so first render shows something.
    this._state.exploredMap[this._state.playerY][this._state.playerX] = true;
    updateFov(this._state);
  }

  /** Public getter for dungeon state (read-only access for renderers) */
  public get state(): Readonly<DungeonState> {
    return this._state;
  }

  /** Update field of view and explored map */
  public updateFov(): void {
    updateFov(this._state);
  }

  /** Handle player movement */
  public tryMovePlayer(dx: number, dy: number): boolean {
    return tryMovePlayer(
      this._state,
      this.rng,
      this.rngInt,
      this.generator,
      dx,
      dy,
    );
  }

  /** Close a door after some time (called periodically) */
  public updateDoors(): void {
    updateDoors(this._state, this.rng);
  }

  /** Get the tile type for rendering */
  public getTileType(x: number, y: number): TileType {
    if (x < 0 || x >= this._state.width || y < 0 || y >= this._state.height) {
      return TileType.WALL;
    }
    return this._state.tiles[y][x].type;
  }

  /** Check if a tile is explored */
  public isTileExplored(x: number, y: number): boolean {
    if (x < 0 || x >= this._state.width || y < 0 || y >= this._state.height) {
      return false;
    }
    return this._state.exploredMap[y][x];
  }

  /** Check if a tile is currently visible */
  public isTileVisible(x: number, y: number): boolean {
    if (x < 0 || x >= this._state.width || y < 0 || y >= this._state.height) {
      return false;
    }
    return this._state.tiles[y][x].visible;
  }

  /** Get entities at a position */
  public getEntitiesAt(x: number, y: number): DungeonEntity[] {
    return this._state.entities.filter((e) => e.x === x && e.y === y);
  }

  /** Get player position */
  public getPlayerPosition(): { x: number; y: number } {
    return { x: this._state.playerX, y: this._state.playerY };
  }

  /** Get player stats */
  public getPlayerStats(): {
    hp: number;
    maxHp: number;
    alarm: number;
    level: number;
    turnCount: number;
  } {
    return {
      hp: this._state.playerHp,
      maxHp: this._state.playerMaxHp,
      alarm: this._state.playerAlarm,
      level: this._state.level,
      turnCount: this._state.turnCount,
    };
  }

  /** Check if game is over (player dead) */
  public isGameOver(): boolean {
    return this._state.playerHp <= 0;
  }

  /** Get stairs positions */
  public getStairsUp(): { x: number | null; y: number | null } {
    return { x: this._state.stairsUpX, y: this._state.stairsUpY };
  }

  public getStairsDown(): { x: number | null; y: number | null } {
    return { x: this._state.stairsDownX, y: this._state.stairsDownY };
  }

  /** Process one game turn (call periodically) */
  public processTurn(): void {
    // Update doors
    updateDoors(this._state, this.rng);

    // Monster AI - simple version: move toward player if they can see them
    processMonsterAi(this._state, this.rng);

    // Update FOV
    updateFov(this._state);
  }

  /** Confirm action - transitions from approach phase to combat phase */
  public confirm(): void {
    if (this.mission) {
      this.mission.runPhase = "combat";
    }
  }

  /** Cancel action - exit dungeon and return to menu */
  public cancel(): void {
    if (this.mission) {
      this.mission.runPhase = "matrix";
    }
  }
}

/** Factory function to create a dungeon crawler from a mission.
 *
 * Pass `seed` for a deterministic layout (used by tests); otherwise the seed is
 * derived from the mission id and the current time so each run differs.
 */
export function createDungeonCrawlerFromMission(
  mission: Mission | null = null,
  seed?: number,
): DungeonCrawler {
  const resolvedSeed =
    seed ?? Date.now() + (mission ? stringHashCode(mission.id) : 0);
  return new DungeonCrawler(resolvedSeed, mission);
}
