#!/usr/bin/env python3
"""Find broken wikilinks in wet_run with file:line:target detail.

Cross-project resolution: per AGENTS.md §4.1, game wikilinks resolve first to
project-local files, then to the Fiction wiki cross-project reference
(../../Fiction/wiki/ from project root). Only flags wikilinks that resolve
to neither location.

Must be run from `Game/wet_run/` directory.
"""

import re
import sys
from pathlib import Path

ROOT = Path(".")
EXCLUDE = {
    ".git",
    "node_modules",
    ".obsidian",
    ".pytest_cache",
    "__pycache__",
    "_archive",
    "_inventory",
    ".venv",
    "prototype",
}

# AGENTS.md §4.1: cross-project Fiction wiki is the canonical reference for
# Gibson-canon characters/settings/concepts. Path is relative to project root.
FICTION_WIKI_ROOT = Path("..") / ".." / "Fiction" / "wiki"


def md_files():
    for p in ROOT.rglob("*.md"):
        if not any(e in p.parts for e in EXCLUDE):
            yield p


def strip(text):
    return re.sub(
        r"\A---\n.*?\n---\n",
        "",
        re.sub(r"`[^`]+`", "", re.sub(r"```.*?```", "", text, flags=re.DOTALL)),
        flags=re.DOTALL,
    )


WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
MDLINK = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)(?:#[^)]*)?\)")


def _build_fiction_stem_index() -> dict[str, Path]:
    """Index Fiction wiki files by stem (Obsidian-style vault-wide matching)."""
    if not FICTION_WIKI_ROOT.exists():
        return {}
    return {p.stem: p for p in FICTION_WIKI_ROOT.rglob("*.md")}


def _resolve(
    target_stem: str,
    source: Path,
    project_stems: dict[str, Path],
    fiction_stems: dict[str, Path],
) -> Path | None:
    """Resolve a wikilink target stem (Obsidian vault-wide + AGENTS.md §4.1).

    Resolution order:
    1. Project-local stem (vault-wide within project)
    2. Project-local relative to source file
    3. Cross-project Fiction wiki reference (AGENTS.md §4.1)
    """
    if target_stem in project_stems:
        return project_stems[target_stem]
    candidates = [source.parent / f"{target_stem}.md", source.parent / target_stem / "index.md"]
    for cand in candidates:
        try:
            if cand.resolve().exists():
                return cand
        except OSError:
            continue
    if target_stem in fiction_stems:
        return fiction_stems[target_stem]
    return None


def main():
    files = list(md_files())
    project_stems = {p.stem: p for p in files}
    fiction_stems = _build_fiction_stem_index()

    broken: list[tuple[str, int, str, str]] = []
    for f in files:
        txt = strip(f.read_text(errors="ignore"))
        lines = txt.splitlines()
        for i, line in enumerate(lines, 1):
            for m in WIKILINK.finditer(line):
                w = m.group(1).strip()
                if not w or w in {"wikilink", "...", "…"}:
                    continue
                if _resolve(w, f, project_stems, fiction_stems) is not None:
                    continue
                broken.append((str(f.relative_to(ROOT)), i, w, line.strip()[:100]))

    fiction_available = FICTION_WIKI_ROOT.exists()
    print(
        "=== BROKEN WIKILINKS (project-scoped + cross-project Fiction wiki per AGENTS.md §4.1) ===\n"
    )
    print(f"Cross-project Fiction wiki: {'resolved' if fiction_available else 'unavailable'}")
    print(f"Total broken: {len(broken)}\n")
    if not broken:
        print("(none)")
        return 0
    for f, ln, w, txt in broken:
        print(f"{f}:{ln}")
        print(f"  target: [[{w}]]")
        print(f"  text:   {txt}")
        print()
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
