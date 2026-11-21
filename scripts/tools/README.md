# Wet Run Tools

> **Parent**: `Game/wet_run/`
> **Updated**: 2026-09-23

Python utilities for `Game/wet_run/`. After the 2026-09-15 consolidation retired
the Python prototype, the only remaining tools are the wikilink audits — the
build/data-export scripts went with the `prototype/` source they read.

## Audit

| Tool | Purpose | Usage |
|------|---------|-------|
| **`find_broken_links.py`** | Find broken wikilinks with file:line:target detail; resolves cross-project Fiction wiki references per AGENTS.md §4.1. Exits 1 on any broken link, so it can gate. | `python3 scripts/tools/find_broken_links.py` |

> For **orphan pages** and the vault-wide (whole-workspace) link audit, use the
> workspace tool `scripts/audit_vault.py` (run from the workspace root) — it already
> covers everything under `Game/wet_run/`.

## Removed (2026-11-18, ADR-0334)

`audit_sprawl.py` was deleted. It duplicated `find_broken_links.py` (same ROOT,
EXCLUDE, strip, regex) **and could never fail** — `main()` had no `sys.exit`, so it
exited 0 even with broken links. A checker that cannot fail is not a gate; keeping
it invited false confidence. Orphan detection lives in `audit_vault.py`.

## Removed (2026-09-23)

`build_dashboard.py`, `build_static_data.py` and `fix_scene_data_drift.py` read
`prototype/data/` and/or wrote `dashboard/` — both removed in the 2026-09-15
consolidation. They could no longer run, so they were deleted (recoverable from
git history). Game data now lives at `web/src/data/*.json`, hand-maintained.

## Conventions

- Python 3.11+
- Audit tools are read-only

## See also

- `Game/wet_run/CHANGELOG.md` — change history
- `Game/wet_run/AGENTS.md` — project conventions
