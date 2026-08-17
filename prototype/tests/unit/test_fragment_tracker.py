"""Tests for MemoryFragmentTracker (ADR-0140 §Proposal 2)."""

from __future__ import annotations

from wet_run.lore.fragment_tracker import MemoryFragmentTracker


class TestMemoryFragmentTracker:
    """Per-run cap enforcement + serialization."""

    def test_default_state(self) -> None:
        tracker = MemoryFragmentTracker()
        assert tracker.count == 0
        assert tracker.remaining == 6
        assert tracker.can_discover() is True
        assert tracker.already_found == set()

    def test_mark_found(self) -> None:
        tracker = MemoryFragmentTracker()
        assert tracker.mark_found("memory_signal_echo_01") is True
        assert tracker.count == 1
        assert tracker.remaining == 5
        assert "memory_signal_echo_01" in tracker.already_found

    def test_mark_found_idempotent(self) -> None:
        tracker = MemoryFragmentTracker()
        tracker.mark_found("memory_signal_echo_01")
        assert tracker.mark_found("memory_signal_echo_01") is False
        assert tracker.count == 1

    def test_per_run_cap_enforced(self) -> None:
        tracker = MemoryFragmentTracker(per_run_cap=2)
        tracker.mark_found("a")
        tracker.mark_found("b")
        assert tracker.can_discover() is False
        assert tracker.mark_found("c") is False
        assert tracker.count == 2
        assert tracker.remaining == 0

    def test_reset_clears(self) -> None:
        tracker = MemoryFragmentTracker()
        tracker.mark_found("a")
        tracker.mark_found("b")
        tracker.reset()
        assert tracker.count == 0
        assert tracker.already_found == set()

    def test_to_dict_roundtrip(self) -> None:
        tracker = MemoryFragmentTracker(per_run_cap=3)
        tracker.mark_found("a")
        tracker.mark_found("b")
        data = tracker.to_dict()
        restored = MemoryFragmentTracker.from_dict(data)
        assert restored.per_run_cap == 3
        assert restored.already_found == {"a", "b"}

    def test_from_dict_malformed_returns_default(self) -> None:
        restored = MemoryFragmentTracker.from_dict({})
        assert restored.per_run_cap == 6
        assert restored.already_found == set()

    def test_from_dict_invalid_types(self) -> None:
        restored = MemoryFragmentTracker.from_dict(
            {"already_found": "not a list", "per_run_cap": -1}
        )
        # Defensive: invalid cap falls back to 6
        assert restored.per_run_cap == 6
        assert restored.already_found == set()

    def test_from_dict_non_string_items_filtered(self) -> None:
        restored = MemoryFragmentTracker.from_dict({"already_found": ["a", 123, None, "b"]})
        assert restored.already_found == {"a", "b"}
