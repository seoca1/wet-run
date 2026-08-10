"""Boss Phase Transitions Integration (F.4, ADR-0180/0190, Round 6).

Integrates F.4 boss profiles (Neuromancer, Loa Baron, Black Baron) with
the existing combat phase transition system. Provides:
- BossPhaseTracker: tracks current phase and handles transitions
- get_current_phase: query current phase from boss profile
- should_transition: check if phase should change based on HP
- apply_phase_effects: apply phase effects to combat
- get_phase_progress: get progress through current phase
"""

from __future__ import annotations

from dataclasses import dataclass

from .boss_expansion import (
    BLACK_BARON_PROFILE,
    BOSS_EXPANSION_REGISTRY,
    LOA_BARON_PROFILE,
    NEUROMANCER_PROFILE,
    BossPhase,
    BossProfile,
)


@dataclass(frozen=True, slots=True)
class PhaseProgress:
    """Progress information for a boss phase."""

    boss_id: str
    phase_index: int
    hp_threshold: float
    hp_fraction: float
    progress_in_phase: float
    is_last_phase: bool

    def is_transition_boundary(self) -> bool:
        """Return True if HP is at or below the threshold for transition."""
        if self.is_last_phase:
            return False
        return self.hp_fraction <= self.hp_threshold


class BossPhaseTracker:
    """Tracks phase transitions for an F.4 boss profile."""

    def __init__(self, boss_profile: BossProfile) -> None:
        self._boss = boss_profile
        self._current_phase_index = 0

    @property
    def boss(self) -> BossProfile:
        """Return the boss profile."""
        return self._boss

    @property
    def current_phase_index(self) -> int:
        """Return the current phase index (0-based)."""
        return self._current_phase_index

    @property
    def current_phase(self) -> BossPhase:
        """Return the current phase."""
        return self._boss.phases[self._current_phase_index]

    @property
    def total_phases(self) -> int:
        """Return total number of phases."""
        return len(self._boss.phases)

    @property
    def is_last_phase(self) -> bool:
        """Return True if on the last phase."""
        return self._current_phase_index >= len(self._boss.phases) - 1

    def get_phase(self, index: int) -> BossPhase:
        """Return the phase at the given index."""
        return self._boss.phases[index]

    def get_progress(self, hp: int, max_hp: int) -> PhaseProgress:
        """Get progress information for the current phase."""
        hp_fraction = hp / max_hp if max_hp > 0 else 0.0
        if self.is_last_phase:
            next_threshold = self.current_phase.hp_threshold
        else:
            next_threshold = self._boss.phases[self._current_phase_index + 1].hp_threshold
        return PhaseProgress(
            boss_id=self._boss.id,
            phase_index=self._current_phase_index,
            hp_threshold=next_threshold,
            hp_fraction=hp_fraction,
            progress_in_phase=hp_fraction / self.current_phase.hp_threshold
            if self.current_phase.hp_threshold > 0
            else 0.0,
            is_last_phase=self.is_last_phase,
        )

    def should_transition(self, hp: int, max_hp: int) -> bool:
        """Return True if the boss should transition to the next phase."""
        if self.is_last_phase:
            return False
        hp_fraction = hp / max_hp if max_hp > 0 else 0.0
        next_threshold = self._boss.phases[self._current_phase_index + 1].hp_threshold
        return hp_fraction <= next_threshold

    def transition(self) -> BossPhase | None:
        """Advance to the next phase. Return the new phase or None if at last."""
        if self.is_last_phase:
            return None
        self._current_phase_index += 1
        return self.current_phase

    def get_damage_multiplier(self) -> float:
        """Return the current phase's damage multiplier."""
        return self.current_phase.damage_multiplier

    def get_glyph(self) -> str:
        """Return the current phase's glyph."""
        return self.current_phase.glyph

    def get_color(self) -> tuple[int, int, int]:
        """Return the current phase's color."""
        return self.current_phase.color

    def get_intro_text(self) -> str:
        """Return the current phase's intro text."""
        return self.current_phase.intro_text

    def reset(self) -> None:
        """Reset to the first phase."""
        self._current_phase_index = 0


def get_tracker_for_boss(boss_id: str) -> BossPhaseTracker | None:
    """Return a phase tracker for the given boss id, or None if not found."""
    profile = BOSS_EXPANSION_REGISTRY.get(boss_id)
    if profile is None:
        return None
    return BossPhaseTracker(profile)


def get_all_f4_boss_ids() -> tuple[str, ...]:
    """Return all F.4 boss ids."""
    return tuple(BOSS_EXPANSION_REGISTRY.keys())


def get_neuromancer_tracker() -> BossPhaseTracker:
    """Return tracker for Neuromancer."""
    return BossPhaseTracker(NEUROMANCER_PROFILE)


def get_loa_baron_tracker() -> BossPhaseTracker:
    """Return tracker for Loa Baron."""
    return BossPhaseTracker(LOA_BARON_PROFILE)


def get_black_baron_tracker() -> BossPhaseTracker:
    """Return tracker for Black Baron."""
    return BossPhaseTracker(BLACK_BARON_PROFILE)


def get_phase_count_for_boss(boss_id: str) -> int:
    """Return the number of phases for a boss."""
    profile = BOSS_EXPANSION_REGISTRY.get(boss_id)
    if profile is None:
        return 0
    return len(profile.phases)


def get_phase_info(boss_id: str, phase_index: int) -> BossPhase | None:
    """Get a specific phase from a boss profile."""
    profile = BOSS_EXPANSION_REGISTRY.get(boss_id)
    if profile is None:
        return None
    if phase_index < 0 or phase_index >= len(profile.phases):
        return None
    return profile.phases[phase_index]


def should_trigger_phase_transition(
    boss_id: str, hp: int, max_hp: int, current_phase_index: int
) -> bool:
    """Check if a boss should transition based on HP and current phase."""
    profile = BOSS_EXPANSION_REGISTRY.get(boss_id)
    if profile is None:
        return False
    if current_phase_index >= len(profile.phases) - 1:
        return False
    hp_fraction = hp / max_hp if max_hp > 0 else 0.0
    next_threshold = profile.phases[current_phase_index + 1].hp_threshold
    return hp_fraction <= next_threshold


def get_next_phase(boss_id: str, current_phase_index: int) -> BossPhase | None:
    """Get the next phase for a boss."""
    profile = BOSS_EXPANSION_REGISTRY.get(boss_id)
    if profile is None:
        return None
    next_index = current_phase_index + 1
    if next_index >= len(profile.phases):
        return None
    return profile.phases[next_index]


def get_damage_multiplier_for_phase(boss_id: str, phase_index: int) -> float:
    """Get damage multiplier for a specific phase."""
    phase = get_phase_info(boss_id, phase_index)
    if phase is None:
        return 1.0
    return phase.damage_multiplier


def get_remaining_phases(boss_id: str, current_phase_index: int) -> int:
    """Get the number of remaining phases after current."""
    profile = BOSS_EXPANSION_REGISTRY.get(boss_id)
    if profile is None:
        return 0
    return max(0, len(profile.phases) - current_phase_index - 1)


__all__ = [
    "BossPhaseTracker",
    "PhaseProgress",
    "get_all_f4_boss_ids",
    "get_black_baron_tracker",
    "get_damage_multiplier_for_phase",
    "get_loa_baron_tracker",
    "get_neuromancer_tracker",
    "get_next_phase",
    "get_phase_count_for_boss",
    "get_phase_info",
    "get_remaining_phases",
    "get_tracker_for_boss",
    "should_trigger_phase_transition",
]
