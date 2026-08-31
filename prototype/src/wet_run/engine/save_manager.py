"""Save/Load system for Run state.

Persists the current Run (and relevant AppState) to a JSON file so the
player can continue later. Save format is versioned for future
migration.

Save format (JSON):
    {
      "version": "0.1.0",
      "saved_at": "2026-06-18T20:00:00Z",
      "elapsed_seconds": 480,
      "run_state": {
        "current_stage": "jack_out",
        "completed_stages": ["meet_npc", "extract_data", "defeat_ice"],
        "pending_advance": true,
        "current_target_node": "ice1",
        "last_visited_node": "data1",
        "mission_id": "first_jack",
        "started_at_ms": 0
      },
      "mission": {
        "id": "first_jack",
        "title": "First Jack",
        "fixer": "finn",
        "arc": 1,
        "grade_min": 1,
        "grade_max": 1,
        "matrix_seed": 42,
        "zone": "surface",
        "rewards": {
          "credits": 500,
          "materials": {"data_fragment": 2}
        }
      },
      "app_state": {
        "inventory": {"data_fragment": 2, "ice_shard": 1},
        "credits": 500,
        "current_node_id": "data1",
        "defeated_nodes": ["ice1"],
        "extracted_nodes": ["data1"],
        "mission_progress": {"extract_data": 1, "defeat": 1}
      },
      "metadata": {
        "player_grade": 1,
        "screen": "matrix"
      }
    }

Auto-save triggers:
- JACK_OUT entry (after defeating ICE, before disconnect)
- DEATH (player can choose to load or restart)
- Manual: F5 (quick save to slot 1), F9 (quick load slot 1)
- Hub menu: Save / Load buttons

Save slots: 5 slots, files in `<save_dir>/slot_N.json`.
Default save dir: `~/.wet_run/saves/` (cross-platform).
"""

from __future__ import annotations

import json
import os
import platform
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .state import AppState


# --- Save format ---


SAVE_FORMAT_VERSION = "0.1.0"
MAX_SLOTS = 10  # Phase 7.3: 5 → 10 manual save slots
DEFAULT_SLOT = 1
AUTO_SAVE_SLOT = 0  # Phase 7.3: separate auto-save slot (slot 0)
AUTO_SAVE_FILENAME = "autosave.json"  # distinct from manual slot_{N}.json


# Migration chain: list of (source_version, target_version, transform) tuples.
# Transforms take a parsed save dict and return the upgraded dict. The
# chain is walked in order until the dict reaches SAVE_FORMAT_VERSION.
#
# Pre-0.1.0 saves lacked a version field entirely; the legacy chain
# normalises them to 0.1.0 by injecting the version key.
#
# GA-016 fix: when SAVE_FORMAT_VERSION is bumped, add a forward-compat
# migration entry that defaults all newly-serialized fields. Example:
#   ("0.1.0", "0.2.0", _build_forward_compat_migration(
#       "0.2.0", {"deck_size": "standard", "gamepad_enabled": True}
#   )),
# Without this, all existing 0.1.0 saves would raise
# SaveVersionMismatchError on load.
_SAVE_MIGRATIONS: list[tuple[str, str, Any]] = [
    (
        "<legacy>",
        SAVE_FORMAT_VERSION,
        lambda data: {**data, "version": SAVE_FORMAT_VERSION},
    ),
]


def _build_forward_compat_migration(
    target_version: str,
    default_fields: dict[str, Any],
) -> Any:
    """Build a migration transform that injects defaults for new fields.

    Use when bumping SAVE_FORMAT_VERSION: each newly-serialized field
    must appear in ``default_fields`` with its AppState default value
    so legacy saves upgrade cleanly without SaveVersionMismatchError.

    Defaults are merged into ``data["app_state"]`` (the nested dict
    that holds AppState fields), not the top-level save dict. Pre-
    existing values in app_state are preserved (defaults only fill
    missing keys).

    Args:
        target_version: The SAVE_FORMAT_VERSION string this migration
            upgrades to (must match the constant at write time).
        default_fields: Mapping of new AppState field name -> default
            value (e.g. {"deck_size": "standard", "gamepad_enabled": True}).

    Returns:
        Transform function ``(data: dict) -> dict`` that bumps the
        version and merges defaults into app_state (preserving any
        existing values).
    """

    def _transform(data: dict[str, Any]) -> dict[str, Any]:
        data["version"] = target_version
        app_state = data.setdefault("app_state", {})
        for key, value in default_fields.items():
            app_state.setdefault(key, value)
        return data

    return _transform


def _migrate_save_data(data: dict[str, Any]) -> dict[str, Any]:
    """Apply version migrations until data reaches SAVE_FORMAT_VERSION.

    Walks ``_SAVE_MIGRATIONS`` from the data's current version to
    ``SAVE_FORMAT_VERSION``. If a version in the chain is missing,
    raises SaveVersionMismatchError (cannot auto-upgrade across gaps).
    """
    current = data.get("version", "<legacy>")
    target = SAVE_FORMAT_VERSION

    if current == target:
        return data

    while current != target:
        # Find a migration from `current` to its successor.
        next_step = next(
            (m for m in _SAVE_MIGRATIONS if m[0] == current),
            None,
        )
        if next_step is None:
            raise SaveVersionMismatchError(
                f"No migration path from save version {current!r} to {target!r}"
            )
        _, successor, transform = next_step
        data = transform(data)
        current = successor

    return data


class SaveError(Exception):
    """Base class for save/load errors."""


class SaveSlotEmptyError(SaveError):
    """Save slot has no data."""


class SaveVersionMismatchError(SaveError):
    """Save file version doesn't match current code version."""


class SaveCorruptedError(SaveError):
    """Save file is corrupted or unreadable."""


# --- Save metadata ---


@dataclass(frozen=True, slots=True)
class SaveMetadata:
    """Metadata about a save file (for listing/displays)."""

    slot: int
    exists: bool
    version: str | None
    saved_at: str | None
    elapsed_seconds: int
    mission_id: str | None
    current_stage: str | None
    player_grade: int | None
    credits: int
    size_bytes: int
    is_compatible: bool


# --- Saved run data ---


@dataclass
class SavedRun:
    """A complete saved Run that can be restored.

    Attributes:
        version: Save format version.
        saved_at: ISO 8601 timestamp.
        elapsed_seconds: Game time elapsed (for display).
        run_state: The RunState as a dict (Stage enums as strings).
        mission: The mission as a dict (enums as strings).
        app_state: AppState fields needed for Run continuation.
        metadata: Display metadata (grade, screen, etc.).
    """

    version: str
    saved_at: str
    elapsed_seconds: int
    run_state: dict[str, Any]
    mission: dict[str, Any] | None
    app_state: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "version": self.version,
            "saved_at": self.saved_at,
            "elapsed_seconds": self.elapsed_seconds,
            "run_state": self.run_state,
            "mission": self.mission,
            "app_state": self.app_state,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SavedRun:
        """Deserialize from JSON dict. Auto-migrates older versions."""
        migrated = _migrate_save_data(data)
        version = migrated.get("version")
        if version != SAVE_FORMAT_VERSION:
            raise SaveVersionMismatchError(
                f"Save version {version!r} != current {SAVE_FORMAT_VERSION!r}"
            )
        return cls(
            version=version,
            saved_at=migrated.get("saved_at", ""),
            elapsed_seconds=migrated.get("elapsed_seconds", 0),
            run_state=migrated.get("run_state", {}),
            mission=migrated.get("mission"),
            app_state=migrated.get("app_state", {}),
            metadata=migrated.get("metadata", {}),
        )


# --- Save manager ---


def _default_save_dir() -> Path:
    """Return the platform-appropriate save directory.

    - macOS/Linux: $XDG_DATA_HOME/wet_run/saves/ or ~/.local/share/...
    - Windows: %APPDATA%/wet_run/saves/
    """
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
    else:
        # Unix-like: XDG_DATA_HOME or ~/.local/share
        xdg = os.environ.get("XDG_DATA_HOME")
        if xdg:
            base = xdg
        else:
            base = str(Path.home() / ".local" / "share")
    return Path(base) / "wet_run" / "saves"


def _log_save_warning(message: str) -> None:
    """Log a save-system warning without raising.

    Used by graceful-degradation paths so a recoverable problem
    (e.g. matrix schema evolution) is visible during debugging but
    doesn't crash the save flow.
    """
    try:
        from .logger import get_logger

        get_logger().warning(message, context="save_manager")
    except Exception:
        # Logger itself may be unavailable — fall back to stderr.
        sys.stderr.write(f"[save_manager] WARN: {message}\n")
        sys.stderr.flush()


def _atomic_write(path: Path, data: str) -> None:
    """Write data to path atomically (write to temp + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(tmp_path, path)
    except OSError:
        # Disk full / permission denied / parent dir disappeared —
        # all transient filesystem issues. Clean up the temp file
        # and re-raise as-is so the caller sees the real cause.
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass  # Best effort — temp cleanup is not the bug
        raise


class SaveManager:
    """Manages save slots and Run persistence."""

    def __init__(self, save_dir: Path | None = None) -> None:
        """Initialize save manager.

        Args:
            save_dir: Directory for save files. Defaults to platform-appropriate path.
        """
        self.save_dir = save_dir or _default_save_dir()
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def _slot_path(self, slot: int) -> Path:
        """Get the file path for a save slot.

        Manual slots are 1..MAX_SLOTS (slot_{N}.json).
        AUTO_SAVE_SLOT (0) uses a separate autosave.json file.

        Raises:
            ValueError: If ``slot`` is outside the valid range. The message
                includes the offending value, the valid range, and the
                ``AUTO_SAVE_SLOT`` alias so callers can self-diagnose
                off-by-one mistakes without reading the constants.
        """
        if slot == AUTO_SAVE_SLOT:
            return self.save_dir / AUTO_SAVE_FILENAME
        if not 1 <= slot <= MAX_SLOTS:
            raise ValueError(
                f"slot must be 1..{MAX_SLOTS} "
                f"(or AUTO_SAVE_SLOT={AUTO_SAVE_SLOT} for autosave), got {slot}"
            )
        return self.save_dir / f"slot_{slot}.json"

    def has_save(self, slot: int) -> bool:
        """Check if a slot has a save file."""
        return self._slot_path(slot).exists()

    def list_slots(self) -> list[SaveMetadata]:
        """List all save slots (1..MAX_SLOTS) with metadata.

        Empty slots are included with exists=False.
        """
        result: list[SaveMetadata] = []
        for slot in range(1, MAX_SLOTS + 1):
            result.append(self.get_metadata(slot))
        return result

    def autosave(self, state: AppState) -> SaveMetadata:
        """Save to the dedicated auto-save slot (Phase 7.3).

        Overwrites any prior auto-save. Auto-save is intended for
        checkpoint-style persistence, not user-initiated saves.
        The auto-save slot is rendered separately in the save/load view.

        Args:
            state: Current AppState snapshot to persist.

        Returns:
            SaveMetadata for the auto-save slot.
        """
        return self.save(AUTO_SAVE_SLOT, state)

    def has_autosave(self) -> bool:
        """Check if an auto-save exists."""
        return self.has_save(AUTO_SAVE_SLOT)

    def list_all(self) -> list[SaveMetadata]:
        """List auto-save (slot 0) + all manual slots (1..MAX_SLOTS).

        Auto-save appears first. Useful for unified save/load UI.
        """
        result: list[SaveMetadata] = [self.get_metadata(AUTO_SAVE_SLOT)]
        result.extend(self.list_slots())
        return result

    def get_metadata(self, slot: int) -> SaveMetadata:
        """Get metadata for a single slot (without loading full data)."""
        path = self._slot_path(slot)
        if not path.exists():
            return SaveMetadata(
                slot=slot,
                exists=False,
                version=None,
                saved_at=None,
                elapsed_seconds=0,
                mission_id=None,
                current_stage=None,
                player_grade=None,
                credits=0,
                size_bytes=0,
                is_compatible=False,
            )
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            version = data.get("version", "")
            return SaveMetadata(
                slot=slot,
                exists=True,
                version=version,
                saved_at=data.get("saved_at"),
                elapsed_seconds=data.get("elapsed_seconds", 0),
                mission_id=(data.get("mission") or {}).get("id"),
                current_stage=(data.get("run_state") or {}).get("current_stage"),
                player_grade=(data.get("metadata") or {}).get("player_grade"),
                credits=(data.get("app_state") or {}).get("credits", 0),
                size_bytes=path.stat().st_size,
                is_compatible=(version == SAVE_FORMAT_VERSION),
            )
        except (json.JSONDecodeError, OSError):
            return SaveMetadata(
                slot=slot,
                exists=True,
                version=None,
                saved_at=None,
                elapsed_seconds=0,
                mission_id=None,
                current_stage=None,
                player_grade=None,
                credits=0,
                size_bytes=path.stat().st_size if path.exists() else 0,
                is_compatible=False,
            )

    def save(
        self,
        slot: int,
        state: AppState,
        elapsed_seconds: int = 0,
    ) -> SaveMetadata:
        """Save current Run state to a slot.

        Args:
            slot: Save slot (0 for auto-save, 1..MAX_SLOTS for manual).
            state: App state to save.
            elapsed_seconds: Game time elapsed (for display).

        Returns:
            Metadata of the saved file.

        Raises:
            ValueError: If slot is invalid.
        """
        from .state import AppState

        if not isinstance(state, AppState):
            raise TypeError(f"state must be AppState, got {type(state).__name__}")
        if state.run_state is None:
            raise SaveError("No run in progress to save")

        saved_run = SavedRun(
            version=SAVE_FORMAT_VERSION,
            saved_at=datetime.now(UTC).isoformat(),
            elapsed_seconds=elapsed_seconds,
            run_state=self._serialize_run_state(state.run_state),
            mission=self._serialize_mission(state.current_mission),
            app_state=self._serialize_app_state(state),
            metadata=self._serialize_metadata(state),
        )
        json_data = json.dumps(saved_run.to_dict(), indent=2, ensure_ascii=False)
        _atomic_write(self._slot_path(slot), json_data)
        return self.get_metadata(slot)

    # ------------------------------------------------------------------
    # save() helpers — split for readability
    # ------------------------------------------------------------------

    def _serialize_run_state(self, run_state: Any) -> dict[str, Any]:
        """Flatten the run-state into a JSON-safe dict (Stage enums → strings)."""
        # GA-011 fix: persist chapter_state (was silently reset to PROLOGUE).
        chapter_state_obj = getattr(run_state, "chapter_state", None)
        chapter_state_value = (
            chapter_state_obj.value if chapter_state_obj is not None else "prologue"
        )
        return {
            "current_stage": run_state.current_stage.value,
            "completed_stages": [s.value for s in run_state.completed_stages],
            "pending_advance": run_state.pending_advance,
            "current_target_node": run_state.current_target_node,
            "last_visited_node": run_state.last_visited_node,
            "mission_id": run_state.mission_id,
            "started_at_ms": run_state.started_at_ms,
            "chapter_state": chapter_state_value,
            # GA-005 fix: persist current_phase_index (was reset to 0 on load).
            "current_phase_index": getattr(run_state, "current_phase_index", 0),
        }

    def _serialize_mission(self, mission: Any) -> dict[str, Any] | None:
        """Flatten the current mission into a JSON-safe dict, or None."""
        if mission is None:
            return None
        return {
            "id": mission.id,
            "title": mission.title,
            "fixer": mission.fixer,
            "arc": mission.arc,
            "grade_min": mission.grade_min,
            "grade_max": mission.grade_max,
            "matrix_seed": mission.matrix_seed,
            "zone": mission.zone.value,
            "rewards": {
                "credits": mission.rewards.credits if mission.rewards else 0,
                "materials": dict(mission.rewards.materials) if mission.rewards else {},
            },
        }

    def _serialize_app_state(self, state: AppState) -> dict[str, Any]:
        """Serialize the AppState fields needed to resume a Run.

        Includes the matrix graph if present — falls back to no-matrix
        save on serialization errors (the player will re-jack-in on
        restore) so a single unknown field doesn't break the entire
        save.
        """
        matrix_dict: dict[str, object] | None = None
        if state.matrix is not None:
            try:
                matrix_dict = state.matrix.to_dict()
            except (AttributeError, KeyError, TypeError, ValueError) as exc:
                _log_save_warning(f"matrix serialization failed: {exc}")
                matrix_dict = None

        # GA-004 fix: equipment_loadout serializes to a dict (no to_dict method).
        # Round-trip via __dict__ + dict() conversion for nested dataclass.
        equipment_dict = self._serialize_equipment(state.equipment_loadout)

        return {
            "inventory": dict(state.inventory),
            "credits": state.credits,
            "current_node_id": state.current_node_id,
            "defeated_nodes": list(state.defeated_nodes),
            "extracted_nodes": list(state.extracted_nodes),
            "mission_progress": dict(state.mission_progress),
            "in_server_browser": state.in_server_browser,
            "selected_server_index": state.selected_server_index,
            "current_mission_id": state.current_mission.id if state.current_mission else None,
            "matrix": matrix_dict,
            # Phase 6+: faction reputation persists across runs.
            "reputation": state.reputation.to_dict(),
            # GA-004 fix: comprehensive field round-trip to prevent
            # save corruption across the 30+ AppState fields not
            # previously serialised.
            "player_loadout_id": getattr(state.player_loadout, "id", "starter"),
            "player_max_hp": state.player_max_hp,
            "deck_size": state.deck_size,
            "hardcore_mode": state.hardcore_mode,
            "ng_plus_unlocked": state.ng_plus_unlocked,
            "ng_plus_active": state.ng_plus_active,
            "construct_companion_active": state.construct_companion_active,
            "story_flags": list(state.story_flags),
            "shown_events": list(state.shown_events),
            "completed_missions": list(state.completed_missions),
            "active_mutators": list(state.active_mutators),
            "active_events": list(state.active_events),
            "event_log": list(state.event_log),
            "faction_tension_triggered": list(state.faction_tension_triggered),
            "purchased_intel_items": list(state.purchased_intel_items),
            "data_fragments": list(state.data_fragments),
            "nodes_visited": list(state.nodes_visited),
            "anomaly_triggered": list(state.anomaly_triggered),
            "available_servers": list(state.available_servers),
            "alarm_level": state.alarm_level,
            "equipment_loadout": equipment_dict,
            "telemetry_opt_in": state.telemetry_opt_in,
            "gamepad_enabled": state.gamepad_enabled,
            "colorblind_mode": state.colorblind_mode,
            "high_contrast": state.high_contrast,
            "font_size": state.font_size,
            "total_runs": state.total_runs,
            "total_deaths": state.total_deaths,
            "resolution": getattr(state, "resolution", "classic"),
            # GA-004 fix (continuation): scalar gameplay fields from QA's
            # identified 50+ missing fields. Simple types only; complex
            # objects (combat_state, gn_*, chapter_*) still require
            # per-object to_dict / from_dict and are out of scope here.
            "is_dead": state.is_dead,
            "death_reason": state.death_reason,
            "death_cause": state.death_cause,
            "heal_disabled": state.heal_disabled,
            "alarm_speed_multiplier": state.alarm_speed_multiplier,
            "encounter_multiplier": state.encounter_multiplier,
            "tempo_mode": state.tempo_mode,
            "salvage_fragments": state.salvage_fragments,
            "pending_salvage": state.pending_salvage,
            "phase4_triggered": state.phase4_triggered,
            "faction_tension_probability_boost": state.faction_tension_probability_boost,
            "near_miss_triggered": state.near_miss_triggered,
        }

    def _serialize_equipment(self, equipment: Any) -> dict[str, Any]:
        """Convert EquipmentLoadout to a JSON-safe dict.

        EquipmentLoadout does not have to_dict(); reconstruct via __dict__.
        Nested items are dicts (already JSON-safe).
        """
        result: dict[str, Any] = {}
        for attr in (
            "deck",
            "programs",
            "wetware",
            "set_bonuses_active",
        ):
            value = getattr(equipment, attr, None)
            if value is None:
                result[attr] = None
            elif isinstance(value, dict):
                result[attr] = {
                    k: list(v) if isinstance(v, (list, tuple)) else v for k, v in value.items()
                }
            elif isinstance(value, (list, tuple, set)):
                result[attr] = list(value)
            else:
                result[attr] = value
        return result

    def _restore_equipment(self, equipment: Any, data: dict[str, Any]) -> None:
        """Populate EquipmentLoadout fields from a serialised dict.

        Mirrors ``_serialize_equipment``; missing keys keep defaults so
        legacy / partial saves still load.
        """
        for attr in ("deck", "programs", "wetware", "set_bonuses_active"):
            if attr not in data:
                continue
            value = data[attr]
            if value is None:
                continue
            current = getattr(equipment, attr, None)
            if isinstance(current, dict):
                # Keys -> str, values -> tuple/list (matches EquipmentLoadout convention)
                setattr(
                    equipment,
                    attr,
                    {k: tuple(v) if isinstance(v, list) else v for k, v in value.items()},
                )
            elif isinstance(current, (list, tuple, set)):
                setattr(equipment, attr, list(value))
            else:
                setattr(equipment, attr, value)

    def _serialize_metadata(self, state: AppState) -> dict[str, Any]:
        """Lightweight display metadata for the save-slot list."""
        return {
            "player_grade": state.player_grade,
            "screen": state.screen.value,
            # Phase 16: Persist ending choice across runs (ADR-0192).
            "ending_choice": getattr(state, "ending_choice", ""),
        }

    def load(self, slot: int) -> SavedRun:
        """Load a saved Run from a slot.

        Args:
            slot: Save slot (0 for auto-save, 1..MAX_SLOTS for manual).

        Returns:
            The SavedRun.

        Raises:
            SaveSlotEmptyError: If the slot has no save.
            SaveVersionMismatchError: If version doesn't match.
            SaveCorruptedError: If the file is corrupted.
        """
        path = self._slot_path(slot)
        if not path.exists():
            raise SaveSlotEmptyError(f"Slot {slot} is empty")

        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise SaveCorruptedError(f"Slot {slot} file is corrupted: {e}") from e
        except OSError as e:
            raise SaveCorruptedError(f"Slot {slot} file is unreadable: {e}") from e

        try:
            return SavedRun.from_dict(data)
        except SaveVersionMismatchError:
            raise
        except (KeyError, TypeError, ValueError) as e:
            # GA-013 fix: removed AttributeError from the corruption-list.
            # AttributeError from from_dict typically signals a missing
            # NEW field on legacy saves (a migration concern, not a
            # corruption). Since the GA-016 _build_forward_compat_migration
            # helper provides explicit migration infrastructure, let
            # AttributeError propagate as a normal load error so the
            # developer sees the real exception (instead of it being
            # masked as "save corrupted"). Corruption detection remains
            # for genuinely malformed data (KeyError, TypeError, ValueError).
            raise SaveCorruptedError(f"Slot {slot} data is invalid: {e}") from e

    def restore_state(self, slot: int, state: AppState) -> None:
        """Restore AppState from a saved Run.

        Args:
            slot: Save slot (0 for auto-save, 1..MAX_SLOTS for manual).
            state: AppState to modify in-place.

        Raises:
            SaveSlotEmptyError, SaveVersionMismatchError, SaveCorruptedError
        """

        saved = self.load(slot)
        rs_data = saved.run_state
        app_data = saved.app_state

        current_stage = self._restore_run_state(state, rs_data)
        self._restore_app_state_fields(state, app_data)
        self._restore_reputation(state, app_data)
        if saved.metadata.get("player_grade") is not None:
            state.player_grade = int(saved.metadata["player_grade"])
        # Phase 16: restore ending choice across runs (ADR-0192).
        # Only overwrite if the key is present in the saved metadata;
        # legacy saves (pre-Phase 16) lack this key, in which case we
        # keep the default empty string on the freshly-built app_state.
        if "ending_choice" in saved.metadata:
            ending_choice = saved.metadata["ending_choice"]
            if isinstance(ending_choice, str):
                state.ending_choice = ending_choice

        matrix_restored = self._restore_matrix(state, app_data)
        self._reset_transient_state(state)
        self._restore_mission(state, app_data)

        # Recompute layouts if matrix came back.
        if matrix_restored and state.matrix is not None:
            state.cyberspace_layouts = self._recompute_layouts(state.matrix)
        else:
            state.cyberspace_layouts = None

        self._restore_screen(state, current_stage)
        state.status_messages.append(f">>> Game loaded from slot {slot}")
        state.status_messages.append(f">>> Stage: {current_stage.value}")
        if matrix_restored and state.matrix is not None:
            state.status_messages.append(
                f">>> Matrix restored: {len(state.matrix.nodes)} nodes, "
                f"{len(state.matrix.edges)} edges"
            )

    # ------------------------------------------------------------------
    # restore_state helpers — each handles one logical step.
    # ------------------------------------------------------------------

    def _restore_run_state(self, state: AppState, rs_data: dict[str, Any]) -> Any:
        """Rebuild ``state.run_state`` from the saved run dict."""
        from ..run import RunState, Stage

        try:
            current_stage = Stage(rs_data.get("current_stage", "pending"))
        except ValueError:
            current_stage = Stage.PENDING
        completed_stages: tuple[Stage, ...] = tuple(
            Stage(s) for s in rs_data.get("completed_stages", [])
        )
        # GA-011 fix: restore chapter_state (was silently reset to PROLOGUE on load).
        from ..run.state import ChapterState

        try:
            chapter_state = ChapterState(rs_data.get("chapter_state", "prologue"))
        except ValueError:
            chapter_state = ChapterState.PROLOGUE
        state.run_state = RunState(
            current_stage=current_stage,
            completed_stages=completed_stages,
            pending_advance=rs_data.get("pending_advance", False),
            current_target_node=rs_data.get("current_target_node"),
            last_visited_node=rs_data.get("last_visited_node"),
            mission_id=rs_data.get("mission_id", "first_jack"),
            started_at_ms=rs_data.get("started_at_ms", 0),
            chapter_state=chapter_state,
            # GA-005 fix: restore current_phase_index (was silently reset to 0).
            current_phase_index=int(rs_data.get("current_phase_index", 0)),
        )
        return current_stage

    def _restore_app_state_fields(self, state: AppState, app_data: dict[str, Any]) -> None:
        """Populate the small AppState scalar / set fields.

        GA-004 fix: round-trip the comprehensive field set serialised in
        _serialize_app_state. Each new field uses ``dict.get()`` with the
        field's existing default so legacy saves (pre-fix) load cleanly.
        """
        state.inventory = dict(app_data.get("inventory", {}))
        state.credits = int(app_data.get("credits", 0))
        state.current_node_id = app_data.get("current_node_id")
        state.defeated_nodes = set(app_data.get("defeated_nodes", []))
        state.extracted_nodes = set(app_data.get("extracted_nodes", []))
        state.mission_progress = dict(app_data.get("mission_progress", {}))
        state.in_server_browser = app_data.get("in_server_browser", True)
        state.selected_server_index = int(app_data.get("selected_server_index", 0))
        # GA-004 fix: restore the comprehensive field set with safe defaults.
        state.player_max_hp = int(app_data.get("player_max_hp", 0))
        state.deck_size = app_data.get("deck_size", "standard")
        state.hardcore_mode = bool(app_data.get("hardcore_mode", False))
        state.ng_plus_unlocked = bool(app_data.get("ng_plus_unlocked", False))
        state.ng_plus_active = bool(app_data.get("ng_plus_active", False))
        state.construct_companion_active = bool(app_data.get("construct_companion_active", False))
        state.story_flags = set(app_data.get("story_flags", []))
        state.shown_events = set(app_data.get("shown_events", []))
        state.completed_missions = set(app_data.get("completed_missions", []))
        state.active_mutators = tuple(app_data.get("active_mutators", []))
        state.active_events = tuple(app_data.get("active_events", []))
        state.event_log = list(app_data.get("event_log", []))
        state.faction_tension_triggered = set(app_data.get("faction_tension_triggered", []))
        state.purchased_intel_items = list(app_data.get("purchased_intel_items", []))
        state.data_fragments = set(app_data.get("data_fragments", []))
        state.nodes_visited = set(app_data.get("nodes_visited", []))
        state.anomaly_triggered = set(app_data.get("anomaly_triggered", []))
        state.available_servers = list(app_data.get("available_servers", []))
        state.alarm_level = int(app_data.get("alarm_level", 0))
        state.telemetry_opt_in = bool(app_data.get("telemetry_opt_in", False))
        state.gamepad_enabled = bool(app_data.get("gamepad_enabled", True))
        state.colorblind_mode = app_data.get("colorblind_mode", "none")
        state.high_contrast = bool(app_data.get("high_contrast", False))
        state.font_size = app_data.get("font_size", "normal")
        state.total_runs = int(app_data.get("total_runs", 0))
        state.total_deaths = int(app_data.get("total_deaths", 0))
        state.resolution = app_data.get("resolution", "classic")
        # GA-004 fix (continuation): round-trip scalar gameplay fields added in
        # _serialize_app_state. Each new field uses dict.get() with the
        # field's existing default so legacy saves (pre-fix) load cleanly.
        state.is_dead = bool(app_data.get("is_dead", False))
        state.death_reason = app_data.get("death_reason", "")
        state.death_cause = app_data.get("death_cause", "Combat")
        state.heal_disabled = bool(app_data.get("heal_disabled", False))
        state.alarm_speed_multiplier = float(app_data.get("alarm_speed_multiplier", 1.0))
        state.encounter_multiplier = int(app_data.get("encounter_multiplier", 1))
        state.tempo_mode = app_data.get("tempo_mode", "normal")
        state.salvage_fragments = int(app_data.get("salvage_fragments", 0))
        state.pending_salvage = bool(app_data.get("pending_salvage", False))
        state.phase4_triggered = bool(app_data.get("phase4_triggered", False))
        state.faction_tension_probability_boost = float(
            app_data.get("faction_tension_probability_boost", 0.0)
        )
        state.near_miss_triggered = bool(app_data.get("near_miss_triggered", False))
        equipment_data = app_data.get("equipment_loadout")
        if isinstance(equipment_data, dict):
            self._restore_equipment(state.equipment_loadout, equipment_data)

    def _restore_reputation(self, state: AppState, app_data: dict[str, Any]) -> None:
        """Phase 6+: restore faction reputation.  Missing/legacy saves
        simply leave the default (empty) reputation state.
        """
        rep_data = app_data.get("reputation")
        if not isinstance(rep_data, dict):
            return
        from ..run.reputation import ReputationState

        try:
            state.reputation = ReputationState.from_dict(rep_data)
        except (KeyError, TypeError, ValueError) as exc:
            _log_save_warning(f"reputation restore failed: {exc}")
            state.reputation = ReputationState()

    def _restore_matrix(self, state: AppState, app_data: dict[str, Any]) -> bool:
        """Try to restore the cyberspace MatrixGraph.  Returns True iff
        a valid matrix was deserialised (the caller then recomputes
        layouts; otherwise the player must re-jack-in).
        """
        matrix_data = app_data.get("matrix")
        if not (matrix_data and isinstance(matrix_data, dict)):
            state.matrix = None
            return False
        try:
            from ..matrix.graph import MatrixGraph

            state.matrix = MatrixGraph.from_dict(matrix_data)
            return True
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            # Matrix schema evolved; treat as missing rather than crash.
            state.status_messages.append(
                f">>> Warning: matrix restore failed ({e}), re-jack-in required"
            )
            state.matrix = None
            return False

    def _recompute_layouts(self, matrix: Any) -> dict[str, Any] | None:
        """Rebuild cyberspace_layouts after a successful matrix restore.
        Returns None if the layout computation can't run for any
        reason — the matrix itself is still valid.
        """
        try:
            from ..matrix.graph import compute_layout

            return dict(compute_layout(matrix))
        except (KeyError, TypeError, ValueError, ImportError):
            return None

    def _reset_transient_state(self, state: AppState) -> None:
        """Clear per-run transient objects (combat, cinematic, NPC)
        that we don't serialise and that should start fresh on load.
        """
        state.server_subgraph = None
        state.combat_state = None
        state.cinematic_state = None
        state.npc_state = None
        state.active_event = None
        state.action_menu_open = False
        state.action_menu_index = 0

    def _restore_mission(self, state: AppState, app_data: dict[str, Any]) -> None:
        """Reload the current mission object from the JSON registry
        if its id is present in the save.
        """
        mission_id = app_data.get("current_mission_id")
        if not mission_id:
            return
        from ..missions import JobBoard
        from . import config as _engine_config

        try:
            board = JobBoard.load(_engine_config.DATA_DIR / "missions" / "missions.json")
            state.current_mission = board.get(mission_id)
        except (OSError, json.JSONDecodeError, KeyError, ValueError):
            # Mission JSON missing or unparseable — fall back to no mission.
            state.current_mission = None

    def _restore_screen(self, state: AppState, current_stage: Any) -> None:
        """Choose the right ScreenKind for the saved stage.
        If the matrix was restored and the stage is mid-run, jump
        back into MATRIX; otherwise fall back to HUB.
        """
        from ..run import Stage
        from .state import ScreenKind

        if current_stage in (
            Stage.PENDING,
            Stage.MEET_NPC,
            Stage.EXTRACT_DATA,
            Stage.DEFEAT_ICE,
        ):
            state.screen = ScreenKind.MATRIX if state.matrix is not None else ScreenKind.HUB
        elif current_stage in (Stage.JACK_OUT, Stage.REWARD, Stage.DEBRIEF):
            state.screen = ScreenKind.HUB
        elif current_stage in (Stage.COMPLETE,):
            state.screen = ScreenKind.HUB
        elif current_stage in (Stage.FAILED, Stage.DEATH_RESTART):
            state.screen = ScreenKind.DEATH

    def delete(self, slot: int) -> bool:
        """Delete a save slot.

        Returns:
            True if a file was deleted, False if slot was empty.
        """
        path = self._slot_path(slot)
        if not path.exists():
            return False
        path.unlink()
        return True

    def quick_save(self, state: AppState, elapsed_seconds: int = 0) -> SaveMetadata:
        """Save to the default quick-save slot (1)."""
        return self.save(DEFAULT_SLOT, state, elapsed_seconds)

    def quick_load(self, state: AppState) -> None:
        """Load from the default quick-save slot (1)."""
        self.restore_state(DEFAULT_SLOT, state)
