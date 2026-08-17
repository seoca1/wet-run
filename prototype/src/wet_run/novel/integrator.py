"""High-level integration helpers (ADR-0061).

A thin facade so the engine does not need to know how the novel
layer is wired.  Callers receive ``(catalog, manifest, dispatcher)``
in one call and feed it a player ``AppState`` cursor.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog import NovelCatalog
from .dispatcher import NovelDispatcher
from .manifest import NovelManifest


@dataclass(slots=True)
class NovelRuntime:
    """Bundle of the three pieces the engine needs.

    Pass to combat, narrative, and graphic-novel subsystems to
    dispatch novel hooks without each module re-importing the
    whole novel subpackage.
    """

    catalog: NovelCatalog
    manifest: NovelManifest
    dispatcher: NovelDispatcher


def load_novel_runtime(
    repo_root: Path,
    *,
    manifest_overrides: Path | None = None,
    dry_run: bool = False,
) -> NovelRuntime:
    """Convenience: discover the corpus and build a runtime bundle.

    Args:
        repo_root: The repository root (the directory that contains
            ``Fiction/``).
        manifest_overrides: Optional JSON file with explicit
            manifest entries.
        dry_run: When True, the dispatcher records what *would* have
            happened without mutating any state.  Useful for tests
            and for staging in a future "preview" mode.
    """
    catalog = NovelCatalog.load(repo_root)
    manifest = NovelManifest.from_catalog(catalog)
    overrides = (
        NovelManifest.from_json(manifest_overrides) if manifest_overrides else NovelManifest()
    )
    manifest.entries.update(overrides.entries)
    dispatcher = NovelDispatcher(catalog, manifest, dry_run=dry_run)
    return NovelRuntime(
        catalog=catalog,
        manifest=manifest,
        dispatcher=dispatcher,
    )


def dispatch_for_state(
    runtime: NovelRuntime,
    stem: str,
    app_state: Any,
    *,
    language: str | None = None,
    mission_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> Any:
    """Convenience: pick the language from ``app_state`` and dispatch.

    Falls back to ``"en"`` if ``app_state`` does not expose a
    ``language`` attribute.  Returns the dispatch report.
    """
    if language is None:
        language = getattr(app_state, "language", "en") or "en"
    return runtime.dispatcher.dispatch(
        stem,
        language=language,
        app_state=app_state,
        mission_id=mission_id,
        payload=payload,
    )


__all__ = [
    "NovelRuntime",
    "dispatch_for_state",
    "load_novel_runtime",
]
