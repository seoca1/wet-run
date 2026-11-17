/** ADR-0317 3b — a watched prologue is remembered, so the screen can say so.
 *
 * The prologue is the run's opening beat and the story does not change between
 * runs. A player who has watched it needs to know ESC is not skipping anything
 * they have not read. "Watched" means watched to the end: a player who skips has
 * not seen it, and the marker would be a lie.
 */
import { describe, expect, it } from "vitest";
import {
  PROLOGUE_SEEN_KEY,
  markPrologueSeen,
  seenPrologues,
} from "../src/core/state/prologue_seen";

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

describe("ADR-0317 3b — watched prologues", () => {
  it("starts empty and records each jockey on its own", () => {
    const storage = fakeStorage();
    expect([...seenPrologues(storage)]).toEqual([]);
    markPrologueSeen(storage, "novice");
    expect([...seenPrologues(storage)]).toEqual(["novice"]);
    markPrologueSeen(storage, "veteran");
    expect([...seenPrologues(storage)].sort()).toEqual(["novice", "veteran"]);
    // Idempotent: watching the same prologue twice changes nothing.
    markPrologueSeen(storage, "novice");
    expect([...seenPrologues(storage)].sort()).toEqual(["novice", "veteran"]);
  });

  it("survives a corrupt value", () => {
    const storage = fakeStorage({ [PROLOGUE_SEEN_KEY]: "{not json" });
    expect([...seenPrologues(storage)]).toEqual([]);
    markPrologueSeen(storage, "novice");
    expect([...seenPrologues(storage)]).toEqual(["novice"]);
  });

  it("ignores a value that is not an array of strings", () => {
    const storage = fakeStorage({ [PROLOGUE_SEEN_KEY]: '{"novice":true}' });
    expect([...seenPrologues(storage)]).toEqual([]);
  });

  it("degrades to empty when storage is absent or blocked", () => {
    expect([...seenPrologues(null)]).toEqual([]);
    expect([...seenPrologues(undefined)]).toEqual([]);
    const blocked = fakeStorage({}, PROLOGUE_SEEN_KEY);
    expect([...seenPrologues(blocked)]).toEqual([]);
    expect(() => markPrologueSeen(blocked, "novice")).not.toThrow();
  });

  it("records nothing for an empty mode", () => {
    const storage = fakeStorage();
    markPrologueSeen(storage, "");
    expect(storage.raw.has(PROLOGUE_SEEN_KEY)).toBe(false);
  });
});
