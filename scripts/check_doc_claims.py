#!/usr/bin/env python3
"""AGENTS.md claim checker — docs must not drift from the tree.

Why this exists (2026-11-04): the project guide claimed "130 ADRs, 0001–0213"
and "107 files, 2654 tests" while the repository held 185 ADRs (max 266) and
182 test files / 4021 tests, and 17 of the 27 paths it named did not exist —
including every `Fiction/wiki` link, which was one directory level off. The
workspace link audit reported CLEAN throughout, because it resolves wikilinks
and stems, not plain paths, and nothing compared a number in prose to a number
in the repository.

So this checks two things and exits non-zero on either:

  paths    every backticked path in the guide must exist, resolved relative to
           the guide itself
  claims   named counts (ADR count and range, test files, test count) must
           equal what the repository measures

Run:
    python3 scripts/check_doc_claims.py            # fast: no test run
    python3 scripts/check_doc_claims.py --tests    # also run vitest to count

Exit codes: 0 = every claim holds, 1 = drift found, 2 = checker error.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "AGENTS.md"
ADR_DIR = ROOT / "docs/wiki/decisions"
TESTS_DIR = ROOT / "web/tests"

# Tokens that are documentation, not checkable paths.
SKIP_PREFIXES = ("http://", "https://", "mailto:", "tel:", "ftp:")


FENCE = re.compile(r"```.*?```", re.DOTALL)
# Words that mark a line as *describing* a path that no longer exists ("raw/ was
# retired"), as opposed to telling the reader to use it. Those are history, not
# instructions, so they warn instead of failing -- but they are still reported,
# because a stale name in a guide is how the next reader gets lost.
RETIRED_MARKERS = (
    "삭제",
    "제거",
    "retired",
    "잔재",
    "없다",
    "없음",
    "이전",
    "과거",
    "historical",
    "was removed",
    "no longer",
)


def inline_paths(text: str) -> list[tuple[str, int]]:
    """Backticked path tokens outside fenced code, with their line numbers."""
    prose = FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    found: list[tuple[str, int]] = []
    for match in re.finditer(r"`([^`\n]+)`", prose):
        token = match.group(1).strip()
        if not token or " " in token:
            continue
        if token.startswith(SKIP_PREFIXES):
            continue
        if any(ch in token for ch in "*{}<>$|"):
            continue
        if "..." in token:  # a deliberately elided path, not a real one
            continue
        if "/" not in token and not re.search(r"\.[a-z]{1,5}$", token):
            continue
        line = prose.count("\n", 0, match.start()) + 1
        found.append((token, line))
    return sorted(set(found))


def resolve_any(guide: Path, token: str) -> bool:
    """A path may be written relative to the guide, the project, or the workspace."""
    candidates = [guide.parent, ROOT, ROOT.parent.parent]
    return any((base / token).exists() for base in candidates)


# Names the guide keeps on purpose because it is describing removals. Each one
# needs a reason: an entry here is a claim that "this name is history, not an
# instruction". Adding one is a deliberate act, which is the point -- a new
# stale path fails the check instead of blending into a big warning list.
# Section-level guessing was tried and was wrong: the Fiction chapter contains
# the word "이전" (older works) and swallowed every broken Fiction link with it.
HISTORICAL_NAMES = {
    "raw/": "prototype-era input tree, retired 2026-09-15",
    "wiki/": "prototype-era wiki, moved to docs/wiki/",
    "world/": "prototype-era world dir, moved to docs/wiki/world/",
    "lore/": "prototype-era lore dir, moved to docs/wiki/lore/",
    "story/": "prototype-era story dir",
    "matrix/": "prototype-era ECS domain dir",
    "design/": "prototype-era design dir, moved to docs/design/",
    "testcases/": "prototype-era testcase dir, moved to docs/testcases/",
    "prototype/": "retired Python prototype",
    "engine/state.py": "retired Python prototype",
    "engine/dungeon_view.py": "retired Python prototype",
    "dashboard/": "moved to docs/dashboard/",
    "data/": "deleted 2026-10-20",
    "docs/wiki/design/": "duplicate removed 2026-10-20",
    "Game/wet_run/wiki/world/": "pre-move path, quoted as history",
    "Game/wet_run/dashboard/stories/": "pre-move path, quoted as history",
    "Projects/Fiction/wiki/": "pre-move path, quoted as history",
}


def is_historical(token: str, lines: list[str], line_no: int) -> bool:
    if token in HISTORICAL_NAMES:
        return True
    local = " ".join(lines[max(0, line_no - 3) : line_no])
    return any(marker in local for marker in RETIRED_MARKERS)


def check_paths(guide: Path, text: str) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """Returns (dead, historical) path references."""
    lines = text.splitlines()
    dead: list[tuple[str, int]] = []
    historical: list[tuple[str, int]] = []
    for token, line in inline_paths(text):
        if resolve_any(guide, token):
            continue
        if is_historical(token, lines, line):
            historical.append((token, line))
        else:
            dead.append((token, line))
    return dead, historical


def measure_adrs() -> dict[str, int]:
    files = [p for p in ADR_DIR.glob("*.md") if re.match(r"^\d{4}-", p.name)]
    ids = sorted(int(p.name[:4]) for p in files)
    if not ids:
        raise RuntimeError(f"no ADR files under {ADR_DIR}")
    return {"count": len(ids), "min": ids[0], "max": ids[-1]}


def adr_files() -> list[Path]:
    return sorted(p for p in ADR_DIR.glob("*.md") if re.match(r"^\d{4}-", p.name))


def check_adr_namespace() -> tuple[list[str], list[str], list[str]]:
    """(failures, warnings, notes) for the ADR namespace.

    Fails on the two things that are mechanically fixable and unambiguous: an
    ADR file outside the canonical directory, and an index that disagrees with
    the file set. Duplicate IDs only warn -- renumbering an Accepted ADR breaks
    every citation to it, so that is an owner decision, not a check.
    """
    failures: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []
    files = adr_files()
    ids: dict[int, list[str]] = {}
    for path in files:
        ids.setdefault(int(path.name[:4]), []).append(path.name)

    # Evidence sidecars share their ADR's number on purpose; they are not dupes.
    real = {
        i: [n for n in names if "-evidence.md" not in n]
        for i, names in ids.items()
    }
    dupes = {i: names for i, names in real.items() if len(names) > 1}
    for i, names in sorted(dupes.items()):
        warnings.append(f"{i:04d}: {len(names)} ADRs share the number — " + ", ".join(names))

    sidecars = sorted(n for names in ids.values() for n in names if "-evidence.md" in n)
    if sidecars:
        warnings.append(
            f"{len(sidecars)} evidence sidecar(s) live in the ADR namespace "
            "(e.g. 0266-evidence.md would read as a second ADR 0266)"
        )

    # Canonical location: nothing that looks like an ADR may live outside it.
    strays = [
        p
        for p in ROOT.rglob("*.md")
        if re.match(r"^(ADR-)?\d{4}-", p.name) and ADR_DIR not in p.parents
    ]
    for p in strays:
        failures.append(f"ADR outside {ADR_DIR.relative_to(ROOT)}/: {p.relative_to(ROOT)}")

    # Index parity.
    index = (ADR_DIR / "README.md").read_text(encoding="utf-8")
    rows = {int(m.group(1)) for m in re.finditer(r"^\|\s*(\d{4})\s*\|", index, re.MULTILINE)}
    file_ids = {int(p.name[:4]) for p in files}
    for missing in sorted(file_ids - rows):
        failures.append(f"ADR {missing:04d} has a file but no index row")
    for ghost in sorted(rows - file_ids):
        failures.append(f"index row {ghost:04d} has no file")

    gaps = [i for i in range(min(file_ids), max(file_ids) + 1) if i not in file_ids]
    notes.append(
        f"{len(files)} ADR files, IDs {min(file_ids)}-{max(file_ids)}, "
        f"{len(gaps)} unused numbers (gaps are allowed; they are not reuse of an ID)"
    )
    return failures, warnings, notes


def measure_test_files() -> int:
    return len(list(TESTS_DIR.glob("*.test.ts")))


def measure_tests() -> int | None:
    """Run vitest and count. Slow, so only with --tests."""
    proc = subprocess.run(
        [
            "npx",
            "vitest",
            "run",
            "--reporter=json",
            "--outputFile=/tmp/wetrun_vitest.json",
        ],
        cwd=ROOT / "web",
        capture_output=True,
        text=True,
        timeout=1800,
    )
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"vitest failed: {proc.stderr[-400:]}")
    data = json.loads(Path("/tmp/wetrun_vitest.json").read_text(encoding="utf-8"))
    return int(data["numTotalTests"])


def is_vitest_line(line: str) -> bool:
    """Only vitest/npm-test lines carry the project's test counts. The guide
    also quotes prototype-era Python counts ("# 40 tests" under tests/unit/),
    which are history and must not be read as the current suite."""
    return "vitest" in line or "npm test" in line


# (label, regex, measurement description, resolver, line filter)
def claim_checks(
    with_tests: bool,
) -> list[tuple[str, re.Pattern[str], str, callable, callable]]:
    adrs = measure_adrs()
    checks: list[tuple[str, re.Pattern[str], str, callable, callable]] = [
        (
            "ADR count",
            re.compile(r"(\d+)(\+?)\s+ADRs"),
            "ADR files",
            lambda: adrs["count"],
            lambda line: True,
        ),
        (
            "ADR range",
            re.compile(r"0001\s*[–-]\s*(\d{4})"),
            "highest ADR number",
            lambda: adrs["max"],
            lambda line: True,
        ),
        (
            "test files",
            re.compile(r"(\d+)(\+?)\s+(?:vitest\s+)?(?:files|파일)"),
            "web/tests/*.test.ts",
            measure_test_files,
            is_vitest_line,
        ),
    ]
    if with_tests:
        checks.append(
            (
                "test count",
                re.compile(r"(\d+)(\+?)\s+tests?"),
                "vitest numTotalTests",
                measure_tests,
                is_vitest_line,
            )
        )
    return checks


def check_claims(text: str, with_tests: bool) -> list[tuple[str, str, str, int]]:
    """Returns (label, claimed, measured, line) for each mismatch."""
    drift: list[tuple[str, str, str, int]] = []
    lines = text.splitlines()
    for label, pattern, what, resolver, keep in claim_checks(with_tests):
        measured = resolver()
        for match in pattern.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            if not keep(lines[line_no - 1] if line_no <= len(lines) else ""):
                continue
            claimed = int(match.group(1))
            floor = match.lastindex is not None and match.lastindex >= 2 and match.group(2) == "+"
            # "180+ files" is a floor: growth keeps the claim true, shrinkage
            # fails it. Exact counts are checked exactly.
            if floor:
                if claimed > int(measured):
                    drift.append((label, f"{claimed}+", f"{measured} ({what})", line_no))
            elif claimed != int(measured):
                drift.append((label, str(claimed), f"{measured} ({what})", line_no))
    return drift


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", action="store_true", help="also run vitest to count tests")
    parser.add_argument("--guide", default=str(GUIDE), help="guide to check")
    args = parser.parse_args(argv)

    guide = Path(args.guide)
    if not guide.exists():
        print(f"checker error: no guide at {guide}", file=sys.stderr)
        return 2
    text = guide.read_text(encoding="utf-8")

    missing, historical = check_paths(guide, text)
    drift = check_claims(text, args.tests)
    ns_failures, ns_warnings, ns_notes = check_adr_namespace()

    if historical:
        print(f"HISTORICAL NAMES ({len(historical)}) — described as retired, not on disk (warn only):")
        for token, line in historical:
            print(f"  line {line}: {token}")
        print()
    if missing:
        print(f"DEAD PATHS ({len(missing)}) — named in {guide.name}, not on disk:")
        for token, line in missing:
            print(f"  line {line}: {token}")
    if drift:
        print(f"\nNUMBER DRIFT ({len(drift)}) — claimed vs measured:")
        for label, claimed, measured, line in drift:
            print(f"  line {line}: {label}: claimed {claimed}, measured {measured}")

    if ns_warnings:
        print(f"ADR NAMESPACE WARNINGS ({len(ns_warnings)}) — need an owner decision, not a fix:")
        for w in ns_warnings:
            print("  " + w)
        print()
    if ns_notes:
        for note in ns_notes:
            print("ADR namespace: " + note)
        print()

    if missing or drift or ns_failures:
        if ns_failures:
            print(f"ADR NAMESPACE FAILURES ({len(ns_failures)}):")
            for f in ns_failures:
                print("  " + f)
            print()
        print(
            f"FAIL: {len(missing)} dead path(s), {len(drift)} number claim(s) drifted, "
            f"{len(ns_failures)} namespace failure(s)."
        )
        return 1
    checked = len(inline_paths(text))
    suffix = "" if args.tests else " (test count not checked: pass --tests)"
    print(f"OK: {checked} paths resolve; every checked count matches.{suffix}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as exc:  # checker error, not a documentation verdict
        print(f"checker error: {exc}", file=sys.stderr)
        sys.exit(2)