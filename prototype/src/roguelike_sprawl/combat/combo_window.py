"""Combo cinematic rendering (ADR-0158 split).

Pure rendering functions for the combo counter, stage-up callout, end
cinematic, and full HUD. Inputs are taken from dataclasses in
``combo.py``; no business logic (stage transition, hit counting, AP
bonus) lives here.
"""

from __future__ import annotations

from .combo import CombatCombo, ComboVisual, TimingBar, get_avatar_for_stage

__all__ = [
    "render_combo_counter",
    "render_combo_end",
    "render_combo_full",
    "render_combo_stage_up",
    "render_timing_bar",
]


def render_combo_counter(visual: ComboVisual, width: int = 30) -> str:
    """Render the combo counter for top-center display.

    Returns the text to display. Empty if no active combo.
    """
    if not visual.counter_text:
        return ""

    text = visual.counter_text
    pad = max(0, (width - len(text)) // 2)
    return " " * pad + text


def render_combo_stage_up(visual: ComboVisual) -> str:
    """Render the stage-up cinematic text (one-time callout)."""
    if visual.stage_up_ms <= 0:
        return ""
    return visual.stage_up_text


def render_combo_end(visual: ComboVisual) -> str:
    """Render the end cinematic text."""
    if visual.end_ms <= 0:
        return ""
    return visual.end_text


def render_timing_bar(combo: CombatCombo, width: int = 20) -> str:
    """Convenience function: render the timing bar."""
    bar = TimingBar(width=width)
    return bar.render(combo)


def render_combo_full(
    combo: CombatCombo,
    visual: ComboVisual | None = None,
    show_avatar: bool = True,
    show_timing: bool = True,
    width: int = 30,
) -> str:
    """Render the full combo HUD as a multi-line string.

    Layout (top to bottom):
      [avatar] 3x CHAIN!
      [████████████████░░░░] 60%
    """
    if combo.count == 0:
        return ""

    lines: list[str] = []

    if show_avatar:
        avatar = get_avatar_for_stage(combo.current_stage)
        pulse_active = visual is not None and visual.counter_pulse_ms > 0
        icon = avatar.get_frame(pulse_active=pulse_active)
        counter = (
            f"{combo.display_count}x {combo.current_stage.label}"
            if combo.current_stage.label
            else f"{combo.display_count}x"
        )
        lines.append(f"{icon} {counter}")

    if show_timing:
        bar = TimingBar(width=width)
        lines.append(bar.render(combo))

    return "\n".join(lines)
