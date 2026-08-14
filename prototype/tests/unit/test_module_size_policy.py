"""ADR-0110 module size policy compliance test.

ADR-0110 (Accepted 2026-07-12) enforces a three-tier module size policy:

* 250 LOC: soft target for new modules (PR review checklist)
* 500 LOC: hard rejection threshold (700-800 LOC is the upper bound
  for one-off / single-use modules)
* 1000+ LOC: requires an ADR (justification + split plan OR hold
  rationale)

This test enforces the 1000+ LOC threshold by scanning every source
file under ``src/roguelike_sprawl/`` and asserting none exceeds
999 LOC. The threshold is the hard ceiling from ADR-0110 — files
over 999 LOC would mandate a follow-up ADR, and the existence of any
such file today would mean the policy is being violated.

Modules in :data:`KNOWN_OVERSIZE_MODULES` are explicitly exempted —
each entry corresponds to an ADR-0110 follow-up (ADR-0111, ADR-0112,
ADR-0113, ADR-0141, etc.) that justified retaining the file past the
threshold. The set should remain small and stable; add to it ONLY when
a new ADR is filed.

Phase 5+ module splits (ADR-0141, 0156, 0157, 0158, 0159, 0162) have
already broken every original 1000+ LOC file into compliant sub-modules,
so this set is currently empty. The test still serves as a regression
guard so a future large module is caught before PR merge.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).parent.parent.parent / "src" / "roguelike_sprawl"

# Files above 999 LOC that have been justified via ADR-0110 follow-up.
# Currently empty (Phase 5+ splits complete); keep as the regression
# guard anchor for future large modules.
KNOWN_OVERSIZE_MODULES: frozenset[str] = frozenset()

# ADR-0110 ceiling: a module of exactly 1000 LOC requires an ADR.
HARD_CEILING_LOC = 999


def _count_loc(path: Path) -> int:
    """Count physical lines (excluding blanks/comments — physical line count)."""
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _iter_python_files() -> list[Path]:
    """Yield every ``.py`` file under :data:`SRC_ROOT`, sorted by path."""
    return sorted(SRC_ROOT.rglob("*.py"))


def _over_threshold() -> list[tuple[str, int]]:
    """Return ``[(relative_path, loc), …]`` for files exceeding the ceiling."""
    out: list[tuple[str, int]] = []
    for path in _iter_python_files():
        loc = _count_loc(path)
        if loc > HARD_CEILING_LOC:
            out.append((str(path.relative_to(SRC_ROOT.parent.parent)), loc))
    return out


def test_no_module_exceeds_1000_loc_without_adr() -> None:
    """ADR-0110 §Consequences: 1000+ LOC modules require a follow-up ADR.

    Enforce the policy: every ``.py`` file under ``src/roguelike_sprawl/``
    must be at most 999 LOC unless exempted via a documented ADR. Failures
    here mean a new large module was added without going through the
    ADR-0110 process — file a follow-up ADR (ADR-0xxx) and either split
    the module or add it to :data:`KNOWN_OVERSIZE_MODULES` with rationale.
    """
    offending = [(rel, loc) for rel, loc in _over_threshold() if rel not in KNOWN_OVERSIZE_MODULES]
    assert not offending, (
        "ADR-0110 violation — modules over 999 LOC without documented ADR:\n"
        + "\n".join(f"  {rel}: {loc} LOC" for rel, loc in offending)
        + "\n\nEither:\n"
        "  1. Split the module (ADR-0110 preferred), OR\n"
        "  2. Add the file to KNOWN_OVERSIZE_MODULES with an ADR reference."
    )


@pytest.mark.parametrize(
    "rel_path",
    sorted(KNOWN_OVERSIZE_MODULES),
)
def test_known_oversize_module_still_justified(rel_path: str) -> None:
    """Sanity check: each entry in :data:`KNOWN_OVERSIZE_MODULES` still exists and is over the ceiling.

    Catches accidental module splits (the file shrinks under 999 LOC and
    should be removed from the exempt set) and missing files (a move or
    rename should update the set).
    """
    full = SRC_ROOT.parent.parent / rel_path
    if not full.exists():
        pytest.fail(
            f"KNOWN_OVERSIZE_MODULES entry {rel_path!r} not found — "
            "remove from the exempt set (file moved/renamed/deleted)."
        )
    loc = _count_loc(full)
    if loc <= HARD_CEILING_LOC:
        pytest.fail(
            f"KNOWN_OVERSIZE_MODULES entry {rel_path!r} has shrunk to {loc} LOC "
            f"(≤ {HARD_CEILING_LOC}) — remove from the exempt set; the file no "
            "longer needs ADR-0110 justification."
        )


def test_oversize_threshold_is_999_loc() -> None:
    """Defensive: the threshold constant itself matches ADR-0110 wording.

    ADR-0110 says ``1000+ LOC: 신규 ADR 필수``. The hard ceiling for
    *compliant* modules is therefore 999 LOC. If you change the
    constant, update this test and the docstring too.
    """
    assert HARD_CEILING_LOC == 999, (
        "HARD_CEILING_LOC must stay at 999 to match ADR-0110 wording "
        "(1000+ LOC triggers ADR requirement)."
    )
