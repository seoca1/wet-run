#!/usr/bin/env python3
"""Headless sound demo: Prologue → Briefing → Matrix → Combat.

Plays all the audio cues that a GUI player would hear, prints stage
transitions to stdout, and exits. No tcod window required.

This is the "audio-only" version for users who just want to hear the
soundtrack of the early game.

Usage:
  uv run python scripts/headless_sound_demo.py
  uv run python scripts/headless_sound_demo.py --fast
  uv run python scripts/headless_sound_demo.py --stage prologue
  uv run python scripts/headless_sound_demo.py --stage briefing
  uv run python scripts/headless_sound_demo.py --stage matrix
  uv run python scripts/headless_sound_demo.py --stage combat
  uv run python scripts/headless_sound_demo.py --no-sound
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.audio import sound_manager


def _play(name: str) -> None:
    """Play a sound (errors swallowed)."""
    if args.no_sound:
        return
    try:
        sound_manager.play(name)
    except Exception as e:
        print(f"  [sound error: {e}]")


def _section(title: str) -> None:
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def _subsection(title: str) -> None:
    print()
    print(f"--- {title} ---")


def main() -> int:
    parser = argparse.ArgumentParser(description="Headless sound demo (audio + text)")
    parser.add_argument(
        "--stage",
        choices=["prologue", "briefing", "matrix", "combat", "all"],
        default="all",
        help="Which stage to demo (default: all)",
    )
    parser.add_argument("--fast", action="store_true", help="Skip narration delays")
    parser.add_argument("--no-sound", action="store_true", help="Print cues without playing audio")
    parser.add_argument("--volume", type=float, default=0.2, help="Volume 0.0-1.0 (default 0.2)")
    global args
    args = parser.parse_args()

    sm = sound_manager.get_sound_manager()
    sm.set_volume(args.volume)

    _section("ROGUELIKE SPRAWL — Sound Demo (Headless)")
    print(f"Backend:  {sm._tool}")
    print(f"Volume:   {int(args.volume * 100)}%")
    print(f"Available: {sm.is_available()}")
    print(f"Sounds:   {len(sm.list_sounds())}")
    print()
    print("This demo plays the audio cues a player would hear during the")
    print("opening 2-3 minutes of the game. Press Ctrl+C to stop.")

    if not sm.is_available() and not args.no_sound:
        print()
        print("WARNING: No audio backend found.")
        print("Sounds will be printed but not played.")
        print("On macOS, 'afplay' should be built-in.")
        print("On Linux, install 'alsa-utils' for 'aplay'.")

    delay = 0.2 if args.fast else 0.6
    pause = 0.05 if args.fast else 0.4

    stages_to_run = (
        ["prologue", "briefing", "matrix", "combat"] if args.stage == "all" else [args.stage]
    )

    try:
        if "prologue" in stages_to_run:
            _demo_prologue(delay, pause)
        if "briefing" in stages_to_run:
            _demo_briefing(delay, pause)
        if "matrix" in stages_to_run:
            _demo_matrix(delay, pause)
        if "combat" in stages_to_run:
            _demo_combat(delay, pause)
    except KeyboardInterrupt:
        print("\n\n[stopped by user]")
        return 0

    _section("Demo complete")
    print("All stages played. Thanks for listening!")
    return 0


def _demo_prologue(delay: float, pause: float) -> None:
    """Demo: Prologue cinematic — typing and event trigger sounds."""
    _section("STAGE 1: PROLOGUE (The Sprawl)")
    print()
    print('"The sky above the port was the color of television,')
    print(' tuned to a dead channel..."')
    print("                                    — Neuromancer, opening line")
    print()
    print("Sound: event_trigger (cinematic begins)")
    _play("story/event_trigger")
    time.sleep(delay)

    # Simulate text typing — 4 chunks
    chunks = [
        "The sky above",
        " the port was the",
        " color of television,",
        " tuned to a dead channel.",
    ]
    for chunk in chunks:
        print(f"  >> typing: '{chunk}'")
        _play("story/text_typing")
        time.sleep(pause)

    print()
    print("Sound: event_trigger (cinematic ends)")
    _play("story/event_trigger")
    time.sleep(delay)


def _demo_briefing(delay: float, pause: float) -> None:
    """Demo: NPC briefing — dialogue advance sounds."""
    _section("STAGE 2: BRIEFING (The Finn's Office)")
    print()
    print("[Jacked into cyberspace. Meeting with The Finn.]")
    print()
    print("Sound: dialogue_advance (The Finn speaks)")
    _play("story/dialogue_advance")
    time.sleep(delay)

    lines = [
        "I need someone to jack into Sense/Net.",
        "First run. Nothing fancy.",
        "You'll find the data in the construct.",
        "ICE will be light — Wisp-class, maybe Hammer.",
    ]
    for line in lines:
        print(f'  THE FINN: "{line}"')
        _play("story/dialogue_advance")
        time.sleep(pause)

    print()
    print("Player choice: [1] Accept  [2] Negotiate fee")
    print("  >> menu select")
    _play("ui/menu_select")
    time.sleep(pause)
    print("  >> menu confirm")
    _play("ui/menu_confirm")
    time.sleep(delay)


def _demo_matrix(delay: float, pause: float) -> None:
    """Demo: Matrix entry + navigation sounds."""
    _section("STAGE 3: MATRIX (Cyberspace)")
    print()
    print("[Jacking into the Sense/Net grid...]")
    _play("movement/jack_in")
    time.sleep(delay)

    print()
    print("[Cyberspace: 12 nodes, depth 0..4]")
    print()
    print("Moving between nodes (graph traversal):")

    moves = [
        "→ Entry → Public_Grid_α",
        "→ Public_Grid_α → Sensor_Bridge",
        "→ Sensor_Bridge → Construct_Dixie",
        "→ Construct_Dixie → ICE_Wisp_01",
    ]
    for move in moves:
        print(f"  {move}")
        _play("movement/nav_step")
        time.sleep(pause)

    print()
    print("Player tries to go north (no path):")
    print("  >> nav_block (no neighbor in that direction)")
    _play("movement/nav_block")
    time.sleep(delay)

    print()
    print("[Reaching a data node — extraction]")
    _play("items/pickup")
    time.sleep(delay)
    print("  >>> Data extracted! +1 Data Fragment")
    _play("items/pickup")
    time.sleep(delay)


def _demo_combat(delay: float, pause: float) -> None:
    """Demo: Combat — skill effects, hits, victory."""
    _section("STAGE 4: COMBAT (ICE Encounter)")
    print()
    print("[Wisp-class ICE detected. Combat initiated.]")
    _play("combat/hit_normal")
    time.sleep(delay)

    print()
    print("Round 1:")
    print("  >> Player uses [Wisp] (T1 program)")
    _play("combat/skill_physical")
    time.sleep(pause)
    print("  >> ICE HP -8")
    _play("combat/hit_normal")
    time.sleep(pause)

    print()
    print("Round 2:")
    print("  >> Player uses [Hammer] (T2 program)")
    _play("combat/skill_physical")
    time.sleep(pause)
    print("  >> CRITICAL HIT! ICE HP -24")
    _play("combat/hit_crit")
    time.sleep(pause)

    print()
    print("Round 3:")
    print("  >> Player uses [Shield] (T2 buff)")
    _play("combat/skill_buff")
    time.sleep(pause)
    print("  >> +5 shield for 3 turns")
    time.sleep(pause)

    print()
    print("Round 4:")
    print("  >> ICE attacks: 6 damage blocked by shield")
    _play("combat/block")
    time.sleep(pause)
    print("  >> Player uses [Hammer] finisher")
    _play("combat/skill_physical")
    time.sleep(pause)
    print("  >> ICE HP -20. ICE defeated!")
    _play("combat/hit_normal")
    time.sleep(pause)

    print()
    print("Sound: combat_victory")
    _play("combat/victory")
    time.sleep(delay)

    print()
    print(">>> VICTORY!")
    print(">>> Rewards: 1x ICE Shard, 50 credits")
    print(">>> ICE node removed from cyberspace")
    _play("items/pickup")
    time.sleep(delay)

    print()
    print("[Demo continues — sound effects would continue for the rest of the run]")


if __name__ == "__main__":
    sys.exit(main())
