"""Ghost Encounter stage (v0.5 stage expansion).

A rare matrix event that happens in deep architecture (ZoneDepth.DEEP / CORE
/ TA). The player encounters a Loa entity — a ghost-god of the matrix.
The player can choose: talk, fight, or leave.

Stage state: Stage.GHOST_ENCOUNTER
Game flow:
    - Player enters during matrix run (DEEP / CORE / TA zone)
    - Loa entity appears with ascii art
    - Player chooses: talk / fight / leave
    - talk → reward (data_fragment + faction rep)
    - fight → combat (high risk)
    - leave → safe but no reward

The Loa is a flavor event, not a required encounter. It's triggered
randomly during matrix exploration in deep zones.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class GhostChoice(StrEnum):
    """Player's choice on encountering a Loa ghost in the matrix.

    TALK: engage the construct and earn its data fragment + faction rep.
    FIGHT: high-risk combat against the Loa.
    LEAVE: safe but no reward.
    """

    TALK = "talk"
    FIGHT = "fight"
    LEAVE = "leave"


@dataclass(frozen=True, slots=True)
class GhostEncounter:
    """A Loa encounter definition.

    Attributes:
        id: Stable id (e.g. "loa.morrison").
        name_en: English name (the Loa's name).
        name_ko: Korean name.
        zone_requirement: Minimum zone depth required (DEEP, CORE, or TA).
        fragment_id: Data fragment id awarded on TALK (or None).
        faction_rep_delta: Tuple of (faction_id, delta) awarded on TALK.
        ascii_art: ASCII portrait of the Loa.
        dialogue_en: English opening line spoken by the Loa.
        dialogue_ko: Korean opening line.
    """

    id: str
    name_en: str
    name_ko: str
    zone_requirement: str
    fragment_id: str | None
    faction_rep_delta: tuple[tuple[str, int], ...]
    ascii_art: tuple[str, ...]
    dialogue_en: str
    dialogue_ko: str


GHOST_CATALOG: dict[str, GhostEncounter] = {
    "loa.morrison": GhostEncounter(
        id="loa.morrison",
        name_en="Morrison",
        name_ko="모리슨",
        zone_requirement="DEEP",
        fragment_id="fragment.morrison_echo",
        faction_rep_delta=(("voodoo", 5),),
        ascii_art=(
            "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
            "  ░   ◢◣◢◣◢◣◢◣◢◣◢◣◢◣  ░",
            "  ░  ──  MORRISON WAITS ── ░",
            "  ░  ░▒▓  IT KNOWS YOUR  ▓▒░ ░",
            "  ░  ░▒▓  NAME        ▓▒░ ░",
            "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
        ),
        dialogue_en="You are a long way from Chiba, cowboy. The cold out here has been waiting for you.",
        dialogue_ko="당신은 치바에서 먼 곳에 있군, 카우보이. 이쪽의 차가움이 당신을 기다리고 있었다.",
    ),
    "loa.zavijava": GhostEncounter(
        id="loa.zavijava",
        name_en="Zavijava (the loa of the channel)",
        name_ko="자비야바 (채널의 로아)",
        zone_requirement="CORE",
        fragment_id=None,
        faction_rep_delta=(("voodoo", 8),),
        ascii_art=(
            "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
            "  ░  ◢◣◢◣◢◣◢◣◢◣◢◣◢◣◢◣  ░",
            "  ░  ──  ZAVIJAVA SINGS ──  ░",
            "  ░  ░▒▓  THROUGH YOUR  ▓▒░ ░",
            "  ░  ░▒▓  ELECTRODES   ▓▒░ ░",
            "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
        ),
        dialogue_en="The channel is open. The channel is always open. Speak into it, cowboy.",
        dialogue_ko="채널이 열려 있다. 채널은 항상 열려 있다. 그것에 대고 말하라, 카우보이.",
    ),
}


def get_for_zone(zone: str) -> list[GhostEncounter]:
    """Return all ghost encounters available for a given zone depth.

    zone is the string name of ZoneDepth (e.g. "DEEP", "CORE", "TA").
    Returns encounters whose zone_requirement is <= the given zone in the
    order SURFACE (0) < MID (1) < DEEP (2) < CORE (3) < TA (4).
    """
    zone_order = {"SURFACE": 0, "MID": 1, "DEEP": 2, "CORE": 3, "TA": 4}
    current = zone_order.get(zone, 0)
    return [g for g in GHOST_CATALOG.values() if zone_order.get(g.zone_requirement, 0) <= current]


__all__ = [
    "GhostChoice",
    "GhostEncounter",
    "GHOST_CATALOG",
    "get_for_zone",
]
