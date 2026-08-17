"""BOSS ICE definitions with multi-phase transitions.

BOSS ICE have:
- Multi-phase progression (3-4 phases triggered at HP thresholds)
- Longer intro sequence (3-5s with multi-line text)
- Multi-phase death sequence (12-15 frames)
- Phase transition effects (screen flash, name callout)
- Per-phase stat buffs (attack speed, damage, special abilities)
- Boss-specific dialogue lines (Korean)

Boss types (3 implemented):
  1. GOLIATH PRIME (goliath base) — earth-shattering, 4 phases
  2. BLACK ICE LORD (black base) — glitch chaos, 3 phases
  3. WATCHDOG ALPHA (watchdog base) — pack leader, 3 phases
"""

from __future__ import annotations

from dataclasses import dataclass

from .effects import (
    IceType,
)
from .palette import GLITCH_COLOR
from .state import Combatant

# ----------------------------------------------------------------------------
# Boss data structures
# ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BossPhase:
    """A single phase of a BOSS fight.

    Activated when the BOSS's HP drops below `hp_threshold_pct` (0-100).
    Each phase has its own intro line and stat modifiers.
    """

    index: int
    name: str
    hp_threshold_pct: int = 0  # 0-100, phase activates when HP% <= this
    intro_line: str = ""  # Korean text shown on transition
    color: tuple[int, int, int] = (255, 255, 255)
    attack_bonus_pct: int = 0  # +X% attack vs previous phase
    speed_bonus_pct: int = 0  # +X% attack speed
    screen_shake_intensity: float = 0.0  # Shake on phase change
    special_ability: str | None = None  # e.g. "ground_slam", "glitch_burst"
    aoe_damage: int = 0  # Damage dealt to player at phase start (0 = no AoE)
    spawn_minions: tuple[str, ...] = ()  # ICE ids spawned at phase start
    vfx_theme: str = "default"
    skills: tuple[object, ...] = ()
    phase5_super_skill: object | None = None
    phase5_dialogue: str = ""
    phase5_damage_multiplier: float = 3.0


@dataclass(frozen=True, slots=True)
class BossSpec:
    """A complete BOSS definition with all phases."""

    id: str
    name: str
    base_ice_type: IceType
    hp_multiplier: float  # 3-5x normal ICE
    attack_multiplier: float  # 1.5-2.5x
    defense_multiplier: float  # 1.2-2.0x
    phases: tuple[BossPhase, ...]  # Ordered high-to-low HP
    intro_lines: tuple[str, ...]  # Multi-line intro text
    death_lines: tuple[str, ...]  # Multi-line death text
    # Phase B-3: default VFX theme for this boss
    vfx_theme: str = (
        "default"  # "default", "wintermute", "goliath", "black_ice", "watchdog", "ta_construct"
    )


# ----------------------------------------------------------------------------
# 3 BOSS definitions
# ----------------------------------------------------------------------------


GOLIATH_PRIME = BossSpec(
    id="goliath_prime",
    name="GOLIATH PRIME",
    base_ice_type=IceType.GOLIATH,
    hp_multiplier=4.0,
    attack_multiplier=2.0,
    defense_multiplier=1.8,
    intro_lines=(
        "[ 경고: GOLIATH PRIME ]",
        "▓▓▓ 보안 시스템 핵심 ▓▓▓",
        "최대 방어 프로토콜 가동",
        "·····",
        "출현.",
    ),
    phases=(
        BossPhase(
            index=0,
            name="정상",
            hp_threshold_pct=100,
            intro_line="",
            color=(150, 150, 170),
        ),
        BossPhase(
            index=1,
            name="경계",
            hp_threshold_pct=75,
            intro_line="▸ 방어 프로토콜 강화",
            color=(255, 180, 100),
            attack_bonus_pct=20,
            speed_bonus_pct=10,
            screen_shake_intensity=2.0,
        ),
        BossPhase(
            index=2,
            name="격노",
            hp_threshold_pct=50,
            intro_line="▸ 격노 상태 돌입",
            color=(255, 100, 100),
            attack_bonus_pct=40,
            speed_bonus_pct=20,
            screen_shake_intensity=3.0,
            special_ability="ground_slam",
            # Phase I: GOLIATH phase 2 spawns watchdog adds
            spawn_minions=("watchdog", "watchdog"),
        ),
        BossPhase(
            index=3,
            name="자폭",
            hp_threshold_pct=25,
            intro_line="▸ 자폭 시퀀스 시작",
            color=(255, 50, 50),
            attack_bonus_pct=80,
            speed_bonus_pct=40,
            screen_shake_intensity=4.5,
            special_ability="desperate_strike",
            # Phase I: GOLIATH phase 3 self-destruct AoE (high damage)
            aoe_damage=25,
            spawn_minions=("corporate_guard",),
        ),
    ),
    death_lines=(
        "[ GOLIATH PRIME ]",
        "·····",
        "방어 프로토콜 해제.",
        "코어 노출.",
        "·····",
        "침묵.",
    ),
)

BLACK_ICE_LORD = BossSpec(
    id="black_ice_lord",
    name="BLACK ICE LORD",
    base_ice_type=IceType.BLACK,
    hp_multiplier=3.5,
    attack_multiplier=2.5,
    defense_multiplier=1.4,
    intro_lines=(
        "▓▓▓ 오류: ICE 권한 초과 ▓▓▓",
        "▓▓▓ BLACK ICE: 관리자 계정 ▓▓▓",
        "·····",
        "▒▒ 관리자 권한으로 시스템 장악 ▒▒",
        "나타남.",
    ),
    phases=(
        BossPhase(
            index=0,
            name="위장",
            hp_threshold_pct=100,
            intro_line="",
            color=(180, 180, 200),
        ),
        BossPhase(
            index=1,
            name="노출",
            hp_threshold_pct=66,
            intro_line="▸ 위장 해제 — 본체 노출",
            color=GLITCH_COLOR,
            attack_bonus_pct=30,
            screen_shake_intensity=1.5,
            special_ability="glitch_burst",
            # Phase I: BLACK phase 1 spawns a construct echo
            spawn_minions=("romantics_ice",),
        ),
        BossPhase(
            index=2,
            name="붕괴",
            hp_threshold_pct=33,
            intro_line="▸ 코드 손상 — 무작위 공격",
            color=(255, 0, 100),
            attack_bonus_pct=60,
            speed_bonus_pct=30,
            screen_shake_intensity=3.0,
            special_ability="corrupt_payload",
            # Phase I: BLACK phase 2 corruption AoE
            aoe_damage=10,
            spawn_minions=("romantics_ice_elite",),
        ),
    ),
    death_lines=(
        "[ERR] BLACK_ICE_LORD",
        "▓▓ 권한 박탈 ▓▓",
        "·····",
        "[연결 종료]",
    ),
)

WATCHDOG_ALPHA = BossSpec(
    id="watchdog_alpha",
    name="WATCHDOG ALPHA",
    base_ice_type=IceType.WATCHDOG,
    hp_multiplier=3.0,
    attack_multiplier=1.8,
    defense_multiplier=1.2,
    intro_lines=(
        "[ 경고: 추적자 ]",
        "·····",
        "WATCHDOG ALPHA 가 잠에서 깨어남.",
        "추적 시작.",
        "도망칠 수 없다.",
    ),
    phases=(
        BossPhase(
            index=0,
            name="추적",
            hp_threshold_pct=100,
            intro_line="",
            color=(200, 150, 100),
        ),
        BossPhase(
            index=1,
            name="분노",
            hp_threshold_pct=50,
            intro_line="▸ 무리 호출 — 공격 빈도 증가",
            color=(255, 100, 100),
            attack_bonus_pct=25,
            speed_bonus_pct=50,
            screen_shake_intensity=2.5,
            special_ability="pack_howl",
        ),
        BossPhase(
            index=2,
            name="집중",
            hp_threshold_pct=20,
            intro_line="▸ 마지막 추적 — 결정타",
            color=(255, 50, 50),
            attack_bonus_pct=100,
            speed_bonus_pct=20,
            screen_shake_intensity=3.5,
            special_ability="alpha_strike",
            # Phase I: WATCHDOG ALPHA phase 2 calls pack members
            spawn_minions=("watchdog", "watchdog"),
        ),
    ),
    death_lines=(
        "WATCHDOG ALPHA:",
        "·····",
        "...woof?",
        "[연결 종료]",
    ),
)

ALL_BOSSES: dict[str, BossSpec] = {
    GOLIATH_PRIME.id: GOLIATH_PRIME,
    BLACK_ICE_LORD.id: BLACK_ICE_LORD,
    WATCHDOG_ALPHA.id: WATCHDOG_ALPHA,
}


def is_boss(ice_id: str) -> bool:
    """Check if an ICE id refers to a BOSS."""
    return ice_id in ALL_BOSSES


def get_boss_spec(ice_id: str) -> BossSpec | None:
    """Get the BOSS spec for an id, or None if not a BOSS."""
    return ALL_BOSSES.get(ice_id)


def get_next_phase(spec: BossSpec, current_hp_pct: int) -> BossPhase | None:
    """Get the next phase to activate given the current HP percentage.

    A phase activates when current_hp_pct drops to or below its threshold.
    Returns None if no phase transition should occur.
    """
    # Phases are ordered high-to-low. Find the highest-index phase
    # whose threshold the HP has just crossed.
    for phase in reversed(spec.phases):
        if current_hp_pct <= phase.hp_threshold_pct:
            return phase
    return None


def should_trigger_phase_5(boss: Combatant, current_phase: BossPhase) -> bool:
    """Return True if boss should enter Phase 5 (Last Stand).

    Phase 5 triggers when currently in phase 4, HP < 10%, and the
    phase has phase5_super_skill configured.
    """
    if current_phase.index != 4:
        return False
    if boss.max_hp <= 0:
        return False
    if current_phase.phase5_super_skill is None:
        return False
    result: bool = boss.hp / boss.max_hp < 0.10
    return result


def boss_phase_5_dialogue(phase: BossPhase) -> str:
    """Return the Phase 5 (Last Stand) dialogue for a phase."""
    return phase.phase5_dialogue


def apply_phase_buff(phase: BossPhase, base_attack: int, base_speed_ms: int) -> tuple[int, int]:
    """Apply a phase's stat buff to base attack and attack speed.

    Returns (new_attack, new_speed_ms).
    """
    new_attack = base_attack * (100 + phase.attack_bonus_pct) // 100
    new_speed = base_speed_ms * 100 // (100 + phase.speed_bonus_pct)
    return (new_attack, new_speed)


# ----------------------------------------------------------------------------
# Boss intro sequence (3-5 second multi-line)
# ----------------------------------------------------------------------------


# Re-export cinematic + spawner functions from bosses_cinematic.py for backwards compat
def boss_epilogue_lines(spec: BossSpec) -> tuple[str, ...]:
    """Return the BOSS's death dialogue."""
    return spec.death_lines


from .bosses_cinematic import (  # noqa: E402,F401
    boss_death_sequence,
    boss_intro_sequence,
    boss_phase_5_sequence,
    boss_phase_transition,
    spawn_boss_death,
    spawn_boss_intro,
    spawn_boss_phase5,
    spawn_boss_phase_transition,
)
