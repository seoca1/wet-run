/** ADR-0352 — the dungeon crawler's glyphs are a rendering contract.
 *
 * The string enums (`TileType` / `EntityType` / `MonsterType`) drive what the
 * map draws. Nothing pinned their VALUES: a change to `"#"` / `"."` / `"@"`
 * would alter every frame and no test would notice (mutation `crawler-floor`
 * etc. survived). This pins the handful that matter.
 */
import { describe, expect, it } from "vitest";
import {
  EntityType,
  MonsterType,
  TileType,
} from "../src/core/dungeon/dungeon_crawler_types";

describe("ADR-0352 · the crawler glyphs are pinned", () => {
  it("tile glyphs", () => {
    expect(TileType.WALL).toBe("#");
    expect(TileType.FLOOR).toBe(".");
    expect(TileType.DOOR).toBe("+");
  });

  it("entity + monster glyphs", () => {
    expect(EntityType.PLAYER).toBe("@");
    expect(EntityType.MONSTER).toBe("M");
    expect(MonsterType.ICE_GOLIATH).toBe("g");
    expect(MonsterType.ICE_BLACK).toBe("B");
  });
});
