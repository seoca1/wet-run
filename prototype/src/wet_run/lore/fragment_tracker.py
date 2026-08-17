"""Memory Fragment tracker — per-run state for fragment discovery.

ADR-0140 §Proposal 2. Tracks which fragments have been discovered
this run and enforces the per-run cap.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MemoryFragmentTracker:
    """Per-run state for Memory Fragment discovery.

    Attributes:
        already_found: Set of fragment IDs discovered this run.
        per_run_cap: Maximum number of fragments per run (ADR-0140 default 6).
    """

    already_found: set[str] = field(default_factory=set)
    per_run_cap: int = 6

    @property
    def count(self) -> int:
        """Number of fragments discovered this run."""
        return len(self.already_found)

    @property
    def remaining(self) -> int:
        """Remaining fragments allowed this run."""
        return max(0, self.per_run_cap - self.count)

    def can_discover(self) -> bool:
        """Check if more fragments can be discovered this run."""
        return self.count < self.per_run_cap

    def mark_found(self, fragment_id: str) -> bool:
        """Mark a fragment as found this run.

        Args:
            fragment_id: Fragment ID to mark.

        Returns:
            True if newly added, False if already found or cap reached.
        """
        if not self.can_discover():
            return False
        if fragment_id in self.already_found:
            return False
        self.already_found.add(fragment_id)
        return True

    def reset(self) -> None:
        """Clear all discoveries (call on new run)."""
        self.already_found.clear()

    def to_dict(self) -> dict[str, object]:
        """Serialize for save/restore."""
        return {
            "already_found": sorted(self.already_found),
            "per_run_cap": self.per_run_cap,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> MemoryFragmentTracker:
        """Restore from dict. Defensive against malformed input."""
        if not isinstance(data, dict):
            return cls()
        already = data.get("already_found", [])
        cap_raw = data.get("per_run_cap", 6)
        cap = 6
        if isinstance(cap_raw, int) and cap_raw > 0:
            cap = cap_raw
        found: set[str] = set()
        if isinstance(already, list):
            for item in already:
                if isinstance(item, str):
                    found.add(item)
        return cls(already_found=found, per_run_cap=cap)


__all__ = ["MemoryFragmentTracker"]
