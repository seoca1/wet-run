"""Save/restore graphic novel progress (ADR-0044).

Persists where the player left off in the graphic novel so they can
resume via "CONTINUE READING" instead of restarting from the
prologue.

This is a separate save system from SaveManager (which handles the
main game Run state). The graphic novel is read-only progress:
    - mode: prologue | novice | veteran | heretic
    - scene_index / dialogue_index: where to resume
    - elapsed_in_dialogue_ms: how far the typing cursor was
    - character_id: which chain (only for mode=prologue)

Save file: ``<save_dir>/gn_progress.json``
Default save_dir: ``<project_root>/data/saves/`` (single slot)

Versioning:
    - GN_SAVE_VERSION = "1.2.0"  (1.0.0 → 1.1.0: `ending` A/B; 1.1.0 → 1.2.0: `ending` A/B/C, ADR-0049)
    - On mismatch, SaveVersionMismatchError raised
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ============================================================================
# Format
# ============================================================================


GN_SAVE_VERSION = "1.2.0"
DEFAULT_SAVE_PATH = Path("data/saves/gn_progress.json")
GN_SAVE_SLOTS = 3  # ADR-0051: 3 save slots
SAVE_SLOT_PATTERN = "gn_progress_slot_{slot_id}.json"


def slot_path(slot_id: int) -> Path:
    """Return the canonical save path for the given slot (1-indexed).

    Args:
        slot_id: Slot number (1..GN_SAVE_SLOTS).

    Returns:
        Path like ``data/saves/gn_progress_slot_1.json``.

    Raises:
        ValueError: If slot_id is out of range.
    """
    if not (1 <= slot_id <= GN_SAVE_SLOTS):
        raise ValueError(f"slot_id must be 1..{GN_SAVE_SLOTS}, got {slot_id}")
    return Path("data/saves") / SAVE_SLOT_PATTERN.format(slot_id=slot_id)


# ============================================================================
# Errors
# ============================================================================


class GNSaveError(Exception):
    """Base class for graphic novel save errors."""


class GNSaveEmptyError(GNSaveError):
    """No save exists at the given path."""


class GNSaveVersionMismatchError(GNSaveError):
    """Save file version doesn't match current code version."""


class GNSaveCorruptedError(GNSaveError):
    """Save file is corrupted or unreadable."""


# ============================================================================
# Data
# ============================================================================


@dataclass(frozen=True, slots=True)
class GNProgress:
    """Snapshot of graphic novel progress.

    Attributes:
        mode: "prologue" | "novice" | "veteran" | "heretic"
        scene_index: 0-based index of the current scene in the chain
        dialogue_index: 0-based index of the current dialogue in the scene
        elapsed_in_dialogue_ms: How far the typing cursor is in the current dialogue
        character_id: Which character the chain is anchored to (always set:
            "novice"/"veteran"/"heretic" for single-character modes; the
            first char in prologue shuffle)
        chain_length: Total scenes in the chain (used to detect mismatched saves)
        ending: "A" (default), "B" or "C" — which ending variant
            (ADR-0046, ADR-0048, ADR-0049).
            Saves from v1.0.0 (no ``ending`` key) default to "A".
            Forward-compat: unknown values default to "A".
        saved_at: ISO 8601 UTC timestamp
        session_id: Unique ID for this save (so multiple sessions don't clobber)
    """

    mode: str
    scene_index: int
    dialogue_index: int
    elapsed_in_dialogue_ms: float
    character_id: str
    chain_length: int
    saved_at: str
    ending: str = "A"
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self) -> dict[str, Any]:
        """Serialize this snapshot to a plain dict (JSON-friendly).

        Returns:
            Dict containing all dataclass fields in declaration order.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GNProgress:
        """Build a :class:`GNProgress` from a previously serialized dict.

        Coerces all fields defensively: missing keys fall back to defaults,
        unknown ``ending`` values collapse to ``"A"``, and numeric fields
        are recovered via ``_safe_int`` / ``_safe_float`` so a corrupted
        save file does not raise. Forward-compatible with older v1.0.0
        saves that lack an ``ending`` key.

        Args:
            data: Dict produced by :meth:`to_dict` (or a previous save file).

        Returns:
            A fully-populated :class:`GNProgress` instance.
        """
        ending_raw = str(data.get("ending", "A"))
        if ending_raw not in ("A", "B", "C"):
            ending_raw = "A"  # unknown values default to A (forward-compat)

        def _safe_int(key: str, default: int = 0) -> int:
            """Read ``data[key]`` and coerce to ``int``.

            Falls back to ``default`` if the key is missing or the value
            cannot be parsed as an integer.
            """
            try:
                return int(str(data.get(key, default)))
            except (TypeError, ValueError):
                return default

        def _safe_float(key: str, default: float = 0.0) -> float:
            """Read ``data[key]`` and coerce to ``float``.

            Falls back to ``default`` if the key is missing or the value
            cannot be parsed as a float.
            """
            try:
                return float(str(data.get(key, default)))
            except (TypeError, ValueError):
                return default

        return cls(
            mode=str(data.get("mode", "prologue")),
            scene_index=_safe_int("scene_index", 0),
            dialogue_index=_safe_int("dialogue_index", 0),
            elapsed_in_dialogue_ms=_safe_float("elapsed_in_dialogue_ms", 0.0),
            character_id=str(data.get("character_id", "novice")),
            chain_length=_safe_int("chain_length", 0),
            saved_at=str(data.get("saved_at", "")),
            ending=ending_raw,
            session_id=str(data.get("session_id", uuid.uuid4().hex[:12])),
        )


# ============================================================================
# Persistence
# ============================================================================


def _default_save_path() -> Path:
    """Return the default save path."""
    return DEFAULT_SAVE_PATH


def has_gn_save(save_path: Path | None = None) -> bool:
    """Return True if a graphic novel save exists at the given path.

    Args:
        save_path: Path to gn_progress.json. Defaults to ``data/saves/gn_progress.json``.

    Returns:
        True if a save file exists and is valid.
    """
    path = save_path or _default_save_path()
    return path.exists() and path.is_file()


def save_gn_progress(
    progress: GNProgress,
    save_path: Path | None = None,
) -> Path:
    """Persist GN progress to disk atomically.

    Uses temp file + rename to avoid leaving a half-written save if
    interrupted.

    Args:
        progress: GNProgress dataclass to save.
        save_path: Where to save. Defaults to ``data/saves/gn_progress.json``.

    Returns:
        The path the save was written to.

    Raises:
        GNSaveError: If the directory cannot be created or written.
    """
    path = save_path or _default_save_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "version": GN_SAVE_VERSION,
        "saved_at": datetime.now(UTC).isoformat(),
        "progress": progress.to_dict(),
    }

    # Atomic write: write to temp, then rename
    fd, tmp_name = tempfile.mkstemp(prefix=".gn_progress_", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        # Atomic rename (POSIX)
        os.replace(tmp_name, path)
    except Exception:
        # Clean up temp on failure
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise

    return path


# GN migration chain. Same pattern as save_manager._SAVE_MIGRATIONS:
# list of (source_version, target_version, transform) tuples. Transforms
# take a parsed save dict and return the upgraded dict. The chain is
# walked in order until the dict reaches GN_SAVE_VERSION.
#
# History:
#   <legacy>  → 1.0.0   inject version key
#   1.0.0     → 1.1.0   add `ending` field (ADR-0048)
#   1.1.0     → 1.2.0   ending now supports A/B/C (ADR-0049)
_GN_SAVE_MIGRATIONS: list[tuple[str, str, Any]] = [
    (
        "<legacy>",
        "1.0.0",
        lambda data: {**data, "version": "1.0.0"},
    ),
    (
        "1.0.0",
        "1.1.0",
        lambda data: {
            **data,
            "version": "1.1.0",
            "progress": {
                **data.get("progress", {}),
                "ending": data.get("progress", {}).get("ending", "A"),
            },
        },
    ),
    (
        "1.1.0",
        "1.2.0",
        # ending letters stay compatible (A/B/C); just bump version.
        lambda data: {**data, "version": "1.2.0"},
    ),
]


def _migrate_gn_data(data: dict[str, Any]) -> dict[str, Any]:
    """Apply GN version migrations until data reaches GN_SAVE_VERSION.

    Walks ``_GN_SAVE_MIGRATIONS`` from the data's current version to
    ``GN_SAVE_VERSION``. If a version in the chain is missing,
    raises GNSaveVersionMismatchError (cannot auto-upgrade across gaps).
    """
    current = data.get("version", "<legacy>")
    target = GN_SAVE_VERSION

    if current == target:
        return data

    while current != target:
        next_step = next(
            (m for m in _GN_SAVE_MIGRATIONS if m[0] == current),
            None,
        )
        if next_step is None:
            raise GNSaveVersionMismatchError(
                f"No migration path from GN save version {current!r} to {target!r}"
            )
        _, successor, transform = next_step
        data = transform(data)
        current = successor

    return data


def load_gn_progress(save_path: Path | None = None) -> GNProgress:
    """Load GN progress from disk.

    Args:
        save_path: Where to load from. Defaults to ``data/saves/gn_progress.json``.

    Returns:
        The persisted GNProgress.

    Raises:
        GNSaveEmptyError: If no save exists at the path.
        GNSaveVersionMismatchError: If save version doesn't match
            and no migration path exists.
        GNSaveCorruptedError: If save file can't be parsed.
    """
    path = save_path or _default_save_path()

    if not path.exists():
        raise GNSaveEmptyError(f"No graphic novel save at {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise GNSaveCorruptedError(f"Save file is not valid JSON: {e}") from e

    migrated = _migrate_gn_data(raw)
    version = migrated.get("version")
    if version != GN_SAVE_VERSION:
        raise GNSaveVersionMismatchError(f"Save version {version!r} != current {GN_SAVE_VERSION!r}")

    progress_data = migrated.get("progress", {})
    if not isinstance(progress_data, dict):
        raise GNSaveCorruptedError("Save progress is not a dict")

    return GNProgress.from_dict(progress_data)


def delete_gn_progress(save_path: Path | None = None) -> bool:
    """Delete the GN progress save if it exists.

    Args:
        save_path: Path to delete. Defaults to ``data/saves/gn_progress.json``.

    Returns:
        True if a save was deleted, False if no save existed.
    """
    path = save_path or _default_save_path()
    if not path.exists():
        return False
    path.unlink()
    return True


# ============================================================================
# Convenience helpers
# ============================================================================


def make_progress(
    mode: str,
    scene_index: int,
    dialogue_index: int,
    elapsed_in_dialogue_ms: float,
    character_id: str,
    chain_length: int,
    ending: str = "A",
) -> GNProgress:
    """Construct a GNProgress with current UTC timestamp.

    Args:
        mode: "prologue" | "novice" | "veteran" | "heretic"
        scene_index: 0-based scene index.
        dialogue_index: 0-based dialogue index.
        elapsed_in_dialogue_ms: typing cursor position.
        character_id: novice/veteran/heretic anchor.
        chain_length: total scenes in the chain.
        ending: "A" (default) or "B" — which ending variant (ADR-0048).

    Returns:
        A fresh GNProgress with saved_at = now.
    """
    return GNProgress(
        mode=mode,
        scene_index=scene_index,
        dialogue_index=dialogue_index,
        elapsed_in_dialogue_ms=elapsed_in_dialogue_ms,
        character_id=character_id,
        chain_length=chain_length,
        ending=ending,
        saved_at=datetime.now(UTC).isoformat(),
    )


def progress_to_dict(progress: GNProgress) -> dict[str, Any]:
    """Convert a GNProgress to a JSON-safe dict (alias for to_dict)."""
    return progress.to_dict()


# ============================================================================
# Multi-slot API (ADR-0051)
# ============================================================================


def has_gn_save_slot(slot_id: int, save_dir: Path | None = None) -> bool:
    """Return True if a save exists in the given slot.

    Args:
        slot_id: Slot number (1..GN_SAVE_SLOTS).
        save_dir: Optional override for save directory.

    Returns:
        True if the slot's save file exists.
    """
    path = _slot_path_with_dir(slot_id, save_dir)
    return path.exists() and path.is_file()


def save_gn_progress_slot(
    progress: GNProgress,
    slot_id: int,
    save_dir: Path | None = None,
) -> Path:
    """Save GNProgress to a specific slot (atomic write).

    Args:
        progress: GNProgress dataclass.
        slot_id: Slot number (1..GN_SAVE_SLOTS).
        save_dir: Optional override for save directory.

    Returns:
        The path the save was written to.
    """
    path = _slot_path_with_dir(slot_id, save_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": GN_SAVE_VERSION,
        "saved_at": datetime.now(UTC).isoformat(),
        "slot_id": slot_id,
        "progress": progress.to_dict(),
    }
    fd, tmp_name = tempfile.mkstemp(prefix=f".gn_slot{slot_id}_", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return path


def load_gn_progress_slot(slot_id: int, save_dir: Path | None = None) -> GNProgress:
    """Load GNProgress from a specific slot.

    Raises:
        GNSaveEmptyError: If no save exists at the slot path.
        GNSaveVersionMismatchError: If save version doesn't match.
        GNSaveCorruptedError: If save file can't be parsed.
    """
    path = _slot_path_with_dir(slot_id, save_dir)
    if not path.exists():
        raise GNSaveEmptyError(f"No graphic novel save at slot {slot_id} ({path})")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise GNSaveCorruptedError(f"Save file is not valid JSON: {e}") from e
    version = raw.get("version")
    if version != GN_SAVE_VERSION:
        raise GNSaveVersionMismatchError(f"Save version {version!r} != current {GN_SAVE_VERSION!r}")
    progress_data = raw.get("progress", {})
    if not isinstance(progress_data, dict):
        raise GNSaveCorruptedError("Save progress is not a dict")
    return GNProgress.from_dict(progress_data)


def delete_gn_progress_slot(slot_id: int, save_dir: Path | None = None) -> bool:
    """Delete the save in the given slot. Returns True if deleted."""
    path = _slot_path_with_dir(slot_id, save_dir)
    if not path.exists():
        return False
    path.unlink()
    return True


def list_save_slots(save_dir: Path | None = None) -> list[dict[str, Any]]:
    """List all GN save slots with metadata.

    Returns:
        List of dicts, one per slot, in slot_id order:
            {
                "slot_id": int (1..GN_SAVE_SLOTS),
                "exists": bool,
                "progress": GNProgress | None,
                "saved_at": str (ISO 8601) | None,
                "mtime": float | None,  # file modification time (epoch seconds)
            }
    """
    base = save_dir or Path("data/saves")
    result: list[dict[str, Any]] = []
    for slot_id in range(1, GN_SAVE_SLOTS + 1):
        path = base / SAVE_SLOT_PATTERN.format(slot_id=slot_id)
        if not path.exists():
            result.append(
                {
                    "slot_id": slot_id,
                    "exists": False,
                    "has_save": False,
                    "progress": None,
                    "saved_at": None,
                    "mtime": None,
                }
            )
            continue
        try:
            progress = load_gn_progress_slot(slot_id, save_dir=save_dir)
            raw = json.loads(path.read_text(encoding="utf-8"))
            result.append(
                {
                    "slot_id": slot_id,
                    "exists": True,
                    "has_save": True,
                    "progress": progress,
                    "saved_at": raw.get("saved_at"),
                    "mtime": path.stat().st_mtime,
                }
            )
        except GNSaveError:
            # Corrupted slot — show as exists but progress=None
            result.append(
                {
                    "slot_id": slot_id,
                    "exists": True,
                    "has_save": False,
                    "progress": None,
                    "saved_at": None,
                    "mtime": path.stat().st_mtime,
                }
            )
    return result


def _slot_path_with_dir(slot_id: int, save_dir: Path | None) -> Path:
    """Return the slot path, optionally overriding the save directory."""
    if save_dir is not None:
        return save_dir / SAVE_SLOT_PATTERN.format(slot_id=slot_id)
    return slot_path(slot_id)


def migrate_legacy_single_slot() -> bool:
    """Migrate the legacy single-slot save (ADR-0044) to slot 1.

    Returns:
        True if a migration was performed, False otherwise.

    If ``data/saves/gn_progress.json`` exists and slot 1 is empty, the
    file is renamed to ``gn_progress_slot_1.json``. If both exist, the
    legacy file is left alone (slot 1 wins).
    """
    legacy = Path("data/saves/gn_progress.json")
    slot1 = slot_path(1)
    if not legacy.exists():
        return False
    if slot1.exists():
        # Both exist — keep slot 1, leave legacy alone (no data loss)
        return False
    slot1.parent.mkdir(parents=True, exist_ok=True)
    legacy.rename(slot1)
    return True
