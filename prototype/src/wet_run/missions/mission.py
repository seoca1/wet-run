"""Mission data model (ADR-0010, ADR-0017, ADR-0188, story_skeleton.md).

Phase 11 additions per ADR-0188:
- 5 new mission types: investigation, defense, dual_objective, extraction_v2, stealth
- MissionChain class for chained missions
- Extended Objective schema with type-specific fields
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ..matrix.node import ZoneDepth


class MissionType(StrEnum):
    """Mission type taxonomy (ADR-0188, mission-types.md).

    Existing types (Phase 1-9):
        EXTRACT_DATA: Pull data from cyberspace
        DEFEAT: Defeat target ICE/boss
        DELIVER: Physical delivery
        ...

    New types (Phase 11):
        INVESTIGATION: Multi-stage intel-gathering (no combat)
        DEFENSE: Survive N waves, protect NPC
        DUAL_OBJECTIVE: Two simultaneous primaries
        EXTRACTION_V2: High-risk extraction with timer
        STEALTH: Avoid detection entirely
    """

    # Existing 6+ types
    EXTRACT_DATA = "extract_data"
    DEFEAT = "defeat"
    DELIVER = "deliver"
    CRAFT_ITEM = "craft_item"
    COLLECT_MATERIAL = "collect_material"
    AUDIT = "audit"
    INVESTIGATION = "investigation"
    DELIVER_MATERIAL = "deliver_material"
    DATA_ANALYSIS = "data_analysis"
    PATCH_ICE_VULNERABILITY = "patch_ice_vulnerability"

    # New 5 types (Phase 11)
    INVESTIGATION_COMPLETE = "investigation_complete"
    SURVIVE_N_WAVES = "survive_n_waves"
    EXTRACTION_AND_DEFEAT = "extraction_AND_defeat"
    REACH_TARGET_AND_EXTRACT_DATA = "reach_target_AND_extract_data"


@dataclass(frozen=True, slots=True)
class Objective:
    """A single mission objective (ADR-0017, ADR-0188).

    Existing fields from ADR-0017:
        type, count, material, enemy, data_id, item_type, tier_level

    New fields for Phase 11 types:
        evidence_required, evidence_types, wave_count, wave_intensity,
        time_limit_seconds, detection_threshold, no_combat_allowed,
        extract_spec, defeat_spec, target_id, objective_lock, etc.
    """

    type: str
    count: int = 1
    material: str | None = None
    enemy: str | None = None
    data_id: str | None = None
    item_type: str | None = None
    tier_level: int | None = None

    # Phase 11 fields — investigation type
    evidence_required: int | None = None
    evidence_types: tuple[str, ...] = ()

    # Phase 11 fields — defense type
    wave_count: int | None = None
    wave_intensity: str | None = None

    # Phase 11 fields — extraction_v2 / dual-objective
    time_limit_seconds: int | None = None
    penalty_on_failure: str | None = None
    extract_spec: dict[str, Any] | None = None
    defeat_spec: dict[str, Any] | None = None
    objective_lock: str | None = None

    # Phase 11 fields — stealth type
    detection_threshold: int | None = None
    no_combat_allowed: bool = False
    target_id: str | None = None
    alert_max: int | None = None
    logging_max: int | None = None
    min_evade: int | None = None
    must_survive: bool = False
    node_hp_min: int | None = None
    corruption_max: int | None = None

    # Phase 11 fields — chain integration
    chain_id: str | None = None
    chain_order: int | None = None
    chain_role: str | None = None


@dataclass(frozen=True, slots=True)
class Rewards:
    """Mission completion rewards (ADR-0017)."""

    credits: int = 0
    materials: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Mission:
    """A single cyberspace run definition (ADR-0010, ADR-0017, ADR-0188).

    Supports both the legacy fields (``objective``, ``reward_tier``,
    ``reward_credits``) and the new structured objectives / rewards
    introduced by ADR-0017, plus Phase 11 mission types.
    """

    id: str
    title: str
    fixer: str
    arc: int
    grade_min: int
    grade_max: int
    matrix_seed: int
    zone: ZoneDepth
    objective: str = ""
    reward_tier: int = 1
    reward_credits: int = 0
    primary_objective: Objective | None = None
    secondary_objectives: tuple[Objective, ...] = ()
    rewards: Rewards | None = None

    # Phase 11 fields (chain integration)
    is_chain_mission: bool = False
    chain_id: str | None = None
    chain_order: int | None = None

    def __post_init__(self) -> None:
        """Validate Mission invariants: non-empty id, arc in 1..6, grade range 1..6,
        reward_tier 1..6, reward_credits >= 0.

        arc 6 = Phase 6 (ADR-0166, NG+ Aftermath).

        All error messages include the offending value (or pair of values
        for the grade-range check) so JSON-data authors can locate the
        bad row quickly when ``missions.json`` fails to load.
        """
        if not self.id:
            raise ValueError("Mission id must be non-empty (got empty string)")
        if not 1 <= self.arc <= 6:
            raise ValueError(f"arc must be in 1..6, got {self.arc} (mission_id={self.id!r})")
        if not 1 <= self.grade_min <= self.grade_max <= 6:
            raise ValueError(
                f"invalid grade range {self.grade_min}..{self.grade_max} "
                "(both bounds must be in 1..6 with grade_min <= grade_max) "
                f"(mission_id={self.id!r})"
            )
        if not 1 <= self.reward_tier <= 6:
            raise ValueError(
                f"reward_tier must be in 1..6, got {self.reward_tier} (mission_id={self.id!r})"
            )
        if self.reward_credits < 0:
            raise ValueError(
                f"reward_credits must be >= 0, got {self.reward_credits} (mission_id={self.id!r})"
            )
        if self.is_chain_mission and not self.chain_id:
            raise ValueError(
                f"chain_mission must have a non-empty chain_id (mission_id={self.id!r})"
            )

    def primary_type(self) -> str:
        """Return the primary objective type, defaulting to 'extract_data'."""
        if self.primary_objective is not None:
            return self.primary_objective.type
        return "extract_data"

    def required_count(self) -> int:
        """Return how many items/events are required to complete primary objective."""
        if self.primary_objective is not None:
            return self.primary_objective.count
        return 1

    def check_completion(self, progress: dict[str, int]) -> bool:
        """Check if the mission is complete based on player progress.

        Args:
            progress: Dict of objective_type -> count.

        Returns:
            True if primary objective is satisfied.
        """
        if self.primary_objective is None:
            return False
        obj = self.primary_objective
        current = progress.get(obj.type, 0)
        return current >= obj.count

    def progress_pct(self, progress: dict[str, int]) -> float:
        """Return 0.0-1.0 progress toward primary objective."""
        required = self.required_count()
        if required <= 0:
            return 1.0
        if self.primary_objective is None:
            return 0.0
        current = progress.get(self.primary_objective.type, 0)
        return min(1.0, current / required)


# ----- Phase 11: Mission Chains (ADR-0188) -----


@dataclass(frozen=True, slots=True)
class ChainMission:
    """A single mission entry within a chain (ADR-0188)."""

    id: str
    order: int
    type: str  # e.g., "investigation", "defense"
    chain_role: str  # "intro" | "escalation" | "climax" | "revelation" | "resolution"


@dataclass(frozen=True, slots=True)
class ChainUnlockCondition:
    """Unlock condition for a chain (ADR-0188)."""

    arc_progress_min: int | None = None
    faction_reputation: dict[str, int] = field(default_factory=dict)
    min_grade: int | None = None
    prerequisite_chain: str | None = None


@dataclass(frozen=True, slots=True)
class ChainReward:
    """Chain-wide reward (ADR-0188)."""

    construct_unlock: str | None = None
    reputation_bonus: dict[str, int] = field(default_factory=dict)
    credits: int = 0
    achievement: str | None = None


@dataclass(frozen=True, slots=True)
class ChainFailure:
    """Chain-wide failure penalty (ADR-0188)."""

    reputation_penalty: dict[str, int] = field(default_factory=dict)
    construct_lock: str | None = None
    achievement: str | None = None


@dataclass(frozen=True, slots=True)
class MissionChain:
    """A 3-5 mission narrative chain (ADR-0188, mission-chains.md).

    Chains unlock mid-game, provide unique rewards, and have higher stakes
    than single missions (chain failure = significant penalty).
    """

    chain_id: str
    chain_name: str
    chain_type: str  # "faction_driven" | "character_driven" | "story_driven"
    chain_arc: int
    unlock_condition: ChainUnlockCondition
    missions: tuple[ChainMission, ...]
    chain_reward: ChainReward
    chain_failure: ChainFailure
    chain_midpoint_save: bool = True
    chain_estimated_time_minutes: int = 60

    def __post_init__(self) -> None:
        """Validate MissionChain invariants: non-empty chain_id, 3-5 missions in chain,
        chain_type in {faction_driven, character_driven, story_driven}."""
        if not self.chain_id:
            raise ValueError("chain_id must be non-empty")
        if not 3 <= len(self.missions) <= 5:
            raise ValueError(
                f"chain must have 3-5 missions, got {len(self.missions)} "
                "(see Phase 13 event chains in events.json: _chains section)"
            )
        if self.chain_type not in ("faction_driven", "character_driven", "story_driven"):
            raise ValueError(
                f"invalid chain_type: {self.chain_type!r} "
                "(must be one of: faction_driven, character_driven, story_driven)"
            )

    def sequence(self) -> tuple[ChainMission, ...]:
        """Return missions in order."""
        return tuple(sorted(self.missions, key=lambda m: m.order))
