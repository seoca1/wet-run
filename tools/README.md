# Wet Run Tools

> **Parent**: `Game/wet_run/` Python roguelike project
> **Updated**: 2026-07-28

Python build and data-prep utilities for the wet_run prototype.

## Structure

```
Game/wet_run/tools/
├── build_dashboard.py    # Build static dashboard JSON for GitHub Pages
└── build_static_data.py  # Generate static game data (missions, items, etc.)
```

## Tools

### Active

| Tool | Purpose | Usage |
|------|---------|-------|
| **`build_dashboard.py`** | Generate dashboard JSON (Story, Stages, Combat, Equipment, Cyberspace) | `python3 tools/build_dashboard.py` |
| **`build_static_data.py`** | Generate static game data files | `python3 tools/build_static_data.py` |

Both tools feed `data/` (consumed by prototype runtime) and `docs/dashboards/` (consumed by GitHub Pages deploy).

## Audit

| Tool | Purpose | Usage |
|------|---------|-------|
| **`audit_sprawl.py`** | Project-scoped wikilink integrity check (broken links + orphans) | `cd Game/wet_run && python3 tools/audit_sprawl.py` |
| **`find_broken_links.py`** | Find broken wikilinks with file:line:target detail; resolves cross-project Fiction wiki references per AGENTS.md §4.1 | `cd Game/wet_run && python3 tools/find_broken_links.py` |

> Both scripts use `ROOT = Path(".")` — must be run from `Game/wet_run/` directory. `audit_sprawl.py` is the more comprehensive tool; `find_broken_links.py` provides detailed per-line output for debugging. Both include the vault-wide `audit_vault.py` cross-project resolution behavior (Fiction wiki).

## Conventions

- Python 3.11+
- Each tool reads from `prototype/src/data/` constants and writes to `data/` and `docs/dashboards/`
- Re-run before deploy to refresh dashboard data

## See also

- `Game/wet_run/prototype/Makefile` — top-level build targets (`build-dashboard`, `build-data`)
- `Game/wet_run/CHANGELOG.md` — change history
- `Game/wet_run/wiki/index.md` — wiki navigation
