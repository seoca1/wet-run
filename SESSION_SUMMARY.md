# Wet Run — Session Index

> **Latest session**: 2026-08-19 (CI hygiene + Pages deploy recovery) — see [SESSION_SUMMARY_2026-08-19.md](./SESSION_SUMMARY_2026-08-19.md)

This is an **index** file pointing to the most recent dated session snapshot. Per project `AGENTS.md §9`, `SESSION_SUMMARY.md` should always point at the current/latest session.

> **2026-08-19 CI hygiene + Pages deploy recovery.** Discovered live dashboard was 46 days stale (frozen on 2026-07-04 deploy with pre-rename ROGUELIKE SPRAWL branding). Root cause: `mkdocs build --strict` failing on 146 broken wikilinks in `wiki/world/derivative_stories.md`. Fixed 5 separate CI issues: pages deploy unblock, interrogate coverage 99.7%→100% (added 7 docstrings), 10 ruff errors + 14 format issues, ruff version pin, 2 deleted test files in dashboard validation. **5 commits pushed**, all CI jobs expected to pass on next run. **5700 passed** (was 5695, +5 phase tests). Branch ahead of origin = 0, working tree clean.

## Recent sessions

| Date | File | Summary |
|---|---|---|
| **2026-08-18 (Axis closure sweep)** | [SESSION_SUMMARY_2026-08-18.md](./SESSION_SUMMARY_2026-08-18.md) | **LATEST.** Axis 5 (Endings) + Axis 4 (Boss F.4) + Axis 6 (Programs/Equipment) closure. 8 commits. `combat/boss_dispatch.py` NEW + `combat/boss_registry.py` NEW + `build_ice_enemy` guard. +43 tests, 0 regressions. |
| 2026-08-13 (mypy strict upgrade) | [SESSION_SUMMARY_2026-08-13.md](./SESSION_SUMMARY_2026-08-13.md) | Previous: Track A no-op (false premises), Track B mostly no-op (already modern), B5: mypy strict mode + @override. 1 real bug fixed in `engine/menu.py`. |
| 2026-08-10 (Phase 14 integration) | [SESSION_SUMMARY_2026-08-10.md](./SESSION_SUMMARY_2026-08-10.md) | Previous: F.2/F.4 deep wiring + mypy 51→0 + ruff 116→0 + 178 metadata fields + 200+ dashboard cards. |
| 2026-08-08 (v1.3.0+ release) | [SESSION_SUMMARY_2026-08-08.md](./SESSION_SUMMARY_2026-08-08.md) | Previous release: 15 tracks across E/F/G sub-tracks, 16 ADRs (0172–0186), +260 tests (4253→4513), 2 tracks cancelled (B.5, D.4 audio), 1 blocked (A.6 push). |
| 2026-08-06 (dirty-tree closure) | [SESSION_SUMMARY_2026-08-06.md](./SESSION_SUMMARY_2026-08-06.md) | 8 atomic commits landed: deps + dashboard regen + 7 obsolete test deletions + docs refresh + design+scripts READMEs + 10 new test files + audit archive + code changes. |
| 2026-08-05 (session close) | [_archive/audits/session-close-2026-08-05.md](./_archive/audits/session-close-2026-08-05.md) | 16-iteration audit + cleanup complete. Definitive close document. |
| 2026-08-05 (cycle audit) | [SESSION_SUMMARY_2026-08-05_cycle-audit.md](./SESSION_SUMMARY_2026-08-05_cycle-audit.md) | Quality audit: 11 cycles of cleanup, 5 real bugs fixed, 14 Draft ADRs → Accepted, coverage 68.8% → 73.36% |
| 2026-08-05 (workspace reorg) | [SESSION_SUMMARY_2026-08-05.md](./SESSION_SUMMARY_2026-08-05.md) | Workspace file reorganization — session summaries archived + Python tools/scripts consolidated |
| 2026-08-03 | [SESSION_SUMMARY_2026-08-03.md](./SESSION_SUMMARY_2026-08-03.md) | Diagnostics + Fiction lift streak: 8 C → B novels + 1 synthesis page + dashboard refresh |
| 2026-07-28 | [_archive/sessions/SESSION_SUMMARY_2026-07-28_v1.1.0a1.md](./_archive/sessions/SESSION_SUMMARY_2026-07-28_v1.1.0a1.md) | v1.1.0a1 release |
| 2026-07-28 | [_archive/sessions/SESSION_SUMMARY_2026-07-28.md](./_archive/sessions/SESSION_SUMMARY_2026-07-28.md) | v1.0.0 FINAL |
| 2026-07-27 | [_archive/sessions/SESSION_SUMMARY_2026-07-27.md](./_archive/sessions/SESSION_SUMMARY_2026-07-27.md) | Phase 1 game balance audit + ADR-0130 draft |
| 2026-07-13 | (this file's original content — preserved in [SESSION_SUMMARY_2026-08-03.md](./SESSION_SUMMARY_2026-08-03.md) history) | v0.8.0 |

> Note: 2026-07-13 v0.8.0 content (originally here) has been superseded. The historical record was migrated to dated snapshots; the canonical 2026-07-13 content is reachable via `git log` on this file if needed.

## Per-project session logs

| Project | Log file |
|---|---|
| Fiction wiki | `Fiction/wiki/log.md` |
| Language wiki | `Language/log.md` |
| Roguelike_sprawl | `Game/wet_run/wiki/log.md` (project-wiki-level) |

Per project convention, today's per-project diagnostic passes were appended to each project's log.md during the session.
