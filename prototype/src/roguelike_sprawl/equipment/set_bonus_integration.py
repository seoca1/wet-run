"""Set Bonus Integration (Round 5).

Wires equipment/equipment.py SET_BONUSES into combat state calculations.
Provides:
- SetBonusCalculator: aggregates active set bonuses
- apply_set_bonuses_to_stats: combines equipment + set bonuses
- Game loadout integration helpers
"""

from __future__ import annotations

from dataclasses import dataclass

from .equipment import (
    SET_BONUSES,
    EquipmentLoadout,
    EquipStats,
    get_set_bonus,
)


@dataclass(frozen=True, slots=True)
class SetBonusSummary:
    """Summary of active set bonuses on a loadout."""

    active_set_ids: tuple[str, ...]
    set_count: dict[str, int]
    total_bonus: EquipStats

    def has_any_bonus(self) -> bool:
        """Return True if any set bonus is active."""
        return bool(self.active_set_ids)


def calculate_set_bonus(loadout: EquipmentLoadout) -> SetBonusSummary:
    """Calculate all active set bonuses for a loadout."""
    counts = loadout.set_counts()
    active_ids = tuple(counts.keys())
    total_bonus = EquipStats()
    for set_id in active_ids:
        bonus = get_set_bonus(set_id, counts[set_id])
        if bonus is not None:
            total_bonus = _add_stats(total_bonus, bonus)
    return SetBonusSummary(
        active_set_ids=active_ids,
        set_count=counts,
        total_bonus=total_bonus,
    )


def get_active_set_ids(loadout: EquipmentLoadout) -> tuple[str, ...]:
    """Return the set IDs of items equipped in the loadout."""
    return tuple(loadout.set_counts().keys())


def get_set_count(loadout: EquipmentLoadout, set_id: str) -> int:
    """Return the number of equipped items with the given set_id."""
    return loadout.set_counts().get(set_id, 0)


def get_best_set_bonus_for(loadout: EquipmentLoadout, set_id: str) -> EquipStats | None:
    """Return the best available set bonus for the given set_id."""
    count = get_set_count(loadout, set_id)
    if count == 0:
        return None
    return get_set_bonus(set_id, count)


def get_all_set_bonuses(loadout: EquipmentLoadout) -> list[EquipStats]:
    """Return all active set bonuses as a list."""
    counts = loadout.set_counts()
    bonuses: list[EquipStats] = []
    for set_id, count in counts.items():
        bonus = get_set_bonus(set_id, count)
        if bonus is not None:
            bonuses.append(bonus)
    return bonuses


def apply_set_bonuses_to_stats(
    base_stats: EquipStats,
    loadout: EquipmentLoadout,
) -> EquipStats:
    """Apply all active set bonuses to base stats."""
    bonuses = get_all_set_bonuses(loadout)
    result = base_stats
    for bonus in bonuses:
        result = _add_stats(result, bonus)
    return result


def get_set_bonus_definitions() -> dict[str, dict[int, EquipStats]]:
    """Return the SET_BONUSES dictionary (read-only)."""
    return SET_BONUSES


def _add_stats(a: EquipStats, b: EquipStats) -> EquipStats:
    """Add two EquipStats."""
    return EquipStats(
        attack_bonus=a.attack_bonus + b.attack_bonus,
        crit_bonus_pct=a.crit_bonus_pct + b.crit_bonus_pct,
        damage_bonus_pct=a.damage_bonus_pct + b.damage_bonus_pct,
        defense=a.defense + b.defense,
        hp_bonus=a.hp_bonus + b.hp_bonus,
        shield_bonus=a.shield_bonus + b.shield_bonus,
        ap_bonus=a.ap_bonus + b.ap_bonus,
        ap_regen_bonus_pct=a.ap_regen_bonus_pct + b.ap_regen_bonus_pct,
        program_power=a.program_power + b.program_power,
        ice_resistance=a.ice_resistance + b.ice_resistance,
        grants_skill_id=a.grants_skill_id or b.grants_skill_id,
        extra_effect=", ".join(filter(None, [a.extra_effect, b.extra_effect])),
    )


__all__ = [
    "SetBonusSummary",
    "apply_set_bonuses_to_stats",
    "calculate_set_bonus",
    "get_active_set_ids",
    "get_all_set_bonuses",
    "get_best_set_bonus_for",
    "get_set_bonus_definitions",
    "get_set_count",
]
