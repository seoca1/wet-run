"""Dispatcher (ADR-0061).

Bridges the manifest and the hook actions.  Given a story stem and
the player's current language, the dispatcher:

    1. Looks up the entry in the catalog.
    2. Resolves the manifest entry (or returns the NARRATIVE default).
    3. Reads the first paragraph of the story as ``excerpt``.
    4. Invokes every registered action for each kind (primary first,
       then every secondary).
    5. Aggregates the resulting ``HookResult`` objects into a single
       dispatch report.

``dispatch_hooks`` is a thin convenience wrapper suitable for
``AppState.on_event``-style flows; ``NovelDispatcher`` is reusable
across runs and exposes some knobs (e.g. dry-run mode).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .catalog import NovelCatalog, NovelEntry
from .hooks import HookContext, HookKind, HookResult, get_hook_actions
from .manifest import NovelManifest, TextProvider


@dataclass(slots=True)
class DispatchReport:
    """Summary of a single dispatch.

    Attributes:
        stem: The story dispatched.
        language: ``"en"`` or ``"ko"``.
        kinds_fired: Kinds actually invoked (in order).
        results: One ``HookResult`` per kind (matches ``kinds_fired``).
        dry_run: True if no actions were executed.
    """

    stem: str
    language: str
    kinds_fired: list[HookKind] = field(default_factory=list)
    results: list[HookResult] = field(default_factory=list)
    dry_run: bool = False


class NovelDispatcher:
    """Reusable dispatcher combining catalog + manifest.

    The dispatcher caches nothing across runs (it is cheap).  Create
    one per process and pass it around.
    """

    __slots__ = (
        "catalog",
        "manifest",
        "text_provider",
        "dry_run",
    )

    def __init__(
        self,
        catalog: NovelCatalog,
        manifest: NovelManifest,
        *,
        text_provider: TextProvider | None = None,
        dry_run: bool = False,
    ) -> None:
        """Bind a catalog + manifest and pick a text source.

        ``text_provider`` defaults to a fresh ``TextProvider`` so the
        dispatcher works in tests without setup. ``dry_run=True``
        suppresses side-effects (file writes, telemetry) so callers
        can preview a dispatch without committing to it.
        """
        self.catalog = catalog
        self.manifest = manifest
        self.text_provider = text_provider or TextProvider()
        self.dry_run = dry_run

    def dispatch(
        self,
        stem: str,
        *,
        language: str = "en",
        app_state: Any = None,
        mission_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> DispatchReport:
        """Dispatch hooks for ``stem``.

        Returns a report regardless of whether the stem is known —
        an unknown stem fires the default NARRATIVE hook on whatever
        ``excerpt`` was supplied.
        """
        entry = self.catalog.by_stem(stem)
        manifest_entry = self.manifest.resolve(stem)
        kinds = manifest_entry.kinds()
        excerpt = _read_excerpt(entry, self.text_provider, language)
        payload = dict(payload or {})
        if mission_id is not None:
            payload.setdefault("mission_id", mission_id)

        report = DispatchReport(
            stem=stem,
            language=language,
            kinds_fired=list(kinds),
            dry_run=self.dry_run,
        )

        for kind in kinds:
            ctx = HookContext(
                story_stem=stem,
                kind=kind,
                language=language,
                excerpt=excerpt,
                mission_id=mission_id,
                payload=payload,
            )
            for action in get_hook_actions(kind):
                if self.dry_run:
                    report.results.append(
                        HookResult(
                            ok=True,
                            messages=[f"[dry-run] {action.__name__} ({kind.value})"],
                        )
                    )
                    continue
                result = action(ctx, app_state)
                report.results.append(result)
        return report


def dispatch_hooks(
    stem: str,
    *,
    catalog: NovelCatalog,
    manifest: NovelManifest,
    language: str = "en",
    app_state: Any = None,
    mission_id: str | None = None,
    payload: dict[str, Any] | None = None,
    text_provider: TextProvider | None = None,
    dry_run: bool = False,
) -> DispatchReport:
    """One-shot helper.

    Constructs a transient ``NovelDispatcher`` and dispatches once.
    Suitable for scripting (e.g. tests, one-off benchmarks); for the
    runtime engine, instantiate ``NovelDispatcher`` once at startup
    to share the manifest across dispatches.
    """
    disp = NovelDispatcher(
        catalog,
        manifest,
        text_provider=text_provider,
        dry_run=dry_run,
    )
    return disp.dispatch(
        stem,
        language=language,
        app_state=app_state,
        mission_id=mission_id,
        payload=payload,
    )


def _read_excerpt(
    entry: NovelEntry | None,
    text_provider: TextProvider,
    language: str,
) -> str:
    """Return the first paragraph of the entry's body, or empty if unknown."""
    if entry is None:
        return ""
    return text_provider.head(entry, lang=language, paragraphs=1)


__all__ = [
    "DispatchReport",
    "NovelDispatcher",
    "dispatch_hooks",
]
