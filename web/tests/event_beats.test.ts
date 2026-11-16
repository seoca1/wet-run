/** ADR-0317 (3b) — the run speaks the authored NPC dialogue.
 *
 * `docs/design/story/event_dialogues.json` was written for the game and never
 * read by it; the graphic-novel prologue carried the story instead. The importer
 * copies it into `web/src/data/` and this module is the one place a dialogue id
 * becomes a beat a screen can show.
 */
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import {
  BEAT_LINES,
  dialogueBeat,
  runOpeningBeat,
} from "../src/core/state/event_beats";

const design = JSON.parse(
  readFileSync(
    fileURLToPath(
      new URL("../../docs/design/story/event_dialogues.json", import.meta.url),
    ),
    "utf-8",
  ),
) as {
  dialogues: Record<
    string,
    { npc?: string; lines?: ReadonlyArray<{ text_en?: string; text_ko?: string }> }
  >;
};

describe("ADR-0317 (3b) — event beats", () => {
  it("turns a dialogue id into a beat with a speaker and lines", () => {
    const beat = dialogueBeat("dixie_intro");
    expect(beat).not.toBeNull();
    expect(beat?.speaker).toBe("Dixie Flatline");
    expect(beat?.lines.length).toBeGreaterThanOrEqual(1);
    expect(beat?.lines.length).toBeLessThanOrEqual(BEAT_LINES);
    expect(beat?.lines[0]).toContain("Hey");
  });

  it("speaks Korean when asked, falling back to English per line", () => {
    const ko = dialogueBeat("dixie_intro", "ko");
    expect(ko).not.toBeNull();
    // The design file carries a Korean text for every line of this beat.
    expect(ko?.lines[0]).toMatch(/[\uac00-\ud7a3]/);
    expect(ko?.speaker).toMatch(/[\uac00-\ud7a3]/);
  });

  it("returns nothing for an unknown id or an empty dialogue", () => {
    expect(dialogueBeat("no_such_beat")).toBeNull();
  });

  it("respects the line cap", () => {
    const one = dialogueBeat("dixie_intro", "en", 1);
    expect(one?.lines.length).toBe(1);
  });

  it("gives the opening beat only to a profile that has not finished a run", () => {
    const first = runOpeningBeat(0);
    expect(first).not.toBeNull();
    expect(first?.speaker).toBe("Dixie Flatline");
    expect(runOpeningBeat(1)).toBeNull();
    expect(runOpeningBeat(12)).toBeNull();
  });

  it("every dialogue in the design file can be spoken in English", () => {
    for (const id of Object.keys(design.dialogues)) {
      const beat = dialogueBeat(id, "en");
      expect(beat, `"${id}" produced no beat`).not.toBeNull();
      expect(beat?.speaker.length, `"${id}" has no speaker`).toBeGreaterThan(0);
    }
  });
});
