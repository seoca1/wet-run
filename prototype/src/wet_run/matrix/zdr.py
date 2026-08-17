"""Zone Difficulty Rating (ZDR) and Status (ADR-0012).

ZDR is a single integer that summarizes how dangerous a node/zone is.
Status is the player's relative strength assessment, derived from PPL/ZDR.
"""

from __future__ import annotations

from enum import StrEnum

from .node import AlarmLevel, Faction, IceKind, Node, ZoneDepth

# --- Base ZDR by zone (ADR-0012 / design/systems/hacking.md) ---
_BASE_ZDR: dict[ZoneDepth, int] = {
    ZoneDepth.SURFACE: 1,
    ZoneDepth.MID: 5,
    ZoneDepth.DEEP: 8,  # Loa / construct zones (between MID and CORE)
    ZoneDepth.CORE: 12,
    ZoneDepth.TA: 25,
    ZoneDepth.FREESIDE: 30,  # Orbital colonies (hardest)
    ZoneDepth.SOHO: 3,  # 3-5 (London-style black market district)
    ZoneDepth.TOKYO: 6,  # 5-8 (Yakuza-adjacent underworld district)
}

# --- ICE modifier (per ADR-0012) ---
_ICE_MODIFIER: dict[IceKind, int] = {
    IceKind.NONE: 0,
    IceKind.STANDARD: 2,
    IceKind.WATCHDOG: 1,
    IceKind.BLACK: 10,
}

# --- Alarm modifier (per ADR-0012) ---
_ALARM_MODIFIER: dict[AlarmLevel, int] = {
    AlarmLevel.LOW: 0,
    AlarmLevel.MEDIUM: 3,
    AlarmLevel.HIGH: 5,
    AlarmLevel.CRITICAL: 10,
}

# --- Faction modifier (per ADR-0012) ---
_FACTION_MODIFIER: dict[Faction, int] = {
    Faction.NONE: 0,
    Faction.HOSAKA: 2,
    Faction.MAAS: 3,
    Faction.SENSE_NET: 4,
    Faction.TA: 5,
}


class Status(StrEnum):
    """Player power assessment relative to a ZDR (ADR-0012)."""

    SAFE = "safe"
    MATCH = "match"
    TOUGH = "tough"
    DEADLY = "deadly"
    FUTILE = "futile"


# Status color palette (RGB). Mirrors `portraits/manager.py` COLOR_NAMES.
_STATUS_COLORS: dict[Status, tuple[int, int, int]] = {
    Status.SAFE: (0, 255, 0),  # green
    Status.MATCH: (0, 255, 255),  # cyan
    Status.TOUGH: (255, 255, 0),  # yellow
    Status.DEADLY: (255, 0, 64),  # red
    Status.FUTILE: (128, 0, 32),  # dark_red
}


def base_zdr(zone: ZoneDepth) -> int:
    """Return the base ZDR for a zone (ADR-0012)."""
    return _BASE_ZDR[zone]


def calculate_zdr(
    zone: ZoneDepth,
    ice: IceKind = IceKind.NONE,
    alarm: AlarmLevel = AlarmLevel.LOW,
    faction: Faction = Faction.NONE,
) -> int:
    """Compute the ZDR for a node (ADR-0012)."""
    return (
        _BASE_ZDR[zone] + _ICE_MODIFIER[ice] + _ALARM_MODIFIER[alarm] + _FACTION_MODIFIER[faction]
    )


def calculate_status(ppl: int, zdr: int) -> Status:
    """Return the Status category for a given PPL vs ZDR (ADR-0012).

    ZDR == 0 is treated as SAFE (no risk).
    """
    if zdr <= 0:
        return Status.SAFE
    ratio = ppl / zdr
    if ratio > 1.5:
        return Status.SAFE
    if ratio >= 1.0:
        return Status.MATCH
    if ratio >= 0.75:
        return Status.TOUGH
    if ratio >= 0.5:
        return Status.DEADLY
    return Status.FUTILE


def status_color(status: Status) -> tuple[int, int, int]:
    """Return the RGB color tuple for a Status (ADR-0011, ADR-0012)."""
    return _STATUS_COLORS[status]


def node_zdr(node: Node) -> int:
    """Convenience: compute ZDR directly from a Node."""
    return calculate_zdr(node.zone, node.ice, node.alarm, node.faction)


def node_status(node: Node, ppl: int) -> Status:
    """Convenience: compute Status for a Node given the player's PPL."""
    return calculate_status(ppl, node_zdr(node))
