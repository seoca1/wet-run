# Design Specs — Canonical Location

> **✅ 2026-10-20**: `docs/design/` is the **single canonical** location for all game design specs.
> `docs/wiki/design/` was a stale mirror — **deleted** (67 duplicate files, 0 unique content).

## Why `docs/design/` is canonical

| Evidence | Source |
|---|---|
| Code references `docs/design/systems/combat.md` | `web/src/core/state_actions_combat.ts:29` |
| Design-conformance tests assert against `docs/design/` | `web/tests/design_conformance.test.ts` |
| User-facing docs link `docs/design/` | `README.md:58` |
| ADRs cite `docs/design/verification-framework.md` | `decisions/ADR-0065-cross-citation.md` |
| AGENTS.md §2 names `docs/design/` as "활성 스펙" | `AGENTS.md:14` |
| `docs/wiki/design/` had **0 unique files** | file tree diff |

## What was deleted

`docs/wiki/design/` (67 files) — identical content to `docs/design/`, diverging only in internal
`../../wiki/decisions/` vs `../../decisions/` path prefixes. All 67 pairs were content-identical
after path normalization except 2 files where `docs/design/` had *additional* retired-marker notes
(`systems/aftermath.md`, `systems/story-archive.md`) — `docs/design/` was strictly newer.

## Remaining structure

```
docs/
├── design/                     # ← CANONICAL design specs (73 files)
├── wiki/
│   ├── decisions/               # ← CANONICAL ADRs (130 files)
│   ├── lore/, world/            # LLM Wiki narrative layer
│   └── (design/ deleted)
├── architecture/                # redirect-only (README.md → wiki/decisions/)
├── dashboard/                   # derivative story HTML + stats
└── sessions/, playtest/
```

## Related

- ADR canonical: `docs/wiki/decisions/` (130 ADRs, redirect-only `docs/architecture/`)
- Game data: `web/src/data/*.json` + `web/public/sounds/` (root `data/` deleted 2026-10-20)
- Audit: `docs/STRUCTURE_AUDIT.md` §3.6