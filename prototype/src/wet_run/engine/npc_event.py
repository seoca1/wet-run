"""NPC event system: dialogue trees and encounters.

Provides structured NPC interactions with dialogue lines and player choices.

Phase 6+ faction-aware dialogue: choices can carry a
``faction_gate`` (Faction) + ``min_tier`` (str) that restricts when
they are visible. The view layer in :mod:`engine.npc_view` filters
choices that don't match the current player's reputation state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..matrix.node import Faction
    from ..run.reputation import ReputationState


# Tier names used by the faction_gate (matches reputation_tier()).
_VALID_TIERS: frozenset[str] = frozenset(
    {"ALLIED", "FRIENDLY", "TRUSTED", "NEUTRAL", "HOSTILE", "ENEMY", "OUTCAST"}
)

# Re-export the matrix Faction for the gate field (avoid circular
# import — dialogue modules only need the type at annotation time).
from ..matrix.node import Faction as Faction  # noqa: E402, F811


class NPCId(StrEnum):
    """Known NPCs in the Sprawl."""

    DIXIE_FLATLINE = "dixie_flatline"
    FINN = "finn"
    ARMITAGE = "armitage"
    MOLLY = "molly"


class ChoiceEffect(StrEnum):
    """Effects of player choices."""

    GIVE_ITEM = "give_item"  # Player receives an item
    TAKE_DAMAGE = "take_damage"  # Player loses HP
    GAIN_INFO = "gain_info"  # Player learns something
    COMBAT = "combat"  # Triggers combat
    GOODBYE = "goodbye"  # Ends conversation
    CONTINUE = "continue"  # Continues to next dialogue


@dataclass
class DialogueChoice:
    """A player choice in dialogue.

    Phase 6+ adds faction-aware gating:
      - ``faction_gate`` (Faction or None): choice is only visible
        when the player has a non-None reputation with this faction
        AND the reputation tier is in the desired direction.
      - ``min_tier`` (str or None): minimum tier required.
        For positive tiers (ALLIED, FRIENDLY, TRUSTED, NEUTRAL) the
        current tier must be **at or above** the required rank
        (i.e. the player is friendly or better).
        For negative tiers (HOSTILE, ENEMY, OUTCAST) the current
        tier must be **at or below** the required rank (i.e. the
        player is hostile or worse — used for dark-plot options).

    Example::

        DialogueChoice(
            key="1",
            text="Mention that Hosaka has your back.",
            text_ko="호사카가 자네 편이라고 말해.",
            faction_gate=Faction.HOSAKA,
            min_tier="FRIENDLY",
        )
    """

    key: str  # 1, 2, 3... or letter
    text: str  # English text
    text_ko: str = ""  # Korean translation
    effect: ChoiceEffect = ChoiceEffect.CONTINUE
    effect_data: dict[str, str] = field(default_factory=dict)
    # Optional: what response the NPC gives after this choice
    response: str = ""
    response_ko: str = ""  # Korean response
    # What message to log in status
    log_message: str = ""
    # Faction-aware gating (Phase 6+).
    faction_gate: Faction | None = None
    min_tier: str | None = None

    def is_available(self, reputation: ReputationState | None) -> bool:
        """Return True if this choice is visible to the player.

        A choice without ``faction_gate`` is always available. A
        gated choice is only available when the player's reputation
        with the configured faction is at or beyond the required
        tier (see class docstring for the directional rule).
        """
        if self.faction_gate is None:
            return True
        if reputation is None:
            # Legacy save (no .reputation). Be conservative: show the
            # choice but flag via default tier neutral.
            return True
        # Lazy import to avoid circular dependency.
        from ..run.reputation import reputation_tier

        score = reputation.get(self.faction_gate).score
        current_tier = reputation_tier(score)
        return _evaluate_faction_gate(current_tier, self.min_tier)


def _evaluate_faction_gate(current_tier: str, min_tier: str | None) -> bool:
    """Return True if the player's tier satisfies the required tier.

    Direction matches :func:`npc_greeting.matches`:
      - Positive tiers (ALLIED, FRIENDLY, TRUSTED, NEUTRAL) trigger
        when current rank ≤ required rank.
      - Negative tiers (HOSTILE, ENEMY, OUTCAST) trigger when
        current rank ≥ required rank.
    """
    if min_tier is None:
        return True
    _rank = {
        "ALLIED": 0,
        "FRIENDLY": 1,
        "TRUSTED": 2,
        "NEUTRAL": 3,
        "HOSTILE": 4,
        "ENEMY": 5,
        "OUTCAST": 6,
    }
    if min_tier not in _rank or current_tier not in _rank:
        return True
    required = _rank[min_tier]
    current = _rank[current_tier]
    if required <= 3:  # positive half
        return current <= required
    return current >= required


@dataclass
class DialogueLine:
    """One line of NPC dialogue."""

    speaker: str = ""  # NPC name
    speaker_ko: str = ""  # Korean name
    text: str = ""  # What they say (English)
    text_ko: str = ""  # Korean translation (optional)
    portrait: str = ""  # ASCII portrait (optional)
    # Choices (if empty, any key advances to next_line_index)
    choices: list[DialogueChoice] = field(default_factory=list)
    # Index of next line if no choices
    next_line_index: int | None = None


@dataclass
class NPCEvent:
    """A complete NPC encounter with multiple dialogue lines."""

    id: str
    npc_name: str
    npc_name_ko: str = ""
    npc_portrait: str = ""
    description: str = ""
    description_ko: str = ""
    lines: list[DialogueLine] = field(default_factory=list)

    def get_line(self, index: int) -> DialogueLine | None:
        """Get dialogue line by index."""
        if 0 <= index < len(self.lines):
            return self.lines[index]
        return None


@dataclass
class NPCState:
    """Current state of an NPC encounter."""

    event: NPCEvent
    current_line_index: int = 0
    finished: bool = False
    result_data: dict[str, str] = field(default_factory=dict)


# ============================================================================
# Predefined NPC Events
# ============================================================================

DIXIE_FLATLINE_EVENT = NPCEvent(
    id="npc_dixie",
    npc_name="Dixie Flatline",
    npc_name_ko="딕시 플랫라인",
    npc_portrait="◇D◇",
    description="The construct of McCoy Pauley",
    description_ko="맥코이 폴리의 구성체",
    lines=[
        DialogueLine(
            speaker="Dixie Flatline",
            speaker_ko="딕시 플랫라인",
            text="Heh. You don't look like a regular jacker. The Finn send you?",
            text_ko="흐흐. 넌 보통 잭커처럼 안 보이는데. 핀이 보냈나?",
            portrait="◇D◇",
            choices=[
                DialogueChoice(
                    key="1",
                    text="Yeah, I'm on a job. Just passing through.",
                    text_ko="응, 일 보러 왔어. 그냥 지나가는 길이야.",
                    effect=ChoiceEffect.GAIN_INFO,
                    log_message="Dixie nods knowingly.",
                ),
                DialogueChoice(
                    key="2",
                    text="Who wants to know?",
                    text_ko="누가 궁금한데?",
                    effect=ChoiceEffect.CONTINUE,
                    response="Me? I'm the ghost in the machine, kid. Dixie Flatline. McCoy Pauley's construct.",
                    response_ko="나? 기계 속 유령이야, 꼬마야. 딕시 플랫라인. 맥코이 폴리의 구성체.",
                ),
                DialogueChoice(
                    key="3",
                    text="Got any advice for navigating this grid?",
                    text_ko="이 그리드 헤쳐나갈 조언이라도?",
                    effect=ChoiceEffect.GAIN_INFO,
                    effect_data={"info": "The ICE blocks the direct path. Find another way."},
                    log_message="Dixie shares tactical info.",
                ),
                # Phase 6+ faction-gated choice: only visible to players
                # who are FRIENDLY or better with Hosaka. Dixie remembers
                # the data they stole for Hosaka and will share it.
                DialogueChoice(
                    key="4",
                    text="I work for Hosaka. We have history.",
                    text_ko="나는 호사카 일해. 우리 사이에 역사 있어.",
                    effect=ChoiceEffect.GAIN_INFO,
                    effect_data={
                        "info": "Hosaka's runs are clean. T-A's are dirty. The difference is who paid first."
                    },
                    response="Oh. Then you already know the game. Hosaka's data is on the second ICE — T-A's on the third. Take your pick.",
                    response_ko="오. 그러면 너는 이미 게임을 알고 있군. 호사카 데이터는 두 번째 ICE에 — T-A는 세 번째. 골라.",
                    log_message="Dixie shares intel — faction-aware branch.",
                    faction_gate=Faction.HOSAKA,
                    min_tier="FRIENDLY",
                ),
                # Dark-plot choice: only visible to players who are
                # HOSTILE or worse with T-A. Dixie reveals the dark side.
                DialogueChoice(
                    key="5",
                    text="I'm here to burn T-A's data.",
                    text_ko="T-A 데이터 태우러 왔어.",
                    effect=ChoiceEffect.GAIN_INFO,
                    effect_data={
                        "info": "T-A ICE will self-destruct. The data's on the second node — not the third. Don't go to the third."
                    },
                    response="Heh. Good. Hit the second node hard — the third is a trap. T-A put a black ICE in the core to catch runners like you.",
                    response_ko="흐흐. 좋아. 두 번째 노드 강하게 쳐 — 세 번째는 함정이다. T-A가 너 같은 러너를 잡으려고 코어에 블랙 ICE를 심어놨어.",
                    log_message="Dixie reveals a dark path — anti-T-A branch.",
                    faction_gate=Faction.TA,
                    min_tier="HOSTILE",
                ),
            ],
        ),
        DialogueLine(
            speaker="Dixie Flatline",
            speaker_ko="딕시 플랫라인",
            text="Look, kid. The ICE ahead is standard-grade, but it's hungry. Watch your AP. And if you see a black box... run.",
            text_ko="봐라, 꼬마야. 앞의 ICE는 표준 등급이지만 배가 고프다. AP를 잘 살펴. 그리고 검은 상자를 보면... 도망쳐.",
            portrait="◇D◇",
            choices=[
                DialogueChoice(
                    key="1",
                    text="Thanks for the tip. I'm out.",
                    text_ko="고마워. 나 간다.",
                    effect=ChoiceEffect.GOODBYE,
                    log_message="You part ways with Dixie.",
                ),
                DialogueChoice(
                    key="2",
                    text="What do you know about the data I'm after?",
                    text_ko="내가 찾는 데이터에 대해 뭘 알아?",
                    effect=ChoiceEffect.GAIN_INFO,
                    effect_data={
                        "info": "Sense/Net's demo file. Worth more than they're paying you, I'd bet."
                    },
                    log_message="Dixie shares a knowing look.",
                ),
                DialogueChoice(
                    key="3",
                    text="Need any help? I'm decent with a deck.",
                    text_ko="도움이 필요해? 나 덱 좀 만져.",
                    effect=ChoiceEffect.GAIN_INFO,
                    effect_data={
                        "info": "I've got a job for a runner like you, but not today. Come back when you're ready."
                    },
                    log_message="Dixie considers your offer.",
                ),
                DialogueChoice(
                    key="4",
                    text="Tell me about the Matrix.",
                    text_ko="매트릭스에 대해 알려줘.",
                    effect=ChoiceEffect.GAIN_INFO,
                    effect_data={
                        "info": "It's a consensual hallucination. The Sprawl's nervous system. Don't get lost in it."
                    },
                    log_message="Dixie waxes philosophical.",
                ),
            ],
        ),
        DialogueLine(
            speaker="Dixie Flatline",
            speaker_ko="딕시 플랫라인",
            text="One more thing, runner. There's a side room with some salvage. Take what's useful.",
            text_ko="하나만 더, 러너야. 옆에 Salvage가 있는 방이 있어. 필요한 거 챙겨.",
            portrait="◇D◇",
            choices=[
                DialogueChoice(
                    key="1",
                    text="I appreciate the help.",
                    text_ko="도움 고마워.",
                    effect=ChoiceEffect.GOODBYE,
                    log_message="You thank Dixie and move on.",
                ),
                DialogueChoice(
                    key="2",
                    text="Anything I should know about the ICE?",
                    text_ko="ICE에 대해 알아야 할 것 있어?",
                    effect=ChoiceEffect.GAIN_INFO,
                    effect_data={
                        "info": "Use your skills wisely. ICE BREAKER is powerful but has a cooldown."
                    },
                    log_message="Dixie offers tactical advice.",
                ),
            ],
        ),
    ],
)
