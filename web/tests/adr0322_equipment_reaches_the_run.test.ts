/**
 * ADR-0322 — the EQUIPMENT menu finally reaches the run.
 *
 * The defect this closes: the menu edited a `Game`-level loadout while a run
 * read `state.equipmentLoadout`, which `makeInitialState` builds as
 * `EMPTY_LOADOUT` and nothing filled. So equipping gear changed no number, and
 * the choice was lost on reload. The store is the missing half — persist the
 * slots, hand them to the run at jack-in.
 *
 * Balance impact is zero *today*: the menu can only equip the tier-0 defaults,
 * whose stats (`programPower`, `apBonus`) no combat path reads. That is a
 * property of the catalog, not of this module, so the tests below pin the
 * round-trip rather than a number.
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { DEFAULT_REGISTRY } from "../src/core/state/equipment";
import {
  hydrateLoadout,
  isEmptyLoadout,
  readEquippedIds,
  writeEquippedIds,
} from "../src/core/state/equipment_store";
import { makeLoadout, equipOn } from "../src/core/state/loadout";
import { buildHudLines, growthLine, makeInitialState } from "../src/core/state/state";
import { loadProgramsCatalog } from "../src/core/data_loaders";
import { startingDeck } from "../src/core/state/starting_deck";
import type { GameState, Ice, Mission } from "../src/core/types";
import programsJson from "../src/data/programs.json" with { type: "json" };

const programs = loadProgramsCatalog(programsJson);

/** A combat state with the jockey's opening deck and one ICE. */
function combatState(): GameState {
  const mission = {
    id: "adr0322",
    title: "ADR 0322",
    fixer: "test",
    arc: 1,
    zone: "surface",
    grade_min: 1,
    grade_max: 1,
    rewards: { credits: 0, materials: {} },
  } as unknown as Mission;
  const foe = {
    id: "watchdog",
    name: "Watchdog",
    hp: 50,
    maxHp: 50,
    armor: 0,
    tier: 1,
    personality: "aggressive",
    aggression: "passive",
  } as unknown as Ice;
  return {
    ...makeInitialState(mission, foe, startingDeck(programs, "novice")),
    phase: "combat",
    runPhase: "combat",
    iceRoster: [foe],
    activeIceIndex: 0,
  } as GameState;
}

const STORAGE_KEY = "wetrun_equipment";

/** A minimal in-memory localStorage for the tests. */
function installStorage(): Map<string, string> {
  const store = new Map<string, string>();
  (globalThis as { localStorage?: unknown }).localStorage = {
    getItem: (k: string) => store.get(k) ?? null,
    setItem: (k: string, v: string) => void store.set(k, v),
    removeItem: (k: string) => void store.delete(k),
    clear: () => store.clear(),
  };
  return store;
}

let store: Map<string, string>;
beforeEach(() => {
  store = installStorage();
});
afterEach(() => {
  delete (globalThis as { localStorage?: unknown }).localStorage;
});

describe("ADR-0322 · the loadout round-trips", () => {
  it("starts empty and reports it", () => {
    const loadout = hydrateLoadout(DEFAULT_REGISTRY, readEquippedIds());
    expect(isEmptyLoadout(loadout)).toBe(true);
  });

  it("survives a write and a read", () => {
    const deck = DEFAULT_REGISTRY.all.find((e) => e.slot === "deck");
    expect(deck).toBeDefined();
    const equipped = equipOn(makeLoadout(), deck!).loadout;
    expect(isEmptyLoadout(equipped)).toBe(false);

    writeEquippedIds(equipped);
    const restored = hydrateLoadout(DEFAULT_REGISTRY, readEquippedIds());
    expect(restored.get("deck")?.id).toBe(deck!.id);
    expect(isEmptyLoadout(restored)).toBe(false);
  });

  it("keeps a slot empty rather than inventing gear", () => {
    writeEquippedIds(makeLoadout());
    expect(store.get(STORAGE_KEY)).toBe("{}");
    expect(isEmptyLoadout(hydrateLoadout(DEFAULT_REGISTRY, readEquippedIds()))).toBe(
      true,
    );
  });
});

describe("ADR-0322 · a malformed store degrades to empty", () => {
  it("ignores a value that is not JSON", () => {
    store.set(STORAGE_KEY, "{not json");
    expect(readEquippedIds()).toEqual({});
  });

  it("ignores a value that is not an object", () => {
    store.set(STORAGE_KEY, '"deck_basic"');
    expect(readEquippedIds()).toEqual({});
    store.set(STORAGE_KEY, "null");
    expect(readEquippedIds()).toEqual({});
  });

  it("drops ids the registry no longer has", () => {
    store.set(
      STORAGE_KEY,
      JSON.stringify({ deck: "deck_deleted_in_2031", headware: "head_basic" }),
    );
    const loadout = hydrateLoadout(DEFAULT_REGISTRY, readEquippedIds());
    expect(loadout.get("deck")).toBeNull();
    expect(loadout.get("headware")?.id).toBe("head_basic");
  });

  it("drops a slot/id pair that disagrees about the slot", () => {
    // `deck_basic` is a deck; asking for it in `headware` must not equip it.
    store.set(STORAGE_KEY, JSON.stringify({ headware: "deck_basic" }));
    const loadout = hydrateLoadout(DEFAULT_REGISTRY, readEquippedIds());
    expect(loadout.get("headware")).toBeNull();
  });

  it("does nothing when storage is unavailable", () => {
    delete (globalThis as { localStorage?: unknown }).localStorage;
    expect(readEquippedIds()).toEqual({});
    expect(() => writeEquippedIds(makeLoadout())).not.toThrow();
  });
});

describe("ADR-0322 · the growth is readable in one line", () => {
  it("names the deck, its average tier, and hides uniques when there are none", () => {
    const state = combatState();
    const line = growthLine(state);
    expect(line).toContain("Deck 5");
    expect(line).toMatch(/T\d\.\d/);
    expect(line).not.toContain("UNQ");
  });

  it("counts a unique once it is owned, wherever it sits in the piles", () => {
    const state = combatState();
    const withUnique = {
      ...state,
      deck: [...state.deck, programs.ghost_key],
    } as GameState;
    expect(growthLine(withUnique)).toContain("Deck 6");
    expect(growthLine(withUnique)).toContain("UNQ 1");
  });

  it("reaches the HUD", () => {
    expect(buildHudLines(combatState()).some((l) => l.startsWith("Deck "))).toBe(
      true,
    );
  });
});
