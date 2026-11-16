/** ADR-0317 (3b) — an ICE tagline is heard once per profile.
 *
 * The heard set lives in one localStorage key so a repeated tagline is noise
 * rather than content, and a blocked or corrupt value degrades to "heard
 * nothing" instead of throwing on a render frame.
 */
import { describe, expect, it } from "vitest";
import {
  ICE_INTRO_SEEN_KEY,
  markIceIntrosSeen,
  seenIceIntros,
} from "../src/core/state/ice_intros";

/** A localStorage stand-in that can also be made to throw. */
function fakeStorage(initial: Record<string, string> = {}, throwOn = "") {
  const map = new Map(Object.entries(initial));
  return {
    getItem(key: string): string | null {
      if (key === throwOn) throw new Error("blocked");
      return map.get(key) ?? null;
    },
    setItem(key: string, value: string): void {
      if (key === throwOn) throw new Error("blocked");
      map.set(key, value);
    },
    raw: map,
  };
}

describe("ADR-0317 (3b) — heard ICE taglines", () => {
  it("starts empty and records what was heard", () => {
    const storage = fakeStorage();
    expect([...seenIceIntros(storage)]).toEqual([]);
    markIceIntrosSeen(storage, ["wisp"]);
    expect([...seenIceIntros(storage)]).toEqual(["wisp"]);
    markIceIntrosSeen(storage, ["black", "wisp"]);
    expect([...seenIceIntros(storage)].sort()).toEqual(["black", "wisp"]);
  });

  it("survives a corrupt value", () => {
    const storage = fakeStorage({ [ICE_INTRO_SEEN_KEY]: "{not json" });
    expect([...seenIceIntros(storage)]).toEqual([]);
    // A bad value is replaceable, not fatal.
    markIceIntrosSeen(storage, ["wisp"]);
    expect([...seenIceIntros(storage)]).toEqual(["wisp"]);
  });

  it("ignores a value that is not an array of strings", () => {
    const storage = fakeStorage({ [ICE_INTRO_SEEN_KEY]: '{"wisp":true}' });
    expect([...seenIceIntros(storage)]).toEqual([]);
  });

  it("degrades to empty when storage is absent or blocked", () => {
    expect([...seenIceIntros(null)]).toEqual([]);
    expect([...seenIceIntros(undefined)]).toEqual([]);
    const blocked = fakeStorage({}, ICE_INTRO_SEEN_KEY);
    expect([...seenIceIntros(blocked)]).toEqual([]);
    expect(() => markIceIntrosSeen(blocked, ["wisp"])).not.toThrow();
  });

  it("writes nothing when there is nothing to record", () => {
    const storage = fakeStorage();
    markIceIntrosSeen(storage, []);
    expect(storage.raw.has(ICE_INTRO_SEEN_KEY)).toBe(false);
  });
});
