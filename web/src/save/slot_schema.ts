/** The on-disk save slot schema — one row per field (refactor 2026-11-24).
 *
 * The slot had three hand-kept lists: the `SaveSlot` type in `core/types.ts`,
 * the writer in `core/state/state.ts`, and the runtime validator in
 * `save/storage.ts`. Adding a field meant editing them in step, and a forgotten
 * row fails silently in both directions — a field the writer emits but nobody
 * validates, or a rule the validator demands but no writer produces.
 *
 * The rows below are the single source for the VALIDATOR. The type stays where
 * it is (it is the compile-time shape), and the writer stays explicit in
 * `state.ts` because it maps state → slot rather than copying keys. What ties
 * them together is `tests/save_slot_schema.test.ts`: it holds the writer's
 * output to these keys and holds this table to `keyof SaveSlot`.
 *
 * `check` is `undefined` for the fields the old validator never inspected. That
 * is a pre-existing gap, kept as data here rather than silently tightened — the
 * tests assert the unchecked set, so narrowing it is a visible decision.
 */
import type { SaveSlot } from "../core/types";

export interface SlotFieldSpec {
  readonly key: keyof SaveSlot & string;
  /** Required fields must be present; the writer always emits them. */
  readonly required: boolean;
  /** `undefined` = not inspected (pre-existing gap). Otherwise: present values
   *  must pass; `undefined` must pass too, since the field is optional. */
  readonly check?: (value: unknown) => boolean;
}

const isString = (v: unknown): boolean => typeof v === "string";
const isNumber = (v: unknown): boolean => typeof v === "number";
const isFiniteNumber = (v: unknown): boolean => typeof v === "number" && Number.isFinite(v);
const isStringArray = (v: unknown): boolean =>
  Array.isArray(v) && v.every((e) => typeof e === "string");
/** Optional: absent, or a list of non-negative integer node indices. */
const isOptionalNodeList = (v: unknown): boolean =>
  v === undefined ||
  (Array.isArray(v) &&
    v.every((i: unknown) => typeof i === "number" && Number.isInteger(i) && i >= 0));
/** Optional: absent, or a non-empty string (ADR-0261). */
const isOptionalId = (v: unknown): boolean =>
  v === undefined || (typeof v === "string" && v.length > 0);
/** Optional and nullable; a malformed value would crash `slotToGameState` on
 *  `chainId.split("_")`. */
const isGraphicNovelProgress = (v: unknown): boolean => {
  if (v === undefined || v === null) return true;
  if (typeof v !== "object" || Array.isArray(v)) return false;
  const g = v as Record<string, unknown>;
  return isString(g.chainId) && isNumber(g.sceneIndex) && isNumber(g.dialogueIndex);
};

export const SLOT_FIELDS: ReadonlyArray<SlotFieldSpec> = Object.freeze([
  { key: "version", required: true, check: isNumber },
  { key: "missionId", required: true, check: isString },
  { key: "playerHp", required: true, check: isNumber },
  { key: "playerMaxHp", required: true, check: isNumber },
  { key: "playerAlarm", required: true, check: isNumber },
  { key: "playerCredits", required: true, check: isNumber },
  { key: "turnCount", required: true, check: isNumber },
  { key: "deckIds", required: true, check: isStringArray },
  { key: "discardIds", required: true, check: isStringArray },
  { key: "drawIds", required: true, check: isStringArray },
  { key: "savedAt", required: true, check: isString },
  { key: "graphicNovelProgress", required: false, check: isGraphicNovelProgress },
  { key: "currentNodeIndex", required: false, check: (v) => v === undefined || isFiniteNumber(v) },
  // The four below are written by `stateToSaveSlot` and read by
  // `slotToGameState`, but the old validator never looked at them.
  { key: "campaignMissionIds", required: false },
  { key: "campaignCompleted", required: false },
  { key: "uniquePickDone", required: false },
  { key: "intelNodes", required: false },
  { key: "clearedEncounterNodes", required: false, check: isOptionalNodeList },
  { key: "bypassedEncounterNodes", required: false, check: isOptionalNodeList },
  { key: "cardRewardTaken", required: false, check: isOptionalId },
  { key: "jockeyId", required: false, check: isOptionalId },
]);

/** Keys the writer is allowed to emit. */
export const SLOT_KEYS: ReadonlyArray<string> = SLOT_FIELDS.map((f) => f.key);

/** Fields the validator requires to be present. */
export const REQUIRED_SLOT_KEYS: ReadonlyArray<string> = SLOT_FIELDS.filter(
  (f) => f.required,
).map((f) => f.key);

/** Fields the validator does not inspect (pre-existing gap, kept visible). */
export const UNCHECKED_SLOT_KEYS: ReadonlyArray<string> = SLOT_FIELDS.filter(
  (f) => f.check === undefined,
).map((f) => f.key);

/** Runtime shape check for a parsed save slot. Same rules as the validator it
 *  replaced in `save/storage.ts` — driven by `SLOT_FIELDS` now. */
export function validateSlot(value: unknown): value is SaveSlot {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  for (const field of SLOT_FIELDS) {
    const raw = v[field.key];
    if (field.required && raw === undefined) return false;
    if (field.check !== undefined && !field.check(raw)) return false;
  }
  return true;
}