"""Salvation Phase screens — epilogue selection, playback, and ending choice (ADR-0090).

Three screens:
    - SALVATION_INTRO:   9-character epilogue selection menu
    - SALVATION_EPILOGUE: play selected epilogue scene (reuses GN scene rendering)
    - SALVATION_ENDING:   A/B/C ending selection

Flow:
    CHAPTER_5_COMPLETE
      → enter_salvation_intro()        → screen = SALVATION_INTRO
      → user selects character
      → start_salvation_epilogue()      → screen = SALVATION_EPILOGUE
      → epilogue scene plays
      → complete_salvation_epilogue()   → screen = SALVATION_ENDING
      → user selects ending
      → reach_final()                   → screen = HUB
"""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym

from ..i18n import Translator
from ..run.state import RunState
from .layout import RegionId, clear_region, draw_controls, draw_dividers, draw_footer, make_shell
from .salvation import (
    SALVATION_ENDINGS,
    SALVATION_EPILOGUES,
    SalvationRunner,
    get_epilogue_ending,
    list_available_epilogues,
    validate_epilogue_selection,
)
from .state import AppState, ScreenKind


def render_salvation_intro(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
) -> None:
    """Render the Salvation Phase epilogue selection menu (9 characters)."""
    shell = make_shell()
    title_r = shell[RegionId.TITLE]
    main_r = shell[RegionId.MAIN]
    ctrl_r = shell[RegionId.CONTROLS]
    foot_r = shell[RegionId.FOOTER]

    for r in shell.values():
        clear_region(console, r)
    draw_dividers(console)

    console.print(
        title_r.x, title_r.y, " ══════════════════════════════════════════ ", fg=(180, 80, 255)
    )
    title = (
        t("salvation.title") if t.lang == "ko" else "=== SALVATION PHASE — Epilogue Selection ==="
    )
    console.print(title_r.x + 2, title_r.y, title, fg=(180, 80, 255))

    lang = t.lang
    choices = list_available_epilogues(lang)

    console.print(main_r.x + 2, main_r.y + 1, "[ Select your epilogue ]", fg=(200, 200, 100))
    y = main_r.y + 3
    for i, (char_id, label) in enumerate(choices):
        entry = SALVATION_EPILOGUES[char_id]
        tagline = entry[f"tagline_{lang}"]
        ending = entry["ending"]
        line = f"  [{i + 1}] {label} (Ending {ending}) — {tagline}"
        console.print(main_r.x + 2, y + i * 2, line, fg=(180, 180, 180))

    selection = getattr(state, "salvation_selection", None)
    if selection:
        console.print(
            main_r.x + 2,
            main_r.y + main_r.h - 3,
            f"Selected: {selection.character_id} | Ending: {selection.ending}",
            fg=(100, 255, 100),
        )

    draw_controls(
        console,
        ctrl_r,
        lines=[
            t("salvation.intro_controls", default="[1-9] Select   [ENTER] Confirm   [ESC] Back")
        ],
    )

    draw_footer(console, foot_r, text="Salvation Phase  |  Step 0")


def handle_salvation_intro_input(
    event: tcod.event.Event,
    state: AppState,
) -> bool:
    """Handle input on the SALVATION_INTRO screen.

    Returns False to quit, True to continue.
    """
    if isinstance(event, KeyDown):
        if event.sym in (KeySym.ESCAPE, KeySym.Q):
            state.screen = ScreenKind.HUB
            return True

        num_keys = [
            KeySym.N1,
            KeySym.N2,
            KeySym.N3,
            KeySym.N4,
            KeySym.N5,
            KeySym.N6,
            KeySym.N7,
            KeySym.N8,
            KeySym.N9,
        ]
        if event.sym in num_keys:
            idx = num_keys.index(event.sym)
            choices = list_available_epilogues("en")
            if 0 <= idx < len(choices):
                char_id, _label = choices[idx]
                try:
                    validate_epilogue_selection(char_id)
                    ending = get_epilogue_ending(char_id)
                    if not hasattr(state, "salvation_runner"):
                        state.salvation_runner = SalvationRunner()
                    runner = state.salvation_runner
                    assert runner is not None
                    runner.choose_epilogue(char_id)
                    state.salvation_selection = runner.selection
                    state.status_messages.append(f"Selected: {char_id} (Ending {ending})")
                except ValueError as e:
                    state.status_messages.append(f"Error: {e}")
            return True

        if event.sym is KeySym.RETURN or event.sym is KeySym.SPACE:
            confirmed_runner: SalvationRunner | None = getattr(state, "salvation_runner", None)
            if confirmed_runner and confirmed_runner.selection:
                rs: RunState | None = state.run_state
                if rs is None:
                    state.status_messages.append("Error: No active run state.")
                    return True
                rs.enter_salvation_intro()
                state.screen = ScreenKind.SALVATION_EPILOGUE
                state.salvation_epilogue_elapsed_ms = 0.0
                state.salvation_epilogue_typed_chars = 0
                state.salvation_epilogue_dialogue_index = 0
                state.ng_plus_unlocked = True
            return True

    return True


def render_salvation_epilogue(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
) -> None:
    """Render the Salvation epilogue scene playback (SALVATION_EPILOGUE screen)."""
    shell = make_shell()
    title_r = shell[RegionId.TITLE]
    main_r = shell[RegionId.MAIN]
    ctrl_r = shell[RegionId.CONTROLS]
    foot_r = shell[RegionId.FOOTER]

    for r in shell.values():
        clear_region(console, r)
    draw_dividers(console)

    runner: SalvationRunner | None = getattr(state, "salvation_runner", None)
    if runner is None or runner.selection is None:
        console.print(main_r.x + 2, main_r.y + 2, "[ No epilogue selected ]", fg=(255, 100, 100))
        return

    char_id = runner.selection.character_id

    title = t("salvation.epilogue_title", default="=== EPILOGUE ===")
    console.print(title_r.x + 2, title_r.y, title, fg=(180, 80, 255))

    entry = SALVATION_EPILOGUES.get(char_id, {})
    name_en = entry.get("name_en", char_id)
    name_ko = entry.get("name_ko", char_id)
    tagline_en = entry.get("tagline_en", "")
    tagline_ko = entry.get("tagline_ko", "")

    is_ko = t.lang == "ko"
    char_name = name_ko if is_ko else name_en
    tagline = tagline_ko if is_ko else tagline_en

    console.print(main_r.x + 2, main_r.y + 2, f"Character: {char_name}", fg=(200, 200, 255))
    console.print(main_r.x + 2, main_r.y + 4, tagline, fg=(180, 180, 100))

    if hasattr(state, "salvation_scene_data") and state.salvation_scene_data:
        scene = state.salvation_scene_data
        dialogue = scene.dialogue
        idx = getattr(state, "salvation_epilogue_dialogue_index", 0)
        elapsed_ms = getattr(state, "salvation_epilogue_elapsed_ms", 0)

        if idx < len(dialogue):
            line = dialogue[idx]
            text = line.text_ko if is_ko else line.text_en
            speaker = line.speaker_ko if is_ko else line.speaker

            char_delay_ms = 30
            new_typed = min(int(elapsed_ms / char_delay_ms), len(text))
            display_text = text[:new_typed]
            state.salvation_epilogue_typed_chars = new_typed

            console.print(main_r.x + 2, main_r.y + 7, f"◆ {speaker}", fg=(200, 150, 100))
            y = main_r.y + 9
            for l2 in display_text.split("\n"):
                console.print(main_r.x + 4, y, l2, fg=(220, 220, 220))
                y += 1
                if y >= main_r.y + main_r.h - 4:
                    break

            progress = f"[{idx + 1}/{len(dialogue)}]"
            console.print(main_r.x + 2, main_r.y + main_r.h - 3, progress, fg=(100, 100, 100))
        else:
            console.print(
                main_r.x + 2,
                main_r.y + main_r.h - 3,
                "[ Press ENTER to continue ]",
                fg=(100, 255, 100),
            )
    else:
        console.print(
            main_r.x + 2, main_r.y + main_r.h - 4, "[ Loading epilogue... ]", fg=(150, 150, 150)
        )

    draw_controls(
        console,
        ctrl_r,
        lines=[
            t(
                "salvation.epilogue_controls",
                default="[ENTER/SPACE] Advance   [S] Skip scene   [ESC] Quit",
            )
        ],
    )

    draw_footer(console, foot_r, text=f"Epilogue: {char_id}  |  Salvation Phase")


def handle_salvation_epilogue_input(
    event: tcod.event.Event,
    state: AppState,
) -> bool:
    """Handle input on the SALVATION_EPILOGUE screen.

    Returns False to quit, True to continue.
    """
    if isinstance(event, KeyDown):
        if event.sym in (KeySym.ESCAPE, KeySym.Q):
            state.screen = ScreenKind.HUB
            return True

        if event.sym in (KeySym.RETURN, KeySym.SPACE, KeySym.RIGHT):
            runner: SalvationRunner | None = getattr(state, "salvation_runner", None)
            if runner and runner.selection:
                rs: RunState | None = state.run_state
                if rs is None:
                    state.status_messages.append("Error: No active run state.")
                    return True

                dialogue_idx = getattr(state, "salvation_epilogue_dialogue_index", 0)

                if not hasattr(state, "salvation_scene_data") or state.salvation_scene_data is None:
                    from . import config

                    scenes_dir = config.DATA_DIR / "scenes"
                    try:
                        state.salvation_scene_data = runner.load_epilogue(scenes_dir)
                    except Exception as exc:
                        state.status_messages.append(f"Failed to load epilogue: {exc}")
                        state.screen = ScreenKind.HUB
                        return True

                scene = state.salvation_scene_data
                dialogue_len = len(scene.dialogue) if scene.dialogue else 1

                if dialogue_idx + 1 < dialogue_len:
                    state.salvation_epilogue_dialogue_index = dialogue_idx + 1
                    state.salvation_epilogue_elapsed_ms = 0
                    state.salvation_epilogue_typed_chars = 0
                else:
                    runner.complete_epilogue()
                    rs.complete_salvation_epilogue()
                    state.screen = ScreenKind.SALVATION_ENDING
            return True

        if event.sym is KeySym.S:
            runner = getattr(state, "salvation_runner", None)
            if runner:
                rs2: RunState | None = state.run_state
                if rs2 is None:
                    state.status_messages.append("Error: No active run state.")
                    return True
                runner.complete_epilogue()
                rs2.complete_salvation_epilogue()
                state.screen = ScreenKind.SALVATION_ENDING
            return True

    elapsed = getattr(state, "salvation_epilogue_elapsed_ms", 0)
    state.salvation_epilogue_elapsed_ms = elapsed + 16

    return True


def render_salvation_ending(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
) -> None:
    """Render the Salvation ending selection screen (A/B/C)."""
    shell = make_shell()
    title_r = shell[RegionId.TITLE]
    main_r = shell[RegionId.MAIN]
    ctrl_r = shell[RegionId.CONTROLS]
    foot_r = shell[RegionId.FOOTER]

    for r in shell.values():
        clear_region(console, r)
    draw_dividers(console)

    title = t("salvation.ending_title", default="=== SALVATION PHASE — Ending Selection ===")
    console.print(title_r.x + 2, title_r.y, title, fg=(180, 80, 255))

    lang = t.lang
    ending_labels = {
        "A": ("New Ending", "새로운 결말"),
        "B": ("The Other Ending", "다른 결말"),
        "C": ("The Third Ending", "세 번째 결말"),
    }

    runner: SalvationRunner | None = getattr(state, "salvation_runner", None)
    char_id = runner.selection.character_id if runner and runner.selection else "unknown"
    char_name_en = SALVATION_EPILOGUES.get(char_id, {}).get("name_en", char_id)
    char_name_ko = SALVATION_EPILOGUES.get(char_id, {}).get("name_ko", char_id)
    is_ko = lang == "ko"

    console.print(
        main_r.x + 2,
        main_r.y + 2,
        f"Epilogue: {char_name_ko if is_ko else char_name_en}",
        fg=(200, 200, 255),
    )

    y = main_r.y + 5
    for ending in SALVATION_ENDINGS:
        label_en, label_ko = ending_labels[ending]
        label = label_ko if is_ko else label_en
        desc = t(f"salvation.ending_{ending.lower()}_desc", default="")
        console.print(main_r.x + 4, y, f"  [{ending}] {label}", fg=(180, 180, 180))
        if desc:
            console.print(main_r.x + 6, y + 1, desc, fg=(120, 120, 120))
        y += 3

    draw_controls(
        console,
        ctrl_r,
        lines=[
            t(
                "salvation.ending_controls",
                default="[A] Ending A   [B] Ending B   [C] Ending C   [ESC] Back",
            )
        ],
    )

    draw_footer(console, foot_r, text=f"Salvation Phase  |  {char_id}")


def handle_salvation_ending_input(
    event: tcod.event.Event,
    state: AppState,
) -> bool:
    """Handle input on the SALVATION_ENDING screen.

    Returns False to quit, True to continue.
    """
    if isinstance(event, KeyDown):
        if event.sym in (KeySym.ESCAPE, KeySym.Q):
            state.screen = ScreenKind.HUB
            return True

        if event.sym in (KeySym.N1, KeySym.A):
            ending = "A"
        elif event.sym in (KeySym.N2, KeySym.B):
            ending = "B"
        elif event.sym in (KeySym.N3, KeySym.C):
            ending = "C"
        else:
            return True

        runner: SalvationRunner | None = getattr(state, "salvation_runner", None)
        if runner and runner.selection:
            rs: RunState | None = state.run_state
            if rs is None:
                state.status_messages.append("Error: No active run state.")
                return True
            runner.choose_ending(ending)
            rs.reach_final()
            state.screen = ScreenKind.HUB
            state.status_messages.append(f"Ending {ending} selected. Returning to Hub...")
            if hasattr(state, "salvation_runner"):
                delattr(state, "salvation_runner")
            if hasattr(state, "salvation_selection"):
                delattr(state, "salvation_selection")
            if hasattr(state, "salvation_scene_data"):
                delattr(state, "salvation_scene_data")
            if hasattr(state, "salvation_epilogue_elapsed_ms"):
                delattr(state, "salvation_epilogue_elapsed_ms")
            if hasattr(state, "salvation_epilogue_typed_chars"):
                delattr(state, "salvation_epilogue_typed_chars")
            if hasattr(state, "salvation_epilogue_dialogue_index"):
                delattr(state, "salvation_epilogue_dialogue_index")

        return True

    return True
