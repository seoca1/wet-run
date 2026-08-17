"""Breach Protocol (ADR-0177).

Matrix hacking minigame: 3-5 row × 5-7 col grid puzzle. Player selects
daemons to match a target sequence. Time pressure creates urgency.
Success = bonus effects (alarm reduce, ICE stun, AP restore).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

DAEMON_VALUES: tuple[str, ...] = (
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
)
DEFAULT_GRID_COLS = 7
DEFAULT_SEQUENCE_LENGTH = 3
DEFAULT_TIMER_MS = 10_000


@dataclass(frozen=True, slots=True)
class BreachProtocol:
    """A matrix hacking minigame."""

    grid: tuple[tuple[str, ...], ...]
    target_sequence: tuple[str, ...]
    timer_ms: int
    difficulty: int


@dataclass(frozen=True, slots=True)
class BreachReward:
    """Reward for successfully completing a breach."""

    reward_type: str
    value: float
    description: str


BREACH_REWARDS: dict[int, BreachReward] = {
    1: BreachReward("alarm_reduce", 2.0, "Alarm ticks down 2"),
    2: BreachReward("armor_break", 0.5, "ICE shield -50% for 2 turns"),
    3: BreachReward("silence", 3.0, "ICE silenced for 3 turns"),
    4: BreachReward("ap_restore", 3.0, "Restore 3 AP"),
    5: BreachReward("all_effects", 1.0, "All breach effects"),
}


def create_breach(difficulty: int, rng: random.Random | None = None) -> BreachProtocol:
    """Create a new breach protocol puzzle."""
    rng = rng or random.Random()
    rows = 3 + (difficulty - 1) // 2
    cols = DEFAULT_GRID_COLS
    grid: list[tuple[str, ...]] = []
    for _ in range(rows):
        row = tuple(rng.choice(DAEMON_VALUES) for _ in range(cols))
        grid.append(row)
    seq_len = DEFAULT_SEQUENCE_LENGTH + (difficulty - 1) // 2
    target = tuple(rng.choice(DAEMON_VALUES) for _ in range(seq_len))
    timer_ms = DEFAULT_TIMER_MS + (difficulty - 1) * 1000
    return BreachProtocol(
        grid=tuple(grid),
        target_sequence=target,
        timer_ms=timer_ms,
        difficulty=difficulty,
    )


def select_daemon(protocol: BreachProtocol, row: int, col: int) -> str | None:
    """Return the daemon value at (row, col), or None if out of bounds."""
    if row < 0 or row >= len(protocol.grid):
        return None
    grid_row = protocol.grid[row]
    if col < 0 or col >= len(grid_row):
        return None
    return grid_row[col]


def check_solution(
    protocol: BreachProtocol,
    selections: list[tuple[int, int]],
) -> bool:
    """Return True if the player's selections match the target sequence."""
    if len(selections) != len(protocol.target_sequence):
        return False
    for (row, col), target in zip(selections, protocol.target_sequence, strict=False):
        if select_daemon(protocol, row, col) != target:
            return False
    return True


def get_remaining_time(protocol: BreachProtocol, elapsed_ms: int) -> int:
    """Return the remaining time in milliseconds (0 if expired)."""
    return max(0, protocol.timer_ms - elapsed_ms)


def is_timer_expired(protocol: BreachProtocol, elapsed_ms: int) -> bool:
    """Return True if the timer has expired."""
    return get_remaining_time(protocol, elapsed_ms) <= 0


def get_breach_reward(difficulty: int) -> BreachReward:
    """Return the reward for a given difficulty level."""
    return BREACH_REWARDS.get(difficulty, BREACH_REWARDS[1])


def get_grid_size(protocol: BreachProtocol) -> tuple[int, int]:
    """Return (rows, cols) of the grid."""
    rows = len(protocol.grid)
    cols = len(protocol.grid[0]) if rows > 0 else 0
    return (rows, cols)


def get_daemon_count(protocol: BreachProtocol) -> int:
    """Return the total number of daemons in the grid."""
    return sum(len(row) for row in protocol.grid)


def progress_ratio(protocol: BreachProtocol, selections: list[tuple[int, int]]) -> float:
    """Return the progress ratio (0.0 to 1.0)."""
    target_len = len(protocol.target_sequence)
    if target_len == 0:
        return 1.0
    return min(1.0, len(selections) / target_len)


def get_max_difficulty() -> int:
    """Return the maximum difficulty level."""
    return max(BREACH_REWARDS.keys())


def has_valid_reward(difficulty: int) -> bool:
    """Return True if a reward exists for the difficulty."""
    return difficulty in BREACH_REWARDS


__all__ = [
    "BREACH_REWARDS",
    "DEFAULT_GRID_COLS",
    "DEFAULT_SEQUENCE_LENGTH",
    "DEFAULT_TIMER_MS",
    "DAEMON_VALUES",
    "BreachProtocol",
    "BreachReward",
    "check_solution",
    "create_breach",
    "get_breach_reward",
    "get_daemon_count",
    "get_grid_size",
    "get_max_difficulty",
    "get_remaining_time",
    "has_valid_reward",
    "is_timer_expired",
    "progress_ratio",
    "select_daemon",
]
