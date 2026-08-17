"""Story event rewards — credit/material/faction-rep grants.

When the player triggers an event story (aftermath, dialogue, chapter
complete), the engine can apply one or more rewards via the
:func:`apply_event_rewards` helper.

The reward schema is intentionally simple — a list of
``{kind, value, source}`` dicts loaded from JSON. New reward kinds
(achievements, equipment drops, etc.) can be added by extending
:class:`RewardKind`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from ..matrix.node import Faction
from ..run.reputation import clamp_delta

if TYPE_CHECKING:
    from ..engine.state import AppState


class RewardKind(StrEnum):
    """How a story event reward is applied to the player."""

    CREDITS = "credits"  # Direct credit grant
    MATERIAL = "material"  # Material grant (e.g. "data_fragment": 1)
    REPUTATION = "reputation"  # Faction reputation delta
    ACHIEVEMENT = "achievement"  # Unlock an achievement by id


@dataclass(frozen=True, slots=True)
class StoryReward:
    """A single reward from a story event.

    Attributes:
        kind: What kind of reward.
        target: What is affected (item id, faction name, achievement
            id, etc.). For CREDITS this is unused.
        amount: Magnitude (credits, material count, rep delta).
    """

    kind: RewardKind
    target: str
    amount: int

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> StoryReward | None:
        """Parse from JSON dict, returning None for malformed entries.

        Args:
            raw: Dict with keys ``kind``, ``target``, ``amount``.
                ``target`` may be missing for CREDITS rewards.
        """
        try:
            kind = RewardKind(str(raw.get("kind", "")))
            target = str(raw.get("target", ""))
            raw_amount: object = raw.get("amount", 0)
            if not isinstance(raw_amount, (bool, int)):
                raw_amount = str(raw_amount) if raw_amount is not None else "0"
            amount = int(raw_amount)
        except (ValueError, TypeError):
            return None
        return cls(kind=kind, target=target, amount=amount)


def apply_event_rewards(state: AppState, rewards: list[StoryReward]) -> list[str]:
    """Apply a list of rewards to ``state``, returning a status summary.

    Each applied reward is reported as a short string suitable for the
    status message panel. The function never raises — bad reward data
    is silently skipped (logged in the returned summary as
    ``"<kind>: failed"``).

    Args:
        state: App state to mutate.
        rewards: List of rewards to apply.

    Returns:
        List of human-readable status strings, one per applied or
        skipped reward.
    """
    summaries: list[str] = []
    for r in rewards:
        try:
            if r.kind is RewardKind.CREDITS:
                state.credits += r.amount
                summaries.append(f"+{r.amount} credits")
            elif r.kind is RewardKind.MATERIAL:
                if not hasattr(state, "inventory") or state.inventory is None:
                    state.inventory = {}
                state.inventory[r.target] = state.inventory.get(r.target, 0) + r.amount
                summaries.append(f"+{r.amount}x {r.target}")
            elif r.kind is RewardKind.REPUTATION:
                try:
                    faction = Faction(r.target)
                except ValueError:
                    summaries.append(f"Rep {r.target}: invalid")
                    continue
                clamped = clamp_delta(r.amount)
                state.reputation.adjust(faction, clamped, source="event")
                summaries.append(f"Rep {r.target}: {clamped:+d}")
            elif r.kind is RewardKind.ACHIEVEMENT:
                # Achievements are managed by achievements.AchievementState.
                # We don't have a direct handle here; the event_story
                # machinery would fire its own achievement check.
                summaries.append(f"Achievement: {r.target}")
        except Exception as exc:
            # Defensive: never let a bad reward break the event flow.
            summaries.append(f"{r.kind.value}: failed ({exc})")
    return summaries


def load_rewards_from(raw: list[object] | None) -> list[StoryReward]:
    """Parse a list of reward dicts (from JSON) into StoryReward objects.

    Invalid entries are silently skipped. Returns empty list if ``raw``
    is None or not a list.
    """
    if not isinstance(raw, list):
        return []
    rewards: list[StoryReward] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        reward = StoryReward.from_dict(item)
        if reward is not None:
            rewards.append(reward)
    return rewards


__all__ = [
    "RewardKind",
    "StoryReward",
    "apply_event_rewards",
    "load_rewards_from",
]
