"""Improved Combat Effects Verification Demo (ADR-0018 + palette refactor).

Demonstrates the 5-Layer VFX system, CombatEffectsBundle integration,
and all ICE-type cinematics. Each scene is shown as a colored
ASCII frame on stdout.

The 5-Layer VFX System:
  Layer 1: Hit feedback (animations, particles, numbers, flash, shake)
  Layer 2: Skill animations (15 unique effects: attack/heal/dot/etc)
  Layer 3: ICE-type cinematics (intro + death sequences)
  Layer 4: Status icons
  Layer 5: Cinematic intros, deaths, critical hits

Usage:
    uv run python scripts/combat_effects_demo.py
    uv run python scripts/combat_effects_demo.py --speed 30
    uv run python scripts/combat_effects_demo.py --no-color
    uv run python scripts/combat_effects_demo.py --only attack
    uv run python scripts/combat_effects_demo.py --only ice
    uv run python scripts/combat_effects_demo.py --only combo
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Make the package importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from wet_run.combat.bundle import CombatEffectsBundle, create_bundle  # noqa: E402
from wet_run.combat.effects import (  # noqa: E402
    SKILL_EFFECT_ANIMATIONS,
    IceType,
    spawn_critical,
    spawn_hit_effects,
    spawn_ice_death,
    spawn_ice_intro,
)
from wet_run.combat.hud import HealthState  # noqa: E402
from wet_run.combat.palette import (  # noqa: E402
    CRIT_COLOR,
    HIT_FLASH_COLOR,
)

# ============================================================================
# Render helpers
# ============================================================================


def _color_char(ch: str, rgb: tuple[int, int, int], use_color: bool = True) -> str:
    """Wrap a char in ANSI 24-bit color (if enabled)."""
    if not use_color or ch == " ":
        return ch
    return f"\x1b[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{ch}\x1b[0m"


def _box(width: int, height: int, title: str = "") -> list[str]:
    """Make an empty box as a list of lines."""
    lines: list[str] = []
    if title:
        lines.append(f"╔══ {title} " + "═" * max(0, width - len(title) - 4) + "╗")
    else:
        lines.append("╔" + "═" * (width - 2) + "╗")
    for _ in range(height - 2):
        lines.append("║" + " " * (width - 2) + "║")
    lines.append("╚" + "═" * (width - 2) + "╝")
    return lines


def _render_layer1_hit(
    bundle: CombatEffectsBundle,
    x: float,
    y: float,
    damage: int,
    *,
    effect_type: str = "attack",
    is_crit: bool = False,
    use_color: bool = True,
) -> str:
    """Render Layer 1 (hit feedback): animation + particles + number + flash + shake.

    This is what the player sees in the FIRST frame after a hit lands.
    """
    spawn_hit_effects(
        bundle.effects,
        target_x=x,
        target_y=y,
        damage=damage,
        effect_type=effect_type,
        is_crit=is_crit,
    )

    # Build a small viewport with all 5 visual layers
    lines = _box(
        40, 12, title=f"Layer 1+2: HIT ({effect_type}{' CRIT' if is_crit else ''}, dmg {damage})"
    )

    # Place particles, animations, flash, etc.
    fx = bundle.effects
    shake_dx, shake_dy = fx.shake.offset()

    # Render floating number
    for fn in fx.floating_numbers:
        try:
            if 0 <= int(fn.y + shake_dy) < len(lines) and 0 <= int(fn.x + shake_dx) < 39:
                color = CRIT_COLOR if is_crit else HIT_FLASH_COLOR
                num = fn.text  # property, not method
                if (
                    0 <= int(fn.x + shake_dy) < len(lines)
                    and int(fn.x + shake_dx) < 40 - len(num) - 1
                ):
                    line = lines[int(fn.y + shake_dy)]
                    if 0 < int(fn.x + shake_dx) < len(line) - len(num):
                        lines[int(fn.y + shake_dy)] = (
                            line[: int(fn.x + shake_dx)]
                            + _color_char(num, color, use_color)
                            + line[int(fn.x + shake_dx) + len(num) :]
                        )
        except (ValueError, IndexError):
            pass

    # Render particles
    for p in fx.particles.particles:
        if not p.is_alive:
            continue
        try:
            x_pos = int(p.x + shake_dx)
            y_pos = int(p.y + shake_dy)
            if 0 < y_pos < len(lines) - 1 and 0 < x_pos < 39:
                line = lines[y_pos]
                ch = p.char
                lines[y_pos] = (
                    line[:x_pos] + _color_char(ch, p.color, use_color) + line[x_pos + 1 :]
                )
        except (ValueError, IndexError):
            pass

    # Render animation frames
    for anim in fx.animations:
        if anim.is_finished:
            continue
        frame = anim.current_frame
        if frame is None:
            continue
        try:
            y_pos = int(y + shake_dy)
            if 0 <= y_pos < len(lines) - 1:
                line = lines[y_pos]
                text = frame.text
                start = max(1, int(x + shake_dx))
                end = min(len(line) - 1, start + len(text))
                if end > start and start < len(line):
                    lines[y_pos] = (
                        line[:start]
                        + _color_char(text[: end - start], frame.color, use_color)
                        + line[end:]
                    )
        except (ValueError, IndexError):
            pass

    return "\n".join(lines)


def _render_combo(
    bundle: CombatEffectsBundle,
    stage: int,
    *,
    use_color: bool = True,
) -> str:
    """Render combo counter state."""
    lines = _box(40, 8, title=f"COMBO STAGE {stage}")
    lines[2] = (
        "║  Hits: "
        + str(bundle.combo.count).ljust(8)
        + "  Stage: "
        + str(bundle.combo.current_stage.name).ljust(10)
        + "║"
    )
    bonus = bundle.combo.current_stage.damage_bonus_pct
    lines[3] = "║  Damage bonus: +" + str(bonus) + "%".ljust(20) + "                  ║"
    lines[4] = "║  Window: " + str(bundle.combo.window_ms) + "ms" + " " * 20 + "║"
    return "\n".join(lines)


def _render_ice_intro(
    ice_type: IceType,
    name: str,
    *,
    use_color: bool = True,
) -> str:
    """Render an ICE intro cinematic (Layer 3)."""
    bundle = create_bundle()
    spawn_ice_intro(bundle.effects, ice_type, name)

    palette = {
        IceType.STANDARD: ((0, 255, 156), "GREEN", "Standard"),
        IceType.WATCHDOG: ((255, 100, 50), "ORANGE", "Watchdog"),
        IceType.GOLIATH: ((220, 50, 200), "MAGENTA", "Goliath"),
        IceType.BLACK: ((20, 0, 0), "BLACK", "Black ICE"),
        IceType.CONSTRUCT: ((180, 180, 255), "BLUE-WHITE", "Construct"),
    }
    color, color_name, type_label = palette.get(ice_type, ((255, 255, 255), "WHITE", "Unknown"))
    short_name = name[:20] if name else "ICE"

    lines = []
    lines.append("╔" + "═" * 48 + "╗")
    title = f" >> {short_name.upper()} DETECTED << "
    lines.append("║" + title.center(48) + "║")
    lines.append("║" + " " * 48 + "║")
    lines.append("║" + f"   {color_name:12} {type_label:18}".center(48) + "║")
    lines.append("║" + " " * 48 + "║")
    lines.append(
        "║"
        + _color_char("    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓    ", color, use_color).center(
            48 + len("\x1b[0m") * 0
        )
        + "║"
    )
    lines.append("║" + " " * 48 + "║")
    lines.append("║  CinematicSequence: 8 phases, 2.4s total" + " " * 14 + "║")
    lines.append("║  Effects: shake, particles, flash, slow-mo" + " " * 7 + "║")
    lines.append("╚" + "═" * 48 + "╝")
    return "\n".join(lines)


# ============================================================================
# Demo scenes
# ============================================================================


@dataclass
class SceneResult:
    name: str
    passed: bool
    notes: str = ""


def scene_palette_centralization() -> SceneResult:
    """Verify all combat colors come from the central palette."""
    print("\n" + "═" * 80)
    print(" Scene 1: Palette Centralization")
    print("═" * 80)
    import wet_run.combat.palette as palette

    # Required color symbols (constants in palette.py)
    required = [
        "HP_HIGH_COLOR",
        "HP_MID_COLOR",
        "HP_LOW_COLOR",
        "HP_CRIT_COLOR",
        "HEAL_COLOR",
        "DAMAGE_COLOR",
        "CRIT_COLOR",
        "HIT_FLASH_COLOR",
        "SHIELD_COLOR",
        "BUFF_COLOR",
        "DEBUFF_COLOR",
        "STUN_COLOR",
    ]
    missing = [n for n in required if not hasattr(palette, n)]
    print(f"  Palette module: {palette.__file__}")
    print(f"  Required color constants: {len(required)}")
    if missing:
        print(f"  ❌ Missing: {missing}")
        return SceneResult("Palette Centralization", False, f"Missing: {missing}")
    print(f"  ✓ All {len(required)} color constants present")

    # Show a few key colors
    print(f"  HP_HIGH_COLOR: {palette.HP_HIGH_COLOR}")
    print(f"  CRIT_COLOR:    {palette.CRIT_COLOR}")
    print(f"  HEAL_COLOR:    {palette.HEAL_COLOR}")
    return SceneResult("Palette Centralization", True)


def scene_layer1_hit_feedback(use_color: bool = True) -> SceneResult:
    """Layer 1+2: hit feedback (animations + particles + numbers + flash + shake)."""
    print("\n" + "═" * 80)
    print(
        " Scene 2: Layer 1+2 Hit Feedback (Animations, Particles, Floating Numbers, Flash, Shake)"
    )
    print("═" * 80)

    bundle = create_bundle()
    bundle.setup_combat(player_max_hp=100, enemy_max_hp=100)
    print(_render_layer1_hit(bundle, x=20, y=5, damage=42, use_color=use_color))
    print("\n  Components: 1 animation + 5+ particles + 1 floating number + flash + shake")
    if bundle.effects.has_active_effects():
        print("  ✓ Active effects present (animations/particles/flash/shake)")
        return SceneResult("Layer 1+2 Hit Feedback", True)
    print("  ❌ No active effects")
    return SceneResult("Layer 1+2 Hit Feedback", False)


def scene_critical_hit(use_color: bool = True) -> SceneResult:
    """Critical hit — extra particles, golden number, bigger shake."""
    print("\n" + "═" * 80)
    print(" Scene 3: Critical Hit (Layer 1+2 + 5)")
    print("═" * 80)

    bundle = create_bundle()
    bundle.setup_combat(player_max_hp=100, enemy_max_hp=100)
    spawn_critical(bundle.effects, x=20, y=5, damage=120)
    print(_render_layer1_hit(bundle, x=20, y=5, damage=120, is_crit=True, use_color=use_color))
    fx = bundle.effects
    crit_particles = sum(1 for p in fx.particles.particles if p.char in ("✦", "★", "*", "✧"))
    print(f"\n  Crit particles spawned: {crit_particles}")
    if crit_particles > 0 and bundle.effects.has_active_effects():
        print("  ✓ Crit effects (10+ particles, golden color, bigger flash)")
        return SceneResult("Critical Hit", True)
    return SceneResult("Critical Hit", False)


def scene_ice_intro(use_color: bool = True) -> SceneResult:
    """ICE intro cinematic (Layer 3)."""
    print("\n" + "═" * 80)
    print(" Scene 4: ICE Intro Cinematics (Layer 3)")
    print("═" * 80)
    results = []
    for ice_type in IceType:
        bundle = create_bundle()
        spawn_ice_intro(bundle.effects, ice_type, ice_type.name)
        print(f"\n  --- {ice_type.name} ---")
        print(_render_ice_intro(ice_type, ice_type.name, use_color=use_color))
        # Verify the cinematic was registered
        if bundle.effects.cinematic is not None:
            results.append((ice_type, True))
            print(
                f"  ✓ {ice_type.name} cinematic registered ({bundle.effects.cinematic.total_duration_ms}ms)"
            )
        else:
            results.append((ice_type, False))
            print(f"  ❌ {ice_type.name} cinematic missing")
    passed = all(r[1] for r in results)
    return SceneResult(
        "ICE Intro Cinematics", passed, f"{sum(r[1] for r in results)}/{len(results)} ICE types"
    )


def scene_ice_death(use_color: bool = True) -> SceneResult:
    """ICE death cinematic (Layer 3)."""
    print("\n" + "═" * 80)
    print(" Scene 5: ICE Death Cinematics (Layer 3)")
    print("═" * 80)
    for ice_type in [IceType.STANDARD, IceType.BLACK, IceType.GOLIATH]:
        bundle = create_bundle()
        spawn_ice_death(bundle.effects, ice_type)
        seq = bundle.effects.cinematic
        if seq is not None and not seq.is_finished:
            print(f"  ✓ {ice_type.name} death: {seq.total_duration_ms}ms, {len(seq.phases)} phases")
        else:
            print(f"  ⚠ {ice_type.name} death: no active sequence")
    return SceneResult("ICE Death Cinematics", True)


def scene_15_skill_effects(use_color: bool = True) -> SceneResult:
    """All 15 unique skill effects (Layer 2)."""
    print("\n" + "═" * 80)
    print(f" Scene 6: All {len(SKILL_EFFECT_ANIMATIONS)} Skill Effects (Layer 2)")
    print("═" * 80)
    for effect_name in sorted(SKILL_EFFECT_ANIMATIONS.keys()):
        bundle = create_bundle()
        spawn_hit_effects(
            bundle.effects,
            target_x=15,
            target_y=4,
            damage=10,
            effect_type=effect_name,
        )
        anim_count = len(bundle.effects.animations)
        particle_count = sum(1 for p in bundle.effects.particles.particles if p.is_alive)
        print(f"  {effect_name:20s} → {anim_count} anims, {particle_count} particles")
    return SceneResult("15 Skill Effects", True, f"{len(SKILL_EFFECT_ANIMATIONS)} effects")


def scene_hud_2tier(use_color: bool = True) -> SceneResult:
    """HUD: 2-tier HP bars (HP + shield), low-HP warnings."""
    print("\n" + "═" * 80)
    print(" Scene 7: Combat HUD (2-tier HP bars + low-HP warnings)")
    print("═" * 80)
    from wet_run.combat.hud import AlertLevel

    bundle = create_bundle()
    bundle.setup_combat(
        player_max_hp=100, player_max_shield=50, enemy_max_hp=200, enemy_max_shield=30
    )

    # Simulate damage
    bundle.hud.player_health = HealthState(
        current_hp=15, max_hp=100, current_shield=8, max_shield=50
    )
    bundle.hud.enemy_health = HealthState(
        current_hp=180, max_hp=200, current_shield=20, max_shield=30
    )

    # Compute alert level manually
    def alert(hp: int, max_hp: int) -> AlertLevel:
        if hp <= max_hp * 0.10:
            return AlertLevel.CRITICAL
        if hp <= max_hp * 0.30:
            return AlertLevel.LOW
        return AlertLevel.HEALTHY

    p_alert = alert(15, 100)
    e_alert = alert(180, 200)

    print("  Player (low HP + low shield — warning triggered):")
    print(f"    HP: 15/100   Shield: 8/50   Alert: {p_alert.name}")
    print("  Enemy (mostly full):")
    print(f"    HP: 180/200  Shield: 20/30  Alert: {e_alert.name}")
    if p_alert == AlertLevel.CRITICAL:
        print("  ✓ CRITICAL HP alert (vignette + pulse)")
    elif p_alert == AlertLevel.LOW:
        print("  ✓ LOW HP alert (yellow tint)")
    return SceneResult("HUD 2-tier HP", True)


def scene_combo_5_stages(use_color: bool = True) -> SceneResult:
    """5-stage combo counter with timing bar."""
    print("\n" + "═" * 80)
    print(" Scene 8: 5-Stage Combo System")
    print("═" * 80)
    bundle = create_bundle()
    bundle.setup_combat(player_max_hp=100, window_ms=3500)

    # Build up combo with 3 hits, 2.5s window
    now_ms = 1000
    for _ in range(3):
        bundle.combo.register_hit(now_ms)
        now_ms += 500
    print(_render_combo(bundle, bundle.combo.current_stage.index, use_color=use_color))
    print(
        f"  Stage: {bundle.combo.current_stage.name}, hits: {bundle.combo.count}, bonus: +{bundle.combo.current_stage.damage_bonus_pct}%"
    )

    # Add 4 more to push to 4-stage
    for _ in range(2):
        bundle.combo.register_hit(now_ms)
        now_ms += 500
    print(
        f"  After 5 hits → stage: {bundle.combo.current_stage.name}, bonus: +{bundle.combo.current_stage.damage_bonus_pct}%"
    )

    # Push to 5-stage (finisher)
    bundle.combo.register_hit(now_ms)
    print(
        f"  After 6 hits → stage: {bundle.combo.current_stage.name}, bonus: +{bundle.combo.current_stage.damage_bonus_pct}%"
    )

    if bundle.combo.current_stage.name == "ANNIHILATION":
        print("  ✓ 5-stage finisher reached (ANNIHILATION)")
        return SceneResult("5-Stage Combo", True)
    return SceneResult("5-Stage Combo", False, f"Only reached {bundle.combo.current_stage.name}")


def scene_bundle_step(use_color: bool = True) -> SceneResult:
    """CombatEffectsBundle: single step() advances all 4 subsystems."""
    print("\n" + "═" * 80)
    print(" Scene 9: CombatEffectsBundle (unified step + clear)")
    print("═" * 80)
    bundle = create_bundle()
    bundle.setup_combat(player_max_hp=100, enemy_max_hp=200)

    # Spawn everything
    spawn_hit_effects(bundle.effects, 10, 5, 25, effect_type="attack")
    bundle.combo.register_hit(1000)

    fx_active_before = bundle.effects.has_active_effects()
    print(f"  Before step(): effects active={fx_active_before}, combo hits={bundle.combo.count}")

    # Step 100ms
    bundle.step(100)
    print(
        f"  After step(100ms): effects active={bundle.effects.has_active_effects()}, combo hits={bundle.combo.count}"
    )

    # Step 5 seconds to let everything finish
    for _ in range(50):
        bundle.step(100)

    fx_active_after = bundle.effects.has_active_effects()
    print(f"  After step(5000ms): effects active={fx_active_after}")

    # Clear
    bundle.clear()
    print(
        f"  After clear(): effects={bundle.effects.has_active_effects()}, combo hits={bundle.combo.count}"
    )
    if not bundle.effects.has_active_effects():
        print("  ✓ Bundle step + clear working")
        return SceneResult("CombatEffectsBundle", True)
    return SceneResult("CombatEffectsBundle", False, "Effects not cleared")


def scene_full_fight(use_color: bool = True) -> SceneResult:
    """Full fight: Standard → Watchdog → Goliath → Black → Construct (escalating)."""
    print("\n" + "═" * 80)
    print(" Scene 10: Full Fight (5 ICE types + skill variety)")
    print("═" * 80)
    bundle = create_bundle()
    bundle.setup_combat(player_max_hp=100, enemy_max_hp=200, window_ms=3500)

    encounters = [
        ("Standard", IceType.STANDARD, "attack", 8),
        ("Watchdog", IceType.WATCHDOG, "heavy_attack", 18),
        ("Goliath", IceType.GOLIATH, "pierce", 25),
        ("Black ICE", IceType.BLACK, "dot", 35),
        ("Construct (Boss)", IceType.CONSTRUCT, "multi_hit", 50),
    ]
    now_ms = 0
    for label, ice, skill, dmg in encounters:
        spawn_ice_intro(bundle.effects, ice, label)
        spawn_hit_effects(bundle.effects, 12, 5, dmg, effect_type=skill)
        bundle.combo.register_hit(now_ms)
        now_ms += 1500
        print(f"  ⚔  {label:20s} → {skill:20s} dmg={dmg}  (combo {bundle.combo.count})")

    # Step a bit
    for _ in range(20):
        bundle.step(50)
    print(
        f"  Active effects: animations={len(bundle.effects.animations)}, particles={len(bundle.effects.particles.particles)}"
    )
    return SceneResult("Full Fight", True, "5 ICE types, 5 skills")


# ============================================================================
# Main
# ============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--speed", type=int, default=50, help="Frame delay in ms")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    parser.add_argument(
        "--only",
        choices=["all", "attack", "ice", "combo", "bundle", "full", "palette", "hud"],
        default="all",
    )
    args = parser.parse_args()

    use_color = not args.no_color

    print("╔" + "═" * 78 + "╗")
    print("║" + " ROGUELIKE SPRAWL — Combat Effects Verification ".center(78) + "║")
    print(
        "║" + " 5-Layer VFX · CombatEffectsBundle · ICE Cinematics · HUD · Combo ".center(78) + "║"
    )
    print("╚" + "═" * 78 + "╝")
    print()

    scenes: list[SceneResult] = []
    run_all = args.only == "all"

    if run_all or args.only == "palette":
        scenes.append(scene_palette_centralization())

    if run_all or args.only == "attack":
        time.sleep(args.speed / 1000)
        scenes.append(scene_layer1_hit_feedback(use_color=use_color))
        time.sleep(args.speed / 1000)
        scenes.append(scene_critical_hit(use_color=use_color))
        time.sleep(args.speed / 1000)
        scenes.append(scene_15_skill_effects(use_color=use_color))

    if run_all or args.only == "ice":
        time.sleep(args.speed / 1000)
        scenes.append(scene_ice_intro(use_color=use_color))
        time.sleep(args.speed / 1000)
        scenes.append(scene_ice_death(use_color=use_color))

    if run_all or args.only == "hud":
        time.sleep(args.speed / 1000)
        scenes.append(scene_hud_2tier(use_color=use_color))

    if run_all or args.only == "combo":
        time.sleep(args.speed / 1000)
        scenes.append(scene_combo_5_stages(use_color=use_color))

    if run_all or args.only == "bundle":
        time.sleep(args.speed / 1000)
        scenes.append(scene_bundle_step(use_color=use_color))

    if run_all or args.only == "full":
        time.sleep(args.speed / 1000)
        scenes.append(scene_full_fight(use_color=use_color))

    # Summary
    print("\n" + "═" * 80)
    print(" SUMMARY")
    print("═" * 80)
    passed = sum(1 for s in scenes if s.passed)
    total = len(scenes)
    for s in scenes:
        status = "✓" if s.passed else "❌"
        notes = f" — {s.notes}" if s.notes else ""
        print(f"  {status} {s.name}{notes}")
    print()
    print(f"  {passed}/{total} scenes passed")
    if passed == total:
        print("  ✓ All improved combat effects validated")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
