"""Wetware augments stacking logic (ADR-0193, Phase 14 integration).

Defines how multiple wetware augments stack when equipped.
Supports 10 augments from wetware.json (7 tier-3 existing + 3 new stats).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).parent.parent.parent.parent / "data" / "equipment" / "wetware.json"


@dataclass(frozen=True, slots=True)
class StackedWetware:
    """Result of stacking multiple wetware augments."""

    ap_regen: float = 0.0
    crit_chance: float = 0.0
    crit_damage: float = 0.0
    dodge: float = 0.0
    hp_bonus: int = 0
    healing: float = 0.0
    shield: float = 0.0
    speed: float = 0.0
    mana: int = 0
    armor: float = 0.0
    focus: float = 0.0
    augment_count: int = 0


def _load_augments() -> dict[str, Any]:
    """Load wetware augments from wetware.json."""
    with open(DATA_PATH) as f:
        return {k: v for k, v in json.load(f).items() if not k.startswith("_")}


_AUGMENTS_CACHE: dict[str, dict[str, Any]] | None = None


def _get_augments() -> dict[str, dict[str, Any]]:
    """Lazy-loaded augments cache."""
    global _AUGMENTS_CACHE
    if _AUGMENTS_CACHE is None:
        _AUGMENTS_CACHE = _load_augments()
    return _AUGMENTS_CACHE


def get_augment(augment_id: str) -> dict[str, Any] | None:
    """Return an augment definition by id."""
    return _get_augments().get(augment_id)


def get_all_augments() -> list[dict[str, Any]]:
    """Return all augments."""
    return list(_get_augments().values())


def get_augments_by_type(augment_type: str) -> list[dict[str, Any]]:
    """Return augments of a specific type."""
    return [a for a in _get_augments().values() if a.get("type") == augment_type]


def count_tier3_augments(augment_ids: list[str]) -> int:
    """Count how many tier-3 augments are in the list."""
    return sum(1 for aid in augment_ids if _is_tier3(aid))


def _is_tier3(augment_id: str) -> bool:
    aug = get_augment(augment_id)
    if aug is None:
        return False
    return aug.get("tier") == 3


def stack_wetware(augment_ids: list[str]) -> StackedWetware:
    """Stack multiple wetware augments using their bonuses.

    Stacking rules (Phase 14/ADR-0193):
    - ap_regen: additive (lv1 + lv2 + lv3)
    - crit_chance: additive
    - crit_damage: additive
    - dodge: additive (capped at 0.95)
    - hp_bonus: additive (int)
    - healing: additive (capped at 1.0)
    - shield: additive (capped at 0.95)
    - speed: additive (capped at 1.0)
    - mana: additive (int)
    - armor: additive (capped at 1.0)
    - focus: additive (capped at 1.0)

    Args:
        augment_ids: List of augment ids to stack.

    Returns:
        StackedWetware with combined bonuses.
    """
    stacked = StackedWetware(augment_count=len(augment_ids))

    for aid in augment_ids:
        aug = get_augment(aid)
        if aug is None:
            continue

        stacked = StackedWetware(
            ap_regen=_cap(stacked.ap_regen + _aug_bonus(aug, "ap_regen_bonus"), 1.0),
            crit_chance=_cap(stacked.crit_chance + _aug_bonus(aug, "crit_chance_bonus"), 0.95),
            crit_damage=_cap(stacked.crit_damage + _aug_bonus(aug, "crit_damage_bonus"), 1.0),
            dodge=_cap(stacked.dodge + _aug_bonus(aug, "dodge_bonus"), 0.95),
            hp_bonus=stacked.hp_bonus + int(_aug_bonus(aug, "hp_bonus")),
            healing=_cap(stacked.healing + _aug_bonus(aug, "heal_bonus"), 1.0),
            shield=_cap(stacked.shield + _aug_bonus(aug, "shield_bonus"), 0.95),
            speed=_cap(stacked.speed + _aug_bonus(aug, "speed_bonus"), 1.0),
            mana=stacked.mana + int(_aug_bonus(aug, "mana_bonus")),
            armor=_cap(stacked.armor + _aug_bonus(aug, "armor_bonus"), 1.0),
            focus=_cap(stacked.focus + _aug_bonus(aug, "focus_bonus"), 1.0),
            augment_count=stacked.augment_count,
        )

    return stacked


def _aug_bonus(augment: dict[str, Any], key: str) -> float:
    """Extract a bonus value from an augment, defaulting to 0.0."""
    val = augment.get(key, 0.0)
    return float(val) if val is not None else 0.0


def _cap(value: float, cap_value: float) -> float:
    """Cap a value at its maximum."""
    return min(value, cap_value)


def get_augment_count() -> int:
    """Return total number of augments."""
    return len(_get_augments())


def get_new_stat_augments() -> list[dict[str, Any]]:
    """Return augments that introduce new stats (mana, armor, focus)."""
    return [a for a in _get_augments().values() if a.get("is_new_stat") is True]


def get_max_ap_regen() -> float:
    """Return max ap_regen if all 3 ap_regen augments are stacked."""
    return 0.5


def validate_stacking(augment_ids: list[str]) -> bool:
    """Validate that all augment ids exist in the registry."""
    return all(aid in _get_augments() for aid in augment_ids)
