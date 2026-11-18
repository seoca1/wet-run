/** Material market — credits buy materials, during the run (ADR-0331).
 *
 * Credits had no sink: a run's bounty (`state.player.credits`) is read by the
 * ending resolver and nothing else, so the only thing money could do was
 * qualify an ending. Meanwhile materials are the growth currency and only drop.
 * This closes the loop — a run can convert its bounty into the material it is
 * short of.
 *
 * It lives at the LOOT STOP, not the menu: ADR-0323 deliberately does not merge
 * credits into the menu wallet, so a menu-screen market would always be broke.
 * The run's credits are where the money actually is.
 *
 * Prices are in the measured income scale (a g3 run banks ~3,300cr), and are
 * placeholders — measured, not chosen for feel.
 */
import { clampGrade } from "../combat/ice_scaling";

export interface MaterialOffer {
  readonly materialId: string;
  readonly name: string;
  readonly quantity: number;
  readonly price: number;
  /** Grades at which this offer is on the bench. */
  readonly grades: ReadonlyArray<number>;
}

export const MATERIAL_OFFERS: ReadonlyArray<MaterialOffer> = Object.freeze([
  Object.freeze({
    materialId: "data_fragment",
    name: "Loose Data",
    quantity: 10,
    price: 300,
    grades: Object.freeze([1, 2]),
  }),
  Object.freeze({
    materialId: "ice_shard",
    name: "ICE Shard",
    quantity: 10,
    price: 300,
    grades: Object.freeze([3, 4]),
  }),
  Object.freeze({
    materialId: "combat_module",
    name: "Combat Module",
    quantity: 2,
    price: 700,
    grades: Object.freeze([5, 6]),
  }),
]);

/** The offer on the bench at this grade, or null. */
export function materialOfferForGrade(grade: number): MaterialOffer | null {
  const g = clampGrade(grade);
  return MATERIAL_OFFERS.find((o) => o.grades.includes(g)) ?? null;
}
