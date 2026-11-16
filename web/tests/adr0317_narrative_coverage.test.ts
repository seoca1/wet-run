/**
 * ADR-0317 (3b) — the ledger: every authored dialogue is either spoken in game
 * or listed as unwired, with a reason.
 *
 * The design file is the source of truth for the story, and the app data is a
 * copy of it. The failure this guards is *silent drift*: a line gets authored,
 * imported, and then nothing reads it — which is exactly how the whole
 * `event_dialogues.json` sat unused while the graphic novel carried the story.
 * The story trace (`e2e/story_trace.spec.ts`) once drifted the same way: it was
 * opt-in and skipped, so it never noticed two new screens.
 *
 * So "what is wired" is a claim the build checks, not something to remember.
 */
import { describe, expect, it } from "vitest";
import eventDialogues from "../src/data/event_dialogues.json";
import iceTypes from "../src/data/ice_types.json";
import {
  endingSignoffBeat,
  firstFightWarningBeat,
  firstVictoryBeat,
  iceIntroBeat,
  runOpeningBeat,
} from "../src/core/state/event_beats";

const DATA: Readonly<Record<string, unknown>> = (
  eventDialogues as { dialogues: Record<string, unknown> }
).dialogues;

/** Dialogues the game does not speak yet, and why. Adding a line here is a
 * deliberate act: this table is the only place that says "not wired". */
const UNWIRED: Readonly<Record<string, string>> = {
  finn_intro: "hub dialogue — needs the dialogue-tree screen (ADR-0317 open question f)",
  finn_followup: "hub dialogue — needs the dialogue-tree screen (ADR-0317 open question f)",
  wim_hub: "hub dialogue — needs the dialogue-tree screen (ADR-0317 open question f)",
  maelcum_intro: "hub dialogue — needs the dialogue-tree screen (ADR-0317 open question f)",
  maelcum_caught: "hub dialogue — needs the dialogue-tree screen (ADR-0317 open question f)",
  ta_warning: "hub dialogue — needs the dialogue-tree screen (ADR-0317 open question f)",
  ice_hammer_intro: "no ICE in the catalog has the id 'hammer', so nothing can trigger it",
};

/** The dialogue ids the game can actually reach today. */
function wiredIds(): ReadonlySet<string> {
  const wired = new Set<string>();
  if (runOpeningBeat(0) !== null) wired.add("dixie_intro");
  if (firstFightWarningBeat() !== null) wired.add("dixie_warning");
  if (firstVictoryBeat() !== null) wired.add("dixie_postcombat");
  if (endingSignoffBeat() !== null) wired.add("dixie_signoff");
  for (const iceId of Object.keys(iceTypes)) {
    if (iceIntroBeat(iceId) !== null) wired.add(`ice_${iceId}_intro`);
  }
  return wired;
}

describe("ADR-0317 (3b) — narrative coverage ledger", () => {
  it("every authored dialogue is spoken in game or listed as unwired", () => {
    const wired = wiredIds();
    const missing = Object.keys(DATA).filter(
      (id) => !wired.has(id) && !(id in UNWIRED),
    );
    expect(
      missing,
      "these dialogues are neither wired nor listed in UNWIRED",
    ).toEqual([]);
  });

  it("the unwired list has no stale or invented entries", () => {
    const wired = wiredIds();
    const stale = Object.keys(UNWIRED).filter(
      (id) => wired.has(id) || !(id in DATA),
    );
    expect(
      stale,
      "these are wired now (or gone) — remove them from UNWIRED",
    ).toEqual([]);
  });

  it("every unwired entry says why, in a sentence", () => {
    for (const [id, reason] of Object.entries(UNWIRED)) {
      expect(reason.length, `"${id}" has no real reason`).toBeGreaterThan(20);
    }
  });

  it("the wired beats actually carry lines", () => {
    const beats = [
      runOpeningBeat(0),
      firstFightWarningBeat(),
      firstVictoryBeat(),
      endingSignoffBeat(),
      iceIntroBeat("wisp"),
    ];
    for (const beat of beats) {
      expect(beat).not.toBeNull();
      expect(beat?.lines.length ?? 0).toBeGreaterThan(0);
    }
  });

  // The adaptation this ledger was written for: the design line named a Wisp
  // and a program the starter deck does not hold. If it ever names one again,
  // the beat only fits one mission.
  it("the rewritten beats fit any ICE and any deck", () => {
    const text = [firstFightWarningBeat(), firstVictoryBeat()]
      .flatMap((beat) => beat?.lines ?? [])
      .join(" ");
    expect(text).not.toMatch(/wisp/i);
    expect(text).not.toMatch(/viral stun/i);
  });
});
