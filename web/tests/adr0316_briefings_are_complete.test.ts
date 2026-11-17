/**
 * ADR-0316 / ADR-0317 — a briefing is a whole sentence, and the screen says what
 * it is.
 *
 * The first importer cut every summary at 150 characters and appended "…", so
 * 20 of 32 briefings ended mid-clause and were then printed as the fixer's
 * words ("FINN: A simple data retrieval job goes sideways when the target turns
 * out to be corporate payroll—a secret that could bring down a mid-level…").
 * Two rules came out of that (2026-11-17):
 *
 *  1. **Authored text never ends with an ellipsis.** A trailing "…" is a cut,
 *     and a cut reads as broken rather than mysterious. (An ellipsis in the
 *     middle is dialogue trailing off — `ice_black_intro` has one — and stays.)
 *  2. **Whatever a screen shows must fit**, at every layout. That is the
 *     ADR-0300 recorder's job, and this holds the briefings to it.
 */
import { describe, expect, it } from "vitest";
import { takeClippedText } from "../src/core/grid";
import { renderMissionBriefing } from "../src/renderer/menu_dialogue";
import { renderMissionList } from "../src/renderer/mission_select";
import { loadMissionsCatalog } from "../src/core/data_loaders";
import missionsData from "../src/data/missions.json" with { type: "json" };
import dialoguesData from "../src/data/event_dialogues.json" with { type: "json" };

const MISSIONS = loadMissionsCatalog(missionsData);
const SPRAWL = MISSIONS.filter((m) => m.source_universe !== "far-grid");
const LAYOUTS = [
  [40, 60],
  [60, 40],
  [80, 50],
] as const;

/** The rule, in one place so both directions can be checked. */
function endsWithEllipsis(text: string): boolean {
  return /(?:…|\.\.\.)\s*$/.test(text);
}

describe("ADR-0316 — the briefings are whole sentences", () => {
  it("the instrument sees a cut", () => {
    // A guard that can silently record nothing is worse than no guard.
    expect(endsWithEllipsis("a secret that could bring down a mid-level…")).toBe(
      true,
    );
    expect(endsWithEllipsis("It's gone.")).toBe(false);
    expect(endsWithEllipsis("...jockey... JACK OUT... NOW...")).toBe(true);
    // A mid-string ellipsis is dialogue trailing off, not a cut.
    expect(endsWithEllipsis("(distant) ...jockey... JACK OUT... NOW")).toBe(false);
  });

  it("no mission briefing ends mid-sentence", () => {
    for (const mission of SPRAWL) {
      const text = mission.briefing;
      if (!text) continue;
      expect(endsWithEllipsis(text), `${mission.id} trails off: ${text.slice(-30)}`).toBe(false);
      expect(
        /[.!?]["')\]]?$/.test(text),
        `${mission.id} does not end on a sentence`,
      ).toBe(true);
    }
  });

  it("no authored dialogue line carries a cut marker", () => {
    // "…" (U+2026) is what a machine appends when it cuts; it appears nowhere
    // in the authored text, so its presence is always a truncation. "..." is
    // authored style — `ice_black_intro`'s voice fading — and stays.
    for (const [id, dialogue] of Object.entries(dialoguesData.dialogues)) {
      for (const line of dialogue.lines) {
        const text = line.text_en ?? "";
        expect(text, `${id} carries a cut marker`).not.toContain("…");
      }
    }
  });

  it("keeps every briefing readable — long enough to say something, short enough to fit", () => {
    for (const mission of SPRAWL) {
      const text = mission.briefing;
      if (!text) continue;
      expect(text.length, `${mission.id} is too short to brief with`).toBeGreaterThan(40);
      expect(text.length, `${mission.id} is too long for one screen`).toBeLessThanOrEqual(240);
    }
  });
});

describe("ADR-0300 — the briefings fit, on both screens, at every layout", () => {
  it("draws nothing past the edge on the briefing screen", () => {
    for (const [cols, rows] of LAYOUTS) {
      for (const mission of SPRAWL) {
        if (!mission.briefing) continue;
        takeClippedText();
        renderMissionBriefing(
          mission.title,
          mission.fixer,
          mission.briefing,
          cols,
          rows,
        );
        expect(
          takeClippedText(),
          `${mission.id} clips at ${cols}x${rows}`,
        ).toEqual([]);
      }
    }
  });

  // ADR-0316: the Korean briefs arrive from the fiction now. Korean glyphs are
  // wider than Latin ones, so they get their own pass at every layout.
  it("draws nothing past the edge with a Korean briefing", () => {
    let checked = 0;
    for (const [cols, rows] of LAYOUTS) {
      for (const mission of SPRAWL) {
        if (!mission.briefing_ko) continue;
        checked += 1;
        takeClippedText();
        renderMissionBriefing(
          mission.title_ko ?? mission.title,
          mission.fixer,
          mission.briefing_ko,
          cols,
          rows,
        );
        expect(
          takeClippedText(),
          `${mission.id} Korean briefing clips at ${cols}x${rows}`,
        ).toEqual([]);
      }
    }
    expect(checked).toBeGreaterThan(0);
  });

  it("draws nothing past the edge on the mission list preview", () => {
    for (const [cols, rows] of LAYOUTS) {
      for (const mission of SPRAWL) {
        if (!mission.briefing) continue;
        takeClippedText();
        renderMissionList(["[1] A mission"], 0, cols, rows, mission.briefing);
        expect(
          takeClippedText(),
          `${mission.id} clips in the list at ${cols}x${rows}`,
        ).toEqual([]);
      }
    }
  });

  it("the list preview says when it is showing only part of the job", () => {
    // The preview is three lines; a long briefing must not look complete.
    const long = SPRAWL.map((m) => m.briefing)
      .filter((b): b is string => typeof b === "string")
      .sort((a, b) => b.length - a.length)[0];
    expect(long).toBeDefined();
    expect((long ?? "").length).toBeGreaterThan(216);
    const grid = renderMissionList(["[1] A mission"], 0, 80, 50, long ?? null);
    const text = grid.cells.map((row) => row.map((c) => c.char).join("")).join("\n");
    expect(text).toContain("…");
    // And a short one needs no mark.
    const short = "A quick job. In and out.";
    const clean = renderMissionList(["[1] A mission"], 0, 80, 50, short);
    const cleanText = clean.cells
      .map((row) => row.map((c) => c.char).join(""))
      .join("\n");
    expect(cleanText).toContain("A quick job.");
    expect(cleanText).not.toContain("…");
  });
});

describe("ADR-0317 — the briefing is a file, not a line the fixer says", () => {
  it("names the fixer as whose job it is, not as the speaker", () => {
    const mission = SPRAWL.find((m) => m.briefing) ?? SPRAWL[0];
    const grid = renderMissionBriefing(
      mission?.title ?? "Job",
      mission?.fixer ?? "finn",
      mission?.briefing ?? "A job.",
      80,
      50,
    );
    const text = grid.cells.map((row) => row.map((c) => c.char).join("")).join("\n");
    expect(text).toContain(`Fixer: ${(mission?.fixer ?? "finn").toUpperCase()}`);
    // The summary is third person; printing it after a speaker colon claimed
    // the fixer said it.
    expect(text).not.toContain("FINN:");
  });
});
