/** Which ICE taglines this profile has already heard (ADR-0317 3b).
 *
 * The design file says ICE are usually silent, and a few broadcast a tagline.
 * A tagline is worth hearing once; after that it is noise, and a player who has
 * met a Wisp already knows what a Wisp says. So the heard set is remembered per
 * profile, the same way the tutorial and the run count are (ADR-0315).
 *
 * Storage is a single JSON array of ICE catalog ids. A blocked or unreadable
 * localStorage degrades to "nothing heard yet" — the tagline repeats, which is
 * harmless, rather than throwing on a render frame.
 */
import type { OnboardingStorage } from "./onboarding";

/** localStorage key: a JSON array of ICE ids whose tagline has been heard. */
export const ICE_INTRO_SEEN_KEY = "wetrun_ice_intro_seen";

/** The ICE ids this profile has already heard. Empty when storage is absent. */
export function seenIceIntros(storage: OnboardingStorage | null | undefined): ReadonlySet<string> {
  if (!storage) return new Set();
  try {
    const raw = storage.getItem(ICE_INTRO_SEEN_KEY);
    if (raw === null) return new Set();
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return new Set();
    return new Set(parsed.filter((id): id is string => typeof id === "string"));
  } catch {
    // A corrupt value must never break the frame that reads it.
    return new Set();
  }
}

/** Remember that these ICE taglines have been heard. No-ops without storage. */
export function markIceIntrosSeen(
  storage: OnboardingStorage | null | undefined,
  ids: readonly string[],
): void {
  if (!storage || ids.length === 0) return;
  try {
    const seen = new Set(seenIceIntros(storage));
    for (const id of ids) seen.add(id);
    storage.setItem(ICE_INTRO_SEEN_KEY, JSON.stringify([...seen].sort()));
  } catch {
    // ignore — a repeated tagline is better than a broken frame.
  }
}
