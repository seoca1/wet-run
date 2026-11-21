/** Which jockey prologues this profile has watched to the end (ADR-0317 3b).
 *
 * The prologue is the run's opening beat, so it plays on every run — and the
 * story does not change between runs. A player who has watched it needs to know
 * that, because otherwise ESC looks like it might skip something they have not
 * read. The screen says so now.
 *
 * "Watched" means watched to the end: a player who skips has not seen it, and
 * the marker would be a lie. One JSON array of jockey modes, the same shape the
 * ICE taglines use.
 */
import type { OnboardingStorage } from "./onboarding";

/** localStorage key: a JSON array of prologue modes that have been watched. */
export const PROLOGUE_SEEN_KEY = "wetrun_prologue_seen";

/** The prologues this profile has watched. Empty when storage is absent. */
export function seenPrologues(storage: OnboardingStorage | null | undefined): ReadonlySet<string> {
  if (!storage) return new Set();
  try {
    const raw = storage.getItem(PROLOGUE_SEEN_KEY);
    if (raw === null) return new Set();
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return new Set();
    return new Set(parsed.filter((m): m is string => typeof m === "string"));
  } catch {
    // A corrupt value must never break the frame that reads it.
    return new Set();
  }
}

/** Remember that this jockey's prologue has been watched. No-ops without
 * storage. */
export function markPrologueSeen(
  storage: OnboardingStorage | null | undefined,
  mode: string,
): void {
  if (!storage || mode.length === 0) return;
  try {
    const seen = new Set(seenPrologues(storage));
    seen.add(mode);
    storage.setItem(PROLOGUE_SEEN_KEY, JSON.stringify([...seen].sort()));
  } catch {
    // ignore — an unmarked prologue is better than a broken frame.
  }
}
