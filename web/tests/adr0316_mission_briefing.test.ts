/**
 * ADR-0316 — the mission says what it is about.
 *
 * The Sprawl missions carried no in-game story text: the narrative lived in
 * `Fiction/derivative/`, where 166 stories declare a `game_mission_id` and a
 * clean `plot_summary`. The mission select now shows the selected mission's
 * briefing, lifted from that summary (`scripts/tools/import_briefings.py`).
 */
import { describe, expect, it } from "vitest";
import { renderMissionList } from "../src/renderer/mission_select";
import missionsJson from "../src/data/missions.json" with { type: "json" };

const ROWS = ["[1] First Jack   T1  500cr", "[2] Data Retrieval   T2  800cr"];

function gridText(grid: { cells: ReadonlyArray<ReadonlyArray<{ char: string }>> }): string {
  return grid.cells.map((row) => row.map((c) => c?.char ?? " ").join("")).join("\n");
}

describe("ADR-0316 · mission briefing", () => {
  it("shows the briefing under the list", () => {
    const text = gridText(
      renderMissionList(ROWS, 0, 80, 50, "Case takes his first real trace job."),
    );
    expect(text).toContain("Case takes his first real trace job.");
  });

  it("renders no briefing block when the mission has none", () => {
    const text = gridText(renderMissionList(ROWS, 0, 80, 50, null));
    expect(text).toContain("First Jack");
    // Nothing below the list should be a sentence.
    expect(text).not.toContain(".");
  });

  it("wraps instead of cutting at 40 columns", () => {
    const briefing =
      "Case experiences the thirty seconds after jack-out — the shaking hands, the matrix.";
    const text = gridText(renderMissionList(ROWS, 0, 40, 60, briefing));
    for (const word of ["Case", "thirty", "shaking", "matrix"]) {
      expect(text, `"${word}" missing at 40 columns`).toContain(word);
    }
  });

  it("ships a briefing for every Sprawl mission", () => {
    const sprawl = Object.values(missionsJson).filter(
      (m) => (m as { source_universe?: string }).source_universe !== "far-grid",
    ) as ReadonlyArray<{ id: string; briefing?: string }>;
    const missing = sprawl.filter((m) => !m.briefing).map((m) => m.id);
    // `dixies_offer` was the one mission with no derivative story. The Fiction
    // side wrote it on 2026-11-17, so the gap is closed — and this asserts the
    // closed state rather than the gap it used to be.
    expect(missing).toEqual([]);
  });

  it("keeps every imported Sprawl briefing to one readable brief", () => {
    // This used to assert "≤ 151 characters, ending in '.' or '…'" — the
    // truncation the importer did, written down as if it were the rule. It was
    // not: the cut ended 20 of 32 briefings mid-clause, and the "…" only said
    // so. The rules that replaced it (whole sentences, no cut marker, and the
    // screen must fit) live in `adr0316_briefings_are_complete.test.ts`.
    // What is checked here is that the import happened at all.
    for (const [id, m] of Object.entries(missionsJson)) {
      const mission = m as { briefing?: string; source_universe?: string };
      if (!mission.briefing) continue;
      if (mission.source_universe === "far-grid") continue;
      expect(mission.briefing.length, `${id} briefing length`).toBeGreaterThan(
        40,
      );
      expect(mission.briefing, `${id} carries a cut marker`).not.toContain("…");
    }
  });
});

describe("ADR-0318 · the mission list says what a pick starts", () => {
  // A grade in the row used to be the whole story; the run is a three-mission
  // contract now, so the same grade means three missions in that band. A
  // contract that completes 2.5% of the time must not look like a 51% mission.
  it("shows the contract's shape under the list", () => {
    const grid = renderMissionList(
      ["[1] First Jack   T1  500cr"],
      0,
      80,
      50,
      null,
      "CONTRACT: 3 missions · T1→T1→T2",
    );
    const text = grid.cells.map((row) => row.map((c) => c.char).join("")).join("\n");
    expect(text).toContain("CONTRACT: 3 missions");
    expect(text).toContain("T1→T1→T2");
  });

  it("draws nothing when there is no contract to describe", () => {
    const grid = renderMissionList(["[1] First Jack   T1  500cr"], 0, 80, 50, null, null);
    const text = grid.cells.map((row) => row.map((c) => c.char).join("")).join("\n");
    expect(text).not.toContain("CONTRACT");
  });
});
