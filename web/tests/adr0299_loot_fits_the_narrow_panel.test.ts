/**
 * ADR-0299 — the loot screen has to fit at 40 columns.
 *
 * ADR-0295-0298 grew the loot screen from four options to eight, and the offer
 * lines grew with it. At 40 columns (and at 60) they were clipped mid-word:
 *
 *   5 INTEL           30cr — name the rout
 *   8 SYPHON          10 COST — +75 HP → 2
 *
 * The clipped part is the PRICE, which is the one thing the screen exists to
 * state. Narrow layouts now get short forms that keep every number, and the
 * panel's footer is built from what is actually offered instead of the stale
 * "1-3: card | 4: repair | 5: intel" that ADR-0287 had already outgrown.
 */
import { describe, expect, it } from "vitest";
import { renderRunScreen } from "../src/renderer/run_screen";
import { runState } from "./view_fixtures";

function rowTexts(state: Parameters<typeof renderRunScreen>[0], w: number, h: number): string[] {
  const view = renderRunScreen(state, w, h);
  return (view?.grid.cells ?? [])
    .map((row) => row.map((c) => c?.char ?? " ").join("").replace(/\s+$/, ""))
    .filter((line) => line.trim().length > 0);
}

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

describe.each([
  [40, 60],
  [60, 40],
] as const)("ADR-0299 · loot at %ix%i", (w, h) => {
  it("keeps every price on screen", () => {
    // Given / When: the widest loot state the game can offer.
    const lines = rowTexts(lootState(), w, h);

    // Then: each option is present with its number intact — the old clip cut
    // "→ 70/100" down to "→ 7" and left a bare "10 CO".
    expect(lines.some((l) => l.includes("INTEL"))).toBe(true);
    expect(lines.some((l) => l.includes("VENT") && l.includes("70/100"))).toBe(true);
    expect(lines.some((l) => l.includes("BURN"))).toBe(true);
    expect(lines.some((l) => l.includes("SYPHON"))).toBe(true);
    expect(lines.some((l) => /4-8 options/.test(l))).toBe(true);
  });

  it("never prints a line wider than the panel", () => {
    // Given / When
    const lines = rowTexts(lootState(), w, h);

    // Then: nothing spills past the right edge.
    for (const line of lines) expect(line.length).toBeLessThanOrEqual(w);
  });
});

describe("ADR-0299 · the wide layout keeps the readable wording", () => {
  it("spells the options out at 80 columns", () => {
    // Given / When
    const lines = rowTexts(lootState(), 80, 50);

    // Then: the full sentences survive where there is room, and the footer
    // names every exit instead of stopping at intel.
    expect(lines.some((l) => l.includes("name the routes ahead"))).toBe(true);
    expect(lines.some((l) => l.includes("7: burn") && l.includes("8: syphon"))).toBe(
      true,
    );
  });
});
