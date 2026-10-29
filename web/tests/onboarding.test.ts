/** Onboarding tests (proposal P11) — first-boot tutorial auto-show +
 * combat-entry hint.
 *
 * These are the pure-module assertions extracted from `main.ts` (which
 * self-boots and therefore cannot be imported under vitest's `node` env),
 * following the `renderer/combat_grid.ts` / `renderer/status_hud.ts`
 * extraction pattern of ADR-0234.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import {
  COMBAT_ENTRY_HINT_LINES,
  TUTORIAL_COMPLETED_KEY,
  combatEntryHint,
  combatEntryHintFits,
  combatEntryHintRows,
  isTutorialCompleted,
  markTutorialCompleted,
  shouldAutoShowTutorial,
  type OnboardingStorage,
} from "../src/core/onboarding.ts";

/**
 * `main.ts` self-boots at import time (it calls `boot()`), so it cannot be
 * imported under vitest's `node` environment. The wiring contract is
 * therefore asserted against the source text — the same trick the ADR-0234
 * extraction avoided by moving the logic into pure modules, but the *call
 * sites* still need a regression guard.
 */
const mainSource = readFileSync(
  fileURLToPath(new URL("../src/main.ts", import.meta.url)),
  "utf-8",
);

/** In-memory storage stub — mirrors the `localStorage` surface we use. */
function makeStorage(
  initial: Record<string, string> = {},
): OnboardingStorage & { readonly map: Map<string, string> } {
  const map = new Map<string, string>(Object.entries(initial));
  return {
    map,
    getItem: (key) => map.get(key) ?? null,
    setItem: (key, value) => {
      map.set(key, value);
    },
  };
}

describe("P11 — tutorial completion flag", () => {
  it("uses the same localStorage key the tutorial overlay writes", () => {
    expect(TUTORIAL_COMPLETED_KEY).toBe("wetrun_tutorial_completed");
  });

  it("reports not-completed when the flag is absent", () => {
    expect(isTutorialCompleted(makeStorage())).toBe(false);
  });

  it("reports completed when the flag is 'true'", () => {
    const storage = makeStorage({ wetrun_tutorial_completed: "true" });
    expect(isTutorialCompleted(storage)).toBe(true);
  });

  it("treats any other flag value as not-completed", () => {
    const storage = makeStorage({ wetrun_tutorial_completed: "1" });
    expect(isTutorialCompleted(storage)).toBe(false);
  });

  it("reports not-completed when storage is null", () => {
    expect(isTutorialCompleted(null)).toBe(false);
  });

  it("survives a storage that throws on read", () => {
    const throwing: OnboardingStorage = {
      getItem: () => {
        throw new Error("blocked");
      },
      setItem: () => {},
    };
    expect(isTutorialCompleted(throwing)).toBe(false);
  });

  it("writes the completion flag", () => {
    const storage = makeStorage();
    markTutorialCompleted(storage);
    expect(storage.getItem(TUTORIAL_COMPLETED_KEY)).toBe("true");
  });

  it("survives a storage that throws on write", () => {
    const throwing: OnboardingStorage = {
      getItem: () => null,
      setItem: () => {
        throw new Error("quota exceeded");
      },
    };
    expect(() => markTutorialCompleted(throwing)).not.toThrow();
  });
});

describe("P11 — first-boot tutorial auto-show gate", () => {
  it("shows the tutorial on a first boot (flag absent)", () => {
    expect(shouldAutoShowTutorial(makeStorage())).toBe(true);
  });

  it("does not show the tutorial once the flag is set", () => {
    const storage = makeStorage({ wetrun_tutorial_completed: "true" });
    expect(shouldAutoShowTutorial(storage)).toBe(false);
  });

  it("shows the tutorial exactly once across repeated boots", () => {
    const storage = makeStorage();
    // First boot: the tutorial is entered, then the overlay completes.
    expect(shouldAutoShowTutorial(storage)).toBe(true);
    markTutorialCompleted(storage);
    // Every later boot short-circuits.
    expect(shouldAutoShowTutorial(storage)).toBe(false);
    expect(shouldAutoShowTutorial(storage)).toBe(false);
  });

  it("shows the tutorial when storage is unavailable (never blocks boot)", () => {
    expect(shouldAutoShowTutorial(null)).toBe(true);
  });

  it("does not show the tutorial when the storage read throws", () => {
    const throwing: OnboardingStorage = {
      getItem: () => {
        throw new Error("blocked");
      },
      setItem: () => {},
    };
    // A blocked storage must not crash the boot; the tutorial is shown and
    // the overlay's own completion write silently no-ops.
    expect(shouldAutoShowTutorial(throwing)).toBe(true);
  });
});

describe("P11 — combat-entry hint", () => {
  it("tells the player that 1-9 uses a program", () => {
    expect(combatEntryHint()).toContain("1-9");
    expect(combatEntryHint()).toContain("USE PROGRAM");
  });

  it("mentions the touch path so mobile players are not left out", () => {
    const all = COMBAT_ENTRY_HINT_LINES.join(" ");
    expect(all).toContain("touch");
  });

  it("mentions the alarm / flatline stakes", () => {
    expect(COMBAT_ENTRY_HINT_LINES.join(" ")).toContain("flatline");
  });

  it("places the hint above the hand row so it never covers the programs", () => {
    const rows = 50;
    const handRow = Math.max(8, rows - Math.floor(rows * 0.16));
    const hintRows = combatEntryHintRows(rows);
    expect(hintRows).toHaveLength(2);
    for (const row of hintRows) {
      expect(row).toBeLessThan(handRow);
    }
  });

  it("keeps the hint clear of the ice_intro banner band (rows 1,2,3,5)", () => {
    const rows = 50;
    const bannerRows = [1, 2, 3, 5];
    for (const row of combatEntryHintRows(rows)) {
      expect(bannerRows).not.toContain(row);
    }
  });

  it("fits on a standard combat grid", () => {
    expect(combatEntryHintFits(50)).toBe(true);
    expect(combatEntryHintFits(40)).toBe(true);
  });

  it("does not claim to fit on a degenerate grid", () => {
    expect(combatEntryHintFits(4)).toBe(false);
  });
});

describe("P11 — main.ts wiring", () => {
  it("gates the first-boot tutorial on the localStorage flag", () => {
    expect(mainSource).toContain("shouldAutoShowTutorial(localStorage)");
  });

  it("enters the tutorial from the boot path", () => {
    expect(mainSource).toContain("game.enterTutorial()");
  });

  it("exposes a tutorial entry point that resets and creates the overlay", () => {
    expect(mainSource).toMatch(/enterTutorial\(\): void \{/);
    expect(mainSource).toContain("createTutorialOverlay()");
  });

  it("draws the combat-entry hint lines onto the grid", () => {
    expect(mainSource).toContain("COMBAT_ENTRY_HINT_LINES");
    expect(mainSource).toContain("combatEntryHintRows");
    // The hint must actually reach the grid, not just be imported.
    expect(mainSource).toMatch(
      /COMBAT_ENTRY_HINT_LINES\.forEach\([\s\S]{0,240}setText\(/,
    );
  });

  it("shows the combat-entry hint only once", () => {
    expect(mainSource).toContain("combatEntryHintShown");
    // The guard must set the flag once the hint has been drawn.
    expect(mainSource).toMatch(
      /combatEntryHintShown[\s\S]{0,400}this\.combatEntryHintShown = true/,
    );
  });
});
