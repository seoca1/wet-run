"""Chapter title card and fade transitions (ADR-0042).

Cohesion: inter-scene transition rendering.
    - _character_label: localized chapter-card character label
    - render_chapter_card: bordered title card with optional fade-in
    - render_blank_transition: brief blank pause between scenes

Split from gn_render.py per ADR-0110 + ADR-0142 v2 split pattern.
"""

from __future__ import annotations

import tcod.console

from ..graphic_novel_data import SceneData
from .text import _to_roman


def _character_label(character_id: str, lang: str) -> str:
    """Localized character label for chapter card."""
    labels = {
        "novice": {"en": "Case (K) — Novice", "ko": "케이 (K) — Novice"},
        "veteran": {"en": "Marly (Sil) — Veteran", "ko": "실 (Sil) — Veteran"},
        "heretic": {"en": "Kumiko (Kas) — Heretic", "ko": "카스 (Kas) — Heretic"},
        "suit": {"en": "Suit — Corporate (3인칭)", "ko": "스위트 — 기업 픽서 (3인칭)"},
        "wigan": {"en": "Wigan — Vodou Construct", "ko": "위건 — 부두 construct"},
        "angie": {"en": "Angie — Loa Receiver", "ko": "앤지 — 로아 수신자"},
        "sally": {"en": "Sally — Market Operator", "ko": "샐리 — 시장 운영자"},
        "3jane": {"en": "3Jane — Family Heir", "ko": "3Jane — 가족의 후계자"},
        "neuromancer": {"en": "Neuromancer — Merged AI", "ko": "뉴로맨서 — 합체된 AI"},
    }
    return labels.get(character_id, {}).get(lang, character_id)


def render_chapter_card(
    console: tcod.console.Console,
    scene: SceneData,
    scene_index: int,
    scene_total: int,
    *,
    transition_ms: int = 0,
    transition_duration_ms: int = 1500,
    lang: str = "en",
    is_last_scene: bool = False,
) -> None:
    """Render a chapter title card between scenes.

    Layout (centered, ~14 rows tall):
        ════════════════════════════════════════════════
            ·  CHAPTER I  ·
            ───────────────────
            CHATTO'S 24/7
            케이 (K) — Novice
            Scene 1 of 4
            ─────────────
        ════════════════════════════════════════════════

    The card uses ASCII ornaments (·, ─, ═) for a book-like feel.
    Optional transition fade-in via ``transition_ms``: the entire card
    is dimmed during the first ``transition_duration_ms`` ms and then
    fades to full brightness.

    Args:
        console: tcod console.
        scene: The scene whose title card to render.
        scene_index: 0-based index of the scene in the chain.
        scene_total: Total scenes in the chain.
        transition_ms: Time elapsed since card appeared (for fade).
        transition_duration_ms: How long the fade-in lasts.
        lang: 'en' or 'ko'.
        is_last_scene: If True, shows "FINALE" instead of "CHAPTER N".
    """
    width, height = console.width, console.height
    console.clear()

    is_ko = lang == "ko"
    title = scene.title_ko if is_ko else scene.title_en
    char_label = _character_label(scene.character, lang)
    fade = _compute_card_fade(transition_ms, transition_duration_ms)
    header = _chapter_header_text(scene_index, scene_total, is_last_scene, is_ko)
    border = "═" * (width - 2)
    card_y_start = (height - 9) // 2

    _draw_card_borders(console, width, card_y_start, border, header)
    _draw_card_text(
        console,
        width,
        card_y_start,
        is_ko,
        title,
        char_label,
        scene_index,
        scene_total,
    )
    _draw_card_bottom_hint(console, width, height, is_ko)
    _apply_card_fade(console, width, card_y_start, fade)


# ------------------------------------------------------------------
# render_chapter_card helpers — one per logical concern
# ------------------------------------------------------------------


def _compute_card_fade(transition_ms: int, transition_duration_ms: int) -> float:
    """Return a 0.0–1.0 fade factor based on elapsed time."""
    if transition_duration_ms <= 0 or transition_ms >= transition_duration_ms:
        return 1.0
    return max(0.0, transition_ms / transition_duration_ms)


def _chapter_header_text(
    scene_index: int,
    scene_total: int,
    is_last_scene: bool,
    is_ko: bool,
) -> str:
    """Format the chapter header (FINALE or roman-numeral)."""
    if is_last_scene and scene_total >= 3:
        return " ·  FINALE  · "
    roman = _to_roman(scene_index + 1)
    return f" ·  CHAPTER {roman}  · "


def _draw_card_borders(
    console: tcod.console.Console,
    width: int,
    card_y_start: int,
    border: str,
    header: str,
) -> None:
    """Top + bottom border, the header line, and a thin divider."""
    console.print(0, card_y_start, border)
    header_x = (width - len(header)) // 2
    console.print(header_x, card_y_start + 1, header)
    divider = "─" * min(width - 6, 30)
    div_x = (width - len(divider)) // 2
    console.print(div_x, card_y_start + 2, divider)


def _draw_card_text(
    console: tcod.console.Console,
    width: int,
    card_y_start: int,
    is_ko: bool,
    title: str,
    char_label: str,
    scene_index: int,
    scene_total: int,
) -> None:
    """Title, character, and scene-count lines (the card body)."""
    title_x = (width - len(title)) // 2
    console.print(title_x, card_y_start + 4, title)
    char_x = (width - len(char_label)) // 2
    console.print(char_x, card_y_start + 5, char_label)

    if is_ko:
        scene_label = f"씬 {scene_index + 1} / {scene_total}"
    else:
        scene_label = f"Scene {scene_index + 1} of {scene_total}"
    scene_x = (width - len(scene_label)) // 2
    console.print(scene_x, card_y_start + 7, scene_label)

    divider = "─" * min(width - 6, 30)
    div_x = (width - len(divider)) // 2
    console.print(div_x, card_y_start + 8, divider)
    console.print(0, card_y_start + 9, "═" * (width - 2))


def _draw_card_bottom_hint(
    console: tcod.console.Console,
    width: int,
    height: int,
    is_ko: bool,
) -> None:
    """Control hint at the bottom of the card."""
    if is_ko:
        hint = "         [Space] 시작  [ESC] 메뉴"
    else:
        hint = "         [Space] begin  [ESC] menu"
    console.print(2, height - 2, hint)


def _apply_card_fade(
    console: tcod.console.Console,
    width: int,
    card_y_start: int,
    fade: float,
) -> None:
    """Substitute ornament glyphs with dimmer characters when fading in."""
    if fade >= 1.0:
        return
    dim_level = int(fade * 100)
    border_height = 10
    for y in range(card_y_start, card_y_start + border_height):
        line = "".join(chr(int(console.ch[x, y])) for x in range(width)).rstrip()
        if dim_level < 33:
            # Heavy fade: heavy- and mid-line ornament to block, dots to space
            line = line.replace("═", "▒").replace("─", "░").replace("·", " ")
        elif dim_level < 66:
            # Mid fade
            line = line.replace("═", "▓").replace("─", "▒")
        for x, ch in enumerate(line):
            if ch:
                console.print(x, y, ch)


def render_blank_transition(
    console: tcod.console.Console,
    transition_ms: int,
    transition_duration_ms: int = 800,
) -> None:
    """Render a brief blank pause between scenes (fade-out to black).

    Uses progressively dimmer background to simulate a fade.
    """
    width, height = console.width, console.height
    console.clear()
    # Show ░▒▓ chars with density based on transition progress
    if transition_duration_ms <= 0:
        return
    progress = min(1.0, transition_ms / transition_duration_ms)
    # First half: dim out (▒), second half: dim in (░)
    if progress < 0.5:
        density = int(progress * 2 * 100)  # 0..100%
        char = "▓" if density > 66 else "▒" if density > 33 else "░"
    else:
        # In fade — show nothing
        return
    for y in range(height):
        console.print(0, y, char * width)
