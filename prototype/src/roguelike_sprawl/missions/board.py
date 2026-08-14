"""Job board: loads missions and filters by grade (ADR-0008, ADR-0010, ADR-0017).

Phase 6+: optionally filter by faction reputation so a player with
too-negative rep with a fixer's primary faction can't see (or take)
that fixer's missions. See :class:`JobBoard.locked_for` and
:func:`mission_rep_status`.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from typing_extensions import override

from ..matrix.node import ZoneDepth
from .mission import Mission, Objective, Rewards

if TYPE_CHECKING:
    from ..run.reputation import ReputationState


class MissionRepStatus(StrEnum):
    """Why a mission is or isn't available right now."""

    AVAILABLE = "available"  # Grade + reputation both qualify
    LOCKED_GRADE = "locked_grade"  # Player grade out of range
    LOCKED_REPUTATION = "locked_reputation"  # Player hostile to fixer's faction


def _mission_rep_status(mission: Mission, reputation: ReputationState | None) -> MissionRepStatus:
    """Determine why ``mission`` is/n't available right now.

    Args:
        mission: Mission to check.
        reputation: Player's faction reputation (or None for legacy
            state — every mission is AVAILABLE in that case).

    Returns:
        One of:
          - AVAILABLE: player qualifies (grade in range AND rep
            not hostile with any of the fixer's factions)
          - LOCKED_REPUTATION: player is at HOSTILE or worse with
            one of the fixer's primary factions
          - LOCKED_GRADE: player grade is out of [grade_min, grade_max]
    """
    # Lazy import to avoid circular dependency with reputation module.
    from ..run.reputation import reputation_tier

    # Rep-based lock: hostile with any of the fixer's factions
    # → mission locked regardless of grade.
    if reputation is not None:
        from ..engine.mission_completion import fixer_to_factions

        for faction in fixer_to_factions(mission.fixer):
            score = reputation.get(faction).score
            tier = reputation_tier(score)
            # Only hostile-or-worse tiers lock the mission. (NEUTRAL
            # and above are fine — the player is welcome to take the
            # job even if not allied.)
            if tier in ("HOSTILE", "ENEMY", "OUTCAST"):
                return MissionRepStatus.LOCKED_REPUTATION
    return MissionRepStatus.AVAILABLE


class JobBoard:
    """The pool of available missions, filterable by player grade.

    Loads from ``missions.json`` (a flat dict of mission id -> mission data).
    Supports both the legacy format (ADR-0010) and the new structured
    format (ADR-0017).
    """

    __slots__ = ("_missions",)

    def __init__(self, missions: tuple[Mission, ...] = ()) -> None:
        """Create a JobBoard pre-populated with ``missions`` (indexed by id)."""
        self._missions = {m.id: m for m in missions}

    @classmethod
    def load(cls, path: Path) -> JobBoard:
        """Load a JobBoard from a JSON file.

        Missing or empty file yields an empty board (not an error).
        Malformed entries are skipped (caller can lint the data file).
        """
        if not path.exists():
            return cls()
        with path.open(encoding="utf-8") as f:
            raw: object = json.load(f)
        if not isinstance(raw, dict):
            return cls()
        missions: list[Mission] = []
        for value in raw.values():
            if not isinstance(value, dict):
                continue
            mission = _parse_mission(value)
            if mission is not None:
                missions.append(mission)
        return cls(tuple(missions))

    def add(self, mission: Mission) -> None:
        """Add or replace a mission by id."""
        self._missions[mission.id] = mission

    def get(self, mission_id: str) -> Mission | None:
        """Return a mission by id, or None if absent."""
        return self._missions.get(mission_id)

    def available_for(
        self,
        grade: int,
        reputation: ReputationState | None = None,
    ) -> tuple[Mission, ...]:
        """Return missions whose ``[grade_min, grade_max]`` includes ``grade``.

        Args:
            grade: Player's current grade (1..6).
            reputation: Optional player reputation state. When provided,
                missions whose fixer is hostile to the player are
                excluded (see :func:`mission_rep_status`).

        Returns:
            Tuple of missions the player can currently take. Empty
            tuple if no missions qualify.
        """
        return tuple(
            m
            for m in self._missions.values()
            if m.grade_min <= grade <= m.grade_max
            and _mission_rep_status(m, reputation)
            in (MissionRepStatus.AVAILABLE, MissionRepStatus.LOCKED_GRADE)
        )

    def select_weighted(
        self,
        state: object,
        available: tuple[Mission, ...] | None = None,
        seed: int | None = None,
    ) -> Mission | None:
        """Select a mission using random_rules weighting (ADR-0188).

        Applies 19 random selection rules from random_selection_rules.json
        to weight the available missions for the current run state.

        Args:
            state: Player/AppState with reputation and progression data.
            available: Optional pre-filtered mission list. If None,
                uses ``available_for()`` with grade from state.
            seed: Optional random seed for deterministic selection.

        Returns:
            Selected mission, or None if no missions available.
        """
        from .random_rules import get_random_mission_with_rule

        if available is None:
            grade = getattr(state, "grade", 1)
            reputation = getattr(state, "reputation", None)
            available = self.available_for(grade, reputation)

        if not available:
            return None

        mission_ids = [m.id for m in available]
        result = get_random_mission_with_rule(state, mission_ids, seed=seed)
        if result is None:
            return None
        selected_id, rule_id = result
        # Phase 17: tag the state with the rule that fired so the Hub UI
        # can annotate the highlighted mission. Production state
        # (AppState) has the field; dummy test states without it are
        # simply skipped via getattr → attribute guard.
        if hasattr(state, "last_rule_id"):
            state.last_rule_id = rule_id
        return self.get(selected_id)

    def select_by_faction(
        self,
        faction: str,
        grade: int,
        reputation: ReputationState | None = None,
    ) -> tuple[Mission, ...]:
        """Return available missions for a specific faction's fixer.

        Applies random_rules' faction-weighted selection to bias
        toward missions from the requested faction.
        """
        available = self.available_for(grade, reputation)
        return tuple(m for m in available if m.fixer == faction)

    def locked_for(self, reputation: ReputationState | None) -> tuple[Mission, ...]:
        """Return missions locked out by the player's reputation.

        These are missions the player could otherwise take (grade
        in range) but whose fixer is hostile with one of the player's
        factions. Useful for the Hub's "locked" sub-list display.
        """
        return tuple(
            m
            for m in self._missions.values()
            if _mission_rep_status(m, reputation) is MissionRepStatus.LOCKED_REPUTATION
        )

    def mission_status(
        self, mission: Mission | None, grade: int, reputation: ReputationState | None = None
    ) -> MissionRepStatus | None:
        """Return the availability status of ``mission`` for the given
        player state.

        Args:
            mission: Mission to check (or None for unknown mission —
                returns None).
            grade: Player's current grade.
            reputation: Optional player reputation.

        Returns:
            One of AVAILABLE / LOCKED_GRADE / LOCKED_REPUTATION, or
            None if ``mission`` is None (unknown id).

        Precedence:
          1. LOCKED_REPUTATION — player hostile to fixer's faction
          2. LOCKED_GRADE — grade out of range
          3. AVAILABLE — both checks pass
        """
        if mission is None:
            return None
        rep_status = _mission_rep_status(mission, reputation)
        if rep_status is MissionRepStatus.LOCKED_REPUTATION:
            return MissionRepStatus.LOCKED_REPUTATION
        if not (mission.grade_min <= grade <= mission.grade_max):
            return MissionRepStatus.LOCKED_GRADE
        return MissionRepStatus.AVAILABLE

    def __iter__(self) -> Iterator[Mission]:
        return iter(self._missions.values())

    def __len__(self) -> int:
        return len(self._missions)

    def __contains__(self, mission_id: object) -> bool:
        return isinstance(mission_id, str) and mission_id in self._missions

    @override
    def __repr__(self) -> str:
        return f"JobBoard({len(self._missions)} missions)"


def _parse_objective(raw: object) -> Objective | None:
    if not isinstance(raw, dict):
        return None
    try:
        tier_raw = raw.get("tier_level")
        tier_value: int | None = None
        if tier_raw is not None and not isinstance(tier_raw, bool):
            try:
                tier_value = int(tier_raw)
            except (TypeError, ValueError):
                tier_value = None
        count_raw = raw.get("count", 1)
        count_value: int = 1
        if count_raw is not None and not isinstance(count_raw, bool):
            try:
                count_value = int(count_raw)
            except (TypeError, ValueError):
                count_value = 1
        return Objective(
            type=str(raw.get("type", "")),
            count=count_value,
            material=_opt_str(raw.get("material")),
            enemy=_opt_str(raw.get("enemy")),
            data_id=_opt_str(raw.get("data_id")),
            item_type=_opt_str(raw.get("item_type")),
            tier_level=tier_value,
        )
    except (TypeError, ValueError):
        return None


def _parse_rewards(raw: object) -> Rewards | None:
    if not isinstance(raw, dict):
        return None
    credits_value = _opt_int(raw.get("credits"), 0) or 0
    materials_raw = raw.get("materials", {})
    materials: dict[str, int] = {}
    if isinstance(materials_raw, dict):
        for k, v in materials_raw.items():
            count = _opt_int(v, 0)
            if count is not None:
                materials[str(k)] = count
    return Rewards(credits=credits_value, materials=materials)


def _parse_mission(value: dict[str, object]) -> Mission | None:
    try:
        primary = _parse_objective(value.get("primary_objective"))
        secondary_raw = value.get("secondary_objectives", ())
        secondary: list[Objective] = []
        if isinstance(secondary_raw, list):
            for s in secondary_raw:
                obj = _parse_objective(s)
                if obj is not None:
                    secondary.append(obj)
        rewards = _parse_rewards(value.get("rewards"))

        if primary is None:
            obj_text = str(value.get("objective", ""))
            if obj_text:
                primary = Objective(type="extract_data", data_id=obj_text)
        if rewards is None:
            credits_value = _opt_int(value.get("reward_credits"), 0) or 0
            rewards = Rewards(credits=credits_value, materials={})

        return Mission(
            id=str(value["id"]),
            title=str(value["title"]),
            fixer=str(value["fixer"]),
            arc=_opt_int(value.get("arc"), 0) or 1,
            grade_min=_opt_int(value.get("grade_min"), 0) or 1,
            grade_max=_opt_int(value.get("grade_max"), 0) or 1,
            matrix_seed=_opt_int(value.get("matrix_seed"), 0) or 0,
            zone=ZoneDepth(str(value["zone"])),
            objective=str(value.get("objective", "")),
            reward_tier=_opt_int(value.get("reward_tier"), 1) or 1,
            reward_credits=rewards.credits,
            primary_objective=primary,
            secondary_objectives=tuple(secondary),
            rewards=rewards,
        )
    except (KeyError, TypeError, ValueError):
        return None


def _opt_int(value: object, default: int) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, (str, bytes, bytearray)):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _opt_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
