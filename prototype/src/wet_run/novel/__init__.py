"""Novel integration subpackage (Phase 5, ADR-0061).

A bridge between the derivative fiction corpus
(``Fiction/derivative/sprawl-trilogy/``) and the gameplay surfaces
(matrix nodes, hub, combat, graphic novel).  Designed to scale:

- Adding a new short story requires only that the file be dropped
  into ``short-stories/`` — the catalog auto-discovers it.
- Adding a new novel-length work or episodic bundle requires a single
  entry in ``manifest.py`` or an automated mapping derived from
  metadata.
- Adding a new *kind* of in-game effect requires adding a single
  ``HookAction`` function in ``hooks.py``.

The four layers:

    1. ``catalog.py``   : discovers and surfaces story metadata
    2. ``hooks.py``     : declares the runtime action kinds (event,
                          combat, item, excerpt, cinematic)
    3. ``manifest.py``  : maps story stems -> hook kinds
    4. ``dispatcher.py``: invokes the matching ``HookAction`` at
                          runtime, given an ``AppState`` cursor
"""

from __future__ import annotations

# Re-export the public surface for ``import novel.X``.
from .catalog import NovelCatalog, NovelEntry, NovelFormat  # noqa: F401
from .dispatcher import (  # noqa: F401
    DispatchReport,
    NovelDispatcher,
    dispatch_hooks,
)
from .hooks import (  # noqa: F401
    HookAction,
    HookContext,
    HookKind,
    HookResult,
    get_hook_actions,
    register_hook_action,
    reset_hook_registry,
)
from .integrator import (  # noqa: F401
    NovelRuntime,
    dispatch_for_state,
    load_novel_runtime,
)
from .manifest import (  # noqa: F401
    ManifestEntry,
    NovelManifest,
    TextProvider,
    infer_default_hook,
)

__all__ = [
    "DispatchReport",
    "HookAction",
    "HookContext",
    "HookKind",
    "HookResult",
    "ManifestEntry",
    "NovelCatalog",
    "NovelDispatcher",
    "NovelEntry",
    "NovelFormat",
    "NovelManifest",
    "NovelRuntime",
    "TextProvider",
    "dispatch_for_state",
    "dispatch_hooks",
    "get_hook_actions",
    "infer_default_hook",
    "load_novel_runtime",
    "register_hook_action",
    "reset_hook_registry",
]
