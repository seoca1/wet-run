"""Jockey avatar renderer.

Maps AvatarState to ASCII art per ADR-0016 / design/systems/avatar.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tcod.console

from .state import (
    AvatarLines,
    AvatarState,
    ConstructKind,
    ProgramSlot,
    Status,
)

# --- Color palette ---

COL_HEAD_FULL = (0, 255, 0)  # Green
COL_HEAD_HIGH = (180, 255, 0)  # Yellow-green
COL_HEAD_MID = (255, 255, 0)  # Yellow
COL_HEAD_LOW = (255, 80, 0)  # Red
COL_HEAD_DEAD = (140, 0, 0)  # Dark red

COL_BODY_NORMAL = (200, 200, 200)
COL_BODY_LOW = (180, 100, 100)
COL_BODY_FUTILE = (120, 60, 60)

COL_PROG_T1 = (140, 140, 140)
COL_PROG_T2 = (180, 180, 180)
COL_PROG_T3 = (0, 200, 255)
COL_PROG_T4 = (200, 130, 255)
COL_PROG_T5 = (255, 200, 0)
COL_PROG_DEPLETED = (80, 80, 80)
COL_PROG_LOCKED = (60, 60, 60)

COL_DECK = (0, 255, 200)
COL_WETWARE = (0, 200, 100)

COL_CONSTRUCT = (255, 200, 100)
COL_CONSTRUCT_LOA = (180, 100, 255)
COL_CONSTRUCT_JANE = (255, 100, 200)

COL_FRAME = (0, 200, 255)
COL_TEXT = (200, 200, 200)
COL_DIM = (100, 100, 100)


# --- Head ---


def _render_head(state: AvatarState) -> tuple[str, tuple[int, int, int]]:
    """Render head based on HP percentage."""
    if state.is_dead:
        return "  X  ", COL_HEAD_DEAD

    pct = state.hp_pct
    if pct >= 0.99:
        return " ◉P◉ ", COL_HEAD_FULL
    if pct >= 0.75:
        return " ◉P· ", COL_HEAD_HIGH
    if pct >= 0.50:
        return " ◉P/ ", COL_HEAD_MID
    return " ◉Px ", COL_HEAD_LOW


# --- Body (pose) ---


def _render_body_pose(state: AvatarState) -> tuple[str, str, tuple[int, int, int]]:
    """Render body trunk (3 lines: shoulders, torso, hips) by status.

    Returns 3 strings + 1 color (shared).
    """
    if state.status is Status.SAFE:
        return " /|\\ ", " \\|/ ", COL_BODY_NORMAL
    if state.status is Status.MATCH:
        return " /|\\ ", " \\|/ ", COL_BODY_NORMAL
    if state.status is Status.TOUGH:
        return " /|\\ ", " \\|/ ", COL_BODY_NORMAL
    if state.status is Status.DEADLY:
        return " /\\  ", "  \\/ ", COL_BODY_LOW
    # FUTILE
    return " .\\  ", "  /, ", COL_BODY_FUTILE


def _render_color_for_status(status: Status) -> tuple[int, int, int]:
    """Map AvatarState ``Status`` → body tint RGB.

    SAFE / MATCH / TOUGH share the calm ``COL_BODY_NORMAL`` palette —
    these are the three non-critical states. DEADLY deepens to
    ``COL_BODY_LOW`` (red) and the implicit FUTILE fallback returns the
    dimmer ``COL_BODY_FUTILE`` so a never-seen status still paints a
    coherent (dark) body rather than raising.
    """
    if status in (Status.SAFE, Status.MATCH):
        return COL_BODY_NORMAL
    if status is Status.TOUGH:
        return COL_BODY_NORMAL
    if status is Status.DEADLY:
        return COL_BODY_LOW
    return COL_BODY_FUTILE


# --- Programs (arms) ---


def _render_program(slot: ProgramSlot) -> tuple[str, tuple[int, int, int]]:
    """Render one program slot.

    Shape:
    - T5: ★X★  (starred)
    - T4: ▓X▓
    - T3: |X|
    - T2: :X:
    - T1: ·X·
    - depleted: ~X~
    """
    if slot.tier < 1:
        return " ═══ ", COL_PROG_LOCKED

    letter = slot.id[0].upper() if slot.id else "?"

    if slot.depleted:
        return f" ~{letter}~ ", COL_PROG_DEPLETED

    if slot.tier >= 5:
        return f" ★{letter}★ ", COL_PROG_T5
    if slot.tier >= 4:
        return f" ▓{letter}▓ ", COL_PROG_T4
    if slot.tier >= 3:
        return f" |{letter}| ", COL_PROG_T3
    if slot.tier >= 2:
        return f" :{letter}: ", COL_PROG_T2
    return f" ·{letter}· ", COL_PROG_T1


def _render_programs_line(programs: tuple[ProgramSlot, ...]) -> str:
    """Render the programs arm line.

    Default 3 slots; pads with spaces if fewer.
    """
    slots = list(programs[:3])
    while len(slots) < 3:
        slots.append(ProgramSlot(id="", tier=0, depleted=False))

    rendered = [_render_program(s) for s in slots]
    return "".join(text for text, _ in rendered)


def _render_programs_colors(programs: tuple[ProgramSlot, ...]) -> list[tuple[int, int, int]]:
    """Get colors for each program slot, for per-cell rendering."""
    slots = list(programs[:3])
    while len(slots) < 3:
        slots.append(ProgramSlot(id="", tier=0, depleted=False))
    return [_render_program(s)[1] for s in slots]


# --- Deck ---


def _render_deck(tier: int) -> tuple[str, tuple[int, int, int]]:
    """Render deck body block."""
    if tier <= 0:
        return " ║X║  ", COL_DECK
    return f" ║DK{tier}║ ", COL_DECK


# --- Wetware (legs) ---


def _render_wetware(tier: int) -> str:
    """Render wetware legs as filled cells."""
    if tier <= 0:
        return "      "
    return " ▓" * tier + " " * (4 - tier) * 2


# --- Construct (echo) ---


def _render_construct(kind: ConstructKind | None) -> tuple[str, tuple[int, int, int]]:
    """Render construct companion echo (only if present)."""
    if kind is None:
        return "      ", COL_DIM
    if kind is ConstructKind.DIXIE:
        return " ◆D◆ ", COL_CONSTRUCT
    if kind is ConstructKind.LOA:
        return " ◯L◯ ", COL_CONSTRUCT_LOA
    # THREE_JANE
    return " ▲▲J▲▲", COL_CONSTRUCT_JANE


# --- Main renderer ---


def render_avatar_lines(state: AvatarState) -> AvatarLines:
    """Render the full avatar as AvatarLines.

    Layout (centered, ~6 cols wide):
    - Line 0: head
    - Line 1: body shoulders
    - Line 2: programs arm
    - Line 3: body hips
    - Line 4: deck
    - Line 5: wetware legs
    - Line 6 (optional): construct echo
    """
    lines: list[tuple[str, tuple[int, int, int]]] = []

    # Head
    head_text, head_color = _render_head(state)
    lines.append((head_text, head_color))

    # Body shoulders
    body_shoulders, body_hips, body_color = _render_body_pose(state)
    lines.append((body_shoulders, body_color))

    # Programs
    prog_text = _render_programs_line(state.programs)
    # Use highest-tier color for the line
    colors = _render_programs_colors(state.programs)
    dominant = max(
        colors,
        key=lambda c: c[0] + c[1] + c[2],
        default=COL_PROG_T1,
    )
    lines.append((prog_text, dominant))

    # Body hips
    lines.append((body_hips, body_color))

    # Deck
    deck_text, deck_color = _render_deck(state.deck_tier)
    lines.append((deck_text, deck_color))

    # Wetware
    lines.append((_render_wetware(state.wetware_tier), COL_WETWARE))

    # Construct (only if present)
    if state.construct is not None:
        c_text, c_color = _render_construct(state.construct)
        lines.append((c_text, c_color))

    # Width: max line length
    width = max(len(text) for text, _ in lines) if lines else 0
    return AvatarLines(lines=lines, width=width)


def render_avatar(
    console: tcod.console.Console,
    x: int,
    y: int,
    state: AvatarState,
    *,
    border: bool = True,
) -> None:
    """Render avatar to tcod console at (x, y).

    Args:
        console: tcod console to draw on.
        x: Left column.
        y: Top row.
        state: Avatar state to render.
        border: If True, draw a frame around the avatar.
    """
    rendered = render_avatar_lines(state)
    width = rendered.width
    height = len(rendered.lines)

    if border:
        # Top border
        console.print(x=x, y=y - 1, string="=" * (width + 2), fg=COL_FRAME)
        # Bottom border
        console.print(x=x, y=y + height, string="=" * (width + 2), fg=COL_FRAME)

    for i, (text, color) in enumerate(rendered.lines):
        # Glitching: random color shift
        if state.glitching and i % 2 == 0:
            color = (color[0] // 2, color[1] // 2, color[2] // 2)
        console.print(x=x, y=y + i, string=text, fg=color)


# --- State builder from engine state ---


def build_avatar_state(
    *,
    hp: int,
    max_hp: int,
    ppl: int,
    zdr: int,
    programs: list[tuple[str, int, bool]] | None = None,
    deck_tier: int = 4,
    wetware_tier: int = 3,
    construct_id: str | None = None,
) -> AvatarState:
    """Build an AvatarState from raw game values.

    Args:
        hp: Current HP.
        max_hp: Maximum HP.
        ppl: Player Power Level.
        zdr: Zone Difficulty Rating.
        programs: List of (program_id, tier, depleted) tuples.
        deck_tier: Deck tier (0-5).
        wetware_tier: Wetware tier (0-5).
        construct_id: "dixie" / "loa" / "jane" / None.

    Returns:
        AvatarState ready for rendering.
    """
    # Status from PPL/ZDR
    if hp <= 0:
        status = Status.FUTILE
    elif zdr <= 0:
        status = Status.SAFE
    else:
        ratio = ppl / zdr
        if ratio >= 2.0:
            status = Status.SAFE
        elif ratio >= 1.0:
            status = Status.MATCH
        elif ratio >= 0.5:
            status = Status.TOUGH
        else:
            status = Status.DEADLY

    # Programs
    prog_slots: list[ProgramSlot] = []
    if programs:
        for prog_id, tier, depleted in programs[:3]:
            prog_slots.append(ProgramSlot(id=prog_id, tier=tier, depleted=depleted))

    # Construct
    construct: ConstructKind | None = None
    if construct_id == "dixie":
        construct = ConstructKind.DIXIE
    elif construct_id == "loa":
        construct = ConstructKind.LOA
    elif construct_id == "jane":
        construct = ConstructKind.THREE_JANE

    return AvatarState(
        hp=hp,
        max_hp=max_hp,
        status=status,
        programs=tuple(prog_slots),
        deck_tier=deck_tier,
        wetware_tier=wetware_tier,
        construct=construct,
    )
