/** NetHack-style tile-based dungeon crawler mode.
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
import { ProceduralDungeonGenerator, DungeonGraph } from "./dungeon.ts";
import { Mission } from "./types.ts";

/** String hashCode function for mission-based seeding (mirrors Python's hash) */
function stringHashCode(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
}

/** Tile types for the dungeon map */
export const enum TileType {
  WALL = '#',
  FLOOR = '.',
  DOOR = '+',
  STAIRS_UP = '<',
  STAIRS_DOWN = '>',
}

/** Entity types that can exist in the dungeon */
export const enum EntityType {
  PLAYER = '@',
  MONSTER = 'M',
  ITEM = '!',
  TRAP = '^',
  STAIRS_UP = '<',
  STAIRS_DOWN = '>',
  DOOR_CLOSED = '+',
  DOOR_OPEN = '/',
}

/** Item types */
export const enum ItemType {
  HEALTH_POTION = '!',
  ENERGY_CELL = 'e',
  DATA_CHIP = 'd',
  WEAPON = 'w',
  ARMOR = 'a',
}

/** Monster types */
export const enum MonsterType {
  ICE_WATCHDOG = 'w',
  ICE_SPIDER = 's',
  ICE_LOA_PRIEST = 'l',
  ICE_GOLIATH = 'g',
  ICE_BLACK = 'B',
}

/** A single tile in the dungeon */
export interface DungeonTile {
  type: TileType;
  explored: boolean; // Has the player ever seen this tile?
  visible: boolean;  // Is the tile currently in field of view?
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

/** Create a new dungeon crawler instance */
export class DungeonCrawler {
  private _state: DungeonState;
  private rng: Rng;
  private rngInt: RngInt;
  private generator: ProceduralDungeonGenerator;
  private mission: Mission | null = null;

  constructor(seed: number, mission: Mission | null = null) {
    this.mission = mission;
    this.rng = this.createRng(seed, mission?.id ?? null);
    this.rngInt = this.withInt(this.rng);
    this.generator = new ProceduralDungeonGenerator(2, 1); // minLeafSize=2, roomPadding=1
    this._state = this.initializeDungeonState();
    this.generateFirstLevel();
    // Reveal the player's starting tile + apply initial FOV so first render shows something.
    this._state.exploredMap[this._state.playerY][this._state.playerX] = true;
    this.updateFov();
  }

  /** Public getter for dungeon state (read-only access for renderers) */
  public get state(): Readonly<DungeonState> {
    return this._state;
  }

  /** Create a seeded RNG (mirrors Python hash(id) % 7919) */
  private createRng(seed: number, missionId: string | null): Rng {
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
  private withInt(rng: Rng): RngInt {
    return (min: number, max: number): number => {
      if (max < min) {
        throw new RangeError(`rngInt: max (${max}) < min (${min})`);
      }
      return min + Math.floor(rng() * (max - min + 1));
    };
  }

  /** Initialize the dungeon state with empty values */
  private initializeDungeonState(): DungeonState {
    // Default size - will be resized during generation
    const width = 80;
    const height = 45;
    
    const tiles: DungeonTile[][] = Array.from({ length: height }, () =>
      Array.from({ length: width }, () => ({
        type: TileType.WALL,
        explored: false,
        visible: false,
      }))
    );
    
    const exploredMap: boolean[][] = Array.from({ length: height }, () =>
      Array.from({ length: width }, () => false)
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
      missionId: this.mission?.id ?? "unknown",
      missionGrade: this.mission?.grade_max ?? 1,
      characterRef: this.mission?.grade_max ?? 1 >= 4 ? "heretic" : 
                   this.mission?.grade_max ?? 1 >= 2 ? "veteran" : "novice",
      exploredMap,
      stairsUpX: null,
      stairsUpY: null,
      stairsDownX: null,
      stairsDownY: null,
      level: 0,
      maxLevel: 0,
    };
  }

  /** Generate the first dungeon level */
  private generateFirstLevel(): void {
    this.generateLevel(0);
  }

  /** Generate a dungeon level */
  private generateLevel(levelNum: number): void {
    // Generate dungeon graph using existing BSP system
    const graph: DungeonGraph = this.generator.generate(
      Date.now() + levelNum * 1000, // Different seed per level
      this._state.missionGrade,
      this._state.characterRef
    );
    
    // Resize the dungeon to fit the generated graph
    this._state.width = graph.width;
    this._state.height = graph.height;
    
    // Initialize tiles as walls
    this._state.tiles = Array.from({ length: this._state.height }, () =>
      Array.from({ length: this._state.width }, () => ({
        type: TileType.WALL,
        explored: false,
        visible: false,
      }))
    );
    
    // Reset explored map for new level
    this._state.exploredMap = Array.from({ length: this._state.height }, () =>
      Array.from({ length: this._state.width }, () => false)
    );
    
    // Clear entities (except player who gets repositioned)
    this._state.entities = [];
    
    // Carry over player stats
    const playerHp = this._state.playerHp;
    const playerMaxHp = this._state.playerMaxHp;
    const playerAlarm = this._state.playerAlarm;
    
// Convert rooms and corridors to tiles
     this.digRoomsAndCorridors(graph);
     
     // Place entities (monsters, items, traps, stairs)
     this.placeEntities();
     
     // Place player at entry point
     this.placePlayerAtEntry(graph);
    
    // Restore player stats
    this._state.playerHp = playerHp;
    this._state.playerMaxHp = playerMaxHp;
    this._state.playerAlarm = playerAlarm;
    
    this._state.level = levelNum;
    this._state.maxLevel = Math.max(this._state.maxLevel, levelNum);
    
    // Place stairs
    this.placeStairs(graph);
  }

  /** Convert dungeon rooms and corridors to walkable tiles */
  private digRoomsAndCorridors(graph: DungeonGraph): void {
    // Start with all walls
    for (let y = 0; y < this._state.height; y++) {
      for (let x = 0; x < this._state.width; x++) {
        this._state.tiles[y][x].type = TileType.WALL;
      }
    }
    
    // Dig out rooms
    for (const room of graph.rooms) {
      for (let y = room.y; y < room.y + room.h; y++) {
        for (let x = room.x; x < room.x + room.w; x++) {
          if (y >= 0 && y < this._state.height && x >= 0 && x < this._state.width) {
            // Room interiors are floors
            this._state.tiles[y][x].type = TileType.FLOOR;
            
            // Room walls (edges) - but we'll handle corridors separately for now
            if (y === room.y || y === room.y + room.h - 1 || 
                x === room.x || x === room.x + room.w - 1) {
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
        this.digCorridor(
          firstRoom.x + Math.floor(firstRoom.w / 2),
          firstRoom.y + Math.floor(firstRoom.h / 2),
          room.x + Math.floor(room.w / 2),
          room.y + Math.floor(room.h / 2)
        );
      }
    }
  }

  /** Dig a corridor between two points (L-shaped path) */
  private digCorridor(x1: number, y1: number, x2: number, y2: number): void {
    // Randomly choose whether to go horizontal first or vertical first
    const goHorizontalFirst = this.rng() < 0.5;
    
    if (goHorizontalFirst) {
      // Go horizontally, then vertically
      for (let x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) {
        if (x >= 0 && x < this._state.width && y1 >= 0 && y1 < this._state.height) {
          if (this._state.tiles[y1][x].type === TileType.WALL) {
            this._state.tiles[y1][x].type = TileType.FLOOR;
          }
        }
      }
      for (let y = Math.min(y1, y2); y <= Math.max(y1, y2); y++) {
        if (x2 >= 0 && x2 < this._state.width && y >= 0 && y < this._state.height) {
          if (this._state.tiles[y][x2].type === TileType.WALL) {
            this._state.tiles[y][x2].type = TileType.FLOOR;
          }
        }
      }
    } else {
      // Go vertically, then horizontally
      for (let y = Math.min(y1, y2); y <= Math.max(y1, y2); y++) {
        if (x1 >= 0 && x1 < this._state.width && y >= 0 && y < this._state.height) {
          if (this._state.tiles[y][x1].type === TileType.WALL) {
            this._state.tiles[y][x1].type = TileType.FLOOR;
          }
        }
      }
      for (let x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) {
        if (x >= 0 && x < this._state.width && y2 >= 0 && y2 < this._state.height) {
          if (this._state.tiles[y2][x].type === TileType.WALL) {
            this._state.tiles[y2][x].type = TileType.FLOOR;
          }
        }
      }
    }
  }

/** Place entities (monsters, items, traps) in the dungeon */
    private placeEntities(): void {
        // Collect all floor tiles where we can place entities
        const floorPositions: {x: number; y: number}[] = [];
        for (let y = 0; y < this._state.height; y++) {
            for (let x = 0; x < this._state.width; x++) {
                if (this._state.tiles[y][x].type === TileType.FLOOR) {
                    floorPositions.push({x, y});
                }
            }
        }
        
        if (floorPositions.length === 0) return;
        
        // Place monsters based on character ref and level
        const monsterCount = this.getMonsterCount();
        for (let i = 0; i < Math.min(monsterCount, floorPositions.length); i++) {
            const pos = this.getRandomFloorPosition(floorPositions);
            if (pos) {
                this.addMonster(pos.x, pos.y);
                // Remove this position from available spots to avoid stacking
                const index = floorPositions.findIndex(p => p.x === pos.x && p.y === pos.y);
                if (index !== -1) floorPositions.splice(index, 1);
            }
        }
        
        // Place items
        const itemCount = this.getItemCount();
        for (let i = 0; i < Math.min(itemCount, floorPositions.length); i++) {
            const pos = this.getRandomFloorPosition(floorPositions);
            if (pos) {
                this.addItem(pos.x, pos.y);
                const index = floorPositions.findIndex(p => p.x === pos.x && p.y === pos.y);
                if (index !== -1) floorPositions.splice(index, 1);
            }
        }
        
        // Place traps (less common)
        const trapCount = Math.floor(this._state.level * 0.5) + 1;
        for (let i = 0; i < Math.min(trapCount, floorPositions.length); i++) {
            const pos = this.getRandomFloorPosition(floorPositions);
            if (pos) {
                this.addTrap(pos.x, pos.y);
                const index = floorPositions.findIndex(p => p.x === pos.x && p.y === pos.y);
                if (index !== -1) floorPositions.splice(index, 1);
            }
        }
    }

  /** Get a random floor position from the available positions */
  private getRandomFloorPosition(positions: {x: number; y: number}[]): {x: number; y: number} | null {
    if (positions.length === 0) return null;
    const index = this.rngInt(0, positions.length - 1);
    return positions[index];
  }

  /** Get monster count based on level and character ref */
  private getMonsterCount(): number {
    const baseCount = this._state.level + 2;
    const charMultiplier = 
      this._state.characterRef === "novice" ? 0.5 :
      this._state.characterRef === "veteran" ? 1.0 :
      1.5; // heretic
    return Math.floor(baseCount * charMultiplier);
  }

  /** Get item count based on level */
  private getItemCount(): number {
    return Math.floor(this._state.level * 0.3) + 2;
  }

  /** Add a monster at the specified position */
  private addMonster(x: number, y: number): void {
    // Determine monster type based on level and character ref
    let monsterType: MonsterType;
    const roll = this.rng();
    
    if (this._state.characterRef === "novice") {
      if (roll < 0.7) monsterType = MonsterType.ICE_WATCHDOG;
      else if (roll < 0.9) monsterType = MonsterType.ICE_SPIDER;
      else monsterType = MonsterType.ICE_LOA_PRIEST;
    } else if (this._state.characterRef === "veteran") {
      if (roll < 0.5) monsterType = MonsterType.ICE_WATCHDOG;
      else if (roll < 0.8) monsterType = MonsterType.ICE_SPIDER;
      else if (roll < 0.95) monsterType = MonsterType.ICE_LOA_PRIEST;
      else monsterType = MonsterType.ICE_GOLIATH;
    } else { // heretic
      if (roll < 0.3) monsterType = MonsterType.ICE_WATCHDOG;
      else if (roll < 0.6) monsterType = MonsterType.ICE_SPIDER;
      else if (roll < 0.8) monsterType = MonsterType.ICE_LOA_PRIEST;
      else if (roll < 0.95) monsterType = MonsterType.ICE_GOLIATH;
      else monsterType = MonsterType.ICE_BLACK;
    }
    
    const monsterHp = this.getMonsterHp(monsterType);
    
    this._state.entities.push({
      id: `monster_${this._state.entities.length}_${Date.now()}`,
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
  private getMonsterHp(type: MonsterType): number {
    switch (type) {
      case MonsterType.ICE_WATCHDOG: return 15 + this._state.level * 2;
      case MonsterType.ICE_SPIDER: return 12 + this._state.level * 2;
      case MonsterType.ICE_LOA_PRIEST: return 20 + this._state.level * 3;
      case MonsterType.ICE_GOLIATH: return 30 + this._state.level * 4;
      case MonsterType.ICE_BLACK: return 50 + this._state.level * 5;
      default: return 10;
    }
  }

  /** Add an item at the specified position */
  private addItem(x: number, y: number): void {
    // Determine item type based on level
    let itemType: ItemType;
    const roll = this.rng();
    
    if (roll < 0.4) itemType = ItemType.HEALTH_POTION;
    else if (roll < 0.7) itemType = ItemType.ENERGY_CELL;
    else if (roll < 0.9) itemType = ItemType.DATA_CHIP;
    else if (roll < 0.95) itemType = ItemType.WEAPON;
    else itemType = ItemType.ARMOR;
    
    this._state.entities.push({
      id: `item_${this._state.entities.length}_${Date.now()}`,
      x,
      y,
      type: EntityType.ITEM,
      subtype: itemType,
      hp: 0,
    });
  }

  /** Add a trap at the specified position */
  private addTrap(x: number, y: number): void {
    this._state.entities.push({
      id: `trap_${this._state.entities.length}_${Date.now()}`,
      x,
      y,
      type: EntityType.TRAP,
      hp: 0,
    });
  }

  /** Place the player at the entry point */
  private placePlayerAtEntry(graph: DungeonGraph): void {
    // Find the entry room (marked as "entry" roomType)
    const entryRoom = graph.rooms.find(r => r.roomType === "entry");
    if (entryRoom) {
      // Place player in the center of the entry room
      this._state.playerX = entryRoom.x + Math.floor(entryRoom.w / 2);
      this._state.playerY = entryRoom.y + Math.floor(entryRoom.h / 2);
    } else {
      // Fallback: place at first room center
      if (graph.rooms.length > 0) {
        const firstRoom = graph.rooms[0];
        this._state.playerX = firstRoom.x + Math.floor(firstRoom.w / 2);
        this._state.playerY = firstRoom.y + Math.floor(firstRoom.h / 2);
      } else {
        // Ultimate fallback: center of map
        this._state.playerX = Math.floor(this._state.width / 2);
        this._state.playerY = Math.floor(this._state.height / 2);
      }
    }
  }

  /** Place stairs for level transitions */
  private placeStairs(graph: DungeonGraph): void {
    // Find rooms for up/down stairs
    const rooms = [...graph.rooms];
    
    // Sort rooms by distance from center to get good distribution
    const centerX = Math.floor(this._state.width / 2);
    const centerY = Math.floor(this._state.height / 2);
    rooms.sort((a, b) => {
      const distA = Math.abs(a.x + a.w/2 - centerX) + Math.abs(a.y + a.h/2 - centerY);
      const distB = Math.abs(b.x + b.w/2 - centerX) + Math.abs(b.y + b.h/2 - centerY);
      return distA - distB;
    });
    
    // Place up stairs in a room near the edge (if we have a previous level)
    if (this._state.level > 0 && rooms.length >= 2) {
      const upRoom = rooms[0]; // Closest to center
      this._state.stairsUpX = upRoom.x + Math.floor(upRoom.w / 2);
      this._state.stairsUpY = upRoom.y + Math.floor(upRoom.h / 2);
      this._state.tiles[this._state.stairsUpY][this._state.stairsUpX].type = TileType.STAIRS_UP;
    }
    
    // Place down stairs in a room farther from center
    if (rooms.length >= 2) {
      const downRoom = rooms[rooms.length - 1]; // Farthest from center
      this._state.stairsDownX = downRoom.x + Math.floor(downRoom.w / 2);
      this._state.stairsDownY = downRoom.y + Math.floor(downRoom.h / 2);
      this._state.tiles[this._state.stairsDownY][this._state.stairsDownX].type = TileType.STAIRS_DOWN;
    }
  }

  /** Update field of view and explored map */
  public updateFov(): void {
    // Simple FOV: illuminate tiles in a radius around player
    // In a full implementation, we'd use proper shadowcasting
    const radius = 6 + Math.floor(this._state.level * 0.5); // Increase FOV with level
    
    // Reset visibility
    for (let y = 0; y < this._state.height; y++) {
      for (let x = 0; x < this._state.width; x++) {
        this._state.tiles[y][x].visible = false;
      }
    }
    
    // Calculate visible tiles (simple circular FOV for now)
    for (let y = -radius; y <= radius; y++) {
      for (let x = -radius; x <= radius; x++) {
        const worldX = this._state.playerX + x;
        const worldY = this._state.playerY + y;
        
        // Check bounds
        if (worldX < 0 || worldX >= this._state.width || worldY < 0 || worldY >= this._state.height) {
          continue;
        }
        
        // Check if within radius (circular)
        const distance = Math.sqrt(x * x + y * y);
        if (distance > radius) continue;
        
        // Check line of sight
        if (this.isTileVisibleFromPlayer(worldX, worldY)) {
          this._state.tiles[worldY][worldX].visible = true;
          this._state.exploredMap[worldY][worldX] = true; // Mark as explored
        }
      }
    }
  }

  /** Check if a tile is visible from player position (line-of-sight check) */
  private isTileVisibleFromPlayer(targetX: number, targetY: number): boolean {
    // Bresenham's line algorithm for line of sight
    let x0 = this._state.playerX;
    let y0 = this._state.playerY;
    const x1 = targetX;
    const y1 = targetY;
    
    const dx = Math.abs(x1 - x0);
    const dy = Math.abs(y1 - y0);
    const sx = x0 < x1 ? 1 : -1;
    const sy = y0 < y1 ? 1 : -1;
    let err = dx - dy;
    
    while (true) {
      // Check if current tile blocks vision
      if (this._state.tiles[y0][x0].type === TileType.WALL) {
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

  /** Handle player movement */
  public tryMovePlayer(dx: number, dy: number): boolean {
    const newX = this._state.playerX + dx;
    const newY = this._state.playerY + dy;
    
    // Check bounds
    if (newX < 0 || newX >= this._state.width || newY < 0 || newY >= this._state.height) {
      return false;
    }
    
    // Check if tile is walkable
    const tile = this._state.tiles[newY][newX];
    if (tile.type === TileType.WALL) {
      return false;
    }
    
    // Check for entities blocking movement
    const blockingEntity = this._state.entities.find(
      e => e.x === newX && e.y === newY && 
           (e.type === EntityType.MONSTER || e.type === EntityType.DOOR_CLOSED)
    );
    
    if (blockingEntity) {
      // Try to attack if it's a monster
      if (blockingEntity.type === EntityType.MONSTER) {
        this.attackEntity(blockingEntity);
        return false; // Don't move into the monster's space
      }
      // For closed doors, try to open them
      if (blockingEntity.type === EntityType.DOOR_CLOSED) {
        this.openDoor(blockingEntity);
        return false; // Don't move yet
      }
      return false; // Blocked by something else
    }
    
    // Move the player
    this._state.playerX = newX;
    this._state.playerY = newY;
    
    // Check for stairs
    this.checkForStairs();
    
    // Check for entity interactions (items, traps)
    this.checkForEntityInteractions();
    
    // Increment turn
    this._state.turnCount++;
    
    // Update FOV
    this.updateFov();
    
    // Apply alarm increase for movement
    this._state.playerAlarm = Math.min(100, this._state.playerAlarm + 1);
    
    return true;
  }

  /** Check if player is on stairs */
  private checkForStairs(): void {
    const tile = this._state.tiles[this._state.playerY][this._state.playerX];
    
    if (tile.type === TileType.STAIRS_UP && this._state.stairsUpX !== null && this._state.stairsUpY !== null) {
      if (this._state.playerX === this._state.stairsUpX && this._state.playerY === this._state.stairsUpY) {
        // Go up a level
        this.changeLevel(-1);
      }
    }
    
    if (tile.type === TileType.STAIRS_DOWN && this._state.stairsDownX !== null && this._state.stairsDownY !== null) {
      if (this._state.playerX === this._state.stairsDownX && this._state.playerY === this._state.stairsDownY) {
        // Go down a level
        this.changeLevel(1);
      }
    }
  }

  /** Change dungeon level */
  private changeLevel(delta: number): void {
    const newLevel = this._state.level + delta;
    
    // Prevent going below level 0
    if (newLevel < 0) return;
    
    // Generate new level
    this.generateLevel(newLevel);
    
    // Position player on stairs
    if (delta > 0) {
      // Going down - place player on up stairs of new level
      if (this._state.stairsUpX !== null && this._state.stairsUpY !== null) {
        this._state.playerX = this._state.stairsUpX;
        this._state.playerY = this._state.stairsUpY;
      }
    } else {
      // Going up - place player on down stairs of new level
      if (this._state.stairsDownX !== null && this._state.stairsDownY !== null) {
        this._state.playerX = this._state.stairsDownX;
        this._state.playerY = this._state.stairsDownY;
      }
    }
    
    // Reset alarm when changing levels (slightly)
    this._state.playerAlarm = Math.max(0, this._state.playerAlarm - 10);
  }

  /** Check for entity interactions (pick up items, trigger traps) */
  private checkForEntityInteractions(): void {
    // Check for items at player position
    const itemIndex = this._state.entities.findIndex(
      e => e.x === this._state.playerX && e.y === this._state.playerY && e.type === EntityType.ITEM
    );
    
    if (itemIndex !== -1) {
      const item = this._state.entities[itemIndex];
      this.pickUpItem(item);
      this._state.entities.splice(itemIndex, 1);
    }
    
    // Check for traps at player position
    const trapIndex = this._state.entities.findIndex(
      e => e.x === this._state.playerX && e.y === this._state.playerY && e.type === EntityType.TRAP
    );
    
    if (trapIndex !== -1) {
      const trap = this._state.entities[trapIndex];
      this.triggerTrap(trap);
      this._state.entities.splice(trapIndex, 1);
    }
  }

  /** Pick up an item */
  private pickUpItem(item: DungeonEntity): void {
    switch (item.subtype) {
      case ItemType.HEALTH_POTION:
        this._state.playerHp = Math.min(this._state.playerMaxHp, this._state.playerHp + 25);
        break;
      case ItemType.ENERGY_CELL:
        this._state.playerAlarm = Math.max(0, this._state.playerAlarm - 15);
        break;
      case ItemType.DATA_CHIP:
        // Data chips give credits or special abilities
        this._state.playerHp = Math.min(this._state.playerMaxHp, this._state.playerHp + 10);
        break;
      case ItemType.WEAPON:
        // Temporary attack boost
        break;
      case ItemType.ARMOR:
        // Temporary defense boost
        break;
    }
  }

  /** Trigger a trap */
  private triggerTrap(_trap: DungeonEntity): void {
    // Different trap types based on level
    const trapRoll = this.rng();
    
    if (trapRoll < 0.3) {
      // Damage trap
      const damage = 10 + this._state.level * 2;
      this._state.playerHp = Math.max(0, this._state.playerHp - damage);
    } else if (trapRoll < 0.6) {
      // Alarm trap
      this._state.playerAlarm = Math.min(100, this._state.playerAlarm + 20);
    } else if (trapRoll < 0.8) {
      // Teleport trap
      this.teleportPlayerRandomly();
    } else {
      // Monster summon trap
      this.summonMonsterNearPlayer();
    }
  }

  /** Teleport player to a random safe location */
  private teleportPlayerRandomly(): void {
    const floorPositions: {x: number; y: number}[] = [];
    for (let y = 0; y < this._state.height; y++) {
      for (let x = 0; x < this._state.width; x++) {
        if (this._state.tiles[y][x].type === TileType.FLOOR) {
          // Check if not occupied by hostile entity
          const occupied = this._state.entities.some(
            e => e.x === x && e.y === y && e.hostile === true
          );
          if (!occupied) {
            floorPositions.push({x, y});
          }
        }
      }
    }
    
    if (floorPositions.length > 0) {
      const pos = this.getRandomFloorPosition(floorPositions);
      if (pos) {
        this._state.playerX = pos.x;
        this._state.playerY = pos.y;
      }
    }
  }

  /** Summon a monster near the player */
  private summonMonsterNearPlayer(): void {
    // Try to find a spot near the player
    for (let dy = -2; dy <= 2; dy++) {
      for (let dx = -2; dx <= 2; dx++) {
        const x = this._state.playerX + dx;
        const y = this._state.playerY + dy;
        
        if (x >= 0 && x < this._state.width && y >= 0 && y < this._state.height) {
          const tile = this._state.tiles[y][x];
          if (tile.type === TileType.FLOOR) {
            // Check if not occupied
            const occupied = this._state.entities.some(e => e.x === x && e.y === y);
            if (!occupied) {
              this.addMonster(x, y);
              return; // Only summon one monster
            }
          }
        }
      }
    }
  }

  /** Attack an entity (typically a monster) */
  private attackEntity(entity: DungeonEntity): void {
    if (!entity.hostile) return;
    
    // Player attack damage (based on level and equipment)
    const damage = Math.max(1, 5 + Math.floor(this._state.level * 0.5));
    
    entity.hp -= damage;
    
    if (entity.hp <= 0) {
      // Monster defeated
      entity.hp = 0;
      // Chance to drop items
      if (this.rng() < 0.3) {
        this.addItem(entity.x, entity.y);
      }
      // Remove dead entity after a short delay (for now, remove immediately)
      const index = this._state.entities.indexOf(entity);
      if (index !== -1) {
        this._state.entities.splice(index, 1);
      }
    }
    
    // Monster gets to attack back if still alive
    if (entity.hp > 0 && this.rng() < 0.5) { // 50% chance to retaliate
      this.playerTakeDamage(this.getMonsterDamage(entity.subtype as MonsterType));
    }
  }

  /** Get damage for a monster type */
  private getMonsterDamage(type: MonsterType | undefined): number {
    if (!type) return 5;
    switch (type) {
      case MonsterType.ICE_WATCHDOG: return 3 + Math.floor(this._state.level * 0.3);
      case MonsterType.ICE_SPIDER: return 4 + Math.floor(this._state.level * 0.4);
      case MonsterType.ICE_LOA_PRIEST: return 2 + Math.floor(this._state.level * 0.2); // Low damage but special effects
      case MonsterType.ICE_GOLIATH: return 6 + Math.floor(this._state.level * 0.5);
      case MonsterType.ICE_BLACK: return 8 + Math.floor(this._state.level * 0.6);
      default: return 5;
    }
  }

  /** Player takes damage */
  private playerTakeDamage(damage: number): void {
    this._state.playerHp = Math.max(0, this._state.playerHp - damage);
    
    // Check for player death
    if (this._state.playerHp <= 0) {
      this.handlePlayerDeath();
    }
  }

  /** Handle player death */
  private handlePlayerDeath(): void {
    // In a full implementation, this would trigger game over sequence
    // For now, just reset to entrance with penalty
    this._state.playerHp = Math.floor(this._state.playerMaxHp * 0.5); // Come back with half HP
    this._state.playerAlarm = Math.min(100, this._state.playerAlarm + 25); // Increase alarm
    
    // Optionally: send back to previous level or apply other penalties
  }

  /** Open a door */
  private openDoor(entity: DungeonEntity): void {
    entity.type = EntityType.DOOR_OPEN;
    // Door stays open for a few turns then closes automatically
    // For simplicity, we'll just leave it open
  }

  /** Close a door after some time (called periodically) */
  public updateDoors(): void {
    // Simple door closing logic - in reality would have timers
    for (const entity of this._state.entities) {
      if (entity.type === EntityType.DOOR_OPEN) {
        // 10% chance per turn to close
        if (this.rng() < 0.1) {
          entity.type = EntityType.DOOR_CLOSED;
        }
      }
    }
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
    return this._state.entities.filter(e => e.x === x && e.y === y);
  }

  /** Get player position */
  public getPlayerPosition(): {x: number; y: number} {
    return {x: this._state.playerX, y: this._state.playerY};
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
  public getStairsUp(): {x: number | null; y: number | null} {
    return {x: this._state.stairsUpX, y: this._state.stairsUpY};
  }
  
  public getStairsDown(): {x: number | null; y: number | null} {
    return {x: this._state.stairsDownX, y: this._state.stairsDownY};
  }

  /** Process one game turn (call periodically) */
  public processTurn(): void {
    // Update doors
    this.updateDoors();
    
    // Monster AI - simple version: move toward player if they can see them
    this.processMonsterAi();
    
    // Update FOV
    this.updateFov();
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

  /** Simple monster AI */
  private processMonsterAi(): void {
    for (const entity of this._state.entities) {
      if (entity.type === EntityType.MONSTER && entity.hostile && entity.hp > 0) {
        // Simple AI: if player is adjacent, attack; otherwise move toward player
        const dx = Math.abs(entity.x - this._state.playerX);
        const dy = Math.abs(entity.y - this._state.playerY);
        
        if (dx <= 1 && dy <= 1) {
          // Adjacent - attack player
          this.playerTakeDamage(this.getMonsterDamage(entity.subtype as MonsterType));
        } else if (dx + dy > 1) {
          // Not adjacent - try to move toward player
          const moveX = this._state.playerX > entity.x ? 1 : 
                       this._state.playerX < entity.x ? -1 : 0;
          const moveY = this._state.playerY > entity.y ? 1 : 
                       this._state.playerY < entity.y ? -1 : 0;
          
          // Try to move diagonally first if both axes need movement
          if (moveX !== 0 && moveY !== 0 && this.rng() < 0.7) {
            // Try diagonal move
            if (this.tryMoveMonster(entity, moveX, moveY)) {
              continue; // Moved successfully
            }
          }
          
          // Try horizontal move
          if (moveX !== 0 && this.tryMoveMonster(entity, moveX, 0)) {
            continue;
          }
          
          // Try vertical move
          if (moveY !== 0 && this.tryMoveMonster(entity, 0, moveY)) {
            continue;
          }
        }
      }
    }
  }

  /** Try to move a monster */
  private tryMoveMonster(entity: DungeonEntity, dx: number, dy: number): boolean {
    const newX = entity.x + dx;
    const newY = entity.y + dy;
    
    // Check bounds
    if (newX < 0 || newX >= this._state.width || newY < 0 || newY >= this._state.height) {
      return false;
    }
    
    // Check if tile is walkable
    const tile = this._state.tiles[newY][newX];
    if (tile.type === TileType.WALL) {
      return false;
    }
    
    // Check if tile is occupied by another entity
    const occupied = this._state.entities.some(
      e => e !== entity && e.x === newX && e.y === newY
    );
    
    if (occupied) {
      return false;
    }
    
    // Move the monster
    entity.x = newX;
    entity.y = newY;
    return true;
  }
}

/** Factory function to create a dungeon crawler from a mission */
export function createDungeonCrawlerFromMission(mission: Mission | null = null): DungeonCrawler {
  // Generate a seed based on mission and current time
  const seed = Date.now() + (mission ? stringHashCode(mission.id) : 0);
  return new DungeonCrawler(seed, mission);
}