# Wet Run — Structure Audit (2026-10-20)

## 1. Overview

| Metric | Value |
|---|---|
| Total files (tracked) | 1,963 |
| Active codebase | `web/` (TS + Vite + Vitest) |
| src/ files | 103 (.ts) |
| test files | 122 (2,902 tests passing) |
| e2e specs | 15 (Playwright) |
| ADRs | 130 (`docs/wiki/decisions/`) |
| Derivative story cards | 970 (`docs/dashboard/stories/short-stories/`) |
| Design specs | 73 (`docs/design/` — single canonical) |
| Build | 699 ms, tsc strict clean, eslint 0 errors |
| Git tree | Clean (0 modified, 0 untracked) |
| Vault lint | ✅ CLEAN (0 broken / 0 orphan) |

## 2. Directory Layout

```
Game/wet_run/
├── web/                        # ACTIVE codebase
│   ├── src/                    # 103 .ts files, 1.1 MB
│   │   ├── core/ (62)          # combat_engine, state, dungeon, boss*, ice_ai...
│   │   ├── renderer/ (30)      # Canvas2D ASCII renderer
│   │   ├── audio/              # Howler.js BGM/SFX
│   │   ├── input/              # keyboard, gamepad, touch
│   │   ├── save/               # compress, storage, IDB, quota
│   │   └── data/               # JSON: effects, ice_types, missions, programs, scenes
│   ├── tests/                  # 122 test files
│   ├── e2e/                    # 15 Playwright specs
│   └── dist/                   # 79 MB build output (gitignored; 78 MB sounds/)
├── docs/
│   ├── wiki/
│   │   ├── decisions/ (130)   # ADR 0001-0213 — SINGLE CANONICAL
│   │   ├── lore/, world/       # LLM Wiki narrative layer
│   │   └── (design/ deleted 2026-10-20 — was 67-file mirror)
│   ├── dashboard/stories/      # 970 short-story HTML cards (EN/KO pairs)
│   ├── design/                 # GDD, scenario, systems specs — SINGLE CANONICAL
│   ├── architecture/           # redirect-only (README.md only, no ADR files)
│   ├── sessions/               # session summaries
│   └── playtest/               # playtest guides
├── data/                       # DELETED 2026-10-20 (was 48 files, legacy)
├── scripts/tools/              # audit_sprawl.py, find_broken_links.py
└── root meta: README, AGENTS, ROADMAP, CHANGELOG, MIGRATION, VALIDATION_SCENARIO, mkdocs.yml
```

## 3. Issues Found

### 3.1 Docs duplication (HIGH) — ✅ RESOLVED 2026-10-20
`docs/design/`, `docs/wiki/design/`, `docs/wiki/decisions/`, and `docs/architecture/` overlapped heavily. **Fixed**: all 130 ADRs moved to `docs/wiki/decisions/` as single canonical location. `docs/architecture/` is now redirect-only (README.md only, no ADR files). `docs/design/` and `docs/wiki/design/` still duplicated — see open issue 3.6.

### 3.2 Root `data/` is dead weight (MEDIUM) — ✅ RESOLVED 2026-10-20
48 files, almost all `sounds_test/` WAVs. Nothing referenced by code. **Deleted entirely** (2026-10-20). Docs referencing `data/jockeys/deceased.json` and `data/sounds_test/` updated with retired markers.

### 3.3 `web/src/core/` flatness (MEDIUM)
62 files in one directory. Per ADR-0110 the target is 100-300 LOC per module, so granularity is good, but the flat structure is crowded and the combat split (ADR-0156-0159) has already proven subdirectories work.

### 3.4 `dist/` size (LOW) — ✅ RESOLVED 2026-10-20
79 MB build output (78 MB sounds). **Guarded**: `.git/hooks/pre-commit` blocks staging of
`dist/`, `build/`, `site/`, `*.map` with exit 1. Same guard added to `.github/workflows/ci.yml`
web job (post-build step). Verified: forced-staging `dist/test.js` → hook exit 1.

### 3.5 ADR canonical path ambiguous (MEDIUM) — ✅ RESOLVED 2026-10-20
`docs/wiki/decisions/` (130 ADRs) is now the single canonical location. `docs/architecture/` is redirect-only. AGENTS.md §2 still references `docs/architecture/` as canonical — see open issue 3.7.

### 3.6 `docs/design/` ↔ `docs/wiki/design/` duplication (MEDIUM) — ✅ RESOLVED 2026-10-20
`docs/wiki/design/` (67 files) was a stale mirror of `docs/design/` — **0 unique files**.
Evidence for `docs/design/` as canonical: code (`web/src/core/state_actions_combat.ts:29`,
`web/tests/design_conformance.test.ts`), `README.md`, `decisions/ADR-0065`, and AGENTS.md §2
all reference `docs/design/`. **Deleted `docs/wiki/design/` entirely.** 2 wikilinks in
`docs/wiki/world/boss-ice-reference.md` were fixed (`../design/` → `../../design/`).

### 3.7 AGENTS.md §2 stale reference (LOW) — ✅ RESOLVED 2026-10-20
§2 now points ADR canonical at `docs/wiki/decisions/` (130 ADRs), with `docs/architecture/`
noted as redirect-only. §5 (LLM Wiki Operations) updated: `docs/wiki/design/` removed from
the wiki tree (design specs live in `docs/design/`).

### 3.8 `docs/wiki/world/` wikilinks (LOW) — ✅ RESOLVED 2026-10-20
`boss-ice-reference.md` had 2 wikilinks (`[[../design/systems/combat]]`,
`[[../design/systems/animations]]`) that resolved against the now-deleted `docs/wiki/design/`.
Fixed to `[[../../design/systems/combat]]` / `[[../../design/systems/animations]]`.

## 4. Recommendations

| # | Action | Effort | Impact | Status |
|---|---|---|---|---|
| 1 | Decide ADR canonical: keep all game ADRs in `docs/wiki/decisions/`, deprecate `docs/architecture/`. | Low | High | ✅ Done |
| 2 | Consolidate `docs/design/` + `docs/wiki/design/`: pick one, move the other. | Medium | High | ✅ Done |
| 3 | Archive or delete root `data/`. | Low | Medium | ✅ Done |
| 4 | Subdivide `web/src/core/` by domain (combat/, dungeon/, state/, renderer/). | Medium | Medium | ⏳ Open |
| 5 | Add `dist/` to pre-commit hook / CI check to fail if build artifacts staged. | Low | Low | ⏳ Open |
| 6 | Add auto-generated `STRUCTURE.md` / `tree.md` to docs/. | Low | Low | ✅ Done (this doc) |
| 7 | Update AGENTS.md §2 to point ADR canonical at `docs/wiki/decisions/`. | Low | Low | ✅ Done |
| 8 | Fix wikilinks in `docs/wiki/world/` after `docs/wiki/design/` deletion. | Low | Low | ✅ Done |

## 5. Verdict

The codebase is **healthy and well-tested**. Issues 1, 2, 3, 4, 5, 6, 7, 8 are closed.
Remaining open item (3.5 `core/` subdivision) is a structural improvement, not debt —
the flat `web/src/core/` is functional (62 files, ADR-0110-compliant 100-300 LOC/module).