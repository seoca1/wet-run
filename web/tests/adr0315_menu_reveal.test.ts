/**
 * ADR-0315 — the menu grows with the player.
 *
 * A brand-new profile never sees the menu at all (the boot goes straight into a
 * run). When it does appear, it shows only what has something to offer: no
 * CONTINUE without a save, no FAR GRID before it unlocks, no archive/workshop
 * rows before a run has been finished, and no TUTORIAL once it is done.
 */
import { describe, expect, it } from "vitest";
import {
  MENU_OPTIONS,
  visibleMenuOptions,
  type MenuReveal,
} from "../src/renderer/menu_main";

const FRESH: MenuReveal = {
  hasSave: false,
  farGridUnlocked: false,
  runsFinished: 0,
  tutorialCompleted: false,
};

const RETURNING: MenuReveal = {
  hasSave: true,
  farGridUnlocked: true,
  runsFinished: 1,
  tutorialCompleted: true,
};

const keys = (r: MenuReveal) => visibleMenuOptions(r).map((o) => o.key);

describe("ADR-0315 · the menu reveal", () => {
  it("shows only the always-on entries to a fresh profile", () => {
    expect(keys(FRESH)).toEqual([
      "new_run",
      "graphic_novel",
      "tutorial",
      "settings",
      "help",
      "credits",
    ]);
  });

  it("hides CONTINUE without a save and FAR GRID before it unlocks", () => {
    expect(keys(FRESH)).not.toContain("continue");
    expect(keys(FRESH)).not.toContain("far_grid_hub");
    expect(keys({ ...FRESH, hasSave: true })).toContain("continue");
    expect(keys({ ...FRESH, farGridUnlocked: true })).toContain("far_grid_hub");
  });

  it("waits for a finished run before showing the archive and workshop", () => {
    for (const key of [
      "dungeon_crawl",
      "craft",
      "equipment",
      "hall_of_dead",
      "endings",
      "stats",
    ]) {
      expect(keys(FRESH), `${key} on a fresh profile`).not.toContain(key);
      expect(keys({ ...FRESH, runsFinished: 1 })).toContain(key);
    }
  });

  it("drops TUTORIAL once it has been completed", () => {
    expect(keys(FRESH)).toContain("tutorial");
    expect(keys({ ...FRESH, tutorialCompleted: true })).not.toContain(
      "tutorial",
    );
  });

  it("shows every entry except the finished tutorial to a returning player", () => {
    const expected = MENU_OPTIONS.map((o) => o.key).filter(
      (k) => k !== "tutorial",
    );
    expect(keys(RETURNING)).toEqual(expected);
  });

  it("never hides the game itself", () => {
    for (const key of ["new_run", "graphic_novel", "settings", "help", "credits"]) {
      expect(keys(FRESH)).toContain(key);
    }
  });
});
