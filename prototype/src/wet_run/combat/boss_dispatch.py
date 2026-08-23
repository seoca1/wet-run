"""F.4 dispatch integration helper (ADR-0190 — Phase 12 Axis 4).

Routes boss ids through their profile registries BEFORE falling through
to the standard IceRegistry path in ``combat.registry.build_ice_enemy``.

Two sources of boss definitions, each with its own data shape:

1. ``zone_bosses.json`` (11 entries — 6 per-zone + 3 ascended + 2 peripheral
   endgame bosses), accessed via :class:`ZoneBossRegistry` (see
   :mod:`wet_run.combat.boss_registry`). Profiles are flat dicts; we build
   the dispatch Combatant inline.

2. ``boss_expansion.py`` (3 entries — Neuromancer, Loa Baron, Black
   Baron), accessed via :data:`BOSS_EXPANSION_REGISTRY`. Profiles carry
   phase info and use the existing :func:`build_boss_combatant`.

Lookup order (zone-bosses first, then boss_expansion) is stable and is
covered by ``tests/unit/test_boss_dispatch.py``.

This module is the F.4 wiring point. ``combat.registry.build_ice_enemy``
guards on :func:`build_boss_combatant_from_id`; if the id resolves to a
boss profile the resulting :class:`Combatant` is returned directly,
otherwise the existing IceRegistry path executes unchanged.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .boss_expansion import (
    BOSS_EXPANSION_REGISTRY,
)
from .boss_expansion import (
    build_boss_combatant as _build_expansion_boss_combatant,
)
from .boss_registry import ZoneBossProfile, ZoneBossRegistry, load_zone_boss_registry
from .palette import MAGENTA_BRIGHT
from .state import Combatant

if TYPE_CHECKING:
    pass

__all__ = [
    "build_boss_combatant_from_id",
    "is_boss_id",
]


# Module-level lazy cache: zone_bosses.json is loaded on first use and
# reused thereafter. Reload only happens if the test suite reuses this
# module after a forced reset.
_zone_boss_registry = None


def _get_zone_registry() -> ZoneBossRegistry:
    """Return the lazily-loaded zone-boss registry (cached)."""
    global _zone_boss_registry
    if _zone_boss_registry is None:
        _zone_boss_registry = load_zone_boss_registry()
    return _zone_boss_registry


def reset_zone_registry_cache() -> None:
    """Drop the cached registry. Test helper only — production code
    should rely on the per-process cache."""
    global _zone_boss_registry
    _zone_boss_registry = None


def is_boss_id(ice_id: str) -> bool:
    """Return True if ``ice_id`` resolves in either boss registry.

    Used by ``build_ice_enemy`` to fast-path boss dispatch before the
    standard IceRegistry lookup. False negatives mean a boss id reaches
    the standard code path (which currently has its own boss handling via
    ``is_boss(ice_type)`` and ``get_boss_profile`` for WINTERMUTE / TA —
    not used by these 11+3 bosses).
    """
    if not isinstance(ice_id, str) or not ice_id:
        return False
    if _get_zone_registry().get(ice_id) is not None:
        return True
    return ice_id in BOSS_EXPANSION_REGISTRY


def build_boss_combatant_from_id(
    ice_id: str, *, player_grade: int | None = None
) -> Combatant | None:
    """Build a Combatant for a known boss id, or return ``None``.

    Lookup order:
        1. ``zone_bosses.json`` (via :class:`ZoneBossRegistry`)
        2. ``boss_expansion.py`` (via :func:`build_boss_combatant`)

    Scaling mirrors ``registry.get_scaled_ice_stats`` for zone-boss entries
    (linear ``hp_per_grade`` / ``dmg_per_grade``) and the existing
    ``1.0 + (player_grade - 1) * 0.15`` factor for boss_expansion entries.
    """
    if not isinstance(ice_id, str) or not ice_id:
        return None

    zone = _get_zone_registry().get(ice_id)
    if zone is not None:
        return _zone_boss_to_combatant(zone, player_grade=player_grade)

    boss = BOSS_EXPANSION_REGISTRY.get(ice_id)
    if boss is not None:
        return _build_expansion_boss_combatant(boss, player_grade=player_grade)

    return None


def _zone_boss_to_combatant(profile: ZoneBossProfile, *, player_grade: int | None) -> Combatant:
    """Convert a :class:`ZoneBossProfile` into a dispatch :class:`Combatant`.

    Scaling formula — same linear branch as
    ``registry.get_scaled_ice_stats`` (linear ``hp_per_grade`` /
    ``dmg_per_grade`` above the boss's declared difficulty tier) but
    without the downscaling branch (zone bosses stay at base stats
    when player is below their tier, which matches roguelike boss
    encounter norms):

        hp  = hp_base + hp_per_grade * max(0, player_grade - tier)
        dmg = dmg_base + dmg_per_grade * max(0, player_grade - tier)

    When ``player_grade`` is ``None`` we use the base values unchanged.
    """
    if player_grade is not None:
        diff = max(0, int(player_grade) - profile.tier)
        hp = int(profile.hp_base + profile.hp_per_grade * diff)
        dmg = int(profile.dmg_base + profile.dmg_per_grade * diff)
    else:
        hp = profile.hp_base
        dmg = profile.dmg_base

    return Combatant(
        id=profile.boss_id,
        name=profile.name,
        portrait="▲BOSS▲",
        color=MAGENTA_BRIGHT,
        hp=hp,
        max_hp=hp,
        ap=0,
        max_ap=0,
        auto_attack_damage=dmg,
        skills=(),  # Skills resolved post-creation via combat_view_state hook
        team="enemy",
        ice_kind="boss",
        ice_resistance=profile.resistance,
        base_attack=dmg,
        base_defense=profile.defense,
    )
