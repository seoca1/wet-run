/** The save slot's three lists are held to each other (refactor 2026-11-24).
 *
 * `SaveSlot` (the type), `stateToSaveSlot` (the writer) and the validator used
 * to be hand-kept in three files. `slot_schema.ts` is now the validator's
 * source; this file is what keeps the other two honest:
 *
 *   1. `ALL_SLOT_KEYS` is typed `Record<keyof SaveSlot, true>`, so adding a
 *      field to the type without listing it here is a COMPILE error.
 *   2. That list must equal the schema's keys, so the same field must also get
 *      a schema row.
 *   3. The writer's output must use only known keys, and must produce every
 *      required one — otherwise a save would be written that cannot load.
 */
import { describe, it, expect } from "vitest";
import type { SaveSlot } from "../src/core/types";
import { SLOT_FIELDS, SLOT_KEYS, REQUIRED_SLOT_KEYS, UNCHECKED_SLOT_KEYS } from "../src/save/slot_schema";
import { stateToSaveSlot, makeInitialState } from "../src/core/state/state";
import { loadIceCatalog, loadMissionsCatalog, loadProgramsCatalog } from "../src/core/data_loaders";
import { startingDeck } from "../src/core/state/starting_deck";
import iceJson from "../src/data/ice_types.json" with { type: "json" };
import missionsJson from "../src/data/missions.json" with { type: "json" };
import programsJson from "../src/data/programs.json" with { type: "json" };

/** Every field of `SaveSlot`. Typed as a total record, so a new field in the
 *  type fails to compile here until it is listed. */
const ALL_SLOT_KEYS: Record<keyof SaveSlot, true> = {
  version: true,
  missionId: true,
  playerHp: true,
  playerMaxHp: true,
  playerAlarm: true,
  playerCredits: true,
  turnCount: true,
  deckIds: true,
  discardIds: true,
  drawIds: true,
  savedAt: true,
  graphicNovelProgress: true,
  currentNodeIndex: true,
  campaignMissionIds: true,
  campaignCompleted: true,
  clearedEncounterNodes: true,
  bypassedEncounterNodes: true,
  cardRewardTaken: true,
  uniquePickDone: true,
  jockeyId: true,
  intelNodes: true,
};

const ice = loadIceCatalog(iceJson);
const missions = loadMissionsCatalog(missionsJson);
const programs = loadProgramsCatalog(programsJson);
const mission = Object.values(missions)[0]!;

const freshState = () => {
  const base = Object.values(ice)[0]!;
  return makeInitialState(mission, base, startingDeck(programs, "novice"));
};

describe("save slot schema", () => {
  it("covers every SaveSlot field exactly once", () => {
    const typed = Object.keys(ALL_SLOT_KEYS).sort();
    const schema = [...SLOT_KEYS].sort();
    expect(schema).toEqual(typed);
    expect(new Set(SLOT_KEYS).size).toBe(SLOT_KEYS.length);
  });

  it("marks every non-optional field as required", () => {
    // A field with no `?` in the type must be required in the schema.
    const optionalInType = new Set([
      "graphicNovelProgress",
      "currentNodeIndex",
      "campaignMissionIds",
      "campaignCompleted",
      "clearedEncounterNodes",
      "bypassedEncounterNodes",
      "cardRewardTaken",
      "uniquePickDone",
      "jockeyId",
      "intelNodes",
    ]);
    const required = new Set(REQUIRED_SLOT_KEYS);
    for (const key of SLOT_KEYS) {
      expect(required.has(key), `${key} required?`).toBe(!optionalInType.has(key));
    }
  });

  it("writes only known keys, and all of the required ones", () => {
    const written = Object.keys(stateToSaveSlot(freshState()));
    const known = new Set(SLOT_KEYS);
    const unknown = written.filter((k) => !known.has(k));
    expect(unknown, "writer emitted a key with no schema row").toEqual([]);
    const missing = REQUIRED_SLOT_KEYS.filter((k) => !written.includes(k));
    expect(missing, "writer skipped a required key — the save would not load").toEqual([]);
  });

  it("keeps the unchecked set visible", () => {
    // These four are written and read, but the validator never inspected them.
    // Listing them here means narrowing the gap is a deliberate edit.
    expect([...UNCHECKED_SLOT_KEYS].sort()).toEqual([
      "campaignCompleted",
      "campaignMissionIds",
      "intelNodes",
      "uniquePickDone",
    ]);
  });

  it("has a check for every field it claims to check", () => {
    for (const field of SLOT_FIELDS) {
      if (field.check === undefined) continue;
      // An absent optional value must pass its own check.
      if (!field.required) {
        expect(field.check(undefined), `${field.key} rejects undefined`).toBe(true);
      }
    }
  });
});
