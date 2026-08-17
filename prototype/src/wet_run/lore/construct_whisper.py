"""Construct Whisper system (ADR-0140 §Proposal 1).

Faction-aware construct hints during combat. When a faction's
reputation tier reaches TRUSTED or higher, that faction's construct
provides a one-time per-run tactical hint during combat.

Hints are triggered automatically when combat begins if the
player qualifies. Once a faction whispers, it won't whisper again
that run (per-run cap = 1 per faction, max 5 total = 1 per tier).

Grade 6 Master Whisper (ADR-0140 §Proposal 4):
When the player's equipment grade is >= 6 (master tier), the
construct's voice becomes more authoritative and reveals deeper
insight. Replaces the normal tier voice when applicable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..matrix.node import Faction
from ..run.reputation import ReputationState, reputation_tier

# Tier threshold for whisper unlock (per ADR-0140 proposal 1).
WHISPER_UNLOCK_TIER = "TRUSTED"

# Player grade threshold for master voice (ADR-0140 proposal 4).
MASTER_GRADE_THRESHOLD: int = 6

# Tier-specific hint text. Each faction has unique voice.
HINTS_BY_FACTION: dict[Faction, dict[str, str]] = {
    Faction.HOSAKA: {
        "TRUSTED": "Hosaka construct observes: 'Their ICE recognizes our signature. Strike first — they hesitate against familiar faces.'",
        "FRIENDLY": "Hosaka construct notes: 'Use the wardrone. Our servers respond to corporate protocols.'",
        "ALLIED": "Hosaka construct reveals: 'Black ICE has a backdoor. Exploit the timing window after their first volley.'",
    },
    Faction.MAAS: {
        "TRUSTED": "Maas construct whispers: 'Biochip signatures are tracked. Their ICE learns — vary your approach.'",
        "FRIENDLY": "Maas construct advises: 'Their construct is young. Confuse it with decoy programs.'",
        "ALLIED": "Maas construct reveals: 'They carry a countermeasure against standard virus. Use the rare program.'",
    },
    Faction.SENSE_NET: {
        "TRUSTED": "Sense/Net construct notes: 'Their system logs every move. Use the worm — it's noisier but unlogged.'",
        "FRIENDLY": "Sense/Net construct advises: 'Probe before engage. Information is ammunition.'",
        "ALLIED": "Sense/Net construct reveals: 'Their alarm threshold is set low. One quick strike bypasses it.'",
    },
    Faction.TA: {
        "TRUSTED": "T-A construct observes: 'The family keeps secrets in layers. Strike the surface — depth reveals itself.'",
        "FRIENDLY": "T-A construct advises: 'Their ICE is old. It hesitates at novel attack patterns.'",
        "ALLIED": "T-A construct reveals: 'The core ICE is bound by family protocol. Break the protocol first.'",
    },
}

# Master-tier hint text (ADR-0140 proposal 4). Used when player is
# at Grade 6+ equipment. More authoritative voice, deeper insight.
MASTER_HINTS_BY_FACTION: dict[Faction, str] = {
    Faction.HOSAKA: (
        "Hosaka master construct decrees: 'The runner who masters T6 has earned the deepest signal. "
        "Black ICE architecture: their daemon is single-threaded. Hit the wardrone to fork their "
        "thread pool — they will collapse at the transition window.'"
    ),
    Faction.MAAS: (
        "Maas master construct intones: 'A runner at master tier deserves the full picture. "
        "Biochip telemetry leaks through their construct — sample it before engage. "
        "Their ICE rewrites itself only at the 4th attack pattern. Strike 5th, and you control the field.'"
    ),
    Faction.SENSE_NET: (
        "Sense/Net master construct reveals: 'Master-tier eyes see what others cannot. "
        "Their alarm threshold is not a single value — it is a sigmoid. Two fast strikes will "
        "land below detection. The third will cascade the system. We have used this exact path before.'"
    ),
    Faction.TA: (
        "T-A master construct speaks: 'The family kept many secrets. Here is one. "
        "Their core ICE inherits the Tessier protocol — it will refuse to engage a runner carrying "
        "a wardrone signature we planted. The kill is in the equipment, not the program.'"
    ),
}


def get_hint_for_faction(faction: Faction, tier: str) -> str | None:
    """Get the hint text for a faction at a given tier.

    Args:
        faction: The faction whose construct should whisper.
        tier: The player's tier with that faction (e.g. "TRUSTED").

    Returns:
        Hint text if faction has hints at this tier, else None.
    """
    faction_hints = HINTS_BY_FACTION.get(faction)
    if not faction_hints:
        return None
    return faction_hints.get(tier)


def get_master_hint_for_faction(faction: Faction) -> str | None:
    """Get the master-tier hint text for a faction.

    Args:
        faction: The faction whose construct should whisper.

    Returns:
        Master-tier hint text if faction has a master hint, else None.
    """
    return MASTER_HINTS_BY_FACTION.get(faction)


def is_player_master(state: Any) -> bool:
    """Check if the player is at master equipment grade (>= 6).

    Args:
        state: AppState-like object with player_grade attribute.

    Returns:
        True if player_grade >= 6, else False.
    """
    return getattr(state, "player_grade", 0) >= MASTER_GRADE_THRESHOLD


@dataclass
class ConstructWhisper:
    """Per-run tracker for construct whispers.

    Tracks which factions have already whispered this run.
    Each faction can whisper at most once per run. Default cap is
    total factions (5), one per faction.

    Attributes:
        whispered_factions: Factions that have whispered this run.
        max_total: Max total whispers per run (default 5).
    """

    whispered_factions: set[Faction] = field(default_factory=set)
    max_total: int = 5

    @property
    def count(self) -> int:
        """Number of whispers delivered this run."""
        return len(self.whispered_factions)

    @property
    def remaining(self) -> int:
        """Remaining whispers allowed this run."""
        return max(0, self.max_total - self.count)

    def has_whispered(self, faction: Faction) -> bool:
        """Check if faction has already whispered this run."""
        return faction in self.whispered_factions

    def can_whisper(self, faction: Faction) -> bool:
        """Check if faction can still whisper this run."""
        if self.has_whispered(faction):
            return False
        return self.count < self.max_total

    def record_whisper(self, faction: Faction) -> bool:
        """Record that a faction has whispered this run.

        Args:
            faction: The faction that whispered.

        Returns:
            True if recorded, False if already whispered or cap reached.
        """
        if not self.can_whisper(faction):
            return False
        self.whispered_factions.add(faction)
        return True

    def reset(self) -> None:
        """Clear all whispers (call on new run)."""
        self.whispered_factions.clear()

    def find_eligible_factions(self, reputation: ReputationState) -> list[tuple[Faction, str]]:
        """Find factions eligible to whisper based on reputation.

        Args:
            reputation: Player's faction reputation state.

        Returns:
            List of (faction, tier) tuples for factions that can
            whisper and have reputation >= TRUSTED.
        """
        eligible: list[tuple[Faction, str]] = []
        for faction in Faction:
            if faction == Faction.NONE:
                continue
            if not self.can_whisper(faction):
                continue
            tier = reputation_tier(reputation.get(faction).score)
            tier_order = ["NEUTRAL", "HOSTILE", "ENEMY", "OUTCAST", "TRUSTED", "FRIENDLY", "ALLIED"]
            tier_index = tier_order.index(tier) if tier in tier_order else 0
            unlock_index = tier_order.index(WHISPER_UNLOCK_TIER)
            if tier_index < unlock_index:
                continue
            eligible.append((faction, tier))
        return eligible


__all__ = [
    "ConstructWhisper",
    "HINTS_BY_FACTION",
    "WHISPER_UNLOCK_TIER",
    "find_eligible_factions",
    "get_hint_for_faction",
]


# Re-export for convenience
find_eligible_factions = ConstructWhisper.find_eligible_factions
