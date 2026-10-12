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
  arcOneMissionIds,
  FAR_GRID_LOCKED_MESSAGE,
  evaluateFarGridUnlock,
  farGridAvailable,
  farGridUnlocked,
  getCompletedMissions,
  isArcOneCleared,
  isFarGridUnlocked,
  recordMissionComplete,
  resetCompletedMissions,
  resetFarGridUnlocked,
  setFarGridUnlocked,
} from "../src/core/far_grid_gate";

const FLAG_STORAGE_KEY = "wetrun_far_grid_unlocked";
const COMPLETED_STORAGE_KEY = "wetrun_completed_missions";

beforeEach(() => {
  // Each test starts from a clean localStorage so writes don't leak between
  // test cases (mirrors tutorial.test.ts convention).
  try {
    localStorage.removeItem(FLAG_STORAGE_KEY);
    localStorage.removeItem(COMPLETED_STORAGE_KEY);
  } catch {
    // localStorage may be unavailable in some test environments — fall back.
  }
});

afterEach(() => {
  try {
    localStorage.removeItem(FLAG_STORAGE_KEY);
    localStorage.removeItem(COMPLETED_STORAGE_KEY);
  } catch {
    // ignore
  }
});

describe("far_grid_gate: locked-by-default", () => {
  it("returns false when localStorage has no entry (fresh save)", () => {
    expect(isFarGridUnlocked()).toBe(false);
  });

  it("returns false when the stored value is anything other than '1'", () => {
    localStorage.setItem(FLAG_STORAGE_KEY, "0");
    expect(isFarGridUnlocked()).toBe(false);
    localStorage.setItem(FLAG_STORAGE_KEY, "true");
    expect(isFarGridUnlocked()).toBe(false);
    localStorage.setItem(FLAG_STORAGE_KEY, "");
    expect(isFarGridUnlocked()).toBe(false);
    localStorage.setItem(FLAG_STORAGE_KEY, "garbage");
    expect(isFarGridUnlocked()).toBe(false);
  });
});

describe("far_grid_gate: unlocked-after-flag", () => {
  it("setFarGridUnlocked flips the flag and isFarGridUnlocked reads true", () => {
    expect(isFarGridUnlocked()).toBe(false);
    setFarGridUnlocked();
    expect(isFarGridUnlocked()).toBe(true);
    expect(localStorage.getItem(FLAG_STORAGE_KEY)).toBe("1");
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
    expect(localStorage.getItem(FLAG_STORAGE_KEY)).toBeNull();
  });
});

describe("far_grid_gate: persistence round-trip", () => {
  it("survives a simulated reload — write, reset module, read still true", () => {
    setFarGridUnlocked();
    expect(localStorage.getItem(FLAG_STORAGE_KEY)).toBe("1");
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
      "Clear all Sprawl Arc 1 missions to unlock the Far Grid",
    );
  });

  it("contains no emoji (tone discipline)", () => {
    // No emoji code points allowed in status strings (per AGENTS.md §6 + ADR-0010).
    const emojiRegex =
      /[\u{1F300}-\u{1FAFF}\u{1F600}-\u{1F64F}\u{1F900}-\u{1F9FF}\u{2600}-\u{27BF}]/u;
    expect(emojiRegex.test(FAR_GRID_LOCKED_MESSAGE)).toBe(false);
  });
});

describe("far_grid_gate: dynamic Arc-1 derivation", () => {
  it("derives the required set from the mission catalog (no hardcoded ids)", () => {
    const ids = arcOneMissionIds();
    expect(ids.length).toBe(6);
    expect(ids).toContain("data_retrieval");
    expect(ids).toContain("delivery_to_finn");
    expect(ids).toContain("first_jack");
    expect(ids).toContain("ice_run");
    expect(ids).toContain("tutorial_maze");
    expect(ids).toContain("watchdog_patrol");
    // Far-Grid tagged Arc-1 missions must NOT be in the Sprawl set.
    expect(ids).not.toContain("far_grid_prelude");
    expect(ids).not.toContain("don_mac_audit");
  });

  it("returns a frozen array reference (cannot be mutated by callers)", () => {
    const ids = arcOneMissionIds();
    expect(Object.isFrozen(ids)).toBe(true);
  });

  it("excludes Arc-1 missions from non-sprawl source universes", () => {
    const ids = arcOneMissionIds();
    for (const id of ids) {
      expect(id).not.toMatch(/^(far_grid_prelude|don_mac_audit|deathspiders_news|warren_meadow|blue_silk_wall|maidens_first_run|pollack_after_dark|hetmans_meeting|maurice_princes|dodgers_office|tin_soldiers_end|moat_burned_blue|rogers_backyard|arkady_in_orange)$/);
    }
  });
});

describe("far_grid_gate: completion record", () => {
  it("starts empty on a fresh save", () => {
    expect(getCompletedMissions()).toEqual([]);
  });

  it("recordMissionComplete adds an id and persists", () => {
    expect(recordMissionComplete("data_retrieval")).toBe(true);
    expect(getCompletedMissions()).toEqual(["data_retrieval"]);
    expect(
      JSON.parse(localStorage.getItem(COMPLETED_STORAGE_KEY) as string),
    ).toEqual(["data_retrieval"]);
  });

  it("recordMissionComplete returns false on duplicate id (idempotent)", () => {
    expect(recordMissionComplete("data_retrieval")).toBe(true);
    expect(recordMissionComplete("data_retrieval")).toBe(false);
    expect(getCompletedMissions()).toEqual(["data_retrieval"]);
  });

  it("recordMissionComplete rejects empty / non-string ids", () => {
    expect(recordMissionComplete("")).toBe(false);
    expect(getCompletedMissions()).toEqual([]);
  });

  it("getCompletedMissions is defensive against non-JSON payloads", () => {
    localStorage.setItem(COMPLETED_STORAGE_KEY, "{not json");
    expect(getCompletedMissions()).toEqual([]);
  });

  it("getCompletedMissions is defensive against non-array payloads", () => {
    localStorage.setItem(COMPLETED_STORAGE_KEY, JSON.stringify({ a: 1 }));
    expect(getCompletedMissions()).toEqual([]);
  });

  it("getCompletedMissions drops non-string entries", () => {
    localStorage.setItem(
      COMPLETED_STORAGE_KEY,
      JSON.stringify(["data_retrieval", 42, null, "", "delivery_to_finn"]),
    );
    expect(getCompletedMissions()).toEqual([
      "data_retrieval",
      "delivery_to_finn",
    ]);
  });

  it("resetCompletedMissions clears the record but leaves the flag intact", () => {
    setFarGridUnlocked();
    recordMissionComplete("data_retrieval");
    resetCompletedMissions();
    expect(getCompletedMissions()).toEqual([]);
    // Legacy flag survives — already-unlocked saves stay unlocked.
    expect(isFarGridUnlocked()).toBe(true);
  });
});

describe("far_grid_gate: full-clear predicate (isArcOneCleared)", () => {
  it("returns false on a fresh save (no completions recorded)", () => {
    expect(isArcOneCleared()).toBe(false);
  });

  it("returns false when 5 of 6 required ids are recorded", () => {
    const ids = arcOneMissionIds();
    expect(ids.length).toBe(6);
    for (let i = 0; i < 5; i++) {
      expect(recordMissionComplete(ids[i] as string)).toBe(true);
    }
    expect(isArcOneCleared()).toBe(false);
  });

  it("returns true when all 6 required ids are recorded", () => {
    for (const id of arcOneMissionIds()) {
      recordMissionComplete(id);
    }
    expect(isArcOneCleared()).toBe(true);
  });

  it("returns true vacuously when the required set is empty", () => {
    expect(isArcOneCleared([])).toBe(true);
  });

  it("accepts an explicit required set (test isolation from catalog)", () => {
    expect(isArcOneCleared(["a", "b", "c"])).toBe(false);
    recordMissionComplete("a");
    recordMissionComplete("b");
    expect(isArcOneCleared(["a", "b", "c"])).toBe(false);
    recordMissionComplete("c");
    expect(isArcOneCleared(["a", "b", "c"])).toBe(true);
  });

  it("ignores completion of non-required ids (far-grid Arc-1 stays irrelevant)", () => {
    recordMissionComplete("far_grid_prelude");
    recordMissionComplete("don_mac_audit");
    expect(isArcOneCleared()).toBe(false);
  });

  it("is referentially transparent for a fixed completed set", () => {
    recordMissionComplete("data_retrieval");
    recordMissionComplete("delivery_to_finn");
    expect(isArcOneCleared()).toBe(isArcOneCleared());
  });
});

describe("far_grid_gate: evaluateFarGridUnlock auto-path", () => {
  it("returns false when no Arc-1 clear has happened yet", () => {
    expect(evaluateFarGridUnlock()).toBe(false);
    expect(isFarGridUnlocked()).toBe(false);
  });

  it("returns false with 5 of 6 completions (gate stays locked)", () => {
    const ids = arcOneMissionIds();
    for (let i = 0; i < 5; i++) {
      recordMissionComplete(ids[i] as string);
    }
    expect(evaluateFarGridUnlock()).toBe(false);
    expect(isFarGridUnlocked()).toBe(false);
  });

  it("returns true and flips the flag exactly when all 6 ids are recorded", () => {
    const ids = arcOneMissionIds();
    for (let i = 0; i < ids.length - 1; i++) {
      recordMissionComplete(ids[i] as string);
      expect(evaluateFarGridUnlock()).toBe(false);
    }
    recordMissionComplete(ids[ids.length - 1] as string);
    expect(evaluateFarGridUnlock()).toBe(true);
    expect(isFarGridUnlocked()).toBe(true);
  });

  it("is idempotent — re-evaluating an already-unlocked save is a no-op", () => {
    for (const id of arcOneMissionIds()) recordMissionComplete(id);
    expect(evaluateFarGridUnlock()).toBe(true);
    expect(evaluateFarGridUnlock()).toBe(false);
    expect(isFarGridUnlocked()).toBe(true);
  });

  it("does NOT re-lock a save that was unlocked under the legacy rule", () => {
    // Phase 2 rule: any Arc 1 clear flipped the flag.
    setFarGridUnlocked();
    // Phase 2 tightening: completed-mission record is empty (legacy save),
    // full-clear predicate is false — but the flag must stay "1".
    expect(isArcOneCleared()).toBe(false);
    expect(evaluateFarGridUnlock()).toBe(false);
    expect(isFarGridUnlocked()).toBe(true);
  });

  it("farGridUnlocked ORs the legacy flag and the full-clear predicate", () => {
    // Legacy-only branch
    setFarGridUnlocked();
    expect(farGridUnlocked()).toBe(true);
    resetFarGridUnlocked();
    expect(farGridUnlocked()).toBe(false);
    // Full-clear-only branch
    for (const id of arcOneMissionIds()) recordMissionComplete(id);
    expect(isFarGridUnlocked()).toBe(false);
    expect(isArcOneCleared()).toBe(true);
    expect(farGridUnlocked()).toBe(true);
  });
});