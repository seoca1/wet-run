"""CYBERSPACE_MAP screen — World/Sector/Server tree view.

Phase D-2: extracted from app.py to reduce main dispatcher size.
"""

from __future__ import annotations

import tcod.console

from ..combat.palette import (
    DEFAULT_COLOR,
    GRAY_BLACK,
    GRAY_MID,
    GRAY_MID_LIGHT,
    ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR,
    OLIVE,
)
from .state import AppState


def render_cyberspace_map(console: tcod.console.Console, state: AppState) -> None:
    """Render CYBERSPACE_MAP as a tree view of worlds/sectors/servers."""
    console.clear(bg=GRAY_BLACK)
    width = console.width

    title = "CYBERSPACE — World Map"
    console.print(0, 0, "═" * width)
    console.print((width - len(title)) // 2, 0, f" {title} ")
    console.print(0, 1, "─" * width)

    wm = state.world_map
    if wm is None:
        return

    y = 3
    for world_id, world in wm.worlds.items():
        marker = "▸ " if world_id == wm.current_world else "  "
        console.print(
            x=2, y=y, string=f"{marker}WORLD: {world.name}", fg=ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR
        )
        y += 1
        for sector_id, sector in world.sectors.items():
            s_marker = "→ " if sector_id == wm.current_sector else "  "
            server_count = len(sector.servers)
            console.print(
                x=6,
                y=y,
                string=f"{s_marker}SECTOR: {sector.name} [{server_count} servers]",
                fg=OLIVE,
            )
            y += 1
            for server in sector.servers[:5]:
                sv_marker = "• " if server.id == wm.current_server else "  "
                console.print(x=10, y=y, string=f"{sv_marker}{server.name}", fg=DEFAULT_COLOR)
                y += 1
            if len(sector.servers) > 5:
                console.print(
                    x=10,
                    y=y,
                    string=f"  ... and {len(sector.servers) - 5} more",
                    fg=GRAY_MID,
                )
                y += 1
        y += 1

    console.print(0, console.height - 1, "═" * width)
    console.print(x=2, y=console.height - 1, string="[ESC] Back to Hub", fg=GRAY_MID_LIGHT)
