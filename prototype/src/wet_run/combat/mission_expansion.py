"""Mission Expansion (ADR-0167).

6 mid-tier missions to bridge the Novice/Veteran/Heretic gap.
Total: 15 base + 4 Phase 6 + 6 expansion = 25 missions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExpansionMission:
    """A single expansion mission (15→25)."""

    id: str
    name: str
    difficulty: str
    zone: str
    description: str
    story_intro: str
    primary_ice: tuple[str, ...]


EXPANSION_MISSIONS: tuple[ExpansionMission, ...] = (
    ExpansionMission(
        id="hosaka_after_hours",
        name="HOSAKA AFTER HOURS",
        difficulty="novice",
        zone="surface",
        description="Corporate espionage at Hosaka — the suits are gone.",
        story_intro="After hours. The suits are gone. The data isn't.",
        primary_ice=("hosaka_security", "hosaka_watchdog"),
    ),
    ExpansionMission(
        id="sense_net_infiltration",
        name="SENSE/NET INFILTRATION",
        difficulty="veteran",
        zone="mid",
        description="ICE-heavy data heist in Sense/Net territory.",
        story_intro="The Sense/Net ring is layered. Deeper than you think.",
        primary_ice=("sense_net_black", "sense_net_watchdog"),
    ),
    ExpansionMission(
        id="yakuza_meeting",
        name="YAKUZA MEETING",
        difficulty="veteran",
        zone="mid",
        description="Social/intimidation scenario in yakuza territory.",
        story_intro="The yakuza don't negotiate. They *posture*.",
        primary_ice=("yakuza_ice", "yakuza_enforcer"),
    ),
    ExpansionMission(
        id="t_a_construction_site",
        name="T-A CONSTRUCTION SITE",
        difficulty="heretic",
        zone="core",
        description="T-A adjacent construction site — heavy ICE.",
        story_intro="They build. They never stop. You infiltrate.",
        primary_ice=("ta_construct_proxy", "ta_construct_prime"),
    ),
    ExpansionMission(
        id="zion_lab_breach",
        name="ZION LAB BREACH",
        difficulty="heretic",
        zone="core",
        description="Zion adjacent lab — experimental constructs.",
        story_intro="Zion is a club. The lab is what they don't show.",
        primary_ice=("zion_guard", "zion_experimental"),
    ),
    ExpansionMission(
        id="construct_market",
        name="CONSTRUCT MARKET",
        difficulty="novice",
        zone="surface",
        description="Pawn shop with ICE-protected merchandise.",
        story_intro="The market sells constructs. The ICE protects inventory.",
        primary_ice=("market_guard", "market_watchdog"),
    ),
)


def get_expansion_mission(mission_id: str) -> ExpansionMission | None:
    """Return an expansion mission by id, or None."""
    for mission in EXPANSION_MISSIONS:
        if mission.id == mission_id:
            return mission
    return None


def is_expansion_mission(mission_id: str) -> bool:
    """Check if a mission is an expansion mission."""
    return get_expansion_mission(mission_id) is not None


def expansion_mission_count() -> int:
    """Return the number of expansion missions."""
    return len(EXPANSION_MISSIONS)


def expansion_missions_by_difficulty(difficulty: str) -> tuple[ExpansionMission, ...]:
    """Return all expansion missions of a given difficulty."""
    return tuple(m for m in EXPANSION_MISSIONS if m.difficulty == difficulty)


def expansion_mission_ids() -> tuple[str, ...]:
    """Return all expansion mission ids."""
    return tuple(m.id for m in EXPANSION_MISSIONS)


__all__ = [
    "EXPANSION_MISSIONS",
    "ExpansionMission",
    "enrich_expansion_mission",
    "expansion_mission_count",
    "expansion_mission_ids",
    "expansion_missions_by_difficulty",
    "get_expansion_mission",
    "is_expansion_mission",
]


def enrich_expansion_mission(
    mission_id: str,
    base_data: dict[str, object],
) -> dict[str, object] | None:
    """Merge Mission Expansion registry fields into a base missions.json entry.

    Returns None when ``mission_id`` is not an expansion mission. When
    the base data already contains a key, the registry value does not
    override (missions.json remains authoritative).
    """
    mission = get_expansion_mission(mission_id)
    if mission is None:
        return None
    enriched = dict(base_data)
    registry_fields: dict[str, object] = {
        "registry_description": mission.description,
        "registry_story_intro": mission.story_intro,
        "registry_primary_ice": list(mission.primary_ice),
        "registry_source": "ADR-0167",
    }
    for key, value in registry_fields.items():
        enriched.setdefault(key, value)
    return enriched
