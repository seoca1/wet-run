"""Near-Miss Extraction (ADR-0140 P3.6).

When the player reaches an exit node with HP above a threshold
(default 80%), grant a bonus reward. Encourages careful play and
rewards skill instead of brute-force extraction.

Pillar 4 safe: rewards are in-run + ephemeral (death = loss).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

# Default HP threshold (0.80 = 80%). Tunable via plan review.
DEFAULT_NEAR_MISS_HP_THRESHOLD: float = 0.80

# Reward constants (flat, no scaling).
NEAR_MISS_CREDITS: int = 75
NEAR_MISS_SALVAGE: int = 1


class NearMissRewardKind(StrEnum):
    """Kinds of near-miss bonus rewards."""

    CREDITS = "credits"
    SALVAGE = "salvage"


@dataclass(frozen=True, slots=True)
class NearMissReward:
    """A single near-miss bonus reward component."""

    kind: NearMissRewardKind
    amount: int
    label: str


@dataclass(frozen=True, slots=True)
class NearMissResult:
    """Outcome of a near-miss extraction check."""

    triggered: bool
    hp_ratio: float
    threshold: float
    rewards: tuple[NearMissReward, ...]
    status_message: str


def compute_hp_ratio(player_hp: int, player_max_hp: int) -> float:
    """Compute HP ratio, clamped to [0, 1].

    Args:
        player_hp: Current HP.
        player_max_hp: Max HP (must be > 0).

    Returns:
        HP / max_hp, clamped to [0, 1]. Returns 0.0 if max_hp <= 0.
    """
    if player_max_hp <= 0:
        return 0.0
    return max(0.0, min(1.0, player_hp / player_max_hp))


def check_near_miss_extraction(
    state: Any,
    *,
    threshold: float = DEFAULT_NEAR_MISS_HP_THRESHOLD,
    already_triggered: bool = False,
) -> NearMissResult:
    """Check if near-miss extraction bonus applies and apply it.

    Args:
        state: AppState-like object with player_hp, player_max_hp, near_miss_triggered,
            credits, salvage_fragments, status_messages attributes.
        threshold: HP ratio threshold (default 0.80).
        already_triggered: Set externally to skip if already fired this run.

    Returns:
        NearMissResult with triggered flag, rewards, and status message.
        Also appends the message to state.status_messages on success.
    """
    hp = getattr(state, "player_hp", 0)
    max_hp = getattr(state, "player_max_hp", 0)
    hp_ratio = compute_hp_ratio(hp, max_hp)

    if already_triggered or hp_ratio < threshold:
        return NearMissResult(
            triggered=False,
            hp_ratio=hp_ratio,
            threshold=threshold,
            rewards=(),
            status_message="",
        )

    rewards = (
        NearMissReward(
            kind=NearMissRewardKind.CREDITS,
            amount=NEAR_MISS_CREDITS,
            label=f"+{NEAR_MISS_CREDITS} credits",
        ),
        NearMissReward(
            kind=NearMissRewardKind.SALVAGE,
            amount=NEAR_MISS_SALVAGE,
            label=f"+{NEAR_MISS_SALVAGE} salvage fragment",
        ),
    )

    current_credits = getattr(state, "credits", 0) or 0
    state.credits = current_credits + NEAR_MISS_CREDITS
    current_salvage = getattr(state, "salvage_fragments", 0) or 0
    state.salvage_fragments = current_salvage + NEAR_MISS_SALVAGE

    pct = int(hp_ratio * 100)
    msg = f">>> Near-miss extraction ({pct}% HP): {rewards[0].label}, {rewards[1].label}"
    status_list = getattr(state, "status_messages", None)
    if isinstance(status_list, list):
        status_list.append(msg)

    return NearMissResult(
        triggered=True,
        hp_ratio=hp_ratio,
        threshold=threshold,
        rewards=rewards,
        status_message=msg,
    )


__all__ = [
    "DEFAULT_NEAR_MISS_HP_THRESHOLD",
    "NEAR_MISS_CREDITS",
    "NEAR_MISS_SALVAGE",
    "NearMissRewardKind",
    "NearMissReward",
    "NearMissResult",
    "compute_hp_ratio",
    "check_near_miss_extraction",
]
