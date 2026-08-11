# Roguelike Sprawl — Session Index

> **Latest session**: 2026-08-10 (Phase 14 v1.3.0+ integration) — see [SESSION_SUMMARY_2026-08-10.md](./SESSION_SUMMARY_2026-08-10.md)

This is an **index** file pointing to the most recent dated session snapshot. Per project `AGENTS.md §9`, `SESSION_SUMMARY.md` should always point at the current/latest session.

> **2026-08-10 Phase 14 integration.** F.2 (deck_size) + F.4 (boss phase tracker + telemetry singleton) deep wiring complete. 10 commits across 3 repos (8 roguelike_sprawl + 1 typing_language + 1 Fiction). Lint clean (116 → 0 ruff errors), types clean (51 → 0 mypy errors), tests 4843 pass + 1 xfail. dashboard data-driven from `game_facts.json` (27 chars). All mechanical work closed; 89+99 missing items remain as creative-content debt. Push remains user-action territory.

## Recent sessions

| Date | File | Summary |
|---|---|---|
| **2026-08-10 (Phase 14 integration)** | [SESSION_SUMMARY_2026-08-10.md](./SESSION_SUMMARY_2026-08-10.md) | **LATEST.** F.2/F.4 deep wiring (telemetry singleton + deck_size + boss phase tracker) + mypy 51→0 + ruff 116→0 + 178 metadata fields backfilled + 200+ dashboard story HTML cards regenerated + build_dashboard character counter data-driven (4→27 chars) + .gitignore `.omo/`. typing_language romaji-mapping file bug fixed (amend 537e423). |
| **2026-08-08 (v1.3.0+ release)** | [SESSION_SUMMARY_2026-08-08.md](./SESSION_SUMMARY_2026-08-08.md) | Previous release: 15 tracks across E/F/G sub-tracks, 16 ADRs (0172–0186), +260 tests (4253→4513), 2 tracks cancelled (B.5, D.4 audio), 1 blocked (A.6 push). |
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
| Roguelike_sprawl | `Game/roguelike_sprawl/wiki/log.md` (project-wiki-level) |

Per project convention, today's per-project diagnostic passes were appended to each project's log.md during the session.
