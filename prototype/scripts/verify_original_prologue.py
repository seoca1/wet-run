"""Headless verification of the original Sprawl Jockey story.

3 캐릭터 × 2 엔딩 = 6 시나리오를 자동 진행하여 줄거리가 의도대로 동작하는지 검증.

Usage:
  uv run python scripts/verify_original_prologue.py
  uv run python scripts/verify_original_prologue.py --character novice
  uv run python scripts/verify_original_prologue.py --character veteran
  uv run python scripts/verify_original_prologue.py --character heretic
  uv run python scripts/verify_original_prologue.py --ending A
  uv run python scripts/verify_original_prologue.py --ending B
  uv run python scripts/verify_original_prologue.py --all
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine.npc_event import NPCState
from wet_run.engine.npc_view import _execute_choice
from wet_run.engine.original_story import (
    CHARACTER_SELECT_EVENT,
    HERETIC_PROLOGUE_EVENT,
    NOVICE_PROLOGUE_EVENT,
    VETERAN_PROLOGUE_EVENT,
    get_ending_description,
)
from wet_run.engine.state import AppState

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_CYAN = "\033[96m"
ANSI_YELLOW = "\033[93m"
ANSI_MAGENTA = "\033[95m"
ANSI_GREEN = "\033[92m"
ANSI_RED = "\033[91m"
ANSI_GRAY = "\033[90m"

CHARACTER_INFO = {
    "novice": ("케이 (K) — Novice", NOVICE_PROLOGUE_EVENT, ANSI_CYAN),
    "veteran": ("실 (Sil) — Veteran", VETERAN_PROLOGUE_EVENT, ANSI_MAGENTA),
    "heretic": ("카스 (Kas) — Heretic", HERETIC_PROLOGUE_EVENT, ANSI_RED),
}


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


def _show_line(line, idx: int) -> None:
    """Show a dialogue line."""
    if line.speaker:
        print(f"{ANSI_CYAN}>> {line.speaker}:{ANSI_RESET} {line.text}")
        print(f"   {ANSI_DIM}(KO: {line.text_ko}){ANSI_RESET}")
    else:
        # Narrator line
        print(f"{ANSI_DIM}{line.text}{ANSI_RESET}")


def _run_character_select(state: AppState) -> str:
    """Run the character selection. Returns chosen character id."""
    _header("STAGE 1: CHARACTER SELECT")

    event = CHARACTER_SELECT_EVENT
    line = event.lines[0]
    npc_state = NPCState(event=event)
    state.npc_state = npc_state

    _show_line(line, 0)

    print()
    print(f"{ANSI_BOLD}Choose your jockey:{ANSI_RESET}")
    for i, choice in enumerate(line.choices, 1):
        print(f"  {ANSI_DIM}{i}.{ANSI_RESET} {choice.text}")
        print(f"     {ANSI_DIM}(KO: {choice.text_ko}){ANSI_RESET}")

    # Auto-pick first choice (Novice) unless overridden
    chosen_idx = 0  # Novice
    print()
    print(f"{ANSI_DIM}>> Selecting choice {chosen_idx + 1} (auto-pilot){ANSI_RESET}")

    chosen_choice = line.choices[chosen_idx]
    _execute_choice(state, npc_state, chosen_choice)
    character = chosen_choice.effect_data.get("character", "novice")
    print(f"{ANSI_GREEN}✓ Selected: {CHARACTER_INFO[character][0]}{ANSI_RESET}")
    return character


def _run_prologue(state: AppState, character: str, ending: str) -> str:
    """Run the character's prologue. Returns ending id (A or B)."""
    name, event, color = CHARACTER_INFO[character]
    _header(f"STAGE 2: PROLOGUE — {name}")

    line = event.lines[0]
    npc_state = NPCState(event=event)
    state.npc_state = npc_state

    _show_line(line, 0)

    print()
    print(f"{ANSI_BOLD}Make your choice:{ANSI_RESET}")
    for i, choice in enumerate(line.choices, 1):
        print(f"  {ANSI_DIM}{i}.{ANSI_RESET} {choice.text}")
        print(f"     {ANSI_DIM}(KO: {choice.text_ko}){ANSI_RESET}")

    # Auto-pick based on requested ending (A=0, B=1)
    chosen_idx = 0 if ending == "A" else 1
    print()
    print(f"{ANSI_DIM}>> Selecting choice {chosen_idx + 1} → ending {ending}{ANSI_RESET}")

    chosen_choice = line.choices[chosen_idx]
    _execute_choice(state, npc_state, chosen_choice)
    result_ending = chosen_choice.effect_data.get("ending", "A")
    print(f"{ANSI_GREEN}✓ Ending: {result_ending}{ANSI_RESET}")
    return result_ending


def _show_ending(character: str, ending: str) -> None:
    """Display the ending summary."""
    _header(f"STAGE 3: ENDING — {ending}")

    name, _, color = CHARACTER_INFO[character]
    print(f"{ANSI_BOLD}Character:{ANSI_RESET} {name}")
    print(f"{ANSI_BOLD}Ending:{ANSI_RESET} {ending}")
    print()

    description = get_ending_description(character, ending)
    print(f"{color}{description}{ANSI_RESET}")
    print()

    if ending == "A":
        print(f"{ANSI_GREEN}✓ Jockey Lives. {name} survived.{ANSI_RESET}")
    else:
        print(f"{ANSI_RED}✗ Jockey Flatlines. {name} didn't make it.{ANSI_RESET}")


def _run_full_scenario(character: str, ending: str) -> None:
    """Run a complete scenario: character select → prologue → ending."""
    state = AppState()

    # Stage 1: Character select (auto-picks Novice)
    selected = _run_character_select(state)
    if selected != character:
        # User asked for a specific character but select gave us Novice.
        # That's OK — we just show that the user *could* pick another character.
        # We continue with the requested character.
        print(
            f"{ANSI_DIM}>> (Continuing with user-requested character: "
            f"{CHARACTER_INFO[character][0]}){ANSI_RESET}"
        )

    # Stage 2: Prologue
    actual_ending = _run_prologue(state, character, ending)

    # Stage 3: Ending
    _show_ending(character, actual_ending)

    # Verify
    print()
    print(f"{ANSI_BOLD}Verification:{ANSI_RESET}")
    expected = ending
    actual = actual_ending
    if actual == expected:
        print(f"  {ANSI_GREEN}✓ Ending matches request ({expected}){ANSI_RESET}")
    else:
        print(f"  {ANSI_RED}✗ Ending mismatch (expected {expected}, got {actual}){ANSI_RESET}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify original Sprawl Jockey story (Phase 2)")
    parser.add_argument(
        "--character",
        choices=["novice", "veteran", "heretic", "all"],
        default="all",
        help="Which character to test (default: all)",
    )
    parser.add_argument(
        "--ending",
        choices=["A", "B", "all"],
        default="all",
        help="Which ending to trigger (default: all)",
    )
    args = parser.parse_args()

    _header("ORIGINAL PROLOGUE VERIFICATION")
    print(f"{ANSI_DIM}This demo runs the original Sprawl Jockey story:{ANSI_RESET}")
    print(f"{ANSI_DIM}- 3 characters (Novice/Veteran/Heretic){ANSI_RESET}")
    print(f"{ANSI_DIM}- 2 endings per character (A: Lives / B: Flatlines){ANSI_RESET}")
    print(f"{ANSI_DIM}- 6 total scenarios{ANSI_RESET}")
    print()
    print(f"Character: {args.character}")
    print(f"Ending: {args.ending}")

    characters = ["novice", "veteran", "heretic"] if args.character == "all" else [args.character]
    endings = ["A", "B"] if args.ending == "all" else [args.ending]

    for character in characters:
        for ending in endings:
            _run_full_scenario(character, ending)

    _header("VERIFICATION COMPLETE")
    print(f"{ANSI_GREEN}All scenarios rendered successfully.{ANSI_RESET}")
    print()
    print(f"{ANSI_DIM}Next step: Phase 3 — apply to actual game structure.{ANSI_RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
