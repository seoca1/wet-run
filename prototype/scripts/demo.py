"""Auto-progressing headless demo (ADR-0005, ADR-0031).

Runs the game state machine without a tcod window, rendering each
frame to plain text on stdout. The state advances automatically:
Menu -> Character Select -> Chapter -> Hub -> Matrix (navigate) -> Jack out -> Hub -> ...

Usage:
    python scripts/demo.py                  # 120s demo, 1.0s per step
    python scripts/demo.py --duration 30   # 30s demo
    python scripts/demo.py --step-delay 0.5
    python scripts/demo.py --no-clear      # don't clear the screen between frames
    python scripts/demo.py --lang ko       # Korean translation
    python scripts/demo.py --character X   # novice | veteran | heretic

Frames are dumped to stdout. With --no-clear, every frame is appended
so the terminal scrolls through the whole playthrough.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import tcod.console

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine import hub, matrix_view, menu
from wet_run.engine.chapter_cutscene import get_arc_for_character
from wet_run.engine.chapter_view import chapter_for_character, tick_chapter
from wet_run.engine.graphic_novel_view import (
    Background,
    Portrait,
    SceneData,
)
from wet_run.engine.state import AppState, ScreenKind
from wet_run.i18n import Translator
from wet_run.matrix import MatrixGenerator
from wet_run.matrix.ppl import calculate_ppl
from wet_run.matrix.zdr import node_status, node_zdr
from wet_run.missions import JobBoard, Mission

# Graphic novel art cache
_demo_gn_cache: dict[str, Background | Portrait | list[SceneData] | None] = {}


def render_to_text(console: tcod.console.Console) -> str:
    """Convert a tcod console buffer to plain text (one char per cell)."""
    lines: list[str] = []
    for y in range(console.height):
        chars: list[str] = []
        for x in range(console.width):
            code = int(console.ch[x, y])
            if 0 < code < 0x110000:
                chars.append(chr(code))
            else:
                chars.append(" ")
        lines.append("".join(chars).rstrip())
    return "\n".join(lines)


def render_frame(
    console: tcod.console.Console,
    state: AppState,
    t: Translator,
    data_dir: Path | None = None,
) -> None:
    """Render the current screen onto ``console`` (in place)."""
    if state.screen is ScreenKind.MENU:
        menu.render_menu(console, t, state)
    elif state.screen is ScreenKind.GRAPHIC_NOVEL_MENU:
        from wet_run.engine import graphic_novel_view

        graphic_novel_view.render_graphic_novel_menu(console, t, selected_index=0, has_save=False)
    elif state.screen is ScreenKind.GRAPHIC_NOVEL_ENDING_MENU:
        from wet_run.engine import graphic_novel_view

        graphic_novel_view.render_graphic_novel_ending_menu(
            console, t, character=state.gn_mode, selected_index=0
        )
    elif state.screen is ScreenKind.GRAPHIC_NOVEL and data_dir is not None:
        # Inline graphic novel frame renderer (mirrors play.py).
        from wet_run.engine.graphic_novel_view import (
            dialogue_typed_chars,
            load_background,
            load_portrait,
            load_prologue_chain,
            load_scene_chain,
            render_scene,
        )

        cache_key = f"chain:{state.gn_mode}:{state.gn_ending_choice}"
        cached = _demo_gn_cache.get(cache_key)
        if not isinstance(cached, list):
            ending = state.gn_ending_choice or "A"
            if state.gn_mode == "prologue":
                chain_data = load_prologue_chain(data_dir / "scenes", seed=42, ending=ending)
            else:
                chain_data = load_scene_chain(data_dir / "scenes", state.gn_mode, ending=ending)
            _demo_gn_cache[cache_key] = list(chain_data)
        chain: list[SceneData] = list(_demo_gn_cache[cache_key])  # type: ignore[arg-type]
        if state.gn_scene_index >= len(chain):
            state.screen = ScreenKind.SAVED_PROGRESS
            console.clear()
        else:
            scene = chain[state.gn_scene_index]
            if not scene.dialogue:
                state.gn_scene_index += 1
                state.gn_elapsed_ms = 0.0
            else:
                dialogue = scene.dialogue[state.gn_dialogue_index]
                text = dialogue.text_ko if t.lang == "ko" else dialogue.text_en
                typed = dialogue_typed_chars(dialogue.duration_ms, state.gn_elapsed_ms, len(text))
                art_dir = data_dir / "art"
                bg: Background | None = None
                p_l: Portrait | None = None
                p_r: Portrait | None = None
                bg_key = f"bg:{scene.background_id}"
                if bg_key not in _demo_gn_cache:
                    try:
                        _demo_gn_cache[bg_key] = load_background(art_dir, scene.background_id)
                    except (KeyError, FileNotFoundError):
                        _demo_gn_cache[bg_key] = None
                bg_val = _demo_gn_cache[bg_key]
                if isinstance(bg_val, Background):
                    bg = bg_val
                for p_id, slot in (
                    (scene.portrait_left, "p_l"),
                    (scene.portrait_right, "p_r"),
                ):
                    if p_id:
                        pkey = f"portrait:{p_id}"
                        if pkey not in _demo_gn_cache:
                            try:
                                _demo_gn_cache[pkey] = load_portrait(art_dir, p_id)
                            except (KeyError, FileNotFoundError):
                                _demo_gn_cache[pkey] = None
                        val = _demo_gn_cache[pkey]
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
                state.gn_elapsed_ms += 100 * 10
                if state.gn_elapsed_ms >= dialogue.duration_ms:
                    state.gn_dialogue_index += 1
                    state.gn_elapsed_ms = 0.0
                    if state.gn_dialogue_index >= len(scene.dialogue):
                        state.gn_scene_index += 1
                        state.gn_dialogue_index = 0
                        if state.gn_scene_index >= len(chain):
                            state.screen = ScreenKind.SAVED_PROGRESS
    elif state.screen is ScreenKind.SAVED_PROGRESS:
        from wet_run.engine import save_progress as sp

        console.clear()
        summary = sp.get_progress_summary(save_dir=data_dir / "saves" if data_dir else None)
        lines = sp.render_summary_lines(summary, t_lang=t.lang)
        console.print(2, 2, "═══ SAVED PROGRESS ═══")
        for i, line in enumerate(lines):
            console.print(2, 4 + i, line)
        console.print(2, 16, "  [1] 다른 캐릭터  [2] 게임 계속  [3] 메인메뉴")
    elif state.screen is ScreenKind.CHARACTER_SELECT:
        console.clear()
        console.print(2, 2, "═══ CHARACTER SELECT (auto-pilot) ═══")
        console.print(2, 4, "> The Finn: I need a jockey. Sense/Net, first run.")
        console.print(2, 6, "  1. 케이 (K) — Novice       'I just need the money.'")
        console.print(2, 7, "  2. 실 (Sil) — Veteran     'I know the risks.'")
        console.print(2, 8, "  3. 카스 (Kas) — Heretic    'I'm here to burn it all down.'")
        console.print(2, 11, f"  → Auto-selected: {state.character_id}")
    elif state.screen is ScreenKind.CHAPTER and data_dir is not None:
        from wet_run.engine import chapter_view

        chapter = chapter_for_character(state.character_id, data_dir)
        state.chapter_elapsed_ms += 100  # ~10fps tick
        state.chapter_typed_chars = tick_chapter(
            chapter, state.chapter_elapsed_ms, state.chapter_typed_chars
        )
        chapter_view.render_chapter(
            console, chapter, t, state.chapter_typed_chars, state.chapter_elapsed_ms
        )
    elif state.screen is ScreenKind.HUB:
        hub.render_hub(console, t, state)
    elif state.screen is ScreenKind.CYBERSPACE_BROWSER and data_dir is not None:
        from wet_run.engine import cyberspace_browser as cb_screen

        cb_screen.render_cyberspace_browser(console, t, state)
    elif state.screen is ScreenKind.CYBERSPACE_MAP:
        console.clear()
        console.print(2, 2, "═══ CYBERSPACE MAP ═══")
        if state.world_map:
            y = 4
            for world_id, world in state.world_map.worlds.items():
                m = "▸ " if world_id == state.world_map.current_world else "  "
                console.print(2, y, f"{m}WORLD: {world.name}")
                y += 1
                for sector_id, sector in world.sectors.items():
                    sm = "→ " if sector_id == state.world_map.current_sector else "  "
                    console.print(
                        4, y, f"{sm}SECTOR: {sector.name} [{len(sector.servers)} servers]"
                    )
                    y += 1
                    for srv in sector.servers[:3]:
                        vm = "• " if srv.id == state.world_map.current_server else "  "
                        console.print(6, y, f"{vm}{srv.name}")
                        y += 1
                    if len(sector.servers) > 3:
                        console.print(6, y, f"  ... and {len(sector.servers) - 3} more")
                        y += 1
                y += 1
        else:
            console.print(2, 4, "No world map loaded.")
        console.print(2, console.height - 3, "[ESC] Back to Hub")
    elif state.screen is ScreenKind.ARC_PHASE and state.current_arc is not None:
        from wet_run.engine import phase_view

        arc = state.current_arc
        if state.current_chapter_index < len(arc.chapters):
            chapter = arc.chapters[state.current_chapter_index]
            if state.current_phase_index < len(chapter.phases):
                phase = chapter.phases[state.current_phase_index]
                phase_view.render_arc_phase(
                    console,
                    phase,
                    state.current_beat_index,
                    state.phase_typed_chars,
                    0.0,
                    state.phase_elapsed_ms,
                    t,
                )
    elif state.screen is ScreenKind.NPC:
        from wet_run.engine import npc_view

        if state.npc_state is not None:
            npc_view.render_npc(console, t, state, state.npc_state)
        else:
            console.clear()
            console.print(2, 2, "=== NO NPC STATE ===")
    elif state.screen is ScreenKind.EVENT:
        from wet_run.engine import event_view

        if state.active_event is not None:
            event_view.render_event_story(console, t, state, state.active_event)
        else:
            console.clear()
            console.print(2, 2, "=== NO ACTIVE EVENT ===")
    elif state.screen is ScreenKind.STORY and data_dir is not None:
        from wet_run.engine import story_view as story_screen

        registry = story_screen.StoryRegistry.load(data_dir)
        story_screen.render_story(console, state, registry, state.story_aftermath_id)
    elif state.screen is ScreenKind.MATRIX and state.matrix is not None:
        layout = matrix_view.get_layout(state.matrix)
        matrix_view.render_matrix(console, t, state, layout)


def print_frame(
    console: tcod.console.Console,
    state: AppState,
    step: int,
    elapsed: float,
    narration: str,
    *,
    clear: bool,
) -> None:
    """Write a single frame to stdout."""
    if clear:
        sys.stdout.write("\033[2J\033[H")
    sys.stdout.write(render_to_text(console))
    sys.stdout.write("\n")
    sys.stdout.write(f"[Step {step:03d}  T+{elapsed:5.1f}s  Screen: {state.screen.value}]\n")
    if narration:
        sys.stdout.write(f"> {narration}\n")
    sys.stdout.write("\n")
    sys.stdout.flush()


def _step_auto(
    state: AppState,
    missions: list[Mission],
    visited: set[str],
    mission_idx: list[int],
    data_dir: Path | None = None,
) -> str:
    """Advance the state by one auto-step. Returns narration."""
    if state.screen is ScreenKind.MENU:
        menu_option = getattr(state, "_demo_menu_option", None)
        if menu_option is not None:
            state.menu_selection_index = menu_option - 1
            if menu_option == 2:
                state.screen = ScreenKind.GRAPHIC_NOVEL_MENU
                return "Auto: Menu → Graphic Novel Menu."
        state.screen = ScreenKind.CHARACTER_SELECT
        return "Auto: New Run. → Character Select."

    if state.screen is ScreenKind.GRAPHIC_NOVEL_MENU:
        # ADR-0048: For character modes, hop through ending menu; prologue skips
        menu_option = getattr(state, "_demo_menu_option", None)
        if menu_option is not None and menu_option >= 3:
            gn_map = {3: "novice", 4: "veteran", 5: "heretic"}
            state.gn_mode = gn_map.get(menu_option, "prologue")
        if state.gn_mode in ("novice", "veteran", "heretic"):
            state.gn_ending_choice = "A"
            state.screen = ScreenKind.GRAPHIC_NOVEL_ENDING_MENU
            return f"Auto: Graphic Novel → choose ending for {state.gn_mode}."
        # prologue
        state.gn_ending_choice = "A"
        state.gn_scene_index = 0
        state.gn_dialogue_index = 0
        state.gn_elapsed_ms = 0.0
        state.gn_paused = False
        state.screen = ScreenKind.GRAPHIC_NOVEL
        return f"Auto: Graphic Novel [{state.gn_mode}] → playing."

    if state.screen is ScreenKind.GRAPHIC_NOVEL_ENDING_MENU:
        # ADR-0048: Auto-pick ending A
        state.gn_ending_choice = "A"
        state.gn_scene_index = 0
        state.gn_dialogue_index = 0
        state.gn_elapsed_ms = 0.0
        state.gn_paused = False
        state.screen = ScreenKind.GRAPHIC_NOVEL
        return f"Auto: Graphic Novel [{state.gn_mode} ending A] → playing."

    if state.screen is ScreenKind.SAVED_PROGRESS:
        state.screen = ScreenKind.MENU
        return "Auto: Saved progress → menu."

    if state.screen is ScreenKind.CHARACTER_SELECT:
        # Auto-pick already-set character_id, advance to chapter.
        state.chapter_id = f"chapter_{state.character_id}"
        state.chapter_elapsed_ms = 0.0
        state.chapter_typed_chars = 0
        # Load arc data (same as _load_chapter in menu.py)
        try:
            from wet_run.engine import config as config_mod

            state.current_arc = get_arc_for_character(config_mod.DATA_DIR, state.character_id)
        except Exception:
            state.current_arc = None
        state.current_chapter_index = 0
        state.current_phase_index = 0
        state.current_beat_index = 0
        state.phase_elapsed_ms = 0.0
        state.phase_typed_chars = 0
        state.screen = ScreenKind.CHAPTER
        return f"Auto: selected {state.character_id}. → Chapter."

    if state.screen is ScreenKind.CHAPTER:
        # Auto-skip chapter after 2s of display → ARC_PHASE (if arc) or HUB
        if state.chapter_elapsed_ms > 2000:
            if state.current_arc is not None:
                state.current_chapter_index = 0
                state.current_phase_index = 0
                state.current_beat_index = 0
                state.phase_elapsed_ms = 0.0
                state.phase_typed_chars = 0
                state.screen = ScreenKind.ARC_PHASE
                return "Auto: Chapter done. → Arc Phase."
            state.screen = ScreenKind.HUB
            return "Auto: Chapter done. → Hub."
        return f"Auto: chapter typing... ({state.chapter_typed_chars} chars)"

    if state.screen is ScreenKind.ARC_PHASE:
        # Auto-advance through beats/phases
        arc = state.current_arc
        if arc is None:
            state.screen = ScreenKind.HUB
            return "Auto: No arc. → Hub."
        if state.current_chapter_index >= len(arc.chapters):
            state.screen = ScreenKind.HUB
            return "Auto: Arc complete. → Hub."
        chapter = arc.chapters[state.current_chapter_index]
        if state.current_phase_index >= len(chapter.phases):
            state.current_chapter_index += 1
            state.current_phase_index = 0
            state.current_beat_index = 0
            state.phase_elapsed_ms = 0.0
            state.phase_typed_chars = 0
            if state.current_chapter_index >= len(arc.chapters):
                state.screen = ScreenKind.HUB
                return "Auto: All chapters done. → Hub."
            return f"Auto: Chapter {state.current_chapter_index}."
        phase = chapter.phases[state.current_phase_index]
        if state.current_beat_index >= len(phase.beats):
            state.current_phase_index += 1
            state.current_beat_index = 0
            state.phase_elapsed_ms = 0.0
            state.phase_typed_chars = 0
            return f"Auto: Phase {state.current_phase_index} done."
        # Tick beat typing
        if phase.beats:
            beat = phase.beats[state.current_beat_index]
            text = beat.text_en
            typed = int(state.phase_elapsed_ms / 30)
            state.phase_typed_chars = min(typed, len(text))
            if typed >= len(text) and state.phase_elapsed_ms >= 500:
                state.current_beat_index += 1
                state.phase_elapsed_ms = 0.0
                state.phase_typed_chars = 0
                return f"Auto: beat {state.current_beat_index}/{len(phase.beats)}."
        state.phase_elapsed_ms += 100
        return (
            f"Auto: arc ch{state.current_chapter_index} ph{state.current_phase_index} "
            f"beat{state.current_beat_index}"
        )

    if state.screen is ScreenKind.HUB:
        if not missions:
            return "No jobs for your grade. Sit tight."
        from wet_run.matrix.exploration import ExplorationState

        m = missions[mission_idx[0] % len(missions)]
        state.current_mission = m
        gen = MatrixGenerator()
        state.matrix = gen.generate(seed=m.matrix_seed, mission_grade=state.player_grade)
        state.current_node_id = state.matrix.entry_id
        state.exploration = ExplorationState(current=state.matrix.entry_id)
        visited.clear()
        visited.add(state.current_node_id)
        state.screen = ScreenKind.MATRIX
        mission_idx[0] += 1
        return f"Auto: selected {m.title!r}. Jacking in..."

    if state.screen is ScreenKind.CYBERSPACE_MAP:
        # Demo: after showing map, return to Hub
        if not hasattr(state, "_cyberspace_map_steps"):
            state._cyberspace_map_steps = 0
        state._cyberspace_map_steps += 1
        if state._cyberspace_map_steps > 2:
            state._cyberspace_map_steps = 0
            state.screen = ScreenKind.HUB
            return "Auto: Map viewed. → Hub."
        return f"Auto: viewing cyberspace map... ({state._cyberspace_map_steps})"

    if state.screen is ScreenKind.MATRIX:
        assert state.matrix is not None
        assert state.current_node_id is not None
        nbrs = state.matrix.neighbors(state.current_node_id)
        unvisited = [n for n in nbrs if n.id not in visited]
        if unvisited:
            target = unvisited[0]
            state.current_node_id = target.id
            if state.exploration is not None:
                state.exploration.visit(target.id)
            visited.add(target.id)
            ppl = calculate_ppl(state.player_loadout)
            zdr = node_zdr(target)
            st = node_status(target, ppl)
            return f"Auto: -> {target.kind.value} (ZDR {zdr}, {st.value.upper()})"
        # All neighbors visited -> jack out and return to Hub
        state.matrix = None
        state.current_node_id = None
        state.current_mission = None
        state.screen = ScreenKind.HUB
        return "Auto: all neighbors visited. Jacking out. Heart racing."

    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--duration", type=float, default=120.0)
    parser.add_argument("--step-delay", type=float, default=1.0)
    parser.add_argument(
        "--no-clear", action="store_true", help="Append frames instead of clearing the screen."
    )
    parser.add_argument("--lang", default="en", choices=["en", "ko"])
    parser.add_argument(
        "--missions", type=int, default=2, help="How many missions to cycle through."
    )
    parser.add_argument(
        "--character",
        default="novice",
        choices=["novice", "veteran", "heretic"],
        help="Auto-selected character (default novice)",
    )
    parser.add_argument(
        "--gn-mode",
        default=None,
        choices=["prologue", "novice", "veteran", "heretic"],
        help="If set, run graphic novel mode instead of normal flow",
    )
    parser.add_argument(
        "--menu-option",
        type=int,
        default=None,
        choices=[1, 2, 3, 4, 5, 6],
        help="Auto-select menu option (1=new run, 2=graphic novel, 3=continue, etc.)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    t = Translator(args.lang, data_dir=data_dir / "i18n")

    state = AppState()
    state.character_id = args.character
    state.job_board = JobBoard.load(data_dir / "missions" / "missions.json")
    # If --gn-mode is set, jump straight to GRAPHIC_NOVEL_MENU
    if args.gn_mode is not None:
        state.gn_mode = args.gn_mode
        state.screen = ScreenKind.GRAPHIC_NOVEL_MENU
    if args.menu_option is not None:
        state._demo_menu_option = args.menu_option
    console = tcod.console.Console(80, 50, order="F")

    available = list(state.job_board.available_for(state.player_grade))
    if not available:
        sys.stderr.write("No missions available. Add missions to data/missions/.\n")
        return 1
    missions = available[: args.missions]
    visited: set[str] = set()
    mission_idx = [0]

    start = time.monotonic()
    step = 0
    narration = "Auto-demo. The world goes gray."
    render_frame(console, state, t, data_dir)
    print_frame(console, state, step, 0.0, narration, clear=not args.no_clear)
    step += 1
    time.sleep(args.step_delay)

    while time.monotonic() - start < args.duration:
        elapsed = time.monotonic() - start
        narration = _step_auto(state, missions, visited, mission_idx, data_dir)
        render_frame(console, state, t, data_dir)
        print_frame(console, state, step, elapsed, narration, clear=not args.no_clear)
        step += 1
        time.sleep(args.step_delay)

    sys.stdout.write(f"\n=== Demo complete: {step} steps in {args.duration:.0f}s ===\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
