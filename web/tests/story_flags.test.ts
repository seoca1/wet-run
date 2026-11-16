/** ADR-0317 (3b) — one-time beats are remembered per profile.
 *
 * The construct warns you before your first fight and congratulates you after
 * your first win. Both are worth hearing once; after that they are noise. A
 * blocked or corrupt localStorage degrades to "not heard", which repeats the
 * line rather than breaking the frame that reads it.
 */
import { describe, expect, it } from "vitest";
import {
  beatKey,
  hasHeardBeat,
  markBeatHeard,
  type StoryBeatFlag,
} from "../src/core/state/story_flags";

const FLAGS: readonly StoryBeatFlag[] = ["first_fight_warning", "first_victory"];

function fakeStorage(initial: Record<string, string> = {}, throwOn = "") {
  const map = new Map(Object.entries(initial));
  return {
    getItem: (key: string): string | null => {
      if (key === throwOn) throw new Error("blocked");
      return map.get(key) ?? null;
    },
    setItem: (key: string, value: string): void => {
      if (key === throwOn) throw new Error("blocked");
      map.set(key, value);
    },
    raw: map,
  };
}

describe("ADR-0317 (3b) — one-time beats", () => {
  it("starts unheard and records each flag on its own key", () => {
    const storage = fakeStorage();
    for (const flag of FLAGS) expect(hasHeardBeat(storage, flag)).toBe(false);
    markBeatHeard(storage, "first_fight_warning");
    expect(hasHeardBeat(storage, "first_fight_warning")).toBe(true);
    // One flag does not answer for another.
    expect(hasHeardBeat(storage, "first_victory")).toBe(false);
    expect(storage.raw.has(beatKey("first_victory"))).toBe(false);
  });

  it("degrades to unheard when storage is absent or blocked", () => {
    expect(hasHeardBeat(null, "first_victory")).toBe(false);
    expect(hasHeardBeat(undefined, "first_victory")).toBe(false);
    const blocked = fakeStorage({}, beatKey("first_victory"));
    expect(hasHeardBeat(blocked, "first_victory")).toBe(false);
    expect(() => markBeatHeard(blocked, "first_victory")).not.toThrow();
  });

  it("treats any non-'true' value as unheard", () => {
    const storage = fakeStorage({ [beatKey("first_victory")]: "1" });
    expect(hasHeardBeat(storage, "first_victory")).toBe(false);
  });
});
