"""NPC faction-aware greeting system.

When the player meets an NPC, the greeting line is chosen based on
the player's faction reputation. Higher rep with a faction → NPC
references that faction positively; hostile rep → NPC warns the player.

Each NPC has a list of :class:`ReputationGreeting` rules. The first
matching rule wins. If no faction rule matches, the **default**
greeting (faction=None, min_tier=None) is used.

This makes the faction reputation system tangible in the game's
narrative loop without requiring a full branching dialogue system.

Example::

    >>> from wet_run.engine.npc_greeting import get_greeting
    >>> greeting = get_greeting("finn", state)
    >>> greeting.line_en
    'Welcome to the Sprawl, cowboy.'
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..matrix.node import Faction
from ..run.reputation import reputation_tier

if TYPE_CHECKING:
    from .state import AppState


# Tier names mapped to numeric ranks where 0 = best and 6 = worst.
# "min_tier='FRIENDLY'" means "trigger when player's standing is at
# least FRIENDLY", i.e. rank <= 1. "min_tier='HOSTILE'" means
# "trigger when player is at least HOSTILE" (the faction dislikes
# them), i.e. rank <= 4 (HOSTILE, ENEMY, OUTCAST all qualify).
_TIER_RANK: dict[str, int] = {
    "ALLIED": 0,
    "FRIENDLY": 1,
    "TRUSTED": 2,
    "NEUTRAL": 3,
    "HOSTILE": 4,
    "ENEMY": 5,
    "OUTCAST": 6,
}


@dataclass(frozen=True, slots=True)
class ReputationGreeting:
    """A single reputation-conditioned NPC greeting.

    Attributes:
        npc_id: Which NPC this greeting belongs to.
        faction: Faction to check reputation against, or None for
            the default fallback.
        min_tier: Minimum tier required to use this greeting (one of
            OUTCAST / ENEMY / HOSTILE / NEUTRAL / TRUSTED / FRIENDLY /
            ALLIED), or None for the default.
        line_en: English greeting text.
        line_ko: Korean greeting text (optional).
    """

    npc_id: str
    faction: Faction | None
    min_tier: str | None
    line_en: str
    line_ko: str = ""

    def matches(self, faction_reputation: dict[Faction, int]) -> bool:
        """Return True if this greeting's condition is satisfied.

        The default greeting (faction=None, min_tier=None) matches
        only when no other rule has matched — see :func:`get_greeting`.

        Tier rank: 0 = ALLIED (best), 6 = OUTCAST (worst). The match
        direction depends on which half of the spectrum ``min_tier``
        lives in:
          - Positive half (ALLIED/FRIENDLY/TRUSTED/NEUTRAL): trigger
            when current rank ≤ required rank (i.e. standing is at
            least as good as the required tier).
          - Negative half (HOSTILE/ENEMY/OUTCAST): trigger when
            current rank ≥ required rank (i.e. standing is at least
            as bad as the required tier).
        """
        if self.faction is None or self.min_tier is None:
            return False  # default — handled by caller
        score = faction_reputation.get(self.faction, 0)
        current_tier = reputation_tier(score)
        current_rank = _TIER_RANK.get(current_tier, 3)
        required_rank = _TIER_RANK.get(self.min_tier, 3)
        # Positive tiers (0..3): player must be ≥ required (lower rank = better)
        # Negative tiers (4..6): player must be ≤ required (higher rank = worse)
        if required_rank <= 3:  # ALLIED, FRIENDLY, TRUSTED, NEUTRAL
            return current_rank <= required_rank
        else:  # HOSTILE, ENEMY, OUTCAST
            return current_rank >= required_rank


# Per-NPC greeting table. Order matters: first matching rule wins.
# The very last entry for each NPC must be the default (faction=None,
# min_tier=None) which always matches if no other rule does.
NPC_GREETINGS: dict[str, list[ReputationGreeting]] = {
    "finn": [
        # Friendly to one of his major clients
        ReputationGreeting(
            npc_id="finn",
            faction=Faction.HOSAKA,
            min_tier="FRIENDLY",
            line_en="Hosaka's been asking about you, cowboy. Good work.",
            line_ko="호사카가 자네에 대해 물어보고 있었네, 카우보이. 잘하고 있어.",
        ),
        ReputationGreeting(
            npc_id="finn",
            faction=Faction.SENSE_NET,
            min_tier="FRIENDLY",
            line_en="Sense/Net cleared you through. Smart move.",
            line_ko="센스넷이 통과시켰네. 똑똑하군.",
        ),
        # Hostile
        ReputationGreeting(
            npc_id="finn",
            faction=Faction.MAAS,
            min_tier="HOSTILE",
            line_en="Maas wants you dead, cowboy. Watch your back out there.",
            line_ko="마스가 자네를 죽이려 하네, 카우보이. 밖에서 조심하게.",
        ),
        # Default
        ReputationGreeting(
            npc_id="finn",
            faction=None,
            min_tier=None,
            line_en="Welcome to the Sprawl, cowboy. Got a job for you?",
            line_ko="스프롤에 온 걸 환영해, 카우보이. 작업 하나 있나?",
        ),
    ],
    "dixie": [
        ReputationGreeting(
            npc_id="dixie",
            faction=Faction.TA,
            min_tier="HOSTILE",
            line_en="Heh. Tessier-Ashpool's been sending ICE after you. Stay sharp.",
            line_ko="흐흐. 테시에-애스풀이 자네한테 ICE를 보내고 있어. 조심해.",
        ),
        ReputationGreeting(
            npc_id="dixie",
            faction=Faction.HOSAKA,
            min_tier="FRIENDLY",
            line_en="Hosaka pays well. Their money keeps me alive. Do right by them.",
            line_ko="호사카는 돈을 잘 써. 그 돈이 날 살려줘. 그쪽 일을 잘 해.",
        ),
        ReputationGreeting(
            npc_id="dixie",
            faction=None,
            min_tier=None,
            line_en="Heh. Back again, kid. What's the play?",
            line_ko="흐흐. 또 왔네, 꼬마. 무슨 작전?",
        ),
    ],
    "maelcum": [
        ReputationGreeting(
            npc_id="maelcum",
            faction=Faction.TA,
            min_tier="FRIENDLY",
            line_en="Tessier-Ashpool trusts you. Zion hears good things.",
            line_ko="테시에-애스풀이 자네를 신뢰하네. 자이언도 좋은 소식을 들었어.",
        ),
        ReputationGreeting(
            npc_id="maelcum",
            faction=Faction.MAAS,
            min_tier="HOSTILE",
            line_en="Maas-folk smell like bad luck. Watch the airlock.",
            line_ko="마스 쪽 사람들은 불운 냄새가 나. 에어록 조심해.",
        ),
        ReputationGreeting(
            npc_id="maelcum",
            faction=None,
            min_tier=None,
            line_en="Breathe deep, runner. The Sprawl gets in your lungs either way.",
            line_ko="숨을 깊이 쉬어, 러너. 어차피 스프롤이 폐에 들어올 거야.",
        ),
    ],
    "bartender": [
        ReputationGreeting(
            npc_id="bartender",
            faction=Faction.SENSE_NET,
            min_tier="ALLIED",
            line_en="Sense/Net drinks for free in this bar. You too, friend.",
            line_ko="센스넷은 여기서 공짜야. 자네도 그래, 친구.",
        ),
        ReputationGreeting(
            npc_id="bartender",
            faction=Faction.MAAS,
            min_tier="HOSTILE",
            line_en="Maas? Bar's full. Try the Chiba entrance, runner.",
            line_ko="마스? 자리 없네. 치바 출입구로 가봐, 러너.",
        ),
        ReputationGreeting(
            npc_id="bartender",
            faction=None,
            min_tier=None,
            line_en="What'll it be, runner? Same as last time?",
            line_ko="뭘로 할래, 러너? 지난번처럼?",
        ),
    ],
    "ta_rep": [
        ReputationGreeting(
            npc_id="ta_rep",
            faction=Faction.TA,
            min_tier="ALLIED",
            line_en="Onikiri-sama speaks well of you. Continue.",
            line_ko="오니키리 님이 자네에 대해 칭찬하셨네. 계속해.",
        ),
        ReputationGreeting(
            npc_id="ta_rep",
            faction=Faction.MAAS,
            min_tier="HOSTILE",
            line_en="Maas. We have no business with Maas-folk. Leave.",
            line_ko="마스. 우리와 마스 쪽은 거래가 없네. 나가.",
        ),
        ReputationGreeting(
            npc_id="ta_rep",
            faction=None,
            min_tier=None,
            line_en="Tessier-Ashpool does not negotiate with strangers. State your business.",
            line_ko="테시에-애스풀은 낯선 자와 협상하지 않아. 용건을 말해.",
        ),
    ],
}


def get_greeting(npc_id: str, state: AppState) -> ReputationGreeting | None:
    """Return the best reputation-conditioned greeting for ``npc_id``.

    Selection algorithm:
      1. Iterate NPC_GREETINGS[npc_id] in declared order.
      2. First rule whose :meth:`ReputationGreeting.matches` returns True
         wins.
      3. If no rule matches, return the default (faction=None,
         min_tier=None) if present.
      4. If NPC has no greeting table, return None.

    Reputation is read from ``state.reputation`` (Phase 6+ system).
    For legacy states without a reputation field, this returns the
    default greeting.
    """
    rules = NPC_GREETINGS.get(npc_id)
    if rules is None:
        return None

    # Build faction → score map (lazy, only on demand).
    faction_reputation: dict[Faction, int] = {}
    # `getattr` covers missing attribute; explicit None check covers
    # legacy / stripped states where reputation was explicitly unset.
    rep = getattr(state, "reputation", None)
    if rep is not None:
        for faction in Faction:
            faction_reputation[faction] = rep.get(faction).score

    default: ReputationGreeting | None = None
    for rule in rules:
        if rule.faction is None and rule.min_tier is None:
            default = rule
            continue
        if rule.matches(faction_reputation):
            return rule
    return default


def get_greeting_text(npc_id: str, state: AppState, *, korean: bool = False) -> str:
    """Convenience: return the greeting line directly.

    Args:
        npc_id: NPC identifier (e.g. "finn", "dixie").
        state: App state (for reputation lookup).
        korean: If True, return Korean text (fallback to English if
            the Korean line is empty).

    Returns:
        The greeting line, or an empty string if no greeting is
        configured for the NPC.
    """
    greeting = get_greeting(npc_id, state)
    if greeting is None:
        return ""
    if korean and greeting.line_ko:
        return greeting.line_ko
    return greeting.line_en


__all__ = [
    "NPC_GREETINGS",
    "ReputationGreeting",
    "get_greeting",
    "get_greeting_text",
]
