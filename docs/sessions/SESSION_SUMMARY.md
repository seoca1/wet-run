# Wet Run — Session Index

> **Latest session**: 2026-08-31 (Gibson verification pipeline expansion — 23 checks, 14 dimensions, 953 stories, dashboard rebuilt) — see `log.md` 2026-08-31 enhancement(dashboard) entry
>
> Previous: 2026-08-26 Part 2 (Tier 4 + ADR-0208 + IDB Save Backend) — [SESSION_REPORT_2026-08-26.md](./SESSION_REPORT_2026-08-26.md) §"Post-Report Addendum"
>
> Earlier: [SESSION_SUMMARY_2026-08-20.md](./SESSION_SUMMARY_2026-08-20.md) (Tracks A+B+C+D+E Full Quality Upgrade)
>
> [SESSION_SUMMARY_2026-08-19_notion.md](./SESSION_SUMMARY_2026-08-19_notion.md) (Notion 통합 Part 2)

This is an **index** file pointing to the most recent dated session snapshot. Per project `AGENTS.md §9`, `SESSION_SUMMARY.md` should always point at the current/latest session.

> **2026-08-26 Part 2 (Tier 4 + ADR-0208 + IDB Save Backend).** Continued same-day work after v1.4.0 Operational Release report. Added 3 new ADR (0207 Tier 4, 0208 random_weight, 0209 IDB) + 8 atomic commits (`feac61b`, `81cffb5`, `4afe25f`, `33ba853`, `5af817b`, `91402f7`, `6c6e352`, `0a420e7`). Bundle 126.10 → **129.63 KB** (+3.53 KB for Tier 4 + IDB). Python + wet_run-web tests stable (4045 pass / 93 pass). Dry-run 단계에서 `storage.ts` TS1128 (orphan dead code) 발견 → 즉시 fix commit으로 해결. Tier 3 literal "cloud save sync"의 on-ramp 완성 (로컬 IDB ✅, 원격 sync ❌ out-of-MVP).

## Recent sessions

| Date | File | Summary |
|---|---|---|
| **2026-08-31 (Pipeline Expansion + Dashboard Rebuild)** | `log.md` (2026-08-31 entries) | **LATEST.** Dashboard rebuilt: 953 stories with 23-check `gibson_style` + 14-dimension `literary`. 5 tools patched for peripheral. S-grade threshold bug fixed. |
| 2026-08-26 Part 2 (Tier 4 + ADR-0208 + IDB Save Backend) | [SESSION_REPORT_2026-08-26.md](./SESSION_REPORT_2026-08-26.md) (Post-Report Addendum) | 3 new ADR + 8 commits. Bundle +3.53 KB. Tier 3 literal "cloud save sync" partial fulfillment (local IDB only). |
| 2026-08-26 Part 1 (v1.4.0 Operational Release) | [SESSION_REPORT_2026-08-26.md](./SESSION_REPORT_2026-08-26.md) | v1.4.0 PyPI + GitHub release + ADR-0194/0195/0200/0201-0206. 30 atomic commits. Previous session — full report in dedicated file. |
| 2026-08-20 (Tracks A+B+C+D+E: Full Quality Upgrade) | [SESSION_SUMMARY_2026-08-20.md](./SESSION_SUMMARY_2026-08-20.md) | All 5 tracks: A.4 module splits (5 parallel agents), B.9 ADR integrations wired, C content verified at target (200/97/30/29/81), D.5 meta & aftermath verified, E.4 release prep. Operational releases (PyPI/GitHub/LFS) deferred to user. |
| 2026-08-19 (Notion 통합 Part 2) | [SESSION_SUMMARY_2026-08-19_notion.md](./SESSION_SUMMARY_2026-08-19_notion.md) | Previous: 66 design doc pages in Notion (3-tier), 5 body updates, ~150 API calls. |
| 2026-08-19 (CI hygiene + Pages deploy) | [SESSION_SUMMARY_2026-08-19.md](./SESSION_SUMMARY_2026-08-19.md) | Previous: 5 root causes fixed (Pages deploy 46d stale, interrogate, ruff lint/format, dashboard validation). 5700 passed baseline restored. |
| **2026-08-18 (Axis closure sweep)** | [SESSION_SUMMARY_2026-08-18.md](./SESSION_SUMMARY_2026-08-18.md) | Previous: Axis 5 (Endings) + Axis 4 (Boss F.4) + Axis 6 (Programs/Equipment) closure. 8 commits. `combat/boss_dispatch.py` NEW + `combat/boss_registry.py` NEW + `build_ice_enemy` guard. +43 tests, 0 regressions. |
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
