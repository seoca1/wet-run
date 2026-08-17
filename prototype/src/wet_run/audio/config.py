"""Sound configuration system (Phase 4).

Categorizes sounds into 6 buckets, each with its own on/off toggle.
Persists master volume, mute state, and per-category toggles.

Categories:
    - theme:    Background music / ambient (loop, low volume)
    - events:   Story / event triggers (typing, dialogue_advance, victory, defeat)
    - keys:     UI key sounds (menu_select, menu_confirm, error) — **default OFF**
    - combat:   Combat effects (hit, skill, block, stun)
    - movement: Movement (nav_step, nav_block, jack_in, jack_out)
    - items:    Inventory/equipment (equip, pickup, cant)

Key bindings (global):
    M = master mute toggle
    T = theme on/off
    E = events on/off
    K = keys on/off
    B = combat on/off
    V = movement on/off
    I = items on/off
    +/- = master volume
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SoundCategory(StrEnum):
    """Sound categories with default-enabled state."""

    THEME = "theme"  # Background music / ambient
    EVENTS = "events"  # Story / event triggers
    KEYS = "keys"  # UI key sounds (default OFF)
    COMBAT = "combat"  # Combat effects
    MOVEMENT = "movement"  # Movement sounds
    ITEMS = "items"  # Inventory/equipment


# Default: KEYS off (per user request), others on
DEFAULT_CATEGORY_ENABLED: dict[SoundCategory, bool] = {
    SoundCategory.THEME: True,
    SoundCategory.EVENTS: True,
    SoundCategory.KEYS: False,
    SoundCategory.COMBAT: True,
    SoundCategory.MOVEMENT: True,
    SoundCategory.ITEMS: True,
}


# All known sound names mapped to their category
SOUND_CATEGORY_MAP: dict[str, SoundCategory] = {
    # Theme (background, ambient) — low volume loop (ADR-0032)
    "theme/matrix_rain": SoundCategory.THEME,
    "theme/cyberspace": SoundCategory.THEME,
    "theme/chiba": SoundCategory.THEME,
    "theme/sense_net": SoundCategory.THEME,
    "theme/finn_office": SoundCategory.THEME,
    "theme/loa_drum": SoundCategory.THEME,
    "theme/loa_drum_fade": SoundCategory.THEME,
    "theme/loa_channel": SoundCategory.THEME,
    "theme/manarase_drone": SoundCategory.THEME,
    "theme/industrial": SoundCategory.THEME,
    "theme/broadcast": SoundCategory.THEME,
    "theme/hammer_alert": SoundCategory.THEME,
    # Events (story / cinematic)
    "story/text_typing": SoundCategory.EVENTS,
    "story/dialogue_advance": SoundCategory.EVENTS,
    "story/event_trigger": SoundCategory.EVENTS,
    "combat/victory": SoundCategory.EVENTS,
    "combat/defeat": SoundCategory.EVENTS,
    # Jack-in/out + cinematic SFX (ADR-0032)
    "movement/jack_in_zap": SoundCategory.MOVEMENT,
    "movement/jack_out_buzz": SoundCategory.MOVEMENT,
    "movement/data_extract": SoundCategory.MOVEMENT,
    "movement/black_ice_roar": SoundCategory.MOVEMENT,
    "movement/broadcast_static": SoundCategory.MOVEMENT,
    "movement/broadcast_out": SoundCategory.MOVEMENT,
    "movement/neon_hum": SoundCategory.MOVEMENT,
    # Keys (UI) — default OFF
    "ui/menu_select": SoundCategory.KEYS,
    "ui/menu_confirm": SoundCategory.KEYS,
    "ui/menu_cancel": SoundCategory.KEYS,
    "ui/error": SoundCategory.KEYS,
    "ui/notification": SoundCategory.KEYS,
    # Combat (effects)
    "combat/hit_normal": SoundCategory.COMBAT,
    "combat/hit_crit": SoundCategory.COMBAT,
    "combat/hit_miss": SoundCategory.COMBAT,
    "combat/skill_physical": SoundCategory.COMBAT,
    "combat/skill_magic": SoundCategory.COMBAT,
    "combat/skill_heal": SoundCategory.COMBAT,
    "combat/skill_buff": SoundCategory.COMBAT,
    "combat/skill_debuff": SoundCategory.COMBAT,
    "combat/block": SoundCategory.COMBAT,
    "combat/stun": SoundCategory.COMBAT,
    # Movement
    "movement/nav_step": SoundCategory.MOVEMENT,
    "movement/nav_block": SoundCategory.MOVEMENT,
    "movement/jack_in": SoundCategory.MOVEMENT,
    "movement/jack_out": SoundCategory.MOVEMENT,
    # Items
    "items/equip": SoundCategory.ITEMS,
    "items/pickup": SoundCategory.ITEMS,
    "items/cant": SoundCategory.ITEMS,
}


@dataclass
class SoundConfig:
    """User-configurable sound settings.

    All toggles can be changed at runtime. Persists as long as
    the AppState lives (could be saved to disk in the future).
    """

    master_volume: float = 0.2
    muted: bool = False
    # Per-category on/off
    category_enabled: dict[str, bool] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Initialize default per-category enabled flags if not provided."""
        if self.category_enabled is None:
            # Initialize with default category settings
            self.category_enabled = {
                cat.value: DEFAULT_CATEGORY_ENABLED[cat] for cat in SoundCategory
            }

    def is_category_enabled(self, category: SoundCategory | str) -> bool:
        """Check if a category is enabled.

        Args:
            category: SoundCategory enum or its string value.

        Returns:
            True if the category is enabled, False if disabled.
        """
        key = category.value if isinstance(category, SoundCategory) else category
        return self.category_enabled.get(key, True)

    def set_category_enabled(self, category: SoundCategory | str, enabled: bool) -> None:
        """Enable or disable a category."""
        key = category.value if isinstance(category, SoundCategory) else category
        self.category_enabled[key] = enabled

    def toggle_category(self, category: SoundCategory | str) -> bool:
        """Toggle a category on/off. Returns the new state."""
        key = category.value if isinstance(category, SoundCategory) else category
        new_state = not self.category_enabled.get(key, True)
        self.category_enabled[key] = new_state
        return new_state

    def toggle_mute(self) -> bool:
        """Toggle master mute. Returns the new state."""
        self.muted = not self.muted
        return self.muted

    def adjust_volume(self, delta: float) -> float:
        """Adjust master volume by delta. Returns new volume."""
        new_vol = max(0.0, min(1.0, self.master_volume + delta))
        self.master_volume = new_vol
        return new_vol

    def is_sound_playable(self, sound_name: str) -> bool:
        """Check if a sound can be played given current config.

        Returns False if:
        - Master muted
        - The sound's category is disabled
        - The sound name is unknown
        """
        if self.muted:
            return False
        category = SOUND_CATEGORY_MAP.get(sound_name)
        if category is None:
            return False  # Unknown sound
        return self.is_category_enabled(category)

    def get_category_for_sound(self, sound_name: str) -> SoundCategory | None:
        """Get the category for a given sound name."""
        return SOUND_CATEGORY_MAP.get(sound_name)

    def get_summary(self) -> dict[str, bool | float]:
        """Get a summary of all settings (for dashboard)."""
        return {
            "master_volume": self.master_volume,
            "muted": self.muted,
            **{f"{cat.value}_enabled": self.is_category_enabled(cat) for cat in SoundCategory},
        }


def category_label(category: SoundCategory) -> str:
    """Human-readable label for a category."""
    labels = {
        SoundCategory.THEME: "Theme (배경음악)",
        SoundCategory.EVENTS: "Events (이벤트)",
        SoundCategory.KEYS: "Keys (키보드)",
        SoundCategory.COMBAT: "Combat (전투)",
        SoundCategory.MOVEMENT: "Movement (이동)",
        SoundCategory.ITEMS: "Items (아이템)",
    }
    return labels.get(category, category.value.title())


# Key bindings (single source of truth)
CATEGORY_KEY_BINDINGS: dict[SoundCategory, str] = {
    SoundCategory.THEME: "T",
    SoundCategory.EVENTS: "E",
    SoundCategory.KEYS: "K",
    SoundCategory.COMBAT: "B",
    SoundCategory.MOVEMENT: "V",
    SoundCategory.ITEMS: "I",
}
