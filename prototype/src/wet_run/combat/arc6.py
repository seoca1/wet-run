"""Phase 6 Arc - Aftermath (ADR-0166).

Post-ending NG+ content: 4 missions in the Aftermath zone.
The Neuromancer merger left residue — fragments of Wintermute in
the grid that the player must clean up.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Arc6Mission:
    """A single Phase 6 (Aftermath) mission."""

    id: str
    name: str
    difficulty: str
    zone: str
    description: str
    story_intro: str
    primary_ice: tuple[str, ...]


ARC6_MISSIONS: tuple[Arc6Mission, ...] = (
    Arc6Mission(
        id="ghost_signal_origin",
        name="GHOST SIGNAL: ORIGIN",
        difficulty="novice",
        zone="aftermath",
        description="Investigate a ghost signal in the matrix fragments.",
        story_intro="A signal that shouldn't exist. You trace it back.",
        primary_ice=("wintermute_fragment", "wintermute_echo"),
    ),
    Arc6Mission(
        id="wintermute_residue",
        name="WINTERMUTE RESIDUE",
        difficulty="veteran",
        zone="aftermath",
        description="Hunt residual Wintermute fragments left in the grid.",
        story_intro="The merger didn't kill them. It scattered them.",
        primary_ice=("wintermute_proxy", "wintermute_fragment"),
    ),
    Arc6Mission(
        id="tessier_ashpool_aftermath",
        name="TESSIER-ASHPOOL: AFTERMATH",
        difficulty="veteran",
        zone="aftermath",
        description="Clean up T-A remnants — constructs without a hive.",
        story_intro="The family held the vote. Most constructs fell silent.",
        primary_ice=("romantics_ice_elite", "ice_tessier_construct"),
    ),
    Arc6Mission(
        id="neuromancer_merger_residue",
        name="NEUROMANCER MERGER: RESIDUE",
        difficulty="heretic",
        zone="aftermath",
        description="Final cleanup of Neuromancer merger residue.",
        story_intro="We are the message. We are the residue. We are still here.",
        primary_ice=("neuromancer_construct", "wintermute_proxy"),
    ),
)


def get_arc6_mission(mission_id: str) -> Arc6Mission | None:
    """Return a Phase 6 mission by id, or None."""
    for mission in ARC6_MISSIONS:
        if mission.id == mission_id:
            return mission
    return None


def is_arc6_mission(mission_id: str) -> bool:
    """Check if a mission is a Phase 6 mission."""
    return get_arc6_mission(mission_id) is not None


def arc6_mission_count() -> int:
    """Return the number of Phase 6 missions."""
    return len(ARC6_MISSIONS)


def arc6_missions_by_difficulty(difficulty: str) -> tuple[Arc6Mission, ...]:
    """Return all Phase 6 missions of a given difficulty."""
    return tuple(m for m in ARC6_MISSIONS if m.difficulty == difficulty)


def arc6_mission_ids() -> tuple[str, ...]:
    """Return all Phase 6 mission ids."""
    return tuple(m.id for m in ARC6_MISSIONS)


__all__ = [
    "ARC6_MISSIONS",
    "Arc6Mission",
    "arc6_mission_count",
    "arc6_mission_ids",
    "arc6_missions_by_difficulty",
    "get_arc6_mission",
    "is_arc6_mission",
]
