"""Manifest (ADR-0061).

Maps story stems (and their mission ids) to the runtime hooks that
should fire when the player encounters that story.

Two ways to populate:

1. **Default mapping** — keywords in the story's text or mission
   synopsis suggest a primary hook kind (ICE-related text → COMBAT,
   data fragment keyword → ITEM, etc).  See ``infer_default_hook``.
2. **Explicit manifest** — supply a JSON file or Python dict to
   override the default and add *secondary* hooks.  This is the
   primary extension point: when an editor adds a new short story
   they can drop an entry into the manifest without touching any
   game code.

The manifest is intentionally a thin layer on top of the catalog
so artists can iterate without recompiling.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .catalog import NovelCatalog, NovelEntry
from .hooks import HookKind


@dataclass(slots=True)
class ManifestEntry:
    """One story's hook plan.

    Attributes:
        stem: The story stem this mapping applies to.
        primary: The principal hook kind (rendered first).
        secondary: Additional hooks fired alongside the primary.
        ice_kind: If the primary is COMBAT, the ICE tier to seed.
        item_id: If the primary is ITEM, the inventory key.
        mission_id: Optional explicit mission association; usually
            auto-derived from the mission whose ``story.source``
            matches ``stem``.
    """

    stem: str
    primary: HookKind = HookKind.NARRATIVE
    secondary: tuple[HookKind, ...] = ()
    ice_kind: str = "STANDARD"
    item_id: str = ""
    mission_id: str = ""

    def kinds(self) -> list[HookKind]:
        """All hook kinds fired for this entry, primary first."""
        return [self.primary, *self.secondary]


# Keywords for ``infer_default_hook``.  Order matters — first match wins.
_DEFAULT_KEYWORDS: tuple[tuple[str, HookKind, str], ...] = (
    ("ice barrier", HookKind.COMBAT, "BLACK"),
    ("black ice", HookKind.COMBAT, "BLACK"),
    ("tessier-ashpool", HookKind.COMBAT, "BLACK"),
    ("wolfgang", HookKind.COMBAT, "STANDARD"),
    ("ice patrol", HookKind.COMBAT, "STANDARD"),
    ("ice ", HookKind.COMBAT, "STANDARD"),  # trailing space prevents ICE keyword clash
    ("data fragment", HookKind.ITEM, ""),
    ("rom construct", HookKind.ITEM, ""),
    ("extract data", HookKind.ITEM, ""),
    ("dixie flatline", HookKind.EVENT, ""),
    ("molly", HookKind.EVENT, ""),
    ("construct", HookKind.EVENT, ""),
)


def infer_default_hook(text: str) -> tuple[HookKind, str]:
    """Infer a default hook from story text or mission synopsis.

    Args:
        text: Combined frontmatter + body excerpt, lower-cased by
            the caller.

    Returns:
        ``(kind, ice_kind)`` — ``ice_kind`` is meaningful only when
        ``kind`` is ``COMBAT``; for other kinds it is ``""``.
        Defaults to ``(HookKind.NARRATIVE, "")`` if nothing matches.
    """
    text = text.lower()
    for needle, kind, ice in _DEFAULT_KEYWORDS:
        if needle in text:
            return kind, ice
    return HookKind.NARRATIVE, ""


@dataclass(slots=True)
class NovelManifest:
    """Book of ``ManifestEntry`` records keyed by story stem.

    Supports JSON round-tripping so editors can maintain overrides
    without touching Python code:

        {
          "case_jackout-30sec": {
            "primary": "narrative",
            "secondary": ["excerpt", "cinematic"],
            "ice_kind": "STANDARD"
          },
          "first_jack": {
            "primary": "excerpt",
            "mission_id": "first_jack"
          }
        }
    """

    entries: dict[str, ManifestEntry] = field(default_factory=dict)

    def set(self, entry: ManifestEntry) -> None:
        """Insert or replace an entry keyed by ``entry.stem``."""
        self.entries[entry.stem] = entry

    def get(self, stem: str) -> ManifestEntry | None:
        """Look up an entry by stem, or ``None`` if absent."""
        return self.entries.get(stem)

    def __contains__(self, stem: object) -> bool:
        """Return ``True`` if a stem is registered as an entry."""
        return isinstance(stem, str) and stem in self.entries

    # ----- factory methods ------------------------------------------------

    @classmethod
    def from_catalog(
        cls,
        catalog: NovelCatalog,
        *,
        text_provider: TextProvider | None = None,
    ) -> NovelManifest:
        """Build a manifest by inferring hooks for every catalog entry.

        If a ``text_provider`` is supplied, the manifest's primary
        hook for each stem is set by ``infer_default_hook`` on the
        first paragraph of the story's English file.  Otherwise it
        defaults to ``NARRATIVE``.
        """
        manifest = cls()
        for entry in catalog:
            if text_provider is not None:
                text = text_provider.head(entry, lang="en", paragraphs=1)
                kind, ice = infer_default_hook(text)
            else:
                kind, ice = HookKind.NARRATIVE, "STANDARD"
            manifest.set(
                ManifestEntry(
                    stem=entry.stem,
                    primary=kind,
                    secondary=(),
                    ice_kind=ice if ice else "STANDARD",
                    mission_id=entry.game_integration
                    if isinstance(entry.game_integration, str)
                    else "",
                )
            )
        return manifest

    @classmethod
    def from_json(cls, path: Path) -> NovelManifest:
        """Load overrides from a JSON file.

        Unknown hook names raise ``ValueError`` so typos are caught
        at startup rather than silently ignored.
        """
        if not path.exists():
            return cls()
        raw = json.loads(path.read_text(encoding="utf-8"))
        manifest = cls()
        if not isinstance(raw, dict):
            raise ValueError("Manifest JSON must be a mapping")
        for stem, payload in raw.items():
            primary = HookKind(payload.get("primary", "narrative"))
            secondary_raw = payload.get("secondary", [])
            secondary = tuple(HookKind(s) for s in secondary_raw)
            manifest.set(
                ManifestEntry(
                    stem=stem,
                    primary=primary,
                    secondary=secondary,
                    ice_kind=payload.get("ice_kind", "STANDARD"),
                    item_id=payload.get("item_id", ""),
                    mission_id=payload.get("mission_id", ""),
                )
            )
        return manifest

    def to_json(self, path: Path) -> None:
        """Persist the manifest as JSON for editors."""
        out = {
            stem: {
                "primary": entry.primary.value,
                "secondary": [k.value for k in entry.secondary],
                "ice_kind": entry.ice_kind,
                "item_id": entry.item_id,
                "mission_id": entry.mission_id,
            }
            for stem, entry in sorted(self.entries.items())
        }
        path.write_text(
            json.dumps(out, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ----- resolution ----------------------------------------------------

    def resolve(self, stem: str) -> ManifestEntry:
        """Return the entry for ``stem``, falling back to a default.

        Always returns a ``ManifestEntry`` — never raises — so call
        sites do not have to handle a missing case.
        """
        entry = self.entries.get(stem)
        if entry is not None:
            return entry
        return ManifestEntry(
            stem=stem,
            primary=HookKind.NARRATIVE,
            secondary=(),
            ice_kind="STANDARD",
            item_id="",
            mission_id="",
        )

    def for_mission(self, mission_id: str) -> list[ManifestEntry]:
        """Return entries that explicitly bind to ``mission_id``."""
        return [e for e in self.entries.values() if e.mission_id == mission_id]


class TextProvider:
    """Read the head of a story's body without parsing all of it."""

    def head(
        self,
        entry: NovelEntry,
        *,
        lang: str = "en",
        paragraphs: int = 1,
    ) -> str:
        """Return the first ``paragraphs`` of ``entry`` in ``lang``."""
        path = entry.en_path if lang == "en" else entry.ko_path
        if path is None or not path.exists():
            return ""
        text = path.read_text(encoding="utf-8")
        # Skip frontmatter
        if text.startswith("---\n"):
            end = text.find("\n---\n", 4)
            if end > 0:
                text = text[end + 5 :]
        chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
        return "\n\n".join(chunks[:paragraphs])


__all__ = [
    "ManifestEntry",
    "NovelManifest",
    "TextProvider",
    "infer_default_hook",
]
