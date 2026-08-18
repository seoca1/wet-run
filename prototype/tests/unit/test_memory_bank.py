"""Tests for the Construct Memory Bank system (Phase 50+ deep upgrade).

Covers the data layer — the only layer this commit touches.
Future phases (51+) will hook up the bank to the Death cycle,
the result screen, and the graphic-novel memory channel.
"""

from __future__ import annotations

import pytest

from wet_run.run.memory_bank import (
    MAX_FRAGMENTS,
    MemoryBank,
    MemoryFragment,
)


@pytest.fixture
def base_fragment() -> MemoryFragment:
    return MemoryFragment(
        text="The neon still hums in the back of my skull.",
        arc=1,
        timestamp_ms=1_700_000_000_000,
    )


class TestMemoryFragment:
    def test_construction(self, base_fragment: MemoryFragment) -> None:
        assert base_fragment.text == "The neon still hums in the back of my skull."
        assert base_fragment.arc == 1
        assert base_fragment.timestamp_ms == 1_700_000_000_000
        assert base_fragment.strength == 1.0

    def test_rejects_arc_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="arc must be in 1..5"):
            MemoryFragment(text="x", arc=0, timestamp_ms=0)
        with pytest.raises(ValueError, match="arc must be in 1..5"):
            MemoryFragment(text="x", arc=6, timestamp_ms=0)

    def test_rejects_strength_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="strength must be in 0.0..1.0"):
            MemoryFragment(text="x", arc=1, timestamp_ms=0, strength=-0.1)
        with pytest.raises(ValueError, match="strength must be in 0.0..1.0"):
            MemoryFragment(text="x", arc=1, timestamp_ms=0, strength=1.5)

    def test_is_immutable(self, base_fragment: MemoryFragment) -> None:
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            base_fragment.text = "overwritten"  # type: ignore[misc]


class TestMemoryBank:
    def test_empty_bank(self) -> None:
        bank = MemoryBank()
        assert bank.fragments == []
        assert bank.recall() == []

    def test_add_single(self, base_fragment: MemoryFragment) -> None:
        bank = MemoryBank()
        bank.add(base_fragment)
        assert len(bank.fragments) == 1
        assert bank.recall()[0].text == base_fragment.text

    def test_preserves_order_of_addition(self) -> None:
        bank = MemoryBank()
        a = MemoryFragment(text="A", arc=1, timestamp_ms=100)
        b = MemoryFragment(text="B", arc=1, timestamp_ms=200)
        c = MemoryFragment(text="C", arc=1, timestamp_ms=300)
        bank.add(a)
        bank.add(b)
        bank.add(c)
        assert [f.text for f in bank.fragments] == ["A", "B", "C"]

    def test_evicts_oldest_at_cap(self) -> None:
        bank = MemoryBank()
        for i in range(MAX_FRAGMENTS + 5):
            bank.add(
                MemoryFragment(
                    text=f"frag-{i}",
                    arc=1,
                    timestamp_ms=1_700_000_000_000 + i,
                )
            )
        assert len(bank.fragments) == MAX_FRAGMENTS
        # First 5 should have been evicted, oldest surviving is frag-5.
        assert bank.fragments[0].text == "frag-5"
        assert bank.fragments[-1].text == f"frag-{MAX_FRAGMENTS + 5 - 1}"

    def test_recall_sorted_by_strength(self) -> None:
        bank = MemoryBank()
        weak = MemoryFragment(text="weak", arc=1, timestamp_ms=1, strength=0.2)
        strong = MemoryFragment(text="strong", arc=1, timestamp_ms=2, strength=0.9)
        bank.add(weak)
        bank.add(strong)
        recalled = bank.recall()
        assert recalled[0].text == "strong"
        assert recalled[1].text == "weak"

    def test_clear(self, base_fragment: MemoryFragment) -> None:
        bank = MemoryBank()
        bank.add(base_fragment)
        bank.clear()
        assert bank.fragments == []


class TestMemoryBankPersistence:
    def test_round_trip_preserves_all_fields(self) -> None:
        original = MemoryBank()
        for i in range(3):
            original.add(
                MemoryFragment(
                    text=f"memory-{i}",
                    arc=(i % 5) + 1,
                    timestamp_ms=1_700_000_000_000 + i,
                    strength=0.5 + 0.1 * i,
                )
            )
        data = original.to_dict()
        restored = MemoryBank.from_dict(data)
        assert len(restored.fragments) == 3
        for original_frag, restored_frag in zip(
            original.fragments, restored.fragments, strict=True
        ):
            assert restored_frag.text == original_frag.text
            assert restored_frag.arc == original_frag.arc
            assert restored_frag.timestamp_ms == original_frag.timestamp_ms
            assert restored_frag.strength == original_frag.strength

    def test_from_dict_handles_non_dict_input(self) -> None:
        assert MemoryBank.from_dict("not a dict").fragments == []  # type: ignore[arg-type]
        assert MemoryBank.from_dict(None).fragments == []  # type: ignore[arg-type]
        assert MemoryBank.from_dict(42).fragments == []  # type: ignore[arg-type]

    def test_from_dict_skips_malformed_entries(self) -> None:
        data = {
            "fragments": [
                {"text": "good", "arc": 1, "timestamp_ms": 1, "strength": 1.0},
                "not a dict",
                None,
                {"text": "bad arc", "arc": 99, "timestamp_ms": 1, "strength": 1.0},
                {"text": "bad strength", "arc": 1, "timestamp_ms": 1, "strength": 9.9},
                {"text": "", "arc": 1, "timestamp_ms": 1, "strength": 1.0},
            ]
        }
        bank = MemoryBank.from_dict(data)
        assert len(bank.fragments) == 1
        assert bank.fragments[0].text == "good"

    def test_to_dict_shape(self) -> None:
        bank = MemoryBank()
        bank.add(MemoryFragment(text="x", arc=1, timestamp_ms=1, strength=0.5))
        data = bank.to_dict()
        assert set(data.keys()) == {"fragments"}
        assert isinstance(data["fragments"], list)
        assert len(data["fragments"]) == 1
        frag_dict = data["fragments"][0]
        assert set(frag_dict.keys()) == {"text", "arc", "timestamp_ms", "strength"}


class TestMaxFragmentsConstant:
    def test_cap_is_at_least_4(self) -> None:
        # Should be large enough to span at least 4-5 storylines.
        assert MAX_FRAGMENTS >= 4
