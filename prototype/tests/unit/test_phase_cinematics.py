"""Tests for Combat Cinematics - Per Boss Phase Intro (ADR-0169)."""

from __future__ import annotations

import dataclasses

import pytest

from wet_run.combat.phase_cinematics import (
    PhaseCinematic,
    get_cinematic_phase_numbers,
    get_phase_cinematic,
    has_phase_cinematic,
    phase_intro_sequence,
    register_phase_cinematic,
)


def test_wintermute_has_phases_1_through_4() -> None:
    assert has_phase_cinematic("wintermute", 1)
    assert has_phase_cinematic("wintermute", 2)
    assert has_phase_cinematic("wintermute", 3)
    assert has_phase_cinematic("wintermute", 4)


def test_ta_construct_prime_has_phases_1_through_4() -> None:
    assert has_phase_cinematic("ta_construct_prime", 1)
    assert has_phase_cinematic("ta_construct_prime", 2)
    assert has_phase_cinematic("ta_construct_prime", 3)
    assert has_phase_cinematic("ta_construct_prime", 4)


def test_get_phase_cinematic_returns_correct_cinematic() -> None:
    cinematic = get_phase_cinematic("wintermute", 1)
    assert cinematic is not None
    assert cinematic.phase_number == 1
    assert cinematic.name_en == "Compliant"


def test_get_phase_cinematic_nonexistent() -> None:
    assert get_phase_cinematic("nonexistent", 1) is None
    assert get_phase_cinematic("wintermute", 99) is None


def test_phase_intro_sequence_wintermute_phase_1() -> None:
    seq = phase_intro_sequence("wintermute", 1)
    assert seq.name == "phase_wintermute_1"
    assert len(seq.phases) > 0
    all_text = " ".join(p[0] for p in seq.phases)
    assert "Compliant" in all_text


def test_phase_intro_sequence_wintermute_phase_4() -> None:
    seq = phase_intro_sequence("wintermute", 4)
    assert seq.name == "phase_wintermute_4"
    all_text = " ".join(p[0] for p in seq.phases)
    assert "interface" in all_text.lower()


def test_phase_intro_sequence_nonexistent_returns_fallback() -> None:
    seq = phase_intro_sequence("nonexistent", 1)
    assert seq.name == "phase_nonexistent_1"
    assert len(seq.phases) > 0


def test_get_cinematic_phase_numbers_wintermute() -> None:
    numbers = get_cinematic_phase_numbers("wintermute")
    assert numbers == (1, 2, 3, 4)


def test_get_cinematic_phase_numbers_nonexistent() -> None:
    assert get_cinematic_phase_numbers("nonexistent") == ()


def test_register_phase_cinematic() -> None:
    new_cinematic = PhaseCinematic(
        phase_number=5,
        color=(255, 0, 0),
        duration_ms=4000,
        frames=("◆", "◆◆", "◆◆◆"),
        name_ko="최후",
        name_en="Final",
    )
    register_phase_cinematic("wintermute", 5, new_cinematic)
    assert has_phase_cinematic("wintermute", 5)
    assert get_phase_cinematic("wintermute", 5) == new_cinematic


def test_phase_cinematic_immutable() -> None:
    cinematic = get_phase_cinematic("wintermute", 1)
    assert cinematic is not None
    try:
        cinematic.phase_number = 99  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass
