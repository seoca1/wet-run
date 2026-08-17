"""Graphic novel render functions — scene + chapter card + blank transition (ADR-0032 + ADR-0042).

Split from graphic_novel_view.py (ADR-0133 § 향후 split 계획).
Owns the heavy rendering logic; graphic_novel_view.py is reduced to a
thin coordinator that re-exports these symbols for backward compatibility.

Module structure (post ADR-0133 v2 split):
    - graphic_novel_data: SceneData, DialogueLine, Portrait, Background
    - graphic_novel_loaders: load_*, _parse_*, list_scenes_for_character
    - gn_render (this file): render_scene + render_chapter_card + render_blank_transition + utilities
    - gn_menu: GRAPHIC_NOVEL_MENU + GRAPHIC_NOVEL_ENDING_MENU
    - graphic_novel_view: top-level screen coordinator + re-exports

Re-exported by graphic_novel_view for backward compat (ADR-0111).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod.console

from .graphic_novel_data import (
    Background,
    DialogueLine,
    Portrait,
    SceneData,
)

if TYPE_CHECKING:
    from ..i18n import Translator


# ============================================================================
# Constants
# ============================================================================


# Default novel layout: how many chars per line of prose.
# Mirrors book margins: ~10 chars left margin, ~10 chars right margin.
NOVEL_LEFT_MARGIN = 2
NOVEL_RIGHT_MARGIN = 2


# Roman numerals for chapter numbering (1-12 covers all current scenes)
_ROMAN = (
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
    "XI",
    "XII",
)


# ============================================================================
# Progress + utility calculations
# ============================================================================


def dialogue_typed_chars(duration_ms: int, elapsed_ms: float, total_chars: int) -> int:
    """Calculate how many characters of a dialogue should be revealed.

    Args:
        duration_ms: Total duration of the dialogue.
        elapsed_ms: Time since dialogue started.
        total_chars: Total character count in the dialogue text.

    Returns:
        Number of characters to reveal (0 to total_chars).
    """
    if duration_ms <= 0:
        return total_chars
    return min(int(elapsed_ms / 30), total_chars)


def scene_progress(chain_index: int, chain_length: int) -> float:
    """Calculate the overall progress through the scene chain.

    Returns:
        Progress 0.0 ~ 1.0
    """
    if chain_length == 0:
        return 0.0
    return min(chain_index / chain_length, 1.0)


# ============================================================================
# Novel-style pagination (book page layout)
# ============================================================================


def wrap_text_for_novel(
    text: str,
    *,
    width: int | None = None,
    left_margin: int = NOVEL_LEFT_MARGIN,
    right_margin: int = NOVEL_RIGHT_MARGIN,
) -> list[str]:
    """Wrap a paragraph of prose into a list of lines that fit the novel page.

    Uses a simple word-wrap algorithm. Single newlines in the source are
    preserved as paragraph breaks (yielding a blank line in output).
    Consecutive newlines collapse to one blank line.

    Args:
        text: The full prose text (may contain ``\\n`` for paragraph breaks).
        width: Console width (defaults to 80).
        left_margin: Left indentation in cells.
        right_margin: Right indentation in cells.

    Returns:
        List of wrapped lines, each <= (width - left_margin - right_margin) chars.
    """
    if width is None:
        width = 80
    usable = max(10, width - left_margin - right_margin)
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        current = ""
        for word in paragraph.split(" "):
            if not current:
                candidate = word
            else:
                candidate = current + " " + word
            if len(candidate) > usable and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
    return lines


def paginate_lines(
    lines: list[str],
    *,
    lines_per_page: int,
    blank_separator: bool = True,
) -> list[list[str]]:
    """Split wrapped lines into pages of at most ``lines_per_page`` lines.

    Page breaks never split a non-empty line. A blank separator line is
    inserted between pages if ``blank_separator`` is True and the boundary
    is mid-paragraph.

    Args:
        lines: Output of :func:`wrap_text_for_novel`.
        lines_per_page: Maximum rendered lines per page.
        blank_separator: Insert a blank line at page boundaries.

    Returns:
        List of pages, each a list of lines.
    """
    if lines_per_page <= 0:
        return [lines]
    pages: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        # Avoid breaking a paragraph: if adding this line would overflow
        # AND the previous line is non-empty, finalize the page first.
        if len(current) >= lines_per_page and current:
            pages.append(current)
            current = []
            if blank_separator and line:
                current.append("")
        current.append(line)
    if current:
        pages.append(current)
    if not pages:
        pages = [[]]
    return pages


def compute_typed_page_index(
    pages: list[list[str]],
    typed_chars: int,
    full_text: str,
) -> int:
    """Determine which page is currently visible based on typed chars.

    Pages advance as the typing cursor crosses the end of each page's
    combined text. This makes pagination feel natural with the existing
    typing effect: when you press Space, the typing skips to a later page.

    Args:
        pages: Output of :func:`paginate_lines`.
        typed_chars: How many characters of the full text are revealed.
        full_text: The original (unwrapped) full text.

    Returns:
        Index of the current page (0-based).
    """
    if not pages:
        return 0
    # Build cumulative character count per page boundary
    cumulative = 0
    for i, page in enumerate(pages):
        page_chars = sum(len(line) for line in page) + max(0, len(page) - 1)
        # Add word-boundary slop
        cumulative += page_chars
        if typed_chars <= cumulative:
            return i
    return len(pages) - 1


# ============================================================================
# Scene rendering (ADR-0032)
# ============================================================================


def render_scene(
    console: tcod.console.Console,
    scene: SceneData,
    dialogue: DialogueLine,
    background: Background | None,
    portrait_l: Portrait | None,
    portrait_r: Portrait | None,
    translator: Translator,
    typed_chars: int,
    scene_index: int,
    scene_total: int,
    *,
    paused: bool = False,
) -> None:
    """Render one frame of the graphic novel — novel-style book layout.

    The screen is treated as an open book page:

    - Top bar (1 line): ``[N/total]  TITLE · CHARACTER`` and controls hint
    - Subtle background art in the upper band (y=1..12) so the page keeps
      its atmosphere without dominating the prose
    - Speaker heading (chapter-style) and full-width wrapped prose
      (y=14..HEIGHT-4) — uses ~30 lines of text instead of 3
    - Page footer with ``PAGE n/N`` and progress bar
    - Long text auto-paginates within the dialogue duration; pagination
      follows the typing cursor so pressing Space skips to the next page

    Args:
        console: tcod console.
        scene: Current scene.
        dialogue: Current dialogue line.
        background: Optional background art.
        portrait_l: Optional left portrait.
        portrait_r: Optional right portrait.
        translator: i18n translator.
        typed_chars: How many characters of the dialogue are revealed.
        scene_index: Zero-based index of the current scene.
        scene_total: Total number of scenes in the chain.
        paused: Whether auto-play is paused.
    """
    width, height = console.width, console.height
    console.clear()

    is_ko = translator.lang == "ko"
    title = scene.title_ko if is_ko else scene.title_en
    speaker = dialogue.speaker_ko if is_ko else dialogue.speaker
    text = dialogue.text_ko if is_ko else dialogue.text_en

    _draw_scene_top_bar(console, width, scene_index, scene_total, title, scene, paused)
    _draw_scene_background_band(console, width, background)
    _draw_scene_portrait(console, width, portrait_l, portrait_r)
    _draw_scene_speaker_heading(console, width, speaker)
    page_count = _draw_scene_prose_body(
        console,
        width,
        text,
        typed_chars,
        speaker,
        scene_index,
        scene_total,
    )
    _draw_scene_footer(console, width, height, scene_index, scene_total, paused, page_count)


# ------------------------------------------------------------------
# render_scene helpers — one per band of the book-page layout.
# ------------------------------------------------------------------


def _draw_scene_top_bar(
    console: tcod.console.Console,
    width: int,
    scene_index: int,
    scene_total: int,
    title: str,
    scene: SceneData,
    paused: bool,
) -> None:
    """Top bar: scene counter + title + character + control hint."""
    top = f" [{scene_index + 1}/{scene_total}]  {title}  ·  {scene.character.upper()}"
    if paused:
        top += "                [PAUSED]  [P] resume"
    else:
        top += "  [S] skip  [P] pause  [ESC] menu"
    console.print(0, 0, top[:width])
    console.print(0, 1, "─" * width)


def _draw_scene_background_band(
    console: tcod.console.Console,
    width: int,
    background: Background | None,
) -> None:
    """Atmospheric background art, y=2..13 with per-cell color support."""
    if background is None:
        return
    bg_band_bottom = 14
    palette = background.palette
    char_colors = background.char_colors
    default_color = palette.get("default", (160, 160, 180))
    for i, line in enumerate(background.art):
        y = 2 + i
        if y >= bg_band_bottom:
            break
        for x_offset, ch in enumerate(line[:width]):
            x = x_offset
            if 0 <= x < width:
                color_key = char_colors.get(ch, "default")
                color = palette.get(color_key, default_color)
                console.print(x, y, ch, fg=color)


def _draw_scene_portrait(
    console: tcod.console.Console,
    width: int,
    portrait_l: Portrait | None,
    portrait_r: Portrait | None,
) -> None:
    """A small portrait in the corner with a dimmed backdrop.

    Renders each character with per-cell color via palette lookup.
    Clipping bug fixed: uses portrait.height (12) instead of hardcoded 14.
    """
    portrait = portrait_l or portrait_r
    if portrait is None:
        return
    px = 2 if portrait_l else width - portrait.width - 2
    py = 2
    bg_band_bottom = 14
    palette = portrait.palette
    char_colors = portrait.char_colors
    default_color = palette.get("default", (200, 200, 220))
    # Dim background panel behind portrait
    for dy in range(portrait.height):
        y = py + dy
        if y >= bg_band_bottom:
            break
        for dx in range(portrait.width + 4):
            x = px - 2 + dx
            if 0 <= x < width:
                code = int(console.ch[x, y])
                if code == 0x20:
                    console.print(x, y, "░", fg=(50, 50, 60))
    for i, line in enumerate(portrait.art):
        y = py + i
        if y >= bg_band_bottom:
            break
        for x_offset, ch in enumerate(line[: portrait.width]):
            x = px + x_offset
            if 0 <= x < width:
                color_key = char_colors.get(ch, "default")
                color = palette.get(color_key, default_color)
                console.print(x, y, ch, fg=color)


def _draw_scene_speaker_heading(
    console: tcod.console.Console,
    width: int,
    speaker: str,
) -> None:
    """Centered chapter-style heading above the prose body."""
    if not speaker:
        return
    heading = f"── {speaker} ──"
    console.print((width - len(heading)) // 2, 14, heading)


def _draw_scene_prose_body(
    console: tcod.console.Console,
    width: int,
    text: str,
    typed_chars: int,
    speaker: str,
    scene_index: int,
    scene_total: int,
) -> int:
    """Auto-paginated prose with a per-character typing effect.

    Uses the typed cursor to figure out which page is on-screen and
    how many characters of it are revealed.
    """
    height = console.height
    body_y = 16 if speaker else 14
    body_bottom = height - 4
    lines_per_page = max(1, body_bottom - body_y)
    body_width = width - NOVEL_LEFT_MARGIN - NOVEL_RIGHT_MARGIN
    wrapped = wrap_text_for_novel(text, width=width)
    pages = paginate_lines(wrapped, lines_per_page=lines_per_page, blank_separator=False)
    current_page = compute_typed_page_index(pages, typed_chars, text)
    page_lines = pages[current_page] if pages else []
    rendered_lines = _truncate_page_to_typed(page_lines, typed_chars, pages, current_page)
    _emit_typed_lines(console, width, body_y, body_bottom, body_width, rendered_lines)
    return len(pages)


def _truncate_page_to_typed(
    page_lines: list[str],
    typed_chars: int,
    pages: list[list[str]],
    current_page: int,
) -> list[str]:
    """Return the page's lines, with the last one cut at the typed
    cursor so the rest of the text appears progressively."""

    def _page_char_count(page: list[str]) -> int:
        """Return the total character count of a page if its lines were joined by spaces.

        Lines are conceptually re-joined with a single space between each, so
        n lines contribute ``sum(len) + (n-1)`` chars (one separator per gap).

        Args:
            page: List of wrapped lines on the page.

        Returns:
            Effective character count of the page.
        """
        # n lines joined by single spaces = sum(len) + (n-1) spaces
        return sum(len(line) for line in page) + max(0, len(page) - 1)

    chars_so_far = sum(_page_char_count(p) for p in pages[:current_page])
    chars_this_page = max(0, typed_chars - chars_so_far)
    cursor = 0
    rendered: list[str] = []
    for line in page_lines:
        if cursor >= chars_this_page:
            rendered.append("")
            continue
        remaining = chars_this_page - cursor
        if remaining >= len(line):
            rendered.append(line)
            cursor += len(line) + 1
        else:
            rendered.append(line[:remaining])
            cursor = chars_this_page
    return rendered


def _emit_typed_lines(
    console: tcod.console.Console,
    width: int,
    body_y: int,
    body_bottom: int,
    body_width: int,
    rendered_lines: list[str],
) -> None:
    """Print each line, character by character, in the soft-cream
    color that we use for novel prose (ADR-0047)."""
    # ADR-0047: prose body text with explicit color for readability.
    # Use light cream-white (warmer than pure white for less eye strain)
    # on a subtle dark teal background to enhance contrast.
    prose_fg = (232, 230, 220)  # soft cream
    for i, line in enumerate(rendered_lines):
        y = body_y + i
        if y >= body_bottom:
            break
        # Render with subtle per-character for proper Korean/CJK width
        for col, ch in enumerate(line.ljust(body_width)):
            xx = NOVEL_LEFT_MARGIN + col
            if xx >= console.width:
                break
            console.print(xx, y, ch, fg=prose_fg)


def _draw_scene_footer(
    console: tcod.console.Console,
    width: int,
    height: int,
    scene_index: int,
    scene_total: int,
    paused: bool,
    page_count: int = 1,
) -> None:
    """Page counter (when paginated) + progress bar + control hint."""
    if height < 6:
        return
    # Page label (y=height-3). Only when paginated — single-page scenes
    # don't need a "PAGE 1/1" footer.
    if page_count > 1:
        label = f" PAGE 1/{page_count} "
        console.print(
            (width - len(label)) // 2,
            height - 3,
            label,
        )
    progress = scene_progress(scene_index, scene_total)
    bar_w = width - 4
    filled = int(bar_w * progress)
    bar = "█" * filled + "░" * (bar_w - filled)
    console.print(2, height - 2, f" [{bar}] {int(progress * 100):3d}%")
    if paused:
        console.print(2, height - 1, "                      [P] resume  [S] skip  [ESC] menu")
    else:
        console.print(2, height - 1, "         [Space] next  [P] pause  [S] skip  [ESC] menu")


# ============================================================================
# Chapter title card (transition between scenes) — ADR-0042
# ============================================================================


def _to_roman(n: int) -> str:
    """Convert 1-12 to roman numeral. Falls back to Arabic for larger values."""
    if 1 <= n <= len(_ROMAN):
        return _ROMAN[n - 1]
    return str(n)


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


# Re-exported by graphic_novel_view for backward compat (ADR-0111).
__all__ = [
    "Background",
    "DialogueLine",
    "NOVEL_LEFT_MARGIN",
    "NOVEL_RIGHT_MARGIN",
    "Portrait",
    "SceneData",
    "_character_label",
    "_to_roman",
    "compute_typed_page_index",
    "dialogue_typed_chars",
    "paginate_lines",
    "render_blank_transition",
    "render_chapter_card",
    "render_scene",
    "scene_progress",
    "wrap_text_for_novel",
]
