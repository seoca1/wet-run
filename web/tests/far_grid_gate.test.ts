/** Tests for Far Grid entry gate (ADR-0213 Phase 2).
 *
 * Covers:
 * - locked-by-default on fresh save
 * - unlocked-after-flag (helper write/read round-trip)
 * - persistence round-trip across reset
 * - farGridAvailable pure predicate
 * - the lock-status message constant (English, no emoji)
 *
 * Note: pure helper module under `src/core/far_grid_gate.ts`. The hook
 * wiring (`state_actions.ts:applyLootAction`, `main.ts:selectMenuOption`,
 * and the menu renderer) is covered by the existing `state_actions.test.ts`
 * + `menu.test.ts` regression tests added in this commit.
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  FAR_GRID_LOCKED_MESSAGE,
  farGridAvailable,
  isFarGridUnlocked,
  resetFarGridUnlocked,
  setFarGridUnlocked,
} from "../src/core/far_grid_gate";

const STORAGE_KEY = "wetrun_far_grid_unlocked";

beforeEach(() => {
  // Each test starts from a clean localStorage so writes don't leak between
  // test cases (mirrors tutorial.test.ts convention).
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // localStorage may be unavailable in some test environments — fall back.
  }
});

afterEach(() => {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
});

describe("far_grid_gate: locked-by-default", () => {
  it("returns false when localStorage has no entry (fresh save)", () => {
    expect(isFarGridUnlocked()).toBe(false);
  });

  it("returns false when the stored value is anything other than '1'", () => {
    localStorage.setItem(STORAGE_KEY, "0");
    expect(isFarGridUnlocked()).toBe(false);
    localStorage.setItem(STORAGE_KEY, "true");
    expect(isFarGridUnlocked()).toBe(false);
    localStorage.setItem(STORAGE_KEY, "");
    expect(isFarGridUnlocked()).toBe(false);
    localStorage.setItem(STORAGE_KEY, "garbage");
    expect(isFarGridUnlocked()).toBe(false);
  });
});

describe("far_grid_gate: unlocked-after-flag", () => {
  it("setFarGridUnlocked flips the flag and isFarGridUnlocked reads true", () => {
    expect(isFarGridUnlocked()).toBe(false);
    setFarGridUnlocked();
    expect(isFarGridUnlocked()).toBe(true);
    expect(localStorage.getItem(STORAGE_KEY)).toBe("1");
  });

  it("setFarGridUnlocked is idempotent — returns false on re-call", () => {
    setFarGridUnlocked();
    expect(setFarGridUnlocked()).toBe(false);
    expect(isFarGridUnlocked()).toBe(true);
  });

  it("setFarGridUnlocked returns true only on the first flip", () => {
    expect(setFarGridUnlocked()).toBe(true);
    expect(setFarGridUnlocked()).toBe(false);
    expect(setFarGridUnlocked()).toBe(false);
  });

  it("resetFarGridUnlocked returns to the locked state", () => {
    setFarGridUnlocked();
    expect(isFarGridUnlocked()).toBe(true);
    resetFarGridUnlocked();
    expect(isFarGridUnlocked()).toBe(false);
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  });
});

describe("far_grid_gate: persistence round-trip", () => {
  it("survives a simulated reload — write, reset module, read still true", () => {
    setFarGridUnlocked();
    expect(localStorage.getItem(STORAGE_KEY)).toBe("1");
    // Simulate a fresh module import / page reload by re-reading only —
    // localStorage is the source of truth and the helper is stateless.
    expect(isFarGridUnlocked()).toBe(true);
    expect(isFarGridUnlocked()).toBe(true);
    // Cleanup
    resetFarGridUnlocked();
    expect(isFarGridUnlocked()).toBe(false);
  });

  it("survives reset+write sequence without leaking between tests", () => {
    // Pre-state: locked (from beforeEach)
    expect(isFarGridUnlocked()).toBe(false);
    setFarGridUnlocked();
    expect(isFarGridUnlocked()).toBe(true);
  });
});

describe("far_grid_gate: farGridAvailable pure predicate", () => {
  it("returns true when flag is true", () => {
    expect(farGridAvailable(true)).toBe(true);
  });

  it("returns false when flag is false", () => {
    expect(farGridAvailable(false)).toBe(false);
  });

  it("is referentially transparent — same input, same output", () => {
    expect(farGridAvailable(false)).toBe(farGridAvailable(false));
    expect(farGridAvailable(true)).toBe(farGridAvailable(true));
  });
});

describe("far_grid_gate: locked status message", () => {
  it("is the canonical locked-selection message (English, Gibson-detached)", () => {
    expect(FAR_GRID_LOCKED_MESSAGE).toBe(
      "Win a Sprawl Arc 1 mission to unlock the Far Grid",
    );
  });

  it("contains no emoji (tone discipline)", () => {
    // No emoji code points allowed in status strings (per AGENTS.md §6 + ADR-0010).
    const emojiRegex =
      /[\u{1F300}-\u{1FAFF}\u{1F600}-\u{1F64F}\u{1F900}-\u{1F9FF}\u{2600}-\u{27BF}]/u;
    expect(emojiRegex.test(FAR_GRID_LOCKED_MESSAGE)).toBe(false);
  });
});