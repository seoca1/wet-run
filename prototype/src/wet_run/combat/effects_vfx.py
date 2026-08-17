"""Combat visual effects — thin re-export facade (ADR-0145 module split).

Original module extracted from combat/effects.py (ADR-0112) to reduce that
module below the 1000+ LOC threshold per ADR-0110. Now further split into
3 concern modules (ADR-0145) to reduce this module below the 700-800
LOC exception threshold:

  - combat/effects_vfx_animations: 14 skill effect animation generators
  - combat/effects_vfx_cinematics: ICE intro/death + boss phase sequences
  - combat/effects_vfx_compose: CombatEffects dataclass + 10 spawn functions
  - combat/effects_vfx (this file): thin re-export facade

Module structure (post ADR-0145):
  - combat/effects_data: 12 data types (dataclasses + StrEnums) [ADR-0144]
  - combat/effects: thin re-export facade [ADR-0144]
  - combat/effects_vfx_animations: skill animation generators
  - combat/effects_vfx_cinematics: ICE cinematic sequences
  - combat/effects_vfx_compose: CombatEffects + spawn functions
  - combat/effects_vfx (this file): thin re-export facade
  - combat/palette: color constants

Backward compat: existing imports of
``from wet_run.combat.effects_vfx import X`` continue to work via
the re-exports below (no import site changes required).
"""

from __future__ import annotations

# Data types (re-exported from effects_data per ADR-0144).
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

# Animation generators (ADR-0145).
from .effects_vfx_animations import (  # noqa: F401 - re-exports for backward compat
    SKILL_EFFECT_ANIMATIONS,
    attack_animation,
    buff_animation,
    counter_animation,
    critical_hit_animation,
    debuff_animation,
    detect_animation,
    dot_animation,
    get_animation_for_effect,
    heal_animation,
    heavy_attack_animation,
    lifesteal_animation,
    multi_hit_animation,
    pierce_animation,
    regen_animation,
    shield_animation,
    stun_animation,
)

# Cinematic sequences (ADR-0145).
from .effects_vfx_cinematics import (  # noqa: F401 - re-exports for backward compat
    boss_phase_transition_sequence,
    ice_death_sequence,
    ice_intro_sequence,
)

# CombatEffects class + spawn functions (ADR-0145).
from .effects_vfx_compose import (  # noqa: F401 - re-exports for backward compat
    CombatEffects,
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
)

__all__ = [
    "Animation",
    "AnimationFrame",
    "CinematicSequence",
    "CombatEffects",
    "ComboCounter",
    "FloatingNumber",
    "HitFlash",
    "IceType",
    "Particle",
    "ParticleSystem",
    "SKILL_EFFECT_ANIMATIONS",
    "ScreenFlash",
    "ScreenShake",
    "StatusIcon",
    "attack_animation",
    "boss_phase_transition_sequence",
    "buff_animation",
    "counter_animation",
    "critical_hit_animation",
    "debuff_animation",
    "detect_animation",
    "dot_animation",
    "get_animation_for_effect",
    "heal_animation",
    "heavy_attack_animation",
    "ice_death_sequence",
    "ice_intro_sequence",
    "lifesteal_animation",
    "multi_hit_animation",
    "pierce_animation",
    "regen_animation",
    "shield_animation",
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
    "stun_animation",
]
