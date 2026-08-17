"""Quick playthrough demo — runs the game in auto-pilot mode.

Single command:
    uv run python scripts/play.py

The script initializes the full game state, then auto-progresses
through the screen state machine:
    Menu → Character Select → Chapter → Hub → Matrix → Hub cycle

Default duration is 30 seconds.

Options:
    --duration N      Total seconds (default 30)
    --step-delay D    Seconds per frame (default 0.4)
    --no-clear        Don't clear the screen between frames
    --lang {en,ko}    UI language (default en)
    --seed N          Mission seed (default 42)
    --mission N       Which mission to play (1=first, default 1)
    --character C     Auto-pick character (novice|veteran|heretic, default novice)
    --gn-mode MODE    If set, play graphic novel mode (prologue|novice|veteran|heretic)
    --phase-1-5       Run all five Phase 1-5 headless demos
                      (play_dungeon_mode / play_vfx_overlay /
                      play_mission_mapping / play_ecs_dungeon /
                      play_novel_runtime / play_arc_bsp) and exit.
                      Useful as a smoke test for the operator-point
                      demos added with ADR-0060 / 0061.
    --bsp-mission ID  Run a single BSP dungeon via play_arc_bsp.py
                      --mission <id>.  Useful for inspecting one
                      layout in detail.
    --bsp-seed N      RNG seed for --bsp-mission (default 2026).
    --bsp-grade N     Mission grade 1-5 (default 2).
    --arc-bsp         Walk all three character arcs through
                      play_arc_bsp.py (3 missions per arc) as a
                      regression check, then exit.  Returns 0 iff
                      every arc finished cleanly.
    --list-missions   Print every mission id in data/missions/missions.json,
                      one per line, then exit.  Use as a target-list
                      for --bsp-mission <id>.
    --show-controls   Print controls hint at start
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import tcod.console

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine import hub, matrix_view, menu, story_view
from wet_run.engine.chapter_cutscene import (
    CombatData,
    get_arc_for_character,
    get_chapter,
)
from wet_run.engine.chapter_view import chapter_for_character, tick_chapter
from wet_run.engine.graphic_novel_view import (
    Background,
    Portrait,
    SceneData,
)
from wet_run.engine.salvation import (
    SalvationRunner,
)
from wet_run.engine.state import AppState, ScreenKind
from wet_run.engine.story_view import StoryRegistry
from wet_run.i18n import Translator
from wet_run.matrix.exploration import ExplorationState
from wet_run.matrix.generator import MatrixGenerator
from wet_run.matrix.ppl import calculate_ppl
from wet_run.matrix.zdr import node_status, node_zdr
from wet_run.missions import JobBoard
from wet_run.run import ChapterState, Stage, ensure_run_state


def _setup(args: argparse.Namespace) -> tuple[AppState, Translator, StoryRegistry]:
    """Initialize the full game state from data files."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    t = Translator(args.lang, data_dir=data_dir / "i18n")
    state = AppState()
    state.job_board = JobBoard.load(data_dir / "missions" / "missions.json")
    registry = StoryRegistry.load(data_dir)
    return state, t, registry


def _console_to_text(console: tcod.console.Console) -> str:
    """Convert a tcod console buffer to plain text."""
    lines: list[str] = []
    for y in range(console.height):
        chars: list[str] = []
        for x in range(console.width):
            code = int(console.ch[x, y])
            chars.append(chr(code) if 0 < code < 0x110000 else " ")
        lines.append("".join(chars).rstrip())
    return "\n".join(lines)


def _render_current(
    console: tcod.console.Console,
    state: AppState,
    t: Translator,
    story_reg: StoryRegistry,
    elapsed: float,
) -> None:
    """Render the current screen onto the console."""
    state.demo_step = state.demo_step
    state.demo_elapsed_s = elapsed
    if state.screen is ScreenKind.MENU:
        menu.render_menu(console, t, state)
    elif state.screen is ScreenKind.GRAPHIC_NOVEL_MENU:
        from wet_run.engine import graphic_novel_view
        from wet_run.engine.graphic_novel_save import list_save_slots

        gn_save_dir = Path(__file__).parent.parent / "data" / "saves"
        slots = list_save_slots(save_dir=gn_save_dir)
        has_save = any(s.get("has_save", False) for s in slots)

        graphic_novel_view.render_graphic_novel_menu(
            console, t, selected_index=state.gn_scene_index, has_save=has_save
        )
    elif state.screen is ScreenKind.GRAPHIC_NOVEL:
        _render_graphic_novel_frame(console, state, t, elapsed)
    elif state.screen is ScreenKind.SAVED_PROGRESS:
        from wet_run.engine import save_progress as sp

        console.clear()
        summary = sp.get_progress_summary(save_dir=Path(__file__).parent.parent / "saves")
        lines = sp.render_summary_lines(summary, t_lang=t.lang)
        console.print(2, 2, "═══ SAVED PROGRESS ═══")
        for i, line in enumerate(lines):
            console.print(2, 4 + i, line)
        console.print(2, 16, "  [1] 다른 캐릭터 보기  [2] 게임 계속  [3] 메인메뉴")
    elif state.screen is ScreenKind.CHARACTER_SELECT:
        # Render as a stub message (real NPC event handled in interactive flow)
        console.clear()
        console.print(2, 2, "═══ CHARACTER SELECT (auto-pilot) ═══")
        console.print(2, 4, "> The Finn: I need a jockey. Sense/Net, first run.")
        console.print(2, 6, "  1. 케이 (K) — Novice       'I just need the money.'")
        console.print(2, 7, "  2. 실 (Sil) — Veteran     'I know the risks.'")
        console.print(2, 8, "  3. 카스 (Kas) — Heretic    'I'm here to burn it all down.'")
        console.print(2, 11, f"  → Auto-selected: {state.character_id}")
    elif state.screen is ScreenKind.CHAPTER:
        # Render the chapter typing effect
        from wet_run.engine import chapter_view

        chapter = chapter_for_character(state.character_id, Path(__file__).parent.parent / "data")
        state.chapter_elapsed_ms = elapsed * 1000
        state.chapter_typed_chars = tick_chapter(
            chapter, state.chapter_elapsed_ms, state.chapter_typed_chars
        )
        chapter_view.render_chapter(
            console, chapter, t, state.chapter_typed_chars, state.chapter_elapsed_ms
        )
    elif state.screen is ScreenKind.ARC_PHASE:
        # Render arc phase with beats
        from wet_run.engine.phase_view import render_arc_phase, tick_arc_phase

        if state.current_arc is not None:
            chapter = state.current_arc.chapters[state.current_chapter_index]
            phase = chapter.phases[state.current_phase_index]

            # Update typing
            state.phase_elapsed_ms += elapsed * 1000
            new_typed, should_advance = tick_arc_phase(
                phase,
                state.current_beat_index,
                state.phase_elapsed_ms,
                state.phase_typed_chars,
                30,
            )
            state.phase_typed_chars = new_typed

            # Advance beat if needed
            if should_advance:
                current_beat = phase.beats[state.current_beat_index]
                if current_beat.type == "combat" and phase.combat is not None:
                    _resolve_arc_combat(state, phase.combat)
                    # Advance to next beat after auto-resolve
                    if state.current_beat_index < len(phase.beats) - 1:
                        state.current_beat_index += 1
                        state.phase_typed_chars = 0
                        state.phase_elapsed_ms = 0.0
                    elif state.current_phase_index < len(chapter.phases) - 1:
                        state.current_phase_index += 1
                        state.current_beat_index = 0
                        state.phase_typed_chars = 0
                        state.phase_elapsed_ms = 0.0
                    else:
                        state.screen = ScreenKind.HUB
                elif state.current_beat_index < len(phase.beats) - 1:
                    state.current_beat_index += 1
                    state.phase_typed_chars = 0
                    state.phase_elapsed_ms = 0.0
                elif state.current_phase_index < len(chapter.phases) - 1:
                    state.current_phase_index += 1
                    state.current_beat_index = 0
                    state.phase_typed_chars = 0
                    state.phase_elapsed_ms = 0.0
                else:
                    # Chapter complete - transition to next screen
                    state.screen = ScreenKind.HUB

            render_arc_phase(
                console,
                phase,
                state.current_beat_index,
                state.phase_typed_chars,
                state.phase_elapsed_ms,
                0,
                t,
                30,
                state,
            )
    elif state.chapter_cutscene_state is not None:
        # Render chapter cutscene (overlaid on current screen)
        from wet_run.engine.chapter_cutscene import render_cutscene_frame

        cs_state = state.chapter_cutscene_state
        dt_ms = int(elapsed * 1000) - int((elapsed - 0.4) * 1000)
        cs_state.tick(dt_ms)
        render_cutscene_frame(console, cs_state, None, None, None, t, 0, 1)
    elif state.screen is ScreenKind.HUB:
        hub.render_hub(console, t, state)
    elif state.screen is ScreenKind.MATRIX and state.matrix is not None:
        layout = matrix_view.get_layout(state.matrix)
        matrix_view.render_matrix(console, t, state, layout)
    elif state.screen is ScreenKind.HACK:
        from wet_run.engine import hacking_view

        hacking_view.step_hack(state, elapsed)
        hacking_view.render_hack(console, t, state)
    elif state.screen is ScreenKind.STORY:
        story_view.render_story(
            console,
            state,
            story_reg,
            aftermath_id=state.story_aftermath_id,
            elapsed_s=elapsed,
        )
    elif state.screen is ScreenKind.ENDING:
        state.ending_elapsed_ms += elapsed * 1000
        _render_ending(console, state, t)


def _render_ending(console: tcod.console.Console, state: AppState, t: Translator) -> None:
    """Render the ending screen."""
    from wet_run.engine.original_story import get_ending_description

    width, height = console.width, console.height
    console.clear()

    rs = state.run_state
    ending_key = rs.chapter_state.value if rs else "ending_a"
    character = state.character_id or "novice"

    if ending_key.startswith("ending_"):
        ending_letter = ending_key.replace("ending_", "").upper()
    else:
        ending_letter = "A"

    console.print(0, 0, "═" * width)
    title = f"━━━ ENDING {ending_letter} ━━━"
    console.print((width - len(title)) // 2, 0, title)

    ending_desc = get_ending_description(character, ending_letter.lower())

    arc_name = state.current_arc.title_en if state.current_arc else f"{character.title()} Arc"

    lines = [
        "",
        f"  {arc_name}",
        "",
        "  The story has reached its conclusion.",
        "",
    ]

    for i, line in enumerate(lines):
        console.print(2, 3 + i, line, fg=(200, 200, 200))

    desc_lines = ending_desc.split("\n") if ending_desc else []
    for i, line in enumerate(desc_lines[:8]):
        color = (220, 200, 100) if i == 0 else (180, 180, 180)
        console.print(2, 8 + i, line, fg=color)

    console.print(0, height - 5, "─" * width)
    console.print(2, height - 4, f"  Character: {character.title()}")
    console.print(2, height - 3, f"  Ending: {ending_letter}")
    console.print(2, height - 2, "  [ESC] Return to Main Menu")
    console.print(0, height - 1, "═" * width)


def _print_frame(
    console: tcod.console.Console,
    *,
    clear: bool,
    step: int,
    elapsed: float,
    narration: str,
) -> None:
    """Write a single frame to stdout."""
    if clear:
        sys.stdout.write("\033[2J\033[H")
    sys.stdout.write(_console_to_text(console))
    sys.stdout.write("\n")
    sys.stdout.write(
        f"[Step {step:03d}  T+{elapsed:5.1f}s  Screen: {state_screen_label(console)}]\n"
    )
    if narration:
        sys.stdout.write(f"> {narration}\n")
    sys.stdout.flush()


def state_screen_label(_: tcod.console.Console) -> str:
    # The actual screen label is rendered into the console; the line
    # above is just metadata for the demo.
    return "rendered"


# Graphic novel state cache (loaded once, reused across frames)
_gn_cache: dict[str, Background | Portrait | list[SceneData] | None] = {}


def _get_scene_chain(state: AppState, data_dir: Path) -> list[SceneData]:
    """Return the scene chain for the current graphic novel mode.

    ADR-0048: chain depends on ``state.gn_ending_choice`` (A/B) too.
    """
    from wet_run.engine.graphic_novel_view import (
        load_prologue_chain,
        load_scene_chain,
    )

    cache_key = f"chain:{state.gn_mode}:{state.character_id}:{state.gn_ending_choice}"
    cached = _gn_cache.get(cache_key)
    if isinstance(cached, list):
        return list(cached)
    ending = state.gn_ending_choice or "A"
    if state.gn_mode == "prologue":
        chain = load_prologue_chain(data_dir / "scenes", seed=42, ending=ending)
    else:
        chain = load_scene_chain(data_dir / "scenes", state.gn_mode, ending=ending)
    _gn_cache[cache_key] = list(chain)
    return list(chain)


def _render_graphic_novel_frame(
    console: tcod.console.Console,
    state: AppState,
    t: Translator,
    elapsed: float,
) -> None:
    """Render one frame of the graphic novel (auto-pilot mode)."""
    from wet_run.engine.graphic_novel_view import (
        dialogue_typed_chars,
        load_background,
        load_portrait,
        render_scene,
    )

    data_dir = Path(__file__).parent.parent / "data"
    chain = _get_scene_chain(state, data_dir)
    if not chain or state.gn_scene_index >= len(chain):
        state.screen = ScreenKind.SAVED_PROGRESS
        return
    scene = chain[state.gn_scene_index]
    if not scene.dialogue:
        state.gn_scene_index += 1
        state.gn_dialogue_index = 0
        state.gn_elapsed_ms = 0.0
        return
    dialogue = scene.dialogue[state.gn_dialogue_index]
    text = dialogue.text_ko if t.lang == "ko" else dialogue.text_en
    typed = dialogue_typed_chars(dialogue.duration_ms, state.gn_elapsed_ms, len(text))

    # Load art (cached per scene id)
    bg: Background | None = None
    p_l: Portrait | None = None
    p_r: Portrait | None = None
    art_dir = data_dir / "art"
    bg_key = f"bg:{scene.background_id}"
    if bg_key not in _gn_cache:
        try:
            _gn_cache[bg_key] = load_background(art_dir, scene.background_id)
        except (KeyError, FileNotFoundError):
            _gn_cache[bg_key] = None
    bg_val = _gn_cache[bg_key]
    if isinstance(bg_val, Background):
        bg = bg_val
    for p_id, slot in (
        (scene.portrait_left, "p_l"),
        (scene.portrait_right, "p_r"),
    ):
        if p_id:
            pkey = f"portrait:{p_id}"
            if pkey not in _gn_cache:
                try:
                    _gn_cache[pkey] = load_portrait(art_dir, p_id)
                except (KeyError, FileNotFoundError):
                    _gn_cache[pkey] = None
            val = _gn_cache[pkey]
            if isinstance(val, Portrait):
                if slot == "p_l":
                    p_l = val
                else:
                    p_r = val

    render_scene(
        console,
        scene,
        dialogue,
        bg,
        p_l,
        p_r,
        t,
        typed,
        state.gn_scene_index,
        len(chain),
        paused=state.gn_paused,
    )

    # Auto-advance: 100ms per frame * 10 (demo speed)
    state.gn_elapsed_ms += 100 * 10
    if state.gn_elapsed_ms >= dialogue.duration_ms:
        state.gn_dialogue_index += 1
        state.gn_elapsed_ms = 0.0
        if state.gn_dialogue_index >= len(scene.dialogue):
            state.gn_scene_index += 1
            state.gn_dialogue_index = 0
            if state.gn_scene_index >= len(chain):
                state.screen = ScreenKind.SAVED_PROGRESS


def _action_menu(state: AppState) -> str:
    """MENU → CHARACTER_SELECT: select New Run (key '1')."""
    if state.screen is ScreenKind.MENU:
        state.screen = ScreenKind.CHARACTER_SELECT
        return "Auto: New Run → Character Select"
    return ""


def _action_graphic_novel_menu(state: AppState, mode: str) -> str:
    """GRAPHIC_NOVEL_MENU → GRAPHIC_NOVEL: start the chosen mode.

    Args:
        state: App state.
        mode: "prologue" | "novice" | "veteran" | "heretic" | "back"

    ADR-0048: For character modes (N2-N4), transition to
    GRAPHIC_NOVEL_ENDING_MENU first; PROLOGUE skips and uses ending A.
    """
    if state.screen is ScreenKind.GRAPHIC_NOVEL_MENU:
        if mode == "back":
            state.screen = ScreenKind.MENU
            return "Auto: Graphic Novel menu → back to main menu"
        if mode in ("novice", "veteran", "heretic"):
            state.gn_mode = mode
            state.gn_ending_choice = "A"
            state.screen = ScreenKind.GRAPHIC_NOVEL_ENDING_MENU
            return f"Auto: Graphic Novel → choose ending for {mode}"
        # prologue — skip ending selection, use A
        state.gn_mode = mode
        state.gn_ending_choice = "A"
        state.gn_scene_index = 0
        state.gn_dialogue_index = 0
        state.gn_elapsed_ms = 0.0
        state.gn_paused = False
        state.screen = ScreenKind.GRAPHIC_NOVEL
        return f"Auto: Graphic Novel [{mode}] → playing"
    return ""


def _action_graphic_novel_ending_menu(state: AppState, ending: str) -> str:
    """GRAPHIC_NOVEL_ENDING_MENU → GRAPHIC_NOVEL: start with chosen ending.

    Args:
        state: App state.
        ending: "A" | "B" | "C" | "back"

    ADR-0048: finalize gn_ending_choice and start playback.
    ADR-0049: ending="C" supported (vanishing / erase / unmaking).
    """
    if state.screen is ScreenKind.GRAPHIC_NOVEL_ENDING_MENU:
        if ending == "back":
            state.screen = ScreenKind.GRAPHIC_NOVEL_MENU
            return "Auto: Ending menu → back to GN menu"
        if ending not in ("A", "B", "C"):
            return ""
        state.gn_ending_choice = ending
        state.gn_scene_index = 0
        state.gn_dialogue_index = 0
        state.gn_elapsed_ms = 0.0
        state.gn_paused = False
        state.screen = ScreenKind.GRAPHIC_NOVEL
        return f"Auto: Graphic Novel [{state.gn_mode} ending {ending}] → playing"
    return ""


def _action_saved_progress(state: AppState, choice: str) -> str:
    """SAVED_PROGRESS → next screen.

    Args:
        state: App state.
        choice: "other_chars" | "continue" | "menu"
    """
    if state.screen is ScreenKind.SAVED_PROGRESS:
        if choice == "other_chars":
            state.screen = ScreenKind.GRAPHIC_NOVEL_MENU
            return "Auto: Other character stories"
        if choice == "continue":
            gn_to_character = {
                "novice": "novice",
                "veteran": "veteran",
                "heretic": "heretic",
                "prologue": state.character_id or "novice",
            }
            character = gn_to_character.get(state.gn_mode, state.character_id or "novice")
            state.character_id = character
            state.chapter_id = f"chapter_{character}"
            state.chapter_elapsed_ms = 0.0
            state.chapter_typed_chars = 0
            run_state = ensure_run_state(state)
            run_state.chapter_state = ChapterState.PROLOGUE
            state.screen = ScreenKind.CHAPTER
            return f"Auto: Continue → Chapter ({character})"
        # menu
        state.screen = ScreenKind.MENU
        return "Auto: Back to main menu"
    return ""


def _action_character_select(state: AppState, character: str) -> str:
    """CHARACTER_SELECT → CHAPTER: pick the requested character."""
    if state.screen is ScreenKind.CHARACTER_SELECT:
        state.character_id = character
        state.chapter_id = f"chapter_{character}"
        state.chapter_elapsed_ms = 0.0
        state.chapter_typed_chars = 0
        run_state = ensure_run_state(state)
        run_state.chapter_state = ChapterState.PROLOGUE
        state.screen = ScreenKind.CHAPTER
        return f"Auto: selected {character} → Chapter (Prologue)"
    return ""


def _get_salvation_runner(state: AppState) -> SalvationRunner:
    """Get or create the SalvationRunner on the app state.

    Lazily initializes on first access; persists for the run.
    """
    runner = getattr(state, "salvation_runner", None)
    if runner is None:
        runner = SalvationRunner()
        state.salvation_runner = runner
    return runner


def _action_salvation_intro(state: AppState, choice: str) -> str:
    """SALVATION_INTRO: select an epilogue character (1-9) or go to menu.

    Args:
        state: App state.
        choice: "1"-"9" (character index) | "back" (return to MENU)

    Phase 9-B: triggers SalvationRunner.choose_epilogue() and transitions
    to SALVATION_EPILOGUE state on the AppState.
    """
    if state.screen is ScreenKind.SALVATION_INTRO:
        if choice == "back":
            state.screen = ScreenKind.MENU
            return "Auto: Salvation intro → Main Menu"
        if not choice.isdigit() or not (1 <= int(choice) <= 9):
            return ""
        # Map 1-9 → character_id
        choices = list(
            __import__(
                "wet_run.engine.salvation", fromlist=["list_available_epilogues"]
            ).list_available_epilogues()
        )
        if int(choice) > len(choices):
            return ""
        char_id = choices[int(choice) - 1][0]
        runner = _get_salvation_runner(state)
        runner.choose_epilogue(char_id)
        state.salvation_runner = runner
        state.screen = ScreenKind.SALVATION_EPILOGUE
        return f"Auto: selected epilogue [{choice}] {char_id} → playing"
    return ""


def _action_salvation_epilogue(state: AppState) -> str:
    """SALVATION_EPILOGUE: advance epilogue playback (auto-completed).

    Phase 9-B: when epilogue is shown (here: instant for demo),
    transition to SALVATION_ENDING for the final ending choice.
    """
    if state.screen is ScreenKind.SALVATION_EPILOGUE:
        runner = _get_salvation_runner(state)
        if runner.state == "salvation_intro":
            return ""
        runner.complete_epilogue()
        state.screen = ScreenKind.SALVATION_ENDING
        return f"Auto: epilogue complete → ending menu ({runner.selection.ending if runner.selection else '?'})"
    return ""


def _action_salvation_ending(state: AppState, choice: str) -> str:
    """SALVATION_ENDING: select final ending A/B/C, transition to ENDING screen.

    Args:
        state: App state.
        choice: "A" | "B" | "C" | "back"
    """
    if state.screen is ScreenKind.SALVATION_ENDING:
        if choice == "back":
            state.screen = ScreenKind.SALVATION_INTRO
            return "Auto: ending menu → back to epilogue menu"
        if choice not in ("A", "B", "C"):
            return ""
        runner = _get_salvation_runner(state)
        runner.choose_ending(choice)
        # Map SalvationRunner ending → existing ENDING_* ChapterState
        if runner.selection is None:
            return ""
        ending_lower = runner.selection.ending.lower()
        state.run_state.chapter_state = ChapterState(f"ending_{ending_lower}")
        state.screen = ScreenKind.ENDING
        state.ending_elapsed_ms = 0.0
        return f"Auto: Salvation complete → Ending {choice} screen"
    return ""


def _action_chapter(state: AppState) -> str:
    """CHAPTER → ARC_PHASE: complete chapter intro, begin story phases."""
    if state.screen is ScreenKind.CHAPTER:
        if state.run_state is not None:
            state.run_state.chapter_state = ChapterState.IN_CHAPTER_1
            state.run_state.current_stage = Stage.PENDING

        character = state.character_id or "novice"
        arc = get_arc_for_character(Path(__file__).parent.parent / "data", character)
        state.current_arc = arc
        state.current_chapter_index = 0
        state.current_phase_index = 0
        state.current_beat_index = 0
        state.phase_typed_chars = 0
        state.phase_elapsed_ms = 0.0
        state.screen = ScreenKind.ARC_PHASE
        return f"Auto: {character} chapter 1 → ARC_PHASE"
    return ""


def _resolve_arc_combat(state: AppState, combat_data: CombatData) -> str:
    """ARC_PHASE: auto-resolve combat story beat as victory (story-mode demo)."""
    if not hasattr(state, "inventory") or state.inventory is None:
        state.inventory = {}
    state.inventory["ice_shard"] = state.inventory.get("ice_shard", 0) + 1
    state.credits = getattr(state, "credits", 0) + 50
    state.status_messages.append(f">>> VICTORY! {combat_data.enemy_type} → 1x ICE Shard + 50cr")

    enemy_name = combat_data.enemy_type.replace("_", " ").title()
    return f"[COMBAT] {enemy_name} defeated → ICE Shard + 50cr"


def _start_chapter_cutscene(state: AppState, scene_id: str, scenes_dir: Path) -> bool:
    """Load a GN scene as a chapter cutscene. Returns True on success."""
    try:
        from wet_run.engine.chapter_cutscene import ChapterCutsceneState, load_scene

        scene = load_scene(scenes_dir, scene_id)
        state.chapter_cutscene_state = ChapterCutsceneState(scene=scene)
        return True
    except Exception:
        return False


def _get_current_chapter(chapter_state: ChapterState | None) -> int:
    """Return chapter number (1-5) for a ChapterState, or 1 if unknown."""
    if chapter_state is None:
        return 1
    mapping = {
        ChapterState.PROLOGUE: 0,
        ChapterState.IN_CHAPTER_1: 1,
        ChapterState.CHAPTER_1_COMPLETE: 1,
        ChapterState.IN_CHAPTER_2: 2,
        ChapterState.CHAPTER_2_COMPLETE: 2,
        ChapterState.IN_CHAPTER_3: 3,
        ChapterState.CHAPTER_3_COMPLETE: 3,
        ChapterState.IN_CHAPTER_4: 4,
        ChapterState.CHAPTER_4_COMPLETE: 4,
        ChapterState.IN_CHAPTER_5: 5,
        ChapterState.CHAPTER_5_COMPLETE: 5,
        ChapterState.ENDING_A: 5,
        ChapterState.ENDING_B: 5,
        ChapterState.ENDING_C: 5,
    }
    return mapping.get(chapter_state, 1)


def _action_hub(state: AppState) -> str:
    """HUB → MATRIX: select first mission (or show cutscene_start first)."""
    if state.screen is not ScreenKind.HUB or not state.job_board:
        return ""

    # If cutscene is in progress and not done, wait
    if state.chapter_cutscene_state is not None and not state.chapter_cutscene_state.done:
        return "Auto: waiting for cutscene..."

    # If cutscene is done, clear it and proceed
    if state.chapter_cutscene_state is not None and state.chapter_cutscene_state.done:
        state.chapter_cutscene_state = None

    scenes_dir = Path(__file__).parent.parent / "data" / "scenes"
    rs = state.run_state

    chapter_cutscenes_seen: set[int] = getattr(state, "chapter_cutscenes_seen", set())

    # Auto-advance: play cutscene_end (COMPLETED chapter) then transition to next
    if rs is not None and rs.chapter_state in (
        ChapterState.CHAPTER_1_COMPLETE,
        ChapterState.CHAPTER_2_COMPLETE,
        ChapterState.CHAPTER_3_COMPLETE,
        ChapterState.CHAPTER_4_COMPLETE,
    ):
        completed_chapter_num = _get_current_chapter(rs.chapter_state)
        arc = get_arc_for_character(scenes_dir.parent, state.character_id)
        prev_chapter = get_chapter(arc, completed_chapter_num)
        if prev_chapter and prev_chapter.cutscene_end and 2 not in chapter_cutscenes_seen:
            scene_id = prev_chapter.cutscene_end.scene_id
            if _start_chapter_cutscene(state, scene_id, scenes_dir):
                state.chapter_cutscenes_seen = chapter_cutscenes_seen | {2}
                title = prev_chapter.cutscene_end.title_en
                return f"Auto: cutscene_end ({title})"
        if rs.chapter_state is ChapterState.CHAPTER_1_COMPLETE:
            rs.start_chapter_2()
            state.chapter_cutscenes_seen = set()
            return "Auto: Chapter 2 starts..."
        elif rs.chapter_state is ChapterState.CHAPTER_2_COMPLETE:
            rs.start_chapter_3()
            state.chapter_cutscenes_seen = set()
            return "Auto: Chapter 3 starts..."
        elif rs.chapter_state is ChapterState.CHAPTER_3_COMPLETE:
            rs.start_chapter_4()
            state.chapter_cutscenes_seen = set()
            return "Auto: Chapter 4 starts..."
        elif rs.chapter_state is ChapterState.CHAPTER_4_COMPLETE:
            rs.start_chapter_5()
            state.chapter_cutscenes_seen = set()
            return "Auto: Chapter 5 starts..."

    # Handle Chapter 5 complete → ENDING
    if rs is not None and rs.chapter_state is ChapterState.CHAPTER_5_COMPLETE:
        arc = get_arc_for_character(scenes_dir.parent, state.character_id)
        ch5 = get_chapter(arc, 5)
        if ch5 and ch5.cutscene_end and 2 not in chapter_cutscenes_seen:
            scene_id = ch5.cutscene_end.scene_id
            if _start_chapter_cutscene(state, scene_id, scenes_dir):
                state.chapter_cutscenes_seen = chapter_cutscenes_seen | {2}
                title = ch5.cutscene_end.title_en
                return f"Auto: cutscene_end ({title})"
        # Phase 9-B: trigger Salvation Phase before final ending
        # (only once — guarded by epilogue_played flag)
        if not getattr(state, "salvation_done", False):
            runner = _get_salvation_runner(state)
            # Set up a sensible default epilogue (matches character) for convenience
            char = state.character_id or "novice"
            if (
                char
                in __import__(
                    "wet_run.engine.salvation", fromlist=["SALVATION_EPILOGUES"]
                ).SALVATION_EPILOGUES
            ):
                runner.choose_epilogue(char)
                state.salvation_runner = runner
            state.salvation_done = True  # mark done to avoid re-entry
            state.screen = ScreenKind.SALVATION_INTRO
            return f"Auto: Chapter 5 complete → Salvation intro ({char})"
        ending_type = (ch5.ending_type if ch5 else "A").upper()
        rs.chapter_state = ChapterState(f"ending_{ending_type.lower()}")
        state.screen = ScreenKind.ENDING
        return f"Auto: Arc complete! ({arc.title_en} — Ending {ending_type})"

    chapter_num = _get_current_chapter(rs.chapter_state if rs else None)
    arc = get_arc_for_character(scenes_dir.parent, state.character_id)
    chapter = get_chapter(arc, chapter_num)

    # Show cutscene_start
    if 0 not in chapter_cutscenes_seen:
        if chapter and chapter.cutscene_start:
            scene_id = chapter.cutscene_start.scene_id
            if _start_chapter_cutscene(state, scene_id, scenes_dir):
                state.chapter_cutscenes_seen = chapter_cutscenes_seen | {0}
                title = chapter.cutscene_start.title_en
                return f"Auto: cutscene_start ({title})"

    # For non-playable chapters: show cutscene_end, then auto-complete
    if chapter and not chapter.is_playable:
        if 2 not in chapter_cutscenes_seen and chapter.cutscene_end:
            scene_id = chapter.cutscene_end.scene_id
            if _start_chapter_cutscene(state, scene_id, scenes_dir):
                state.chapter_cutscenes_seen = chapter_cutscenes_seen | {2}
                title = chapter.cutscene_end.title_en
                return f"Auto: cutscene_end ({title})"
        # Auto-complete non-playable chapter
        if rs:
            if rs.chapter_state is ChapterState.IN_CHAPTER_2:
                rs.complete_chapter_2()
            elif rs.chapter_state is ChapterState.IN_CHAPTER_3:
                rs.complete_chapter_3()
            elif rs.chapter_state is ChapterState.IN_CHAPTER_4:
                rs.complete_chapter_4()
            elif rs.chapter_state is ChapterState.IN_CHAPTER_5:
                rs.complete_chapter_5()
        return "Auto: Non-playable chapter complete..."

    missions = list(state.job_board.available_for(state.player_grade))
    if not missions:
        return "No missions for this grade."
    m = missions[0]
    state.current_mission = m
    state.matrix = MatrixGenerator().generate(seed=m.matrix_seed, mission_grade=state.player_grade)
    state.current_node_id = state.matrix.entry_id
    state.exploration = ExplorationState(current=state.matrix.entry_id)
    state.screen = ScreenKind.MATRIX
    return f"Auto: select '{m.title}' → Matrix"


def _action_matrix(state: AppState) -> str:
    """MATRIX: navigate to next unvisited neighbor, or jack out when done."""
    if state.screen is ScreenKind.MATRIX and state.matrix is not None:
        # If cutscene is in progress and not done, wait
        if state.chapter_cutscene_state is not None and not state.chapter_cutscene_state.done:
            return "Auto: waiting for cutscene_mid..."

        # If cutscene_mid is done, clear it and proceed
        if state.chapter_cutscene_state is not None and state.chapter_cutscene_state.done:
            state.chapter_cutscene_state = None

        # Check if cutscene_mid should be shown (after first node visit)
        scenes_dir = Path(__file__).parent.parent / "data" / "scenes"
        chapter_cutscenes_seen: set[int] = getattr(state, "chapter_cutscenes_seen", set())

        if 1 not in chapter_cutscenes_seen:
            arc = get_arc_for_character(scenes_dir.parent, state.character_id)
            chapter_num = _get_current_chapter(
                state.run_state.chapter_state if state.run_state else None
            )
            chapter = get_chapter(arc, chapter_num)
            if chapter and chapter.cutscene_mid and chapter.is_playable:
                scene_id = chapter.cutscene_mid.scene_id
                if _start_chapter_cutscene(state, scene_id, scenes_dir):
                    state.chapter_cutscenes_seen = chapter_cutscenes_seen | {1}
                    title = chapter.cutscene_mid.title_en
                    return f"Auto: cutscene_mid ({title})"

        nbrs = state.matrix.neighbors(state.current_node_id or "")
        unvisited = [
            n
            for n in nbrs
            if n.id not in (state.exploration.discovered if state.exploration else set())
        ]
        if unvisited:
            target = unvisited[0]
            state.current_node_id = target.id
            if state.exploration is not None:
                state.exploration.visit(target.id)
            ppl = calculate_ppl(state.player_loadout)
            zdr = node_zdr(target)
            st = node_status(target, ppl)
            return f"Auto: → {target.kind.value} (ZDR {zdr}, {st.value.upper()})"
        # All neighbors visited → jack out
        state.matrix = None
        state.current_node_id = None
        state.exploration = None
        state.current_mission = None
        # Mark current chapter complete and advance
        rs = state.run_state
        if rs is not None:
            chapter_names = {
                ChapterState.IN_CHAPTER_1: "Chapter 1",
                ChapterState.IN_CHAPTER_2: "Chapter 2",
                ChapterState.IN_CHAPTER_3: "Chapter 3",
                ChapterState.IN_CHAPTER_4: "Chapter 4",
                ChapterState.IN_CHAPTER_5: "Chapter 5",
            }
            chapter_name = chapter_names.get(rs.chapter_state, "Chapter")
            if rs.chapter_state is ChapterState.IN_CHAPTER_1:
                rs.complete_chapter_1()
            elif rs.chapter_state is ChapterState.IN_CHAPTER_2:
                rs.complete_chapter_2()
            elif rs.chapter_state is ChapterState.IN_CHAPTER_3:
                rs.complete_chapter_3()
            elif rs.chapter_state is ChapterState.IN_CHAPTER_4:
                rs.complete_chapter_4()
            elif rs.chapter_state is ChapterState.IN_CHAPTER_5:
                rs.complete_chapter_5()
        else:
            chapter_name = "Unknown"
        state.screen = ScreenKind.HUB
        return f"Auto: Jack out → Hub ({chapter_name} Complete!)"
    return ""


def _run_phase_1_5_smoke() -> int:
    """Run all five Phase 1-5 headless demos as a smoke test.

    Each demo is invoked as a subprocess with the same Python
    interpreter, src on PYTHONPATH, and exits 0 on success.  The
    intended use is a CI-friendly smoke test that confirms the
    operator-point demos (added alongside ADR-0060 / 0061) still
    pass after a refactor.
    """
    import subprocess

    scripts = [
        "play_dungeon_mode.py",
        "play_vfx_overlay.py",
        "play_mission_mapping.py",
        "play_ecs_dungeon.py",
        "play_novel_runtime.py",
        "play_arc_bsp.py",
    ]
    proto = Path(__file__).resolve().parent
    env = {**__import__("os").environ, "PYTHONPATH": str(proto.parent / "src")}
    rc = 0
    print("=" * 64)
    print("Phase 1-5 headless smoke test (ADR-0060 / ADR-0061)")
    print("=" * 64)
    for s in scripts:
        cmd = [sys.executable, str(proto / s)]
        print(f"\n--- {s} ---")
        try:
            res = subprocess.run(cmd, env=env, check=False, capture_output=True, text=True)
        except FileNotFoundError as exc:
            print(f"  ERR: {exc}")
            rc = 1
            continue
        # Surface only the final summary line to keep output short.
        out_lines = res.stdout.splitlines()
        tail = out_lines[-1] if out_lines else ""
        print(tail)
        if res.returncode != 0:
            print(f"  rc={res.returncode}; stderr tail:")
            for line in res.stderr.splitlines()[-3:]:
                print(f"    {line}")
            rc = res.returncode
    print()
    print("=" * 64)
    print(f"phase-1-5 smoke {'PASS' if rc == 0 else 'FAIL'} (rc={rc})")
    print("=" * 64)
    return rc


def _run_bsp_mission(mission_id: str, *, seed: int = 2026, grade: int = 2) -> int:
    """Run a single BSP dungeon for the named mission via play_arc_bsp.py.

    Falls back to --mission <id> in the demo script; surfaces its
    full output verbatim.  Returns its exit code.
    """
    import subprocess

    proto = Path(__file__).resolve().parent
    cmd = [
        sys.executable,
        str(proto / "play_arc_bsp.py"),
        "--mission",
        mission_id,
        "--seed",
        str(seed),
        "--grade",
        str(grade),
    ]
    env = {**__import__("os").environ, "PYTHONPATH": str(proto.parent / "src")}
    print("=" * 64)
    print(f"play.py --bsp-mission {mission_id} (seed={seed}, grade={grade})")
    print("=" * 64)
    res = subprocess.run(cmd, env=env, check=False)
    return res.returncode


def _list_missions() -> int:
    """Print every mission id available via data/missions/missions.json.

    Imported lazily so the GUI playthrough is unaffected when the
    --list-missions flag is absent.
    """
    from wet_run.missions import JobBoard

    p = Path(__file__).resolve().parents[1] / "data" / "missions" / "missions.json"
    board = JobBoard.load(p)
    ids = sorted(board._missions.keys())
    print(f"Available missions ({len(ids)}):")
    for mid in ids:
        print(f"  {mid}")
    return 0


def _run_arc_bsp_all() -> int:
    """Walk all three character arcs via play_arc_bsp.py.

    Spawns play_arc_bsp.py once per arc ('novice' / 'veteran' /
    'heretic') and surfaces one tail-summary line per arc.
    Returns 0 only if every arc finished cleanly.
    """
    import subprocess

    proto = Path(__file__).resolve().parent
    env = {**__import__("os").environ, "PYTHONPATH": str(proto.parent / "src")}
    arcs = ("novice", "veteran", "heretic")
    rc = 0
    print("=" * 64)
    print(f"play.py --arc-bsp ({len(arcs)} arcs)")
    print("=" * 64)
    for arc in arcs:
        cmd = [sys.executable, str(proto / "play_arc_bsp.py"), "--arc", arc, "--missions", "3"]
        res = subprocess.run(cmd, env=env, check=False, capture_output=True, text=True)
        tail = res.stdout.splitlines()[-1] if res.stdout else ""
        print(f"--- {arc:8s} rc={res.returncode} ---")
        print(f"  {tail}")
        if res.returncode != 0:
            rc = res.returncode
    print()
    print("=" * 64)
    print(f"arc-bsp smoke {'PASS' if rc == 0 else 'FAIL'} (rc={rc})")
    print("=" * 64)
    return rc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--step-delay", type=float, default=0.4)
    parser.add_argument("--no-clear", action="store_true")
    parser.add_argument("--lang", default="en", choices=["en", "ko"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mission", type=int, default=1)
    parser.add_argument(
        "--character",
        default="novice",
        choices=["novice", "veteran", "heretic"],
        help="Auto-selected character (default novice)",
    )
    parser.add_argument(
        "--ending",
        default=None,
        choices=["A", "B", "C"],
        help="Auto-pick ending when entering GRAPHIC_NOVEL_ENDING_MENU (default: A, ADR-0049)",
    )
    parser.add_argument(
        "--gn-mode",
        default=None,
        choices=["prologue", "novice", "veteran", "heretic"],
        help=("If set, play graphic novel mode after MENU. Otherwise defaults to NEW RUN flow."),
    )
    parser.add_argument(
        "--phase-1-5",
        action="store_true",
        help=("Run all five Phase 1-5 headless demos and exit.  Bypasses the GUI playthrough."),
    )
    parser.add_argument(
        "--bsp-mission",
        default=None,
        help=(
            "Run the BSP dungeon for a single mission via "
            "play_arc_bsp.py --mission <id>.  Bypasses the GUI "
            "playthrough."
        ),
    )
    parser.add_argument(
        "--bsp-seed",
        type=int,
        default=2026,
        help="RNG seed forwarded to play_arc_bsp.py (default 2026).",
    )
    parser.add_argument(
        "--bsp-grade",
        type=int,
        default=2,
        help="Mission grade 1-5 (default 2).",
    )
    parser.add_argument(
        "--arc-bsp",
        action="store_true",
        help=(
            "Walk all three character arcs (novice / veteran / "
            "heretic) through the BSP integration pipeline and "
            "print one summary line per arc.  Useful as a "
            "regression check whenever ProceduralDungeonGenerator "
            "or mission_to_graph is touched."
        ),
    )
    parser.add_argument(
        "--list-missions",
        action="store_true",
        help=(
            "Print all available mission ids from data/missions/"
            "missions.json, one per line.  Useful as a target-list "
            "for --bsp-mission <id>."
        ),
    )
    parser.add_argument("--show-controls", action="store_true")
    args = parser.parse_args()

    # Phase 1-5 smoke test mode: run each headless demo as a subprocess.
    if args.phase_1_5:
        return _run_phase_1_5_smoke()

    # Single-mission BSP mode: hand off to play_arc_bsp.py.
    if args.bsp_mission is not None:
        return _run_bsp_mission(args.bsp_mission, seed=args.bsp_seed, grade=args.bsp_grade)

    # List-missions mode: print ids and exit before any GUI setup.
    if args.list_missions:
        return _list_missions()

    # All-arcs BSP walk: run play_arc_bsp.py once per character arc
    # and surface a one-line summary per arc.
    if args.arc_bsp:
        return _run_arc_bsp_all()

    state, t, story_reg = _setup(args)
    # Apply character selection to state so CHARACTER_SELECT → CHAPTER
    # transitions pick the requested character.
    state.character_id = args.character
    # If --gn-mode is set, jump straight to GRAPHIC_NOVEL_MENU
    if args.gn_mode is not None:
        state.gn_mode = args.gn_mode
        state.screen = ScreenKind.GRAPHIC_NOVEL_MENU
    console = tcod.console.Console(80, 50, order="F")

    if args.show_controls:
        sys.stdout.write(
            "=== Quick Demo ===\n"
            "Commands: q = quit early, Enter = next frame.\n"
            f"Duration: {args.duration:.0f}s, step-delay: {args.step_delay}s, lang: {args.lang}\n\n"
        )
        sys.stdout.flush()

    start = time.monotonic()
    step = 0
    narration = "(initial)"

    _render_current(console, state, t, story_reg, 0.0)
    _print_frame(
        console,
        clear=not args.no_clear,
        step=step,
        elapsed=0.0,
        narration=narration,
    )
    step += 1
    time.sleep(args.step_delay)

    while time.monotonic() - start < args.duration:
        elapsed = time.monotonic() - start

        # Decide next action based on current screen
        # Every 4th step, act (instead of every other)
        if step % 4 == 0:
            if state.screen is ScreenKind.MENU:
                if step > 1:
                    # Pick flow based on --gn-mode argument
                    if args.gn_mode is not None:
                        narration = _action_graphic_novel_menu(state, args.gn_mode)
                    else:
                        narration = _action_menu(state)
                    # After action, transition: demo the Story screen briefly
                    next_screen: ScreenKind = state.screen
                    if next_screen is ScreenKind.HUB and state.current_mission is not None:
                        # Demo Story after first mission
                        state.screen = ScreenKind.STORY
            elif state.screen is ScreenKind.GRAPHIC_NOVEL_MENU:
                # Auto-pick the requested mode (already in state.gn_mode from --gn-mode)
                narration = _action_graphic_novel_menu(state, state.gn_mode)
            elif state.screen is ScreenKind.GRAPHIC_NOVEL_ENDING_MENU:
                # ADR-0048: pick ending B/C if requested via --ending CLI
                target_ending = getattr(args, "ending", "A") or "A"
                narration = _action_graphic_novel_ending_menu(state, target_ending)
            elif state.screen is ScreenKind.SALVATION_INTRO:
                # Auto-pick first option or go back based on arg
                pick = getattr(args, "salvation_pick", "1")
                narration = _action_salvation_intro(state, pick)
            elif state.screen is ScreenKind.SALVATION_EPILOGUE:
                # Auto-complete epilogue immediately (demo)
                narration = _action_salvation_epilogue(state)
            elif state.screen is ScreenKind.SALVATION_ENDING:
                ending = getattr(args, "salvation_ending", "A")
                narration = _action_salvation_ending(state, ending)
            elif state.screen is ScreenKind.SAVED_PROGRESS:
                narration = _action_saved_progress(state, "menu")
            elif state.screen is ScreenKind.CHARACTER_SELECT:
                narration = _action_character_select(state, args.character)
            elif state.screen is ScreenKind.CHAPTER:
                # Auto-skip chapter after 2 seconds of display
                if state.chapter_elapsed_ms > 2000:
                    narration = _action_chapter(state)
            elif state.screen is ScreenKind.ARC_PHASE:
                # Auto-advance to next phase after 3 seconds per beat
                if state.phase_elapsed_ms > 3000 and state.phase_typed_chars > 0:
                    if state.current_arc is not None:
                        chapter = state.current_arc.chapters[state.current_chapter_index]
                        phase = chapter.phases[state.current_phase_index]
                        current_beat = phase.beats[state.current_beat_index]
                        if current_beat.type == "combat" and phase.combat is not None:
                            _resolve_arc_combat(state, phase.combat)
                            # Advance to next beat after auto-resolve
                            if state.current_beat_index < len(phase.beats) - 1:
                                state.current_beat_index += 1
                                state.phase_typed_chars = 0
                                state.phase_elapsed_ms = 0.0
                            elif state.current_phase_index < len(chapter.phases) - 1:
                                state.current_phase_index += 1
                                state.current_beat_index = 0
                                state.phase_typed_chars = 0
                                state.phase_elapsed_ms = 0.0
                            else:
                                state.screen = ScreenKind.HUB
                                narration = "Chapter complete: → HUB"
                        elif state.current_beat_index < len(phase.beats) - 1:
                            state.current_beat_index += 1
                            state.phase_typed_chars = 0
                            state.phase_elapsed_ms = 0.0
                        elif state.current_phase_index < len(chapter.phases) - 1:
                            state.current_phase_index += 1
                            state.current_beat_index = 0
                            state.phase_typed_chars = 0
                            state.phase_elapsed_ms = 0.0
                        else:
                            state.screen = ScreenKind.HUB
                            narration = "Chapter complete: → HUB"
            elif state.screen is ScreenKind.HUB:
                if step > 1:
                    narration = _action_hub(state)
            elif state.screen is ScreenKind.MATRIX:
                if step > 2:
                    narration = _action_matrix(state)
            elif state.screen is ScreenKind.HACK:
                hack_state = getattr(state, "hack_state", None)
                if hack_state is not None and hack_state.outcome is not None:
                    if not hasattr(state, "_hack_result_shown_at"):
                        state._hack_result_shown_at = elapsed
                    elif elapsed - state._hack_result_shown_at > 2.0:
                        from wet_run.engine import hacking_view

                        state.screen = ScreenKind.MATRIX
                        hacking_view._clear_hack_state(state)
                        if hasattr(state, "_hack_result_shown_at"):
                            delattr(state, "_hack_result_shown_at")
                        narration = "Auto: HACK complete → Matrix"
                else:
                    if not hasattr(state, "_hack_started_at"):
                        state._hack_started_at = elapsed
                    elif elapsed - state._hack_started_at > 1.0:
                        from wet_run.engine import hacking_view

                        hacking_view._execute_probe(hack_state)
                        hacking_view._apply_hack_reward(state, hack_state.outcome)
                        state._hack_result_shown_at = elapsed
                        narration = f"Auto: HACK → {hack_state.outcome}"
            elif state.screen is ScreenKind.STORY:
                # Auto-leave Story to Hub
                if state.current_mission is not None:
                    state.screen = ScreenKind.HUB
                    state.current_mission = None
                else:
                    state.screen = ScreenKind.MENU
                narration = "Auto: → next screen"
            elif state.screen is ScreenKind.ENDING:
                # Auto-return to MENU after 5 seconds on ENDING screen
                if state.ending_elapsed_ms > 5000:
                    state.screen = ScreenKind.MENU
                    state.ending_elapsed_ms = 0.0
                    narration = "Auto: Ending → Main Menu"

        _render_current(console, state, t, story_reg, elapsed)
        _print_frame(
            console,
            clear=not args.no_clear,
            step=step,
            elapsed=elapsed,
            narration=narration,
        )
        step += 1
        time.sleep(args.step_delay)

    sys.stdout.write(f"\n=== Demo complete: {step} steps in {args.duration:.0f}s ===\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.stdout.write("\n[interrupted]\n")
        sys.exit(130)
