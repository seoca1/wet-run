"""Headless verification of boss phase indicator rendering.

Per .omo/plans/wet-run-ui-visibility-upgrade.md T2.1.

Verifies engine/combat_view_render.py:285-302:

    phase_str = f"PHASE {progress.phase_index + 1}/{tracker.total_phases}"

renders correctly for the 3 F.4 bosses that use BossPhaseTracker
(neuromancer / loa_baron / black_baron) and that the render path cleanly
skips the phase block when no tracker is present (wintermute /
ta_construct_prime — handled directly in combat/boss.py).

The library test suite (tests/unit/test_boss_phase_tracker.py + tests/unit/
test_f4_boss_phase_combat.py, 130 tests) covers tracker data + combat
integration. This script locks the RENDER PATH itself: the actual
console buffer must contain ``PHASE N/M`` at the expected row/col.

Usage:
    uv run python scripts/boss_phase_indicator_check.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import tcod.console  # type: ignore[import-untyped]

# Make the package importable when run from anywhere (mirrors combat_status_overlay_check.py)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from wet_run.combat.boss_expansion import (  # noqa: E402
    BLACK_BARON_PROFILE,
    LOA_BARON_PROFILE,
    NEUROMANCER_PROFILE,
)
from wet_run.combat.boss_phase_tracker import (  # noqa: E402
    BossPhaseTracker,
    get_black_baron_tracker,
    get_loa_baron_tracker,
    get_neuromancer_tracker,
    get_phase_count_for_boss,
)
from wet_run.combat.state import CombatState  # noqa: E402
from wet_run.combat.state_models import Combatant  # noqa: E402
from wet_run.engine.combat_view_render import _draw_combatants  # noqa: E402
from wet_run.engine.layout import Region, RegionId  # noqa: E402

# Enemy portrait starts at (main.x + main.w - 25, main.y + 2). With the
# default test region (0, 0, 80, 30), portrait draws at row 2, name row 3,
# HP text row 4, hp_bar row 5, phase_str row 6, NEXT row 7, ATK row 8.
PHASE_ROW = 6
NEXT_ROW = 7
ENEMY_X = 55  # 0 + 80 - 25


def _make_player() -> Combatant:
    return Combatant(
        id="player",
        name="Hero",
        portrait="@",
        color=(255, 255, 255),
        hp=80,
        max_hp=100,
        ap=5,
        max_ap=10,
        auto_attack_damage=10,
        skills=(),
        team="player",
        ice_kind="standard",
    )


def _make_boss(hp: int, max_hp: int, name: str, ice_kind: str) -> Combatant:
    return Combatant(
        id=ice_kind,
        name=name,
        portrait="*",
        color=(255, 0, 100),
        hp=hp,
        max_hp=max_hp,
        ap=0,
        max_ap=0,
        auto_attack_damage=20,
        skills=(),
        team="enemy",
        ice_kind=ice_kind,
        current_phase=1,
    )


def _make_console(width: int = 80, height: int = 50) -> tcod.console.Console:
    return tcod.console.Console(width=width, height=height)


def _decode_row(console: tcod.console.Console, y: int, x_start: int, x_end: int) -> str:
    """Decode the unicode codepoints in row ``y``, cols ``[x_start, x_end)``."""
    cells = console.ch[y][x_start:x_end].tolist()
    return "".join(chr(c) if c != 0 else " " for c in cells)


def _verify_tracker_render(
    boss_label: str,
    profile,
    tracker_factory,
    total_phases: int,
    failures: list[str],
) -> None:
    """Happy path: tracker set → phase_str renders at (ENEMY_X, PHASE_ROW)."""
    console = _make_console()
    region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
    player = _make_player()
    enemy = _make_boss(hp=400, max_hp=400, name=boss_label, ice_kind=profile.id)
    cs = CombatState(player=player, enemy=enemy)
    tracker = tracker_factory()
    cs.boss_phase_tracker = tracker
    cs.phase_change_ms = 0
    _draw_combatants(console, region, cs)

    expected = f"PHASE 1/{total_phases}"
    row_text = _decode_row(console, PHASE_ROW, ENEMY_X, ENEMY_X + len(expected) + 2)
    if expected not in row_text:
        failures.append(
            f"[{boss_label}] phase 1 render: expected {expected!r} in row {PHASE_ROW} "
            f"at x={ENEMY_X}, got {row_text!r}"
        )
        return

    # Transition to phase 2 → re-render and verify
    tracker.transition()
    enemy.current_phase = 2
    console2 = _make_console()
    cs2 = CombatState(player=player, enemy=enemy)
    cs2.boss_phase_tracker = tracker
    cs2.phase_change_ms = 0
    _draw_combatants(console2, region, cs2)
    expected2 = f"PHASE 2/{total_phases}"
    row_text2 = _decode_row(console2, PHASE_ROW, ENEMY_X, ENEMY_X + len(expected2) + 2)
    if expected2 not in row_text2:
        failures.append(
            f"[{boss_label}] phase 2 render: expected {expected2!r} in row {PHASE_ROW} "
            f"at x={ENEMY_X}, got {row_text2!r}"
        )

    # Phase 1 is NOT last → NEXT row must contain "NEXT:" prefix
    next_text = _decode_row(console, NEXT_ROW, ENEMY_X, ENEMY_X + 20)
    if "NEXT:" not in next_text:
        failures.append(
            f"[{boss_label}] phase 1 NEXT render: expected 'NEXT:' in row {NEXT_ROW}, "
            f"got {next_text!r}"
        )


def _verify_no_tracker_skip(failures: list[str]) -> None:
    """Failure path: tracker is None (wintermute / ta_construct_prime).
    Render must cleanly skip the phase block — no orphan PHASE str at row 6.
    """
    console = _make_console()
    region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
    player = _make_player()
    # Wintermute / ta_construct_prime — phase logic lives in combat/boss.py
    # and is NOT exposed via BossPhaseTracker. boss_phase_tracker stays None.
    enemy = _make_boss(hp=400, max_hp=400, name="Wintermute", ice_kind="wintermute")
    cs = CombatState(player=player, enemy=enemy)
    assert cs.boss_phase_tracker is None, "Pre-condition: tracker must default to None"
    _draw_combatants(console, region, cs)

    # Row 6 must NOT contain "PHASE" — the block was cleanly skipped.
    row_text = _decode_row(console, PHASE_ROW, 0, 80)
    if "PHASE" in row_text:
        failures.append(
            f"[no-tracker] orphan PHASE str at row {PHASE_ROW} when tracker is None: {row_text!r}"
        )

    # ATK line must still render normally below (smoke: no crash, layout intact)
    atk_row = _decode_row(console, PHASE_ROW, 0, 80)
    if "ATK:" not in atk_row:
        failures.append(f"[no-tracker] ATK line missing at row {PHASE_ROW}: {atk_row!r}")


def main() -> int:
    failures: list[str] = []

    # Happy: 3 tracker bosses
    _verify_tracker_render(
        "neuromancer",
        NEUROMANCER_PROFILE,
        get_neuromancer_tracker,
        total_phases=get_phase_count_for_boss("neuromancer"),
        failures=failures,
    )
    _verify_tracker_render(
        "loa_baron",
        LOA_BARON_PROFILE,
        get_loa_baron_tracker,
        total_phases=get_phase_count_for_boss("loa_baron"),
        failures=failures,
    )
    _verify_tracker_render(
        "black_baron",
        BLACK_BARON_PROFILE,
        get_black_baron_tracker,
        total_phases=get_phase_count_for_boss("black_baron"),
        failures=failures,
    )

    # Failure: tracker=None → clean skip
    _verify_no_tracker_skip(failures)

    # Also exercise direct BossPhaseTracker(profile) construction (no getter)
    # to lock that profile-driven instantiation renders correctly.
    console = _make_console()
    region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
    player = _make_player()
    enemy = _make_boss(hp=400, max_hp=400, name="neuromancer", ice_kind="neuromancer")
    cs = CombatState(player=player, enemy=enemy)
    cs.boss_phase_tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
    cs.phase_change_ms = 0
    _draw_combatants(console, region, cs)
    if "PHASE 1/" not in _decode_row(console, PHASE_ROW, 0, 80):
        failures.append(
            f"[direct BossPhaseTracker(profile)] expected PHASE 1/ render at row "
            f"{PHASE_ROW}: {_decode_row(console, PHASE_ROW, 0, 80)!r}"
        )

    if failures:
        print("FAIL:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print(
        "PASS: boss phase indicator renders for 3 F.4 bosses; cleanly skipped for non-tracker bosses"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
