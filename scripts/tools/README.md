# Wet Run Tools

> **Parent**: `Game/wet_run/`
> **Updated**: 2026-09-23

Python utilities for `Game/wet_run/`. After the 2026-09-15 consolidation retired
the Python prototype, the only remaining tools are the wikilink audits — the
build/data-export scripts went with the `prototype/` source they read.

## Audit

| Tool | Purpose | Usage |
|------|---------|-------|
| **`audit_sprawl.py`** | Project-scoped wikilink integrity check (broken links + orphans) | `python3 scripts/tools/audit_sprawl.py` |
| **`find_broken_links.py`** | Find broken wikilinks with file:line:target detail; resolves cross-project Fiction wiki references per AGENTS.md §4.1 | `python3 scripts/tools/find_broken_links.py` |

> Both scripts resolve paths from their own location, so they run from any cwd. `audit_sprawl.py` is the more comprehensive tool; `find_broken_links.py` provides detailed per-line output for debugging. Both include the vault-wide `audit_vault.py` cross-project resolution behavior (Fiction wiki).

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
