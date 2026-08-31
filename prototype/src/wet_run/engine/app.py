"""Main application entry point.

Phase 5: screen state machine (Menu → Hub → Matrix → back).
"""

from __future__ import annotations

import sys
import time

import tcod.console
import tcod.context
import tcod.tileset

from ..audio import sound_manager
from ..combat.registry import IceRegistry, ProgramRegistry
from ..i18n import Translator
from ..missions import JobBoard
from ..portraits import PortraitManager
from . import config
from .state import AppState, ScreenKind

__all__ = ["AppState", "ScreenKind"]


def _load_job_board() -> JobBoard:
    """Load the mission JSON if present; return an empty board otherwise."""
    return JobBoard.load(config.DATA_DIR / "missions" / "missions.json")


def main() -> int:
    """Run the game. Returns exit code (0 = success)."""
    if not config.FONT_PATH.exists() and config.find_ttf_font() is None:
        sys.stderr.write(
            f"ERROR: No font found.\n"
            f"  Bitmap: {config.FONT_PATH}\n"
            f"  TTF: search system fonts\n"
            f"Run: make download-font\n"
        )
        return 1

    try:
        return _main_inner()
    except Exception as exc:  # pragma: no cover
        from . import crash_reporter

        crash_reporter.report_crash(exc, None, "main() top-level")
        sys.stderr.write(
            f"CRASH: {exc.__class__.__name__}: {exc}\n"
            f"Crash log: {crash_reporter.crash_report_path()}\n"
        )
        return 1


def _main_inner() -> int:
    """Inner main function where crash reporter is not yet active."""
    from .font_loader import load_font
    from .main_loop import tick_current_screen

    tileset, is_ttf = load_font()

    t = Translator(config.DEFAULT_LANGUAGE, data_dir=config.DATA_DIR / "i18n")
    portraits = PortraitManager(data_dir=config.DATA_DIR / "portraits")
    prog_registry = ProgramRegistry.load(config.DATA_DIR / "programs" / "programs.json")
    ice_registry = IceRegistry.load(config.DATA_DIR / "combat" / "ice_types.json")

    state = AppState()
    state.job_board = _load_job_board()

    # Detect existing saves to enable CONTINUE option in main menu.
    # GA-002 fix: state.has_save was never assigned, so the CONTINUE
    # option was permanently disabled even when saves existed on disk.
    from .save_manager import (
        AUTO_SAVE_SLOT,
        MAX_SLOTS,
        SaveManager,
    )

    save_manager = SaveManager()
    state.has_save = save_manager.has_save(AUTO_SAVE_SLOT) or any(
        save_manager.has_save(slot) for slot in range(1, MAX_SLOTS + 1)
    )

    # Store registries for combat (passed to _render/_handle_input)
    _global_prog_registry = prog_registry
    _global_ice_registry = ice_registry

    # Initialize telemetry if opted in
    if state.telemetry_opt_in:
        from ..combat.telemetry_integration import TelemetryConfig, TelemetryIntegrator

        state.telemetry = TelemetryIntegrator(
            TelemetryConfig(opted_in_at_start=state.telemetry_opt_in)
        )
    else:
        from ..combat.telemetry_integration import TelemetryIntegrator

        state.telemetry = TelemetryIntegrator()

    # ADR-0198: resolve the user's selected resolution preset.
    preset_name = getattr(state, "resolution", config.DEFAULT_RESOLUTION)
    preset = config.RESOLUTION_PRESETS.get(
        preset_name, config.RESOLUTION_PRESETS[config.DEFAULT_RESOLUTION]
    )
    cols, rows = preset.cols or config.SCREEN_WIDTH, preset.rows or config.SCREEN_HEIGHT

    with tcod.context.new(
        columns=cols,
        rows=rows,
        tileset=tileset,  # type: ignore[arg-type]
        title=config.SCREEN_TITLE,
        vsync=True,
    ) as context:
        root_console = tcod.console.Console(cols, rows, order="F")

        running = True
        last_time = time.monotonic()
        while running:
            try:
                now = time.monotonic()
                delta_s = now - last_time
                last_time = now
                # Phase D-2 deep3: per-screen tick dispatch (extracted)
                tick_current_screen(
                    state,
                    delta_s,
                    ice_registry=_global_ice_registry,
                    program_registry=_global_prog_registry,
                )

                _render(
                    root_console,
                    t,
                    portraits,
                    state,
                    _global_prog_registry,
                    _global_ice_registry,
                )
                context.present(root_console)

                for event in tcod.event.wait():
                    if isinstance(event, tcod.event.WindowEvent) and event.type == "WindowClose":
                        running = False
                        break
                    # ADR-0197: Gamepad adapter - intercept ControllerButton/Axis/Device
                    # BEFORE dispatch and translate to synthetic KeyDown events.
                    # Zero per-screen handler changes (35 ScreenKinds, ~12 active).
                    import time as _gamepad_time

                    if state.gamepad_enabled:
                        from . import gamepad as _gamepad

                        # Handle ControllerDevice (hot-plug) events.
                        if isinstance(event, tcod.event.ControllerDevice):
                            from . import gamepad_state as _gamepad_state

                            _gamepad_state.handle_device_event(event, state)
                            continue

                        # Handle ControllerAxis (analog sticks + triggers).
                        if isinstance(event, tcod.event.ControllerAxis):
                            # Convert raw axis int -> ControllerAxis enum.
                            axis_enum = tcod.sdl.joystick.ControllerAxis(event.axis)
                            # Trigger -> Combat skill (LT=1, RT=2)
                            skill_idx = _gamepad.trigger_to_skill_index(axis_enum, event.value)
                            if skill_idx is not None and state.screen is ScreenKind.COMBAT:
                                keysym = (
                                    tcod.event.KeySym.N1 if skill_idx == 0 else tcod.event.KeySym.N2
                                )
                                synthetic_axis = tcod.event.KeyDown(
                                    sym=keysym,
                                    scancode=tcod.event.Scancode(event.scancode)
                                    if hasattr(event, "scancode")
                                    else tcod.event.Scancode(0),
                                    mod=tcod.event.Modifier(0),
                                    sdl_event=event.sdl_event,
                                    timestamp_ns=event.timestamp_ns,
                                )
                                result = _handle_input(
                                    synthetic_axis,
                                    state,
                                    _global_prog_registry,
                                    _global_ice_registry,
                                )
                                if not result:
                                    running = False
                                    break
                                continue
                            # Stick -> arrow keys (deadzone + repeat)
                            nav_key: tcod.event.KeySym | None = _gamepad.axis_to_navigation_keysym(
                                axis_enum, event.value
                            )
                            if nav_key is not None:
                                # Only emit once per stick motion (axis events fire continuously)
                                # by checking magnitude change threshold. For simplicity,
                                # we let per-screen handlers handle repeat naturally.
                                synthetic_axis_nav = tcod.event.KeyDown(
                                    sym=nav_key,
                                    scancode=tcod.event.Scancode(0),
                                    mod=tcod.event.Modifier(0),
                                    sdl_event=event.sdl_event,
                                    timestamp_ns=event.timestamp_ns,
                                )
                                result = _handle_input(
                                    synthetic_axis_nav,
                                    state,
                                    _global_prog_registry,
                                    _global_ice_registry,
                                )
                                if not result:
                                    running = False
                                    break
                                continue

                        # Handle ControllerButton (digital face buttons + shoulders).
                        if isinstance(event, tcod.event.ControllerButton):
                            mapped_keysym: tcod.event.KeySym | None = _gamepad.gamepad_to_keysym(
                                event.button
                            )
                            if mapped_keysym is not None and event.pressed:
                                # Button repeat logic: emit KeyDown only if enough time
                                # has passed since last press of the same button.
                                now_ns = event.timestamp_ns or (_gamepad_time.monotonic_ns())
                                last_ns = state.gamepad_button_last_press.get(int(event.button), 0)
                                elapsed_ms = (now_ns - last_ns) / 1_000_000
                                if last_ns > 0 and elapsed_ms < _gamepad.GAMEPAD_REPEAT_INTERVAL_MS:
                                    continue  # too soon, skip
                                state.gamepad_button_last_press[int(event.button)] = now_ns
                                synthetic_btn = tcod.event.KeyDown(
                                    sym=mapped_keysym,
                                    scancode=tcod.event.Scancode(0),
                                    mod=tcod.event.Modifier(0),
                                    sdl_event=event.sdl_event,
                                    timestamp_ns=event.timestamp_ns,
                                )
                                result = _handle_input(
                                    synthetic_btn,
                                    state,
                                    _global_prog_registry,
                                    _global_ice_registry,
                                )
                                if not result:
                                    running = False
                                    break
                                continue

                    result = _handle_input(
                        event, state, _global_prog_registry, _global_ice_registry
                    )
                    if not result:
                        running = False
                        break
            except Exception as exc:  # pragma: no cover
                from . import crash_reporter

                crash_reporter.report_crash(exc, state, "game loop")
                sys.stderr.write(
                    f"CRASH during loop: {exc.__class__.__name__}: {exc}\n"
                    f"Crash log: {crash_reporter.crash_report_path()}\n"
                )
                return 1

        return 0


def _render_cyberspace_map(console: tcod.console.Console, t: Translator, state: AppState) -> None:
    """Render CYBERSPACE_MAP (Phase D-2: thin wrapper, see cyberspace_map_view)."""
    from .cyberspace_map_view import render_cyberspace_map as _do_render

    _do_render(console, state)


def _advance_arc_phase(state: AppState) -> None:
    """Advance arc phase (Phase D-2: thin wrapper, see arc_phase)."""
    from .arc_phase import advance_arc_phase as _do_advance

    _do_advance(state)


def _render(
    console: tcod.console.Console,
    t: Translator,
    portraits: PortraitManager,
    state: AppState,
    prog_registry: ProgramRegistry,
    ice_registry: IceRegistry,
) -> None:
    """Render the current screen (Phase D-2 deep2: dispatch table).

    ``portraits`` is reserved for later use. Actual rendering logic lives
    in screen_dispatch.py — this function just sets BGM theme + delegates.
    """
    _ = portraits
    # BGM: play appropriate theme for the current screen
    try:
        from . import original_story

        original_story.update_screen_theme(state.screen.value, state.sound_config)
    except Exception:
        pass
    from .screen_dispatch import render_current_screen

    render_current_screen(
        console,
        t,
        state,
        prog_registry=prog_registry,
        ice_registry=ice_registry,
    )

    if state.perf_hud_enabled:
        _draw_perf_hud(console, state)


def _draw_perf_hud(console: tcod.console.Console, state: AppState) -> None:
    """Draw performance HUD overlay (Phase 15)."""
    if state.perf_tracker is None:
        return

    from ..combat.performance_integration import PerfTracker

    assert state.perf_tracker is not None
    tracker: PerfTracker = state.perf_tracker
    profiles = tracker.get_tick_profiles()
    if not profiles:
        return

    last = profiles[-1]

    # Draw in top-right corner
    x = console.width - 30
    y = 1
    bg = (0, 0, 40)
    fg = (0, 255, 0)

    lines = [
        "─── PERFORMANCE ───",
        f"Tick: {last.tick_label}",
        f"Frame: {last.frame_time_ms:.2f}ms",
        f"Memory: {last.memory_mb:.2f}MB",
        f"Objects: {last.object_count}",
    ]

    for i, line in enumerate(lines):
        console.print(x=x, y=y + i, string=line.ljust(28), fg=fg, bg=bg)


def _handle_global_hotkeys(
    event: object,
    state: AppState,
) -> bool | None:
    """Phase D-2 deep: process global hotkeys (work on all screens).

    Returns:
        True: hotkey handled (event consumed)
        False: global quit signal
        None: not a hotkey, defer to per-screen handler
    """
    import tcod.event

    if not isinstance(event, tcod.event.KeyDown):
        return None

    if event.sym is tcod.event.KeySym.F3:
        state.perf_hud_enabled = not state.perf_hud_enabled
        label = "ENABLED" if state.perf_hud_enabled else "DISABLED"
        state.status_messages.append(f">>> Performance HUD {label}")
        return True

    if event.sym is tcod.event.KeySym.F5:
        from .save_manager import SaveManager, SaveSlotEmptyError

        manager = SaveManager()
        try:
            meta = manager.save(1, state, elapsed_seconds=int(state.demo_elapsed_s))
            state.status_messages.append(f">>> Quicksaved to slot 1 ({meta.size_bytes} bytes)")
        except Exception as e:
            state.status_messages.append(f">>> Quicksave failed: {e}")
        return True

    if event.sym is tcod.event.KeySym.F9:
        from .save_manager import SaveError, SaveManager, SaveSlotEmptyError

        manager = SaveManager()
        try:
            manager.restore_state(1, state)
        except SaveSlotEmptyError:
            state.status_messages.append(">>> Quickload failed: slot 1 is empty")
        except SaveError as e:
            state.status_messages.append(f">>> Quickload failed: {e}")
        return True

    if event.sym is tcod.event.KeySym.M:
        muted = sound_manager.toggle_mute()
        label = "MUTED" if muted else "UNMUTED"
        state.status_messages.append(f">>> Audio {label}")
        return True

    if event.sym in (
        tcod.event.KeySym.EQUALS,
        tcod.event.KeySym.PLUS,
        tcod.event.KeySym.KP_PLUS,
    ):
        from .settings_ui import adjust_volume

        new_vol = adjust_volume(+0.1)
        state.status_messages.append(f">>> Volume: {int(new_vol * 100)}%")
        return True

    if event.sym in (tcod.event.KeySym.MINUS, tcod.event.KeySym.KP_MINUS):
        from .settings_ui import adjust_volume

        new_vol = adjust_volume(-0.1)
        state.status_messages.append(f">>> Volume: {int(new_vol * 100)}%")
        return True

    # Per-category sound toggles
    from ..audio.config import SoundCategory
    from .settings_ui import toggle_category

    category_by_key = {
        tcod.event.KeySym.T: SoundCategory.THEME,
        tcod.event.KeySym.E: SoundCategory.EVENTS,
        tcod.event.KeySym.K: SoundCategory.KEYS,
        tcod.event.KeySym.B: SoundCategory.COMBAT,
        tcod.event.KeySym.V: SoundCategory.MOVEMENT,
        tcod.event.KeySym.I: SoundCategory.ITEMS,
    }
    if event.sym in category_by_key:
        category = category_by_key[event.sym]
        new_state = toggle_category(category)
        label = "ON" if new_state else "OFF"
        state.status_messages.append(f">>> Sound category '{category.value}' toggled: {label}")
        return True

    return None


def _handle_input(
    event: object,
    state: AppState,
    prog_registry: ProgramRegistry,
    ice_registry: IceRegistry,
) -> bool:
    """Dispatch an event to the current screen's handler. False = quit.

    Phase D-2 deep: delegates global hotkeys to _handle_global_hotkeys.
    Phase D-2 deep4: delegates screen-specific input to input_dispatch.
    """
    global_result = _handle_global_hotkeys(event, state)
    if global_result is not None:
        return global_result

    from .input_dispatch import handle_current_screen_input

    return handle_current_screen_input(event, state, prog_registry, ice_registry)


if __name__ == "__main__":
    sys.exit(main())
