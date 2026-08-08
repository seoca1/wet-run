"""Tests for Tutorial System (ADR-0175)."""

from __future__ import annotations

import dataclasses

import pytest

from roguelike_sprawl.combat.tutorial import (
    TUTORIAL_ACTS,
    TutorialAct,
    get_act_index,
    get_current_act,
    get_tutorial_act,
    get_tutorial_acts,
    get_tutorial_tips,
    is_first_run,
    is_learning_phase,
    should_show_tutorial,
    tutorial_has_tips,
)


def test_get_tutorial_act_existing() -> None:
    act = get_tutorial_act("act1")
    assert act is not None
    assert act.title == "FIRST JACK"


def test_get_tutorial_act_nonexistent() -> None:
    assert get_tutorial_act("nonexistent") is None


def test_get_tutorial_acts() -> None:
    acts = get_tutorial_acts()
    assert len(acts) == 3
    assert acts[0].id == "act1"
    assert acts[1].id == "act2"
    assert acts[2].id == "act3"


def test_get_current_act_first_run() -> None:
    act = get_current_act(1)
    assert act is not None
    assert act.id == "act1"


def test_get_current_act_second_run() -> None:
    act = get_current_act(2)
    assert act is not None
    assert act.id == "act2"


def test_get_current_act_third_run() -> None:
    act = get_current_act(3)
    assert act is not None
    assert act.id == "act3"


def test_get_current_act_after_third() -> None:
    act = get_current_act(10)
    assert act is not None
    assert act.id == "act3"


def test_get_tutorial_tips() -> None:
    tips = get_tutorial_tips("act1")
    assert len(tips) >= 4


def test_get_tutorial_tips_unknown() -> None:
    assert get_tutorial_tips("unknown") == ()


def test_get_tutorial_tips_act3_empty() -> None:
    assert get_tutorial_tips("act3") == ()


def test_should_show_tutorial() -> None:
    assert should_show_tutorial(1)
    assert should_show_tutorial(2)
    assert not should_show_tutorial(3)


def test_is_first_run() -> None:
    assert is_first_run(1)
    assert not is_first_run(2)


def test_is_learning_phase() -> None:
    assert is_learning_phase(1)
    assert is_learning_phase(2)
    assert not is_learning_phase(3)


def test_tutorial_has_tips() -> None:
    assert tutorial_has_tips("act1")
    assert tutorial_has_tips("act2")
    assert not tutorial_has_tips("act3")


def test_get_act_index() -> None:
    assert get_act_index("act1") == 1
    assert get_act_index("act2") == 2
    assert get_act_index("act3") == 3
    assert get_act_index("unknown") == 0


def test_act_immutable() -> None:
    act = get_tutorial_act("act1")
    assert act is not None
    try:
        act.title = "Modified"  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_all_acts_have_trigger_conditions() -> None:
    for act in TUTORIAL_ACTS.values():
        assert act.trigger_condition != ""


def test_act1_basics_tips() -> None:
    tips = get_tutorial_tips("act1")
    assert any("skill" in t.lower() for t in tips)
    assert any("heal" in t.lower() for t in tips)


def test_progression_logic() -> None:
    for run_count in [1, 2, 3, 5, 10]:
        act = get_current_act(run_count)
        assert act is not None
        assert act.id in ("act1", "act2", "act3")
