"""Tests for Breach Protocol (ADR-0177)."""

from __future__ import annotations

import dataclasses
import random

import pytest

from roguelike_sprawl.combat.breach_protocol import (
    DAEMON_VALUES,
    BreachProtocol,
    check_solution,
    create_breach,
    get_breach_reward,
    get_daemon_count,
    get_grid_size,
    get_max_difficulty,
    get_remaining_time,
    has_valid_reward,
    is_timer_expired,
    progress_ratio,
    select_daemon,
)


def test_create_breach_difficulty_1() -> None:
    rng = random.Random(42)
    breach = create_breach(1, rng=rng)
    assert breach.difficulty == 1
    assert len(breach.grid) >= 3
    assert len(breach.target_sequence) >= 3


def test_create_breach_difficulty_5() -> None:
    rng = random.Random(42)
    breach = create_breach(5, rng=rng)
    assert breach.difficulty == 5
    assert len(breach.grid) >= 5
    assert len(breach.target_sequence) >= 5
    assert breach.timer_ms >= 14000


def test_grid_values_are_valid_daemons() -> None:
    rng = random.Random(42)
    breach = create_breach(3, rng=rng)
    for row in breach.grid:
        for val in row:
            assert val in DAEMON_VALUES


def test_target_sequence_valid() -> None:
    rng = random.Random(42)
    breach = create_breach(3, rng=rng)
    for val in breach.target_sequence:
        assert val in DAEMON_VALUES


def test_select_daemon_in_bounds() -> None:
    rng = random.Random(42)
    breach = create_breach(1, rng=rng)
    val = select_daemon(breach, 0, 0)
    assert val is not None
    assert val in DAEMON_VALUES


def test_select_daemon_out_of_bounds() -> None:
    rng = random.Random(42)
    breach = create_breach(1, rng=rng)
    assert select_daemon(breach, -1, 0) is None
    assert select_daemon(breach, 0, -1) is None
    assert select_daemon(breach, 100, 0) is None
    assert select_daemon(breach, 0, 100) is None


def test_check_solution_correct() -> None:
    breach = BreachProtocol(
        grid=(("A", "B", "C"), ("D", "E", "F"), ("1", "2", "3")),
        target_sequence=("A", "D", "1"),
        timer_ms=10000,
        difficulty=1,
    )
    assert check_solution(breach, [(0, 0), (1, 0), (2, 0)])


def test_check_solution_wrong() -> None:
    breach = BreachProtocol(
        grid=(("A", "B", "C"), ("D", "E", "F"), ("1", "2", "3")),
        target_sequence=("A", "D", "1"),
        timer_ms=10000,
        difficulty=1,
    )
    assert not check_solution(breach, [(0, 0), (0, 1), (0, 2)])


def test_check_solution_wrong_length() -> None:
    breach = BreachProtocol(
        grid=(("A", "B", "C"),),
        target_sequence=("A", "B"),
        timer_ms=10000,
        difficulty=1,
    )
    assert not check_solution(breach, [(0, 0)])


def test_get_remaining_time() -> None:
    breach = BreachProtocol(
        grid=(("A",),),
        target_sequence=("A",),
        timer_ms=10000,
        difficulty=1,
    )
    assert get_remaining_time(breach, 0) == 10000
    assert get_remaining_time(breach, 3000) == 7000
    assert get_remaining_time(breach, 10000) == 0
    assert get_remaining_time(breach, 15000) == 0


def test_is_timer_expired() -> None:
    breach = BreachProtocol(
        grid=(("A",),),
        target_sequence=("A",),
        timer_ms=5000,
        difficulty=1,
    )
    assert not is_timer_expired(breach, 0)
    assert not is_timer_expired(breach, 4999)
    assert is_timer_expired(breach, 5000)
    assert is_timer_expired(breach, 10000)


def test_get_breach_reward() -> None:
    for diff in range(1, 6):
        reward = get_breach_reward(diff)
        assert reward.value > 0
        assert reward.reward_type != ""


def test_has_valid_reward() -> None:
    for diff in range(1, 6):
        assert has_valid_reward(diff)
    assert not has_valid_reward(99)


def test_get_max_difficulty() -> None:
    assert get_max_difficulty() >= 5


def test_get_grid_size() -> None:
    rng = random.Random(42)
    breach = create_breach(1, rng=rng)
    rows, cols = get_grid_size(breach)
    assert rows >= 3
    assert cols == 7


def test_get_daemon_count() -> None:
    rng = random.Random(42)
    breach = create_breach(1, rng=rng)
    assert get_daemon_count(breach) >= 21


def test_progress_ratio() -> None:
    breach = BreachProtocol(
        grid=(("A", "B"),),
        target_sequence=("A", "B"),
        timer_ms=10000,
        difficulty=1,
    )
    assert progress_ratio(breach, []) == 0.0
    assert progress_ratio(breach, [(0, 0)]) == 0.5
    assert progress_ratio(breach, [(0, 0), (0, 1)]) == 1.0


def test_progress_ratio_overflow() -> None:
    breach = BreachProtocol(
        grid=(("A",),),
        target_sequence=("A",),
        timer_ms=10000,
        difficulty=1,
    )
    assert progress_ratio(breach, [(0, 0), (0, 0)]) == 1.0


def test_breach_immutable() -> None:
    breach = BreachProtocol(
        grid=(("A",),),
        target_sequence=("A",),
        timer_ms=10000,
        difficulty=1,
    )
    try:
        breach.difficulty = 99  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_rewards_progression() -> None:
    highest = get_breach_reward(5)
    assert highest.reward_type == "all_effects"
    base = get_breach_reward(1)
    assert base.reward_type != highest.reward_type


def test_all_grid_rows_valid_length() -> None:
    rng = random.Random(42)
    for diff in range(1, 6):
        breach = create_breach(diff, rng=rng)
        for row in breach.grid:
            assert len(row) == 7


def test_create_breach_deterministic_with_seed() -> None:
    rng1 = random.Random(42)
    rng2 = random.Random(42)
    b1 = create_breach(3, rng=rng1)
    b2 = create_breach(3, rng=rng2)
    assert b1.grid == b2.grid
    assert b1.target_sequence == b2.target_sequence
