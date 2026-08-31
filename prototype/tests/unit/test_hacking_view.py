"""Tests for the hacking minigame (GA-015 defensive clamp regression).

Validates:
- step_hack clamps indicator_pos to [0, _HACK_BAR_LEN - 1] after each tick
- The defensive clamp handles transient out-of-range float values
  that could otherwise slip through and cause an IndexError at
  _HACK_ZONES[indicator_pos]
"""

from __future__ import annotations

from wet_run.engine.hacking_view import (
    _HACK_BAR_LEN,
    HackingState,
    step_hack,
)


def _make_state_with_hack(
    indicator_pos: float,
    indicator_dir: int = 1,
) -> object:
    """Build a minimal AppState-like object with hack_state populated.

    step_hack only reads state.hack_state; constructing a full AppState
    is unnecessary for this targeted regression.
    """

    class _StubState:
        pass

    state = _StubState()
    state.hack_state = HackingState(
        indicator_pos=indicator_pos,
        indicator_dir=indicator_dir,
    )
    state.player_loadout = type("L", (), {"grade": 1})()
    return state


def test_step_hack_clamps_transient_overshoot() -> None:
    """Regression (GA-015): when indicator_pos temporarily exceeds the
    bar length (e.g. from float-arithmetic rounding past _HACK_BAR_LEN - 1),
    step_hack clamps it back into the valid index range so the next
    _HACK_ZONES[indicator_pos] read does not raise IndexError.
    """
    # Use a position just past the maximum valid index (19). The
    # defensive clamp should pull it back to 19.0 exactly.
    state = _make_state_with_hack(indicator_pos=_HACK_BAR_LEN + 0.5, indicator_dir=1)
    step_hack(state, dt_s=0.016)
    assert 0.0 <= state.hack_state.indicator_pos <= float(_HACK_BAR_LEN - 1)


def test_step_hack_clamps_transient_undershoot() -> None:
    """Regression (GA-015): same clamp logic for the negative side.
    When indicator_pos drifts below 0 (e.g. -0.1), step_hack pulls it
    back into [0, _HACK_BAR_LEN - 1].
    """
    state = _make_state_with_hack(indicator_pos=-0.1, indicator_dir=-1)
    step_hack(state, dt_s=0.016)
    assert 0.0 <= state.hack_state.indicator_pos <= float(_HACK_BAR_LEN - 1)


def test_step_hack_keeps_in_range_position_in_range() -> None:
    """Sanity: positions already in range stay in range after step_hack
    (the clamp must not corrupt valid positions).
    """
    state = _make_state_with_hack(indicator_pos=10.0, indicator_dir=1)
    step_hack(state, dt_s=0.016)
    assert 0.0 <= state.hack_state.indicator_pos <= float(_HACK_BAR_LEN - 1)
