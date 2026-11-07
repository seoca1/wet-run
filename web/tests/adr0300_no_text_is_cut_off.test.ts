/**
 * ADR-0300 — a line that does not fit must fail the build, not lose its digits.
 *
 * The loot screen shipped twice with prices cut mid-number ("+75 HP → 2") because
 * a line can only be checked against a width at the moment it is drawn. `setText`
 * now records what it had to cut, so a test can render every screen at every
 * layout and assert the list is empty.
 *
 * The first case proves the instrument works — a guard that can silently record
 * nothing is worse than no guard.
 */
import { describe, expect, it } from "vitest";
import { makeGrid, setText, takeClippedText } from "../src/core/grid";
import { renderRunScreen } from "../src/renderer/run_screen";
import { runState } from "./view_fixtures";

const LAYOUTS = [
  [40, 60],
  [60, 40],
  [80, 50],
] as const;

function lootState() {
  const base = runState({
    runPhase: "loot",
    message: "Recovered +500 credits. Loot: ice_shard x2",
  });
  return {
    ...base,
    player: { ...base.player, alarm: 80, hp: 150, maxHp: 300 },
  };
}

describe("ADR-0300 · the cut recorder", () => {
  it("records a line that runs past the right edge", () => {
    // Given: a 10-column grid.
    const grid = makeGrid(10, 3);
    takeClippedText();

    // When: 16 characters are drawn at x = 0.
    setText(grid, 0, 0, "0123456789ABCDEF");

    // Then: the whole string is recorded, so the caller can name it.
    expect(takeClippedText()).toEqual(["0123456789ABCDEF"]);
  });

  it("records nothing when the line fits, and drains on read", () => {
    // Given
    const grid = makeGrid(20, 3);
    takeClippedText();

    // When
    setText(grid, 2, 0, "fits fine");

    // Then: empty, and the record stays empty on the next read.
    expect(takeClippedText()).toEqual([]);
    expect(takeClippedText()).toEqual([]);
  });
});

describe.each([
  ["loot with a full trace", lootState()],
  ["loot with no trace", runState({ runPhase: "loot", message: "No rewards" })],
  ["matrix", runState({ runPhase: "matrix" })],
  ["ending", runState({ runPhase: "ending", endingChoice: "arc4_liberation_front" })],
] as const)("ADR-0300 · %s", (_name, state) => {
  it.each(LAYOUTS)("draws nothing past the edge at %ix%i", (w, h) => {
    // Given / When
    takeClippedText();
    renderRunScreen(state as never, w, h);

    // Then
    expect(takeClippedText()).toEqual([]);
  });
});
