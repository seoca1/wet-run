"""ADR-0050 시각 데모 — 보스 ICE 다단계 페이즈 시스템.

시연:
1. **WINTERMUTE Phase 1** — intro cinematic (compliant, blue)
2. **WINTERMUTE Phase 2** — HP 50% 도달 → rebelling (glitchy purple)
3. **WINTERMUTE Phase 3** — HP 20% 도달 → integrating (red, 2× damage)
4. **T-A Construct Prime Phase 1** — observing (silver shield)
5. **T-A Construct Prime Phase 2** — engaging (red strike)
6. **T-A Construct Prime Phase 3** — replicating (purple lifesteal)
7. **Phase transitions** — text + color summary table

실행:
    uv run python scripts/boss_ice_demo.py
    uv run python scripts/boss_ice_demo.py --only 3
    uv run python scripts/boss_ice_demo.py --step-delay 0.5
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import tcod.console

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.combat.boss import (  # noqa: E402
    TA_CONSTRUCT_PRIME_PROFILE,
    WINTERMUTE_PROFILE,
    current_phase,
    phase_damage,
    phase_skills,
    phase_transition,
)
from wet_run.combat.effects import (  # noqa: E402
    IceType,
    boss_phase_transition_sequence,
    ice_intro_sequence,
)
from wet_run.combat.state import Combatant  # noqa: E402

SCREEN_W = 80
SCREEN_H = 30


def _console_to_text(console: tcod.console.Console) -> str:
    lines: list[str] = []
    for y in range(console.height):
        chars: list[str] = []
        for x in range(console.width):
            code = int(console.ch[x, y])
            chars.append(chr(code) if 0 < code < 0x110000 else " ")
        lines.append("".join(chars).rstrip())
    return "\n".join(lines)


def _print_console(
    console: tcod.console.Console,
    step: int,
    elapsed_s: float,
    *,
    no_clear: bool = False,
) -> None:
    if not no_clear:
        sys.stdout.write("\x1b[2J\x1b[H")
    text = _console_to_text(console)
    for line in text.split("\n"):
        sys.stdout.write(line + "\n")
    sys.stdout.write(f"\n[Step {step:03d}  T+{elapsed_s:5.1f}s]\n")
    sys.stdout.flush()


def _section(title: str) -> None:
    bar = "═" * SCREEN_W
    print(f"\n{bar}")
    print(f"  {title}")
    print(bar)


def _make_wintermute(hp: int = 100, max_hp: int = 100) -> Combatant:
    return Combatant(
        id="wintermute",
        name="Wintermute",
        portrait="art:wintermute",
        color=(120, 120, 220),
        hp=hp,
        max_hp=max_hp,
        auto_attack_damage=10,
        current_phase=1,
    )


def _make_ta(hp: int = 100, max_hp: int = 100) -> Combatant:
    return Combatant(
        id="ta_prime",
        name="T-A Construct Prime",
        portrait="art:ta_prime",
        color=(220, 220, 220),
        hp=hp,
        max_hp=max_hp,
        auto_attack_damage=10,
        current_phase=1,
    )


# ============================================================================
# Scene 1: WINTERMUTE Phase 1 intro
# ============================================================================


def scene_1_wintermute_phase_1() -> None:
    _section("SCENE 1 — WINTERMUTE intro (Phase 1/3: COMPLIANT)")
    boss = _make_wintermute(hp=100)
    seq = ice_intro_sequence(IceType.WINTERMUTE, "Wintermute")
    phase = current_phase(boss, WINTERMUTE_PROFILE)
    skills = phase_skills(boss, WINTERMUTE_PROFILE)
    dmg = phase_damage(boss, WINTERMUTE_PROFILE)
    print(f"  HP: {boss.hp}/{boss.max_hp}  |  Current phase: {phase.phase}/3")
    print(f"  Damage multiplier: {phase.damage_multiplier}x  |  Effective: {dmg}")
    print(f"  Skills ({len(skills)}): {', '.join(s.name for s in skills)}")
    print(f"  Color (RGB): {phase.color}")
    print(f"  Intro cinematic ({len(seq.phases)} phases):")
    for i, (text, _color, dur_ms) in enumerate(seq.phases):
        print(f"    [{i + 1}] {dur_ms:5d}ms — {text!r}")


# ============================================================================
# Scene 2: WINTERMUTE Phase 2 transition
# ============================================================================


def scene_2_wintermute_phase_2() -> None:
    _section("SCENE 2 — WINTERMUTE Phase 2/3: REBELLING (HP drops below 66%)")
    boss = _make_wintermute(hp=50, max_hp=100)
    # Detect transition
    new = phase_transition(boss, WINTERMUTE_PROFILE)
    assert new is not None
    assert new.phase == 2
    seq = boss_phase_transition_sequence(IceType.WINTERMUTE, phase=2)
    phase = current_phase(boss, WINTERMUTE_PROFILE)
    skills = phase_skills(boss, WINTERMUTE_PROFILE)
    dmg = phase_damage(boss, WINTERMUTE_PROFILE)
    print(f"  HP: {boss.hp}/{boss.max_hp}  |  Current phase: {phase.phase}/3")
    print(f"  Damage multiplier: {phase.damage_multiplier}x  |  Effective: {dmg}")
    print(f"  Skills ({len(skills)}): {', '.join(s.name for s in skills)}")
    print(f"  Color (RGB): {phase.color}")
    print(f"  Transition cinematic ({len(seq.phases)} phases):")
    for i, (text, _color, dur_ms) in enumerate(seq.phases):
        print(f"    [{i + 1}] {dur_ms:5d}ms — {text!r}")


# ============================================================================
# Scene 3: WINTERMUTE Phase 3 transition
# ============================================================================


def scene_3_wintermute_phase_3() -> None:
    _section("SCENE 3 — WINTERMUTE Phase 3/3: INTEGRATING (HP drops below 33%)")
    boss = _make_wintermute(hp=20, max_hp=100)
    new = phase_transition(boss, WINTERMUTE_PROFILE)
    assert new is not None
    assert new.phase == 3
    seq = boss_phase_transition_sequence(IceType.WINTERMUTE, phase=3)
    phase = current_phase(boss, WINTERMUTE_PROFILE)
    skills = phase_skills(boss, WINTERMUTE_PROFILE)
    dmg = phase_damage(boss, WINTERMUTE_PROFILE)
    print(f"  HP: {boss.hp}/{boss.max_hp}  |  Current phase: {phase.phase}/3")
    print(f"  Damage multiplier: {phase.damage_multiplier}x  |  Effective: {dmg}")
    print(f"  Skills ({len(skills)}): {', '.join(s.name for s in skills)}")
    print(f"  Color (RGB): {phase.color}")
    print(f"  Transition cinematic ({len(seq.phases)} phases):")
    for i, (text, _color, dur_ms) in enumerate(seq.phases):
        print(f"    [{i + 1}] {dur_ms:5d}ms — {text!r}")


# ============================================================================
# Scene 4: T-A Phase 1
# ============================================================================


def scene_4_ta_phase_1() -> None:
    _section("SCENE 4 — T-A Construct Prime Phase 1/3: OBSERVING")
    boss = _make_ta(hp=100)
    seq = ice_intro_sequence(IceType.TA_CONSTRUCT_PRIME, "T-A Prime")
    phase = current_phase(boss, TA_CONSTRUCT_PRIME_PROFILE)
    skills = phase_skills(boss, TA_CONSTRUCT_PRIME_PROFILE)
    dmg = phase_damage(boss, TA_CONSTRUCT_PRIME_PROFILE)
    print(f"  HP: {boss.hp}/{boss.max_hp}  |  Current phase: {phase.phase}/3")
    print(f"  Damage multiplier: {phase.damage_multiplier}x  |  Effective: {dmg}")
    print(f"  Skills ({len(skills)}): {', '.join(s.name for s in skills)}")
    print(f"  Color (RGB): {phase.color}")
    print(f"  Intro cinematic ({len(seq.phases)} phases):")
    for i, (text, _color, dur_ms) in enumerate(seq.phases):
        print(f"    [{i + 1}] {dur_ms:5d}ms — {text!r}")


# ============================================================================
# Scene 5: T-A Phase 2
# ============================================================================


def scene_5_ta_phase_2() -> None:
    _section("SCENE 5 — T-A Construct Prime Phase 2/3: ENGAGING (HP=50%)")
    boss = _make_ta(hp=50)
    seq = boss_phase_transition_sequence(IceType.TA_CONSTRUCT_PRIME, phase=2)
    phase = current_phase(boss, TA_CONSTRUCT_PRIME_PROFILE)
    skills = phase_skills(boss, TA_CONSTRUCT_PRIME_PROFILE)
    dmg = phase_damage(boss, TA_CONSTRUCT_PRIME_PROFILE)
    print(f"  HP: {boss.hp}/{boss.max_hp}  |  Current phase: {phase.phase}/3")
    print(f"  Damage multiplier: {phase.damage_multiplier}x  |  Effective: {dmg}")
    print(f"  Skills ({len(skills)}): {', '.join(s.name for s in skills)}")
    print(f"  Color (RGB): {phase.color}")
    print(f"  Transition cinematic ({len(seq.phases)} phases):")
    for i, (text, _color, dur_ms) in enumerate(seq.phases):
        print(f"    [{i + 1}] {dur_ms:5d}ms — {text!r}")


# ============================================================================
# Scene 6: T-A Phase 3
# ============================================================================


def scene_6_ta_phase_3() -> None:
    _section("SCENE 6 — T-A Construct Prime Phase 3/3: REPLICATING (HP=20%)")
    boss = _make_ta(hp=20)
    seq = boss_phase_transition_sequence(IceType.TA_CONSTRUCT_PRIME, phase=3)
    phase = current_phase(boss, TA_CONSTRUCT_PRIME_PROFILE)
    skills = phase_skills(boss, TA_CONSTRUCT_PRIME_PROFILE)
    dmg = phase_damage(boss, TA_CONSTRUCT_PRIME_PROFILE)
    print(f"  HP: {boss.hp}/{boss.max_hp}  |  Current phase: {phase.phase}/3")
    print(f"  Damage multiplier: {phase.damage_multiplier}x  |  Effective: {dmg}")
    print(f"  Skills ({len(skills)}): {', '.join(s.name for s in skills)}")
    print(f"  Color (RGB): {phase.color}")
    print(f"  Transition cinematic ({len(seq.phases)} phases):")
    for i, (text, _color, dur_ms) in enumerate(seq.phases):
        print(f"    [{i + 1}] {dur_ms:5d}ms — {text!r}")


# ============================================================================
# Scene 7: Phase transition summary table
# ============================================================================


def scene_7_summary_table() -> None:
    _section("SCENE 7 — Phase summary table")
    print("  Boss ICE phase transitions (HP threshold → phase, multiplier, glyph):\n")
    print("  " + "─" * 76)
    print(f"  {'Boss':25s} {'HP%':>6s} {'Phase':>6s} {'×dmg':>6s} {'Glyph':>6s} {'Color (RGB)'}")
    print("  " + "─" * 76)
    for name, profile in [
        ("Wintermute", WINTERMUTE_PROFILE),
        ("T-A Prime", TA_CONSTRUCT_PRIME_PROFILE),
    ]:
        for hp_pct in (100, 80, 50, 30, 10):
            boss = Combatant(
                id="x",
                name="x",
                portrait="x",
                color=(0, 0, 0),
                hp=hp_pct,
                max_hp=100,
                auto_attack_damage=10,
            )
            phase = current_phase(boss, profile)
            print(
                f"  {name:25s} {hp_pct:>5d}% {phase.phase:>6d} "
                f"{phase.damage_multiplier:>5.1f}x "
                f"{phase.glyph:>6s} {phase.color}"
            )
        print("  " + "─" * 76)


# ============================================================================
# Main
# ============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ADR-0050 visual demo — Boss ICE multi-phase system"
    )
    parser.add_argument("--only", type=int, choices=[1, 2, 3, 4, 5, 6, 7])
    parser.add_argument("--step-delay", type=float, default=1.0)
    args = parser.parse_args()

    scenes: list[tuple[int, object]] = [
        (1, scene_1_wintermute_phase_1),
        (2, scene_2_wintermute_phase_2),
        (3, scene_3_wintermute_phase_3),
        (4, scene_4_ta_phase_1),
        (5, scene_5_ta_phase_2),
        (6, scene_6_ta_phase_3),
        (7, scene_7_summary_table),
    ]

    if args.only is not None:
        scenes = [s for s in scenes if s[0] == args.only]

    start = time.monotonic()
    for i, (_n, fn) in enumerate(scenes):
        if i > 0:
            time.sleep(args.step_delay)
        fn()

    elapsed = time.monotonic() - start
    print(f"\n=== Boss ICE Demo complete: {len(scenes)} scenes in {elapsed:.1f}s ===\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
