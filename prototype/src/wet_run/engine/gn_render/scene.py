"""Scene rendering for the graphic novel (ADR-0032).

Cohesion: novel-style book-page layout rendering for an in-progress
scene + dialogue. Owns the top bar, atmospheric background band,
portrait, speaker heading, prose body (typed cursor + auto-pagination),
and footer with progress bar.

    - dialogue_typed_chars / scene_progress: timing + progress math
    - render_scene: top-level dispatcher; one helper per band

Split from gn_render.py per ADR-0110 + ADR-0142 v2 split pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod.console

from ..graphic_novel_data import (
    Background,
    DialogueLine,
    Portrait,
    SceneData,
)
from .text import (
    NOVEL_LEFT_MARGIN,
    NOVEL_RIGHT_MARGIN,
    compute_typed_page_index,
    paginate_lines,
    wrap_text_for_novel,
)

if TYPE_CHECKING:
    from ...i18n import Translator


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
