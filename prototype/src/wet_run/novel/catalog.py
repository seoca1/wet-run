"""Novel catalog (ADR-0061).

Auto-discovers derivative stories on disk and exposes a small query
API.  Designed so adding a new short story is a *filesystem* event:
drop the file into the conventional directory and it shows up the
next time ``NovelCatalog`` loads.

Supports two story *formats*:

- ``short_story``: a single markdown file with frontmatter
- ``episode``: a markdown file plus a sibling ``.episodes.json`` index

The enum is forward-compatible: a future ``novelette`` or
``serial`` format can be added without changing call sites.

Stories can be filtered by:

- ``language()``        → ``"en"`` / ``"ko"``
- ``by_stem(stem)``     → exact lookup
- ``by_tag(tag)``       → frontmatter ``game_integration`` matches
- ``by_hook_kind(kind)``→ stories that the manifest says produce ``kind``
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class NovelFormat(StrEnum):
    """Story container formats.

    Extending the corpus (novelettes, episode bundles, serial
    installments) requires adding a new format and a matching
    parser below.  Existing code never instantiates these directly —
    it asks the catalog for an entry, which carries its own format.
    """

    SHORT_STORY = "short_story"
    EPISODE = "episode"
    NOVELETTE = "novelette"
    SERIAL = "serial"


@dataclass(slots=True)
class NovelEntry:
    """A single story (or episode bundle) discovered on disk.

    Attributes:
        stem: Stable identifier — strips date and language suffix.
        format: Container format (see ``NovelFormat``).
        title_en / title_ko: Best-effort extracted titles.
        author_en / author_ko: Author strings, may be missing.
        tags: Frontmatter tags (e.g. ``"matrix"``, ``"sally"``).
        sources: Other stems this story depends on / cites.
        game_integration: Game integration string (e.g. mission id).
        en_path / ko_path: On-disk paths for the two translations.
        episodes: List of (episode_id, title, path) tuples; empty
            for non-EPISODE formats.
    """

    stem: str
    format: NovelFormat = NovelFormat.SHORT_STORY
    title_en: str = ""
    title_ko: str = ""
    author_en: str = ""
    author_ko: str = ""
    tags: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    game_integration: str = ""
    en_path: Path | None = None
    ko_path: Path | None = None
    episodes: list[tuple[str, str, Path]] = field(default_factory=list)


@dataclass(slots=True)
class NovelCatalog:
    """Indexed view over all derivative stories on disk.

    Use ``NovelCatalog.load(repo_root)`` once at process start and
    share the resulting instance.  Call sites look up entries by
    ``stem`` (mission source) and ask the catalog for their hooks.
    """

    repo_root: Path
    entries: dict[str, NovelEntry] = field(default_factory=dict)
    stems_by_tag: dict[str, set[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Lazily populate the catalog if no entries were supplied at construction."""
        if not self.entries:
            self.refresh()

    # ----- discovery ----------------------------------------------------

    SHORT_STORIES_DIR = Path("Fiction/derivative/sprawl-trilogy/short-stories")

    @classmethod
    def load(cls, repo_root: Path) -> NovelCatalog:
        """Construct a catalog, scanning the corpus if needed."""
        cat = cls(repo_root=repo_root, entries={}, stems_by_tag={})
        cat.refresh()
        return cat

    def refresh(self) -> None:
        """Rescan the corpus and rebuild the index.

        Cheap to call; intended for use after dropping a new file
        into the short-stories directory.
        """
        self.entries.clear()
        self.stems_by_tag.clear()
        base = self.repo_root / self.SHORT_STORIES_DIR
        if not base.exists():
            return
        # Group files by stem first.
        by_stem: dict[str, dict[str, Path]] = {}
        for f in base.glob("*.md"):
            stem, lang = _parse_filename(f.name)
            if not stem:
                continue
            by_stem.setdefault(stem, {})[lang] = f
        # Build entries.
        for stem, paths in sorted(by_stem.items()):
            en = paths.get("en")
            ko = paths.get("ko")
            en_meta = _read_frontmatter(en) if en else {}
            ko_meta = _read_frontmatter(ko) if ko else {}
            tags = _coerce_str_list(en_meta.get("game_integration"))
            sources = _coerce_str_list(en_meta.get("wiki_references"))
            entry = NovelEntry(
                stem=stem,
                format=NovelFormat.SHORT_STORY,
                title_en=_title_for(en_meta, lang="en"),
                title_ko=_title_for(ko_meta, lang="ko"),
                author_en=_author_for(en_meta),
                author_ko=_author_for(ko_meta),
                tags=tags,
                sources=sources,
                game_integration=str(en_meta.get("game_integration", "")),
                en_path=en,
                ko_path=ko,
            )
            self.entries[stem] = entry
            for tag in tags:
                self.stems_by_tag.setdefault(tag, set()).add(stem)

    # ----- query helpers ------------------------------------------------

    def __len__(self) -> int:
        """Return the number of registered novel entries."""
        return len(self.entries)

    def __iter__(self) -> Iterator[NovelEntry]:
        """Iterate over all registered :class:`NovelEntry` values."""
        return iter(self.entries.values())

    def by_stem(self, stem: str) -> NovelEntry | None:
        """Look up an entry by its file stem.

        Args:
            stem: The stem of the short-story file (no extension, no language suffix).

        Returns:
            The matching :class:`NovelEntry`, or ``None`` if not found.
        """
        return self.entries.get(stem)

    def __contains__(self, stem: object) -> bool:
        """Return ``True`` if a stem is registered as an entry.

        Non-string keys always return ``False``.
        """
        return isinstance(stem, str) and stem in self.entries

    def by_tag(self, tag: str) -> list[NovelEntry]:
        """Return all entries tagged with ``tag``, sorted by stem.

        Args:
            tag: Game-integration tag (e.g. ``"first_jack"``).

        Returns:
            Sorted list of matching :class:`NovelEntry` objects.
        """
        return [self.entries[s] for s in sorted(self.stems_by_tag.get(tag, set()))]

    def language_pairs(self) -> list[tuple[str, str]]:
        """Return all (stem, language) pairs available on disk."""
        pairs: list[tuple[str, str]] = []
        for stem, entry in self.entries.items():
            if entry.en_path is not None:
                pairs.append((stem, "en"))
            if entry.ko_path is not None:
                pairs.append((stem, "ko"))
        return pairs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_FILENAME_RE = re.compile(r"^(?:\d{4}-\d{2}-\d{2}_)?(.+?)(?:\.ko)?\.md$")


def _parse_filename(name: str) -> tuple[str, str]:
    """Extract the stem and language from a filename.

    Examples:
        >>> _parse_filename("2026-06-23_case_jackout-30sec.md")
        ("case_jackout-30sec", "en")
        >>> _parse_filename("2026-06-23_case_jackout-30sec.ko.md")
        ("case_jackout-30sec", "ko")
    """
    match = _FILENAME_RE.match(name)
    if not match:
        return "", "en"
    stem = match.group(1)
    lang = "ko" if name.endswith(".ko.md") else "en"
    return stem, lang


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _read_frontmatter(path: Path | None) -> dict[str, object]:
    """Read the YAML-ish frontmatter block at the top of a markdown file.

    Pure stdlib — no PyYAML dependency.  Supports the limited grammar
    used by our derivative corpus: ``key: value`` pairs, list blocks
    (lines starting with ``  - ``), and inline ``key: { en: …, ko: … }``.
    """
    if path is None or not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    body = match.group(1)
    result: dict[str, object] = {}
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, _, raw = line.partition(":")
        key = key.strip()
        raw = raw.strip()
        # List of scalars
        if not raw:
            j = i + 1
            # Nested block?
            child_pairs: dict[str, str] = {}
            nested_block = False
            while j < len(lines):
                stripped = lines[j].lstrip()
                if not stripped:
                    j += 1
                    continue
                # Stop if line is no longer indented (new top-level key)
                if lines[j] and lines[j][0] not in (" ", "\t") and ":" in lines[j]:
                    break
                # Hyphen-prefixed list item
                if stripped.startswith("- "):
                    break
                if not nested_block and ":" in stripped:
                    nested_block = True
                if nested_block and ":" in stripped:
                    ckey, _, cval = stripped.partition(":")
                    child_pairs[ckey.strip()] = cval.strip().strip('"').strip("'")
                j += 1
            if nested_block:
                result[key] = child_pairs
                i = j
                continue
            # Otherwise treat as a list block (hyphen items)
            j = i + 1
            items = []
            while j < len(lines) and lines[j].strip().startswith("- "):
                items.append(lines[j].strip()[2:].strip().strip('"').strip("'"))
                j += 1
            result[key] = items
            i = j
            continue
        # Inline dict { en: ..., ko: ... }
        if raw.startswith("{") and raw.endswith("}"):
            result[key] = _parse_inline_dict(raw)
            i += 1
            continue
        # Quoted scalar
        if raw.startswith('"') and raw.endswith('"'):
            result[key] = raw[1:-1]
        elif raw.startswith("'") and raw.endswith("'"):
            result[key] = raw[1:-1]
        elif raw.lstrip("-").isdigit():
            result[key] = int(raw)
        else:
            result[key] = raw
        i += 1
    return result


def _parse_inline_dict(raw: str) -> dict[str, str]:
    """Parse a ``{ en: "x", ko: "y" }`` style inline dict."""
    inner = raw.strip("{}").strip()
    if not inner:
        return {}
    parts = _split_top_level_commas(inner)
    out: dict[str, str] = {}
    for part in parts:
        if ":" not in part:
            continue
        k, _, v = part.partition(":")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _split_top_level_commas(text: str) -> list[str]:
    """Split on commas, ignoring any inside quotes."""
    items: list[str] = []
    depth = 0
    in_str: str | None = None
    current: list[str] = []
    for ch in text:
        if in_str:
            current.append(ch)
            if ch == in_str and (not current or current[-2] != "\\"):
                in_str = None
            continue
        if ch in ('"', "'"):
            in_str = ch
            current.append(ch)
        elif ch == "{":
            depth += 1
            current.append(ch)
        elif ch == "}":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            items.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        items.append("".join(current).strip())
    return items


def _coerce_str_list(value: object) -> list[str]:
    """Coerce a parsed-YAML value to a list of strings.

    YAML list inputs are stringified element-wise; a non-empty scalar
    string becomes a single-element list; anything else (``None``, empty
    string, mapping, …) yields an empty list.

    Args:
        value: Arbitrary YAML value (list, str, or other).

    Returns:
        List of string elements, possibly empty.
    """
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str) and value:
        return [value]
    return []


def _title_for(meta: dict[str, object], lang: str) -> str:
    """Best-effort: title may be a dict (en/ko) or a string."""
    val = meta.get("title", "")
    if isinstance(val, dict):
        return str(val.get(lang, val.get("en", "")))
    return str(val) if val else ""


def _author_for(meta: dict[str, object]) -> str:
    """Best-effort author (en preferred)."""
    val = meta.get("author", "")
    if isinstance(val, dict):
        return str(val.get("en", val.get("ko", "")))
    return str(val) if val else ""


__all__ = [
    "NovelCatalog",
    "NovelEntry",
    "NovelFormat",
]
