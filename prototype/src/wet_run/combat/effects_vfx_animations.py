"""Combat visual effects — animation generators (ADR-0145 module split).

Extracted from combat/effects_vfx.py to reduce that module below the
856 LOC threshold (700-800 exception). Provides 14 skill effect animation
generators + critical hit animation + the effect→animation factory.

Module structure (post ADR-0145):
  - combat/effects_vfx_animations (this file): 14 animation generators + factory
  - combat/effects_vfx_cinematics: ICE-type intro/death + boss phase transitions
  - combat/effects_vfx_compose: CombatEffects class + 10 spawn functions
  - combat/effects_vfx: thin re-export facade

All Animation instances return Animation(frames=(...)) with color/timing
matching the visual aesthetic established by ADR-0002 (pure ASCII rendering).
"""

from __future__ import annotations

from collections.abc import Callable

from .effects_data import Animation, AnimationFrame
from .palette import (
    BUFF_COLOR,
    CRIT_COLOR,
    DAMAGE_COLOR,
    DAMAGE_FLASH_COLOR,
    DEBUFF_COLOR,
    DEFAULT_COLOR,
    GOLIATH_PARTICLE_COLOR,
    HEAL_COLOR,
    HIT_FLASH_COLOR,
    ICE_BREAK_COLOR,
    ICE_FADE_PURPLE,
    ICE_GREEN_BRIGHT,
    ICE_GREEN_PALE,
    ICE_RED_FADED,
    ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR,
    ICE_WARN_GOLD,
    ORANGE,
    SHIELD_COLOR,
    STUN_COLOR,
    TA_CONSTRUCT_P2_COLOR,
    WARM,
    YELLOW_BRIGHT,
    YELLOW_PALE,
)


def attack_animation(damage: int = 0) -> Animation:
    """ATTACK: a forward strike with target flash."""
    return Animation(
        frames=(
            AnimationFrame("[=>", DAMAGE_COLOR, 60),
            AnimationFrame("[==>", DAMAGE_COLOR, 60),
            AnimationFrame("[===>", CRIT_COLOR, 80),
            AnimationFrame("[===>", HIT_FLASH_COLOR, 60),  # flash
            AnimationFrame("[===>", DEFAULT_COLOR, 80),
        )
    )


def heavy_attack_animation() -> Animation:
    """HEAVY_ATTACK: charge, slam, screen shake trigger."""
    return Animation(
        frames=(
            AnimationFrame("[<=", BUFF_COLOR, 200),  # charge
            AnimationFrame("[<==", BUFF_COLOR, 150),
            AnimationFrame("[<===", (255, 200, 50), 200),  # windup peak
            AnimationFrame("[<<<<", ORANGE, 80),  # slam
            AnimationFrame("[*<<<*", ICE_BREAK_COLOR, 120),  # impact
            AnimationFrame("·[<<<]·", (150, 150, 200), 150),  # shockwave
        )
    )


def pierce_animation() -> Animation:
    """PIERCE: arrow passes through target."""
    return Animation(
        frames=(
            AnimationFrame("---->", WARM, 60),
            AnimationFrame("----==>", (255, 200, 100), 60),
            AnimationFrame("----==>", HIT_FLASH_COLOR, 50),  # flash
            AnimationFrame("----==>", WARM, 60),
            AnimationFrame("---->", (150, 150, 100), 80),
        )
    )


def multi_hit_animation() -> Animation:
    """MULTI_HIT: 3 quick strikes."""
    return Animation(
        frames=(
            AnimationFrame("[>", DAMAGE_COLOR, 50),
            AnimationFrame("[>", HIT_FLASH_COLOR, 30),
            AnimationFrame("[>>", DAMAGE_COLOR, 50),
            AnimationFrame("[>>", HIT_FLASH_COLOR, 30),
            AnimationFrame("[>>>", DAMAGE_COLOR, 50),
            AnimationFrame("[>>>", (255, 200, 100), 80),
        )
    )


def dot_animation() -> Animation:
    """DOT/POISON: toxic particles around target."""
    return Animation(
        frames=(
            AnimationFrame("(•*•)", ICE_FADE_PURPLE, 100),
            AnimationFrame("(•••)", (200, 80, 220), 100),
            AnimationFrame("·•••·", ICE_FADE_PURPLE, 100),
            AnimationFrame("(•••)", (160, 80, 200), 100),
            AnimationFrame("(•*•)", (140, 60, 180), 150),
        )
    )


def shield_animation() -> Animation:
    """SHIELD: hexagonal shield pattern around self."""
    return Animation(
        frames=(
            AnimationFrame("·❖·", SHIELD_COLOR, 100),
            AnimationFrame("❖❖❖", (180, 230, 255), 100),
            AnimationFrame("❖●❖", HIT_FLASH_COLOR, 80),
            AnimationFrame("❖❖❖", SHIELD_COLOR, 100),
            AnimationFrame("·❖·", (100, 180, 230), 150),
        )
    )


def heal_animation() -> Animation:
    """HEAL: rising plus signs."""
    return Animation(
        frames=(
            AnimationFrame("·+·", HEAL_COLOR, 100),
            AnimationFrame("·✚·", (120, 255, 150), 100),
            AnimationFrame("·❀·", (200, 255, 220), 100),
            AnimationFrame("+✚❀", ICE_GREEN_PALE, 100),
            AnimationFrame("✚❀✚", (100, 255, 150), 150),
        )
    )


def regen_animation() -> Animation:
    """REGEN: gentle pulse of plus signs."""
    return Animation(
        frames=(
            AnimationFrame("·+·", ICE_GREEN_BRIGHT, 150),
            AnimationFrame("·+·", (150, 220, 170), 150),
            AnimationFrame("·+·", ICE_GREEN_BRIGHT, 150),
        )
    )


def buff_animation() -> Animation:
    """BUFF: upward arrow burst."""
    return Animation(
        frames=(
            AnimationFrame("·↑·", BUFF_COLOR, 100),
            AnimationFrame("·⇈·", (255, 240, 150), 100),
            AnimationFrame("↑↑↑", YELLOW_PALE, 100),
            AnimationFrame("·⇈·", BUFF_COLOR, 100),
            AnimationFrame("·↑·", (200, 180, 100), 150),
        )
    )


def debuff_animation() -> Animation:
    """DEBUFF: downward arrow."""
    return Animation(
        frames=(
            AnimationFrame("·↓·", DEBUFF_COLOR, 100),
            AnimationFrame("·⇊·", (230, 130, 255), 100),
            AnimationFrame("↓↓↓", DEBUFF_COLOR, 100),
            AnimationFrame("·⇊·", DEBUFF_COLOR, 100),
            AnimationFrame("·↓·", (150, 80, 200), 150),
        )
    )


def stun_animation() -> Animation:
    """STUN: stars spinning around target."""
    return Animation(
        frames=(
            AnimationFrame("✦·✦", STUN_COLOR, 80),
            AnimationFrame("·✦·", (255, 255, 150), 80),
            AnimationFrame("✦·✦", YELLOW_BRIGHT, 80),
            AnimationFrame("·✦·", (255, 200, 50), 80),
            AnimationFrame("✦·✦", STUN_COLOR, 100),
        )
    )


def counter_animation() -> Animation:
    """COUNTER: shield bash returning damage."""
    return Animation(
        frames=(
            AnimationFrame("❖<", SHIELD_COLOR, 80),
            AnimationFrame("❖<<", (200, 230, 255), 80),
            AnimationFrame("❖✦<", HIT_FLASH_COLOR, 60),
            AnimationFrame("<❖✦", DAMAGE_COLOR, 80),
            AnimationFrame("·❖·", (150, 200, 230), 120),
        )
    )


def lifesteal_animation() -> Animation:
    """LIFESTEAL: red line from target to self."""
    return Animation(
        frames=(
            AnimationFrame("~~>", DAMAGE_COLOR, 80),
            AnimationFrame("~~=>", TA_CONSTRUCT_P2_COLOR, 80),
            AnimationFrame("~~==>", ICE_RED_FADED, 80),
            AnimationFrame("·✦·", HEAL_COLOR, 100),
            AnimationFrame("·+·", ICE_GREEN_PALE, 150),
        )
    )


def detect_animation() -> Animation:
    """DETECT: scanning reticle."""
    return Animation(
        frames=(
            AnimationFrame("[·]", SHIELD_COLOR, 100),
            AnimationFrame("[<·>]", (150, 220, 255), 100),
            AnimationFrame("[<·>]", (200, 240, 255), 100),
            AnimationFrame("[<!>]", STUN_COLOR, 100),
            AnimationFrame("[·]", SHIELD_COLOR, 150),
        )
    )


# Effect → animation factory
SKILL_EFFECT_ANIMATIONS: dict[str, Callable[[], Animation]] = {
    "attack": attack_animation,
    "heavy_attack": heavy_attack_animation,
    "pierce": pierce_animation,
    "multi_hit": multi_hit_animation,
    "dot": dot_animation,
    "poison": dot_animation,
    "shield": shield_animation,
    "heal": heal_animation,
    "regen": regen_animation,
    "buff": buff_animation,
    "debuff": debuff_animation,
    "stun": stun_animation,
    "counter": counter_animation,
    "lifesteal": lifesteal_animation,
    "detect": detect_animation,
}


def get_animation_for_effect(effect: str) -> Animation:
    """Get the animation for a SkillEffect name."""
    factory = SKILL_EFFECT_ANIMATIONS.get(effect, attack_animation)
    return factory()


def critical_hit_animation() -> Animation:
    """A multi-frame critical hit sequence with glitch."""
    return Animation(
        frames=(
            AnimationFrame("!·!", GOLIATH_PARTICLE_COLOR, 60),
            AnimationFrame("!!", DAMAGE_FLASH_COLOR, 60),
            AnimationFrame("·!·", (255, 200, 100), 60),
            AnimationFrame("!", ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR, 80),
            AnimationFrame("!", ICE_WARN_GOLD, 100),
        )
    )


__all__ = [
    "SKILL_EFFECT_ANIMATIONS",
    "attack_animation",
    "buff_animation",
    "counter_animation",
    "critical_hit_animation",
    "debuff_animation",
    "detect_animation",
    "dot_animation",
    "get_animation_for_effect",
    "heal_animation",
    "heavy_attack_animation",
    "lifesteal_animation",
    "multi_hit_animation",
    "pierce_animation",
    "regen_animation",
    "shield_animation",
    "stun_animation",
]
