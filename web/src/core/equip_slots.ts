/** Equipment slot definitions — shared to break circular import between equipment.ts and equipment_catalog.ts. */

export type EquipSlot =
  | "deck"
  | "headware"
  | "eyeware"
  | "bodysuit"
  | "gloves"
  | "boots"
  | "implant"
  | "trodes";

/** Ordered slot list. Mirrors Python `EquipSlot` enum iteration order. */
export const EQUIP_SLOTS: ReadonlyArray<EquipSlot> = Object.freeze([
  "deck",
  "headware",
  "eyeware",
  "bodysuit",
  "gloves",
  "boots",
  "implant",
  "trodes",
] as const);
