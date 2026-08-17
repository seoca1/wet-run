"""Variable Reward Nodes — anomaly reward distribution (ADR-0140 P2.6).

When the player enters a matrix node flagged as ``is_anomaly``, this
module rolls a reward from the engagement table and applies it to the
``AppState`` (one-shot, run-scoped — never cross-run, Pillar 4 safe).

Reward kinds (Pillar 4 compliant — no inheritance):
    CREDITS  +50 in-run credits (flat)
    SALVAGE +1 salvage fragment (in-run crafting material)
    INFO    +1 lore/info piece (narrative, in-run only)
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class AnomalyRewardKind(StrEnum):
    """Anomaly reward kinds (ADR-0140 P2.6)."""

    CREDITS = "credits"
    SALVAGE = "salvage"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class AnomalyReward:
    """A single anomaly reward pick."""

    kind: AnomalyRewardKind
    amount: int
    label: str


@dataclass(frozen=True, slots=True)
class AnomalyResult:
    """Outcome of an anomaly-trigger check on node entry."""

    reward: AnomalyReward | None
    status_message: str


# Reward weights (uniform across kinds; tier scaling deferred to v1.1.0+).
# All rewards are *flat* — none cross runs (Pillar 4 unlocked-metaprogression-only).
_REWARD_TABLE: dict[AnomalyRewardKind, AnomalyReward] = {
    AnomalyRewardKind.CREDITS: AnomalyReward(
        kind=AnomalyRewardKind.CREDITS,
        amount=50,
        label="+50 credits",
    ),
    AnomalyRewardKind.SALVAGE: AnomalyReward(
        kind=AnomalyRewardKind.SALVAGE,
        amount=1,
        label="+1 salvage fragment",
    ),
    AnomalyRewardKind.INFO: AnomalyReward(
        kind=AnomalyRewardKind.INFO,
        amount=1,
        label="+1 data fragment",
    ),
}


def roll_anomaly_reward(rng: random.Random) -> AnomalyReward:
    """Roll a uniform reward from the anomaly reward table.

    Args:
        rng: Random instance (seeded for determinism).

    Returns:
        AnomalyReward pick (always returns one — uniform distribution).
    """
    kinds = list(_REWARD_TABLE)
    chosen = kinds[rng.randrange(len(kinds))]
    return _REWARD_TABLE[chosen]


def apply_anomaly_reward(state: Any, reward: AnomalyReward) -> AnomalyResult:
    """Apply an anomaly reward to AppState (fields may not exist yet — defensive).

    New fields are added opportunistically if the state supports them:
    - credits:         int counter (added to existing or initialized)
    - salvage_fragments: int counter
    - info_pieces:     int counter

    Args:
        state: AppState-like object.
        reward: The reward to apply.

    Returns:
        AnomalyResult with the reward and a status message for the UI.
    """
    if reward.kind is AnomalyRewardKind.CREDITS:
        current = getattr(state, "credits", 0) or 0
        state.credits = current + reward.amount
    elif reward.kind is AnomalyRewardKind.SALVAGE:
        current = getattr(state, "salvage_fragments", 0) or 0
        state.salvage_fragments = current + reward.amount
    elif reward.kind is AnomalyRewardKind.INFO:
        current = getattr(state, "info_pieces", 0) or 0
        state.info_pieces = current + reward.amount

    msg = f">>> Anomaly recovered: {reward.label}"
    status_list = getattr(state, "status_messages", None)
    if isinstance(status_list, list):
        status_list.append(msg)

    return AnomalyResult(reward=reward, status_message=msg)


def check_anomaly_reward_on_node_entry(
    state: Any,
    node: Any,
    rng: random.Random,
    *,
    already_triggered: set[str],
) -> AnomalyResult:
    """Check if the entered node is an anomaly and apply reward if eligible.

    Args:
        state: AppState-like object.
        node: Node that was entered.
        rng: Random instance.
        already_triggered: Set of node ids that already fired in this run
            (prevents double-trigger on re-entry).

    Returns:
        AnomalyResult with reward (or None) and status message.
    """
    if not getattr(node, "is_anomaly", False):
        return AnomalyResult(reward=None, status_message="")
    if node.id in already_triggered:
        return AnomalyResult(
            reward=None,
            status_message=">>> Anomaly node already triggered this run",
        )

    reward = roll_anomaly_reward(rng)
    already_triggered.add(node.id)
    return apply_anomaly_reward(state, reward)


__all__ = [
    "AnomalyRewardKind",
    "AnomalyReward",
    "AnomalyResult",
    "roll_anomaly_reward",
    "apply_anomaly_reward",
    "check_anomaly_reward_on_node_entry",
]
