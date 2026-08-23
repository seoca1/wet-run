"""Combat HUD: enhanced HP bars, low-HP warnings, camera effects.

Provides:
  - HealthBar: 2-tier (HP + shield) bar with smooth drain animation
  - LowHpState: pulsing red border, screen vignette at HP < 30%, < 10%
  - PhaseColorState: HP bar recolor on boss phase transition
  - DamageFlash / HealFlash: localized flash on HP bar
  - CameraVignette: screen edge darkening (low HP / boss phase)
  - CameraShake (alias for ScreenShake from effects)
  - ColorDesaturation: critical HP desaturation effect

All visual, no game logic. Pure ASCII rendering per ADR-0002.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# ASCII palette for HUD
# All colors are now centralized in palette.py
from .palette import (  # noqa: E402
    DAMAGE_COLOR,
    DAMAGE_FLASH_COLOR,
    HEAL_COLOR,
    HIT_FLASH_COLOR,
    HP_CRIT_COLOR,
    HP_HIGH_COLOR,
    HP_LOW_COLOR,
    HP_MID_COLOR,
    PHASE_COLORS,
    SHIELD_COLOR,
    VIGNETTE_COLOR,
)

# ----------------------------------------------------------------------------
# Health state
# ----------------------------------------------------------------------------


class AlertLevel(IntEnum):
    """HP alert level (drives visual treatment)."""

    HEALTHY = 0  # > 50% HP
    LOW = 1  # <= 30% HP
    CRITICAL = 2  # <= 10% HP


@dataclass(slots=True)
class HealthState:
    """Current HP and shield with smooth drain animation.

    The bar smoothly transitions from `displayed_hp` toward `target_hp`
    over `drain_ms` milliseconds. This creates the "draining" effect
    when an enemy hits the player.
    """

    current_hp: int
    max_hp: int
    current_shield: int = 0
    max_shield: int = 0
    # Smooth drain animation
    displayed_hp: float = 0
    displayed_shield: float = 0
    drain_ms: int = 0
    # Recent damage (for visual damage flash)
    last_damage_ms: int = -10000  # Time of last damage
    last_heal_ms: int = -10000  # Time of last heal
    flash_duration_ms: int = 200


@dataclass(slots=True)
class PhaseColorState:
    """Current HP bar color based on boss phase.

    Boss phase transition can change the bar color from green
    to phase-specific colors (warning → danger → critical).
    """

    phase_index: int = 0
    custom_color: tuple[int, int, int] | None = None
    transition_ms: int = 0
    elapsed_ms: int = 0

    def set_phase(self, phase_index: int, color: tuple[int, int, int] | None = None) -> None:
        """Start a 400ms transition to the given phase with optional accent color."""
        self.phase_index = phase_index
        self.custom_color = color
        self.transition_ms = 400
        self.elapsed_ms = 0

    def step(self, dt_ms: int) -> None:
        """Advance the phase transition timer; transitions complete in 400ms."""
        if self.transition_ms > 0:
            self.elapsed_ms += dt_ms
            if self.elapsed_ms >= self.transition_ms:
                self.transition_ms = 0

    @property
    def transition_progress(self) -> float:
        """Return 0.0-1.0 progress of the current phase transition (1.0 if idle)."""
        if self.transition_ms <= 0:
            return 1.0
        return min(1.0, self.elapsed_ms / self.transition_ms)


# ----------------------------------------------------------------------------
# Low HP state
# ----------------------------------------------------------------------------


@dataclass(slots=True)
class LowHpState:
    """Visual feedback when player HP is low.

    Activates at 30% HP (pulse) and intensifies at 10% (critical).
    Drives:
    - HP bar color change
    - Screen vignette
    - Audio cue (placeholder)
    """

    alert_level: AlertLevel = AlertLevel.HEALTHY
    pulse_elapsed_ms: int = 0
    pulse_period_ms: int = 600  # Pulse every 600ms
    vignette_intensity: float = 0.0  # 0.0 to 1.0
    desaturation: float = 0.0  # 0.0 to 1.0


def update_low_hp_state(state: LowHpState, hp_pct: int, dt_ms: int) -> AlertLevel:
    """Update low HP state based on current HP percentage.

    Returns the new alert level for use by other systems.
    """
    if hp_pct > 30:
        new_level = AlertLevel.HEALTHY
    elif hp_pct > 10:
        new_level = AlertLevel.LOW
    else:
        new_level = AlertLevel.CRITICAL

    if new_level != state.alert_level:
        state.alert_level = new_level

    # Pulse
    state.pulse_elapsed_ms += dt_ms
    if state.pulse_elapsed_ms >= state.pulse_period_ms:
        state.pulse_elapsed_ms = 0

    # Vignette intensity (smoother transition)
    target_vignette = {
        AlertLevel.HEALTHY: 0.0,
        AlertLevel.LOW: 0.3,
        AlertLevel.CRITICAL: 0.7,
    }[state.alert_level]
    # Lerp toward target
    state.vignette_intensity += (target_vignette - state.vignette_intensity) * 0.1

    # Desaturation (critical only)
    target_desat = 0.5 if state.alert_level == AlertLevel.CRITICAL else 0.0
    state.desaturation += (target_desat - state.desaturation) * 0.05

    return state.alert_level


def is_pulsing(state: LowHpState) -> bool:
    """True during the first half of the pulse period (for visual pulse)."""
    return state.pulse_elapsed_ms < state.pulse_period_ms // 2


# ----------------------------------------------------------------------------
# Health bar rendering
# ----------------------------------------------------------------------------


def render_health_bar(
    state: HealthState,
    phase_color: PhaseColorState | None = None,
    low_hp: LowHpState | None = None,
    width: int = 20,
) -> str:
    """Render a 2-tier HP bar (HP + shield) as ASCII text.

    Format: [████████░░░░░░░░░] 60/100 HP [▓▓▓░░] 30/50 SH
    """
    hp_pct = state.current_hp / state.max_hp if state.max_hp > 0 else 0
    displayed_pct = state.displayed_hp / state.max_hp if state.max_hp > 0 else 0
    shield_pct = state.current_shield / state.max_shield if state.max_shield > 0 else 0

    # HP bar fill (using block characters for smooth fill)
    filled_hp = int(round(displayed_pct * width))
    empty_hp = width - filled_hp

    # Color selection
    if phase_color is not None and phase_color.custom_color is not None:
        # Boss phase color (with possible transition flash)
        if phase_color.transition_ms > 0:
            # Flash to white during transition
            color = HIT_FLASH_COLOR
        else:
            color = phase_color.custom_color
    elif hp_pct > 0.5:
        color = HP_HIGH_COLOR
    elif hp_pct > 0.3:
        color = HP_MID_COLOR
    elif hp_pct > 0.1:
        color = HP_LOW_COLOR
    else:
        color = HP_CRIT_COLOR

    # Low HP pulse: alternate between dim and bright
    if low_hp is not None and low_hp.alert_level != AlertLevel.HEALTHY:
        if is_pulsing(low_hp):
            color = (min(255, color[0] + 30), color[1], color[2])

    # Build HP bar
    bar_chars = "█" * filled_hp + "░" * empty_hp
    hp_bar = f"[{bar_chars}]"

    # Shield bar (overlay)
    shield_str = ""
    if state.max_shield > 0:
        filled_shield = int(round(shield_pct * width))
        empty_shield = width - filled_shield
        shield_chars = "▓" * filled_shield + "░" * empty_shield
        shield_str = f" [{shield_chars}] SH"

    # Numeric display
    result = f"{hp_bar} {state.current_hp}/{state.max_hp} HP{shield_str}"
    return result


def render_health_bar_rich(
    state: HealthState,
    *,
    phase_color: PhaseColorState | None = None,
    low_hp: LowHpState | None = None,
    width: int = 20,
) -> tuple[str, tuple[int, int, int]]:
    """Like render_health_bar but returns (text, color) for color rendering."""
    text = render_health_bar(state, phase_color, low_hp, width)

    # Compute color
    hp_pct = state.current_hp / state.max_hp if state.max_hp > 0 else 0
    if phase_color is not None and phase_color.custom_color is not None:
        # During transition, flash to white
        if phase_color.transition_ms > 0:
            color = HIT_FLASH_COLOR
        else:
            color = phase_color.custom_color
    elif hp_pct > 0.5:
        color = HP_HIGH_COLOR
    elif hp_pct > 0.3:
        color = HP_MID_COLOR
    elif hp_pct > 0.1:
        color = HP_LOW_COLOR
    else:
        color = HP_CRIT_COLOR

    if low_hp is not None and low_hp.alert_level != AlertLevel.HEALTHY:
        if is_pulsing(low_hp):
            color = (min(255, color[0] + 30), color[1], color[2])

    return (text, color)


# ----------------------------------------------------------------------------
# Damage / heal flash
# ----------------------------------------------------------------------------


@dataclass(slots=True)
class BarFlash:
    """Brief flash on a HP bar (damage=red, heal=green)."""

    duration_ms: int = 200
    elapsed_ms: int = 0
    color: tuple[int, int, int] = DAMAGE_COLOR
    is_active: bool = False

    def trigger(self, color: tuple[int, int, int], duration_ms: int = 200) -> None:
        """Start a screen flash with the given RGB color and duration in ms."""
        self.color = color
        self.duration_ms = duration_ms
        self.elapsed_ms = 0
        self.is_active = True

    def step(self, dt_ms: int) -> None:
        """Advance the flash timer; deactivate when duration expires."""
        if self.is_active:
            self.elapsed_ms += dt_ms
            if self.elapsed_ms >= self.duration_ms:
                self.is_active = False

    @property
    def alpha(self) -> float:
        """Return 0.0-1.0 fading alpha (1.0 just triggered, 0.0 expired/idle)."""
        if not self.is_active or self.duration_ms <= 0:
            return 0.0
        return max(0.0, 1.0 - self.elapsed_ms / self.duration_ms)


# ----------------------------------------------------------------------------
# Camera effects
# ----------------------------------------------------------------------------


@dataclass(slots=True)
class CameraVignette:
    """Screen-edge darkening effect.

    Activates at low HP (intensity from LowHpState) and during boss
    phase transitions (briefly). Renders as progressively darker
    edges around the screen.
    """

    intensity: float = 0.0  # 0.0 to 1.0
    flash_intensity: float = 0.0  # For phase transition
    flash_duration_ms: int = 0
    flash_elapsed_ms: int = 0

    def flash(self, intensity: float = 0.8, duration_ms: int = 400) -> None:
        """Trigger a one-shot flash overlay with given intensity (0.0-1.0)."""
        self.flash_intensity = intensity
        self.flash_duration_ms = duration_ms
        self.flash_elapsed_ms = 0

    def step(self, dt_ms: int) -> None:
        """Advance the flash timer; clear when duration expires."""
        if self.flash_duration_ms > 0:
            self.flash_elapsed_ms += dt_ms
            if self.flash_elapsed_ms >= self.flash_duration_ms:
                self.flash_intensity = 0.0
                self.flash_duration_ms = 0

    @property
    def total_intensity(self) -> float:
        """Return combined base + flash intensity, clamped to [0.0, 1.0]."""
        return min(1.0, self.intensity + self.flash_intensity)


def render_vignette(
    vignette: CameraVignette,
    width: int,
    height: int,
) -> str:
    """Render a screen vignette as a string of progressively darker chars.

    Returns a multi-line string showing the vignette pattern.
    """
    if vignette.total_intensity <= 0:
        return ""

    intensity = vignette.total_intensity
    lines = []
    max_dist = math.sqrt((width / 2) ** 2 + (height / 2) ** 2)
    for y in range(height):
        line = ""
        for x in range(width):
            # Distance from center
            dx = abs(x - width / 2)
            dy = abs(y - height / 2)
            dist = math.sqrt(dx * dx + dy * dy)
            # Normalize
            dist_norm = dist / max_dist
            # Vignette: darker at edges
            edge_factor = max(0, dist_norm - 0.5) * 2  # 0 in center, 1 at corners
            value = edge_factor * intensity
            if value > 0.7:
                line += "█"
            elif value > 0.4:
                line += "▓"
            elif value > 0.2:
                line += "░"
            else:
                line += " "
        lines.append(line)
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# HUD container
# ----------------------------------------------------------------------------


@dataclass(slots=True)
class CombatHUD:
    """Container for all HUD effects (HP bars, low-HP, camera)."""

    player_health: HealthState = field(
        default_factory=lambda: HealthState(current_hp=100, max_hp=100)
    )
    enemy_health: HealthState = field(
        default_factory=lambda: HealthState(current_hp=100, max_hp=100)
    )
    player_phase: PhaseColorState = field(default_factory=PhaseColorState)
    enemy_phase: PhaseColorState = field(default_factory=PhaseColorState)
    player_low_hp: LowHpState = field(default_factory=LowHpState)
    enemy_low_hp: LowHpState = field(default_factory=LowHpState)
    player_damage_flash: BarFlash = field(default_factory=BarFlash)
    player_heal_flash: BarFlash = field(default_factory=BarFlash)
    enemy_damage_flash: BarFlash = field(default_factory=BarFlash)
    enemy_heal_flash: BarFlash = field(default_factory=BarFlash)
    vignette: CameraVignette = field(default_factory=CameraVignette)

    def step(self, dt_ms: int) -> None:
        """Step all HUD effects."""
        # Drain animations
        for hs in (self.player_health, self.enemy_health):
            if hs.drain_ms > 0 and hs.displayed_hp != hs.current_hp:
                diff = hs.current_hp - hs.displayed_hp
                step_amount = abs(diff) * dt_ms / hs.drain_ms
                if diff > 0:
                    hs.displayed_hp = min(hs.current_hp, hs.displayed_hp + step_amount)
                else:
                    hs.displayed_hp = max(hs.current_hp, hs.displayed_hp - step_amount)
                if abs(hs.displayed_hp - hs.current_hp) < 0.5:
                    hs.displayed_hp = hs.current_hp
                    hs.drain_ms = 0
            if hs.drain_ms > 0 and hs.displayed_shield != hs.current_shield:
                diff = hs.current_shield - hs.displayed_shield
                step_amount = abs(diff) * dt_ms / hs.drain_ms
                if diff > 0:
                    hs.displayed_shield = min(hs.current_shield, hs.displayed_shield + step_amount)
                else:
                    hs.displayed_shield = max(hs.current_shield, hs.displayed_shield - step_amount)
                if abs(hs.displayed_shield - hs.current_shield) < 0.5:
                    hs.displayed_shield = hs.current_shield
                    hs.drain_ms = 0

        # Phase transitions
        self.player_phase.step(dt_ms)
        self.enemy_phase.step(dt_ms)

        # Low HP
        for hs, lh in (
            (self.player_health, self.player_low_hp),
            (self.enemy_health, self.enemy_low_hp),
        ):
            if hs.max_hp > 0:
                hp_pct = int(hs.current_hp * 100 / hs.max_hp)
                update_low_hp_state(lh, hp_pct, dt_ms)
            # Apply low-HP vignette (player only — enemy doesn't cause panic)
            if hs is self.player_health:
                self.vignette.intensity = lh.vignette_intensity

        # Flashes
        for f in (
            self.player_damage_flash,
            self.player_heal_flash,
            self.enemy_damage_flash,
            self.enemy_heal_flash,
        ):
            f.step(dt_ms)

        # Camera vignette
        self.vignette.step(dt_ms)

    def take_damage(self, who: str, amount: int) -> None:
        """Apply damage to a combatant. `who` is 'player' or 'enemy'."""
        if who == "player":
            self.player_health.current_hp = max(0, self.player_health.current_hp - amount)
            self.player_health.drain_ms = 200
            self.player_damage_flash.trigger(color=DAMAGE_FLASH_COLOR, duration_ms=200)
        else:
            self.enemy_health.current_hp = max(0, self.enemy_health.current_hp - amount)
            self.enemy_health.drain_ms = 200
            self.enemy_damage_flash.trigger(color=DAMAGE_FLASH_COLOR, duration_ms=200)

    def heal(self, who: str, amount: int) -> None:
        """Apply heal to a combatant."""
        if who == "player":
            self.player_health.current_hp = min(
                self.player_health.max_hp,
                self.player_health.current_hp + amount,
            )
            self.player_health.drain_ms = 200
            self.player_heal_flash.trigger(color=HEAL_COLOR, duration_ms=200)
        else:
            self.enemy_health.current_hp = min(
                self.enemy_health.max_hp,
                self.enemy_health.current_hp + amount,
            )
            self.enemy_health.drain_ms = 200
            self.enemy_heal_flash.trigger(color=HEAL_COLOR, duration_ms=200)

    def set_boss_phase(
        self, who: str, phase_index: int, color: tuple[int, int, int] | None = None
    ) -> None:
        """Set the boss phase color (recolors HP bar)."""
        if who == "player":
            self.player_phase.set_phase(phase_index, color)
        else:
            self.enemy_phase.set_phase(phase_index, color)
        self.vignette.flash(intensity=0.4, duration_ms=300)


__all__ = [
    "AlertLevel",
    "BarFlash",
    "HP_HIGH_COLOR",
    "HP_MID_COLOR",
    "HP_LOW_COLOR",
    "HP_CRIT_COLOR",
    "SHIELD_COLOR",
    "PHASE_COLORS",
    "VIGNETTE_COLOR",
    "CameraVignette",
    "CombatHUD",
    "HealthState",
    "LowHpState",
    "PhaseColorState",
    "is_pulsing",
    "render_health_bar",
    "render_health_bar_rich",
    "render_vignette",
    "update_low_hp_state",
]
