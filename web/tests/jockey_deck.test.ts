/** ADR-0276 — the jockey decides how the run plays, not only whose it is.
 *
 * Each deck keeps the ADR-0260 shape (most cards press, at least one blunts —
 * the all-defense opening was measured and rejected there) and differs by one
 * or two thematic swaps. The curves are recorded in the ADR and measured with
 * `npm run balance -- --deck veteran|heretic`; this pins the composition, so a
 * deck edit cannot pass unnoticed.
 */
import { describe, expect, it } from "vitest";
import {
  JOCKEY_DECK_IDS,
  STARTING_DECK_IDS,
  STARTING_DECK_SIZE,
  startingDeck,
  startingDeckIds,
} from "../src/core/state/starting_deck";
import { loadProgramsCatalog } from "../src/core/data_loaders";
import programsData from "../src/data/programs.json";
import type { Program } from "../src/core/types";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const PROGRAMS = loadProgramsCatalog(programsData);

/** The authored `type` (attack/defense/support) from the raw JSON.
 *
 * `loadProgramsCatalog` drops it — the loaded `Program` keeps only `effect`,
 * which defaults to `"attack"` for every card. The shape claim is about the
 * authored intent, so read the JSON the catalog was built from. */
const authoredType = (id: string): string =>
  (programsData as Record<string, { type?: string }>)[id]?.type ?? "?";

describe("ADR-0276 — per-jockey starting decks", () => {
  it("has a deck per jockey plus the curated fallback", () => {
    expect(Object.keys(JOCKEY_DECK_IDS).sort()).toEqual([
      "heretic",
      "novice",
      "veteran",
    ]);
    expect(JOCKEY_DECK_IDS.novice).toEqual(STARTING_DECK_IDS);
    expect(startingDeckIds(null)).toEqual(STARTING_DECK_IDS);
    expect(startingDeckIds("nonsense")).toEqual(STARTING_DECK_IDS);
  });

  it("each deck is five distinct cards that exist in the catalog", () => {
    for (const [jockey, ids] of Object.entries(JOCKEY_DECK_IDS)) {
      expect(ids, jockey).toHaveLength(STARTING_DECK_SIZE);
      expect(new Set(ids).size, jockey).toBe(ids.length);
      for (const id of ids) {
        expect(PROGRAMS[id], `${jockey}: ${id}`).toBeDefined();
      }
    }
  });

  it("keeps the ADR-0260 shape: it presses and it does not turtle", () => {
    const press = (ids: readonly string[]) =>
      ids.filter((id) => authoredType(id) !== "defense").length;
    const blunt = (ids: readonly string[]) =>
      ids.filter((id) => authoredType(id) === "defense").length;
    for (const [jockey, ids] of Object.entries(JOCKEY_DECK_IDS)) {
      // ADR-0260 measured the alphabetical opening (one attacker, four
      // defensive/support) and rejected it as too passive. Every deck must
      // press with most of its cards and still hold a guard or two.
      expect(press(ids), jockey).toBeGreaterThanOrEqual(3);
      expect(blunt(ids), jockey).toBeGreaterThanOrEqual(1);
      expect(press(ids) + blunt(ids), jockey).toBe(5);
    }
  });

  it("the jockey decks are actually different from each other", () => {
    const decks = Object.entries(JOCKEY_DECK_IDS).map(([k, v]) => [
      k,
      v.join(","),
    ]);
    expect(new Set(decks.map(([, v]) => v)).size).toBe(decks.length);
  });

  it("resolves against a catalog and drops unknown ids", () => {
    expect(startingDeck(PROGRAMS, "veteran").map((p) => p.id)).toEqual([
      ...JOCKEY_DECK_IDS.veteran,
    ]);
    // A catalog missing one id must not crash the boot.
    const partial = { ...PROGRAMS } as Record<string, Program>;
    delete partial.exploit;
    expect(startingDeck(partial, "veteran")).toHaveLength(4);
  });

  it("main.ts deals the jockey's deck", () => {
    const main = readFileSync(
      fileURLToPath(new URL("../src/main.ts", import.meta.url)),
      "utf-8",
    ).replace(/\s+/g, "");
    // Trim the trailing `,` prettier may or may not add before the close: the
    // stable part is the call, not its formatting.
    expect(main).toContain(
      "startingDeck(programs,JOCKEYS[this.selectedJockey]?.id??null",
    );
  });
});
