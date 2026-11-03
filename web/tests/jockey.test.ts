/** ADR-0274 — the run belongs to a jockey, and never forgets which.
 *
 * The prologue is one story per jockey, keyed by the novel player's
 * CharacterId. A run used to belong to nobody, so the story just read left no
 * trace in the run or in its ending. The choice is display-only: it names the
 * runner in the intro and the ending summary and changes no number.
 */
import { describe, expect, it } from "vitest";
import { JOCKEYS, isJockeyId, jockeyHandle } from "../src/core/state/jockey";
import { renderJockeySelect } from "../src/renderer/jockey_select";
import { renderRunIntro } from "../src/renderer/run_intro";
import { renderEndingScreen } from "../src/renderer/ending";
import {
  makeInitialState,
  slotToGameState,
  stateToSaveSlot,
} from "../src/core/state/state";
import {
  loadIceCatalog,
  loadMissionsCatalog,
  loadProgramsCatalog,
} from "../src/core/data_loaders";
import missionsData from "../src/data/missions.json";
import programsData from "../src/data/programs.json";
import iceTypesData from "../src/data/ice_types.json";
import type { GameState, Ice, Mission, Program } from "../src/core/types";

const MISSIONS = loadMissionsCatalog(missionsData);
const PROGRAMS = loadProgramsCatalog(programsData);
const ICE = loadIceCatalog(iceTypesData);
const MISSION = MISSIONS[0] as Mission;
const BASE_ICE = Object.values(ICE)[0] as Ice;
const DECK: Program[] = Object.keys(PROGRAMS)
  .sort()
  .slice(0, 5)
  .map((id) => ({ ...(PROGRAMS[id] as Program), id }));

const text = (grid: { cells: readonly (readonly { char: string }[])[] }) =>
  grid.cells.map((row) => row.map((c) => c.char).join("")).join("\n");

function stateWith(jockeyId: string | null): GameState {
  return { ...makeInitialState(MISSION, BASE_ICE, DECK), jockeyId };
}

describe("ADR-0274 — jockey identity", () => {
  it("has the three prologue jockeys, matching the novel player's ids", () => {
    expect(JOCKEYS.map((j) => j.id)).toEqual(["novice", "veteran", "heretic"]);
    expect(jockeyHandle("novice")).toBe("CASE");
    expect(jockeyHandle("veteran")).toBe("SIL");
    expect(jockeyHandle("heretic")).toBe("KAS");
    expect(jockeyHandle(null)).toBeNull();
    expect(jockeyHandle("nonsense")).toBeNull();
  });

  it("narrows save data to a known id", () => {
    expect(isJockeyId("novice")).toBe(true);
    expect(isJockeyId("kas")).toBe(false);
    expect(isJockeyId(undefined)).toBe(false);
  });

  it("the select screen names all three and states its keys", () => {
    const out = text(renderJockeySelect(0, 80, 50));
    for (const jockey of JOCKEYS) expect(out).toContain(jockey.handle);
    expect(out).toContain("WHO IS JACKING IN");
    expect(out).toContain("ENTER: jack in");
    // Fits the narrowest layout.
    for (const row of text(renderJockeySelect(2, 40, 60)).split("\n")) {
      expect(row.length).toBeLessThanOrEqual(40);
    }
  });

  it("the run intro says who is jacking in", () => {
    expect(text(renderRunIntro(1, 80, 50, "CASE"))).toContain("CASE JACKS IN");
    // Without a jockey the card is unchanged (older runs, CONTINUE).
    expect(text(renderRunIntro(1, 80, 50))).not.toContain("JACKS IN");
  });

  it("the ending summary names whose run it was", () => {
    const out = text(
      renderEndingScreen("arc4_liberation_front", 80, 50, {
        mission: "Aleph Fragment",
        jockey: "CASE",
        hp: 87,
        maxHp: 100,
        credits: 4700,
        turns: 21,
      }),
    );
    expect(out).toContain("CASE — Aleph Fragment");
    const anonymous = text(
      renderEndingScreen("arc4_liberation_front", 80, 50, {
        mission: "Aleph Fragment",
        hp: 87,
        maxHp: 100,
        credits: 4700,
        turns: 21,
      }),
    );
    expect(anonymous).toContain("Aleph Fragment");
    expect(anonymous).not.toContain("CASE —");
  });

  it("survives a save round-trip, and an older slot without it restores null", () => {
    const slot = stateToSaveSlot(stateWith("kas"));
    expect(slot.jockeyId).toBe("kas");
    const restored = slotToGameState(slot, MISSIONS, PROGRAMS, BASE_ICE, ICE);
    expect(restored?.jockeyId).toBe("kas");

    // A slot written before this field existed must not break the load.
    const legacy = { ...slot } as Record<string, unknown>;
    delete legacy.jockeyId;
    const fromLegacy = slotToGameState(
      legacy as never,
      MISSIONS,
      PROGRAMS,
      BASE_ICE,
      ICE,
    );
    expect(fromLegacy?.jockeyId).toBeNull();
  });
});
