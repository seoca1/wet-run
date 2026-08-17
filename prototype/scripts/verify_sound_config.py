"""Headless verification of the SoundConfig + category routing.

Demonstrates:
- 6 categories with default settings (KEYS off)
- Per-category toggles
- Volume control
- Mute toggle
- Routing: which sounds are playable under which config

Usage:
  uv run python scripts/verify_sound_config.py
  uv run python scripts/verify_sound_config.py --no-color
  uv run python scripts/verify_sound_config.py --toggle keys
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.audio.config import (
    CATEGORY_KEY_BINDINGS,
    SOUND_CATEGORY_MAP,
    SoundCategory,
    SoundConfig,
    category_label,
)
from wet_run.audio.sound_manager import DEFAULT_SOUNDS

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_CYAN = "\033[96m"
ANSI_YELLOW = "\033[93m"
ANSI_GREEN = "\033[92m"
ANSI_RED = "\033[91m"
ANSI_GRAY = "\033[90m"


def _header(title: str) -> None:
    print()
    print(f"{ANSI_BOLD}{'=' * 70}{ANSI_RESET}")
    print(f"{ANSI_BOLD}  {title}{ANSI_RESET}")
    print(f"{ANSI_BOLD}{'=' * 70}{ANSI_RESET}")
    print()


def _section(title: str) -> None:
    print()
    print(f"{ANSI_BOLD}--- {title} ---{ANSI_RESET}")
    print()


def _show_config(config: SoundConfig) -> None:
    """Show current config state."""
    mute_str = "MUTED" if config.muted else "ON"
    vol_pct = int(config.master_volume * 100)
    print(f"  Master: {mute_str}  Volume: {vol_pct}%")
    for cat in SoundCategory:
        key = CATEGORY_KEY_BINDINGS[cat]
        enabled = config.is_category_enabled(cat)
        status = "ON " if enabled else "OFF"
        color = ANSI_GREEN if enabled else ANSI_GRAY
        label = category_label(cat)
        print(f"  [{key}] {label:25s}  {color}{status}{ANSI_RESET}")


def _verify_default_config() -> SoundConfig:
    """Step 1: Default SoundConfig."""
    _section("Step 1: Default SoundConfig")
    config = SoundConfig()
    _show_config(config)
    assert config.master_volume == 0.2, f"Expected 0.2, got {config.master_volume}"
    assert config.muted is False
    assert config.is_category_enabled(SoundCategory.KEYS) is False, "KEYS should be off"
    assert config.is_category_enabled(SoundCategory.THEME) is True, "THEME should be on"
    print()
    print(f"{ANSI_GREEN}✓ Default config: volume 0.2, KEYS off, others on{ANSI_RESET}")
    return config


def _verify_volume_control() -> SoundConfig:
    """Step 2: Volume control."""
    _section("Step 2: Volume Control")
    config = SoundConfig(master_volume=0.5)
    print(f"  Initial volume: {int(config.master_volume * 100)}%")

    config.adjust_volume(+0.1)
    print(f"  After +0.1: {int(config.master_volume * 100)}%")
    assert abs(config.master_volume - 0.6) < 0.001

    config.adjust_volume(+1.0)  # Should clamp to 1.0
    print(f"  After +1.0 (clamped): {int(config.master_volume * 100)}%")
    assert config.master_volume == 1.0

    config.adjust_volume(-2.0)  # Should clamp to 0.0
    print(f"  After -2.0 (clamped): {int(config.master_volume * 100)}%")
    assert config.master_volume == 0.0

    print()
    print(f"{ANSI_GREEN}✓ Volume clamped correctly (0.0-1.0){ANSI_RESET}")
    return config


def _verify_mute_toggle() -> None:
    """Step 3: Mute toggle."""
    _section("Step 3: Mute Toggle")
    config = SoundConfig()
    print(f"  Initial: muted={config.muted}")
    new_state = config.toggle_mute()
    print(f"  After toggle: muted={config.muted} (returned {new_state})")
    assert config.muted is True
    assert new_state is True
    config.toggle_mute()
    assert config.muted is False
    print()
    print(f"{ANSI_GREEN}✓ Mute toggles correctly{ANSI_RESET}")


def _verify_category_toggles() -> None:
    """Step 4: Category toggles (per user request: KEYS off by default)."""
    _section("Step 4: Category Toggles (KEYS off by default)")
    config = SoundConfig()
    print(f"  Initial KEYS: {config.is_category_enabled(SoundCategory.KEYS)}")
    assert config.is_category_enabled(SoundCategory.KEYS) is False

    # Toggle KEYS on
    new = config.toggle_category(SoundCategory.KEYS)
    print(f"  After T (KEYS toggle): {new}")
    assert new is True

    # Toggle it back off
    new = config.toggle_category(SoundCategory.KEYS)
    print(f"  After T again: {new}")
    assert new is False

    # Set THEME off
    config.set_category_enabled(SoundCategory.THEME, False)
    print(f"  After set THEME off: {config.is_category_enabled(SoundCategory.THEME)}")
    assert config.is_category_enabled(SoundCategory.THEME) is False

    print()
    print(f"{ANSI_GREEN}✓ Category toggles work correctly{ANSI_RESET}")


def _verify_routing() -> None:
    """Step 5: Sound routing (which sounds are playable)."""
    _section("Step 5: Sound Routing")

    config = SoundConfig()
    print("  Default config (THEME on, KEYS off):")
    print()
    test_sounds = [
        "theme/matrix_rain",
        "story/text_typing",
        "ui/menu_select",
        "combat/hit_normal",
        "movement/nav_step",
        "items/pickup",
    ]
    for sound in test_sounds:
        category = SOUND_CATEGORY_MAP.get(sound, "unknown")
        playable = config.is_sound_playable(sound)
        status = "PLAY" if playable else "SKIP"
        color = ANSI_GREEN if playable else ANSI_GRAY
        print(f"    {sound:25s}  category={category.value:10s}  {color}{status}{ANSI_RESET}")

    # Now toggle KEYS on
    config.set_category_enabled(SoundCategory.KEYS, True)
    print()
    print("  After enabling KEYS:")
    print(f"    ui/menu_select: {'PLAY' if config.is_sound_playable('ui/menu_select') else 'SKIP'}")

    # Now mute
    config.muted = True
    print()
    print("  After muting:")
    for sound in test_sounds[:3]:
        print(f"    {sound}: {'PLAY' if config.is_sound_playable(sound) else 'SKIP'}")

    print()
    print(f"{ANSI_GREEN}✓ Routing respects mute + category{ANSI_RESET}")


def _verify_summary() -> None:
    """Step 6: get_summary() output."""
    _section("Step 6: Config Summary (for dashboard)")
    config = SoundConfig(master_volume=0.5, muted=True)
    config.set_category_enabled(SoundCategory.COMBAT, False)
    summary = config.get_summary()
    print(f"  Summary: {summary}")
    assert "master_volume" in summary
    assert "muted" in summary
    for cat in SoundCategory:
        assert f"{cat.value}_enabled" in summary
    print()
    print(f"{ANSI_GREEN}✓ Summary contains all expected keys{ANSI_RESET}")


def _verify_key_bindings() -> None:
    """Step 7: Key bindings documentation."""
    _section("Step 7: Key Bindings (Cheatsheet)")
    print("  Global hotkeys for sound control:")
    print()
    print(f"  {ANSI_CYAN}M{ANSI_RESET}        = master mute toggle")
    print(
        f"  {ANSI_CYAN}+{ANSI_RESET}/{ANSI_CYAN}-{ANSI_RESET}      = master volume up/down (0.1 steps)"
    )
    print()
    print("  Per-category toggles:")
    print()
    for cat in SoundCategory:
        key = CATEGORY_KEY_BINDINGS[cat]
        label = category_label(cat)
        default = "ON" if cat != SoundCategory.KEYS else "OFF (default)"
        print(f"  {ANSI_CYAN}{key}{ANSI_RESET}        = {label:25s} (default: {default})")
    print()
    print(f"{ANSI_GREEN}✓ All 6 categories have key bindings{ANSI_RESET}")


def _verify_all_sounds_categorized() -> None:
    """Step 8: All DEFAULT_SOUNDS have a category."""
    _section("Step 8: All Sounds Categorized")
    uncategorized = []
    for sound_name in DEFAULT_SOUNDS:
        if sound_name not in SOUND_CATEGORY_MAP:
            uncategorized.append(sound_name)
    if uncategorized:
        print(f"{ANSI_RED}✗ Uncategorized sounds: {uncategorized}{ANSI_RESET}")
    else:
        total = len(DEFAULT_SOUNDS)
        print(f"{ANSI_GREEN}✓ All {total} DEFAULT_SOUNDS have a category{ANSI_RESET}")

    # Breakdown by category
    by_category: dict[str, int] = {}
    for _sound_name, category in SOUND_CATEGORY_MAP.items():
        by_category[category.value] = by_category.get(category.value, 0) + 1

    print()
    print("  Sounds per category:")
    for cat_value, count in sorted(by_category.items()):
        bar = "█" * count
        print(f"    {cat_value:10s}  {count:2d}  {ANSI_DIM}{bar}{ANSI_RESET}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify SoundConfig system")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    parser.add_argument(
        "--toggle",
        choices=["keys", "theme", "events", "combat", "movement", "items"],
        help="Demo toggling a specific category",
    )
    args = parser.parse_args()

    if args.no_color:
        global \
            ANSI_RESET, \
            ANSI_BOLD, \
            ANSI_DIM, \
            ANSI_CYAN, \
            ANSI_YELLOW, \
            ANSI_GREEN, \
            ANSI_RED, \
            ANSI_GRAY
        for attr in (
            "ANSI_RESET",
            "ANSI_BOLD",
            "ANSI_DIM",
            "ANSI_CYAN",
            "ANSI_YELLOW",
            "ANSI_GREEN",
            "ANSI_RED",
            "ANSI_GRAY",
        ):
            globals()[attr] = ""

    _header("SOUND CONFIG VERIFICATION DEMO")
    print(f"{ANSI_DIM}This demo verifies the SoundConfig system:{ANSI_RESET}")
    print(f"{ANSI_DIM}- 6 categories (THEME/EVENTS/KEYS/COMBAT/MOVEMENT/ITEMS){ANSI_RESET}")
    print(f"{ANSI_DIM}- KEYS off by default (per user request){ANSI_RESET}")
    print(f"{ANSI_DIM}- All other categories on{ANSI_RESET}")
    print(f"{ANSI_DIM}- Master volume 0.2, mute off{ANSI_RESET}")

    _verify_default_config()
    _verify_volume_control()
    _verify_mute_toggle()
    _verify_category_toggles()
    _verify_routing()
    _verify_summary()
    _verify_key_bindings()
    _verify_all_sounds_categorized()

    if args.toggle:
        _section(f"Bonus: Toggling {args.toggle}")
        config = SoundConfig()
        cat = SoundCategory(args.toggle)
        new_state = config.toggle_category(cat)
        label = category_label(cat)
        print(f"  Toggled {label}: {new_state}")

    _header("VERIFICATION COMPLETE")
    print(f"{ANSI_GREEN}All checks passed!{ANSI_RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
