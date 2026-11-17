/** ADR-0317 (3b) — the beats that arrive mid-run.
 *
 * The construct warns before the first fight and speaks after the first win.
 * Those two would not fit inline on the encounter or loot panels (the encounter
 * screen's own ICE voice already had to be trimmed to keep its footer), so they
 * get a full-screen card — the same shape the run's opening beat uses.
 *
 * The ending gets no card: the ending screen already has room under the
 * verdict, so the sign-off sits there instead of asking for one more keypress
 * after the run is over.
 */
import { describe, expect, it } from "vitest";
import { renderBeatCard } from "../src/renderer/beat_card";
import { renderEndingScreen } from "../src/renderer/ending";
import {
  endingSignoffBeat,
  firstFightWarningBeat,
  firstVictoryBeat,
  flatlineBeat,
} from "../src/core/state/event_beats";
import type { Grid } from "../src/core/types";

const text = (grid: Grid): string =>
  grid.cells.map((row) => row.map((cell) => cell.char).join("")).join("\n");

describe("ADR-0317 (3b) — beat card", () => {
  it("shows the title, the voice and one exit line", () => {
    const beat = firstFightWarningBeat();
    expect(beat).not.toBeNull();
    const drawn = text(renderBeatCard("ICE AHEAD", beat!, 80, 50));
    expect(drawn).toContain("ICE AHEAD");
    expect(drawn).toContain("Dixie Flatline");
    expect(drawn).toContain("already awake");
    expect(drawn).toContain("PRESS ANY KEY");
  });

  it("wraps the warning instead of cutting it at 40 columns", () => {
    const beat = firstFightWarningBeat();
    const drawn = text(renderBeatCard("ICE AHEAD", beat!, 40, 60));
    for (const row of drawn.split("\n")) {
      expect(row.length).toBeLessThanOrEqual(40);
    }
    expect(drawn).toContain("already awake");
    // The last line is the one a naive renderer would lose (it wraps).
    expect(drawn).toContain("flatline");
    expect(drawn).toContain("construct");
  });

  // ADR-0317 3b: the one moment the story went silent was the one it had been
  // building to — she says she can only watch, and then said nothing when it
  // happened. The text is new (the design file had no death beat).
  it("speaks the death beat", () => {
    const beat = flatlineBeat();
    expect(beat).not.toBeNull();
    const drawn = text(renderBeatCard("FLATLINE", beat!, 80, 50));
    expect(drawn).toContain("FLATLINE");
    expect(drawn).toContain("Dixie Flatline");
    expect(drawn).toContain("I'm sorry");
    expect(drawn).toContain("nothing left in there");
  });

  it("speaks the victory beat too", () => {
    const beat = firstVictoryBeat();
    const drawn = text(renderBeatCard("FIRST BLOOD", beat!, 80, 50));
    expect(drawn).toContain("FIRST BLOOD");
    expect(drawn).toContain("Not bad");
    expect(drawn).toContain("Finn is waiting");
  });
});

describe("ADR-0317 (3b) — ending sign-off", () => {
  it("speaks the construct's last word under the verdict", () => {
    const beat = endingSignoffBeat();
    expect(beat).not.toBeNull();
    const drawn = text(
      renderEndingScreen("arc2_status_quo", 80, 50, null, beat),
    );
    expect(drawn).toContain("Dixie Flatline");
    expect(drawn).toContain("It's over");
    expect(drawn).toContain("moves on");
  });

  it("adds nothing when there is no sign-off", () => {
    const drawn = text(renderEndingScreen("arc2_status_quo", 80, 50, null, null));
    expect(drawn).not.toContain("Dixie Flatline");
  });

  // The sign-off is dropped rather than crowding the run's numbers if it ever
  // stops fitting, so every supported layout has to still show it.
  it("survives at every supported layout", () => {
    const beat = endingSignoffBeat();
    for (const [cols, rows] of [
      [40, 60],
      [60, 40],
      [80, 50],
    ] as const) {
      const drawn = text(renderEndingScreen("arc2_status_quo", cols, rows, null, beat));
      expect(drawn, `${cols}x${rows} lost the sign-off`).toContain("Dixie Flatline");
      for (const row of drawn.split("\n")) {
        expect(row.length).toBeLessThanOrEqual(cols);
      }
    }
  });
});
