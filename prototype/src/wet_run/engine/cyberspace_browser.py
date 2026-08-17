"""Cyberspace Browser: select world, sector, and server to jack into.

Two-level UI:
  1. Top: Browse worlds and sectors
  2. Bottom: Browse servers in selected sector
  3. ENTER: Jack into selected server
"""

from __future__ import annotations

from typing import Any

import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym

from ..audio import safe_play
from ..cyberspace.world import Sector, Server, World, WorldMap
from ..i18n import Translator
from .layout import (
    Region,
    RegionId,
    clear_region,
    draw_controls,
    draw_dividers,
    draw_footer,
    draw_title,
    make_shell,
)
from .state import AppState, ScreenKind
from .status_panel import render_status_panel


def render_cyberspace_browser(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
) -> None:
    """Render the cyberspace browser (world/sector/server selection)."""
    if not hasattr(state, "world_map") or state.world_map is None:
        return

    shell = make_shell()
    title_r = shell[RegionId.TITLE]
    main_r = shell[RegionId.MAIN]
    ctrl_r = shell[RegionId.CONTROLS]
    foot_r = shell[RegionId.FOOTER]
    panel_r = shell[RegionId.STATUS_PANEL]

    # Clear
    for r in shell.values():
        clear_region(console, r)
    draw_dividers(console, shell)

    render_status_panel(console, state, panel_r)

    # Title
    title = "CYBERSPACE — Select Target"
    subtitle = "Choose a server to jack into"
    draw_title(console, title_r, title=title, subtitle=subtitle)

    # Main: render world/sector/server hierarchy
    _render_browser(console, main_r, state)

    # Controls
    draw_controls(
        console,
        ctrl_r,
        lines=[
            "↑↓ Servers  ←→ Sectors  PgUp/PgDn Worlds  ENTER Jack In",
            "ESC Back to Hub  Q Quit",
        ],
    )

    # Footer
    draw_footer(
        console,
        foot_r,
        text=f"Step {state.demo_step}  T+{state.demo_elapsed_s:.1f}s",
        status_messages=state.status_messages,
    )


def _render_browser(console: tcod.console.Console, main: Region, state: AppState) -> None:
    """Render the world/sector/server browser."""
    wm = state.world_map
    if wm is None:
        return

    top_h = main.h // 2 - 2
    y = _render_browser_worlds(console, main, wm)
    _render_browser_servers(console, main, state, wm, top_h, y)


# ------------------------------------------------------------------
# _render_browser helpers
# ------------------------------------------------------------------


def _render_browser_worlds(console: tcod.console.Console, main: Region, wm: Any) -> int:
    """Render the world/sector tree in the top half of the browser.

    Returns the y-row just past the world tree.
    """
    y = main.y + 1
    bar = "=" * (main.w - 4)
    console.print(x=main.x + 2, y=y, string=bar, fg=(0, 200, 200))
    y += 1
    console.print(x=main.x + 2, y=y, string=" WORLDS & SECTORS", fg=(0, 255, 255))
    y += 1
    console.print(x=main.x + 2, y=y, string=bar, fg=(0, 200, 200))
    y += 1

    current_world = wm.current_world
    for world in wm.worlds.values():
        is_current_world = world.id is current_world
        world_fg = (255, 255, 0) if is_current_world else (180, 180, 180)
        world_marker = "\u25b6" if is_current_world else " "
        console.print(
            x=main.x + 2,
            y=y,
            string=f"{world_marker} [{world.id.value}] {world.name}",
            fg=world_fg,
        )
        y += 1
        console.print(
            x=main.x + 4,
            y=y,
            string=f"   {world.description[: main.w - 8]}",
            fg=(120, 120, 120),
        )
        y += 1

        current_sector = wm.current_sector
        for sector in world.sectors.values():
            is_current_sector = (
                is_current_world and current_sector is not None and sector.id is current_sector
            )
            sector_marker = "\u2192" if is_current_sector else " "
            sector_fg = (0, 255, 255) if is_current_sector else (150, 150, 150)
            console.print(
                x=main.x + 4,
                y=y,
                string=f"   {sector_marker} {sector.name} ({len(sector.servers)} servers)",
                fg=sector_fg,
            )
            y += 1

        y += 1  # Space between worlds
    return y


def _render_browser_servers(
    console: tcod.console.Console, main: Region, state: AppState, wm: Any, top_h: int, y: int
) -> None:
    """Render the server list in the bottom half of the browser."""
    y = main.y + top_h + 2
    sep = "-" * (main.w - 4)
    console.print(x=main.x + 2, y=y, string=sep, fg=(80, 80, 80))
    y += 1

    current_sector_obj = wm.get_current_sector()
    if current_sector_obj is None:
        return

    console.print(
        x=main.x + 2,
        y=y,
        string=f" SERVERS in {current_sector_obj.name}:",
        fg=(0, 255, 255),
    )
    y += 1
    console.print(x=main.x + 2, y=y, string=sep, fg=(80, 80, 80))
    y += 1

    for i, server in enumerate(current_sector_obj.servers):
        is_selected = i == state.selected_server_index
        marker = "\u25b6" if is_selected else " "
        if is_selected:
            fg = (255, 255, 0)
        elif server.mission_id is not None:
            fg = (255, 215, 0)
        else:
            fg = (180, 180, 180)

        mission_marker = " \u2605" if server.mission_id else "  "
        line = f"{marker}{mission_marker} {server.name} (Diff: {server.difficulty})"
        console.print(
            x=main.x + 2,
            y=y + i,
            string=line[: main.w - 4],
            fg=fg,
        )


def handle_browser_input(
    event: tcod.event.Event,
    state: AppState,
) -> bool:
    """Handle input on the cyberspace browser."""
    if not isinstance(event, KeyDown):
        return True

    if event.sym is KeySym.Q:
        return False
    if event.sym is KeySym.ESCAPE:
        state.screen = ScreenKind.HUB
        return True

    wm = state.world_map
    if wm is None:
        return True

    # Navigation in server list
    current_sector = wm.get_current_sector()
    if current_sector is None or not current_sector.servers:
        return True

    n_servers = len(current_sector.servers)

    if event.sym is KeySym.UP:
        state.selected_server_index = max(0, state.selected_server_index - 1)
        return True

    if event.sym is KeySym.DOWN:
        state.selected_server_index = min(n_servers - 1, state.selected_server_index + 1)
        return True

    # Switch world/sector with LEFT/RIGHT (cycles (world, sector) pairs)
    if event.sym is KeySym.LEFT or event.sym is KeySym.RIGHT:
        _cycle_sector(wm, event.sym)
        # Reset server index to 0 and clamp to new sector's server count
        new_sector = wm.get_current_sector()
        if new_sector is not None and new_sector.servers:
            state.selected_server_index = min(
                state.selected_server_index, len(new_sector.servers) - 1
            )
        else:
            state.selected_server_index = 0
        return True

    # Switch world only with PgUp/PgDn or W/S
    if event.sym in (KeySym.PAGEUP, KeySym.PAGEDOWN, KeySym.W, KeySym.S):
        _cycle_world(wm, event.sym)
        new_sector = wm.get_current_sector()
        if new_sector is not None and new_sector.servers:
            state.selected_server_index = min(
                state.selected_server_index, len(new_sector.servers) - 1
            )
        else:
            state.selected_server_index = 0
        return True

    # ENTER to jack into selected server
    if event.sym in (KeySym.RETURN, KeySym.KP_ENTER, KeySym.SPACE):
        if current_sector.servers:
            idx = max(0, min(state.selected_server_index, len(current_sector.servers) - 1))
            _jack_into_server(state, current_sector.servers[idx])
        return True

    return True


def _cycle_sector(wm: WorldMap, sym: KeySym) -> None:
    """Cycle through available (world, sector) pairs."""
    if not wm.worlds:
        return

    # Build flat list of (world, sector) pairs
    pairs: list[tuple[World, Sector]] = []
    for w in wm.worlds.values():
        for s in w.sectors.values():
            pairs.append((w, s))

    if not pairs:
        return

    # Find current index
    current_idx = 0
    for i, (w, s) in enumerate(pairs):
        if w.id is wm.current_world and s.id is wm.current_sector:
            current_idx = i
            break

    # Move
    if sym is KeySym.RIGHT:
        new_idx = (current_idx + 1) % len(pairs)
    else:
        new_idx = (current_idx - 1) % len(pairs)

    new_world, new_sector = pairs[new_idx]

    # Actually update the world map
    wm.set_location(new_world.id, new_sector.id, None)


def _cycle_world(wm: WorldMap, sym: KeySym) -> None:
    """Cycle through worlds (skipping sectors within each world)."""
    if not wm.worlds:
        return

    world_list = list(wm.worlds.values())
    if not world_list:
        return

    current_idx = 0
    for i, w in enumerate(world_list):
        if w.id is wm.current_world:
            current_idx = i
            break

    if sym is KeySym.PAGEUP or sym is KeySym.W:
        new_idx = (current_idx - 1) % len(world_list)
    else:
        new_idx = (current_idx + 1) % len(world_list)

    new_world = world_list[new_idx]
    # Pick first sector of new world
    first_sector = next(iter(new_world.sectors.values()), None)
    if first_sector is not None:
        wm.set_location(new_world.id, first_sector.id, None)


def _jack_into_server(state: AppState, server: Server) -> None:
    """Jack into a server, generating its subgraph."""
    from ..cyberspace.server_generator import ServerSubgraphGenerator

    # Play jack-in sound
    safe_play("movement/jack_in")

    # Generate server's subgraph
    gen = ServerSubgraphGenerator()
    seed = hash(server.id) & 0xFFFFFFFF
    graph, layouts = gen.generate(seed=seed, difficulty=server.difficulty)

    # Set state
    state.matrix = graph
    state.current_node_id = graph.entry_id
    # Save layouts so cyberspace_view can render and the demo can navigate
    state.cyberspace_layouts = dict(layouts)

    # Set world map
    wm = state.world_map
    if wm is not None:
        wm.current_server = server.id

    state.in_server_browser = False
    state.screen = ScreenKind.MATRIX
    state.status_messages.append(f">>> Jacked into {server.name}")
    state.status_messages.append(f">>> Difficulty: {server.difficulty}")

    # Trigger entry event (chiba city intro) on first jack-in
    _check_entry_event(state)


def _check_entry_event(state: AppState) -> None:
    """Check if an entry event should trigger on jack-in."""
    from .event_story import (
        EventRegistry,
        EventState,
        EventTrigger,
        check_event_trigger,
    )

    if not hasattr(state, "_event_registry") or state._event_registry is None:
        state._event_registry = EventRegistry()

    event = check_event_trigger(
        state,
        registry=state._event_registry,
        trigger=EventTrigger.NODE_ENTER,
        trigger_id="entry",
    )
    if event is not None:
        state.active_event = EventState(event=event)
        state.screen = ScreenKind.EVENT
