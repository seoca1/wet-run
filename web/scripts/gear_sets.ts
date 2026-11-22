/** Gear loadouts shared by the probes (ADR-0336, ADR-0341).
 *
 * `balance` and `survival` measure the BARE runner (EMPTY_LOADOUT) on purpose —
 * that is the recorded baseline. `gear` and, since ADR-0341, `campaign` also need
 * to measure a runner who is actually wearing something; the sets live here so
 * both read the same definition instead of drifting apart.
 */
import {
  EMPTY_LOADOUT,
  equipOn,
  makeLoadout,
  type EquipmentLoadout,
} from "../src/core/state/loadout";
import {
  ARASAKA_DECK,
  BOOTS_GHOST,
  CHROME_GLOVES,
  CORPORATE_DECK,
  MASTER_BODY,
  MILITECH_EYES,
  STREET_DECK,
  SUBDERMAL,
  TACTICAL_BODY,
  TRODES_NINJA,
  ZION_TRODES,
  type Equipment,
} from "../src/core/state/equipment";

const gear = (...items: Equipment[]): EquipmentLoadout =>
  items.reduce((l, e) => equipOn(l, e).loadout, makeLoadout());

export interface GearSet {
  readonly name: string;
  readonly loadout: EquipmentLoadout;
}

/** The five rungs measured by `npm run gear` (ADR-0326/0328). */
export const GEAR_SETS: ReadonlyArray<GearSet> = [
  { name: "bare (recorded baseline)", loadout: EMPTY_LOADOUT },
  { name: "T1 street+eyes+gloves", loadout: gear(STREET_DECK, MILITECH_EYES, CHROME_GLOVES) },
  {
    name: "T2 corp+subdermal+ninja+boots",
    loadout: gear(CORPORATE_DECK, SUBDERMAL, TRODES_NINJA, BOOTS_GHOST),
  },
  { name: "T4 arasaka+body", loadout: gear(ARASAKA_DECK, TACTICAL_BODY) },
  { name: "T6 master+zion", loadout: gear(MASTER_BODY, ZION_TRODES) },
];

/** Resolve `--gear T2` (case-insensitive prefix of the set name) to a loadout.
 *  An empty or absent value means bare, so callers keep the recorded baseline. */
export function gearSetByPrefix(prefix: string): GearSet {
  const wanted = prefix.trim().toUpperCase();
  if (wanted === "") return GEAR_SETS[0]!;
  if (wanted === "BARE") return GEAR_SETS[0]!;
  const found = GEAR_SETS.find((set) => set.name.toUpperCase().startsWith(wanted));
  if (found === undefined) {
    throw new Error(
      `unknown gear set ${prefix}; pick one of ${GEAR_SETS.map((s) => s.name.split(" ")[0]).join(", ")}`,
    );
  }
  return found;
}