/** The jockey a run belongs to (ADR-0274).
 *
 * The graphic-novel prologue tells one story per jockey — `scene_case_*`,
 * `scene_sil_*`, `scene_kas_*`, keyed by the same `CharacterId` the novel
 * player uses (`novice`/`veteran`/`heretic`). Until now a run belonged to
 * nobody: the prologue handed over to mission select and the run began
 * anonymous, so the story the player had just read left no trace in the run or
 * its ending.
 *
 * Display-only. The jockey names the runner in the run intro and the ending
 * summary; it changes no number. Kept as a small table so the screen, the
 * intro and the ending read the same names.
 */
import type { CharacterId } from "../graphic_novel/graphic_novel_types";

export interface JockeyProfile {
  readonly id: CharacterId;
  /** The handle shown on screens. */
  readonly handle: string;
  /** Who they are, in one line — used by the select screen. */
  readonly tagline: string;
}

export const JOCKEYS: ReadonlyArray<JockeyProfile> = [
  {
    id: "novice",
    handle: "CASE",
    // ADR-0278: the old line ("The deck is already warm") argued with the arc-1
    // intro ("The deck is cold in your hands"). This one keeps the "old
    // reflexes" idea without claiming a temperature the next screen contradicts.
    tagline: "New hands. Old reflexes. The deck remembers.",
  },
  {
    id: "veteran",
    handle: "SIL",
    tagline: "Louisiana money, corporate ice. She has done this before.",
  },
  {
    id: "heretic",
    handle: "KAS",
    tagline: "Manarase midnight. He is not here to be careful.",
  },
];

/** The handle for a jockey id, or null when the run belongs to nobody. */
export function jockeyHandle(id: string | null | undefined): string | null {
  if (id === null || id === undefined) return null;
  return JOCKEYS.find((j) => j.id === id)?.handle ?? null;
}

/** Narrow an arbitrary string to a jockey id (save data is untrusted). */
export function isJockeyId(value: unknown): value is CharacterId {
  return JOCKEYS.some((j) => j.id === value);
}
