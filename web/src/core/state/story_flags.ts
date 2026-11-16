/** One-time story beats this profile has already heard (ADR-0317 3b).
 *
 * Some beats are worth hearing once and are noise after that: the construct's
 * warning before your first fight, her relief after your first win. Which ones
 * have been heard is per profile, the same way the tutorial and the run count
 * are (ADR-0315).
 *
 * One key per flag rather than one JSON blob: a corrupt value then costs one
 * beat, not the whole set, and the keys are readable in devtools.
 */
import type { OnboardingStorage } from "./onboarding";

/** The beats that fire once per profile. */
export type StoryBeatFlag = "first_fight_warning" | "first_victory";

const KEYS: Readonly<Record<StoryBeatFlag, string>> = {
  first_fight_warning: "wetrun_beat_first_fight",
  first_victory: "wetrun_beat_first_victory",
};

/** Has this profile already heard the beat? False without storage. */
export function hasHeardBeat(
  storage: OnboardingStorage | null | undefined,
  flag: StoryBeatFlag,
): boolean {
  if (!storage) return false;
  try {
    return storage.getItem(KEYS[flag]) === "true";
  } catch {
    // A blocked localStorage must never break the frame that reads it.
    return false;
  }
}

/** Remember that the beat has been heard. No-ops without storage. */
export function markBeatHeard(
  storage: OnboardingStorage | null | undefined,
  flag: StoryBeatFlag,
): void {
  if (!storage) return;
  try {
    storage.setItem(KEYS[flag], "true");
  } catch {
    // ignore — a repeated line is better than a broken frame.
  }
}

/** The storage key for a flag. Exported so tests and tools can read it. */
export function beatKey(flag: StoryBeatFlag): string {
  return KEYS[flag];
}
