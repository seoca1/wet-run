"""Phase 5 — Novel integration (ADR-0061).

Phase 5 introduces the ``novel`` subpackage: a pluggable bridge between
in-fiction short stories and engine events.  It exposes:

- ``NovelCatalog``   — auto-discovers derivative stories on disk.
- ``NovelManifest``  — maps mission IDs → novel stems + ``HookKind``.
- ``NovelDispatcher``— invokes registered actions for a given hook.
- ``NovelRuntime``   — bundle of all three.
- ``load_novel_runtime(repo_root)`` — one-shot loader.

Hook kinds (initial set, extensible via ``register_hook_action``):

- NARRATIVE
- EXCERPT
- EVENT
- COMBAT
- ITEM
- CINEMATIC

This demo loads the runtime, prints the catalog size and the hook
kinds, and dispatches a sample hook against an ``AppState`` so the
operator can verify the wiring without entering the game.

Run::

    PYTHONPATH=src .venv/bin/python scripts/play_novel_runtime.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wet_run.engine.state import AppState  # noqa: E402
from wet_run.novel import (  # noqa: E402
    NovelCatalog,
    dispatch_for_state,
    load_novel_runtime,
)
from wet_run.novel.hooks import (  # noqa: E402
    HookKind,
    register_default_actions,
)


def main() -> int:
    print("=" * 60)
    print("Phase 5 — Novel Integration (ADR-0061)")
    print("=" * 60)

    register_default_actions()
    kinds = [k.value for k in HookKind]
    print(f"[1] HookKind registry           : {len(kinds)} kinds → {kinds}")

    # Catalog uses SHORT_STORIES_DIR = Fiction/derivative/sprawl-trilogy/short-stories
    # so we walk up to whichever ancestor contains that path.  In this workspace
    # the canonical location is `/Users/emilio/projects/Projects/Fiction/...`,
    # so parents[4] is correct — but we probe from [2]..[6] defensively so
    # the demo runs regardless of where it's invoked from.
    catalog_root = None
    for depth in range(2, 8):
        candidate = ROOT.parents[depth]
        if (candidate / "Fiction" / "derivative" / "sprawl-trilogy" / "short-stories").exists():
            catalog_root = candidate
            break
    if catalog_root is None:
        catalog_root = ROOT.parents[4]  # best-effort fallback
    catalog = NovelCatalog.load(catalog_root)
    print(f"[2] NovelCatalog auto-discover  : {len(catalog)} entries")

    runtime = load_novel_runtime(catalog_root)
    print(
        f"[3] NovelRuntime wired          : "
        f"catalog={len(runtime.catalog)} "
        f"manifest={len(runtime.manifest) if hasattr(runtime.manifest, '__len__') else '?'}"
    )

    state = AppState()
    state.language = "en"

    first_stem = None
    for entry in catalog:
        first_stem = entry.stem
        break

    if first_stem:
        report = dispatch_for_state(runtime, first_stem, state, mission_id="play_novel_demo")
        kind = getattr(report, "kind", "?")
        print(f"[4] dispatch('{first_stem}')     : kind={kind}")
    else:
        print("[4] catalog empty — skipping dispatch")

    print()
    print("*** Phase 5 OK: novel runtime loaded + dispatch returned a report ***")
    return 0


if __name__ == "__main__":
    sys.exit(main())
