"""MetaState disk persistence (load/save/atomic write/migration).

ADR-0131. Operates on `data/saves/meta_state.json` with atomic write
(temp file + rename) to prevent corruption on crash mid-write.

This is a *separate* file from per-run save slots — it tracks cross-run
meta progression (faction reputation persistence, future: Hall of Dead
and achievements).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from ..run.meta_state import META_STATE_VERSION, MetaState

_LOG = logging.getLogger(__name__)

# Default location — relative to project data dir.
DEFAULT_META_STATE_FILENAME = "meta_state.json"


def default_meta_state_path(data_dir: Path) -> Path:
    """Resolve the canonical path to meta_state.json.

    Args:
        data_dir: Project's data directory (typically ``prototype/data``).

    Returns:
        Path to ``data_dir/saves/meta_state.json``.
    """
    return data_dir / "saves" / DEFAULT_META_STATE_FILENAME


def load_meta_state(path: Path) -> MetaState:
    """Load MetaState from disk. Returns empty MetaState if file missing/corrupt.

    Args:
        path: Absolute path to meta_state.json.

    Returns:
        Restored MetaState, or empty default if the file is missing,
        empty, malformed, or has an incompatible schema version.
    """
    if not path.exists():
        return MetaState()
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        _LOG.warning("meta_state.json unreadable (%s); using empty default", exc)
        return MetaState()
    if not isinstance(data, dict):
        return MetaState()
    state = MetaState.from_dict(data)
    if state.version > META_STATE_VERSION:
        _LOG.warning(
            "meta_state.json version %s > runtime %s; using empty default",
            state.version,
            META_STATE_VERSION,
        )
        return MetaState()
    return state


def save_meta_state(state: MetaState, path: Path) -> None:
    """Persist MetaState to disk with atomic write semantics.

    Writes to a sibling temp file first, then renames atomically. This
    prevents corruption if the process is killed mid-write.

    Args:
        state: The MetaState to persist.
        path: Destination file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(state.to_dict(), indent=2, ensure_ascii=False, sort_keys=True)
    try:
        with tmp.open("w", encoding="utf-8") as f:
            f.write(payload)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except OSError as exc:
        _LOG.warning("meta_state.json write failed (%s)", exc)
        # Best-effort cleanup of temp file
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def reset_meta_state(path: Path) -> None:
    """Delete the meta state file (testing/admin only).

    Args:
        path: Path to meta_state.json to delete.
    """
    if path.exists():
        try:
            path.unlink()
        except OSError as exc:
            _LOG.warning("meta_state.json delete failed (%s)", exc)


__all__ = [
    "DEFAULT_META_STATE_FILENAME",
    "default_meta_state_path",
    "load_meta_state",
    "reset_meta_state",
    "save_meta_state",
]
