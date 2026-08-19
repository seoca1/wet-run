"""Construct Memory Bank (Phase 50+ — deep upgrade, Pillar 1: The Run).

The Memory Bank carries fragments of a dead jockey's consciousness
into the next run. When a jockey flatlines in the Death cycle, a
portion of their last mission memories are preserved as fragments
that the next jockey can recall from the construct space.

This is a meta-progression system layered on top of the existing
unlock-only meta state. It does NOT grant gameplay power — only
narrative memory fragments that surface in flavour text and (in
future phases) the graphic-novel memory-channel system.

The system is intentionally lightweight:

* ``MemoryFragment`` is a single string + arc + timestamp + strength
* ``MemoryBank`` is a thin collection wrapper with a cap of 12 fragments
  (the most recent 12 survive across runs; older fragments decay)
* ``save/load`` round-trip via ``to_dict``/``from_dict`` (same pattern
  as ``ReputationState`` and ``StageLockInfo``)
* No external dependencies (matches the rest of the run/ package)

Design notes
-----------
* The memory_bank is a property on ``AppState`` (default empty bank)
* It does NOT affect game balance — purely cosmetic / narrative
* The strength decay is a placeholder for a future decay model
  (Phase 50+ doesn't yet implement decay; left as a data field for
  forward-compat)
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Cap on the number of fragments preserved across runs. 12 is
# large enough to give 4-5 storylines × 3 fragments each, small
# enough that the localStorage payload stays under 4 KB.
MAX_FRAGMENTS = 12


@dataclass(frozen=True, slots=True)
class MemoryFragment:
    """A single preserved memory fragment from a flatlined jockey.

    Attributes:
        text: The memory's narrative text (1-2 sentences).
        arc: Arc during which the memory was captured (1-5).
        timestamp_ms: ms since epoch when the fragment was preserved.
        strength: Decay placeholder (0.0-1.0). Phase 50+ does not
            yet implement decay, so fragments keep their initial
            strength of 1.0. Reserved for a future Phase 51+ decay
            system.
    """

    text: str
    arc: int
    timestamp_ms: int
    strength: float = 1.0

    def __post_init__(self) -> None:
        """Validate arc range (1-5) and strength range (0.0-1.0)."""
        if not 1 <= self.arc <= 5:
            raise ValueError(
                f"MemoryFragment arc must be in 1..5, got {self.arc} (text={self.text!r})"
            )
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(f"MemoryFragment strength must be in 0.0..1.0, got {self.strength}")


@dataclass
class MemoryBank:
    """Per-profile construct memory bank.

    Most recent ``MAX_FRAGMENTS`` survive; older fragments are
    discarded when a new one is added (FIFO eviction).
    """

    fragments: list[MemoryFragment] = field(default_factory=list)

    def add(self, fragment: MemoryFragment) -> None:
        """Add a fragment, evicting the oldest if at cap."""
        if len(self.fragments) >= MAX_FRAGMENTS:
            self.fragments.pop(0)
        self.fragments.append(fragment)

    def recall(self) -> list[MemoryFragment]:
        """Return all current fragments, strongest first.

        Phase 50+ doesn't implement decay, so this is just
        ``sorted(fragments, key=lambda f: f.strength, reverse=True)``.
        Future phases that implement strength decay will fold the
        decay here.
        """
        return sorted(self.fragments, key=lambda f: f.strength, reverse=True)

    def clear(self) -> None:
        """Remove all fragments from the bank."""
        self.fragments.clear()

    def to_dict(self) -> dict[str, object]:
        """Serialize the bank to a JSON-compatible dict (for save data)."""
        return {
            "fragments": [
                {
                    "text": f.text,
                    "arc": f.arc,
                    "timestamp_ms": f.timestamp_ms,
                    "strength": f.strength,
                }
                for f in self.fragments
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> MemoryBank:
        """Deserialize a bank from its ``to_dict`` form. Returns empty bank on malformed input."""
        if not isinstance(data, dict):
            return cls()
        raw_fragments = data.get("fragments", [])
        if not isinstance(raw_fragments, list):
            return cls()
        bank = cls()
        for entry in raw_fragments:
            if not isinstance(entry, dict):
                continue
            text = str(entry.get("text", ""))
            try:
                arc = int(entry.get("arc", 0))
                timestamp_ms = int(entry.get("timestamp_ms", 0))
            except (TypeError, ValueError):
                continue
            try:
                strength = float(entry.get("strength", 1.0))
            except (TypeError, ValueError):
                strength = 1.0
            if not 1 <= arc <= 5 or not 0.0 <= strength <= 1.0 or not text:
                continue
            bank.fragments.append(
                MemoryFragment(
                    text=text,
                    arc=arc,
                    timestamp_ms=timestamp_ms,
                    strength=strength,
                )
            )
        return bank


__all__ = [
    "MAX_FRAGMENTS",
    "MemoryBank",
    "MemoryFragment",
]
