"""Combat visual effects — data types only (ADR-0144 module split).

Extracted from combat/effects.py to:
1. Break circular import between combat/effects.py and combat/effects_vfx.py
   (effects_vfx.py previously imported data classes from effects.py, and
   effects.py re-exported behavior from effects_vfx.py).
2. Group pure data types (dataclasses + StrEnums) in their own module —
   no behavior, just types and lifecycle (step/is_finished/alpha).

Module structure (post ADR-0144):
    - combat/effects_data (this file): IceType, StatusIcon, 10 dataclasses
    - combat/effects: thin re-export facade (data + behavior from effects_vfx)
    - combat/effects_vfx: animation sequences + CombatEffects + spawn functions
    - combat/palette: color constants

Backward compat: combat/effects.py re-exports everything, so existing
imports of ``from wet_run.combat.effects import X`` continue to
work via the facade.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import StrEnum

from .palette import (
    DAMAGE_COLOR,
    DEFAULT_COLOR,
    HEAL_COLOR,
    HIT_FLASH_COLOR,
)


class IceType(StrEnum):
    """ICE enemy types with unique visual effects."""

    STANDARD = "standard"
    WATCHDOG = "watchdog"
    GOLIATH = "goliath"
    BLACK = "black"
    CONSTRUCT = "construct"
    # Boss types (ADR-0050) — multi-phase
    WINTERMUTE = "wintermute"
    TA_CONSTRUCT_PRIME = "ta_construct_prime"


class StatusIcon(StrEnum):
    """Status effect icons shown next to combatants."""

    POISON = "P"
    BURN = "B"
    STUN = "S"
    SHIELD = "❖"
    BUFF = "↑"
    DEBUFF = "↓"
    REGEN = "+"
    DOT = "•"


# ----------------------------------------------------------------------------
# Animation primitives
# ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AnimationFrame:
    """A single frame in an animation.

    Attributes:
        text: The ASCII art or symbol for this frame.
        color: RGB tuple for tcod rendering.
        duration_ms: How long this frame shows.
        offset: (dx, dy) position offset from the spawn point.
    """

    text: str
    color: tuple[int, int, int] = DEFAULT_COLOR
    duration_ms: int = 80
    offset: tuple[int, int] = (0, 0)


@dataclass(slots=True)
class Animation:
    """A multi-frame animation that plays once and completes.

    Use `step()` to advance; use `current_frame` to render; use
    `is_finished` to know when to remove.
    """

    frames: tuple[AnimationFrame, ...]
    elapsed_ms: int = 0
    _current_index: int = 0

    def step(self, dt_ms: int) -> None:
        """Advance animation by dt_ms milliseconds."""
        if self.is_finished:
            return
        self.elapsed_ms += dt_ms
        # Advance frames until we find one that covers elapsed_ms
        cumulative = 0
        for i, frame in enumerate(self.frames):
            cumulative += frame.duration_ms
            if self.elapsed_ms < cumulative:
                self._current_index = i
                return
        # Past the end
        self._current_index = len(self.frames) - 1

    @property
    def current_frame(self) -> AnimationFrame | None:
        """The frame to render this tick, or None if finished."""
        if self.is_finished:
            return None
        return self.frames[self._current_index]

    @property
    def is_finished(self) -> bool:
        """True when all frames have been displayed."""
        return self.elapsed_ms >= self.total_duration_ms

    @property
    def total_duration_ms(self) -> int:
        """Total animation duration."""
        return sum(f.duration_ms for f in self.frames)

    def progress(self) -> float:
        """0.0 to 1.0 progress through the animation."""
        total = self.total_duration_ms
        if total == 0:
            return 1.0
        return min(1.0, self.elapsed_ms / total)


# ----------------------------------------------------------------------------
# Particle system
# ----------------------------------------------------------------------------


@dataclass(slots=True)
class Particle:
    """A single particle in the particle system.

    Particles fly outward from a spawn point, fall/rise, and fade.
    Used for hit sparks, blood splatter, healing sparkles, etc.
    """

    x: float
    y: float
    vx: float  # velocity x (units per second)
    vy: float  # velocity y
    char: str
    color: tuple[int, int, int]
    life_ms: int = 0
    max_life_ms: int = 400
    gravity: float = 0.0  # y-acceleration per second

    def step(self, dt_ms: int) -> None:
        """Advance particle by dt_ms."""
        dt_s = dt_ms / 1000.0
        self.x += self.vx * dt_s
        self.y += self.vy * dt_s
        self.vy += self.gravity * dt_s
        self.life_ms += dt_ms

    @property
    def is_alive(self) -> bool:
        """True while particle has remaining life_ms."""
        return self.life_ms < self.max_life_ms

    @property
    def alpha(self) -> float:
        """0.0 to 1.0 fade-out multiplier."""
        if self.max_life_ms == 0:
            return 0.0
        return max(0.0, 1.0 - self.life_ms / self.max_life_ms)


@dataclass(slots=True)
class ParticleSystem:
    """Container for all active particles."""

    particles: list[Particle] = field(default_factory=list)

    def spawn(self, particle: Particle) -> None:
        """Append a single particle to the active list."""
        self.particles.append(particle)

    def spawn_burst(
        self,
        x: float,
        y: float,
        chars: tuple[str, ...] = ("*", "+", "x", "·"),
        color: tuple[int, int, int] = DAMAGE_COLOR,
        count: int = 6,
        speed: float = 30.0,
        life_ms: int = 400,
        spread: float = math.tau,
    ) -> None:
        """Spawn `count` particles in a burst pattern."""
        for _ in range(count):
            angle = random.uniform(0, spread)
            v = speed * random.uniform(0.6, 1.0)
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=math.cos(angle) * v,
                    vy=math.sin(angle) * v - v * 0.3,  # bias upward
                    char=random.choice(chars),
                    color=color,
                    max_life_ms=life_ms,
                    gravity=80.0,
                )
            )

    def spawn_upward(
        self,
        x: float,
        y: float,
        chars: tuple[str, ...] = ("+", "✚", "✿"),
        color: tuple[int, int, int] = HEAL_COLOR,
        count: int = 4,
        life_ms: int = 600,
    ) -> None:
        """Spawn particles rising upward (for healing/buffs)."""
        for _ in range(count):
            self.particles.append(
                Particle(
                    x=x + random.uniform(-0.5, 0.5),
                    y=y,
                    vx=random.uniform(-8.0, 8.0),
                    vy=-random.uniform(15.0, 30.0),
                    char=random.choice(chars),
                    color=color,
                    max_life_ms=life_ms,
                    gravity=-10.0,
                )
            )

    def step(self, dt_ms: int) -> None:
        """Advance every particle by dt_ms and drop expired ones."""
        for p in self.particles:
            p.step(dt_ms)
        self.particles = [p for p in self.particles if p.is_alive]

    def clear(self) -> None:
        """Remove all particles immediately."""
        self.particles.clear()


# ----------------------------------------------------------------------------
# Screen shake
# ----------------------------------------------------------------------------


@dataclass(slots=True)
class ScreenShake:
    """Camera shake state.

    On each step, returns (dx, dy) integer offset to apply to the
    whole render. Intensity decays over time.
    """

    intensity: float = 0.0
    duration_ms: int = 0
    elapsed_ms: int = 0

    def trigger(self, intensity: float, duration_ms: int) -> None:
        """Start a new shake; replaces any existing shake."""
        self.intensity = max(self.intensity, intensity)
        self.duration_ms = max(self.duration_ms, duration_ms)
        self.elapsed_ms = 0

    def step(self, dt_ms: int) -> None:
        """Advance the shake timeline by ``dt_ms`` milliseconds.

        No-op when intensity is already zero (inactive shake). When the
        elapsed time meets or exceeds ``duration_ms`` the shake is reset
        (intensity=0, duration_ms=0, elapsed_ms=0) so subsequent
        ``start()`` calls begin from a clean slate.
        """
        if self.intensity <= 0:
            return
        self.elapsed_ms += dt_ms
        if self.elapsed_ms >= self.duration_ms:
            self.intensity = 0.0
            self.duration_ms = 0
            self.elapsed_ms = 0

    def offset(self) -> tuple[int, int]:
        """Current shake offset (dx, dy). Returns (0, 0) if no shake."""
        if self.intensity <= 0 or self.duration_ms <= 0:
            return (0, 0)
        # Decay factor: 1.0 at start, 0.0 at end
        decay = 1.0 - (self.elapsed_ms / self.duration_ms)
        magnitude = self.intensity * decay
        # Random jitter
        dx = int(random.uniform(-magnitude, magnitude))
        dy = int(random.uniform(-magnitude, magnitude))
        return (dx, dy)


# ----------------------------------------------------------------------------
# Floating damage numbers
# ----------------------------------------------------------------------------


@dataclass(slots=True)
class FloatingNumber:
    """A floating damage/heal number that rises and fades."""

    x: float
    y: float
    value: int
    color: tuple[int, int, int]
    life_ms: int = 0
    max_life_ms: int = 800
    is_crit: bool = False

    def step(self, dt_ms: int) -> None:
        """Advance the number's life and float it upward."""
        self.life_ms += dt_ms
        # Float upward over time
        self.y -= 0.03 * dt_ms

    @property
    def is_alive(self) -> bool:
        """True while the number has remaining life_ms."""
        return self.life_ms < self.max_life_ms

    @property
    def text(self) -> str:
        """Render the damage number, bracketed with ``!`` for crits.

        Critical hits display as ``!42!`` (symmetric emphasis) while
        normal hits display as ``42``. The bracketing is a Gibson-flavored
        visual cue that matches the screen-flash and shake intensities
        raised on crit.
        """
        prefix = "!" if self.is_crit else ""
        return f"{prefix}{self.value}{prefix}"

    @property
    def alpha(self) -> float:
        """Fade-out factor in ``[0.0, 1.0]`` as the number nears max life.

        Returns 0.0 when ``max_life_ms == 0`` (degenerate lifetime,
        no fade). Otherwise ``max(0.0, 1.0 - life_ms / max_life_ms)`` —
        full opacity at spawn, zero at expiry.
        """
        if self.max_life_ms == 0:
            return 0.0
        return max(0.0, 1.0 - self.life_ms / self.max_life_ms)


# ----------------------------------------------------------------------------
# Hit flash
# ----------------------------------------------------------------------------


@dataclass(slots=True)
class HitFlash:
    """Brief flash on a target tile after a hit."""

    duration_ms: int = 0
    elapsed_ms: int = 0
    color: tuple[int, int, int] = HIT_FLASH_COLOR

    def trigger(
        self, color: tuple[int, int, int] = HIT_FLASH_COLOR, duration_ms: int = 120
    ) -> None:
        """Start a new tile-level flash; replaces any existing flash."""
        self.color = color
        self.duration_ms = duration_ms
        self.elapsed_ms = 0

    def step(self, dt_ms: int) -> None:
        """Advance elapsed_ms while the flash is active."""
        if self.duration_ms > 0:
            self.elapsed_ms += dt_ms

    @property
    def is_active(self) -> bool:
        """True while the flash has remaining time."""
        return self.elapsed_ms < self.duration_ms

    @property
    def alpha(self) -> float:
        """Fade-out factor in ``[0.0, 1.0]`` as the flash decays.

        Returns 0.0 when ``duration_ms == 0`` (degenerate lifetime). The
        flash fades linearly from full opacity at spawn to zero at
        expiry, in lockstep with the underlying animation timer.
        """
        if self.duration_ms == 0:
            return 0.0
        return max(0.0, 1.0 - self.elapsed_ms / self.duration_ms)


@dataclass(slots=True)
class ScreenFlash:
    """Full-screen flash effect for AoE damage / boss phase transitions (ADR-0125 follow-up).

    Unlike HitFlash (tile-level), ScreenFlash covers the entire viewport.
    Used by boss phase AoE bursts and dramatic combat moments.

    Alpha fades from 1.0 (peak) to 0.0 over duration_ms.
    """

    duration_ms: int = 0
    elapsed_ms: int = 0
    color: tuple[int, int, int] = HIT_FLASH_COLOR

    def trigger(
        self, color: tuple[int, int, int] = HIT_FLASH_COLOR, duration_ms: int = 250
    ) -> None:
        """Start a new full-screen flash; replaces any existing flash."""
        self.color = color
        self.duration_ms = duration_ms
        self.elapsed_ms = 0

    def step(self, dt_ms: int) -> None:
        """Advance elapsed_ms while the screen flash is active."""
        if self.duration_ms > 0:
            self.elapsed_ms += dt_ms

    @property
    def is_active(self) -> bool:
        """True while the screen flash has remaining time."""
        return self.elapsed_ms < self.duration_ms

    @property
    def alpha(self) -> float:
        """Current alpha (1.0 = full flash, 0.0 = faded out).

        Uses a sharp attack + ease-out curve: fast spike (first 15%)
        then linear fade. Avoids the harsh look of pure linear decay.
        """
        if self.duration_ms == 0:
            return 0.0
        progress = self.elapsed_ms / self.duration_ms
        if progress < 0.15:
            return 1.0
        fade = (progress - 0.15) / 0.85
        return max(0.0, 1.0 - fade * fade)


# ----------------------------------------------------------------------------
# Cinematic intro / death sequences
# ----------------------------------------------------------------------------


@dataclass(slots=True)
class CinematicSequence:
    """A scripted multi-phase cinematic (intro, death, critical).

    Each phase is a (text, color, duration_ms) tuple. The sequence
    advances through phases automatically.
    """

    name: str
    phases: tuple[tuple[str, tuple[int, int, int], int], ...]
    elapsed_ms: int = 0
    _phase_index: int = 0

    def step(self, dt_ms: int) -> None:
        """Advance elapsed_ms; no-op once finished."""
        if self.is_finished:
            return
        self.elapsed_ms += dt_ms

    @property
    def current_phase(self) -> tuple[str, tuple[int, int, int], int] | None:
        """Return the active (text, color, duration_ms) phase, or None when finished."""
        if self.is_finished:
            return None
        cumulative = 0
        for phase in self.phases:
            cumulative += phase[2]
            if self.elapsed_ms < cumulative:
                return phase
        return None

    @property
    def is_finished(self) -> bool:
        """True when elapsed_ms has covered all phase durations."""
        return self.elapsed_ms >= self.total_duration_ms

    @property
    def total_duration_ms(self) -> int:
        """Sum of all phase durations."""
        return sum(p[2] for p in self.phases)


# ----------------------------------------------------------------------------
# Combo counter
# ----------------------------------------------------------------------------


@dataclass(slots=True)
class ComboCounter:
    """Tracks consecutive hits within a short window.

    Combo decays after a short pause (combo_window_ms).
    """

    count: int = 0
    last_hit_ms: int = 0
    combo_window_ms: int = 2500

    def register_hit(self, current_ms: int) -> int:
        """Register a hit; returns new combo count."""
        if current_ms - self.last_hit_ms > self.combo_window_ms:
            self.count = 1
        else:
            self.count += 1
        self.last_hit_ms = current_ms
        return self.count

    def reset(self) -> None:
        """Clear combo count and last-hit timestamp."""
        self.count = 0
        self.last_hit_ms = 0

    @property
    def label(self) -> str:
        """Display label, e.g. '3x HIT!'."""
        if self.count < 2:
            return ""
        if self.count >= 5:
            return f"{self.count}x RAMPAGE!"
        return f"{self.count}x HIT!"


__all__ = [
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
]
