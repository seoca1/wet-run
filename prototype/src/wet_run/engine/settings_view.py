"""Settings screen — audio, colorblind mode, keymap (Phase 7).

Options:
- Audio Volume: +/- to adjust
- Colorblind Mode: ON/OFF toggle
- Keymap: display current controls (read-only)
- Resolution: display current resolution
- Back to Menu
"""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym

from ..audio import sound_manager
from ..i18n import Translator
from .layout import (
    RegionId,
    clear_region,
    draw_controls,
    draw_dividers,
    draw_footer,
    draw_title,
    make_shell,
)
from .state import AppState, ScreenKind

SETTINGS_OPTIONS = [
    ("audio", "Audio Volume"),
    ("colorblind", "Colorblind Mode"),
    ("telemetry", "Telemetry Opt-in"),
    ("font_size", "Font Size"),
    ("high_contrast", "High Contrast"),
    ("keymap", "Keymap"),
    ("reset_keymap", "Reset Keymap to Defaults"),
    ("resolution", "Resolution"),
    ("back", "Back to Menu"),
]


def _get_volume() -> float:
    """Return the current master volume from the global SoundManager."""
    return sound_manager.get_sound_manager().volume


def _set_volume(volume: float) -> None:
    """Set the master volume, clamped to [0.0, 1.0]."""
    sound_manager.set_volume(max(0.0, min(1.0, volume)))


def _adjust_volume(delta: float) -> float:
    """Adjust the master volume by ``delta`` and return the new clamped value."""
    sm = sound_manager.get_sound_manager()
    new_vol = max(0.0, min(1.0, sm.volume + delta))
    sm.set_volume(new_vol)
    return new_vol


def render_settings(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
) -> None:
    """Render the settings screen."""
    shell = make_shell()
    title_r = shell[RegionId.TITLE]
    main_r = shell[RegionId.MAIN]
    ctrl_r = shell[RegionId.CONTROLS]
    foot_r = shell[RegionId.FOOTER]

    for r in shell.values():
        clear_region(console, r)
    draw_dividers(console)

    draw_title(console, title_r, title=t("settings.title"), subtitle=t("settings.subtitle"))

    selected = getattr(state, "settings_selected", 0)

    y = main_r.y + 1
    for i, (opt_id, label) in enumerate(SETTINGS_OPTIONS):
        if y > main_r.y + main_r.h - 3:
            break

        is_selected = i == selected
        fg = (255, 255, 255) if is_selected else (180, 180, 180)
        prefix = ">" if is_selected else " "
        value_str = ""

        if opt_id == "audio":
            vol = _get_volume()
            vol_pct = int(vol * 100)
            bar_len = 20
            filled = int(vol * bar_len)
            bar = "[" + "=" * filled + " " * (bar_len - filled) + "]"
            value_str = f"{bar} {vol_pct}%"
        elif opt_id == "colorblind":
            cb = getattr(state, "colorblind_mode", False)
            value_str = t("settings.on") if cb else t("settings.off")
        elif opt_id == "telemetry":
            tel = getattr(state, "telemetry_opt_in", False)
            value_str = t("settings.on") if tel else t("settings.off")
        elif opt_id == "font_size":
            fs = getattr(state, "font_size", "normal")
            value_str = fs.capitalize()
        elif opt_id == "high_contrast":
            hc = getattr(state, "high_contrast", False)
            value_str = t("settings.on") if hc else t("settings.off")
        elif opt_id == "keymap":
            customized = getattr(state, "keymap_customized", False)
            value_str = t("settings.keymap_custom") if customized else t("settings.keymap_default")
        elif opt_id == "reset_keymap":
            customized = getattr(state, "keymap_customized", False)
            value_str = t("settings.keymap_apply") if customized else t("settings.keymap_default")
        elif opt_id == "resolution":
            from . import config as cfg

            value_str = f"{cfg.SCREEN_WIDTH}x{cfg.SCREEN_HEIGHT}"
        else:
            value_str = ""

        line = f"{prefix} [{i + 1}] {label}"
        if value_str:
            line += f"  {value_str}"

        console.print(x=main_r.x + 2, y=y, string=line, fg=fg)
        y += 1

    controls_text = t("settings.controls")
    draw_controls(console, ctrl_r, [controls_text])
    draw_footer(console, foot_r, text=t("settings.footer"))


def handle_settings_input(
    event: tcod.event.Event,
    state: AppState,
) -> AppState | None:
    """Handle input on the settings screen. Returns updated state or None."""
    if not isinstance(event, KeyDown):
        return state

    selected = getattr(state, "settings_selected", 0)
    max_options = len(SETTINGS_OPTIONS)

    if event.sym is KeySym.ESCAPE:
        state.screen = ScreenKind.MENU
        if hasattr(state, "settings_selected"):
            delattr(state, "settings_selected")
        return state

    if event.sym is KeySym.UP:
        state.settings_selected = (selected - 1) % max_options
        return state

    if event.sym is KeySym.DOWN:
        state.settings_selected = (selected + 1) % max_options
        return state

    if event.sym in (KeySym.RETURN, KeySym.SPACE, KeySym.RIGHT):
        opt_id = SETTINGS_OPTIONS[selected][0]
        if opt_id == "audio":
            _adjust_volume(+0.1)
            return state
        elif opt_id == "colorblind":
            current = getattr(state, "colorblind_mode", False)
            state.colorblind_mode = not current
            return state
        elif opt_id == "telemetry":
            current = getattr(state, "telemetry_opt_in", False)
            state.telemetry_opt_in = not current
            # Update active telemetry integrator if it exists
            if hasattr(state, "telemetry") and state.telemetry is not None:
                from ..combat.telemetry_integration import TelemetryConfig, TelemetryIntegrator

                state.telemetry = TelemetryIntegrator(
                    TelemetryConfig(opted_in_at_start=state.telemetry_opt_in)
                )
            return state
        elif opt_id == "font_size":
            cycle = ("small", "normal", "large")
            current = getattr(state, "font_size", "normal")
            idx = cycle.index(current) if current in cycle else 1
            state.font_size = cycle[(idx + 1) % 3]
            return state
        elif opt_id == "high_contrast":
            current = getattr(state, "high_contrast", False)
            state.high_contrast = not current
            return state
        elif opt_id == "back":
            state.screen = ScreenKind.MENU
            if hasattr(state, "settings_selected"):
                delattr(state, "settings_selected")
            return state
        elif opt_id == "keymap":
            return state
        elif opt_id == "reset_keymap":
            state.keymap_customized = False
            return state
        elif opt_id == "resolution":
            return state

    if event.sym in (KeySym.LEFT, KeySym.MINUS, KeySym.KP_MINUS):
        opt_id = SETTINGS_OPTIONS[selected][0]
        if opt_id == "audio":
            _adjust_volume(-0.1)
        return state

    if event.sym in (KeySym.N1, KeySym.N2, KeySym.N3, KeySym.N4, KeySym.N5):
        idx = event.sym.value - KeySym.N1.value
        if 0 <= idx < max_options:
            state.settings_selected = idx
            opt_id = SETTINGS_OPTIONS[idx][0]
            if opt_id == "audio":
                _adjust_volume(+0.1)
            elif opt_id == "colorblind":
                current = getattr(state, "colorblind_mode", False)
                state.colorblind_mode = not current
            elif opt_id == "back":
                state.screen = ScreenKind.MENU
                if hasattr(state, "settings_selected"):
                    delattr(state, "settings_selected")
        return state

    return state
