"""Visual demo of the Jockey Avatar system (ADR-0016).

Renders multiple avatar states side-by-side to show:
- HP variation (100% → 0%)
- Status variation (SAFE → FUTILE)
- Program tier variation (T1 → T5)
- Construct companion
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.avatar import (  # noqa: E402
    Status,
    build_avatar_state,
)
from wet_run.avatar.renderer import render_avatar_lines  # noqa: E402


def main() -> int:
    print("=" * 70)
    print("  JOCKEY AVATAR DEMO (ADR-0016)")
    print("=" * 70)
    print()

    scenarios = [
        (
            "Full Loadout (100% HP, SAFE)",
            build_avatar_state(
                hp=100,
                max_hp=100,
                ppl=25,
                zdr=2,
                programs=[("wisp", 5, False), ("hammer", 2, False), ("probe", 3, False)],
                deck_tier=4,
                wetware_tier=4,
                construct_id="dixie",
            ),
        ),
        (
            "Damaged (50% HP, TOUGH, wisp depleted)",
            build_avatar_state(
                hp=50,
                max_hp=100,
                ppl=25,
                zdr=20,
                programs=[("wisp", 1, True), ("hammer", 2, False), ("probe", 3, False)],
                deck_tier=4,
                wetware_tier=4,
                construct_id="dixie",
            ),
        ),
        (
            "Critical (25% HP, DEADLY, 1 program lost)",
            build_avatar_state(
                hp=25,
                max_hp=100,
                ppl=17,
                zdr=30,
                programs=[("hammer", 2, False), ("probe", 3, False)],
                deck_tier=4,
                wetware_tier=4,
                construct_id="dixie",
            ),
        ),
        (
            "Flatline (0% HP, DEAD)",
            build_avatar_state(
                hp=0,
                max_hp=100,
                ppl=25,
                zdr=20,
                programs=[("wisp", 5, False), ("hammer", 2, False), ("probe", 3, False)],
                deck_tier=4,
                wetware_tier=4,
                construct_id="dixie",
            ),
        ),
        (
            "Low Deck (T2, T2 wetware, no construct)",
            build_avatar_state(
                hp=80,
                max_hp=100,
                ppl=10,
                zdr=8,
                programs=[("wisp", 1, False), ("shield", 2, False)],
                deck_tier=2,
                wetware_tier=2,
                construct_id=None,
            ),
        ),
        (
            "Loa companion (mid HP)",
            build_avatar_state(
                hp=70,
                max_hp=100,
                ppl=15,
                zdr=12,
                programs=[("wisp", 3, False), ("hammer", 2, False), ("shield", 1, False)],
                deck_tier=3,
                wetware_tier=3,
                construct_id="loa",
            ),
        ),
    ]

    for title, state in scenarios:
        print(f"--- {title} ---")
        print(f"  HP: {state.hp}/{state.max_hp}  Status: {state.status.value.upper()}")
        rendered = render_avatar_lines(state)
        # Frame
        width = max(len(t) for t, _ in rendered.lines)
        print(f"  {'=' * (width + 2)}")
        for text, _color in rendered.lines:
            print(f"  {text}")
        print(f"  {'=' * (width + 2)}")
        print()

    # Status-only reference
    print("=" * 70)
    print("  STATUS POSES (reference)")
    print("=" * 70)
    print()
    for status in Status:
        print(f"  {status.value.upper():8s} - body: ", end="")
        # Render a simple state at this status
        # Adjust PPL/ZDR to force the status
        if status is Status.SAFE:
            state = build_avatar_state(hp=100, max_hp=100, ppl=20, zdr=5)
        elif status is Status.MATCH:
            state = build_avatar_state(hp=100, max_hp=100, ppl=10, zdr=10)
        elif status is Status.TOUGH:
            state = build_avatar_state(hp=100, max_hp=100, ppl=10, zdr=15)
        elif status is Status.DEADLY:
            state = build_avatar_state(hp=40, max_hp=100, ppl=5, zdr=20)
        else:  # FUTILE
            state = build_avatar_state(hp=10, max_hp=100, ppl=2, zdr=30)
        rendered = render_avatar_lines(state)
        # Print body lines (1 and 3)
        print(
            f"shoulders={rendered.lines[1][0].strip()!r:8s}  hips={rendered.lines[3][0].strip()!r}"
        )
    print()

    # Tier reference
    print("=" * 70)
    print("  PROGRAM TIERS (reference)")
    print("=" * 70)
    print()
    for tier in range(1, 6):
        state = build_avatar_state(
            hp=100,
            max_hp=100,
            ppl=10,
            zdr=5,
            programs=[("wisp", tier, False)],
        )
        rendered = render_avatar_lines(state)
        prog_text = rendered.lines[2][0].strip()
        tier_name = {
            1: "T1 (Wisp)",
            2: "T2 (Hammer)",
            3: "T3 (Goliath)",
            4: "T4 (Wardrone)",
            5: "T5 (Kraken)",
        }[tier]
        print(f"  {tier_name:18s}  {prog_text}")
    print()

    print("=" * 70)
    print("  All avatar states rendered successfully!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
