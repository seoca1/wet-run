/** NetHack-style tile-based dungeon crawler mode — public entry point.
 *
 * Split into focused modules (AGENTS.md §6 module-size policy):
 * - `dungeon_crawler_types.ts`      — enums + state/entity interfaces
 * - `dungeon_crawler_generation.ts` — seeded RNG + level layout + stairs
 * - `dungeon_crawler_entities.ts`   — entity placement + field-of-view
 * - `dungeon_crawler_actions.ts`    — player movement, combat, traps, doors
 * - `dungeon_crawler_core.ts`       — monster AI + `DungeonCrawler` facade + factory
 *
 * This barrel preserves the original import path so existing importers
 * (`main.ts`, `renderer/dungeon.ts`, tests) keep working unchanged.
 */

export {
  TileType,
  EntityType,
  ItemType,
  MonsterType,
} from "./dungeon_crawler_types.ts";
export type {
  DungeonTile,
  DungeonEntity,
  DungeonState,
} from "./dungeon_crawler_types.ts";
export {
  DungeonCrawler,
  createDungeonCrawlerFromMission,
} from "./dungeon_crawler_core.ts";
