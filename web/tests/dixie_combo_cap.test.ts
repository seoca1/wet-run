/** ADR-0268 — the ally must not outgrow the player.
 *
 * Measured in a real run: Dixie's line read 11 → 35 → 68 → 92 dmg while the
 * player's cards read 4-17. `playerCombo` is only set to 0 at run start
 * (`openArrivalEncounter` keeps it), so the raw counter grew for the whole
 * run -- and `COMBO_BONUSES` itself ends at 6, where a card's multiplier
 * already falls back to 1.0.
 */
import { describe, expect, it } from "vitest";
import {
  DIXIE_BASE_DAMAGE,
  DIXIE_SYNERGY_BONUS,
  MAX_COMBO,
  dixieDamage,
} from "../src/core/combat/state_actions_combat";

describe("ADR-0268 — Dixie's synergy is bounded by the combo ceiling", () => {
  it("uses the ceiling the damage table defines", () => {
    expect(MAX_COMBO).toBe(6);
  });

  it("is the base at combo 0 and grows by the synergy per combo step", () => {
    expect(dixieDamage(0)).toBe(DIXIE_BASE_DAMAGE);
    expect(dixieDamage(1)).toBe(DIXIE_BASE_DAMAGE + DIXIE_SYNERGY_BONUS);
    expect(dixieDamage(MAX_COMBO)).toBe(
      DIXIE_BASE_DAMAGE + MAX_COMBO * DIXIE_SYNERGY_BONUS,
    );
  });

  it("stops growing past the ceiling — the run-long counter cannot become a cannon", () => {
    const atCeiling = dixieDamage(MAX_COMBO);
    for (const combo of [7, 12, 28, 60]) {
      expect(dixieDamage(combo)).toBe(atCeiling);
    }
    // The measured runaway was 92 at combo 28; capped, it is 26.
    expect(dixieDamage(28)).toBe(26);
  });
});
