/** Apply the equipment's survival axis to a fresh run (ADR-0326).
 *
 * Of the equipment stats, `defense` and `iceResistance` are read live on the
 * incoming-damage path (`player_mitigation.ts`) and need no state change. The
 * other two survival stats are run-start facts:
 *
 * - `hpBonus` raises the run's maxHP and fills it — the same shape `applyPrep`
 *   uses for its HP option.
 * - `shieldBonus` adds a player shield pool — the same mechanism `applyPrep`
 *   uses for its "ice" option (a `shield` status effect, spent by absorption).
 *
 * This runs at jack-in, next to `applyPrep`, so the per-encounter balance
 * harness (which builds runs with `EMPTY_LOADOUT`) keeps measuring the same
 * fight it always did. An empty loadout is a no-op.
 */
import type { GameState } from "../types";
import type { EquipmentLoadout } from "./loadout";

/** The shield effect's lifetime. Prep gives it 9999 so it is spent by
 *  absorbing damage, not by running out of enemy ticks — gear matches. */
const GEAR_SHIELD_LIFETIME = 9999;

export function applyEquipmentSurvival(
  state: GameState,
  loadout: EquipmentLoadout,
): GameState {
  const stats = loadout.totalStats();
  let next = state;

  if (stats.hpBonus > 0) {
    const maxHp = next.player.maxHp + stats.hpBonus;
    next = {
      ...next,
      player: {
        ...next.player,
        maxHp,
        hp: next.player.hp + stats.hpBonus,
      },
    };
  }

  if (stats.shieldBonus > 0) {
    next = {
      ...next,
      statusEffects: [
        ...next.statusEffects,
        {
          kind: "shield",
          target: "player",
          magnitude: stats.shieldBonus,
          remaining: GEAR_SHIELD_LIFETIME,
        },
      ],
    };
  }

  return next;
}
