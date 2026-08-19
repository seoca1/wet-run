"""Novel Hook integration with engine runtime (ADR-0061).

Bridges the in-fiction ``short-stories/`` corpus to gameplay events:

- Mission completion → ``mission_to_stem()`` → ``dispatch_for_state()``.
- Lazy-loads the ``NovelRuntime`` once and caches it module-side.
- Best-effort: any error is swallowed and surfaced via
  ``state.status_messages`` so a missing file or bad manifest cannot
  crash gameplay.

Public API:

- ``mission_to_stem(mission_id)``             — raw ``missions.json`` lookup.
- ``trigger_mission_completion_novel_hooks``  — main entry point for
                                                 gameplay code.
- ``reset_novel_runtime_cache``               — test helper.

The wiring point lives in ``engine/reward_view.return_to_hub_from_reward``.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ..data.story_resolver import list_available_stems
from ..novel import NovelRuntime, dispatch_for_state, load_novel_runtime

_log = logging.getLogger(__name__)

# Repo root for the NovelCatalog (parent of Fiction/). Cached on first use.
_REPO_ROOT: Path | None = None

# Module-level runtime cache. Lazy-init.
_RUNTIME: NovelRuntime | None = None

# Lazy-loaded missions.json (full dict: mission_id -> raw record w/ story.source).
_MISSIONS_RAW: dict[str, dict[str, Any]] | None = None
_MISSIONS_PATH: Path | None = None


def _find_repo_root() -> Path:
    """Locate the workspace root (Projects/) by walking up from this file."""
    global _REPO_ROOT
    if _REPO_ROOT is not None:
        return _REPO_ROOT

    here = Path(__file__).resolve()
    for ancestor in [here, *here.parents]:
        if (ancestor / "Fiction" / "derivative" / "sprawl-trilogy" / "short-stories").exists():
            _REPO_ROOT = ancestor
            return _REPO_ROOT

    raise RuntimeError(
        "novel_integration: could not find repo root with "
        "Fiction/derivative/sprawl-trilogy/short-stories/."
    )


def _find_missions_path() -> Path:
    """Locate the live ``missions.json`` shipped with the engine."""
    global _MISSIONS_PATH
    if _MISSIONS_PATH is not None and _MISSIONS_PATH.exists():
        return _MISSIONS_PATH

    root = _find_repo_root()
    candidate = root / "Game" / "wet_run" / "prototype" / "data" / "missions" / "missions.json"
    if candidate.exists():
        _MISSIONS_PATH = candidate
        return _MISSIONS_PATH

    raise RuntimeError(f"novel_integration: missions.json not found at {candidate}")


def _get_runtime() -> NovelRuntime:
    """Lazy-loaded, cached ``NovelRuntime``."""
    global _RUNTIME
    if _RUNTIME is None:
        root = _find_repo_root()
        _RUNTIME = load_novel_runtime(root)
    return _RUNTIME


def _load_missions_raw() -> dict[str, dict[str, Any]]:
    """Lazy-load the ``missions.json`` raw dict (mission_id -> record)."""
    global _MISSIONS_RAW
    if _MISSIONS_RAW is None:
        path = _find_missions_path()
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        _MISSIONS_RAW = data if isinstance(data, dict) else {}
    return _MISSIONS_RAW


def reset_novel_runtime_cache() -> None:
    """Test helper: drop cached runtime + missions + repo root.

    The next call to ``trigger_mission_completion_novel_hooks`` will
    rebuild everything from scratch.
    """
    global _REPO_ROOT, _RUNTIME, _MISSIONS_RAW, _MISSIONS_PATH
    _REPO_ROOT = None
    _RUNTIME = None
    _MISSIONS_RAW = None
    _MISSIONS_PATH = None


def mission_to_stem(mission_id: str) -> str | None:
    """Resolve a ``mission_id`` to its ``story.source`` novel stem.

    Args:
        mission_id: The mission id (e.g. ``"first_jack"``).

    Returns:
        The short-story stem (e.g. ``"case_jackout-30sec"``) if the
        mission has a ``story.source`` and the source exists on disk.
        Returns ``None`` if either the mission is unknown, the source
        is missing, or the source has no matching short story.
    """
    raw = _load_missions_raw()
    record = raw.get(mission_id)
    if not isinstance(record, dict):
        return None
    story = record.get("story")
    if not isinstance(story, dict):
        return None
    stem = story.get("source")
    if not isinstance(stem, str) or not stem:
        return None

    available = set(list_available_stems(_find_repo_root()))
    return stem if stem in available else None


def trigger_mission_completion_novel_hooks(
    app_state: Any,
    mission_id: str,
) -> dict[str, Any] | None:
    """Fire the novel hook chain for a completed mission.

    Looks up the mission's ``story.source`` stem and dispatches all
    hooks registered for it (NARRATIVE / EXCERPT / EVENT / COMBAT /
    ITEM / CINEMATIC). Status messages are appended to ``app_state``.

    Args:
        app_state: The live ``AppState`` (or anything with a
            ``status_messages`` list).
        mission_id: The completed mission's id.

    Returns:
        A small summary dict ``{"stem": ..., "kind": ..., "ok": bool,
        "messages": [...]}`` or ``None`` if the mission has no novel
        mapping. Failures are swallowed and logged so a missing file
        cannot break gameplay.
    """
    stem = mission_to_stem(mission_id)
    if stem is None:
        return None

    try:
        runtime = _get_runtime()
        report = dispatch_for_state(
            runtime,
            stem,
            app_state,
            mission_id=mission_id,
        )
    except Exception as exc:  # pragma: no cover — defensive
        _log.warning("novel hook dispatch failed for %s: %s", mission_id, exc)
        return {
            "stem": stem,
            "kind": "error",
            "ok": False,
            "messages": [f"!! Novel hook failed: {exc!s}"],
        }

    kind = getattr(report, "kind", None)
    kind_value = getattr(kind, "value", kind)

    # DispatchReport has no top-level "messages" field; aggregate from
    # results (one HookResult per kind).
    results = list(getattr(report, "results", []) or [])
    messages: list[str] = []
    ok = True
    for r in results:
        if not getattr(r, "ok", True):
            ok = False
        messages.extend(getattr(r, "messages", []) or [])

    if hasattr(app_state, "status_messages"):
        if ok:
            app_state.status_messages.append(f">>> Novel hook fired: {stem} ({kind_value})")
        else:
            app_state.status_messages.append(f"!! Novel hook failed: {stem} ({kind_value})")

    return {
        "stem": stem,
        "kind": kind_value,
        "ok": ok,
        "messages": messages,
    }


__all__ = [
    "mission_to_stem",
    "reset_novel_runtime_cache",
    "trigger_mission_completion_novel_hooks",
]
