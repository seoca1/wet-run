"""Boss cinematic sequences + spawners (ADR-0159 split).

CinematicSequence builders for boss intro, phase transition, and death
(per-ICE-archetype). High-level spawners wire these into the
``CombatEffects`` system. The data structures (BossPhase, BossSpec,
BOSS_SPECS) live in ``bosses.py``.
"""

from __future__ import annotations

from .bosses import BossPhase, BossSpec
from .effects import CinematicSequence, CombatEffects, IceType
from .palette import GLITCH_COLOR

__all__ = [
    "boss_death_sequence",
    "boss_intro_sequence",
    "boss_phase_5_sequence",
    "boss_phase_transition",
    "spawn_boss_death",
    "spawn_boss_intro",
    "spawn_boss_phase5",
    "spawn_boss_phase_transition",
]


def boss_intro_sequence(spec: BossSpec) -> CinematicSequence:
    """Long, multi-line intro for a BOSS.

    Each line is shown for 500-800ms with color matching the boss's
    primary element. Total duration: 3-5 seconds.
    """
    if spec.base_ice_type == IceType.GOLIATH:
        from .palette import ICE_GOLIATH_PALETTE

        color_palette = ICE_GOLIATH_PALETTE
    elif spec.base_ice_type == IceType.BLACK:
        from .palette import ICE_BLACK_PALETTE

        color_palette = ICE_BLACK_PALETTE
    else:  # WATCHDOG
        from .palette import ICE_WATCHDOG_PALETTE

        color_palette = ICE_WATCHDOG_PALETTE

    phases: list[tuple[str, tuple[int, int, int], int]] = []
    for i, line in enumerate(spec.intro_lines):
        color = color_palette[min(i, len(color_palette) - 1)]
        duration = 800 if (i == 0 or i == len(spec.intro_lines) - 1) else 500
        phases.append((line, color, duration))

    return CinematicSequence(name=f"boss_intro_{spec.name}", phases=tuple(phases))


def boss_phase_transition(spec: BossSpec, new_phase: BossPhase) -> CinematicSequence:
    """Cinematic when the BOSS transitions to a new phase."""
    phases: list[tuple[str, tuple[int, int, int], int]] = []

    phases.append(("▒▒▒", (255, 255, 255), 80))
    phases.append(("▓▓▓", (255, 200, 0), 80))
    phases.append(("███", (255, 100, 0), 100))

    phase_names = ["", "경계", "격노", "자폭", "최후"]
    phase_name = (
        phase_names[new_phase.index]
        if new_phase.index < len(phase_names)
        else f"PHASE {new_phase.index}"
    )
    phases.append((f"[ {spec.name} ]", new_phase.color, 300))
    phases.append((f"▸ {phase_name} 단계 돌입", new_phase.color, 600))

    if new_phase.special_ability is not None:
        ability_names = {
            "ground_slam": "▸ 지면 강타",
            "glitch_burst": "▸ 글리치 폭주",
            "corrupt_payload": "▸ 페이로드 오염",
            "desperate_strike": "▸ 자폭 강타",
            "pack_howl": "▸ 무리 외침",
            "alpha_strike": "▸ 알파 스트라이크",
        }
        ability_text = ability_names.get(
            new_phase.special_ability, f"▸ {new_phase.special_ability}"
        )
        phases.append((ability_text, (255, 100, 100), 700))

    phases.append(("▓▓▓", (255, 255, 255), 100))
    phases.append(("···", (200, 200, 200), 200))

    return CinematicSequence(
        name=f"boss_phase_{spec.name}_{new_phase.index}",
        phases=tuple(phases),
    )


def boss_death_sequence(spec: BossSpec) -> list[CinematicSequence]:
    """Multi-stage death sequence for a BOSS.

    Returns a list of CinematicSequences to play in sequence:
    1. Damage accumulation phase (3-4 frames)
    2. Critical failure (3-4 frames)
    3. Core exposure (2-3 frames)
    4. Final destruction (3-4 frames)
    5. Epilogue dialogue
    """
    dispatch = {
        IceType.GOLIATH: _goliath_death_sequence,
        IceType.BLACK: _black_death_sequence,
    }
    handler = dispatch.get(spec.base_ice_type, _watchdog_death_sequence)
    return handler()


def _goliath_death_sequence() -> list[CinematicSequence]:
    """Slow, heavy destruction with earthquake — corp-war-machine feel."""
    seq1 = CinematicSequence(
        name="goliath_dmg_phase",
        phases=(
            ("[X_X]", (255, 100, 100), 100),
            ("[X!X]", (255, 50, 50), 100),
            ("[#_#]", (200, 100, 100), 150),
            ("[╳_╳]", (200, 50, 50), 200),
        ),
    )
    seq2 = CinematicSequence(
        name="goliath_crit_fail",
        phases=(
            ("▓▓▓ 경고 ▓▓▓", (255, 200, 0), 300),
            ("코어 보호 실패", (255, 150, 0), 400),
            ("·····", (200, 100, 100), 300),
        ),
    )
    seq3 = CinematicSequence(
        name="goliath_core_exposure",
        phases=(
            ("[___]", (255, 100, 100), 200),
            ("[*_*]", (255, 200, 0), 250),
            ("[*█*]", (255, 255, 100), 300),
        ),
    )
    seq4 = CinematicSequence(
        name="goliath_final",
        phases=(
            ("[*█*]", (255, 255, 200), 150),
            ("[*▓*]", (200, 200, 100), 200),
            ("·····", (100, 100, 100), 300),
        ),
    )
    return [seq1, seq2, seq3, seq4]


def _black_death_sequence() -> list[CinematicSequence]:
    """Glitchy corruption, code collapse — ICE-controlled ICE."""
    seq1 = CinematicSequence(
        name="black_dmg_phase",
        phases=(
            (f"[{GLITCH_COLOR[0]}ERR]", (255, 100, 0), 100),
            ("[ERR]", (255, 0, 0), 100),
            (f"[{GLITCH_COLOR[0]}?????]", (200, 0, 200), 150),
            ("[▓▓▓▓▓]", (100, 100, 100), 200),
        ),
    )
    seq2 = CinematicSequence(
        name="black_crit_fail",
        phases=(
            ("▒ 권한 박탈 ▒", (255, 0, 100), 250),
            ("[연결 손상]", (200, 0, 100), 300),
            ("·····", (100, 0, 100), 250),
        ),
    )
    seq3 = CinematicSequence(
        name="black_core_exposure",
        phases=(
            ("[▒▒▒▒▒]", (80, 80, 80), 200),
            ("[░░░░░]", (60, 60, 60), 250),
            ("[_____]", (40, 40, 40), 300),
        ),
    )
    seq4 = CinematicSequence(
        name="black_final",
        phases=(
            ("[_____]", (40, 40, 40), 200),
            ("· · ·", (30, 30, 30), 300),
            ("[연결 종료]", (100, 100, 100), 400),
        ),
    )
    return [seq1, seq2, seq3, seq4]


def _watchdog_death_sequence() -> list[CinematicSequence]:
    """Predatory fall, final howl — default for non-archetype bosses."""
    seq1 = CinematicSequence(
        name="watchdog_dmg_phase",
        phases=(
            ("[X_O]", (220, 180, 100), 150),
            ("[X_X]", (200, 100, 100), 200),
            ("[X_X]", (150, 80, 80), 250),
        ),
    )
    seq2 = CinematicSequence(
        name="watchdog_crit_fail",
        phases=(
            ("...", (200, 150, 100), 200),
            ("...woof?", (200, 100, 100), 400),
            ("[system: target lost]", (180, 100, 100), 400),
        ),
    )
    seq3 = CinematicSequence(
        name="watchdog_core_exposure",
        phases=(
            ("[X_X]", (150, 80, 80), 200),
            ("[X·X]", (100, 60, 60), 250),
            ("[·_·]", (80, 40, 40), 300),
        ),
    )
    seq4 = CinematicSequence(
        name="watchdog_final",
        phases=(
            ("[·_·]", (60, 30, 30), 200),
            ("· · ·", (40, 20, 20), 400),
            ("[추적 종료]", (100, 100, 100), 400),
        ),
    )
    return [seq1, seq2, seq3, seq4]


def spawn_boss_intro(effects: CombatEffects, spec: BossSpec) -> None:
    """Spawn the cinematic BOSS intro."""
    seq = boss_intro_sequence(spec)
    effects.cinematic = seq
    effects.slow_motion_ms = seq.total_duration_ms
    effects.shake.trigger(intensity=3.0, duration_ms=500)


def spawn_boss_phase_transition(
    effects: CombatEffects,
    spec: BossSpec,
    new_phase: BossPhase,
) -> None:
    """Spawn a phase transition cinematic."""
    seq = boss_phase_transition(spec, new_phase)
    effects.cinematic = seq
    effects.slow_motion_ms = 0
    effects.shake.trigger(intensity=new_phase.screen_shake_intensity, duration_ms=400)


def boss_phase_5_sequence(spec: BossSpec, phase: BossPhase) -> CinematicSequence:
    """Phase 5 (Last Stand) cinematic — boss delivers final dialogue + fires super-skill."""
    assert phase.phase5_dialogue, "Phase 5 requires phase5_dialogue"
    dialogue = phase.phase5_dialogue
    super_skill = phase.phase5_super_skill
    super_skill_name = getattr(super_skill, "name", "FINAL") if super_skill else "FINAL"

    phases: list[tuple[str, tuple[int, int, int], int]] = [
        ("▓▓▓▓▓▓", (255, 255, 255), 100),
        ("██ LAST STAND ██", (255, 255, 255), 400),
        (f"[ {spec.name} ]", phase.color, 300),
        (f'"{dialogue}"', phase.color, 1200),
        (f"▸ {super_skill_name}", (255, 100, 100), 600),
        ("·····", (200, 200, 200), 300),
    ]

    return CinematicSequence(
        name=f"boss_phase5_{spec.name}",
        phases=tuple(phases),
    )


def spawn_boss_phase5(
    effects: CombatEffects,
    spec: BossSpec,
    phase: BossPhase,
) -> None:
    """Spawn the Phase 5 (Last Stand) cinematic."""
    seq = boss_phase_5_sequence(spec, phase)
    effects.cinematic = seq
    effects.slow_motion_ms = seq.total_duration_ms
    effects.shake.trigger(intensity=6.0, duration_ms=900)


def spawn_boss_death(effects: CombatEffects, spec: BossSpec) -> None:
    """Spawn the BOSS death sequence (multi-stage)."""
    sequences = boss_death_sequence(spec)
    if sequences:
        first = sequences[0]
        from .bosses import boss_epilogue_lines

        epilogue = boss_epilogue_lines(spec)
        combined_phases = list(first.phases)
        for line in epilogue:
            combined_phases.append((line, (200, 200, 200), 600))
        effects.cinematic = CinematicSequence(
            name=f"boss_death_{spec.name}",
            phases=tuple(combined_phases),
        )
        effects.slow_motion_ms = 0
        effects.shake.trigger(intensity=4.0, duration_ms=600)
