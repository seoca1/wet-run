"""Arc Chapter Phase View — renders arc.json phases with beats (ADR-0031 extended).

Renders arc chapter phases with per-beat typing effect.
Each phase contains multiple beats (interior_monologue, action, dialogue, combat).
Supports beat-type-specific color coding and progression.

Module structure:
    - ArcPhaseData: dataclass wrapping phase beats
    - render_arc_phase: render a phase with beats
    - tick_arc_phase: advance beat typing animation
"""

from __future__ import annotations

from typing import Any

import tcod.console

from wet_run.engine.chapter_cutscene import PhaseData

from ..combat.palette import HIT_FLASH_COLOR, ORANGE_BRIGHT

if True:
    from wet_run.engine.state import AppState
    from wet_run.i18n import Translator

BEAT_TYPE_COLORS = {
    "interior_monologue": ORANGE_BRIGHT,
    "action": (80, 200, 120),
    "dialogue": (50, 180, 220),
    "combat": (220, 80, 80),
}


def tick_arc_phase(
    phase: PhaseData,
    beat_index: int,
    beat_elapsed_ms: float,
    typed_chars: int,
    char_delay_ms: float = 30,
) -> tuple[int, int]:
    """Advance typing animation for current beat.

    Args:
        phase: The phase containing beats.
        beat_index: Current beat index (0-based).
        beat_elapsed_ms: Elapsed ms for current beat.
        typed_chars: Currently typed characters.
        char_delay_ms: Typing delay per character.

    Returns:
        (new_typed_chars, advance_to_next_beat)
    """
    if beat_index >= len(phase.beats):
        return typed_chars, True

    beat = phase.beats[beat_index]
    text = beat.text_en

    if char_delay_ms <= 0:
        return len(text), True

    new_typed = int(beat_elapsed_ms / char_delay_ms)
    new_typed = min(new_typed, len(text))

    if new_typed >= len(text):
        return len(text), True

    return new_typed, False


def render_arc_phase(
    console: tcod.console.Console,
    phase: PhaseData,
    beat_index: int,
    typed_chars: int,
    beat_elapsed_ms: float,
    phase_elapsed_ms: float,
    translator: Translator,
    char_delay_ms: float = 30,
    state: AppState | None = None,
) -> None:
    """Render a phase's current beat with typing effect.

    Layout:
        - Top bar: phase title + beat type
        - Main area: typing-effect beat text
        - Beat progress bar
        - Phase progress bar
        - Controls hint

    Args:
        console: tcod console to draw onto.
        phase: The phase to render.
        beat_index: Current beat index (0-based).
        typed_chars: Number of characters revealed.
        beat_elapsed_ms: Elapsed ms for current beat.
        phase_elapsed_ms: Total elapsed ms for phase.
        translator: i18n translator.
        char_delay_ms: Per-character typing delay.
    """
    width, height = console.width, console.height
    console.clear()

    is_ko = translator.lang == "ko"

    if beat_index >= len(phase.beats):
        console.print(2, 2, "Phase complete.")
        return

    beat = phase.beats[beat_index]
    text = beat.text_ko if is_ko else beat.text_en
    beat_type = beat.type

    color = BEAT_TYPE_COLORS.get(beat_type, HIT_FLASH_COLOR)

    phase_title = phase.title_ko if is_ko else phase.title_en

    console.print(0, 0, "═" * width)

    header = f" PHASE {phase.phase_index + 1} — {phase_title} "
    console.print(2, 0, header)
    console.print(width - len(beat_type) - 4, 0, f" {beat_type.upper()} ")

    console.print(0, 1, "─" * width)

    revealed = text[:typed_chars]

    text_x = 2
    text_y = 3
    text_width = width - text_x - 2

    wrapped_lines: list[str] = []
    for paragraph in revealed.split("\n"):
        if not paragraph:
            wrapped_lines.append("")
            continue
        words = paragraph.split(" ")
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if len(test) > text_width and current:
                wrapped_lines.append(current)
                current = word
            else:
                current = test
        if current:
            wrapped_lines.append(current)

    max_y = height - 8
    for i, line in enumerate(wrapped_lines[:max_y]):
        console.print(text_x, text_y + i, line, fg=color)

    console.print(0, height - 5, "─" * width)

    beat_progress = len(text) / max(len(text), 1)
    beat_bar_width = width - 4
    int(beat_bar_width * (typed_chars / max(len(text), 1)))
    _draw_arc_phase_footer(
        console,
        width,
        height,
        phase,
        beat_index,
        beat_bar_width,
        beat_progress,
        state,
    )


def _draw_arc_phase_footer(
    console: Any,
    width: int,
    height: int,
    phase: Any,
    beat_index: int,
    beat_bar_width: int,
    beat_progress: float,
    state: Any,
) -> None:
    """Render the two progress bars + the controls hint or last status.

    The state argument is the original AppState; it may be ``None``
    in some test paths and we fall back to a generic controls hint.
    """
    if state is not None and state.status_messages:
        last_msg = state.status_messages[-1]
        msg_color = (255, 180, 100) if "VICTORY" in last_msg else (180, 180, 180)
        status = last_msg[: width - 4]
    else:
        msg_color = (180, 180, 180)
        status = " [ENTER] Next Beat   [SPACE] Skip Beat   [ESC] Exit Phase"

    beat_bar = "█" * int(beat_bar_width * beat_progress) + "░" * (
        beat_bar_width - int(beat_bar_width * beat_progress)
    )
    console.print(
        2,
        height - 4,
        f"Beat {beat_index + 1}/{len(phase.beats)}: [{beat_bar}] {int(beat_progress * 100):3d}%",
    )

    num_beats = len(phase.beats)
    phase_progress = (beat_index + beat_progress) / max(num_beats, 1)
    phase_filled = int(beat_bar_width * phase_progress)
    phase_bar = "▓" * phase_filled + "░" * (beat_bar_width - phase_filled)
    console.print(2, height - 3, f"Phase: [{phase_bar}] {int(phase_progress * 100):3d}%")

    console.print(2, height - 2, status, fg=msg_color)
    console.print(0, height - 1, "═" * width)
