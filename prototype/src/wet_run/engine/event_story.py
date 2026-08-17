"""Event Story System: cinematic scenes triggered by NPC actions.

Event stories are extended narrative moments that can occur:
- After specific NPC dialogue choices
- After defeating certain enemies
- At specific locations (matrix nodes)
- After story milestones

Each event features:
- Character art (large ASCII portrait)
- Multi-line dialogue
- Player choices (optional)
- Korean translations
- Rewards / consequences
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import AppState


class EventTrigger(StrEnum):
    """When an event story is triggered.

    Phase 6+ additions:
      - CHAPTER_COMPLETE: after a chapter arc finishes
      - VENDOR_UNLOCKED: a vendor/faction rep threshold reached
      - HUB_VISITED: every hub transition (replayable)
      - DIALOGUE_COMPLETED: after a dialogue tree finishes
    """

    NPC_CHOICE = "npc_choice"  # After a specific NPC choice
    NPC_GREETING = "npc_greeting"  # When meeting NPC first time
    COMBAT_END = "combat_end"  # After defeating an enemy
    NODE_ENTER = "node_enter"  # When entering a specific node
    STORY_MILESTONE = "story_milestone"  # After story progress
    CHAPTER_COMPLETE = "chapter_complete"  # After a chapter arc finishes
    VENDOR_UNLOCKED = "vendor_unlocked"  # Faction rep threshold → vendor access
    HUB_VISITED = "hub_visited"  # Every hub transition (replayable flavor)
    DIALOGUE_COMPLETED = "dialogue_completed"  # Dialogue tree finished


class CharacterMood(StrEnum):
    """Character emotional state (affects art)."""

    NEUTRAL = "neutral"
    HAPPY = "happy"
    ANGRY = "angry"
    SAD = "sad"
    MYSTERIOUS = "mysterious"
    DETERMINED = "determined"
    SCARED = "scared"
    WISE = "wise"


# ============================================================================
# Character Art (Large ASCII portraits)
# ============================================================================


@dataclass(frozen=True, slots=True)
class CharacterArt:
    """Large multi-line ASCII art of a character.

    Each line is one row. 20-30 lines typical for a full character.
    Use monospace characters and align columns.
    """

    character_id: str
    art_lines: tuple[str, ...]
    color_hint: tuple[int, int, int] = (200, 200, 200)
    width: int = 20
    height: int = 20

    def get_lines(self) -> tuple[str, ...]:
        """Return the raw art lines (no colors).

        Returns:
            The tuple of art lines in declared order.
        """
        return self.art_lines

    def get_colored_lines(self) -> list[tuple[str, tuple[int, int, int]]]:
        """Return lines with color hints for each character."""
        return [(line, self.color_hint) for line in self.art_lines]


# ============================================================================
# Event Story
# ============================================================================


@dataclass
class EventLine:
    """One line in an event story.

    Similar to cinematic StoryLine but with character art support.
    """

    speaker: str = ""  # Character name (for dialogue)
    speaker_ko: str = ""
    portrait: str = ""  # Small ASCII portrait (1-2 chars)
    text: str = ""  # English text
    text_ko: str = ""  # Korean text
    art: CharacterArt | None = None  # Large character art for this line
    # Effects
    effect: str = "none"  # none, glitch, type
    effect_intensity: float = 1.0
    # Dialogue choices
    choices: list[EventChoice] = field(default_factory=list)


@dataclass
class EventChoice:
    """A player choice in an event story."""

    key: str
    text: str
    text_ko: str = ""
    # What happens next
    next_line_index: int | None = None  # Specific line
    # Or trigger
    grants_item: str | None = None
    grants_credits: int = 0
    grants_xp: int = 0
    triggers_another_event: str | None = None


@dataclass
class EventStory:
    """A complete event story (cutscene with character art)."""

    id: str = ""
    title: str = ""
    title_ko: str = ""
    trigger: EventTrigger = EventTrigger.STORY_MILESTONE
    trigger_id: str = ""  # e.g., "npc_dixie_choice_3" or "combat_ice_victory"
    character_id: str = ""  # Main character
    description: str = ""
    description_ko: str = ""
    lines: list[EventLine] = field(default_factory=list)
    # Trigger conditions
    required_flag: str | None = None  # Story flag required
    set_flag: str | None = None  # Set this flag when shown
    # One-time only?
    one_time: bool = True

    def get_line(self, index: int) -> EventLine | None:
        """Return the line at ``index`` or ``None`` if out of range.

        Args:
            index: 0-based line index.

        Returns:
            The :class:`EventLine` at that position, or ``None`` when the
            index is negative or beyond the end of ``self.lines``.
        """
        if 0 <= index < len(self.lines):
            return self.lines[index]
        return None


@dataclass
class EventState:
    """Current state of event story playback."""

    event: EventStory
    current_line_index: int = 0
    finished: bool = False
    choice_index: int = 0
    reward_granted: dict[str, object] = field(default_factory=dict)


# ============================================================================
# Character Arts (Gibson-inspired cyberpunk characters)
# ============================================================================


THE_CASE_ART = CharacterArt(
    character_id="case",
    art_lines=(
        "       ╔══╗       ",
        "       ║██║       ",
        "      ╔╩══╩╗      ",
        "     ╔╝░░░░╚╗     ",
        "     ║░░██░░║     ",
        "     ║░░░░░░║     ",
        "     ╚══╦╦══╝     ",
        "    ╔══╩╩══╗      ",
        "   ╔╝░░██░░╚╗    ",
        "   ║░░░██░░░║    ",
        "   ║░░░░░░░░║    ",
        "   ╚══╦╦╦══╝     ",
        "     ║░║░║       ",
        "    ╔╩╗╔╩╗      ",
        "    ╚╦╝╚╦╝      ",
    ),
    color_hint=(200, 200, 255),
    width=15,
    height=15,
)

MOLLY_ART = CharacterArt(
    character_id="molly",
    art_lines=(
        "     ╔══╗╔══╗    ",
        "     ║██║║██║    ",
        "    ╔╩══╩══╩╗   ",
        "   ╔╝░▒▒▒▒▒░╚╗  ",
        "   ║░▒▓▓▓▓▒░║  ",
        "   ║░▒▓▓██▓▒░║  ",
        "   ║░▒▓░░░▓▒░║  ",
        "   ╚══╦╦╦╦══╝   ",
        "      ║░║       ",
        "     ╔╩╩╗      ",
        "    ╔╝░░╚╗     ",
        "    ║░░░║      ",
        "    ╚══╝      ",
    ),
    color_hint=(255, 100, 200),
    width=14,
    height=13,
)

DIXIE_ART = CharacterArt(
    character_id="dixie",
    art_lines=(
        "      ┌──┐      ",
        "      │██│      ",
        "     ┌┴──┴┐     ",
        "    ┌┘▓▓▓▓└┐    ",
        "    │▓██▓▓▓│    ",
        "    │▓░░▓▓▓│    ",
        "    └┐▓▓▓┌┘     ",
        "     │░░░│      ",
        "   ┌─┘░░└─┐     ",
        "   │░░░░░░│     ",
        "   │░░░░░░│     ",
        "   └──┬┬──┘     ",
        "      ││       ",
    ),
    color_hint=(100, 200, 255),
    width=12,
    height=13,
)

ARMITAGE_ART = CharacterArt(
    character_id="armitage",
    art_lines=(
        "    ╔══════╗    ",
        "    ║▓▓▓▓▓▓║    ",
        "   ╔╝▓▓██▓▓╚╗  ",
        "   ║▓▓▓░░▓▓▓║  ",
        "   ║▓▓▓░░▓▓▓║  ",
        "   ╚╗▓▓▓▓▓▓╔╝  ",
        "    ║▓▓▓▓▓▓║    ",
        "   ╔╩═╦╦╦═╩╗   ",
        "   ║▓▓▓▓▓▓▓║   ",
        "   ║▓░░░░░▓║   ",
        "   ╚══╦╦╦══╝   ",
        "     ║░║       ",
    ),
    color_hint=(180, 50, 50),
    width=14,
    height=12,
)

THE_FINN_ART = CharacterArt(
    character_id="finn",
    art_lines=(
        "      ┌──┐      ",
        "      │██│      ",
        "     ┌┴──┴┐     ",
        "    ┌┘▒▒▒▒└┐    ",
        "    │▒░░▒▒▒│    ",
        "    │▒░░▒▒▒│    ",
        "    └┐▒▒▒┌┘     ",
        "     │░░░│      ",
        "   ┌─┘██└─┐     ",
        "   │██░░██│     ",
        "   │██░░██│     ",
        "   └──┬┬──┘     ",
        "      ││       ",
    ),
    color_hint=(255, 215, 0),
    width=12,
    height=13,
)

ICE_GLYPH_ART = CharacterArt(
    character_id="ice",
    art_lines=(
        "   ╔════════╗  ",
        "   ║▓▓▓▓▓▓▓▓▓║  ",
        "   ║▓▓████▓▓▓║  ",
        "  ╔╝▓▓░░░░▓▓╚╗ ",
        "  ║▓▓▓▓░██░▓▓▓║ ",
        "  ║▓▓▓▓░░░░▓▓▓║ ",
        "  ╚╗▓▓▓░░░▓▓╔╝ ",
        "   ║▓▓▓▓▓▓▓▓▓║  ",
        "   ║▓▓░░██░░▓▓║  ",
        "   ╚═══╦╦═══╝  ",
        "       ║║       ",
        "       ║║       ",
    ),
    color_hint=(255, 0, 0),
    width=15,
    height=12,
)

CHIBACITY_ART = CharacterArt(
    character_id="chibacity",
    art_lines=(
        "  ▄▄▄▄▄▄▄▄▄▄▄▄  ",
        "  █              █  ",
        "  █  ▄▄      ▄▄  █  ",
        "  █  ██      ██  █  ",
        "  █  ██  ▄▄  ██  █  ",
        "  █      ██      █  ",
        "  █  ▄▄██▄▄▄▄    █  ",
        "  █  ██▄▄██      █  ",
        "  █    ▄▄██      █  ",
        "  █  ██  ▄▄      █  ",
        "  █      ██      █  ",
        "  █▄▄▄▄▄▄▄▄▄▄▄▄▄█  ",
    ),
    color_hint=(100, 255, 100),
    width=18,
    height=12,
)


# ============================================================================
# Predefined Event Stories
# ============================================================================


# === Dixie Encounter Event ===
DIXIE_ENCOUNTER = EventStory(
    id="event_dixie_encounter",
    title="The Flatline",
    title_ko="플랫라인",
    trigger=EventTrigger.NPC_GREETING,
    trigger_id="npc_dixie",
    character_id="dixie",
    description="Dixie Flatline's ghost offers you wisdom from beyond.",
    description_ko="딕시 플랫라인의 유령이 저승에서 지혜를 나눠준다.",
    lines=[
        EventLine(
            speaker="Dixie Flatline",
            speaker_ko="딕시 플랫라인",
            portrait="◇D◇",
            art=DIXIE_ART,
            text="I knew you'd come, kid. The Finn's runners always do.",
            text_ko="네가 올 줄 알았어, 꼬마야. 핀의 러너는 항상 그렇지.",
            effect="type",
        ),
        EventLine(
            speaker="Dixie Flatline",
            speaker_ko="딕시 플랫라인",
            portrait="◇D◇",
            art=DIXIE_ART,
            text="I died twelve years ago, but my code still walks these corridors.",
            text_ko="난 12년 전에 죽었지만, 내 코드는 아직 이 복도를 걸어.",
            effect="type",
        ),
        EventLine(
            speaker="",
            text="",
            text_ko="",
            art=DIXIE_ART,
        ),
        EventLine(
            speaker="Dixie Flatline",
            speaker_ko="딕시 플랫라인",
            portrait="◇D◇",
            art=DIXIE_ART,
            text="Three rules. Memorize them:",
            text_ko="세 가지 규칙. 기억해:",
            effect="type",
        ),
        EventLine(
            speaker="Dixie Flatline",
            speaker_ko="딕시 플랫라인",
            portrait="◇D◇",
            art=DIXIE_ART,
            text="One: The Matrix is consensual. The walls are real if you believe.",
            text_ko="하나: 매트릭스는 합의된 거야. 네가 믿으면 벽도 진짜야.",
            effect="type",
        ),
        EventLine(
            speaker="Dixie Flatline",
            speaker_ko="딕시 플랫라인",
            portrait="◇D◇",
            art=DIXIE_ART,
            text="Two: Black ICE doesn't negotiate. Run or burn.",
            text_ko="둘: 블랙 ICE는 협상 안 해. 도망치거나 타거나.",
            effect="type",
        ),
        EventLine(
            speaker="Dixie Flatline",
            speaker_ko="딕시 플랫라인",
            portrait="◇D◇",
            art=DIXIE_ART,
            text="Three: The data wants to be free. Let it.",
            text_ko="셋: 데이터는 자유로워지길 원해. 놔줘.",
            effect="type",
        ),
        EventLine(
            speaker="",
            text="",
            text_ko="",
            art=DIXIE_ART,
        ),
        EventLine(
            speaker="Dixie Flatline",
            speaker_ko="딕시 플랫라인",
            portrait="◇D◇",
            art=DIXIE_ART,
            text="Now go. The Finn's waiting, and time's a flat circle in here.",
            text_ko="이제 가. 핀이 기다리고 있고, 시간은 여기서 평평한 원이야.",
            effect="type",
        ),
    ],
    set_flag="met_dixie",
    one_time=True,
)


# === Finn's Office Event (after mission) ===
FINN_AFTER_JACK = EventStory(
    id="event_finn_after_jack",
    title="The Finn's Office",
    title_ko="핀의 사무실",
    trigger=EventTrigger.COMBAT_END,
    trigger_id="first_jack_victory",
    character_id="finn",
    description="The Finn acknowledges your successful run.",
    description_ko="핀이 성공적인 런을 인정한다.",
    lines=[
        EventLine(
            speaker="The Finn",
            speaker_ko="핀",
            portrait="♠F♠",
            art=THE_FINN_ART,
            text="You made it back. Good.",
            text_ko="돌아왔군. 좋아.",
            effect="type",
        ),
        EventLine(
            speaker="The Finn",
            speaker_ko="핀",
            portrait="♠F♠",
            art=THE_FINN_ART,
            text="The data's clean. Sense/Net won't know what hit 'em.",
            text_ko="데이터는 깨끗해. 센스/넷은 뭘 맞았는지 모를 거야.",
            effect="type",
        ),
        EventLine(
            speaker="",
            text="",
            text_ko="",
            art=THE_FINN_ART,
        ),
        EventLine(
            speaker="The Finn",
            speaker_ko="핀",
            portrait="♠F♠",
            art=THE_FINN_ART,
            text="Credits transferred. Five hundred, as agreed.",
            text_ko="크레딧 이체 완료. 합의대로 500.",
            effect="type",
        ),
        EventLine(
            speaker="The Finn",
            speaker_ko="핀",
            portrait="♠F♠",
            art=THE_FINN_ART,
            text="You'll hear from me again, runner.",
            text_ko="또 연락이 갈 거야, 러너.",
            effect="type",
        ),
    ],
    set_flag="completed_first_jack",
    one_time=True,
)


# === Chiba City Establishing Shot (on entry) ===
CHIBA_CITY_INTRO = EventStory(
    id="event_chiba_intro",
    title="Chiba City at Night",
    title_ko="치바 시티의 밤",
    trigger=EventTrigger.NODE_ENTER,
    trigger_id="entry",
    character_id="chibacity",
    description="The sprawl at night. Neon. Rain. The Matrix awaits.",
    description_ko="스프롤의 밤. 네온. 비. 매트릭스가 기다린다.",
    lines=[
        EventLine(
            speaker="",
            text="",
            text_ko="",
            art=CHIBACITY_ART,
        ),
        EventLine(
            speaker="",
            text="The sky above the port was the color of television,",
            text_ko="항구 위의 하늘은 텔레비전의 색깔이었고,",
            effect="type",
        ),
        EventLine(
            speaker="",
            text="tuned to a dead channel.",
            text_ko="죽은 채널에 맞춰져 있었다.",
            effect="type",
        ),
        EventLine(
            speaker="",
            text="",
            text_ko="",
            art=CHIBACITY_ART,
        ),
        EventLine(
            speaker="",
            text="Chiba City. Night City. You know the streets",
            text_ko="치바 시티. 나이트 시티. 거리 구석구석을",
            effect="type",
        ),
        EventLine(
            speaker="",
            text="like the back of your hand.",
            text_ko="손금보듯 알고 있다.",
            effect="type",
        ),
        EventLine(
            speaker="",
            text="",
            text_ko="",
            art=CHIBACITY_ART,
        ),
        EventLine(
            speaker="",
            text="The Matrix is waiting...",
            text_ko="매트릭스가 기다리고 있다...",
            effect="glitch",
            effect_intensity=1.5,
        ),
    ],
    set_flag="entered_chiba",
    one_time=True,
)


# === ICE Combat Victory Event ===
ICE_VICTORY = EventStory(
    id="event_ice_victory",
    title="ICE Broken",
    title_ko="ICE 격파",
    trigger=EventTrigger.COMBAT_END,
    trigger_id="standard_ice_victory",
    character_id="ice",
    description="The ICE falls. The data is yours.",
    description_ko="ICE가 무너졌다. 데이터는 너의 것이다.",
    lines=[
        EventLine(
            speaker="",
            text="",
            text_ko="",
            art=ICE_GLYPH_ART,
        ),
        EventLine(
            speaker="",
            text="The ICE shatters into fragments of light...",
            text_ko="ICE가 빛의 파편으로 부서진다...",
            effect="glitch",
            effect_intensity=2.0,
        ),
        EventLine(
            speaker="",
            text="",
            text_ko="",
            art=ICE_GLYPH_ART,
        ),
        EventLine(
            speaker="",
            text="Data fragments scatter. The path is clear.",
            text_ko="데이터 파편이 흩어진다. 길이 열렸다.",
            effect="type",
        ),
        EventLine(
            speaker="",
            text="",
            text_ko="",
            art=ICE_GLYPH_ART,
        ),
        EventLine(
            speaker="",
            text="You gather what you can:",
            text_ko="주울 수 있는 것을 모은다:",
            effect="type",
        ),
    ],
    one_time=False,
)


# ============================================================================
# Event Registry
# ============================================================================


class EventRegistry:
    """Registry of event stories and triggers."""

    def __init__(self) -> None:
        """Initialize an empty registry and auto-load the default event set."""
        self._events: dict[str, EventStory] = {}
        # Auto-load default events
        for event in self._default_events():
            self._events[event.id] = event

    def _default_events(self) -> list[EventStory]:
        """Return the built-in event stories that every fresh registry starts with.

        Returns:
            The curated default event list (Dixie, Finn, Chiba City, ICE victory, …).
        """
        return [
            DIXIE_ENCOUNTER,
            FINN_AFTER_JACK,
            CHIBA_CITY_INTRO,
            ICE_VICTORY,
        ]

    def get(self, event_id: str) -> EventStory | None:
        """Look up an event story by its id.

        Args:
            event_id: The event's unique id (e.g. ``"dixie_encounter"``).

        Returns:
            The matching :class:`EventStory` or ``None`` if not registered.
        """
        return self._events.get(event_id)

    def get_by_trigger(self, trigger: EventTrigger, trigger_id: str) -> EventStory | None:
        """Find an event matching trigger."""
        for event in self._events.values():
            if event.trigger == trigger and event.trigger_id == trigger_id:
                return event
        return None

    def all(self) -> list[EventStory]:
        """Return every registered event story.

        Returns:
            A fresh list of all :class:`EventStory` values in insertion order.
        """
        return list(self._events.values())


def check_event_trigger(
    state: AppState,
    trigger: EventTrigger,
    trigger_id: str,
    registry: EventRegistry,
) -> EventStory | None:
    """Check if an event should fire and hasn't been shown yet.

    Returns the event if it should fire, None otherwise.
    """
    if not hasattr(state, "shown_events"):
        state.shown_events = set()

    event = registry.get_by_trigger(trigger, trigger_id)
    if event is None:
        return None

    # Check one-time constraint
    if event.one_time and event.id in state.shown_events:
        return None

    # Check required flag
    if event.required_flag is not None:
        flags: set[str] = getattr(state, "story_flags", set())
        if event.required_flag not in flags:
            return None

    # Check if story already started
    if hasattr(state, "active_event") and state.active_event is not None:
        return None

    return event
