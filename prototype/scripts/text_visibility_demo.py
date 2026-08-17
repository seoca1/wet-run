"""Text Visibility Demo (ADR-0047).

Visualizes all the text visibility improvements:
    Scene 1: Before/After — Footer + Side Panel message styling
    Scene 2: All 8 MessageKind categories with icons + colors
    Scene 3: GN prose body — new cream-white color
    Scene 4: Combined — full matrix screen with messages + log

Run:
    uv run python scripts/text_visibility_demo.py
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import tcod.console

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine.layout import (  # noqa: E402
    Region,
    RegionId,
    draw_footer,
    draw_message_log,
    draw_title,
    make_shell,
)
from wet_run.engine.matrix_view import (  # noqa: E402
    _last_layout,
    render_matrix,
)
from wet_run.engine.state import AppState  # noqa: E402
from wet_run.engine.status_message import (  # noqa: E402
    MESSAGE_STYLE,
    MessageKind,
    StatusMessage,
)
from wet_run.i18n import Translator  # noqa: E402
from wet_run.matrix import Edge  # noqa: E402
from wet_run.matrix.graph import MatrixGraph  # noqa: E402
from wet_run.matrix.node import (  # noqa: E402
    AlarmLevel,
    Faction,
    IceKind,
    Node,
    NodeKind,
    ZoneDepth,
)

SCREEN_W = 80
SCREEN_H = 50


def _console_to_text(console: tcod.console.Console) -> str:
    """Convert tcod console to plain text."""
    lines = []
    for y in range(console.height):
        chars = []
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
    scene: str,
    narration: str,
) -> None:
    if clear:
        sys.stdout.write("\033[2J\033[H")
    sys.stdout.write(_console_to_text(console))
    sys.stdout.write("\n")
    sys.stdout.write(f"[Step {step:03d}  T+{elapsed:5.1f}s  Scene: {scene}]\n")
    if narration:
        sys.stdout.write(f"> {narration}\n")
    sys.stdout.flush()


def make_demo_matrix() -> MatrixGraph:
    """3x3 grid with diagonal edges for movement demo."""
    nodes = []
    for y in range(3):
        for x in range(3):
            nodes.append(
                Node(
                    id=f"n_{x}_{y}",
                    kind=NodeKind.DATA if (x + y) % 2 == 0 else NodeKind.ICE,
                    label=f"N{x}{y}",
                    zone=ZoneDepth.SURFACE,
                    ice=IceKind.STANDARD if (x + y) % 2 == 1 else IceKind.NONE,
                    alarm=AlarmLevel.LOW,
                    faction=Faction.NONE,
                )
            )
    edges = []
    for y in range(3):
        for x in range(2):
            edges.append(Edge(src=f"n_{x}_{y}", dst=f"n_{x + 1}_{y}"))
            edges.append(Edge(src=f"n_{x + 1}_{y}", dst=f"n_{x}_{y}"))
    for y in range(2):
        for x in range(3):
            edges.append(Edge(src=f"n_{x}_{y}", dst=f"n_{x}_{y + 1}"))
            edges.append(Edge(src=f"n_{x}_{y + 1}", dst=f"n_{x}_{y}"))
    for x in range(2):
        for y in range(2):
            edges.append(Edge(src=f"n_{x}_{y}", dst=f"n_{x + 1}_{y + 1}"))
            edges.append(Edge(src=f"n_{x + 1}_{y + 1}", dst=f"n_{x}_{y}"))
    return MatrixGraph(nodes=tuple(nodes), edges=tuple(edges), entry_id="n_1_1")


# ============================================================================
# Scene 1: BEFORE vs AFTER — Footer message styling
# ============================================================================


def render_scene1_footer_comparison(console: tcod.console.Console) -> None:
    """Show OLD vs NEW footer rendering side by side."""
    console.clear()
    # Title
    draw_title(
        console,
        make_shell()[RegionId.TITLE],
        title="SCENE 1 — Footer styling: BEFORE vs AFTER",
        subtitle="ADR-0047: typed messages with icons + colors + bg highlights",
    )

    # Split console into top half (before) and bottom half (after)
    y_mid = 24
    console.print(x=2, y=y_mid - 1, string="═" * 76, fg=(120, 120, 120))

    # ---- BEFORE (top half) ----
    console.print(x=2, y=4, string="▼ BEFORE — flat gray, no icon, no category", fg=(200, 200, 200))
    region_top = Region(RegionId.FOOTER, x=0, y=20, w=SCREEN_W, h=1)
    draw_footer(
        console,
        region_top,
        "Step 12  T+0.5s",
        [">>> EXTRACT: Got data fragment"],
        use_styled=False,
    )
    region_top2 = Region(RegionId.FOOTER, x=0, y=22, w=SCREEN_W, h=1)
    draw_footer(
        console,
        region_top2,
        "Step 13  T+0.6s",
        [">>> WARNING: Low HP — incoming ICE detected in adjacent node"],
        use_styled=False,
    )

    # ---- AFTER (bottom half) ----
    console.print(
        x=2,
        y=26,
        string="▼ AFTER — typed message, icons, colors, bg highlight on warning",
        fg=(200, 200, 200),
    )

    # Build typed messages
    msgs = [
        StatusMessage(text="EXTRACT: Got data fragment", kind=MessageKind.SUCCESS),
        StatusMessage(text="WARNING: Low HP — incoming ICE detected", kind=MessageKind.WARNING),
        StatusMessage(text="MOVE: passed through → n_0_1", kind=MessageKind.MOVEMENT),
        StatusMessage(text="ERROR: Jack-out failed — connection lost", kind=MessageKind.ERROR),
    ]

    region_bot = Region(RegionId.FOOTER, x=0, y=42, w=SCREEN_W, h=1)
    draw_footer(console, region_bot, "Step 12  T+0.5s", [msgs[0].text], use_styled=True)
    region_bot2 = Region(RegionId.FOOTER, x=0, y=44, w=SCREEN_W, h=1)
    draw_footer(console, region_bot2, "Step 13  T+0.6s", [msgs[1].text], use_styled=True)
    region_bot3 = Region(RegionId.FOOTER, x=0, y=46, w=SCREEN_W, h=1)
    draw_footer(console, region_bot3, "Step 14  T+0.7s", [msgs[2].text], use_styled=True)
    region_bot4 = Region(RegionId.FOOTER, x=0, y=48, w=SCREEN_W, h=1)
    draw_footer(console, region_bot4, "Step 15  T+0.8s", [msgs[3].text], use_styled=True)


# ============================================================================
# Scene 2: All 8 MessageKind — color/icon showcase
# ============================================================================


def render_scene2_kind_showcase(console: tcod.console.Console) -> None:
    """Display all 8 MessageKind with their icons, colors, and example text."""
    console.clear()
    draw_title(
        console,
        make_shell()[RegionId.TITLE],
        title="SCENE 2 — All 8 MessageKind categories",
        subtitle="Icons + foreground colors (warning/error also have background highlight)",
    )

    examples = [
        ("DEBUG", "Tick 100: combat frame processed"),
        ("INFO", "Welcome to the Freeside arcology, jockey."),
        ("MOVEMENT", "MOVE: passed through N00 → N10"),
        ("DIALOG", "“The sky above the port was the color of television…”"),
        ("COMBAT", "⚔ Hit ICE Standard for 12 damage!"),
        ("SUCCESS", "Gained: 1x Data Fragment"),
        ("WARNING", "Low HP — incoming ICE in adjacent node"),
        ("ERROR", "Jack-out failed: connection lost. Flatline imminent."),
    ]

    y = 4
    console.print(
        x=2,
        y=y,
        string=f"{'Kind':<10} {'Icon':<6} {'FG':<14} {'BG':<8} {'Example message'}",
        fg=(200, 200, 200),
    )
    y += 1
    console.print(x=2, y=y, string="─" * 76, fg=(80, 80, 80))
    y += 1

    for name, text in examples:
        kind = MessageKind[name]
        icon, fg, bg = MESSAGE_STYLE[kind]
        bg_str = "yes" if bg else "-"
        console.print(x=2, y=y, string=f"{name:<10} ", fg=(180, 180, 180))
        console.print(x=13, y=y, string=f"{icon:<6}", fg=fg)
        console.print(x=20, y=y, string=f"({fg[0]:>3},{fg[1]:>3},{fg[2]:>3})", fg=fg)
        console.print(x=34, y=y, string=f"{bg_str:<8}", fg=fg)

        # Render the actual example message with styling
        msg = StatusMessage(text=text, kind=kind)
        x = 44
        if bg:
            for i, ch in enumerate(msg.prefix):
                console.print(x=x + i, y=y, string=ch, fg=fg, bg=bg)
        else:
            console.print(x=x, y=y, string=msg.prefix, fg=fg)
        y += 2

    # Color legend
    y += 2
    console.print(x=2, y=y, string="Colors used (terminal-dependent):", fg=(180, 180, 180))
    y += 1
    legend = [
        ("▸ Info", "(200, 200, 200)", "default — neutral"),
        ("→ Move", "(160, 200, 255)", "calm blue — direction"),
        ("✓ Success", "(100, 230, 130)", "green — good"),
        ("⚠ Warning", "(255, 220, 100)", "yellow + bg highlight"),
        ("✗ Error", "(255, 100, 100)", "red + bg highlight"),
    ]
    for name, color, desc in legend:
        console.print(x=4, y=y, string=f"{name:<12} {color:<18} {desc}", fg=(160, 160, 160))
        y += 1


# ============================================================================
# Scene 3: GN prose body — new cream color
# ============================================================================


def render_scene3_gn_prose(console: tcod.console.Console) -> None:
    """Show GN prose with new cream color + speaker heading."""
    from wet_run.engine.graphic_novel_view import _parse_scene

    console.clear()
    draw_title(
        console,
        make_shell()[RegionId.TITLE],
        title="SCENE 3 — GN prose body (new cream color)",
        subtitle="ADR-0047: prose_fg = (232, 230, 220) for readability",
    )

    # Load a real scene
    scene_path = Path(__file__).parent.parent / "data" / "scenes" / "kas" / "04_wheel.json"
    import json

    with scene_path.open(encoding="utf-8") as f:
        sd = _parse_scene(json.load(f))

    # Reveal full first dialogue
    console.clear()
    console.print(x=2, y=2, string="[1/4]  THE WHEEL  ·  HERETIC", fg=(255, 255, 0))
    console.print(x=2, y=3, string="─" * 76, fg=(80, 80, 80))

    # Speaker heading
    heading_y = 4
    heading = "── kumiko ──"
    console.print((SCREEN_W - len(heading)) // 2, heading_y, heading, fg=(255, 200, 100))

    # Prose body (force full reveal by setting typed_chars to text length)
    text = sd.dialogue[0].text_en
    body_y = 6
    body_bottom = SCREEN_H - 4
    from wet_run.engine.graphic_novel_view import NOVEL_LEFT_MARGIN, NOVEL_RIGHT_MARGIN

    body_width = SCREEN_W - NOVEL_LEFT_MARGIN - NOVEL_RIGHT_MARGIN
    prose_fg = (232, 230, 220)  # The new color!

    # Naive word wrap
    words = text.split(" ")
    current = ""
    y = body_y
    for word in words:
        test = (current + " " + word).strip()
        if len(test) > body_width:
            if current:
                for col, ch in enumerate(current.ljust(body_width)):
                    console.print(NOVEL_LEFT_MARGIN + col, y, ch, fg=prose_fg)
                y += 1
                if y >= body_bottom:
                    break
            current = word
        else:
            current = test
    if current and y < body_bottom:
        for col, ch in enumerate(current.ljust(body_width)):
            console.print(NOVEL_LEFT_MARGIN + col, y, ch, fg=prose_fg)

    # Show comparison note at bottom
    console.print(
        x=2,
        y=SCREEN_H - 2,
        string="Previous (default): white #ffffff (eye strain on dark bg)  →  New: cream #e8e6dc (warmer, easier on eyes)",
        fg=(160, 160, 160),
    )


# ============================================================================
# Scene 4: Combined — full matrix screen with messages
# ============================================================================


def render_scene4_combined(console: tcod.console.Console) -> None:
    """Show full matrix view with status messages + log."""
    console.clear()
    state = AppState()
    matrix = make_demo_matrix()
    state.matrix = matrix
    state.current_node_id = "n_1_1"
    state.status_messages.extend(
        [
            ">>> EXTRACT: Got data fragment from N11",
            ">>> Move: passed through → n_1_0",
            ">>> SCAN: data node N00 detected",
            ">>> WARNING: Black ICE detected in adjacent zone",
            ">>> ENGAGE: Initiating combat with N22",
            ">>> COMBAT: Hit ICE Standard for 18 damage!",
            ">>> SUCCESS: ICE Standard defeated!",
            ">>> Move: passed through → n_2_2",
            ">>> EXTRACT: Got Tessier-Ashpool payroll fragment",
            ">>> WARNING: Incoming ICE patrol detected",
        ]
    )

    tr = Translator("en", data_dir=Path(__file__).parent.parent / "data" / "i18n")
    render_matrix(console, tr, state, _last_layout.get(matrix, {}))

    # Add a log overlay in the SIDE panel
    shell = make_shell()
    log_region = Region(
        RegionId.SIDE,
        x=0,
        y=shell[RegionId.SIDE].y + 1,
        w=SCREEN_W,
        h=3,
    )
    draw_message_log(console, log_region, state.status_messages[-3:])


# ============================================================================
# Main
# ============================================================================


SCENES = [
    ("Scene 1 — Footer styling: BEFORE vs AFTER", render_scene1_footer_comparison),
    ("Scene 2 — All 8 MessageKind categories", render_scene2_kind_showcase),
    ("Scene 3 — GN prose body (new cream color)", render_scene3_gn_prose),
    ("Scene 4 — Full matrix + message log", render_scene4_combined),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--step-delay", type=float, default=2.0, help="Seconds per scene")
    parser.add_argument("--no-clear", action="store_true", help="Don't clear between scenes")
    parser.add_argument(
        "--only",
        type=int,
        choices=[1, 2, 3, 4],
        help="Show only one scene (1-4)",
    )
    args = parser.parse_args()

    scenes_to_show = [SCENES[args.only - 1]] if args.only else SCENES

    console = tcod.console.Console(SCREEN_W, SCREEN_H, order="F")
    start = time.monotonic()
    step = 0
    for title, renderer in scenes_to_show:
        renderer(console)
        elapsed = time.monotonic() - start
        _print_frame(
            console,
            clear=not args.no_clear,
            step=step,
            elapsed=elapsed,
            scene=title,
            narration=f"ADR-0047 text visibility improvements ({title})",
        )
        step += 1
        time.sleep(args.step_delay)

    sys.stdout.write(
        f"\n=== Text Visibility Demo complete: {step} scenes in {time.monotonic() - start:.1f}s ===\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
