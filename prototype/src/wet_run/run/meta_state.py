"""Meta progression state — cross-run, cross-save-file persistence.

Pillar 4 (The Build) allows *unlock-only* meta progression. This module
stores persistent relationships (faction reputation, future: Hall of Dead,
achievements) in a separate file (`data/saves/meta_state.json`) that
survives across sessions, save slots, and character deaths.

The data lives in `AppState.reputation` at runtime; this module owns the
*persistent* record (promoted on explicit user choice — see ADR-0131).

ADR-0131 (Accepted 2026-07-27): Meta State File
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..matrix.node import Faction
from .reputation import ReputationState

# Schema version. Bump when adding fields that need migration.
META_STATE_VERSION = 1


@dataclass
class MetaState:
    """Cross-run persistent meta progression state (ADR-0131).

    Currently tracks:
      - Faction reputation (mirrors ReputationState shape but lives outside
        the per-run AppState)

    Future fields (placeholder):
      - hall_of_dead: list of past jockeys
      - achievements_unlocked: list of achievement IDs

    Attributes:
        version: Schema version for migration. Must match META_STATE_VERSION.
        reputation: Cross-run faction reputation (separate from AppState).
        future_buckets: Dict for forward-compatible extension. Items here
            are not migrated but survive save roundtrips for safe additive
            changes in minor versions.
    """

    version: int = META_STATE_VERSION
    reputation: ReputationState = field(default_factory=ReputationState)
    future_buckets: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialize for disk persistence."""
        return {
            "version": self.version,
            "reputation": self.reputation.to_dict(),
            **self.future_buckets,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> MetaState:
        """Restore from a dict produced by ``to_dict``.

        Defensive: malformed inputs return an empty default state.
        Unknown fields are preserved in ``future_buckets`` for forward
        compatibility.
        """
        if not isinstance(data, dict):
            return cls()
        version_raw = data.get("version", META_STATE_VERSION)
        try:
            version = (
                int(version_raw) if isinstance(version_raw, (int, str)) else META_STATE_VERSION
            )
        except (TypeError, ValueError):
            version = META_STATE_VERSION
        # Reserved keys (consumed by this class); everything else goes into
        # future_buckets.
        reserved = {"version", "reputation"}
        future_buckets: dict[str, object] = {k: v for k, v in data.items() if k not in reserved}
        rep_data = data.get("reputation")
        if isinstance(rep_data, dict):
            reputation = ReputationState.from_dict(rep_data)
        else:
            reputation = ReputationState()
        return cls(version=version, reputation=reputation, future_buckets=future_buckets)

    # ---- Promotion API (ADR-0131) ----

    def promote_from_run(self, run_reputation: ReputationState) -> None:
        """Merge a finished run's reputation history into the meta state.

        History entries from the run are appended to the meta reputation
        with a "run:" prefix so the player can see which events came
        from which run. Per-event clamping (±25) is applied at the
        FactionReputation level, so the meta state's reputation score
        accumulates gradually across runs.

        Args:
            run_reputation: The completed run's ReputationState.
        """
        for faction in Faction:
            run_rep = run_reputation.get(faction)
            if not run_rep.history:
                continue  # No interaction this run
            meta_rep = self.reputation.get(faction)
            for delta, src in run_rep.history:
                meta_rep.adjust(delta, source=f"run:{src}")


__all__ = ["META_STATE_VERSION", "MetaState"]
