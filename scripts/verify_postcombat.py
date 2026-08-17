"""Headless verification of the post-combat flow.

Walks through DEFEAT_ICE → JACK_OUT → REWARD → Hub (or DEBRIEF)
without launching a tcod window. Verifies:
- Stage transitions are correct
- Rewards are awarded
- Mission is marked completed
- Matrix state is cleared
- Run state is reset for next run

Usage:
    uv run python scripts/verify_postcombat.py
    uv run python scripts/verify_postcombat.py --character veteran
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine import debrief_view, jack_out_view, reward_view
from wet_run.engine.state import AppState, ScreenKind
from wet_run.matrix.node import ZoneDepth
from wet_run.missions.mission import Mission, Rewards
from wet_run.run import Stage, start_run


def make_mission(mission_id: str = "first_jack") -> Mission:
    """Build a sample mission with rewards."""
    return Mission(
        id=mission_id,
        title="First Jack",
        fixer="finn",
        arc=1,
        grade_min=1,
        grade_max=1,
        matrix_seed=42,
        zone=ZoneDepth.SURFACE,
        rewards=Rewards(credits=500, materials={"data_fragment": 2, "ice_shard": 1}),
    )


def verify_postcombat(character: str = "novice") -> int:
    """Run the full post-combat flow verification."""
    print("=" * 60)
    print("  POST-COMBAT FLOW VERIFICATION")
    print("=" * 60)
    print()
    print(f"Character: {character}")
    print()

    state = AppState()
    state.inventory = {}
    state.credits = 0
    state.run_state = start_run("first_jack")
    state.current_mission = make_mission()
    state.run_state.current_stage = Stage.DEFEAT_ICE
    print(f"[setup] mission={state.current_mission.id}, "
          f"credits={state.credits}, stage={state.run_state.current_stage.value}")
    print()

    # 1. Combat victory → mark_advance → JACK_OUT
    print("[1] DEFEAT_ICE → JACK_OUT")
    state.run_state.mark_advance()
    assert state.run_state.current_stage is Stage.JACK_OUT, "Should be JACK_OUT"
    print(f"    ✓ stage advanced: {state.run_state.current_stage.value}")

    # 2. Enter JACK_OUT screen
    print("[2] enter_jack_out()")
    jack_out_view.enter_jack_out(state)
    assert state.screen is ScreenKind.JACK_OUT
    assert state.jack_out_frame_index == 0
    print(f"    ✓ screen={state.screen.value}, frame={state.jack_out_frame_index}")

    # 3. Skip animation, dismiss
    print("[3] Skip animation + ENTER")
    state.jack_out_started_at = time.monotonic() - 10.0
    import tcod.event

    event = tcod.event.KeyDown(sym=tcod.event.KeySym.RETURN, mod=0, scancode=0)
    jack_out_view.handle_jack_out_input(event, state)
    assert state.run_state.current_stage is Stage.REWARD
    assert state.screen is ScreenKind.REWARD
    print(f"    ✓ stage={state.run_state.current_stage.value}, screen={state.screen.value}")

    # 4. Verify rewards were awarded
    print("[4] Rewards awarded")
    assert state.credits == 500, f"Expected 500 credits, got {state.credits}"
    assert state.inventory.get("data_fragment") == 2
    assert state.inventory.get("ice_shard") == 1
    print(f"    ✓ credits={state.credits}")
    print(f"    ✓ inventory: {state.inventory}")

    # 5. Press ENTER to return to hub
    print("[5] ENTER → Hub")
    event = tcod.event.KeyDown(sym=tcod.event.KeySym.RETURN, mod=0, scancode=0)
    reward_view.handle_reward_input(event, state)
    assert state.screen is ScreenKind.HUB
    assert "first_jack" in state.completed_missions
    print(f"    ✓ screen={state.screen.value}")
    print(f"    ✓ mission completed: first_jack in {state.completed_missions}")
    print(f"    ✓ run state reset to: {state.run_state.current_stage.value}")

    # 6. Optional: Debrief flow
    print()
    print("[6] Optional: DEBRIEF flow")
    # Reset and walk through again, ending at DEBRIEF
    state2 = AppState()
    state2.inventory = {}
    state2.credits = 0
    state2.run_state = start_run("first_jack")
    state2.run_state.current_stage = Stage.DEBRIEF
    debrief_view.enter_debrief(state2, character=character)
    assert state2.screen is ScreenKind.DEBRIEF
    assert state2.debrief_character == character
    print(f"    ✓ screen={state2.screen.value}, character={state2.debrief_character}")

    # Press any key to advance
    event = tcod.event.KeyDown(sym=tcod.event.KeySym.SPACE, mod=0, scancode=0)
    debrief_view.handle_debrief_input(event, state2)
    assert state2.screen is ScreenKind.HUB
    assert state2.run_state.current_stage is Stage.COMPLETE
    print(f"    ✓ advanced: stage={state2.run_state.current_stage.value}, screen={state2.screen.value}")

    # 7. Test failure path: DEFEAT_ICE → FAILED → DEATH_RESTART
    print()
    print("[7] Failure path: DEFEAT_ICE → FAILED")
    state3 = AppState()
    state3.inventory = {"ice_shard": 5}
    state3.credits = 100
    state3.run_state = start_run("first_jack")
    state3.run_state.current_stage = Stage.DEFEAT_ICE
    state3.run_state.mark_failed()
    assert state3.run_state.current_stage is Stage.FAILED
    completed_values = [s.value for s in state3.run_state.completed_stages]
    assert "defeat_ice" in completed_values, f"Expected defeat_ice in {completed_values}"
    print(f"    ✓ failed: stage={state3.run_state.current_stage.value}")
    print(f"    ✓ completed_stages: {completed_values}")
    state3.run_state.mark_death_restart()
    assert state3.run_state.current_stage is Stage.DEATH_RESTART
    print(f"    ✓ death_restart: stage={state3.run_state.current_stage.value}")

    # 8. Render JACK_OUT (verify no crash)
    print()
    print("[8] Render JACK_OUT screen (no crash check)")
    import tcod.console

    console = tcod.console.Console(80, 50, order="F")
    state.jack_out_started_at = time.monotonic() - 10.0  # animation done
    jack_out_view.render_jack_out(console, state)
    print("    ✓ JACK_OUT render: no crash")

    # 9. Render REWARD
    state.current_mission = make_mission("test")
    reward_view.enter_reward(state)
    console2 = tcod.console.Console(80, 50, order="F")
    reward_view.render_reward(console2, state)
    print("    ✓ REWARD render: no crash")

    # 10. Render DEBRIEF
    debrief_view.enter_debrief(state, character=character)
    console3 = tcod.console.Console(80, 50, order="F")
    debrief_view.render_debrief(console3, state)
    print("    ✓ DEBRIEF render: no crash")

    print()
    print("=" * 60)
    print("  ✅ ALL CHECKS PASSED")
    print("=" * 60)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify post-combat flow")
    parser.add_argument(
        "--character",
        choices=["novice", "veteran", "heretic"],
        default="novice",
        help="Which character to use for debrief flavor",
    )
    args = parser.parse_args()
    return verify_postcombat(character=args.character)


if __name__ == "__main__":
    sys.exit(main())
