/** Navigation numbering convention (UI triage U3).
 *
 * Main menu, mission select and matrix all label list entries with the same
 * 1-based `[N]` form produced by `formatNavIndex`. The matrix previously used
 * 0-based `[i]` and the mission select used `N.`.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { formatNavIndex } from "../src/renderer/nav_index";
import { renderMainMenu, MENU_OPTIONS } from "../src/renderer/menu_main";
import { renderMatrix } from "../src/renderer/matrix";
import type { Matrix } from "../src/core/types";

function gridText(
  grid: ReturnType<typeof renderMatrix>,
  cols: number,
  rows: number,
): string {
  const lines: string[] = [];
  for (let y = 0; y < rows; y++) {
    let line = "";
    for (let x = 0; x < cols; x++) line += grid.get(x, y)?.char ?? " ";
    lines.push(line);
  }
  return lines.join("\n");
}

const MATRIX: Matrix = {
  nodes: [
    {
      id: 0,
      zone: "surface",
      iceIds: ["watchdog"],
      iceHp: [100],
      reward: { credits: 50 },
      isBoss: false,
      adjacent: [1],
    },
    {
      id: 1,
      zone: "core",
      iceIds: ["watchdog"],
      iceHp: [120],
      reward: { credits: 75 },
      isBoss: true,
      adjacent: [],
    },
  ],
  startNode: 0,
  bossNode: 1,
};

describe("formatNavIndex", () => {
  it("renders a 0-based index as 1-based bracketed number", () => {
    expect(formatNavIndex(0)).toBe("[1]");
    expect(formatNavIndex(8)).toBe("[9]");
    expect(formatNavIndex(13)).toBe("[14]");
  });
});

describe("unified numbering across screens", () => {
  it("main menu labels the first option [1]", () => {
    const text = gridText(renderMainMenu(0, 80, 40), 80, 40);
    expect(text).toContain("[1] ");
    expect(text).toContain(`[${MENU_OPTIONS.length}] `);
    expect(text).not.toContain("[0] ");
  });

  it("matrix labels nodes 1-based (first node is [1], not [0])", () => {
    const text = gridText(renderMatrix(MATRIX, 0, [], 80, 40), 80, 40);
    expect(text).toContain("[1] SURFACE");
    expect(text).toContain("[2] CORE");
    expect(text).not.toContain("[0]");
  });

  it("mission select formats entries through formatNavIndex, not `N.`", () => {
    // main.ts self-boots on import, so the call site is checked in source text
    // (same approach as tests/onboarding.test.ts).
    const mainSource = readFileSync(
      fileURLToPath(new URL("../src/main.ts", import.meta.url)),
      "utf-8",
    );
    expect(mainSource).toContain("${formatNavIndex(index)} ${titleText}");
    expect(mainSource).not.toContain("${index + 1}. ${titleText}");
  });
});
