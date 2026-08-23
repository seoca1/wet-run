"""Headless verification of status-effect overlay icons on enemy portrait.

Per .omo/plans/wet-run-ui-visibility-upgrade.md T1.4.

Verifies combat/battle_portraits.py:get_status_overlay() composes correct
glyph suffixes for the 5 status effects (burn / stun / slow / silence /
vulnerable), and that get_portrait() integrates the overlay into the
BattlePortrait suffix for the render loop at engine/combat_view_render.py:265.

Glyphs are taken verbatim from battle_portraits.py:106-119 and locked against
the library test suite (tests/unit/test_battle_portraits.py, 30 tests).

Usage:
    uv run python scripts/combat_status_overlay_check.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the package importable when run from anywhere (mirrors combat_effects_demo.py)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from wet_run.combat.battle_portraits import get_portrait, get_status_overlay  # noqa: E402

# Glyph mapping — sourced from get_status_overlay() at
# prototype/src/wet_run/combat/battle_portraits.py:106-119.
EXPECTED_GLYPHS: dict[str, str] = {
    "burn": "^",
    "stun": "~",
    "slow": "...",
    "silence": "X",
    "vulnerable": "!",
}


def main() -> int:
    failures: list[str] = []

    # Happy: empty status list -> empty suffix (no spurious chars)
    result = get_status_overlay(())
    if result != "":
        failures.append(f"Empty status list should return empty string, got {result!r}")

    # Happy: each individual effect produces its glyph
    for sid, expected_glyph in EXPECTED_GLYPHS.items():
        result = get_status_overlay((sid,))
        if result != expected_glyph:
            failures.append(f"Single effect {sid!r}: expected {expected_glyph!r}, got {result!r}")

    # Happy: all 5 effects combined -> all glyphs present in composed suffix
    all_effects: tuple[str, ...] = tuple(EXPECTED_GLYPHS.keys())
    combined = get_status_overlay(all_effects)
    for sid, expected_glyph in EXPECTED_GLYPHS.items():
        if expected_glyph not in combined:
            failures.append(
                f"All effects combined missing {sid!r} glyph {expected_glyph!r} in {combined!r}"
            )

    # Failure: invalid effect_id -> graceful skip (no crash, no glyph)
    try:
        result = get_status_overlay(("nonexistent_effect",))
        if result != "":
            failures.append(f"Invalid effect_id should produce empty overlay, got {result!r}")
    except Exception as e:
        failures.append(f"Invalid effect_id should not crash, got {type(e).__name__}: {e}")

    # Full render integration: get_portrait() with full status set wires overlay
    # into BattlePortrait.suffix as " [<overlay>]". This is what
    # engine/combat_view_render.py:265 prints to the console.
    try:
        portrait = get_portrait(
            ice_type="watchdog",
            hp_ratio=1.0,
            status_effect_ids=all_effects,
            phase=1,
        )
        if not portrait.effect_overlay:
            failures.append("get_portrait().effect_overlay is empty for full status set")
        if (
            "[^" not in portrait.suffix
            or "..." not in portrait.suffix
            or "!]" not in portrait.suffix
        ):
            failures.append(
                f"get_portrait().suffix missing expected overlay brackets, got {portrait.suffix!r}"
            )
    except Exception as e:
        failures.append(
            f"get_portrait should not crash with full status set: {type(e).__name__}: {e}"
        )

    # Edge: no statuses -> empty suffix (render loop shows no overlay)
    try:
        portrait = get_portrait(ice_type="watchdog", hp_ratio=1.0)
        if portrait.effect_overlay != "" or portrait.suffix != "":
            failures.append(
                f"get_portrait() with no statuses should produce empty overlay, got "
                f"effect_overlay={portrait.effect_overlay!r} suffix={portrait.suffix!r}"
            )
    except Exception as e:
        failures.append(f"get_portrait with no statuses should not crash: {type(e).__name__}: {e}")

    if failures:
        print("FAIL:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print("PASS: all overlays rendered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
