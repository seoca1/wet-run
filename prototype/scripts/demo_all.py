"""Full game flow demo with save progress integration (ADR-0032 + ADR-0021).

Creates a sample save file (if none exists), then runs through the entire
state machine showing:
    1. MENU (5 options)
    2. GRAPHIC_NOVEL_MENU (5 options)
    3. GRAPHIC_NOVEL (auto-play scenes)
    4. SAVED_PROGRESS (showing actual save data)
    5. Back to MENU

Usage:
    uv run python scripts/demo_all.py
    uv run python scripts/demo_all.py --duration 15
    uv run python scripts/demo_all.py --no-clear
    uv run python scripts/demo_all.py --lang ko
    uv run python scripts/demo_all.py --no-seed   # don't create sample save
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import tcod.console

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine import graphic_novel_view, menu, save_progress
from wet_run.engine.graphic_novel_view import (
    dialogue_typed_chars,
    load_background,
    load_portrait,
    load_prologue_chain,
    load_scene_chain,
    render_scene,
)
from wet_run.engine.state import AppState
from wet_run.i18n import Translator
from wet_run.missions import JobBoard

# Art cache
_demo_all_cache: dict[str, object] = {}


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


def create_sample_save(save_dir: Path, character_id: str = "veteran") -> None:
    """Create a sample save file for demo purposes.

    Writes a valid SavedRun JSON to slot 1 with rich data.
    """
    save_dir.mkdir(parents=True, exist_ok=True)
    sample = {
        "version": "0.1.0",
        "saved_at": datetime.now(UTC).isoformat(),
        "elapsed_seconds": 90 * 60,
        "run_state": {
            "current_stage": "Tessier-Ashpool HQ",
            "completed_stages": [f"mission_{i}" for i in range(12)],
            "pending_advance": False,
            "current_target_node": "ta_payroll_inner",
            "last_visited_node": "ta_payroll_inner",
            "mission_id": "watchdog_patrol",
            "started_at_ms": int(time.time() * 1000) - 90 * 60 * 1000,
        },
        "mission": None,
        "app_state": {
            "character_id": character_id,
            "screen": "HUB",
        },
        "metadata": {
            "player_grade": 3,
            "credits": 567,
            "data_recovered": 234,
            "character_id": character_id,
        },
    }
    path = save_dir / "slot_1.json"
    path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stderr.write(f"[demo_all] Created sample save at {path}\n")


def render_saved_progress(
    console: tcod.console.Console,
    t: Translator,
    save_dir: Path,
) -> None:
    """Render the SAVED_PROGRESS screen."""
    summary = save_progress.get_progress_summary(save_dir=save_dir)
    console.clear()
    width = console.width

    # Top bar
    title = "당신의 자키" if t.lang == "ko" else "Your Jockey"
    console.print(0, 0, "═" * width)
    console.print((width - len(title)) // 2, 0, f" {title} ")
    console.print(0, 1, "─" * width)

    if not summary.has_save:
        msg = "아직 자키가 없습니다" if t.lang == "ko" else "No save file yet"
        console.print((width - len(msg)) // 2, 8, msg)
        hint = "[1] NEW RUN  [2] 다른 캐릭터  [3] 메인메뉴"
        console.print((width - len(hint)) // 2, 14, hint)
        return

    # Summary lines
    lines = save_progress.render_summary_lines(summary, t_lang=t.lang)
    y = 3
    for line in lines:
        console.print(4, y, line)
        y += 1

    # Bottom options
    y += 1
    console.print(4, y, "─" * 40)
    y += 1
    if t.lang == "ko":
        opts = [
            "[1] 다른 캐릭터 스토리 보기",
            "[2] 게임플레이 계속 (HUB)",
            "[3] 메인메뉴",
        ]
    else:
        opts = [
            "[1] Other character stories",
            "[2] Continue gameplay (HUB)",
            "[3] Main menu",
        ]
    for opt in opts:
        console.print(4, y, opt)
        y += 1


def render_gn_menu(
    console: tcod.console.Console,
    t: Translator,
    selected: int,
) -> None:
    """Render GRAPHIC_NOVEL_MENU."""
    graphic_novel_view.render_graphic_novel_menu(
        console, t, selected_index=selected, has_save=False
    )


def render_gn_frame(
    console: tcod.console.Console,
    state: AppState,
    t: Translator,
    data_dir: Path,
) -> bool:
    """Render one frame of graphic novel. Returns True if finished."""
    chain: list = _demo_all_cache.get(f"chain:{state.gn_mode}:{state.gn_ending_choice}")  # type: ignore[assignment]
    if chain is None:
        ending = state.gn_ending_choice or "A"
        if state.gn_mode == "prologue":
            chain = load_prologue_chain(data_dir / "scenes", seed=42, ending=ending)
        else:
            chain = load_scene_chain(data_dir / "scenes", state.gn_mode, ending=ending)
        _demo_all_cache[f"chain:{state.gn_mode}:{state.gn_ending_choice}"] = list(chain)

    if state.gn_scene_index >= len(chain):
        return True

    scene = chain[state.gn_scene_index]
    if not scene.dialogue:
        state.gn_scene_index += 1
        state.gn_elapsed_ms = 0.0
        return False

    dialogue = scene.dialogue[state.gn_dialogue_index]
    text = dialogue.text_ko if t.lang == "ko" else dialogue.text_en
    typed = dialogue_typed_chars(dialogue.duration_ms, state.gn_elapsed_ms, len(text))

    art_dir = data_dir / "art"
    bg = _demo_all_cache.get(f"bg:{scene.background_id}")
    if bg is None and f"bg:{scene.background_id}" not in _demo_all_cache:
        try:
            bg = load_background(art_dir, scene.background_id)
        except (KeyError, FileNotFoundError):
            bg = None
        _demo_all_cache[f"bg:{scene.background_id}"] = bg

    p_l = None
    p_r = None
    for p_id, slot in (
        (scene.portrait_left, "p_l"),
        (scene.portrait_right, "p_r"),
    ):
        if p_id:
            pkey = f"portrait:{p_id}"
            val = _demo_all_cache.get(pkey)
            if val is None and pkey not in _demo_all_cache:
                try:
                    val = load_portrait(art_dir, p_id)
                except (KeyError, FileNotFoundError):
                    val = None
                _demo_all_cache[pkey] = val
            if slot == "p_l":
                p_l = val
            else:
                p_r = val

    render_scene(
        console,
        scene,
        dialogue,
        bg,  # type: ignore[arg-type]
        p_l,  # type: ignore[arg-type]
        p_r,  # type: ignore[arg-type]
        t,
        typed,
        state.gn_scene_index,
        len(chain),
        paused=state.gn_paused,
    )

    # Advance
    state.gn_elapsed_ms += 100 * 10  # 10x speed for demo
    if state.gn_elapsed_ms >= dialogue.duration_ms:
        state.gn_dialogue_index += 1
        state.gn_elapsed_ms = 0.0
        if state.gn_dialogue_index >= len(scene.dialogue):
            state.gn_scene_index += 1
            state.gn_dialogue_index = 0
            if state.gn_scene_index >= len(chain):
                return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--duration", type=float, default=20.0)
    parser.add_argument("--step-delay", type=float, default=0.5)
    parser.add_argument("--no-clear", action="store_true")
    parser.add_argument("--lang", default="ko", choices=["en", "ko"])
    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Don't create sample save (use existing or none)",
    )
    parser.add_argument(
        "--character",
        default="veteran",
        choices=["novice", "veteran", "heretic"],
        help="Sample save character (default veteran)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    save_dir = project_root / "saves"

    # Create sample save if requested
    if not args.no_seed:
        create_sample_save(save_dir, character_id=args.character)

    t = Translator(args.lang, data_dir=data_dir / "i18n")
    state = AppState()
    state.job_board = JobBoard.load(data_dir / "missions" / "missions.json")
    state.gn_mode = "prologue"
    console = tcod.console.Console(80, 30, order="F")

    # State machine
    # MENU → GRAPHIC_NOVEL_MENU → GRAPHIC_NOVEL → SAVED_PROGRESS → MENU
    step = 0
    start = time.monotonic()
    screen = "MENU"
    gn_finished = False
    sp_shown = False

    # Initial frame: MENU
    menu.render_menu(console, t, state)
    _print_frame(
        console,
        clear=not args.no_clear,
        step=step,
        elapsed=0.0,
        screen=screen,
        narration="MENU — 5 options (NEW RUN / GRAPHIC NOVEL / CONTINUE / SETTINGS / CREDITS)",
    )
    step += 1
    time.sleep(args.step_delay)

    while time.monotonic() - start < args.duration:
        elapsed = time.monotonic() - start

        if screen == "MENU":
            # After 1 step, transition to GRAPHIC_NOVEL_MENU
            if step > 1:
                state.gn_scene_index = 0
                state.gn_dialogue_index = 0
                state.gn_elapsed_ms = 0.0
                state.gn_paused = False
                screen = "GRAPHIC_NOVEL_MENU"
        elif screen == "GRAPHIC_NOVEL_MENU":
            # ADR-0048: prologue skips ending menu
            state.gn_ending_choice = "A"
            screen = "GRAPHIC_NOVEL"
        elif screen == "GRAPHIC_NOVEL":
            gn_finished = render_gn_frame(console, state, t, data_dir)
            if gn_finished:
                screen = "SAVED_PROGRESS"
        elif screen == "SAVED_PROGRESS":
            if not sp_shown:
                sp_shown = True
            # After 3 steps, return to MENU
            if step > 1 and state.gn_scene_index == 0 and state.gn_dialogue_index == 0:
                # Already moved past
                pass
            if step % 6 == 0:
                state.has_save = True
                state.gn_scene_index = 0
                state.gn_dialogue_index = 0
                state.gn_elapsed_ms = 0.0
                screen = "MENU"
                sp_shown = False

        # Render
        if screen == "MENU":
            menu.render_menu(console, t, state)
            narration = "MENU"
        elif screen == "GRAPHIC_NOVEL_MENU":
            render_gn_menu(console, t, selected=0)
            narration = "GRAPHIC_NOVEL_MENU (prologue selected)"
        elif screen == "GRAPHIC_NOVEL":
            narration = f"GRAPHIC_NOVEL scene {state.gn_scene_index + 1}/..."
        elif screen == "SAVED_PROGRESS":
            render_saved_progress(console, t, save_dir)
            narration = "SAVED_PROGRESS (sample save data)"

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

    sys.stdout.write(f"\n=== demo_all complete: {step} steps in {args.duration:.0f}s ===\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.stdout.write("\n[interrupted]\n")
        sys.exit(130)
