"""Zone boss registry (ADR-0190, Phase 12 — Axis 4 zone-bosses part).

Loads :data-file:`prototype/data/combat/zone_bosses.json` (11 entries — 6
per-zone bosses, 3 ascended variants, 2 Peripheral endgame bosses) into a
typed registry. Provides id- and zone-keyed lookup, plus a hook point for
the upcoming F.4 dispatch integration.

Data flows through ``ZoneBossProfile`` (frozen dataclass, slots=True) so
downstream code (combat dispatch, AI, dialogue) can rely on typed access
instead of raw dict reads.

This module is intentionally additive — it does NOT yet wire zone bosses
into ``registry.build_ice_enemy``. That wiring is the next commit
(ADR-0190 ``Option 2`` + F.4 integration).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = [
    "ZoneBossProfile",
    "ZoneBossRegistry",
    "load_zone_boss_registry",
]


@dataclass(frozen=True, slots=True)
class ZoneBossProfile:
    """A single zone boss definition mirrored from ``zone_bosses.json``.

    Attributes:
        boss_id: Top-level JSON key (e.g. ``"dj_cyberspace"``). Acts as the
            stable, callable identifier in combat spawn tables.
        name: Player-visible name (e.g. ``"DJ Cyberspace"``).
        zone: Zone the boss anchors (``"surface"``, ``"mid"``, ``"deep"``,
            ``"core"``, ``"ta"``, ``"freeside"``) or ``None`` for ascended
            variants and endgame content that span all zones.
        tier: Difficulty tier (3-6). Per ADR-0149 boss-phase semantics,
            tier 5+ implies multi-phase combat.
        hp_base: HP at grade 1 (no scaling).
        hp_per_grade: Additive HP per player grade above 1.
        dmg_base: Auto-attack damage at grade 1.
        dmg_per_grade: Additive damage per player grade above 1.
        defense: Flat damage reduction.
        speed: Initiative/speed stat (used by boss AI).
        skills: Tuple of skill ids the boss activates per phase (resolved
            against ``programs.json`` in the dispatch integration commit).
        resistance: 0.0 - 1.0 damage resistance (clamped on use).
        phase_count: Total phase count declared for this boss.
        portrait: ASCII portrait id (e.g. ``"ice.boss"``).
        description: Player-facing lore text (Gibson tone).
        loot_table: Tuple of loot-entry dicts with ``item``, ``chance``,
            ``quantity`` keys.
        ice_kind: ICE kind discriminator. Always ``"boss"`` for these
            entries; reserved for future sub-boss variants.
    """

    boss_id: str
    name: str
    zone: str | None
    tier: int
    hp_base: int
    hp_per_grade: int
    dmg_base: int
    dmg_per_grade: int
    defense: int
    speed: int
    skills: tuple[str, ...]
    resistance: float
    phase_count: int
    portrait: str
    description: str
    loot_table: tuple[dict[str, Any], ...]
    ice_kind: str


def _parse_entry(boss_id: str, raw: dict[str, Any]) -> ZoneBossProfile:
    """Convert one ``zone_bosses.json`` entry dict into a ZoneBossProfile."""
    zone_raw = raw.get("zone")
    return ZoneBossProfile(
        boss_id=boss_id,
        name=str(raw.get("name", boss_id)),
        zone=str(zone_raw) if zone_raw is not None else None,
        tier=int(raw.get("tier", 1)),
        hp_base=int(raw.get("hp_base", 100)),
        hp_per_grade=int(raw.get("hp_per_grade", 0)),
        dmg_base=int(raw.get("dmg_base", 5)),
        dmg_per_grade=int(raw.get("dmg_per_grade", 0)),
        defense=int(raw.get("defense", 0)),
        speed=int(raw.get("speed", 0)),
        skills=tuple(str(s) for s in raw.get("skills", [])),
        resistance=float(raw.get("resistance", 0.0)),
        phase_count=int(raw.get("phase_count", 1)),
        portrait=str(raw.get("portrait", "ice.boss")),
        description=str(raw.get("description", "")),
        loot_table=tuple(dict(item) for item in raw.get("loot_table", [])),
        ice_kind=str(raw.get("ice_kind", "boss")),
    )


class ZoneBossRegistry:
    """In-memory registry of zone-boss definitions from ``zone_bosses.json``.

    Indexes bosses two ways:
        - by id (top-level JSON key) — see :meth:`get`
        - by zone (anchored zone name) — see :meth:`get_for_zone`

    Mutations are intentionally absent: the registry is loaded once at
    process start and treated as immutable.
    """

    def __init__(self, entries: dict[str, ZoneBossProfile]) -> None:
        """Build the registry and a zone→bosses index for fast lookup."""
        self._entries: dict[str, ZoneBossProfile] = dict(entries)
        self._by_zone: dict[str, list[str]] = {}
        for boss_id, profile in self._entries.items():
            if profile.zone is not None:
                self._by_zone.setdefault(profile.zone, []).append(boss_id)

    def get(self, boss_id: str) -> ZoneBossProfile | None:
        """Return the boss profile for ``boss_id`` or ``None`` if missing."""
        return self._entries.get(boss_id)

    def get_for_zone(self, zone: str) -> tuple[ZoneBossProfile, ...]:
        """Return all bosses assigned to ``zone`` (empty tuple if none)."""
        ids = self._by_zone.get(zone, [])
        return tuple(self._entries[i] for i in ids)

    def list_all(self) -> tuple[ZoneBossProfile, ...]:
        """Return every boss in registration order (top-down JSON order)."""
        return tuple(self._entries.values())

    def list_ids(self) -> tuple[str, ...]:
        """Return every boss id in registration order."""
        return tuple(self._entries.keys())

    def list_zones(self) -> tuple[str, ...]:
        """Return all zone names that have at least one boss."""
        return tuple(sorted(self._by_zone.keys()))

    def __len__(self) -> int:
        """Number of registered bosses."""
        return len(self._entries)

    def __contains__(self, boss_id: object) -> bool:
        """Whether ``boss_id`` is registered."""
        return boss_id in self._entries


def _default_data_path() -> Path:
    """Resolve the canonical ``zone_bosses.json`` path.

    Layout: ``<repo>/prototype/data/combat/zone_bosses.json``. Module is
    located at ``<repo>/prototype/src/wet_run/combat/boss_registry.py`` so
    the walk is ``parents[3] / 'data' / 'combat' / 'zone_bosses.json'``:
        parents[0] = combat/, parents[1] = wet_run/, parents[2] = src/,
        parents[3] = prototype/.
    """
    return Path(__file__).resolve().parents[3] / "data" / "combat" / "zone_bosses.json"


def load_zone_boss_registry(path: Path | None = None) -> ZoneBossRegistry:
    """Load ``zone_bosses.json`` from disk and return a populated registry.

    Args:
        path: Optional explicit path. When omitted, falls back to the
            canonical project location. Pass a custom path to use a stub
            fixture or alternate data file in tests.

    Returns:
        A new :class:`ZoneBossRegistry` populated with all valid entries.

    Notes:
        - Top-level keys starting with ``_`` (e.g. ``_metadata``) are
          silently skipped.
        - Non-dict values (corrupt/typo'd entries) are silently skipped
          to keep the loader resilient to partial data corruption.
        - The function performs no I/O outside of the file open.
    """
    resolved = path or _default_data_path()
    with open(resolved) as f:
        data = json.load(f)
    entries: dict[str, ZoneBossProfile] = {}
    for boss_id, raw in data.items():
        if not isinstance(boss_id, str) or boss_id.startswith("_"):
            continue
        if not isinstance(raw, dict):
            continue
        try:
            entries[boss_id] = _parse_entry(boss_id, raw)
        except (TypeError, ValueError):
            continue
    return ZoneBossRegistry(entries)
