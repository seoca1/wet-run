/** Tests for Far Grid hub renderer (ADR-0213 Phase 1). */
import { describe, it, expect } from "vitest";
import { renderFarGridHub } from "../src/renderer/far_grid_hub";
import type { Cell, Mission, MissionRewards } from "../src/core/types";

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

function makeMissionWithStory(
  id: string,
  title: string,
  source: string,
): Mission {
  return { ...makeMission(id, title), story: { source } };
}

function makeMissionWithBriefing(
  id: string,
  title: string,
  briefing: string,
): Mission {
  return { ...makeMission(id, title), briefing };
}

function gridText(grid: { cells: ReadonlyArray<ReadonlyArray<Cell>> }): string {
  return grid.cells
    .map((row) => row.map((c) => c?.char ?? " ").join(""))
    .join("\n");
}

function getRowText(
  grid: { cells: ReadonlyArray<ReadonlyArray<Cell>> },
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

describe("renderFarGridHub", () => {
  it("renders the header 'FAR GRID HUB' on row 1", () => {
    const missions: ReadonlyArray<Mission> = [makeMission("m1", "Echo Lattice")];
    const grid = renderFarGridHub(missions, 0, 80, 24);
    const header = getRowText(grid, 1, 2, "FAR GRID HUB".length);
    expect(header).toBe("FAR GRID HUB");
  });

  it("lists each mission title on its own row starting at row 5", () => {
    const missions: ReadonlyArray<Mission> = [
      makeMission("m1", "Echo Lattice"),
      makeMission("m2", "Ghost Frequencies"),
      makeMission("m3", "Silent Channel"),
    ];
    const grid = renderFarGridHub(missions, 0, 80, 24);
    expect(getRowText(grid, 5, 6, "Echo Lattice".length)).toBe("Echo Lattice");
    expect(getRowText(grid, 6, 6, "Ghost Frequencies".length)).toBe(
      "Ghost Frequencies",
    );
    expect(getRowText(grid, 7, 6, "Silent Channel".length)).toBe(
      "Silent Channel",
    );
  });

  it("places the ▸ marker on the selected row", () => {
    const missions: ReadonlyArray<Mission> = [
      makeMission("m1", "Echo Lattice"),
      makeMission("m2", "Ghost Frequencies"),
      makeMission("m3", "Silent Channel"),
    ];
    // selected = 1 → marker on row 5 + 1 = 6
    const grid = renderFarGridHub(missions, 1, 80, 24);
    expect(getRowText(grid, 6, 4, 1)).toBe("▸");
    // Other rows use blank marker
    expect(getRowText(grid, 5, 4, 1)).toBe(" ");
    expect(getRowText(grid, 7, 4, 1)).toBe(" ");
  });

  it("shows '(no Far Grid missions available)' when mission list is empty", () => {
    const missions: ReadonlyArray<Mission> = [];
    const grid = renderFarGridHub(missions, 0, 80, 24);
    const emptyMsg = "(no Far Grid missions available)";
    expect(getRowText(grid, 5, 2, emptyMsg.length)).toBe(emptyMsg);
    // No ▸ marker should appear when the list is empty
    const text = gridText(grid);
    expect(text).not.toContain("▸");
  });

  it("shows the statusMessage line when provided, and omits it otherwise", () => {
    const missions: ReadonlyArray<Mission> = [makeMission("m1", "Echo Lattice")];
    const cols = 80;
    const rows = 24;

    // statusMessage given → rendered one row above footer
    const statusText = "Loading Far Grid uplinks...";
    const gridWithStatus = renderFarGridHub(
      missions,
      0,
      cols,
      rows,
      statusText,
    );
    const statusRow = rows - 3;
    expect(getRowText(gridWithStatus, statusRow, 2, statusText.length)).toBe(
      statusText,
    );

    // statusMessage omitted → status row stays empty (background)
    const gridWithoutStatus = renderFarGridHub(missions, 0, cols, rows);
    expect(getRowText(gridWithoutStatus, statusRow, 2, statusText.length)).not.toBe(
      statusText,
    );
    // Sanity: the header and footer are still present in both variants
    expect(getRowText(gridWithoutStatus, 1, 2, "FAR GRID HUB".length)).toBe(
      "FAR GRID HUB",
    );
  });

  it("shows [Source: stem] on the same line when mission has story.source", () => {
    const stem = "xauthors/true-names/en/2026-10-11_far_grid_prelude";
    const grid = renderFarGridHub(
      [makeMissionWithStory("m1", "Echo Lattice", stem)],
      0,
      80,
      24,
    );
    const text = gridText(grid);
    expect(text).toContain(`[Source: ${stem}]`);
    // Title row position unchanged (row 5)
    expect(getRowText(grid, 5, 6, "Echo Lattice".length)).toBe("Echo Lattice");
  });

  it("shows no source annotation when mission has no story", () => {
    const grid = renderFarGridHub([makeMission("m1", "Echo Lattice")], 0, 80, 24);
    expect(gridText(grid)).not.toContain("[Source:");
  });
});

describe("renderFarGridHub — Wave 2 briefing block (ADR-0213)", () => {
  it("renders the selected mission's briefing on the row below the list", () => {
    const missions: ReadonlyArray<Mission> = [
      makeMissionWithBriefing("m1", "Echo Lattice", "First, second, third."),
    ];
    const grid = renderFarGridHub(missions, 0, 80, 24);
    // List row 5 (title at x=6: marker x=4, space x=5); blank row 6;
    // briefing row 7 (text at x=2, matching the intro).
    expect(getRowText(grid, 5, 6, "Echo Lattice".length)).toBe("Echo Lattice");
    expect(getRowText(grid, 6, 2, 1)).toBe(" ");
    expect(getRowText(grid, 7, 2, "First, second, third.".length)).toBe(
      "First, second, third.",
    );
  });

  it("follows the selected mission when selection changes", () => {
    const missions: ReadonlyArray<Mission> = [
      makeMissionWithBriefing("m1", "Echo Lattice", "Alpha briefing."),
      makeMissionWithBriefing("m2", "Ghost Frequencies", "Bravo briefing."),
    ];
    const gridA = renderFarGridHub(missions, 0, 80, 24);
    const gridB = renderFarGridHub(missions, 1, 80, 24);
    // List rows 5–6 (2 missions); gap row 7; briefing row 8.
    expect(getRowText(gridA, 8, 2, "Alpha briefing.".length)).toBe(
      "Alpha briefing.",
    );
    expect(getRowText(gridB, 8, 2, "Bravo briefing.".length)).toBe(
      "Bravo briefing.",
    );
  });

  it("wraps a long briefing to multiple lines within grid width", () => {
    const longBriefing =
      "One two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen.";
    const missions: ReadonlyArray<Mission> = [
      makeMissionWithBriefing("m1", "Echo Lattice", longBriefing),
    ];
    const cols = 40;
    const rows = 24;
    const grid = renderFarGridHub(missions, 0, cols, rows);
    const text = gridText(grid);
    // Briefing must appear (some line contains a portion of the text).
    expect(text).toContain("One two");
    // No rendered cell on any row may exceed the grid width.
    for (const row of grid.cells) {
      expect(row.length).toBe(cols);
    }
  });

  it("does not break grid width when a single word exceeds the cap", () => {
    // 80-char single word vs 20-col cap → must be sliced and never overflow.
    const hugeWord = "x".repeat(80);
    const missions: ReadonlyArray<Mission> = [
      makeMissionWithBriefing("m1", "Echo Lattice", hugeWord),
    ];
    const cols = 20;
    const rows = 24;
    const grid = renderFarGridHub(missions, 0, cols, rows);
    for (const row of grid.cells) {
      expect(row.length).toBe(cols);
    }
  });

  it("renders a mission without briefing without empty garbage lines", () => {
    const missions: ReadonlyArray<Mission> = [
      makeMission("m1", "Echo Lattice"),
      makeMission("m2", "Ghost Frequencies"),
    ];
    const grid = renderFarGridHub(missions, 0, 80, 24);
    // List rows 5 and 6; row 7 is the gap row (single space) and should NOT
    // be followed by an empty rendered briefing. The text below the list
    // should not contain "briefing" leaks or stray newlines.
    const text = gridText(grid);
    expect(text).not.toContain("undefined");
    expect(text).not.toContain("null");
    // Footer still present (sanity).
    expect(getRowText(grid, 22, 2, "↑↓: navigate".length)).toBe("↑↓: navigate");
  });

  it("omits briefing when missions list is empty (no crash, no garbage)", () => {
    const grid = renderFarGridHub([], 0, 80, 24);
    const text = gridText(grid);
    expect(text).toContain("(no Far Grid missions available)");
    expect(text).not.toContain("undefined");
    expect(text).not.toContain("null");
  });

  it("does not collide with the footer even on a very short grid", () => {
    const longBriefing =
      "One two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen.";
    const missions: ReadonlyArray<Mission> = [
      makeMissionWithBriefing("m1", "Echo Lattice", longBriefing),
    ];
    // 14 rows: list row 5, briefing rows 6+ — footer is row 12. Briefing
    // must be clipped, never overwrite the footer.
    const grid = renderFarGridHub(missions, 0, 80, 14);
    const footerY = 12;
    const footerText = "↑↓: navigate | ENTER: launch | ESC: back";
    expect(getRowText(grid, footerY, 2, footerText.length)).toBe(footerText);
  });

  it("keeps the [Source: stem] line unchanged when briefing is present", () => {
    const stem = "xauthors/true-names/en/2026-10-11_wileys_gate";
    const mission: Mission = {
      ...makeMission("m1", "Wiley's Gate"),
      story: { source: stem },
      briefing: "Single page of a red book has been read.",
    };
    const grid = renderFarGridHub([mission], 0, 80, 24);
    const text = gridText(grid);
    expect(text).toContain(`[Source: ${stem}]`);
    expect(text).toContain("Single page of a red book has been read.");
  });
});