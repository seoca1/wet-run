/**
 * ADR-0317 — the job is on file before you jack in.
 *
 * The mission's story (ADR-0316, lifted from the derivative fiction) is spoken
 * on a screen between the mission list and the advance: mission select →
 * briefing → prep → run. The screen was designed in the web port
 * (`renderBriefingScreen`, Finn's office) and never wired; this one is wired,
 * wraps, and promises only the keys that work (ADR-0251 rule 5).
 */
import { describe, expect, it } from "vitest";
import { renderMissionBriefing } from "../src/renderer/menu_dialogue";
import missionsJson from "../src/data/missions.json" with { type: "json" };

function gridText(grid: { cells: ReadonlyArray<ReadonlyArray<{ char: string }>> }): string {
  return grid.cells.map((row) => row.map((c) => c?.char ?? " ").join("")).join("\n");
}

const STORY =
  "Case takes his first real trace job for The Finn. The target is a mid-level node.";

describe("ADR-0317 · mission briefing", () => {
  it("names the mission and speaks the story", () => {
    const text = gridText(renderMissionBriefing("First Jack", "finn", STORY, 80, 50));
    expect(text).toContain("MISSION BRIEFING");
    expect(text).toContain("Mission: First Jack");
    expect(text).toContain("Fixer: FINN");
    expect(text).toContain("first real trace job");
  });

  it("wraps instead of cutting at 40 columns", () => {
    const text = gridText(renderMissionBriefing("First Jack", "finn", STORY, 40, 60));
    for (const word of ["Fixer: FINN", "trace", "node"]) {
      expect(text, `"${word}" missing at 40 columns`).toContain(word);
    }
  });

  it("promises only the keys that work", () => {
    const wide = gridText(renderMissionBriefing("X", "finn", STORY, 80, 50));
    expect(wide).toContain("ENTER: continue | ESC: back to mission select");
    // At 40 columns the long footer would be cut, so the short one is used.
    const narrow = gridText(renderMissionBriefing("X", "finn", STORY, 40, 60));
    expect(narrow).toContain("ENTER continue · ESC back");
  });

  it("every Sprawl mission has a story to brief with (except dixies_offer)", () => {
    const sprawl = Object.values(missionsJson).filter(
      (m) => (m as { source_universe?: string }).source_universe !== "far-grid",
    ) as ReadonlyArray<{ id: string; briefing?: string }>;
    const missing = sprawl.filter((m) => !m.briefing).map((m) => m.id);
    expect(missing).toEqual(["dixies_offer"]);
  });
});
