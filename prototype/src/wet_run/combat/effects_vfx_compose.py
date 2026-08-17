"""Combat visual effects — composition container + spawn functions (ADR-0145 module split).

Extracted from combat/effects_vfx.py to reduce that module below the
856 LOC threshold. Owns:
  - CombatEffects dataclass (Layer 1 container holding all active effects)
  - 10 spawn functions used by combat_view (Layer 1 hit feedback, boss events,
    matrix/dungeon VFX per ADR-0060 Phase 1.5)

Module structure (post ADR-0145):
  - combat/effects_vfx_animations: 14 animation generators + factory
  - combat/effects_vfx_cinematics: ICE intro/death + boss phase transitions
  - combat/effects_vfx_compose (this file): CombatEffects class + 10 spawn functions
  - combat/effects_vfx: thin re-export facade
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .effects_data import (
    Animation,
    CinematicSequence,
    ComboCounter,
    FloatingNumber,
    HitFlash,
    IceType,
    ParticleSystem,
    ScreenFlash,
    ScreenShake,
    StatusIcon,
)
from .effects_vfx_animations import critical_hit_animation, get_animation_for_effect
from .effects_vfx_cinematics import ice_death_sequence, ice_intro_sequence
from .palette import (
    CRIT_COLOR,
    DAMAGE_COLOR,
    HEAL_COLOR,
)


@dataclass(slots=True)
class CombatEffects:
    """Container for all active combat visual effects.

    One instance lives in AppState. combat_view.py reads it to render
    overlays and steps it each frame.
    """

    animations: list[Animation] = field(default_factory=list)
    particles: ParticleSystem = field(default_factory=ParticleSystem)
    shake: ScreenShake = field(default_factory=ScreenShake)
    floating_numbers: list[FloatingNumber] = field(default_factory=list)
    hit_flash: HitFlash = field(default_factory=HitFlash)
    screen_flash: ScreenFlash = field(default_factory=ScreenFlash)
    cinematic: CinematicSequence | None = None
    combo: ComboCounter = field(default_factory=ComboCounter)
    slow_motion_ms: int = 0  # When > 0, time runs at half speed

    def step(self, dt_ms: int) -> None:
        """Step all effects forward by dt_ms."""
        if self.slow_motion_ms > 0:
            dt_ms = dt_ms // 2
            self.slow_motion_ms = max(0, self.slow_motion_ms - 16)
        for anim in self.animations:
            anim.step(dt_ms)
        self.animations = [a for a in self.animations if not a.is_finished]
        self.particles.step(dt_ms)
        for fn in self.floating_numbers:
            fn.step(dt_ms)
        self.floating_numbers = [f for f in self.floating_numbers if f.is_alive]
        self.shake.step(dt_ms)
        self.hit_flash.step(dt_ms)
        self.screen_flash.step(dt_ms)
        if self.cinematic is not None:
            self.cinematic.step(dt_ms)
            if self.cinematic.is_finished:
                self.cinematic = None

    def clear(self) -> None:
        """Reset all effects (e.g. on combat end)."""
        self.animations.clear()
        self.particles.clear()
        self.floating_numbers.clear()
        self.shake = ScreenShake()
        self.hit_flash = HitFlash()
        self.screen_flash = ScreenFlash()
        self.cinematic = None
        self.combo.reset()
        self.slow_motion_ms = 0

    def has_active_effects(self) -> bool:
        """True if any effect is currently rendering."""
        return bool(
            self.animations
            or self.particles.particles
            or self.floating_numbers
            or self.shake.intensity > 0
            or self.hit_flash.is_active
            or self.screen_flash.is_active
            or self.cinematic is not None
        )


# ----------------------------------------------------------------------------
# Effect spawners (high-level API for combat_view)
# ----------------------------------------------------------------------------


def spawn_hit_effects(
    effects: CombatEffects,
    target_x: float,
    target_y: float,
    damage: int,
    *,
    effect_type: str = "attack",
    is_crit: bool = False,
    hit_color: tuple[int, int, int] | None = None,
) -> None:
    """Spawn a complete hit effect package: animation, particles, number, flash, shake.

    This is the high-level entry point called from combat_view when a
    skill resolves. It triggers all Layer 1+2 visuals for one hit.
    """
    # Layer 2: skill animation
    effects.animations.append(get_animation_for_effect(effect_type))

    # Layer 1: particles
    if is_crit:
        effects.particles.spawn_burst(
            target_x,
            target_y,
            chars=("✦", "★", "*", "✧"),
            color=CRIT_COLOR,
            count=10,
            speed=50.0,
        )
    elif effect_type in ("heal", "regen"):
        effects.particles.spawn_upward(target_x, target_y, color=HEAL_COLOR)
    elif effect_type in ("dot", "poison"):
        effects.particles.spawn_burst(
            target_x,
            target_y,
            chars=("•", "○", "◌"),
            color=(180, 100, 220),
            count=6,
            speed=20.0,
        )
    else:
        effects.particles.spawn_burst(
            target_x,
            target_y,
            chars=("*", "+", "x", "·", "✦"),
            color=DAMAGE_COLOR,
            count=6,
            speed=30.0,
        )

    # Layer 1: floating number
    if damage > 0:
        color = hit_color or (CRIT_COLOR if is_crit else DAMAGE_COLOR)
        effects.floating_numbers.append(
            FloatingNumber(
                x=target_x,
                y=target_y - 1.0,
                value=damage,
                color=color,
                is_crit=is_crit,
            )
        )

    # Layer 1: hit flash
    flash_color = (255, 255, 255) if is_crit else (255, 220, 100)
    effects.hit_flash.trigger(color=flash_color, duration_ms=120)

    # Layer 1: screen shake (only for big hits)
    if is_crit or effect_type in ("heavy_attack", "multi_hit"):
        effects.shake.trigger(intensity=2.5, duration_ms=200)
    elif effect_type in ("attack", "pierce"):
        effects.shake.trigger(intensity=1.0, duration_ms=80)


def spawn_ice_intro(effects: CombatEffects, ice_type: IceType, name: str) -> None:
    """Spawn a cinematic intro for an ICE type."""
    effects.cinematic = ice_intro_sequence(ice_type, name)
    effects.slow_motion_ms = effects.cinematic.total_duration_ms


def spawn_ice_death(effects: CombatEffects, ice_type: IceType) -> None:
    """Spawn a cinematic death for an ICE type."""
    effects.cinematic = ice_death_sequence(ice_type)
    effects.slow_motion_ms = 0  # No slow-mo for death
    effects.shake.trigger(intensity=2.0, duration_ms=250)


def spawn_critical(effects: CombatEffects, x: float, y: float, damage: int) -> None:
    """Spawn a critical hit effect package."""
    effects.animations.append(critical_hit_animation())
    effects.particles.spawn_burst(x, y, chars=("✦", "★"), color=CRIT_COLOR, count=12, speed=60.0)
    effects.floating_numbers.append(
        FloatingNumber(x=x, y=y - 1.0, value=damage, color=CRIT_COLOR, is_crit=True)
    )
    effects.hit_flash.trigger(color=(255, 255, 200), duration_ms=150)
    effects.shake.trigger(intensity=3.5, duration_ms=250)
    effects.slow_motion_ms = 250  # 250ms of slow-mo


def spawn_status_icon(combatant: object, status: StatusIcon) -> None:
    """Attach a status icon to a combatant. (Placeholder for HUD integration.)"""
    # In a full implementation this would push to a list on the combatant
    # or set a flag. combat_view reads the list to display icons.
    if not hasattr(combatant, "status_icons"):
        combatant.status_icons = []  # type: ignore[attr-defined]
    if status not in combatant.status_icons:  # type: ignore[attr-defined]
        combatant.status_icons.append(status)  # type: ignore[attr-defined]


# ----------------------------------------------------------------------------
# Matrix / dungeon VFX (ADR-0060 Phase 1.5)
#
# These provide the cyberspace atmosphere that the simplified NetHack-style
# map no longer carries. The map renders pure gameplay UI; cyberspace is
# layered as effects.
# ----------------------------------------------------------------------------


def spawn_jackin_glitch(effects: CombatEffects) -> None:
    """Spawn a one-shot 'jack-in' glitch VFX (Phase 1.5)."""
    effects.particles.spawn_burst(
        x=0.0,
        y=0.0,
        chars=("▓", "▒", "░", "+", "·", "/", "\\"),
        color=(120, 220, 220),
        count=18,
        speed=45.0,
        life_ms=500,
        spread=math.tau,
    )
    effects.particles.spawn_burst(
        x=0.0,
        y=0.0,
        chars=("▒", "*", "+"),
        color=(220, 100, 220),
        count=8,
        speed=30.0,
        life_ms=300,
        spread=math.tau,
    )
    effects.shake.trigger(intensity=80, duration_ms=180)
    effects.hit_flash.trigger(color=(120, 220, 220), duration_ms=120)
    effects.cinematic = CinematicSequence(
        name="jackin",
        phases=(
            (">> JACKING IN...", (120, 220, 220), 180),
            (">> SCANNING HOST...", (220, 180, 100), 180),
            (">> CYBERSPACE LOADED", (180, 220, 120), 220),
        ),
    )


def spawn_room_flash(
    effects: CombatEffects,
    color: tuple[int, int, int] = (180, 180, 100),
) -> None:
    """Spawn a short color flash on room transition (Phase 1.5)."""
    effects.hit_flash.trigger(color=color, duration_ms=80)
    effects.particles.spawn_burst(
        x=1.0,
        y=1.0,
        chars=("·", "+", "·"),
        color=color,
        count=4,
        speed=10.0,
        life_ms=160,
        spread=math.pi,
    )


def spawn_aoe_screen_flash(
    effects: CombatEffects,
    color: tuple[int, int, int] = (255, 80, 80),
    duration_ms: int = 280,
) -> None:
    """Spawn a full-screen flash for AoE damage events (ADR-0125 follow-up).

    Triggers ScreenFlash (full-viewport, distinct from tile-level HitFlash),
    paired with screen shake for impact.
    """
    effects.screen_flash.trigger(color=color, duration_ms=duration_ms)
    effects.shake.trigger(intensity=0.6, duration_ms=duration_ms)


def spawn_data_acquired(effects: CombatEffects, x: float = 0.0, y: float = 0.0) -> None:
    """Spawn a 'data fragment recovered' VFX on DATA room pickup (Phase 1.5)."""
    effects.particles.spawn_burst(
        x=x,
        y=y,
        chars=("$", "·", "+", "·"),
        color=(255, 215, 0),
        count=14,
        speed=40.0,
        life_ms=500,
        spread=math.tau,
    )
    effects.hit_flash.trigger(color=(255, 215, 0), duration_ms=120)
    effects.cinematic = CinematicSequence(
        name="data_acquired",
        phases=(
            (">> DATA FRAGMENT RECOVERED", (255, 215, 0), 280),
            ("+ CREDITS + REPUTATION", (220, 220, 180), 200),
        ),
    )


def spawn_jackout_whiteout(effects: CombatEffects) -> None:
    """Spawn a 'jack-out' whiteout VFX on EXIT room (Phase 1.5)."""
    effects.hit_flash.trigger(color=(255, 255, 255), duration_ms=260)
    effects.particles.spawn_burst(
        x=0.0,
        y=0.0,
        chars=("·", "+", "·"),
        color=(220, 220, 220),
        count=10,
        speed=20.0,
        life_ms=400,
        spread=math.tau,
    )
    effects.cinematic = CinematicSequence(
        name="jackout",
        phases=(
            (">> JACKING OUT...", (220, 220, 220), 220),
            (">> CONNECTION SEVERED", (180, 180, 220), 220),
            (">> MATRIX CLOSED", (140, 140, 180), 200),
        ),
    )


__all__ = [
    "CombatEffects",
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
