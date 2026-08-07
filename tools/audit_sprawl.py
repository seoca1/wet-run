#!/usr/bin/env python3
"""Project-scoped audit for Game/roguelike_sprawl/ — wikilink integrity check.

Includes cross-project Fiction wiki resolution per AGENTS.md §4.1.
"""

import re
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(".").resolve()
EXCLUDE = {".git", "node_modules", ".obsidian", ".pytest_cache", "__pycache__", "_archive", "_inventory", ".venv"}

# AGENTS.md §4.1: cross-project Fiction wiki is the canonical reference for
# Gibson-canon characters/settings/concepts. Path is relative to project root.
FICTION_WIKI_ROOT = Path("..") / ".." / "Fiction" / "wiki"


def md_files():
    for p in ROOT.rglob("*.md"):
        if not any(e in p.parts for e in EXCLUDE):
            yield p


def strip(text):
    return re.sub(r"\A---\n.*?\n---\n", "", re.sub(r"`[^`]+`", "", re.sub(r"```.*?```", "", text, flags=re.DOTALL)), flags=re.DOTALL)


def obsidian_slug(title):
    s = title.strip().lower()
    s = re.sub(r"[\[\]\(\)\*_`]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s


def _build_fiction_stem_index() -> dict[str, Path]:
    """Index Fiction wiki files by stem (Obsidian-style vault-wide matching)."""
    if not FICTION_WIKI_ROOT.exists():
        return {}
    return {p.stem: p for p in FICTION_WIKI_ROOT.rglob("*.md")}


def main():
    files = [p.resolve() for p in md_files()]
    fiction_stems = _build_fiction_stem_index()
    anchor_index = {}
    for p in files:
        for m in re.finditer(r"^(#{1,6})\s+(.+?)\s*$", p.read_text(errors="ignore"), re.MULTILINE):
            title = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", m.group(2).strip()).replace("`", "")
            a = obsidian_slug(title)
            if a:
                anchor_index.setdefault(a, p)

    stems = {p.stem: p for p in files}
    WIKILINK = re.compile(r"(?<!`)\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
    MDLINK = re.compile(r"\[([^\]]+)\]\(([^\)]+\.md)(?:#[^\)]*)?\)")

    cats = defaultdict(list)
    broken = 0
    inbound = defaultdict(set)

    for f in files:
        txt = strip(f.read_text(errors="ignore"))
        for m in WIKILINK.finditer(txt):
            w = m.group(1).strip()
            if not w or w in {"wikilink", "...", "…"} or "{" in w or "}" in w:
                continue
            try:
                ok = (f.parent / (w + ".md")).resolve().exists()
            except Exception:
                ok = False
            if not ok:
                ok = w in stems
            if not ok:
                ok = w in fiction_stems
            if not ok and w in anchor_index:
                ok = True
            if ok:
                resolved = (f.parent / (w + ".md")).resolve() if (f.parent / (w + ".md")).exists() else stems.get(w, fiction_stems.get(w, anchor_index.get(w)))
                if resolved and resolved != f:
                    inbound[resolved].add(f)
                continue
            broken += 1
            if "/" in w or w.startswith("../"):
                cat = "PATH"
            elif any('\uac00' <= c <= '\ud7a3' for c in w):
                cat = "KR-word"
            elif any('\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff' for c in w):
                cat = "JP/CJK-word"
            elif ' ' in w:
                cat = "multi-word"
            elif w.startswith("\\"):
                cat = "regex-backref-artifact"
            else:
                cat = "OTHER"
            cats[cat].append((f.relative_to(ROOT), w))
        for m in MDLINK.finditer(txt):
            target = m.group(2)
            if "://" in target or target.startswith(("mailto:", "tel:", "ftp:")):
                continue
            target_path = (f.parent / target).resolve()
            if target_path.exists():
                inbound[target_path].add(f)
            else:
                broken += 1
                cats["PATH"].append((f.relative_to(ROOT), target))

    wiki_files = [p for p in files if "wiki/" in str(p)]
    orphans = [p for p in wiki_files if not inbound.get(p) and p.name != "index.md"]

    print(f"=== ROGUELIKE_SPRAWL PROJECT AUDIT ===\n")
    print(f"Total .md files scanned: {len(files)}")
    print(f"Wiki files: {len(wiki_files)}")
    print(f"Broken links: {broken}")
    print(f"Wiki orphans: {len(orphans)}\n")

    print("--- BROKEN LINKS BY CATEGORY ---")
    for cat, items in sorted(cats.items(), key=lambda x: -len(x[1])):
        print(f"\n{cat} ({len(items)}):")
        for f, w in Counter(i[1] for i in items).most_common(5):
            count = sum(1 for x in items if x[1] == w)
            print(f"  {count:3}  [[{w}]]")

    print("\n--- ORPHAN WIKI PAGES ---")
    for p in sorted(orphans)[:20]:
        print(f"  {p.relative_to(ROOT)}")
    if len(orphans) > 20:
        print(f"  ... +{len(orphans) - 20} more")


if __name__ == "__main__":
    main()
