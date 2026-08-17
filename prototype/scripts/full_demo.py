#!/usr/bin/env python3
"""Full game flow demo: Prologue → Briefing → Matrix → Combat.

Shows the complete player experience from story to first combat.

Usage:
  uv run python scripts/full_demo.py
  uv run python scripts/full_demo.py --skip-prologue
  uv run python scripts/full_demo.py --fast
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tcod.console
import tcod.context
import tcod.event
import tcod.tileset

from wet_run.combat.registry import IceRegistry, ProgramRegistry
from wet_run.combat.state import step_combat
from wet_run.engine import (
    combat_view,
    config,
    cyberspace_browser,
    hub,
    story_cinematic,
)
from wet_run.engine.state import AppState, ScreenKind
from wet_run.engine.story_cinematic import (
    BRIEFING_FINN_SCENE,
    PROLOGUE_SCENE,
    CinematicState,
)
from wet_run.i18n import Translator
from wet_run.matrix.node import NodeKind
from wet_run.missions import JobBoard


def main() -> int:
    """Run the full demo."""
    parser = argparse.ArgumentParser(description="Full game flow demo")
    parser.add_argument(
        "--skip-prologue",
        action="store_true",
        help="Skip prologue and start at briefing",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast typing speed for all cinematics",
    )
    parser.add_argument(
        "--auto-combat",
        action="store_true",
        help="Auto-play combat (no user input)",
    )
    parser.add_argument(
        "--no-korean",
        action="store_true",
        help="Disable Korean subtitles (English only)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode (player controls everything, no auto-pilot)",
    )
    parser.add_argument(
        "--manual-combat",
        action="store_true",
        help="Manual combat (player uses skills)",
    )
    parser.add_argument(
        "--story-mode",
        action="store_true",
        help="Story-only mode: skip combat, auto-resolve ICE encounters as victories",
    )
    args = parser.parse_args()

    # Default: --auto-combat ON unless --interactive or --manual-combat or --story-mode
    if not args.interactive and not args.manual_combat and not args.story_mode:
        args.auto_combat = True

    # Setup tcod with TTF (Korean-capable) or bitmap font
    if not config.FONT_PATH.exists() and config.find_ttf_font() is None:
        sys.stderr.write("ERROR: No font found (bitmap or TTF)\nRun: make download-font\n")
        return 1

    from wet_run.engine.font_loader import load_font

    tileset, _ = load_font()

    t = Translator(config.DEFAULT_LANGUAGE, data_dir=config.DATA_DIR / "i18n")
    prog_registry = ProgramRegistry.load(config.DATA_DIR / "programs" / "programs.json")
    ice_registry = IceRegistry.load(config.DATA_DIR / "combat" / "ice_types.json")

    state = AppState()
    state.job_board = JobBoard.load(config.DATA_DIR / "missions" / "missions.json")

    # Initialize equipment with starting gear
    from wet_run.equipment.equipment import (
        STARTER_DECK,
        STARTER_HEADWARE,
        EquipmentLoadout,
        EquipmentRegistry,
    )

    equip_reg = EquipmentRegistry.load_default()
    state.equipment_loadout = EquipmentLoadout()
    state.equipment_loadout.equip(equip_reg.get("deck_basic") or STARTER_DECK)
    state.equipment_loadout.equip(equip_reg.get("head_basic") or STARTER_HEADWARE)

    # Start with prologue or skip to briefing
    if args.skip_prologue:
        _start_briefing(state, args.fast, args.no_korean)
    else:
        _start_prologue(state, args.fast, args.no_korean)

    start_time = time.time()

    with tcod.context.new(
        columns=config.SCREEN_WIDTH,
        rows=config.SCREEN_HEIGHT,
        tileset=tileset,
        title=f"{config.SCREEN_TITLE} — Full Demo",
        vsync=True,
    ) as context:
        root_console = tcod.console.Console(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, order="F")

        # Initialize RunState — the single source of truth for what
        # the player should be doing right now.
        from wet_run.run import ensure_run_state

        ensure_run_state(state)

        running = True
        last_combat_step = 0
        last_npc_step = 0
        last_auto_step = 0
        # Track which "stops" we've visited for the tour
        npc_triggered = False
        combat_started = False

        while running:
            elapsed_s = time.time() - start_time
            elapsed_ms = int(elapsed_s * 1000)
            state.demo_elapsed_s = elapsed_s
            state.demo_step += 1

            # Step cinematic (if active)
            if state.screen is ScreenKind.CINEMATIC and state.cinematic_state is not None:
                story_cinematic.step_cinematic(state.cinematic_state, elapsed_ms)

                # Auto-advance to next stage when cinematic finishes
                if state.cinematic_state.finished:
                    _advance_demo_stage(state, prog_registry, ice_registry)

            # Step combat (always progress auto-attacks/regen, regardless of mode)
            if state.screen is ScreenKind.COMBAT and state.combat_state is not None:
                # Auto-step combat every 100ms (auto-attacks, AP regen, etc.)
                if state.demo_step - last_combat_step > 6:  # ~100ms at 60 FPS
                    step_combat(state.combat_state)
                    last_combat_step = state.demo_step

                    # Check if combat finished
                    if state.combat_state.finished:
                        outcome = state.combat_state.outcome
                        print(f"\n=== Combat finished: {outcome} ===")
                        if outcome == "victory":
                            print(">>> Rewards: 1x ICE Shard, 50 credits")
                            print(">>> ICE node removed from dungeon")
                        # Wait 3 seconds to show result
                        time.sleep(3)
                        # Use _end_combat to handle rewards + ICE removal
                        from wet_run.engine.combat_view import _end_combat

                        _end_combat(state, state.combat_state)
                        state.combat_state = None
                        state.message = "Combat ended."
                        print(f"=== Returned to: {state.screen} ===")
                        print(
                            f"=== Matrix now has {len(state.matrix.nodes) if state.matrix else 0} nodes ==="
                        )

            # Auto-advance NPC (demo mode) - SKIP if interactive
            if (
                not args.interactive
                and state.screen is ScreenKind.NPC
                and state.npc_state is not None
            ):
                # After 3 seconds, select first option and continue
                if state.demo_step - last_npc_step > 180:  # ~3s at 60 FPS
                    from wet_run.engine import npc_view

                    line = state.npc_state.event.get_line(state.npc_state.current_line_index)
                    if line and line.choices:
                        npc_view._execute_choice(state, state.npc_state, line.choices[0])
                    else:
                        npc_view._advance_dialogue(state, state.npc_state)
                    last_npc_step = state.demo_step

            # Auto-jack in from cyberspace browser (demo mode)
            if (
                not args.interactive
                and state.screen is ScreenKind.CYBERSPACE_BROWSER
                and hasattr(state, "_browser_auto_step")
                and state.demo_step - state._browser_auto_step > 90
            ):
                # ~1.5s at 60 FPS — auto-jack in
                from tcod.event import KeySym, Modifier, Scancode

                ev = tcod.event.KeyDown(
                    sym=KeySym.RETURN, scancode=Scancode.RETURN, mod=Modifier.NONE
                )
                cyberspace_browser.handle_browser_input(ev, state)
                state._browser_auto_step = state.demo_step
            elif not args.interactive and state.screen is ScreenKind.CYBERSPACE_BROWSER:
                # First time entering browser — start the auto timer
                state._browser_auto_step = state.demo_step

            # Auto-navigate cyberspace in demo mode - SKIP if interactive
            if (
                not args.interactive
                and state.screen is ScreenKind.MATRIX
                and not state.action_menu_open
            ):
                if state.matrix is not None and state.current_node_id is not None:
                    current_node = state.matrix.get(state.current_node_id)
                    if current_node is not None:
                        # Auto-move every 30 frames (~0.5s)
                        if state.demo_step - last_auto_step > 30:
                            from tcod.event import KeySym

                            from wet_run.engine import cyberspace_view
                            from wet_run.run import (
                                ObjectiveKind,
                                ensure_run_state,
                                resolve_target_for_stage,
                            )

                            # RunState-driven target selection. The current
                            # stage's objective determines which node to seek.
                            run_state = ensure_run_state(state)
                            run_state.mark_visited(state.current_node_id)
                            target_id = resolve_target_for_stage(run_state, state.matrix)
                            # Keep the resolved target in RunState so other
                            # systems (status panel) can read it.
                            run_state.set_target(target_id)

                            # If we're already at the target, trigger the
                            # right action depending on the objective kind.
                            if target_id and state.current_node_id == target_id:
                                if (
                                    run_state.objective_kind() is ObjectiveKind.NPC
                                    and not npc_triggered
                                ):
                                    from wet_run.engine.npc_event import (
                                        DIXIE_FLATLINE_EVENT,
                                        NPCState,
                                    )

                                    state.npc_state = NPCState(event=DIXIE_FLATLINE_EVENT)
                                    state.screen = ScreenKind.NPC
                                    npc_triggered = True
                                    print(f"\n=== NPC ENCOUNTER: {current_node.label} ===")
                                elif run_state.objective_kind() is ObjectiveKind.DATA:
                                    from wet_run.engine import action_menu

                                    action_menu._execute_action(
                                        state,
                                        current_node,
                                        "extract",
                                        prog_registry,
                                        ice_registry,
                                    )
                                    print("\n=== Data extracted ===")
                                elif (
                                    run_state.objective_kind() is ObjectiveKind.ICE
                                    and not combat_started
                                ):
                                    if args.story_mode:
                                        # Story-mode: auto-resolve as victory
                                        _story_mode_victory(state)
                                        print(
                                            f"\n=== ICE defeated (story-mode): {current_node.label} ==="
                                        )
                                        combat_started = True
                                    else:
                                        state.action_menu_open = True
                                        combat_started = True
                                        print(f"\n=== ICE detected: {current_node.label} ===")

                            # Move toward target using cyberspace movement
                            at_stop = target_id is not None and state.current_node_id == target_id
                            if target_id and state.current_node_id != target_id and not at_stop:
                                # Get current and target positions
                                if state.cyberspace_layouts is None:
                                    # Layouts not initialized — skip movement
                                    continue
                                current_layout = state.cyberspace_layouts.get(state.current_node_id)
                                target_layout = state.cyberspace_layouts.get(target_id)
                                if current_layout and target_layout:
                                    cx, cy = current_layout.x, current_layout.y
                                    tx, ty = target_layout.x, target_layout.y
                                    # Choose direction
                                    if tx > cx:
                                        cyberspace_view._handle_cyberspace_movement(
                                            state, KeySym.RIGHT
                                        )
                                    elif tx < cx:
                                        cyberspace_view._handle_cyberspace_movement(
                                            state, KeySym.LEFT
                                        )
                                    elif ty > cy:
                                        cyberspace_view._handle_cyberspace_movement(
                                            state, KeySym.DOWN
                                        )
                                    elif ty < cy:
                                        cyberspace_view._handle_cyberspace_movement(
                                            state, KeySym.UP
                                        )

                            last_auto_step = state.demo_step

            # Mark NPC as visited when NPC encounter finishes — handled
            # via RunState.advance() inside npc_view._advance_dialogue
            # when the dialogue ends. No flag tracking needed here.

            # Render
            _render_demo(root_console, t, state, prog_registry, ice_registry)
            context.present(root_console)

            # Handle input
            for event in tcod.event.wait(timeout=0.016):  # ~60 FPS
                if not _handle_demo_input(event, state, prog_registry, ice_registry):
                    running = False
                    break

    print("\n=== Demo finished ===")
    print(f"Total time: {elapsed_s:.1f}s")
    print(f"Final screen: {state.screen}")
    return 0


def _start_prologue(state: AppState, fast: bool, no_korean: bool = False) -> None:
    """Start the demo with prologue."""
    scene = PROLOGUE_SCENE
    if fast:
        scene = _make_fast_scene(scene)
    state.screen = ScreenKind.CINEMATIC
    state.cinematic_state = CinematicState(scene=scene, show_korean=not no_korean)


def _start_briefing(state: AppState, fast: bool, no_korean: bool = False) -> None:
    """Start the demo with briefing."""
    scene = BRIEFING_FINN_SCENE
    if fast:
        scene = _make_fast_scene(scene)
    state.screen = ScreenKind.CINEMATIC
    state.cinematic_state = CinematicState(scene=scene, show_korean=not no_korean)


def _make_fast_scene(scene: story_cinematic.StoryScene) -> story_cinematic.StoryScene:
    """Convert scene to fast typing speed."""
    from wet_run.engine.story_cinematic import StoryLine, TextSpeed

    new_lines = tuple(
        StoryLine(
            text_en=line.text_en,
            text_ko=line.text_ko,
            speaker=line.speaker,
            portrait=line.portrait,
            effect=line.effect,
            speed=TextSpeed.FAST,
            pause_ms=200,  # Shorter pause
        )
        for line in scene.lines
    )
    return story_cinematic.StoryScene(
        id=scene.id,
        title_en=scene.title_en,
        title_ko=scene.title_ko,
        lines=new_lines,
        next_scene=scene.next_scene,
    )


def _advance_demo_stage(
    state: AppState,
    prog_registry: ProgramRegistry,
    ice_registry: IceRegistry,
) -> None:
    """Auto-advance to next demo stage when current stage finishes."""
    if state.cinematic_state is None:
        return

    scene_id = state.cinematic_state.scene.id

    if scene_id == "prologue_sprawl":
        # Prologue finished → Start briefing
        print("\n=== Prologue finished → Starting briefing ===")
        time.sleep(1)
        show_korean = state.cinematic_state.show_korean
        _start_briefing(state, fast=False, no_korean=not show_korean)

    elif scene_id == "briefing_finn_first_jack":
        # Briefing finished → Start matrix (First Jack mission)
        print("\n=== Briefing finished → Jacking into matrix ===")
        time.sleep(1)
        _start_matrix(state)

    else:
        # Unknown scene → return to hub
        state.screen = ScreenKind.HUB
        state.cinematic_state = None


def _story_mode_victory(state: AppState) -> None:
    """Auto-resolve combat as victory (for story-mode demo).

    Mimics the post-combat victory flow without entering combat screen:
    - Awards ICE Shard + credits
    - Marks ICE node as defeated
    - Advances RunState if on DEFEAT_ICE stage
    """
    # Award rewards
    if not hasattr(state, "inventory") or state.inventory is None:
        state.inventory = {}
    state.inventory["ice_shard"] = state.inventory.get("ice_shard", 0) + 1
    state.status_messages.append(">>> VICTORY! (story-mode) Gained: 1x ICE Shard")
    state.credits = getattr(state, "credits", 0) + 50
    state.status_messages.append(">>> Gained: 50 credits")

    # Progress mission objective (defeat)
    from wet_run.engine.mission_completion import update_mission_progress

    update_mission_progress(state, "defeat", 1)

    # Advance RunState: if we're on the DEFEAT_ICE stage, this
    # victory satisfies the objective.
    from wet_run.run import Stage, check_combat_victory, ensure_run_state

    run_state = ensure_run_state(state)
    if check_combat_victory(run_state):
        run_state.mark_advance()
        state.status_messages.append(f">>> Stage complete: {run_state.current_info().title}")
        if run_state.current_stage is Stage.JACK_OUT:
            # Jack out after ICE defeat
            from wet_run.engine.jack_out_view import enter_jack_out

            enter_jack_out(state)
            _defeat_current_ice_node(state)
            return

    # Mark current ICE node as defeated - removed from dungeon
    _defeat_current_ice_node(state)
    state.screen = ScreenKind.MATRIX
    state.message = "ICE defeated! (story-mode)"


def _defeat_current_ice_node(state: AppState) -> None:
    """Mark the current ICE node as defeated and remove from graph."""
    if state.matrix is None or state.current_node_id is None:
        return
    defeated_id = state.current_node_id
    state.defeated_nodes.add(defeated_id)
    state.status_messages.append(f">>> ICE [{defeated_id}] destroyed")
    # Remove node from graph
    from wet_run.matrix.graph import MatrixGraph

    state.matrix = MatrixGraph(
        nodes=tuple(n for n in state.matrix.nodes if n.id != defeated_id),
        edges=tuple(e for e in state.matrix.edges if e.src != defeated_id and e.dst != defeated_id),
        entry_id=state.matrix.entry_id,
    )
    if state.matrix is not None and len(state.matrix.nodes) > 0:
        neighbors = list(state.matrix.neighbors(defeated_id))
        if neighbors:
            state.current_node_id = neighbors[0].id
        else:
            state.current_node_id = state.matrix.entry_id


def _start_matrix(state: AppState) -> None:
    """Start the matrix screen via cyberspace browser."""
    from wet_run.cyberspace.registry import WorldRegistry

    # Load first mission
    available = state.job_board.available_for(state.player_grade)
    if not available:
        print("ERROR: No missions available")
        state.screen = ScreenKind.HUB
        return

    first_mission = available[0]  # "First Jack"
    state.current_mission = first_mission

    # Load world map
    if not hasattr(state, "world_map") or state.world_map is None:
        registry = WorldRegistry.load(config.DATA_DIR / "cyberspace" / "worlds.json")
        state.world_map = registry.world_map

    # Find server for this mission
    registry = WorldRegistry(state.world_map)
    location = registry.get_server_by_mission(first_mission.id)
    if location is not None:
        world_id, sector_id, server = location
        state.world_map.set_location(world_id, sector_id, server.id)
        # Find server index
        world = state.world_map.get_current_world()
        if world:
            sector = world.get_sector(sector_id)
            if sector:
                for i, s in enumerate(sector.servers):
                    if s.id == server.id:
                        state.selected_server_index = i
                        break

    state.in_server_browser = True
    state.screen = ScreenKind.CYBERSPACE_BROWSER
    state.message = "Select a server to jack into."

    print(f"\n=== Cyberspace browser: {len(state.world_map.worlds)} worlds available ===")


def _render_demo(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
    prog_registry: ProgramRegistry,
    ice_registry: IceRegistry,
) -> None:
    """Render the current demo screen."""
    if state.screen is ScreenKind.CINEMATIC:
        if state.cinematic_state is not None:
            elapsed_ms = int(state.demo_elapsed_s * 1000)
            story_cinematic.render_cinematic(console, t, state, state.cinematic_state, elapsed_ms)
    elif state.screen is ScreenKind.MENU:
        # Simple menu screen for demo
        console.clear(bg=(0, 0, 0))
        console.print(x=35, y=20, string="ROGUELIKE SPRAWL", fg=(0, 255, 255))
        console.print(x=30, y=22, string="Demo transitioning...", fg=(200, 200, 200))
        console.print(x=28, y=24, string="Press any key to continue", fg=(128, 128, 128))
    elif state.screen is ScreenKind.HUB:
        hub.render_hub(console, t, state)
    elif state.screen is ScreenKind.CYBERSPACE_BROWSER:
        from wet_run.engine import cyberspace_browser

        cyberspace_browser.render_cyberspace_browser(console, t, state)
    elif state.screen is ScreenKind.MATRIX:
        # Use cyberspace-style rendering (scrolling graph)
        from wet_run.engine import cyberspace_view

        cyberspace_view.render_cyberspace(console, t, state, prog_registry, ice_registry)
    elif state.screen is ScreenKind.NPC:
        from wet_run.engine import npc_view

        if state.npc_state is not None:
            npc_view.render_npc(console, t, state, state.npc_state)
    elif state.screen is ScreenKind.EVENT:
        from wet_run.engine import event_view

        if state.active_event is not None:
            event_view.render_event_story(console, t, state, state.active_event)
    elif state.screen is ScreenKind.COMBAT:
        if state.combat_state is not None:
            combat_view.render_combat(console, t, state, state.combat_state)
    else:
        console.clear(bg=(0, 0, 0))
        console.print(x=2, y=2, string=f"Unknown screen: {state.screen}", fg=(255, 0, 0))


def _handle_demo_input(
    event: object,
    state: AppState,
    prog_registry: ProgramRegistry,
    ice_registry: IceRegistry,
) -> bool:
    """Handle input for the current demo screen. Returns False to quit."""
    import tcod.event

    if not isinstance(event, tcod.event.KeyDown):
        return True

    # Global quit
    if event.sym is tcod.event.KeySym.Q:
        return False

    # Delegate to screen handlers
    if state.screen is ScreenKind.CINEMATIC:
        if state.cinematic_state is not None:
            result = story_cinematic.handle_cinematic_input(event, state, state.cinematic_state)
            # If ESC was pressed and moved to MENU, advance demo instead
            if state.screen is ScreenKind.MENU:
                print("\n=== Cinematic skipped (ESC) → Advancing demo ===")
                _advance_demo_stage(state, prog_registry, ice_registry)
            return result
    elif state.screen is ScreenKind.MENU:
        # Any key in menu: advance demo
        print("\n=== Menu → Advancing demo ===")
        _advance_demo_stage(state, prog_registry, ice_registry)
        return True
    elif state.screen is ScreenKind.HUB:
        # Auto-select first mission on any key press
        if event.sym in (tcod.event.KeySym.SPACE, tcod.event.KeySym.RETURN):
            _start_matrix(state)
        return True
    elif state.screen is ScreenKind.CYBERSPACE_BROWSER:
        from wet_run.engine import cyberspace_browser

        result = cyberspace_browser.handle_browser_input(event, state)
        # In demo mode, auto-jack into selected server after a moment
        return result
    elif state.screen is ScreenKind.MATRIX:
        # Use cyberspace-style input handler
        from wet_run.engine import cyberspace_view

        result = cyberspace_view.handle_cyberspace_input(event, state, prog_registry, ice_registry)

        # Auto-detect ICE node and open action menu (demo mode)
        if (
            state.matrix is not None
            and state.current_node_id is not None
            and not state.action_menu_open
            and state.screen is ScreenKind.MATRIX
        ):
            current_node = state.matrix.get(state.current_node_id)
            if current_node is not None and current_node.kind is NodeKind.ICE:
                # Auto-open action menu on ICE
                print(f"\n=== ICE detected: {current_node.label} ===")
                state.action_menu_open = True

        return result
    elif state.screen is ScreenKind.NPC:
        from wet_run.engine import npc_view

        if state.npc_state is not None:
            return npc_view.handle_npc_input(event, state, state.npc_state)
        return True
    elif state.screen is ScreenKind.EVENT:
        from wet_run.engine import event_view

        if state.active_event is not None:
            return event_view.handle_event_input(event, state, state.active_event)
        return True
    elif state.screen is ScreenKind.COMBAT:
        if state.combat_state is not None:
            return combat_view.handle_combat_input(event, state, state.combat_state)
        return True

    return True


if __name__ == "__main__":
    sys.exit(main())
