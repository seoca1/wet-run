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
