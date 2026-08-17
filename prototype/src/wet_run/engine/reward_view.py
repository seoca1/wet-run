"""Reward screen — mission completion summary.

When a Run enters Stage.REWARD, this screen shows what the player
earned: credits, materials, and any unlocked intel. Player presses
ENTER to return to the Hub.

References:
    run.state.Stage.REWARD
    design/systems/stage_structure.json
"""

from __future__ import annotations

from typing import Any

import tcod.console
import tcod.event

from ..audio import sound_manager as _sm_module
from ..run import Stage, start_run
from . import config as _engine_config
from .novel_integration import trigger_mission_completion_novel_hooks
from .state import AppState, ScreenKind

# --- Stage transition helpers ---


def enter_reward(state: AppState) -> None:
    """Transition into the Reward screen.

    Called from jack_out_view.advance_to_reward().
    Awards credits/materials to the player based on mission rewards.
    """
    state.screen = ScreenKind.REWARD

    # Award rewards from the mission
    if state.current_mission is not None:
        mission = state.current_mission
        if mission.rewards is not None:
            credits_earned = mission.rewards.credits
            if credits_earned:
                state.credits += credits_earned
                state.status_messages.append(f">>> +{credits_earned} credits")

            materials = mission.rewards.materials
            for mat_id, qty in materials.items():
                state.inventory[mat_id] = state.inventory.get(mat_id, 0) + qty
                state.status_messages.append(f">>> +{qty}x {mat_id}")

    state.status_messages.append(">>> Press ENTER to return to hub")

    # Play victory sound
    try:
        _sm_module.play("combat/victory")
    except Exception:
        pass


def return_to_hub_from_reward(state: AppState) -> None:
    """Move from REWARD to COMPLETE stage, then return to Hub.

    Called when the player dismisses the reward screen.
    """
    if state.run_state is None:
        return

    # Advance run state to COMPLETE
    while state.run_state.current_stage not in (Stage.COMPLETE, Stage.FAILED):
        state.run_state.mark_advance()
        # Safety: prevent infinite loop
        if state.run_state.current_stage in (Stage.COMPLETE, Stage.FAILED):
            break

    # Mark mission as completed
    if state.current_mission is not None:
        mission_id = state.current_mission.id
        if mission_id not in state.completed_missions:
            state.completed_missions.add(mission_id)
        state.mission_progress[mission_id] = 100  # Mark as 100% complete
        state.status_messages.append(f">>> Mission '{mission_id}' completed")

        # Fire novel hooks tied to this mission's story.source (ADR-0061).
        # Best-effort: novel_integration swallows its own errors.
        trigger_mission_completion_novel_hooks(state, mission_id)

    # Clean up matrix state
    state.matrix = None
    state.current_node_id = None
    state.cyberspace_layouts = None
    state.server_subgraph = None
    state.in_server_browser = True
    state.selected_server_index = 0

    # Reset mission
    state.current_mission = None
    state.mission_progress = {}

    # Reset run state for next run
    state.run_state = start_run(mission_id="first_jack")

    # Switch to hub
    state.screen = ScreenKind.HUB
    state.status_messages.append(">>> Returned to hub. Ready for next job.")

    # Phase 16: Successful runs emit ``run_completed`` before the state
    # is reset for the next run. Failed runs are handled in death.py.
    if getattr(state, "telemetry_opt_in", False):
        integrator = getattr(state, "telemetry", None)
        if integrator is not None:
            try:
                integrator.record_run_completed(
                    run_id=str(state.total_runs + 1),
                    grade=state.player_grade,
                )
            except Exception as exc:  # pragma: no cover - defensive
                state.status_messages.append(f">>> Telemetry run_completed failed: {exc}")


# --- Rendering ---


def render_reward(console: tcod.console.Console, state: AppState) -> None:
    """Render the Reward screen.

    Shows mission title, credits earned, materials, and "Press ENTER" prompt.
    """
    SCREEN_WIDTH = _engine_config.SCREEN_WIDTH  # noqa: N806
    SCREEN_HEIGHT = _engine_config.SCREEN_HEIGHT  # noqa: N806

    console.clear(bg=(0, 0, 0))

    box_x, box_y, box_w, box_h = _draw_reward_box(console, SCREEN_WIDTH)

    _draw_reward_title(console, box_x, box_y, box_w)
    _draw_reward_mission(console, box_x, box_y, box_w, state)
    _draw_reward_credits(console, box_x, box_y, state)
    _draw_reward_materials(console, box_x, box_y, state)
    _draw_reward_bottom_accent(console, box_x, box_y, box_h)
    _draw_reward_prompt(console, SCREEN_WIDTH, box_x, box_y, box_h)
    _draw_reward_status(console, SCREEN_HEIGHT, state)


# ------------------------------------------------------------------
# render_reward helpers
# ------------------------------------------------------------------


def _draw_reward_box(console: Any, screen_width: int) -> tuple[int, int, int, int]:
    """Draw the centered box outline and return (x, y, w, h)."""
    box_w = 50
    box_x = (screen_width - box_w) // 2
    box_y = 4
    box_h = 12

    box_border_h = "─" * (box_w - 2)
    console.print(
        x=box_x,
        y=box_y,
        string=f"┌{box_border_h}┐",
        fg=(0, 255, 100),
    )
    for y in range(box_y + 1, box_y + box_h - 1):
        console.print(
            x=box_x,
            y=y,
            string=f"│{' ' * (box_w - 2)}│",
            fg=(0, 255, 100),
        )
    console.print(
        x=box_x,
        y=box_y + box_h - 1,
        string=f"└{box_border_h}┘",
        fg=(0, 255, 100),
    )
    return box_x, box_y, box_w, box_h


def _draw_reward_title(console: Any, box_x: int, box_y: int, box_w: int) -> None:
    """The green "✓ MISSION COMPLETE" header."""
    title = "✓ MISSION COMPLETE"
    console.print(
        x=box_x + (box_w - len(title)) // 2,
        y=box_y + 1,
        string=title,
        fg=(0, 255, 100),
    )


def _draw_reward_mission(console: Any, box_x: int, box_y: int, box_w: int, state: Any) -> None:
    """Center the mission title, if a mission is in flight."""
    if state.current_mission is None:
        return
    mission_name = state.current_mission.title
    console.print(
        x=box_x + (box_w - len(mission_name)) // 2,
        y=box_y + 3,
        string=mission_name,
        fg=(255, 200, 100),
    )


def _draw_reward_credits(console: Any, box_x: int, box_y: int, state: Any) -> None:
    """Show credits earned and the new total."""
    credits_line = f"Credits:  {state.credits}"
    if state.current_mission is not None and state.current_mission.rewards:
        earned = state.current_mission.rewards.credits
        credits_line = f"Credits:  +{earned}  (total: {state.credits})"
    console.print(
        x=box_x + 4,
        y=box_y + 5,
        string=credits_line,
        fg=(255, 200, 100),
    )


def _draw_reward_materials(console: Any, box_x: int, box_y: int, state: Any) -> None:
    """List up to 4 inventory items; collapse the rest into a summary."""
    mat_y = box_y + 7
    console.print(x=box_x + 4, y=mat_y, string="Materials:", fg=(200, 200, 200))
    if not state.inventory:
        console.print(
            x=box_x + 4,
            y=mat_y + 1,
            string="  (none)",
            fg=(150, 150, 150),
        )
    else:
        for i, (mat_id, qty) in enumerate(sorted(state.inventory.items())):
            mat_line = f"  • {qty}x {mat_id}"
            console.print(
                x=box_x + 4,
                y=mat_y + 1 + i,
                string=mat_line,
                fg=(100, 200, 255),
            )
            if i >= 3:
                remaining = len(state.inventory) - 4
                if remaining > 0:
                    console.print(
                        x=box_x + 4,
                        y=mat_y + 2 + i,
                        string=f"  • ... and {remaining} more",
                        fg=(150, 150, 150),
                    )
                break

    # Phase E-1: AAR (After Action Report) — combat statistics summary
    _draw_aar_stats(console, box_x, mat_y, state)


def _draw_reward_bottom_accent(console: Any, box_x: int, box_y: int, box_h: int) -> None:
    """Single horizontal line under the inner content."""
    console.print(
        x=box_x + 1,
        y=box_y + box_h - 1,
        string="─" * 48,
        fg=(0, 200, 80),
    )


def _draw_aar_stats(console: Any, box_x: int, mat_y: int, state: Any) -> None:
    """Phase E-1: After Action Report — combat statistics summary.

    Shows damage dealt/received, crits, max combo, peak alarm from
    the most recent combat_state.stats if available.
    """
    cs = getattr(state, "combat_state", None)
    if cs is None or not hasattr(cs, "stats"):
        return
    stats = cs.stats
    aar_y = mat_y + 6
    lines = [
        "── Combat Report ──",
        f"  Damage dealt:    {stats.damage_dealt}",
        f"  Damage received: {stats.damage_received}",
        f"  Crits (you/them):{stats.crits_landed}/{stats.crits_received}",
        f"  Max combo:       {stats.max_combo_reached}",
        f"  Peak alarm:      {stats.peak_alarm_level}/5",
        f"  Duration:        {cs.tick_ms // 1000}s",
    ]
    for i, line in enumerate(lines):
        fg = (200, 200, 100) if i == 0 else (180, 180, 180)
        console.print(
            x=box_x + 4,
            y=aar_y + i,
            string=line,
            fg=fg,
        )


def _draw_reward_prompt(
    console: Any, screen_width: int, box_x: int, box_y: int, box_h: int
) -> None:
    """Centered "[ENTER] Return to Hub" line below the box."""
    prompt = "[ENTER] Return to Hub"
    console.print(
        x=(screen_width - len(prompt)) // 2,
        y=box_y + box_h + 2,
        string=prompt,
        fg=(200, 200, 200),
    )


def _draw_reward_status(console: Any, screen_height: int, state: Any) -> None:
    """Last few status messages, dimmed, at the bottom of the screen."""
    if not state.status_messages:
        return
    for i, msg in enumerate(state.status_messages[-5:]):
        console.print(
            x=2,
            y=screen_height - 7 + i,
            string=msg,
            fg=(120, 120, 120),
        )


def handle_reward_input(
    event: tcod.event.Event,
    state: AppState,
) -> bool:
    """Handle input on the Reward screen. Returns False to quit."""
    if not isinstance(event, tcod.event.KeyDown):
        return True

    if event.sym is tcod.event.KeySym.Q:
        return False
    if event.sym is tcod.event.KeySym.ESCAPE:
        return False

    # ENTER or SPACE advances
    if event.sym in (
        tcod.event.KeySym.RETURN,
        tcod.event.KeySym.SPACE,
        tcod.event.KeySym.KP_ENTER,
    ):
        return_to_hub_from_reward(state)
        return True

    return True
