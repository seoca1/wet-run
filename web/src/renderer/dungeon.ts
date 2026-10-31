/** Dungeon tile renderer for NetHack-style crawler mode.
 *
 * Renders the dungeon map with:
 * - Tile-based graphics (walls, floors, doors, stairs)
 * - Entity rendering (player, monsters, items)
 * - Fog of war / exploration system
 * - Color coding for different tile types and entities
 * - ADR-0237 §2: an inset Green Grid frame (panel.ts) around the map
 */

import { Grid } from "../core/types";
import { PALETTE } from "./palette";
import {
  TileType,
  EntityType,
  ItemType,
  MonsterType,
} from "../core/dungeon/dungeon_crawler";
import { DungeonCrawler } from "../core/dungeon/dungeon_crawler";
import { makeGrid, setCell } from "../core/grid";
import {
  drawPanel,
  panelInnerRect,
  screenFrameRect,
  type PanelRect,
} from "./panel";

/** Inset Green Grid frame of the dungeon screen (ADR-0237 §2): a one-cell
 * gutter to the canvas edge on every side, shared with the other screens. */
export function dungeonFrame(cols: number, rows: number): PanelRect {
  return screenFrameRect({ width: cols, height: rows });
}

/** Render the dungeon map to a grid.
 *
 * The map is centred inside the frame's inner rectangle and clipped to it;
 * the frame is drawn last so no tile or entity can land on a rail.
 */
export function renderDungeonMap(
  crawler: DungeonCrawler,
  cols: number,
  rows: number,
): Grid {
  // Create empty grid using makeGrid
  let grid = makeGrid(cols, rows);
  const frame = dungeonFrame(cols, rows);
  const inner = panelInnerRect(grid, frame);

  // Calculate offset to center the dungeon in the framed viewport
  const dungeonWidth = crawler.state.width;
  const dungeonHeight = crawler.state.height;

  // A dungeon larger than the inner area is anchored at its top-left corner.
  const offsetX =
    inner.x + Math.max(0, Math.floor((inner.width - dungeonWidth) / 2));
  const offsetY =
    inner.y + Math.max(0, Math.floor((inner.height - dungeonHeight) / 2));

  // Render each tile
  for (let y = 0; y < dungeonHeight; y++) {
    for (let x = 0; x < dungeonWidth; x++) {
      const screenX = offsetX + x;
      const screenY = offsetY + y;

      // Skip if outside the framed viewport
      if (!insideRect(inner, screenX, screenY)) {
        continue;
      }

      const tile = crawler.state.tiles[y][x];
      const explored = crawler.isTileExplored(x, y);
      const visible = crawler.isTileVisible(x, y);

      let char: string;
      let fg: string;
      const bg: string = PALETTE.BACKGROUND;

      if (!explored) {
        // Unexplored area - completely dark
        char = " ";
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

      grid = setCell(grid, { x: screenX, y: screenY }, { char, fg, bg });
    }
  }

  // Render entities on top of tiles
  grid = renderEntities(grid, crawler, offsetX, offsetY, inner);

  // Player after entities, so no monster or item can cover the `@`.
  grid = renderPlayer(grid, crawler, offsetX, offsetY, inner);

  // Frame last, so the map can never overwrite a rail.
  return drawPanel(grid, frame).grid;
}

function insideRect(rect: PanelRect, x: number, y: number): boolean {
  return (
    x >= rect.x &&
    x < rect.x + rect.width &&
    y >= rect.y &&
    y < rect.y + rect.height
  );
}

/** Draw the player `@` at its position, coloured by HP ratio.
 *
 * The crawler tracks the player as `playerX`/`playerY`, not as an entry in
 * `state.entities`, so it gets its own pass. The player's own tile is always
 * explored, so no visibility gate is applied; viewport clipping still is.
 */
function renderPlayer(
  grid: Grid,
  crawler: DungeonCrawler,
  offsetX: number,
  offsetY: number,
  viewport: PanelRect,
): Grid {
  const { x, y } = crawler.getPlayerPosition();
  const screenX = offsetX + x;
  const screenY = offsetY + y;
  if (!insideRect(viewport, screenX, screenY)) {
    return grid;
  }
  const { hp, maxHp } = crawler.getPlayerStats();
  return setCell(
    grid,
    { x: screenX, y: screenY },
    { char: "@", fg: getPlayerFg(hp, maxHp), bg: PALETTE.BACKGROUND },
  );
}

/** Render entities (monsters, items, traps) on top of the map */
function renderEntities(
  grid: Grid,
  crawler: DungeonCrawler,
  offsetX: number,
  offsetY: number,
  viewport: PanelRect,
): Grid {
  const entities = crawler.state.entities;

  for (const entity of entities) {
    // Only render if explored
    if (!crawler.isTileExplored(entity.x, entity.y)) {
      continue;
    }

    const screenX = offsetX + entity.x;
    const screenY = offsetY + entity.y;

    // Skip if outside the framed viewport
    if (!insideRect(viewport, screenX, screenY)) {
      continue;
    }

    const visible = crawler.isTileVisible(entity.x, entity.y);

    let char: string;
    let fg: string;
    const bg: string = PALETTE.BACKGROUND;

    if (!visible) {
      // Entity in explored but not visible area - show as explored tile
      const tile = crawler.state.tiles[entity.y][entity.x];
      char = getTileChar(tile.type);
      fg = getTileFg(tile.type, true); // Dimmed
    } else {
      // Entity is visible
      // The player is not an entity (core tracks it as playerX/playerY);
      // renderPlayer() draws it after this pass.
      switch (entity.type) {
        case EntityType.MONSTER:
          char = entity.subtype
            ? getMonsterChar(entity.subtype as MonsterType)
            : "M";
          fg = getMonsterFg(
            entity.subtype as MonsterType,
            (entity.hp ?? 0) > 0,
          );
          break;
        case EntityType.ITEM:
          char = getItemChar(entity.subtype as ItemType);
          fg = getItemFg(entity.subtype as ItemType);
          break;
        case EntityType.TRAP:
          char = "^";
          fg = PALETTE.RED_BRIGHT;
          break;
        case EntityType.DOOR_CLOSED:
          char = "+";
          fg = PALETTE.YELLOW_AMBER;
          break;
        case EntityType.DOOR_OPEN:
          char = "/";
          fg = PALETTE.YELLOW_AMBER;
          break;
        default:
          char = "?";
          fg = PALETTE.FOREGROUND;
          break;
      }
    }

    grid = setCell(grid, { x: screenX, y: screenY }, { char, fg, bg });
  }

  return grid;
}

/** Get character representation for a tile type */
function getTileChar(type: TileType): string {
  switch (type) {
    case TileType.WALL:
      return "#";
    case TileType.FLOOR:
      return ".";
    case TileType.DOOR:
      return "+";
    case TileType.STAIRS_UP:
      return "<";
    case TileType.STAIRS_DOWN:
      return ">";
    default:
      return " ";
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
    case MonsterType.ICE_WATCHDOG:
      return "w";
    case MonsterType.ICE_SPIDER:
      return "s";
    case MonsterType.ICE_LOA_PRIEST:
      return "l";
    case MonsterType.ICE_GOLIATH:
      return "g";
    case MonsterType.ICE_BLACK:
      return "B";
    default:
      return "M";
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
    case ItemType.HEALTH_POTION:
      return "!";
    case ItemType.ENERGY_CELL:
      return "e";
    case ItemType.DATA_CHIP:
      return "d";
    case ItemType.WEAPON:
      return "w";
    case ItemType.ARMOR:
      return "a";
    default:
      return "?";
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
  if (hexColor === PALETTE.GREEN_NEON) return "#008000";
  if (hexColor === PALETTE.RED_BRIGHT) return "#800000";
  if (hexColor === PALETTE.BLUE_BRIGHT) return "#000080";
  if (hexColor === PALETTE.MAGENTA_LIGHT) return "#800080";
  if (hexColor === PALETTE.CYAN_LIGHT) return "#008080";
  if (hexColor === PALETTE.WHITE) return PALETTE.GRAY_LIGHT;

  return hexColor; // Fallback
}

/** Render dungeon UI elements (sidebar with stats, etc.) */
export function renderDungeonUi(
  crawler: DungeonCrawler,
  _cols: number,
  _rows: number,
): ReadonlyArray<string> {
  const stats = crawler.getPlayerStats();

  const lines: string[] = [];

  // WET header
  lines.push("WET");

  // Level
  lines.push(`LVE: ${String(stats.level).padStart(2, "0")}`);

  // HP
  lines.push(`HP: ${stats.hp}/${stats.maxHp}`);

  // Alarm
  lines.push(`ALM: ${stats.alarm}%`);

  // Turn
  lines.push(`TRN: ${String(stats.turnCount).padStart(4, "0")}`);

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
