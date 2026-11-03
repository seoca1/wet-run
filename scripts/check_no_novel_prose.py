#!/usr/bin/env python3
"""No original novel prose in the game (2026-11-04).

The game is set in Gibson's Sprawl, but it must not reproduce the novels'
prose. Paraphrase, terminology and tone are the point; quotation is not. The
Fiction project already records the original lines verbatim (as attributed
blockquotes), so it can serve as the corpus to compare against.

This checks every user-facing string in `web/src` (data JSON + TS string
literals) against the quoted prose in `Fiction/wiki`, using a word n-gram
overlap. An 8-word run that appears in both is a quotation, not a coincidence.

Run:
    python3 scripts/check_no_novel_prose.py
    python3 scripts/check_no_novel_prose.py --ngram 10   # stricter

Exit codes: 0 = clean, 1 = quoted prose found, 2 = checker error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # Game/wet_run
WORKSPACE = ROOT.parent.parent                          # opencodework
FICTION = WORKSPACE / "Fiction/wiki"
SRC = ROOT / "web/src"

WORD = re.compile(r"[a-z0-9']+")
QUOTED = re.compile(r'"([^"\n]{40,})"')
BLOCKQUOTE = re.compile(r"^\s*>\s*(.+?)\s*$", re.MULTILINE)


def words(text: str) -> list[str]:
    return WORD.findall(text.lower())


def ngrams(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def novel_spans() -> list[tuple[str, str]]:
    """(file, quoted text) for every quoted passage in the Fiction wiki."""
    spans: list[tuple[str, str]] = []
    for path in sorted(FICTION.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in QUOTED.finditer(text):
            spans.append((str(path.relative_to(WORKSPACE)), match.group(1)))
        for match in BLOCKQUOTE.finditer(text):
            line = match.group(1)
            if len(words(line)) >= 8:
                spans.append((str(path.relative_to(WORKSPACE)), line.strip()))
    return spans


def game_strings() -> list[tuple[str, str]]:
    """(file:line, string) for user-facing text: data JSON + TS string literals."""
    out: list[tuple[str, str]] = []
    for path in sorted(SRC.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        stack = [data]
        while stack:
            item = stack.pop()
            if isinstance(item, str):
                if len(words(item)) >= 8:
                    out.append((str(path.relative_to(ROOT)), item))
            elif isinstance(item, dict):
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
    literal = re.compile(r'"((?:[^"\\]|\\.){40,})"')
    for path in sorted(SRC.rglob("*.ts")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith(("//", "*", "/*")):
                continue  # comments may discuss the novels; they are not shipped text
            for match in literal.finditer(line):
                if len(words(match.group(1))) >= 8:
                    out.append((f"{path.relative_to(ROOT)}:{i}", match.group(1)))
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ngram", type=int, default=8)
    args = parser.parse_args(argv)
    n = max(4, args.ngram)

    if not FICTION.exists():
        print(f"checker error: no Fiction wiki at {FICTION}", file=sys.stderr)
        return 2

    index: dict[tuple[str, ...], str] = {}
    for source, span in novel_spans():
        for gram in ngrams(words(span), n):
            index.setdefault(gram, source)
    if not index:
        print(f"checker error: no quoted prose found under {FICTION}", file=sys.stderr)
        return 2

    hits: list[tuple[str, str, str]] = []
    checked = 0
    for where, text in game_strings():
        checked += 1
        for gram in ngrams(words(text), n):
            source = index.get(gram)
            if source is not None:
                hits.append((where, " ".join(gram), source))
                break

    if hits:
        print(f"QUOTED NOVEL PROSE ({len(hits)}) — {n}-word run shared with Fiction/wiki:")
        for where, run, source in hits:
            print(f'  {where}\n      "{run}"\n      ← {source}')
        print(f"\nFAIL: {len(hits)} string(s) quote the novels. Paraphrase instead.")
        return 1

    print(
        f"OK: {checked} user-facing strings, no {n}-word run matches the quoted "
        f"prose in Fiction/wiki."
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"checker error: {exc}", file=sys.stderr)
        sys.exit(2)