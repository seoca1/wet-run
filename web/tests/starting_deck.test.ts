import { describe, it, expect } from "vitest";
import {
  STARTING_DECK_IDS,
  STARTING_DECK_SIZE,
  startingDeck,
} from "../src/core/state/starting_deck";
import { loadProgramsCatalog } from "../src/core/data_loaders";
import programsData from "../src/data/programs.json";

/**
 * ADR-0260 — the opening hand is chosen, not sorted.
 *
 * It used to be "the first five ids alphabetically", which happened to be one
 * attack and four defensive cards. The list is now deliberate: three cards
 * that press the attack and two that blunt the counter-attack.
 */
describe("starting deck", () => {
  const catalog = loadProgramsCatalog(programsData);

  it("resolves to as many programs as it lists", () => {
    const deck = startingDeck(catalog);
    expect(deck).toHaveLength(STARTING_DECK_IDS.length);
    expect(deck.map((p) => p.id)).toEqual([...STARTING_DECK_IDS]);
  });

  it("is the opening hand size", () => {
    expect(STARTING_DECK_IDS).toHaveLength(STARTING_DECK_SIZE);
  });

  it("ids are unique", () => {
    expect(new Set(STARTING_DECK_IDS).size).toBe(STARTING_DECK_IDS.length);
  });

  it("every id exists in the catalog (a data edit cannot silently drop one)", () => {
    for (const id of STARTING_DECK_IDS) {
      expect(catalog[id], `${id} is missing from programs.json`).toBeDefined();
    }
  });

  it("is not alphabetical, precisely because the order is a choice now", () => {
    const sorted = [...STARTING_DECK_IDS].sort();
    expect([...STARTING_DECK_IDS]).not.toEqual(sorted);
  });

  it("mixes offense and defence rather than stacking defence", () => {
    // `role` is the authored archetype; the starting hand must not be
    // all-guard, which is what made the opening so tanky (ADR-0260).
    const roles = STARTING_DECK_IDS.map(
      (id) => (programsData as Record<string, { role?: string }>)[id]?.role,
    );
    const guards = roles.filter((r) => r === "guard").length;
    expect(guards).toBeLessThanOrEqual(2);
  });

  it("stays at low tier so the opening teaches the basics", () => {
    for (const id of STARTING_DECK_IDS) {
      expect(catalog[id]!.tier, `${id} tier`).toBeLessThanOrEqual(3);
    }
  });

  it("skips ids the catalog lacks instead of returning undefined slots", () => {
    expect(startingDeck({})).toHaveLength(0);
  });
});
