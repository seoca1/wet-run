"""Visual verification demo for combat VFX.

Simulates a combat scenario and prints each VFX frame to stdout,
so you can see what the player would see on screen.

Usage:
    uv run python scripts/verify_combat_vfx.py
    uv run python scripts/verify_combat_vfx.py --speed 30
    uv run python scripts/verify_combat_vfx.py --only attack
    uv run python scripts/verify_combat_vfx.py --ice goliath
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Make the package importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from wet_run.combat.effects import (  # noqa: E402
    SKILL_EFFECT_ANIMATIONS,
    CombatEffects,
    IceType,
    spawn_critical,
    spawn_hit_effects,
    spawn_ice_death,
    spawn_ice_intro,
)

ALL_EFFECTS = sorted(SKILL_EFFECT_ANIMATIONS.keys())
ALL_ICE = [it.value for it in IceType]


def _color_char(ch: str, rgb: tuple[int, int, int]) -> str:
    """Wrap a char in ANSI 24-bit color."""
    return f"\x1b[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{ch}\x1b[0m"


def _render_frame(
    fx: CombatEffects,
    width: int = 60,
    height: int = 15,
    shake_dx: int = 0,
    shake_dy: int = 0,
) -> str:
    """Render a single frame to an ANSI string."""
    grid: list[list[tuple[str, tuple[int, int, int]]]] = [
        [(" ", (0, 0, 0)) for _ in range(width)] for _ in range(height)
    ]
    cx, cy = width // 2 + shake_dx, height // 2 + shake_dy

    # Hit flash
    if fx.hit_flash.is_active:
        ch = "·"
        for y in range(height):
            for x in range(width):
                if (x + y) % 3 == 0:
                    grid[y][x] = (ch, fx.hit_flash.color)

    # Animations (current frame in center)
    for anim in fx.animations:
        f = anim.current_frame
        if f is None:
            continue
        text = f.text
        ox, oy = f.offset
        for i, c in enumerate(text):
            tx = cx + ox + i
            ty = cy + oy
            if 0 <= tx < width and 0 <= ty < height:
                grid[ty][tx] = (c, f.color)

    # Particles
    for p in fx.particles.particles:
        px, py = int(p.x) + cx, int(p.y) + cy
        if 0 <= px < width and 0 <= py < height:
            r, g, b = p.color
            faded = (int(r * p.alpha), int(g * p.alpha), int(b * p.alpha))
            grid[py][px] = (p.char, faded)

    # Floating numbers
    for n in fx.floating_numbers:
        nx, ny = int(n.x) + cx, int(n.y) + cy
        if 0 <= nx < width and 0 <= ny < height:
            grid[ny][nx] = (n.text[0], n.color)

    # Cinematic centered text
    if fx.cinematic is not None and fx.cinematic.current_phase is not None:
        text, color, _ = fx.cinematic.current_phase
        ox = (width - len(text)) // 2
        for i, c in enumerate(text):
            tx = ox + i
            if 0 <= tx < width:
                grid[height // 2][tx] = (c, color)

    lines = []
    for row in grid:
        line = ""
        for ch, rgb in row:
            if ch == " ":
                line += " "
            else:
                line += _color_char(ch, rgb)
        lines.append(line)
    return "\n".join(lines)


def _play_animation(
    fx: CombatEffects,
    label: str,
    speed_ms: int = 50,
    width: int = 60,
    height: int = 15,
) -> None:
    """Play all active effects to completion, printing each frame."""
    print(f"\n\x1b[1;36m━━━ {label} ━━━\x1b[0m")
    for tick in range(100):
        fx.step(speed_ms)
        if not fx.has_active_effects():
            break
        shake_dx, shake_dy = fx.shake.offset()
        frame = _render_frame(fx, width, height, shake_dx, shake_dy)
        # Clear and redraw
        os.system("cls" if os.name == "nt" else "clear")
        print(f"\x1b[1;36m━━━ {label} ━━━\x1b[0m  [t={tick * speed_ms}ms]")
        print(frame)
        # Tiny pause for human viewing
        time.sleep(speed_ms / 1000.0)
    os.system("cls" if os.name == "nt" else "clear")


def demo_all_effects(speed: int, only: str | None, width: int, height: int) -> None:
    """Demo every skill effect animation."""
    effects = sorted(SKILL_EFFECT_ANIMATIONS.keys())
    if only:
        effects = [e for e in effects if only in e]
    for name in effects:
        fx = CombatEffects()
        # Spawn hit (target at center)
        spawn_hit_effects(
            fx,
            x=float(width // 2),
            y=float(height // 2),
            damage=42,
            effect_type=name,
            is_crit=(name in ("attack", "heavy_attack", "multi_hit")),
        )
        _play_animation(fx, f"EFFECT: {name}", speed, width, height)


def demo_critical(speed: int, width: int, height: int) -> None:
    """Demo critical hit effect (Layer 5 cinematic)."""
    fx = CombatEffects()
    spawn_critical(fx, x=float(width // 2), y=float(height // 2), damage=99)
    _play_animation(fx, "CRITICAL HIT (Layer 5 cinematic)", speed, width, height)


def demo_ice_intro(ice: str, speed: int, width: int, height: int) -> None:
    """Demo ICE intro cinematic."""
    ice_type = IceType(ice)
    fx = CombatEffects()
    spawn_ice_intro(fx, ice_type, name=f"{ice.upper()}-V")
    _play_animation(fx, f"ICE INTRO: {ice.upper()}", speed, width, height)


def demo_ice_death(ice: str, speed: int, width: int, height: int) -> None:
    """Demo ICE death cinematic."""
    ice_type = IceType(ice)
    fx = CombatEffects()
    spawn_ice_death(fx, ice_type)
    _play_animation(fx, f"ICE DEATH: {ice.upper()}", speed, width, height)


def demo_combo(speed: int, width: int, height: int) -> None:
    """Demo a 5x hit combo with combo counter."""
    fx = CombatEffects()
    print("\n\x1b[1;36m━━━ 5x COMBO ━━━\x1b[0m")
    for i in range(5):
        spawn_hit_effects(
            fx,
            x=float(width // 2),
            y=float(height // 2),
            damage=20 + i * 5,
            effect_type="multi_hit",
            is_crit=(i % 2 == 0),
        )
        fx.combo.register_hit(i * 200)
        # Step a few times
        for _ in range(3):
            fx.step(speed)
            if not fx.has_active_effects():
                break
        shake_dx, shake_dy = fx.shake.offset()
        frame = _render_frame(fx, width, height, shake_dx, shake_dy)
        os.system("cls" if os.name == "nt" else "clear")
        print(f"\x1b[1;36m━━━ 5x COMBO ━━━\x1b[0m  hit {i + 1}/5  combo={fx.combo.label}")
        print(frame)
        time.sleep(0.4)
    # Step to completion
    while fx.has_active_effects():
        fx.step(speed)
        shake_dx, shake_dy = fx.shake.offset()
        frame = _render_frame(fx, width, height, shake_dx, shake_dy)
        os.system("cls" if os.name == "nt" else "clear")
        print(f"\x1b[1;36m━━━ 5x COMBO ━━━\x1b[0m  hit 5/5  combo={fx.combo.label}")
        print(frame)
        time.sleep(speed / 1000.0)
    os.system("cls" if os.name == "nt" else "clear")


def main() -> int:
    parser = argparse.ArgumentParser(description="Combat VFX visual demo")
    parser.add_argument("--speed", type=int, default=50, help="ms per tick (default 50)")
    parser.add_argument("--width", type=int, default=60)
    parser.add_argument("--height", type=int, default=15)
    parser.add_argument(
        "--only",
        type=str,
        choices=ALL_EFFECTS,
        help="Show only this effect",
    )
    parser.add_argument(
        "--ice",
        type=str,
        choices=ALL_ICE,
        help="Show only this ICE type intro",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["effects", "critical", "intro", "death", "combo", "all"],
        default="all",
    )
    args = parser.parse_args()

    print("\x1b[1;32m=== Combat VFX Visual Verification ===\x1b[0m")
    print(f"speed={args.speed}ms/tick  size={args.width}x{args.height}")

    if args.mode in ("effects", "all"):
        demo_all_effects(args.speed, args.only, args.width, args.height)

    if args.mode in ("critical", "all"):
        demo_critical(args.speed, args.width, args.height)

    if args.mode in ("intro", "all"):
        if args.ice:
            demo_ice_intro(args.ice, args.speed, args.width, args.height)
        else:
            for ice in ALL_ICE:
                demo_ice_intro(ice, args.speed, args.width, args.height)

    if args.mode in ("death", "all"):
        if args.ice:
            demo_ice_death(args.ice, args.speed, args.width, args.height)
        else:
            for ice in ALL_ICE:
                demo_ice_death(ice, args.speed, args.width, args.height)

    if args.mode in ("combo", "all"):
        demo_combo(args.speed, args.width, args.height)

    print("\n\x1b[1;32m=== Done ===\x1b[0m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
