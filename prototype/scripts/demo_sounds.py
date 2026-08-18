"""Demo: Play all 27 default sounds in sequence.

Usage:
    python scripts/demo_sounds.py
    python scripts/demo_sounds.py --category combat
    python scripts/demo_sounds.py --fast
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.audio import sound_manager  # noqa: E402
from wet_run.audio.sound_manager import DEFAULT_SOUNDS  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Play all default sounds in sequence")
    parser.add_argument(
        "--category",
        choices=["ui", "story", "combat", "movement", "items", "all"],
        default="all",
        help="Filter by category (default: all)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip delay between sounds",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.6,
        help="Delay between sounds in seconds (default: 0.6)",
    )
    args = parser.parse_args()

    sm = sound_manager.get_sound_manager()

    print("=" * 60)
    print("  Wet Run - Sound Demo")
    print("=" * 60)
    print(f"Backend available: {sm.is_available()}")
    print(f"Volume: {int(sm.volume * 100)}%")
    print(f"Muted: {sm.muted}")
    print(f"Total sounds: {len(DEFAULT_SOUNDS)}")
    print("=" * 60)

    if not sm.is_available():
        print("WARNING: No audio backend found.")
        print("On macOS, 'afplay' should be built-in.")
        print("On Linux, install 'alsa-utils' for 'aplay'.")
        print("On Windows, 'winsound' is built-in.")
        return 1

    # Filter sounds
    if args.category == "all":
        sounds = list(DEFAULT_SOUNDS.items())
    else:
        prefix = f"{args.category}/"
        sounds = [(n, info) for n, info in DEFAULT_SOUNDS.items() if n.startswith(prefix)]

    print(f"\nPlaying {len(sounds)} sounds in category: {args.category}")
    print("(Press Ctrl+C to stop)\n")

    delay = 0.05 if args.fast else args.delay

    try:
        for i, (name, (_filename, freq, dur_ms, kind)) in enumerate(sounds, 1):
            print(f"  [{i:2d}/{len(sounds)}] {name:<25} ({kind}, {freq}Hz, {dur_ms}ms)")
            sm.play(name)
            if i < len(sounds):
                time.sleep(delay)
    except KeyboardInterrupt:
        print("\n\nStopped by user.")
        return 0

    print("\n" + "=" * 60)
    print("  All sounds played successfully!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
