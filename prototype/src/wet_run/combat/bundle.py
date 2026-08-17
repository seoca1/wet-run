"""Unified combat effects bundle.

Combines all combat VFX systems into a single container for easy
state management and integration with combat_view.py.

Components:
  - CombatEffects: animations, particles, screen shake, floating numbers,
    hit flash, cinematic, slow-motion
  - CombatHUD: 2-tier HP bars, low-HP warnings, boss phase colors,
    camera vignette, damage/heal flashes
  - CombatCombo: 5-stage combo counter, timing bar, finishers
  - CombatVisual: combo display state (counter text, stage-up, end)

This bundle provides:
  - Single point of creation (all defaults)
  - Single step() to advance all systems
  - Single clear() to reset
  - Centralized state for save/load

Layered system architecture:
  - Layer 1: Hit feedback (animations, particles, numbers, flash, shake)
  - Layer 2: Skill animations (15 unique effects)
  - Layer 3: ICE-type cinematics
  - Layer 4: Status icons
  - Layer 5: Cinematic intros/deaths/critical hits
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .combo import CombatCombo, ComboVisual
from .effects import CombatEffects
from .hud import CombatHUD, HealthState

if TYPE_CHECKING:
    pass


@dataclass(slots=True)
class CombatEffectsBundle:
    """All-in-one combat VFX state container.

    One instance per AppState.combat_effects. combat_view steps this
    each frame, then renders each subsystem's overlay.
    """

    effects: CombatEffects = field(default_factory=CombatEffects)
    hud: CombatHUD = field(default_factory=CombatHUD)
    combo: CombatCombo = field(default_factory=CombatCombo)
    combo_visual: ComboVisual = field(default_factory=ComboVisual)

    def step(self, dt_ms: int) -> None:
        """Step all subsystems forward by dt_ms milliseconds."""
        self.effects.step(dt_ms)
        self.hud.step(dt_ms)
        self.combo.step(dt_ms)
        # Note: ComboVisual updates are event-driven (on hit, on stage-up)
        # so we don't step it here.

    def clear(self) -> None:
        """Reset all subsystems to a clean state.

        Called on combat end, scene transition, or fresh game.
        Preserves combo max stats.
        """
        self.effects.clear()
        # HUD player/enemy HP are owned elsewhere; just reset flash state
        self.combo.reset()
        # ComboVisual cleared on next update
        self.combo_visual = ComboVisual()

    def has_active_effects(self) -> bool:
        """True if any subsystem is currently animating/rendering."""
        if self.effects.has_active_effects():
            return True
        # HUD always has a vignette state if vignette_intensity > 0
        if self.hud.vignette.flash_intensity > 0:
            return True
        # Combo has end cinematic
        if self.combo_visual.end_ms > 0:
            return True
        return False

    def setup_combat(
        self,
        player_max_hp: int,
        player_max_shield: int = 0,
        enemy_max_hp: int = 100,
        enemy_max_shield: int = 0,
        window_ms: int = 3500,
    ) -> None:
        """Initialize for a new combat encounter.

        Sets up HUD HP values, combo window, clears all effects.
        """
        # HUD setup
        self.hud.player_health = HealthState(
            current_hp=player_max_hp,
            max_hp=player_max_hp,
            current_shield=player_max_shield,
            max_shield=player_max_shield,
            displayed_hp=float(player_max_hp),
            displayed_shield=float(player_max_shield),
        )
        self.hud.enemy_health = HealthState(
            current_hp=enemy_max_hp,
            max_hp=enemy_max_hp,
            current_shield=enemy_max_shield,
            max_shield=enemy_max_shield,
            displayed_hp=float(enemy_max_hp),
            displayed_shield=float(enemy_max_shield),
        )
        # Combo setup
        self.combo.window_ms = window_ms
        # Clear VFX
        self.clear()


# Convenience aliases
def create_bundle() -> CombatEffectsBundle:
    """Create a fresh bundle with all defaults."""
    return CombatEffectsBundle()


__all__ = [
    "CombatEffectsBundle",
    "create_bundle",
]
