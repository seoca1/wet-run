"""Combat visual effects system — thin re-export facade (ADR-0144 module split).

Provides ASCII animations, particles, screen shake, status icons,
and cinematic effects for combat. Pure ASCII rendering per ADR-0002.

Layer architecture:
  Layer 1: Hit feedback (flash, floating numbers, particles, shake)
  Layer 2: Skill animations (15 unique effects, 5-15 frames each)
  Layer 3: ICE-type specific (5 ICE types, unique intro/death)
  Layer 4: Status effect icons (persistent)
  Layer 5: Cinematic intro/finish (slow-mo, glitch, combo counter)

Module structure (post ADR-0144):
  - combat/effects_data: 12 data types (dataclasses + StrEnums)
  - combat/effects (this file): thin re-export facade
  - combat/effects_vfx: animation sequences + CombatEffects + spawn functions
  - combat/palette: color constants

Backward compat: existing imports of
``from wet_run.combat.effects import X`` continue to work via
the re-exports below (no import site changes required).
"""

from __future__ import annotations

# Data types (ADR-0144: moved from this module to effects_data).
from .effects_data import (  # noqa: F401 - re-exports for backward compat
    Animation,
    AnimationFrame,
    CinematicSequence,
    ComboCounter,
    FloatingNumber,
    HitFlash,
    IceType,
    Particle,
    ParticleSystem,
    ScreenFlash,
    ScreenShake,
    StatusIcon,
)

# Behavior (re-exported from effects_vfx for backward compat — ADR-0112).
from .effects_vfx import (  # noqa: F401,F402 - re-exports for backward compat
    # Class (moved to effects_vfx per ADR-0112 module split)
    CombatEffects,
    # Skill effect animations (Layer 2)
    attack_animation,
    # Cinematic sequences (Layer 3 + 5)
    boss_phase_transition_sequence,
    buff_animation,
    counter_animation,
    debuff_animation,
    detect_animation,
    dot_animation,
    get_animation_for_effect,
    heal_animation,
    heavy_attack_animation,
    ice_death_sequence,
    ice_intro_sequence,
    lifesteal_animation,
    multi_hit_animation,
    pierce_animation,
    regen_animation,
    shield_animation,
    # Spawn effects (Layer 1)
    spawn_aoe_screen_flash,
    spawn_critical,
    spawn_data_acquired,
    spawn_hit_effects,
    spawn_ice_death,
    spawn_ice_intro,
    spawn_jackin_glitch,
    spawn_jackout_whiteout,
    spawn_room_flash,
    spawn_status_icon,
    stun_animation,
)

# Palette color constants (re-exported from palette for backward compat).
from .palette import (  # noqa: F401 - re-exports for backward compat
    BUFF_COLOR,
    CRIT_COLOR,
    DAMAGE_COLOR,
    DEBUFF_COLOR,
    DEFAULT_COLOR,
    GLITCH_COLOR,
    HEAL_COLOR,
    ICE_BREAK_COLOR,
    SHIELD_COLOR,
    STUN_COLOR,
)

__all__ = [
    # Data classes (re-exported from effects_data)
    "IceType",
    "StatusIcon",
    "AnimationFrame",
    "Animation",
    "Particle",
    "ParticleSystem",
    "ScreenShake",
    "FloatingNumber",
    "HitFlash",
    "ScreenFlash",
    "CinematicSequence",
    "ComboCounter",
    # Behavior (re-exported from effects_vfx)
    "CombatEffects",
    "attack_animation",
    "buff_animation",
    "counter_animation",
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
    "boss_phase_transition_sequence",
    "ice_death_sequence",
    "ice_intro_sequence",
    "spawn_aoe_screen_flash",
    "spawn_critical",
    "spawn_data_acquired",
    "spawn_hit_effects",
    "spawn_ice_death",
    "spawn_ice_intro",
    "spawn_jackin_glitch",
    "spawn_jackout_whiteout",
    "spawn_room_flash",
    "spawn_status_icon",
]
