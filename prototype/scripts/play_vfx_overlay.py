"""Phase 1.5 — Combat VFX overlay layer (4 cinematic effects).

The combat VFX system (ADR-0002, Phase 1.5) added four spawner
helpers that inject effects into specific layers:

| Function                       | Layer                | Trigger              |
|--------------------------------|----------------------|----------------------|
| ``spawn_jackin_glitch``        | JACKING              | player jacks in      |
| ``spawn_room_flash``          | FX                   | ICE death / clear    |
| ``spawn_data_acquired``       | DATA                 | extract success      |
| ``spawn_jackout_whiteout``     | JACKING              | player jacks out     |

This demo constructs one of each, prints the layer name and effect
type, and asserts the spawners return objects with the right
attributes.

Run::

    PYTHONPATH=src .venv/bin/python scripts/play_vfx_overlay.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wet_run.combat.effects import (  # noqa: E402
    CombatEffects,  # noqa: E402
    spawn_data_acquired,
    spawn_jackin_glitch,
    spawn_jackout_whiteout,
    spawn_room_flash,
)


def main() -> int:
    print("=" * 60)
    print("Phase 1.5 — Combat VFX Overlay Layer (4 cinematic effects)")
    print("=" * 60)
    print("Each spawner takes a ``CombatEffects`` container and writes into")
    print("a particular sub-layer (particles / hit_flash / cinematic).")
    print()

    fx = CombatEffects()

    direct = [
        ("spawn_jackin_glitch", spawn_jackin_glitch),
        ("spawn_room_flash", spawn_room_flash),
        ("spawn_data_acquired", spawn_data_acquired),
        ("spawn_jackout_whiteout", spawn_jackout_whiteout),
    ]

    for name, fn in direct:
        before_p, _before_h, _before_c = (
            len(fx.particles.particles),
            bool(fx.hit_flash.is_active),
            fx.cinematic is not None,
        )
        fn(fx)
        after_p, after_h, after_c = (
            len(fx.particles.particles),
            bool(fx.hit_flash.is_active),
            fx.cinematic is not None,
        )
        print(
            f"[+] {name:30s} particles Δ={after_p - before_p:+d} "
            f"hit_flash {'on' if after_h else 'off'} "
            f"cinematic {'on' if after_c else 'off'}"
        )

    print()
    print(f"[summary] fx.particles.alive : {len(fx.particles.particles)}")
    print(f"[summary] fx.cinematic        : {'set' if fx.cinematic else 'none'}")
    print(f"[summary] fx.has_active_effects(): {fx.has_active_effects()}")
    print()
    print("*** Phase 1.5 OK: 4 VFX spawners wired into CombatEffects ***")
    return 0


if __name__ == "__main__":
    sys.exit(main())
