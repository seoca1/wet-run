"""Interactive demo of sound config + key bindings.

Demonstrates:
- M = master mute toggle
- +/- = volume ±0.1
- T/E/K/B/V/I = per-category toggle
- ENTER = exit

This demo is interactive — keys are read from stdin. Works in any
terminal (including headless via piped input).

Usage:
  uv run python scripts/demo_sound_keys.py
  uv run python scripts/demo_sound_keys.py --input "M+T-E"
  echo "T+E+Q" | uv run python scripts/demo_sound_keys.py
"""

from __future__ import annotations

import argparse
import sys
import termios
import tty
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.audio.config import (
    CATEGORY_KEY_BINDINGS,
    SoundCategory,
    SoundConfig,
    category_label,
)
from wet_run.audio.sound_manager import get_sound_config

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_CYAN = "\033[96m"
ANSI_YELLOW = "\033[93m"
ANSI_GREEN = "\033[92m"
ANSI_RED = "\033[91m"
ANSI_GRAY = "\033[90m"
ANSI_WHITE = "\033[97m"


def render_status(config: SoundConfig) -> str:
    """Render current sound config as ANSI-colored text."""
    lines = []
    lines.append(f"{ANSI_BOLD}  Sound Status{ANSI_RESET}")
    lines.append(f"  {'─' * 50}")
    mute_str = "MUTED" if config.muted else "ON"
    vol_pct = int(config.master_volume * 100)
    mute_color = ANSI_RED if config.muted else ANSI_GREEN
    lines.append(
        f"  [{ANSI_CYAN}M{ANSI_RESET}] Master: {mute_color}{mute_str}{ANSI_RESET}  Volume: {vol_pct}%"
    )
    lines.append("")
    lines.append(f"  {ANSI_DIM}Categories (T/E/K/B/V/I to toggle):{ANSI_RESET}")
    for cat in SoundCategory:
        key = CATEGORY_KEY_BINDINGS[cat]
        enabled = config.is_category_enabled(cat)
        status = "ON " if enabled else "OFF"
        color = ANSI_GREEN if enabled else ANSI_GRAY
        label = category_label(cat)
        lines.append(f"  [{ANSI_CYAN}{key}{ANSI_RESET}] {label:25s}  {color}{status}{ANSI_RESET}")
    return "\n".join(lines)


def toggle_master_mute(config: SoundConfig) -> None:
    """Toggle master mute."""
    new_state = config.toggle_mute()
    label = "MUTED" if new_state else "UNMUTED"
    print(f"\n{ANSI_BOLD}[M]{ANSI_RESET} Master toggled: {label}")


def adjust_volume(config: SoundConfig, delta: float) -> None:
    """Adjust master volume by delta."""
    new_vol = config.adjust_volume(delta)
    print(f"\n{ANSI_BOLD}[+/-]{ANSI_RESET} Volume: {int(new_vol * 100)}%")


def toggle_category(config: SoundConfig, category: SoundCategory) -> None:
    """Toggle a sound category."""
    new_state = config.toggle_category(category)
    label = "ON" if new_state else "OFF"
    label_text = category_label(category)
    key = CATEGORY_KEY_BINDINGS[category]
    print(f"\n{ANSI_BOLD}[{key}]{ANSI_RESET} {label_text} toggled: {label}")


def process_key(config: SoundConfig, key: str) -> bool:
    """Process a single key. Returns False if user wants to quit."""
    key = key.lower()
    if key in ("q", "esc", "escape", "\x1b"):
        return False
    if key == "m":
        toggle_master_mute(config)
    elif key in ("+", "=", "p"):  # +/=/p (plus)
        adjust_volume(config, +0.1)
    elif key == "-":
        adjust_volume(config, -0.1)
    elif key in ("t", "e", "k", "b", "v", "i"):
        # Category toggle
        for cat, k in CATEGORY_KEY_BINDINGS.items():
            if k.lower() == key:
                toggle_category(config, cat)
                break
    elif key == "?" or key == "h":
        print(
            f"\n{ANSI_BOLD}Help:{ANSI_RESET}\n"
            f"  {ANSI_CYAN}M{ANSI_RESET}   = master mute toggle\n"
            f"  {ANSI_CYAN}+/-{ANSI_RESET} = master volume ±0.1\n"
            f"  {ANSI_CYAN}T{ANSI_RESET}   = toggle theme\n"
            f"  {ANSI_CYAN}E{ANSI_RESET}   = toggle events\n"
            f"  {ANSI_CYAN}K{ANSI_RESET}   = toggle keys (default OFF)\n"
            f"  {ANSI_CYAN}B{ANSI_RESET}   = toggle combat\n"
            f"  {ANSI_CYAN}V{ANSI_RESET}   = toggle movement\n"
            f"  {ANSI_CYAN}I{ANSI_RESET}   = toggle items\n"
            f"  {ANSI_CYAN}?/h{ANSI_RESET} = help\n"
            f"  {ANSI_CYAN}q/ESC{ANSI_RESET} = quit\n"
        )
    else:
        # Ignore other keys
        pass
    return True


def getch() -> str:
    """Read a single character from stdin (raw mode)."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive demo of sound config + key bindings")
    parser.add_argument(
        "--input",
        type=str,
        help="Pre-defined key sequence (for testing without terminal)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Just show current config and exit (no key loop)",
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
            ANSI_GRAY, \
            ANSI_WHITE
        for attr in (
            "ANSI_RESET",
            "ANSI_BOLD",
            "ANSI_DIM",
            "ANSI_CYAN",
            "ANSI_YELLOW",
            "ANSI_GREEN",
            "ANSI_RED",
            "ANSI_GRAY",
            "ANSI_WHITE",
        ):
            globals()[attr] = ""

    config = get_sound_config()

    print(f"{ANSI_BOLD}{'=' * 60}{ANSI_RESET}")
    print(f"{ANSI_BOLD}  Sound Config — Interactive Demo{ANSI_RESET}")
    print(f"{ANSI_BOLD}{'=' * 60}{ANSI_RESET}")
    print()
    print(render_status(config))
    print()
    print(f"  {ANSI_DIM}Press ? for help, q/ESC to quit{ANSI_RESET}")
    print()

    if args.summary:
        return 0

    if args.input is not None:
        # Process pre-defined input
        for ch in args.input:
            print(f"{ANSI_DIM}> {ch}{ANSI_RESET}")
            if not process_key(config, ch):
                break
            # Re-render status
            print()
            print(render_status(config))
            print()
        return 0

    # Interactive mode (requires terminal)
    if not sys.stdin.isatty():
        print(f"{ANSI_RED}Error: stdin is not a terminal.{ANSI_RESET}")
        print("Use --input to provide a key sequence, or --summary for status.")
        return 1

    while True:
        try:
            ch = getch()
        except (KeyboardInterrupt, EOFError):
            break
        if not process_key(config, ch):
            break
        # Re-render
        print()
        print(render_status(config))
        print()
        print(f"  {ANSI_DIM}Press ? for help, q/ESC to quit{ANSI_RESET}")
        print()

    print(f"\n{ANSI_DIM}Demo ended.{ANSI_RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
