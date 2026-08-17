"""Faction reputation system.

자키의 5개 faction 별 평판을 추적. Pillar 4 (The Build) 의
확장 — 같은 미션도 faction 호감도에 따라 다른 의뢰인, 보상,
엔딩 가능.

Faction 호감도 조정:
  - 미션 완료 (+mission rep depending on objective)
  - ICE 처치 (+faction whose server you hit)
  - 의뢰인 선택 (+fixer rep)
  - 엔딩 선택 (+faction tied to ending)

영향:
  - 사용 가능한 미션 필터링 (rep_threshold 메타)
  - Info Market 가격 할인 (-rep × 5%)
  - NPC 반응 (rep 높으면 다른 dialogue)
  - Hub 시각 표시 (5 dots)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..matrix.node import Faction

# ============================================================================
# Constants
# ============================================================================


# Default reputation for new runs (neutral).
DEFAULT_REPUTATION = 0

# Reputation thresholds for tier labels.
TIER_THRESHOLDS: list[tuple[int, str]] = [
    (80, "ALLIED"),
    (50, "FRIENDLY"),
    (20, "TRUSTED"),
    (-20, "NEUTRAL"),
    (-50, "HOSTILE"),
    (-80, "ENEMY"),
]
TIER_DEFAULT = "NEUTRAL"


def reputation_tier(rep: int) -> str:
    """Map a reputation score to its tier label.

    Args:
        rep: Reputation score (any int, typically -100..+100).

    Returns:
        Tier label string (ALLIED, FRIENDLY, TRUSTED, NEUTRAL,
        HOSTILE, ENEMY, or OUTCAST for very low rep).
    """
    if rep >= 80:
        return "ALLIED"
    if rep >= 50:
        return "FRIENDLY"
    if rep >= 20:
        return "TRUSTED"
    if rep > -20:
        return "NEUTRAL"
    if rep > -50:
        return "HOSTILE"
    if rep > -80:
        return "ENEMY"
    return "OUTCAST"


# Maximum reputation delta per single event. Prevents single missions
# from swinging the player's standing too dramatically.
MAX_DELTA_PER_EVENT = 25


def clamp_delta(delta: int) -> int:
    """Clamp a single delta to MAX_DELTA_PER_EVENT."""
    return max(-MAX_DELTA_PER_EVENT, min(MAX_DELTA_PER_EVENT, delta))


# ============================================================================
# Reputation state
# ============================================================================


@dataclass
class FactionReputation:
    """Player reputation with one specific faction.

    Attributes:
        faction: Which faction this reputation tracks.
        score: Current reputation score (-100..+100 typical).
        history: Recent deltas with source descriptions, newest first.
            Capped at 20 entries to prevent unbounded growth.
    """

    faction: Faction
    score: int = DEFAULT_REPUTATION
    history: list[tuple[int, str]] = field(default_factory=list)

    HISTORY_MAX = 20

    def adjust(self, delta: int, source: str = "") -> None:
        """Adjust reputation by ``delta`` (clamped), record source.

        Args:
            delta: Raw reputation change (positive = better, negative = worse).
            source: Short description of what caused the change
                (e.g. "mission:ta_heist", "combat:black_ice").
        """
        clamped = clamp_delta(delta)
        self.score += clamped
        self.history.insert(0, (clamped, source))
        if len(self.history) > self.HISTORY_MAX:
            self.history = self.history[: self.HISTORY_MAX]

    def tier(self) -> str:
        """Return current reputation tier label."""
        return reputation_tier(self.score)


# ============================================================================
# Reputation collection (all factions at once)
# ============================================================================


@dataclass
class ReputationState:
    """Player reputation across all 5 factions.

    Each faction has its own FactionReputation (lazily created on
    first access via ``get``).
    """

    _reputations: dict[Faction, FactionReputation] = field(default_factory=dict)

    def get(self, faction: Faction) -> FactionReputation:
        """Return the FactionReputation for ``faction``, creating if absent."""
        if faction not in self._reputations:
            self._reputations[faction] = FactionReputation(faction=faction)
        return self._reputations[faction]

    def adjust(self, faction: Faction, delta: int, source: str = "") -> None:
        """Adjust the given faction's reputation by ``delta``."""
        self.get(faction).adjust(delta, source)

    def all_factions(self) -> list[Faction]:
        """Return factions the player has any interaction with."""
        return list(self._reputations.keys())

    def total_score(self) -> int:
        """Sum of reputation scores across all known factions."""
        return sum(r.score for r in self._reputations.values())

    def to_dict(self) -> dict[str, object]:
        """Serialize for save/restore."""
        return {
            "reputations": {
                f.value: {"score": r.score, "history": list(r.history)}
                for f, r in self._reputations.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ReputationState:
        """Restore from a dict produced by ``to_dict``.

        Defensive against malformed inputs: returns an empty state if
        ``data`` is not a dict or has no ``reputations`` key.
        """
        if not isinstance(data, dict):
            return cls()
        rep_data = data.get("reputations", {})
        if not isinstance(rep_data, dict):
            return cls()
        state = cls()
        for faction_value, payload in rep_data.items():
            try:
                faction = Faction(faction_value)
            except ValueError:
                continue  # Unknown faction — skip
            if not isinstance(payload, dict):
                continue
            raw_score = payload.get("score", 0)
            try:
                score = int(raw_score)
            except (TypeError, ValueError):
                score = 0
            raw_history = payload.get("history", [])
            history: list[tuple[int, str]] = []
            if isinstance(raw_history, list):
                for entry in raw_history[-cls.get_history_max() :]:
                    if isinstance(entry, (list, tuple)) and len(entry) == 2:
                        try:
                            delta = int(entry[0])
                            src = str(entry[1])
                            history.append((delta, src))
                        except (TypeError, ValueError):
                            continue
            rep = FactionReputation(faction=faction, score=score, history=history)
            state._reputations[faction] = rep
        return state

    @staticmethod
    def get_history_max() -> int:
        """Return the max history size (mirrors FactionReputation.HISTORY_MAX)."""
        return FactionReputation.HISTORY_MAX


__all__ = [
    "DEFAULT_REPUTATION",
    "FactionReputation",
    "MAX_DELTA_PER_EVENT",
    "ReputationState",
    "TIER_THRESHOLDS",
    "clamp_delta",
    "reputation_tier",
]
