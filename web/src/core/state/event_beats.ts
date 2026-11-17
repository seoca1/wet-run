/** Event beats (ADR-0317 migration step 3b) — the run speaks the authored NPC
 * dialogue.
 *
 * `web/src/data/event_dialogues.json` (copied from
 * `docs/design/story/event_dialogues.json` by
 * `scripts/tools/import_event_dialogues.py`) holds the authored beats: the
 * companion's first words, the ICE tag-lines, the post-combat relief, the
 * endings. Nothing read it until now — the graphic-novel prologue carried the
 * story and the run was silent. This module is the one place a dialogue id
 * becomes the lines a screen shows, so a screen cannot drift from the data.
 *
 * Beats are display-only, exactly like the run intro (ADR-0272): nothing here
 * touches `GameState`, nothing is saved, and a resumed run replays nothing.
 */
import eventDialogues from "../../data/event_dialogues.json";
import type { Language } from "../i18n";

/** A spoken beat: who is talking, and what they say.
 *
 * `speaker` is set only when every line has the same voice — the screens then
 * print it once as a heading. When a beat has more than one voice (Black ICE
 * answers with the Narrator and Dixie), `speaker` is empty and each line is
 * already prefixed with its own, so nothing is misattributed.
 */
export interface DialogueBeat {
  readonly speaker: string;
  readonly lines: readonly string[];
}

/** The slice of the data file this module reads. */
interface DialogueLine {
  readonly speaker?: string;
  readonly speaker_ko?: string;
  readonly text_en?: string;
  readonly text_ko?: string;
}

interface Dialogue {
  readonly npc?: string;
  readonly lines?: readonly DialogueLine[];
}

const DIALOGUES: Readonly<Record<string, Dialogue>> = (
  eventDialogues as { dialogues?: Record<string, Dialogue> }
).dialogues ?? {};

/** How many lines of a beat a card shows. Kept small: the run intro is a card,
 * not a conversation, and the player should be in the matrix in one keypress. */
export const BEAT_LINES = 3;

/** ICE taglines are shorter — an ICE broadcasts a warning, not a speech. */
export const ICE_BEAT_LINES = 3;

/** The line's text in the requested language, falling back to English. */
function lineText(line: DialogueLine, language: Language): string {
  const ko = language === "ko" ? line.text_ko : undefined;
  return (ko && ko.length > 0 ? ko : line.text_en) ?? "";
}

/** The speaker's name in the requested language, falling back to English. */
function speakerName(line: DialogueLine, language: Language): string {
  const ko = language === "ko" ? line.speaker_ko : undefined;
  return (ko && ko.length > 0 ? ko : line.speaker) ?? "";
}

/** Turn a dialogue id into a beat a screen can show.
 *
 * Returns `null` for an unknown id, or for a dialogue whose lines are all
 * empty — a screen asked for a beat it cannot speak gets nothing, never a
 * placeholder that pretends the story said something.
 */
export function dialogueBeat(
  id: string,
  language: Language = "en",
  maxLines: number = BEAT_LINES,
): DialogueBeat | null {
  const spoken = (DIALOGUES[id]?.lines ?? [])
    .map((line) => ({
      speaker: speakerName(line, language),
      text: lineText(line, language),
    }))
    .filter((line) => line.text.length > 0)
    .slice(0, Math.max(1, maxLines));
  const first = spoken[0];
  if (first === undefined) return null;
  // One voice -> a heading. Several voices -> each line names its own, so a
  // line is never attributed to whoever spoke first.
  const oneVoice =
    spoken.every((line) => line.speaker === first.speaker) &&
    first.speaker.length > 0;
  return {
    speaker: oneVoice ? first.speaker : "",
    lines: spoken.map((line) =>
      oneVoice || line.speaker.length === 0
        ? line.text
        : `${line.speaker}: ${line.text}`,
    ),
  };
}

/** The run's opening beat: the companion's first words, once per profile.
 *
 * The construct only introduces herself on the first jack-in — a player who
 * has finished a run has already met her, and a resumed run (CONTINUE) never
 * replays its opening. `finishedRuns` is `runsFinished(storage)` (ADR-0315).
 */
export function runOpeningBeat(
  finishedRuns: number,
  language: Language = "en",
): DialogueBeat | null {
  if (finishedRuns > 0) return null;
  return dialogueBeat("dixie_intro", language);
}

/** An ICE's own tagline, if it has one (ADR-0317 3b).
 *
 * The design file names these `ice_<catalog id>_intro`, so the mapping is the
 * ICE's own id — there is nothing to guess and no table to keep in sync. Most
 * ICE are silent, as the design file says they should be; only the ones with a
 * tagline return a beat, and `null` means "this one says nothing".
 */
export function iceIntroBeat(
  iceId: string,
  language: Language = "en",
): DialogueBeat | null {
  return dialogueBeat(`ice_${iceId}_intro`, language, ICE_BEAT_LINES);
}

/** How many lines a story card shows. Roomier than the run intro: these are
 * read once, at a beat the player stopped for. */
export const STORY_BEAT_LINES = 4;

/** The construct's warning before the profile's first fight (ADR-0317 3b).
 *
 * The design line named a Wisp and a program the starter deck does not hold, so
 * it was rewritten to fit any ICE. It fires once per profile, at the first
 * combat, where the advice is something the player can act on.
 */
export function firstFightWarningBeat(
  language: Language = "en",
): DialogueBeat | null {
  return dialogueBeat("dixie_warning", language, STORY_BEAT_LINES);
}

/** The construct's relief after the profile's first win (ADR-0317 3b). */
export function firstVictoryBeat(language: Language = "en"): DialogueBeat | null {
  return dialogueBeat("dixie_postcombat", language, STORY_BEAT_LINES);
}

/** How many lines a conversation card shows. The fixer's introduction is five;
 * the other debriefs are four. */
export const CONVERSATION_BEAT_LINES = 5;

/** The fixer introduces himself (ADR-0317 3b).
 *
 * `finn_intro` was authored for the first time the player walks into his office
 * and was never wired: the game's first contract started with no introduction to
 * the man handing it out. It plays once per profile, on a card before the first
 * briefing — which is his office, and which the game never opened.
 */
export function finnIntroBeat(language: Language = "en"): DialogueBeat | null {
  return dialogueBeat("finn_intro", language, CONVERSATION_BEAT_LINES);
}

/** The fixer's debrief after the contract's first job (ADR-0317 3b).
 *
 * `finn_followup` was authored for "the player returns from the first
 * successful run", which is exactly the first leg transition — a moment the
 * campaign created and nothing spoke at.
 */
export function firstReturnBeat(language: Language = "en"): DialogueBeat | null {
  return dialogueBeat("finn_followup", language, STORY_BEAT_LINES);
}

/** Tessier-Ashpool's call after the contract's second job (ADR-0317 3b).
 *
 * `ta_warning` escalates the debrief: the fixer says they noticed, and then
 * they call. Authored, and unwired until the campaign gave it a moment.
 */
export function ashpoolCallBeat(language: Language = "en"): DialogueBeat | null {
  return dialogueBeat("ta_warning", language, STORY_BEAT_LINES);
}

/** The construct's last word when the runner flatlines (ADR-0317 3b).
 *
 * The design file had no death beat, so the one moment the story went silent was
 * the one it had been building to: she says "If you flatline, I can't save you.
 * I'm a construct. I just watch" before the first fight, and then said nothing
 * when it happened. The text is new and owner-reviewable — Jev picked it at
 * confidence 0.2, which is taste rather than deduction.
 */
export function flatlineBeat(language: Language = "en"): DialogueBeat | null {
  return dialogueBeat("dixie_flatline", language, STORY_BEAT_LINES);
}

/** The construct's last word on the ending screen (ADR-0317 3b).
 *
 * The design's two ending scenes were written for a burn/keep choice the game
 * never had — its endings are arc outcomes — so they were replaced by one
 * arc-agnostic sign-off that fits every ending the screen can show.
 */
export function endingSignoffBeat(
  language: Language = "en",
): DialogueBeat | null {
  return dialogueBeat("dixie_signoff", language, STORY_BEAT_LINES);
}
