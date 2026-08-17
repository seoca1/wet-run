"""Status message types and styling (ADR-0047).

Categorizes messages by severity for better visual hierarchy:
    - INFO (default): neutral system messages
    - SUCCESS: positive events (data extracted, mission complete)
    - WARNING: soft alerts (low HP, partial success)
    - ERROR: failures (combat loss, action denied)
    - COMBAT: damage numbers, kill events
    - MOVEMENT: node transitions
    - DIALOG: narrative events (rare in game status)

Each message gets:
    - Icon prefix (▶ ★ ⚠ ✗ ⚔ →)
    - Color tint (cyan / green / yellow / red / orange / light blue)
    - Priority for sorting/decay
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import IntEnum


class MessageKind(IntEnum):
    """Message severity/kind, ordered for sorting (higher = more important)."""

    DEBUG = 0
    INFO = 10
    MOVEMENT = 15
    DIALOG = 18
    COMBAT = 20
    SUCCESS = 30
    WARNING = 40
    ERROR = 50


# Visual config per kind: (icon, foreground RGB, background RGB or None)
MESSAGE_STYLE: dict[MessageKind, tuple[str, tuple[int, int, int], tuple[int, int, int] | None]] = {
    MessageKind.DEBUG: ("·", (96, 96, 96), None),
    MessageKind.INFO: ("▸", (200, 200, 200), None),
    MessageKind.MOVEMENT: ("→", (160, 200, 255), None),
    MessageKind.DIALOG: ("❝", (220, 220, 180), None),
    MessageKind.COMBAT: ("⚔", (255, 180, 100), None),
    MessageKind.SUCCESS: ("✓", (100, 230, 130), None),
    MessageKind.WARNING: ("⚠", (255, 220, 100), (60, 50, 0)),
    MessageKind.ERROR: ("✗", (255, 100, 100), (60, 20, 20)),
}


@dataclass(slots=True)
class StatusMessage:
    """A categorized status message.

    Attributes:
        text: The message text (without icon prefix).
        kind: Message category (INFO, SUCCESS, WARNING, etc).
        timestamp: When the message was created (time.time()).
    """

    text: str
    kind: MessageKind = MessageKind.INFO
    timestamp: float = field(default_factory=time.time)

    @property
    def icon(self) -> str:
        """Return the single-character icon prefix for this message kind (e.g. '⚔' for COMBAT)."""
        return MESSAGE_STYLE[self.kind][0]

    @property
    def fg(self) -> tuple[int, int, int]:
        """Return the foreground (text) RGB color tuple for this message kind."""
        return MESSAGE_STYLE[self.kind][1]

    @property
    def bg(self) -> tuple[int, int, int] | None:
        """Return the optional background RGB color tuple, or None when no background highlight is used."""
        return MESSAGE_STYLE[self.kind][2]

    @property
    def prefix(self) -> str:
        """Format: 'icon text' (e.g. '✓ Data extracted')."""
        return f"{self.icon} {self.text}"

    @classmethod
    def from_legacy(cls, text: str) -> StatusMessage:
        """Convert legacy `>>> ACTION: ...` strings to typed messages.

        Heuristic detection based on text prefix:
            - 'WARNING:' / 'ERROR:' → WARNING / ERROR
            - 'SCAN:' / 'EXTRACT:' / 'Gained:' → SUCCESS
            - 'ENGAGE:' / 'JACK OUT:' / 'Stage complete' → SUCCESS or INFO
            - 'MOVE:' / 'Passed through' → MOVEMENT
            - 'ERROR:' → ERROR
            - otherwise INFO
        """
        # Strip multiple leading '>' chars and whitespace
        cleaned = text.lstrip("> ").lstrip("> ").lstrip("> ").strip()
        low = cleaned.lower()
        if low.startswith("warning"):
            kind = MessageKind.WARNING
        elif low.startswith("error"):
            kind = MessageKind.ERROR
        elif (
            low.startswith("scan:")
            or low.startswith("extract:")
            or "gained" in low
            or "retrieved" in low
        ):
            kind = MessageKind.SUCCESS
        elif low.startswith("move:") or "passed through" in low or "→" in text:
            kind = MessageKind.MOVEMENT
        elif low.startswith("engage:") or "jack out" in low or "stage complete" in low:
            kind = MessageKind.SUCCESS
        elif "damage" in low or "hit" in low or "combat" in low:
            kind = MessageKind.COMBAT
        else:
            kind = MessageKind.INFO
        return cls(text=cleaned, kind=kind)


# ============================================================================
# Parsing legacy status_messages list
# ============================================================================


def parse_legacy_messages(legacy: list[str], max_keep: int = 10) -> list[StatusMessage]:
    """Convert a list of `>>> text` strings or StatusMessage objects to typed StatusMessages.

    Keeps only the most recent ``max_keep`` messages (sorted newest-last).
    """
    msgs: list[StatusMessage] = []
    for s in legacy:
        if isinstance(s, StatusMessage):
            msgs.append(s)
        else:
            msgs.append(StatusMessage.from_legacy(s))
    if len(msgs) > max_keep:
        msgs = msgs[-max_keep:]
    return msgs


def render_message(
    console: tcod.console.Console,
    x: int,
    y: int,
    msg: StatusMessage,
    max_width: int,
) -> None:
    """Render a single message at (x, y) with icon + color + (optional) bg.

    Args:
        console: tcod console.
        x: Starting column.
        y: Row.
        msg: StatusMessage to render.
        max_width: Maximum characters to render.
    """
    text = msg.prefix
    if len(text) > max_width:
        text = text[: max_width - 1] + "…"
    if msg.bg is not None:
        # Render with background highlight (warning/error)
        for i, ch in enumerate(text):
            if x + i >= console.width:
                break
            console.print(x + i, y, ch, fg=msg.fg, bg=msg.bg)
    else:
        console.print(x, y, text, fg=msg.fg)


# Late import for type hints
import tcod.console  # noqa: E402  (placed here to avoid circular issues at import)
