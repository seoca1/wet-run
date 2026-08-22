"""Text utilities for the graphic novel renderer (ADR-0032 + ADR-0042).

Cohesion: pure text/pagination helpers with no rendering side effects.
    - NOVEL_LEFT_MARGIN / NOVEL_RIGHT_MARGIN: book-page layout constants
    - _ROMAN / _to_roman: roman numerals for chapter numbering
    - wrap_text_for_novel / paginate_lines / compute_typed_page_index:
      novel-style word wrap and page pagination

Split from gn_render.py per ADR-0110 + ADR-0142 v2 split pattern.
"""

from __future__ import annotations

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


def _to_roman(n: int) -> str:
    """Convert 1-12 to roman numeral. Falls back to Arabic for larger values."""
    if 1 <= n <= len(_ROMAN):
        return _ROMAN[n - 1]
    return str(n)


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
