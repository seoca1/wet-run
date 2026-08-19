"""Death and restart system (Pillar 3: The Flatline, ADR-0040).

When a player's HP hits 0 in combat (or other circumstances), they
"flatline" — a story moment, not just a game over. The death screen
shows the iconic X head (avatar flatline state) and offers:
- [ENTER] Jack out (return to hub, lose inventory, restart mission)
- [Q] Quit game

ADR-0040 extends this with:
- DEATH_SUMMARY screen: jockey's final report + Sprawl's epitaph
- 3 restart options: new jockey / same jockey / Hall of Dead
- Hall of Dead Jockeys archive (persistent across runs)
- Runner statistics (total_runs, total_deaths, longest_run)

Death is not a hard reset — the player's grade, story progress, and
unlocked missions persist. Only the current run is lost.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod.console

from ..audio import sound_manager as _sm_module
from ..run.memory_bank import MemoryFragment
from .jockey_history import (
    DeceasedJockey,
    JockeyHistory,
    build_deceased_from_state,
    render_death_summary_lines,
    render_hall_of_dead_lines,
)
from .settings_ui import get_volume
from .state import AppState, ScreenKind

if TYPE_CHECKING:
    from collections.abc import Callable

    from ..combat.telemetry_integration import TelemetryIntegrator


def _emit_telemetry_event(
    state: AppState,
    event_name: str,
    recorder: Callable[[TelemetryIntegrator], None],
) -> None:
    """Fire a telemetry recorder only when the player opted in (Phase 16).

    Args:
        state: App state (carry ``telemetry_opt_in`` and ``telemetry``).
        event_name: Human-readable name (used for graceful failure logs).
        recorder: Callable invoked with the active TelemetryIntegrator.
    """
    if not getattr(state, "telemetry_opt_in", False):
        return
    integrator = getattr(state, "telemetry", None)
    if integrator is None:
        return
    try:
        recorder(integrator)
    except Exception as exc:  # pragma: no cover - defensive
        state.status_messages.append(f">>> Telemetry {event_name} failed: {exc}")


def _get_history() -> JockeyHistory:
    """Get the singleton JockeyHistory instance."""
    return JockeyHistory()


def _char_label(character_id: str) -> str:
    """Return the human-readable character label."""
    labels = {
        "novice": "케이 (K) — Novice",
        "veteran": "실 (Sil) — Veteran",
        "heretic": "카스 (Kas) — Heretic",
    }
    return labels.get(character_id, character_id)


def _inventory_snapshot(state: AppState) -> tuple[str, ...]:
    """Get the current inventory as a sorted tuple of item ids."""
    inv = state.inventory or {}
    if isinstance(inv, dict):
        return tuple(sorted(inv.keys()))
    return tuple(sorted(inv))


def _mission_count(state: AppState) -> int:
    """Count missions completed in this run (approx from state)."""
    if state.completed_missions:
        return len(state.completed_missions)
    return state.mission_progress.get("extract_data", 0) + state.mission_progress.get("defeat", 0)


def _playtime_minutes(state: AppState) -> int:
    """Estimate playtime in minutes from demo_elapsed_s."""
    return max(0, int(state.demo_elapsed_s / 60))


def _data_recovered(state: AppState) -> int:
    """Estimate data recovered from mission progress."""
    return int(state.mission_progress.get("extract_data", 0) * 100)


def build_deceased_jockey_from_state(
    state: AppState,
    *,
    timestamp_ms: int | None = None,
    seed: int | None = None,
) -> DeceasedJockey:
    """Build a DeceasedJockey from the current AppState (ADR-0040).

    Args:
        state: The current app state at time of death.
        timestamp_ms: Optional timestamp (defaults to now).
        seed: Optional seed for epitaph selection.

    Returns:
        The DeceasedJockey record to be archived.
    """
    char_id = getattr(state, "character_id", "novice")
    name = _char_label(char_id)
    grade = int(getattr(state, "player_grade", 1))

    died_at_node = ""
    if state.current_node_id:
        died_at_node = state.current_node_id
    elif state.matrix and getattr(state.matrix, "entry_id", None):
        died_at_node = state.matrix.entry_id

    died_at_mission = ""
    if state.current_mission is not None:
        died_at_mission = getattr(state.current_mission, "id", "") or getattr(
            state.current_mission, "title", ""
        )
    elif state.run_state is not None:
        died_at_mission = state.run_state.mission_id

    return build_deceased_from_state(
        name=name,
        character_id=char_id,
        grade=grade,
        died_at_node=died_at_node,
        died_at_mission=died_at_mission,
        inventory=_inventory_snapshot(state),
        missions_completed=_mission_count(state),
        data_recovered=_data_recovered(state),
        playtime_minutes=_playtime_minutes(state),
        timestamp_ms=timestamp_ms,
        seed=seed,
    )


def trigger_death(state: AppState, reason: str = "Combat") -> None:
    """Trigger player death (flatline) — ADR-0040 extended.

    Args:
        state: App state.
        reason: Why the player died (shown in death screen).

    Side effects:
        - Flatlines the current jockey (state.is_dead = True)
        - Persists a memory fragment to ``state.memory_bank`` so the
          next jockey can recall it from construct space
        - Caps the bank at MAX_FRAGMENTS (FIFO eviction)
    """
    state.is_dead = True
    state.death_reason = reason
    state.death_cause = reason
    state.screen = ScreenKind.DEATH
    state.status_messages.append(f">>> FLATLINE: {reason}")
    state.status_messages.append(">>> Press ENTER to jack out")

    # Phase 51+: persist a memory fragment so the next jockey can
    # recall it. Single fragment per death — keeps the bank tight
    # and the narrative moment specific.
    import time as _time

    current_arc = 1
    if state.current_mission is not None:
        raw_arc = getattr(state.current_mission, "arc", 1)
        try:
            current_arc = max(1, min(5, int(raw_arc)))
        except (TypeError, ValueError):
            current_arc = 1
    fragment = MemoryFragment(
        text=(f"Last thing I remember before flatline: {reason}. The construct kept the rest."),
        arc=current_arc,
        timestamp_ms=int(_time.time() * 1000),
    )
    state.memory_bank.add(fragment)

    # Phase 16: Telemetry recorders — gated by player opt-in.
    _emit_telemetry_event(
        state,
        "record_death",
        lambda integrator: integrator.record_death(reason),
    )
    _emit_telemetry_event(
        state,
        "record_run_completed",
        lambda integrator: integrator.record_run_completed(
            run_id=str(state.total_runs),
            grade=state.player_grade,
        ),
    )

    # Play defeat sound (if not already played)
    try:
        _sm_module.play("combat/defeat")
    except Exception:
        pass

    # Build a DeceasedJockey from current state and add to archive (ADR-0040)
    try:
        jockey = build_deceased_jockey_from_state(state)
        history = _get_history()
        history.add(jockey)
        state.last_jockey_summary_id = jockey.jockey_id
        # Bump counters
        state.total_runs += 1
        state.total_deaths += 1
        state.jockey_history_loaded = True
        state.status_messages.append(f">>> Jockey archived: {jockey.name}")
        state.status_messages.append(f'>>> "{jockey.epitaph}"')
    except Exception as e:  # pragma: no cover - defensive
        state.status_messages.append(f">>> Archive failed: {e}")

    # Auto-save on death (player can choose to reload and try again)
    try:
        from .save_manager import SaveManager

        manager = SaveManager()
        manager.save(slot=3, state=state, elapsed_seconds=int(state.demo_elapsed_s))
        state.status_messages.append(">>> Auto-saved death state to slot 3")
    except Exception:
        pass


def advance_to_death_summary(state: AppState) -> None:
    """Transition from DEATH to DEATH_SUMMARY screen (ADR-0040).

    Should be called after the DEATH screen has been shown briefly.
    """
    state.screen = ScreenKind.DEATH_SUMMARY


def jack_out_to_hub(state: AppState) -> None:
    """Recover from death: return to hub, lose current run progress.

    Pillar 3 recovery: The player flatlines but doesn't lose everything.
    Inventory and credits from the current run are forfeited.
    Story progress and unlocked missions persist.
    """
    if not state.is_dead:
        return

    # Clear combat
    state.combat_state = None
    state.action_menu_open = False

    # Clear current matrix (start fresh)
    state.matrix = None
    state.current_node_id = None
    state.cyberspace_layouts = None
    state.server_subgraph = None
    state.in_server_browser = True
    state.selected_server_index = 0

    # Reset mission progress
    state.mission_progress = {}
    state.current_mission = None

    # Reset HP to full (respawn)
    state.player_hp = state.player_max_hp

    # Forfeit inventory (materials gathered this run)
    state.inventory = {}

    # Player is alive again
    state.is_dead = False
    state.death_reason = ""

    # Return to hub
    state.screen = ScreenKind.HUB
    state.status_messages.append(">>> Jacked out. Returning to hub...")
    state.status_messages.append(">>> Inventory lost. Grade preserved.")


def restart_with_new_jockey(state: AppState, new_character_id: str) -> None:
    """Restart with a different jockey (ADR-0040).

    Args:
        state: App state.
        new_character_id: "novice" | "veteran" | "heretic" (must differ from current).

    Raises:
        ValueError: If hardcore_mode is True (1-life permadeath — revival blocked).
    """
    if state.hardcore_mode:
        raise ValueError(
            "Hardcore mode (1-life permadeath): restart_with_new_jockey blocked. "
            "Caller must route player to MENU."
        )

    if new_character_id == state.character_id:
        # Same character — use jack_out_to_hub
        jack_out_to_hub(state)
        return

    # Reset character
    state.character_id = new_character_id
    state.player_grade = 1  # New jockey starts at grade 1
    state.player_hp = state.player_max_hp if state.player_max_hp > 0 else 100
    state.player_ppl = 0
    state.inventory = {}
    from ..equipment.equipment import EquipmentLoadout

    state.equipment_loadout = EquipmentLoadout()
    state.completed_missions = set()
    state.mission_progress = {}

    # Clear matrix
    state.matrix = None
    state.current_node_id = None
    state.exploration = None
    state.combat_state = None
    state.action_menu_open = False

    # Clear chapter/graphic novel state
    state.chapter_id = f"chapter_{new_character_id}"
    state.chapter_progress = 0.0
    state.chapter_elapsed_ms = 0.0
    state.chapter_typed_chars = 0

    # Reset run state to PENDING (new run)
    if state.run_state is not None:
        state.run_state.reset(mission_id="first_jack")

    # Player is alive
    state.is_dead = False
    state.death_reason = ""
    state.death_cause = ""

    # Go to character select first
    state.screen = ScreenKind.CHARACTER_SELECT
    state.status_messages.append(f">>> New jockey: {_char_label(new_character_id)}")
    state.status_messages.append(">>> Sprawl has a fresh face. Pick your poison.")


def render_death_screen(
    console: tcod.console.Console,
    state: AppState,
) -> None:
    """Render the flatline (death) screen.

    Shows the X head (jockey avatar flatline state) and recovery options.
    """
    from ..avatar import build_avatar_state
    from ..avatar.renderer import render_avatar_lines
    from . import config as _engine_config

    SCREEN_WIDTH = _engine_config.SCREEN_WIDTH  # noqa: N806
    SCREEN_HEIGHT = _engine_config.SCREEN_HEIGHT  # noqa: N806

    console.clear(bg=(0, 0, 0))

    if state.hardcore_mode:
        title = "PERMANENT DEATH"
        title_fg = (200, 30, 30)
        subtitle = "1-life permadeath. No revival."
    else:
        title = "FLATLINE"
        title_fg = (140, 0, 0)
        subtitle = "Static. Silence."

    console.print(
        x=(SCREEN_WIDTH - len(title)) // 2,
        y=4,
        string=title,
        fg=title_fg,
    )
    console.print(
        x=(SCREEN_WIDTH - len(subtitle)) // 2,
        y=5,
        string=subtitle,
        fg=(80, 80, 80),
    )

    # Avatar (X head, flatline state)
    avatar_state = build_avatar_state(
        hp=0,
        max_hp=state.player_max_hp if state.player_max_hp > 0 else 100,
        ppl=state.player_ppl if state.player_ppl > 0 else 5,
        zdr=99,  # Always deadly
        deck_tier=3,
        wetware_tier=3,
        construct_id=None,  # Construct disappears at death
    )
    rendered = render_avatar_lines(avatar_state)
    avatar_x = (SCREEN_WIDTH - rendered.width) // 2
    avatar_y = 8
    # Frame
    console.print(
        x=avatar_x - 1,
        y=avatar_y - 1,
        string="=" * (rendered.width + 2),
        fg=(140, 0, 0),
    )
    for i, (text, color) in enumerate(rendered.lines):
        console.print(
            x=avatar_x,
            y=avatar_y + i,
            string=text,
            fg=color,
        )
    console.print(
        x=avatar_x - 1,
        y=avatar_y + len(rendered.lines),
        string="=" * (rendered.width + 2),
        fg=(140, 0, 0),
    )

    # Death reason
    reason_text = f"Cause: {state.death_reason}"
    console.print(
        x=(SCREEN_WIDTH - len(reason_text)) // 2,
        y=avatar_y + len(rendered.lines) + 3,
        string=reason_text,
        fg=(180, 80, 80),
    )

    # Options
    if state.hardcore_mode:
        option1 = "[ENTER] Return to Menu"
        option1_fg = (200, 200, 200)
    else:
        option1 = "[ENTER] Continue — See Summary"
        option1_fg = (200, 200, 200)
    option2 = "[Q] Quit Game"
    console.print(
        x=(SCREEN_WIDTH - len(option1)) // 2,
        y=SCREEN_HEIGHT // 2 + 6,
        string=option1,
        fg=option1_fg,
    )
    console.print(
        x=(SCREEN_WIDTH - len(option2)) // 2,
        y=SCREEN_HEIGHT // 2 + 8,
        string=option2,
        fg=(100, 100, 100),
    )

    # Volume indicator (bottom)
    vol_pct = int(get_volume() * 100)
    console.print(
        x=2,
        y=SCREEN_HEIGHT - 2,
        string=f"[M] mute  [+/-] vol: {vol_pct}%",
        fg=(80, 80, 80),
    )


def render_death_summary_screen(
    console: tcod.console.Console,
    state: AppState,
    width: int = 80,
    height: int = 30,
) -> None:
    """Render the DEATH_SUMMARY screen (ADR-0040).

    Shows the deceased jockey's final report + Sprawl's epitaph +
    3 restart options.
    """
    console.clear()

    # Find the most recent jockey
    history = _get_history()
    recent = history.recent(1)
    jockey: DeceasedJockey | None = recent[0] if recent else None

    # Top bar
    console.print(0, 0, "═" * width)
    title = "FLATLINE" if not jockey else "> FLATLINE <"
    console.print((width - len(title)) // 2, 0, f" {title} ")
    console.print(0, 1, "─" * width)

    if jockey is None:
        # Fallback if no jockey found
        console.print(2, 3, "(Jockey archive not available)")
        console.print(0, height - 4, "─" * width)
        opts = [
            "[1] HUB",
            "[2] 메인메뉴" if state.character_id == "novice" else "[2] Main menu",
        ]
        for i, opt in enumerate(opts):
            console.print(2, height - 3 + i, opt)
        return

    # Render summary lines (default Korean; en/ko toggle via state)
    summary_lines = render_death_summary_lines(jockey, lang="ko")
    y = 3
    for line in summary_lines:
        if y >= height - 8:
            break
        console.print(2, y, line)
        y += 1

    # Bottom options
    console.print(0, height - 8, "─" * width)
    opts = [
        "[1] 새 자키 (다른 자키 선택)",
        "[2] 같은 자키 (HUB로)",
        "[3] Hall of Dead Jockeys",
        "[4] 메인메뉴",
    ]
    for i, opt in enumerate(opts):
        console.print(2, height - 7 + i, opt)


def render_hall_of_dead_screen(
    console: tcod.console.Console,
    state: AppState,
    width: int = 80,
    height: int = 30,
) -> None:
    """Render the HALL_OF_DEAD screen (ADR-0040).

    Shows the archive of deceased jockeys.
    """
    from wet_run.i18n import Translator  # noqa: F401

    console.clear()
    history = _get_history()
    selected = state.hall_of_dead_selected

    # Top bar
    console.print(0, 0, "═" * width)
    console.print(0, 1, "─" * width)

    lines = render_hall_of_dead_lines(history, selected=selected, lang="ko")
    y = 2
    for line in lines:
        if y >= height - 3:
            break
        console.print(2, y, line)
        y += 1

    # Footer
    console.print(0, height - 3, "─" * width)
    console.print(
        2,
        height - 2,
        "[↑/↓] navigate   [ENTER] detail   [ESC] back",
    )


def handle_death_input(
    event: tcod.event.Event,
    state: AppState,
) -> bool:
    """Handle input on the death screen. Returns False to quit.

    ADR-0040: ENTER advances to DEATH_SUMMARY.
    Hardcore mode (1-life permadeath): ENTER routes to MENU instead — no revival.
    """
    import tcod.event

    if not isinstance(event, tcod.event.KeyDown):
        return True

    if event.sym is tcod.event.KeySym.Q:
        return False

    if event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.SPACE, tcod.event.KeySym.KP_ENTER):
        if state.hardcore_mode:
            state.screen = ScreenKind.MENU
            state.is_dead = False
            state.death_reason = ""
            state.death_cause = ""
            state.status_messages.append(">>> HARDCORE MODE: 1-life permadeath. No revival.")
            return True
        advance_to_death_summary(state)
        return True

    if event.sym is tcod.event.KeySym.M:
        muted = _sm_module.toggle_mute()
        label = "MUTED" if muted else "UNMUTED"
        state.status_messages.append(f">>> Audio {label}")
        return True

    # Volume controls
    if event.sym in (tcod.event.KeySym.EQUALS, tcod.event.KeySym.PLUS, tcod.event.KeySym.KP_PLUS):
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

    return True


def handle_death_summary_input(
    event: tcod.event.Event,
    state: AppState,
) -> bool:
    """Handle input on DEATH_SUMMARY screen.

    N1=new jockey, N2=same jockey, N3=hall of dead, N4/ESC/Q=menu.
    """
    import tcod.event

    if isinstance(event, tcod.event.KeyDown):
        if event.sym is tcod.event.KeySym.N1:
            handle_death_summary_choice(state, "new_jockey")
            return True
        if event.sym is tcod.event.KeySym.N2:
            handle_death_summary_choice(state, "same_jockey")
            return True
        if event.sym is tcod.event.KeySym.N3:
            handle_death_summary_choice(state, "hall_of_dead")
            return True
        if event.sym in (tcod.event.KeySym.N4, tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
            handle_death_summary_choice(state, "menu")
            return True
    return True


def handle_hall_of_dead_input(
    event: tcod.event.Event,
    state: AppState,
) -> bool:
    """Handle input on HALL_OF_DEAD screen.

    Arrow keys (↑↓) or K/J navigate; Enter/Space shows detail; ESC/Q returns to DEATH_SUMMARY.
    """
    import tcod.event

    if isinstance(event, tcod.event.KeyDown):
        if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
            state.screen = ScreenKind.DEATH_SUMMARY
            return True
        if event.sym in (tcod.event.KeySym.UP, tcod.event.KeySym.K):
            state.hall_of_dead_selected = max(0, state.hall_of_dead_selected - 1)
            return True
        if event.sym in (tcod.event.KeySym.DOWN, tcod.event.KeySym.J):
            state.hall_of_dead_selected += 1
            return True
        if event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.SPACE):
            return True
    return True


def handle_death_summary_choice(
    state: AppState,
    choice: str,
) -> None:
    """Apply the player's choice from DEATH_SUMMARY.

    Args:
        state: App state.
        choice: "new_jockey" | "same_jockey" | "hall_of_dead" | "menu"

    Hardcore mode (1-life permadeath): "new_jockey" and "same_jockey" choices
    are routed to MENU instead of attempting restart (which would raise).
    "hall_of_dead" and "menu" remain available.
    """
    if state.hardcore_mode and choice in ("new_jockey", "same_jockey"):
        state.status_messages.append(">>> HARDCORE MODE: 1-life permadeath. No revival.")
        state.screen = ScreenKind.MENU
        state.is_dead = False
        state.death_reason = ""
        state.death_cause = ""
        return

    if choice == "new_jockey":
        # Pick a different character (any of the 3, not the current one)
        available = [c for c in ("novice", "veteran", "heretic") if c != state.character_id]
        if available:
            # Default to first non-current
            new_char = available[0]
            restart_with_new_jockey(state, new_char)
        else:
            # All 3 same (shouldn't happen) — fall back to HUB
            jack_out_to_hub(state)
    elif choice == "same_jockey":
        jack_out_to_hub(state)
    elif choice == "hall_of_dead":
        state.screen = ScreenKind.HALL_OF_DEAD
        state.hall_of_dead_selected = 0
    elif choice == "menu":
        state.screen = ScreenKind.MENU
        state.is_dead = False
        state.death_reason = ""
        state.death_cause = ""
