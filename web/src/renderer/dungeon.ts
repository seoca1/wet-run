/** Dungeon tile renderer for NetHack-style crawler mode.
 * 
 * Renders the dungeon map with:
 * - Tile-based graphics (walls, floors, doors, stairs)
 * - Entity rendering (player, monsters, items)
 * - Fog of war / exploration system
 * - Color coding for different tile types and entities
 */

import { Grid } from "../core/types.ts";
import { PALETTE } from "./palette.ts";
import { TileType, EntityType, ItemType, MonsterType } from "../core/dungeon_crawler.ts";
import { DungeonCrawler } from "../core/dungeon_crawler.ts";
import { makeGrid, setCell } from "../core/grid.ts";

/** Render the dungeon map to a grid */
export function renderDungeonMap(
  crawler: DungeonCrawler,
  cols: number,
  rows: number
): Grid {
  // Create empty grid using makeGrid
  const grid = makeGrid(cols, rows);

  // Calculate offset to center the dungeon in the viewport
  const dungeonWidth = crawler.state.width;
  const dungeonHeight = crawler.state.height;
  
  let offsetX = Math.max(0, Math.floor((cols - dungeonWidth) / 2));
  let offsetY = Math.max(0, Math.floor((rows - dungeonHeight) / 2));
  
  // Ensure we don't go negative if dungeon is larger than viewport
  offsetX = Math.min(offsetX, cols - 1);
  offsetY = Math.min(offsetY, rows - 1);
  
  // Render each tile
  for (let y = 0; y < dungeonHeight; y++) {
    for (let x = 0; x < dungeonWidth; x++) {
      const screenX = offsetX + x;
      const screenY = offsetY + y;
      
      // Skip if outside viewport
      if (screenX < 0 || screenX >= cols || screenY < 0 || screenY >= rows) {
        continue;
      }
      
      const tile = crawler.state.tiles[y][x];
      const explored = crawler.isTileExplored(x, y);
      const visible = crawler.isTileVisible(x, y);
      
      let char: string;
      let fg: string;
      let bg: string = PALETTE.BACKGROUND;
      
      if (!explored) {
        // Unexplored area - completely dark
        char = ' ';
        fg = PALETTE.FOREGROUND;
      } else if (!visible) {
        // Explored but not currently visible - dim colors
        char = getTileChar(tile.type);
        fg = getTileFg(tile.type, true); // Dimmed
      } else {
        // Currently visible - full colors
        char = getTileChar(tile.type);
        fg = getTileFg(tile.type, false); // Bright
      }
      
      setCell(grid, { x: screenX, y: screenY }, { char, fg, bg });
    }
  }
  
  // Render entities on top of tiles
  renderEntities(grid, crawler, offsetX, offsetY, cols, rows);
  
  return grid;
}

/** Render entities (player, monsters, items) on top of the map */
function renderEntities(
  grid: Grid,
  crawler: DungeonCrawler,
  offsetX: number,
  offsetY: number,
  cols: number,
  rows: number
): void {
  const entities = crawler.state.entities;
  
  for (const entity of entities) {
    // Only render if explored
    if (!crawler.isTileExplored(entity.x, entity.y)) {
      continue;
    }
    
    const screenX = offsetX + entity.x;
    const screenY = offsetY + entity.y;
    
    // Skip if outside viewport
    if (screenX < 0 || screenX >= cols || screenY < 0 || screenY >= rows) {
      continue;
    }
    
    const visible = crawler.isTileVisible(entity.x, entity.y);
    
    let char: string;
    let fg: string;
    let bg: string = PALETTE.BACKGROUND;
    
    if (!visible) {
      // Entity in explored but not visible area - show as explored tile
      const tile = crawler.state.tiles[entity.y][entity.x];
      char = getTileChar(tile.type);
      fg = getTileFg(tile.type, true); // Dimmed
    } else {
      // Entity is visible
      switch (entity.type) {
        case EntityType.PLAYER:
          char = '@';
          fg = getPlayerFg(crawler.getPlayerStats().hp, crawler.getPlayerStats().maxHp);
          break;
        case EntityType.MONSTER:
          char = getMonsterChar(entity.subtype as MonsterType);
          fg = getMonsterFg(entity.subtype as MonsterType, entity.hp! > 0);
          break;
        case EntityType.ITEM:
          char = getItemChar(entity.subtype as ItemType);
          fg = getItemFg(entity.subtype as ItemType);
          break;
        case EntityType.TRAP:
          char = '^';
          fg = PALETTE.RED_BRIGHT;
          break;
        case EntityType.DOOR_CLOSED:
          char = '+';
          fg = PALETTE.YELLOW_AMBER;
          break;
        case EntityType.DOOR_OPEN:
          char = '/';
          fg = PALETTE.YELLOW_AMBER;
          break;
        default:
          char = '?';
          fg = PALETTE.FOREGROUND;
          break;
      }
    }
    
    setCell(grid, { x: screenX, y: screenY }, { char, fg, bg });
  }
}

/** Get character representation for a tile type */
function getTileChar(type: TileType): string {
  switch (type) {
    case TileType.WALL: return '#';
    case TileType.FLOOR: return '.';
    case TileType.DOOR: return '+';
    case TileType.STAIRS_UP: return '<';
    case TileType.STAIRS_DOWN: return '>';
    default: return ' ';
  }
}

/** Get foreground color for a tile type */
function getTileFg(type: TileType, dimmed: boolean): string {
  const baseColors: Record<TileType, string> = {
    [TileType.WALL]: PALETTE.GRAY_MID,
    [TileType.FLOOR]: PALETTE.GRAY_LIGHT,
    [TileType.DOOR]: PALETTE.YELLOW_AMBER,
    [TileType.STAIRS_UP]: PALETTE.GREEN_NEON,
    [TileType.STAIRS_DOWN]: PALETTE.GREEN_NEON,
  };
  
  const color = baseColors[type] || PALETTE.FOREGROUND;
  
  if (dimmed) {
    // Return a dimmed version of the color
    return dimColor(color);
  }
  
  return color;
}

/** Get character for player based on HP */
function getPlayerFg(currentHp: number, maxHp: number): string {
  const hpRatio = currentHp / maxHp;
  
  if (hpRatio > 0.6) return PALETTE.GREEN_NEON;
  if (hpRatio > 0.3) return PALETTE.YELLOW_AMBER;
  return PALETTE.RED_BRIGHT;
}

/** Get character representation for a monster type */
function getMonsterChar(type: MonsterType): string {
  switch (type) {
    case MonsterType.ICE_WATCHDOG: return 'w';
    case MonsterType.ICE_SPIDER: return 's';
    case MonsterType.ICE_LOA_PRIEST: return 'l';
    case MonsterType.ICE_GOLIATH: return 'g';
    case MonsterType.ICE_BLACK: return 'B';
    default: return 'M';
  }
}

/** Get foreground color for a monster type */
function getMonsterFg(type: MonsterType | undefined, alive: boolean): string {
  if (!type) return PALETTE.FOREGROUND;
  
  if (!alive) {
    return PALETTE.GRAY_MID; // Dead monster
  }
  
  const colors: Record<MonsterType, string> = {
    [MonsterType.ICE_WATCHDOG]: PALETTE.CYAN_LIGHT,
    [MonsterType.ICE_SPIDER]: PALETTE.MAGENTA_LIGHT,
    [MonsterType.ICE_LOA_PRIEST]: PALETTE.YELLOW_AMBER,
    [MonsterType.ICE_GOLIATH]: PALETTE.RED_BRIGHT,
    [MonsterType.ICE_BLACK]: PALETTE.WHITE,
  };
  
  return colors[type] || PALETTE.FOREGROUND;
}

/** Get character representation for an item type */
function getItemChar(type: ItemType): string {
  switch (type) {
    case ItemType.HEALTH_POTION: return '!';
    case ItemType.ENERGY_CELL: return 'e';
    case ItemType.DATA_CHIP: return 'd';
    case ItemType.WEAPON: return 'w';
    case ItemType.ARMOR: return 'a';
    default: return '?';
  }
}

/** Get foreground color for an item type */
function getItemFg(type: ItemType): string {
  const colors: Record<ItemType, string> = {
    [ItemType.HEALTH_POTION]: PALETTE.RED_BRIGHT,
    [ItemType.ENERGY_CELL]: PALETTE.BLUE_BRIGHT,
    [ItemType.DATA_CHIP]: PALETTE.CYAN_LIGHT,
    [ItemType.WEAPON]: PALETTE.YELLOW_AMBER,
    [ItemType.ARMOR]: PALETTE.GREEN_NEON,
  };
  
  return colors[type] || PALETTE.FOREGROUND;
}

/** Dim a color for fog of war effect */
function dimColor(hexColor: string): string {
  // Simple dimming - in a real implementation we'd convert to HSL and reduce lightness
  if (hexColor === PALETTE.GRAY_MID) return PALETTE.GRAY_DARK;
  if (hexColor === PALETTE.GRAY_LIGHT) return PALETTE.GRAY;
  if (hexColor === PALETTE.YELLOW_AMBER) return PALETTE.YELLOW;
  if (hexColor === PALETTE.GREEN_NEON) return '#008000';
  if (hexColor === PALETTE.RED_BRIGHT) return '#800000';
  if (hexColor === PALETTE.BLUE_BRIGHT) return '#000080';
  if (hexColor === PALETTE.MAGENTA_LIGHT) return '#800080';
  if (hexColor === PALETTE.CYAN_LIGHT) return '#008080';
  if (hexColor === PALETTE.WHITE) return PALETTE.GRAY_LIGHT;
  
  return hexColor; // Fallback
}

/** Render dungeon UI elements (sidebar with stats, etc.) */
export function renderDungeonUi(
  crawler: DungeonCrawler,
  _cols: number,
  _rows: number
): ReadonlyArray<string> {
  const stats = crawler.getPlayerStats();
  
  const lines: string[] = [];
  
  // WET header
  lines.push("WET");
  
  // Level
  lines.push(`LVE: ${String(stats.level).padStart(2, '0')}`);
  
  // HP
  lines.push(`HP: ${stats.hp}/${stats.maxHp}`);
  
  // Alarm
  lines.push(`ALM: ${stats.alarm}%`);
  
  // Turn
  lines.push(`TRN: ${String(stats.turnCount).padStart(4, '0')}`);
  
  // Stairs indicators
  const stairsUp = crawler.getStairsUp();
  const stairsDown = crawler.getStairsDown();
  
  if (stairsUp.x !== null && stairsUp.y !== null) {
    lines.push("< UP");
  }
  
  if (stairsDown.x !== null && stairsDown.y !== null) {
    lines.push("> DN");
  }
  
  return lines;
}