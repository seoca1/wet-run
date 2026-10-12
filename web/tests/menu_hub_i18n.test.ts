/** i18n wiring tests for the main-menu + Far Grid hub renderers (ADR-0010).
 *
 * Pins two contracts:
 *  1. EN output is byte-identical whether `language` is omitted (default) or
 *     explicitly "en" — the i18n tables carry the exact current literals.
 *  2. KO resolves the covered literals (labels, suffixes, hub header/intro/
 *     footer/empty) to Korean. Proper nouns ("FAR GRID", "WET RUN") stay as-is
 *     in KO (documented rule: proper nouns + Gibson tech terms retain English).
 */
import { describe, it, expect } from "vitest";
import { renderMainMenu } from "../src/renderer/menu_main";
import { renderFarGridHub } from "../src/renderer/far_grid_hub";
import type { Cell, Mission, MissionRewards } from "../src/core/types";

type GridLike = { cells: ReadonlyArray<ReadonlyArray<Cell>> };

function gridText(grid: GridLike): string {
  return grid.cells
    .map((row) => row.map((c) => c?.char ?? " ").join(""))
    .join("\n");
}

function getRowText(
  grid: GridLike,
  y: number,
  x: number,
  length: number,
): string {
  let result = "";
  const row = grid.cells[y];
  if (!row) return result;
  for (let i = 0; i < length; i++) {
    result += row[x + i]?.char ?? " ";
  }
  return result;
}

const EMPTY_REWARDS: MissionRewards = { credits: 0, materials: {} };

function makeMission(id: string, title: string): Mission {
  return {
    id,
    title,
    fixer: "test_fixer",
    arc: 1,
    zone: "far_grid_test",
    grade_min: 1,
    grade_max: 1,
    rewards: EMPTY_REWARDS,
    source_universe: "far-grid",
  };
}

const FOOTER_HUB_EN = "↑↓: navigate | ENTER: launch | ESC: back";
const FOOTER_MENU_EN = "↑↓: navigate | ENTER: select | ESC: back";

describe("renderMainMenu i18n — EN byte-identical", () => {
  it("default language equals explicit en (locked, no save)", () => {
    expect(gridText(renderMainMenu(1, 80, 50, false, null, "", false))).toBe(
      gridText(renderMainMenu(1, 80, 50, false, null, "", false, "en")),
    );
  });

  it("default language equals explicit en (save present)", () => {
    const meta = { missionId: "x", turnCount: 2 };
    expect(gridText(renderMainMenu(3, 80, 50, true, meta, "", true))).toBe(
      gridText(renderMainMenu(3, 80, 50, true, meta, "", true, "en")),
    );
  });

  it("default language equals explicit en (status message)", () => {
    expect(
      gridText(renderMainMenu(7, 80, 50, false, null, "coming soon", false)),
    ).toBe(
      gridText(
        renderMainMenu(7, 80, 50, false, null, "coming soon", false, "en"),
      ),
    );
  });

  it("renders the exact English literals on their pinned cells", () => {
    const grid = renderMainMenu(1, 80, 50, false, null, "", false, "en");
    const text = gridText(grid);
    expect(text).toContain("WET RUN");
    expect(text).toContain(
      "A cyberpunk roguelike based on Gibson's Sprawl trilogy",
    );
    expect(text).toContain("[1] NEW RUN");
    expect(text).toContain("[3] DUNGEON CRAWL");
    expect(text).toContain("[5] CONTINUE    (no save)");
    expect(text).toContain("[2] FAR GRID    (locked)");
    expect(text).toContain("[7] CRAFT");
    expect(text).toContain("[8] EQUIPMENT");
    expect(text).toContain(FOOTER_MENU_EN);
    expect(text).toContain("Tier 4 · v0.1.0 · ADR-0209 IDB");
  });

  it("keeps the (locked) suffix off the FAR GRID row when unlocked", () => {
    const grid = renderMainMenu(1, 80, 50, false, null, "", true, "en");
    expect(gridText(grid)).toContain("[2] FAR GRID");
    expect(gridText(grid)).not.toContain("(locked)");
  });
});

describe("renderMainMenu i18n — KO", () => {
  it("resolves the (locked) suffix to Korean and keeps FAR GRID as-is", () => {
    const text = gridText(
      renderMainMenu(1, 80, 50, false, null, "", false, "ko"),
    );
    expect(text).toContain("FAR GRID");
    expect(text).toContain("(잠김)");
    expect(text).not.toContain("(locked)");
  });

  it("resolves the (no save) suffix and CONTINUE label to Korean", () => {
    const text = gridText(
      renderMainMenu(4, 80, 50, false, null, "", true, "ko"),
    );
    expect(text).toContain("이어서 하기    (저장 없음)");
    expect(text).not.toContain("(no save)");
  });

  it("resolves the menu label set and footer to Korean", () => {
    const text = gridText(
      renderMainMenu(0, 80, 50, false, null, "", true, "ko"),
    );
    expect(text).toContain("[7] 제작");
    expect(text).toContain("[8] 장비");
    expect(text).toContain("[3] 던전 크롤");
    expect(text).toContain("↑↓: 이동 | ENTER: 선택 | ESC: 뒤로");
  });
});

describe("renderFarGridHub i18n — EN byte-identical", () => {
  const missions: ReadonlyArray<Mission> = [
    makeMission("m1", "Echo Lattice"),
    makeMission("m2", "Ghost Frequencies"),
  ];

  it("default language equals explicit en (non-empty list)", () => {
    expect(gridText(renderFarGridHub(missions, 0, 80, 24))).toBe(
      gridText(renderFarGridHub(missions, 0, 80, 24, "", "en")),
    );
  });

  it("default language equals explicit en (empty list)", () => {
    expect(gridText(renderFarGridHub([], 0, 80, 24))).toBe(
      gridText(renderFarGridHub([], 0, 80, 24, "", "en")),
    );
  });

  it("renders the exact English literals on their pinned rows", () => {
    const grid = renderFarGridHub(missions, 0, 80, 24, "", "en");
    const text = gridText(grid);
    expect(getRowText(grid, 1, 2, "FAR GRID HUB".length)).toBe("FAR GRID HUB");
    expect(text).toContain("Beyond the Sprawl — Far Grid-tagged missions");
    expect(text).toContain("Echo Lattice");
    expect(getRowText(grid, 22, 2, FOOTER_HUB_EN.length)).toBe(FOOTER_HUB_EN);
  });

  it("renders the exact English empty-list message", () => {
    const grid = renderFarGridHub([], 0, 80, 24, "", "en");
    expect(
      getRowText(grid, 5, 2, "(no Far Grid missions available)".length),
    ).toBe("(no Far Grid missions available)");
  });
});

describe("renderFarGridHub i18n — KO", () => {
  const missions: ReadonlyArray<Mission> = [makeMission("m1", "Echo Lattice")];

  it("renders the hub header in Korean (proper noun retained)", () => {
    const grid = renderFarGridHub(missions, 0, 80, 24, "", "ko");
    expect(getRowText(grid, 1, 2, "FAR GRID 허브".length)).toBe(
      "FAR GRID 허브",
    );
    expect(getRowText(grid, 1, 2, "FAR GRID HUB".length)).not.toBe(
      "FAR GRID HUB",
    );
  });

  it("renders the intro and footer in Korean", () => {
    const text = gridText(renderFarGridHub(missions, 0, 80, 24, "", "ko"));
    expect(text).toContain("스프롤 너머 — FAR GRID 임무");
    expect(text).toContain("↑↓: 이동 | ENTER: 출격 | ESC: 뒤로");
  });

  it("renders the Korean empty-list message and leaves mission titles as data", () => {
    const empty = renderFarGridHub([], 0, 80, 24, "", "ko");
    expect(gridText(empty)).toContain("(표시할 FAR GRID 임무 없음)");
    const withMission = renderFarGridHub(missions, 0, 80, 24, "", "ko");
    expect(gridText(withMission)).toContain("Echo Lattice");
  });
});
