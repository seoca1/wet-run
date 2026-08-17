"""Death & Restart Cycle demo (ADR-0040).

Demonstrates the full death → archive → restart flow:
    1. Player triggers death → DEATH screen
    2. Auto-advances to DEATH_SUMMARY (jockey's epitaph)
    3. Player picks: 새 자키 / 같은 자키 / Hall of Dead / 메뉴
    4. Hall of Dead Jockeys archive is shown

Usage:
    uv run python scripts/death_demo.py
    uv run python scripts/death_demo.py --no-clear
    uv run python scripts/death_demo.py --lang ko
    uv run python scripts/death_demo.py --fast
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import tcod.console

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine import death  # noqa: F401  # used for _get_history monkeypatch
from wet_run.engine.death import (
    handle_death_summary_choice,
    render_death_screen,
    render_death_summary_screen,
    render_hall_of_dead_screen,
    trigger_death,
)
from wet_run.engine.jockey_history import JockeyHistory
from wet_run.engine.state import AppState, ScreenKind
from wet_run.i18n import Translator


def _console_to_text(console: tcod.console.Console) -> str:
    """Convert tcod console to plain text."""
    lines: list[str] = []
    for y in range(console.height):
        chars: list[str] = []
        for x in range(console.width):
            code = int(console.ch[x, y])
            chars.append(chr(code) if 0 < code < 0x110000 else " ")
        lines.append("".join(chars).rstrip())
    return "\n".join(lines)


def _print_frame(
    console: tcod.console.Console,
    *,
    clear: bool,
    step: int,
    elapsed: float,
    screen: str,
    narration: str,
) -> None:
    if clear:
        sys.stdout.write("\033[2J\033[H")
    sys.stdout.write(_console_to_text(console))
    sys.stdout.write("\n")
    sys.stdout.write(f"[Step {step:03d}  T+{elapsed:5.1f}s  Screen: {screen}]\n")
    if narration:
        sys.stdout.write(f"> {narration}\n")
    sys.stdout.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--duration", type=float, default=8.0)
    parser.add_argument("--step-delay", type=float, default=1.0)
    parser.add_argument("--no-clear", action="store_true")
    parser.add_argument("--lang", default="ko", choices=["en", "ko"])
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    # Use a dedicated save path for the demo to avoid clobbering real data
    demo_jockeys = data_dir / "jockeys" / "deceased_demo.json"

    # Initialize state — mid-run, about to die
    state = AppState()
    state.character_id = "veteran"
    state.player_grade = 3
    state.player_hp = 0
    state.player_max_hp = 100
    state.player_ppl = 12
    state.inventory = {"wisp_T2": 1, "loa_drum": 3, "credit_chip": 5}
    state.completed_missions = {"mission_1", "mission_2", "mission_3"}
    state.current_node_id = "ta_payroll_inner"
    state.current_mission = type("M", (), {"id": "watchdog_patrol"})()
    state.mission_progress = {"extract_data": 2, "defeat": 1}
    state.demo_elapsed_s = 47 * 60  # 47 minutes in
    state.is_dead = False
    state.screen = ScreenKind.DEATH

    Translator(args.lang, data_dir=data_dir / "i18n")
    console = tcod.console.Console(80, 30, order="F")

    # Patch JockeyHistory to use demo path
    from wet_run.engine import death as death_mod

    def _demo_history() -> JockeyHistory:
        # Load or create the demo archive
        return JockeyHistory(save_path=demo_jockeys)

    death_mod._get_history = _demo_history  # type: ignore[assignment]

    start = time.monotonic()
    step = 0
    narration = "Demo: Death & Restart Cycle (ADR-0040)"
    screen = "DEATH"

    # 1) DEATH screen
    render_death_screen(console, state)
    _print_frame(
        console,
        clear=not args.no_clear,
        step=step,
        elapsed=0.0,
        screen=screen,
        narration=narration,
    )
    step += 1
    time.sleep(args.step_delay)

    while time.monotonic() - start < args.duration:
        elapsed = time.monotonic() - start
        if state.screen is ScreenKind.DEATH and not state.is_dead:
            # Trigger death
            trigger_death(state, reason="Combat")
            screen = "DEATH"
            narration = "HP=0 → trigger_death() → DEATH"
            render_death_screen(console, state)
        elif state.screen is ScreenKind.DEATH and state.is_dead:
            # Already dead — advance to DEATH_SUMMARY
            from wet_run.engine.death import advance_to_death_summary

            advance_to_death_summary(state)
            screen = "DEATH_SUMMARY"
            narration = "DEATH → DEATH_SUMMARY (jockey archived)"
            render_death_summary_screen(console, state, width=80, height=30)
        elif state.screen is ScreenKind.DEATH_SUMMARY:
            # Pick a choice: 1 (new jockey)
            handle_death_summary_choice(state, "new_jockey")
            screen = str(state.screen.value)
            narration = "[1] 새 자키 → CHARACTER_SELECT"
            if state.screen is ScreenKind.CHARACTER_SELECT:
                render_death_summary_screen(console, state, width=80, height=30)
            else:
                render_hall_of_dead_screen(console, state, width=80, height=30)
        elif state.screen is ScreenKind.HALL_OF_DEAD:
            # Show Hall of Dead
            screen = "HALL_OF_DEAD"
            narration = "Hall of Dead Jockeys (archive)"
            render_hall_of_dead_screen(console, state, width=80, height=30)
        elif state.screen is ScreenKind.CHARACTER_SELECT:
            screen = "CHARACTER_SELECT"
            narration = "새 자키 선택 (캐릭터 변경됨)"
            console.clear()
            console.print(2, 4, f"> New jockey: {state.character_id}")
            console.print(2, 6, "[1] 케이 (K) — Novice")
            console.print(2, 7, "[2] 실 (Sil) — Veteran")
            console.print(2, 8, "[3] 카스 (Kas) — Heretic")
            console.print(2, 11, f"  → Selected: {state.character_id}")
        else:
            screen = str(state.screen.value)
            narration = "End of demo flow"
            break

        _print_frame(
            console,
            clear=not args.no_clear,
            step=step,
            elapsed=elapsed,
            screen=screen,
            narration=narration,
        )
        step += 1
        time.sleep(args.step_delay)

    sys.stdout.write(f"\n=== death_demo complete: {step} steps in {args.duration:.0f}s ===\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.stdout.write("\n[interrupted]\n")
        sys.exit(130)
