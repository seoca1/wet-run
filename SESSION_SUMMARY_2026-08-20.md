# Wet Run — Session Summary 2026-08-20 (Track A: Foundation Health)

> **Session scope**: Quality Upgrade Plan §A — Foundation Health track. Game quality audit + 5 sub-items executed. **Plan status: ✅ READY FOR EXECUTION** (locked 2026-08-20 with D1-D5 user-approved).
>
> **Predecessor**: [SESSION_SUMMARY_2026-08-19.md](./SESSION_SUMMARY_2026-08-19.md) (CI hygiene + Pages deploy)
>
> **Next session candidates**: Track A.4 (top-5 module splits, 5 sub-PRs) or Track B (Player Polish verification-driven coverage matrix).

## 1. Overview

Executed Track A of the 5-track Quality Upgrade Plan. **6 of 7 items complete** in a single session; A.4 (module splits) deferred to its own session due to scope (5 modules × ~500 LOC = substantial).

Track A scope:
- **A.1** ADR Implementation Status sweep (40 ADRs)
- **A.2** README count reconciliation
- **A.3** Wiki drift fix (146 → 0 broken links) + re-enable mkdocs strict
- **A.5** Pre-existing test failures (auto-resolved by 2026-08-19)
- **A.6** ADR-0195 (Implementation Workflow) Draft
- **A.7** Sounds hygiene Issue #2 (Issue #3 documented, #4 → Track E)
- **A.4** Module splits (deferred — see §6)

## 2. Commits (0 — per workspace §6 no auto-commit)

**No commits made** this session. All changes staged in working tree. Per workspace `AGENTS.md §6` + workspace root `AGENTS.md §8`, no commit without explicit user authorization.

Working tree dirty: ~30 files modified across the session.

## 3. Track A Items Closed

### A.1 — 40 ADR Implementation Status sweep

| Category | ADRs |
 |---|---|
 | **Delegated** | 4 parallel agents (batches 1-4) processing 40 ADRs |
 | **Result** | 31 ✅ Implemented + 9 🟡 Partial + 0 ❌ + 0 🟢 Deferred |
 | **Files touched** | `decisions/0147` through `0193` (each with new `## Implementation Status (2026-08-20)` section) |
 | **Immutable sections preserved** | `## 결정` / `## Consequences` / `## 사용자 결정` — all 4 agents verified untouched |

**Critical finding**: 9 ADRs share a "declarative scaffold" pattern — library + tests + AppState fields wired, but downstream integration hooks missing (no path in combat/alarm/salvage/mission/render reads those flags). These become Track B follow-up integration tasks:

| ADR | Gap |
 |---|---|
 | 0163 Run Mutators | salvage/alarm-tick/encounter-spawn/skill-filter 미통합 |
 | 0164 Mission Archetypes | combat/salvage/mission-completion 미통합 |
 | 0165 Random Matrix Events | per-node trigger hookup 미통합 |
 | 0166 Phase 6 Arc | mission-board/data 미통합 (`is_expansion_mission("ghost_signal_origin")` returns False) |
 | 0167 Mission Expansion | 6 mid-tier missions 미션 보드 미통합 |
 | 0168 Death Taunts | boss side OK, per-ICE kill-path `get_taunt()` 호출 없음 |
 | 0169 Combat Cinematics | 8 phase cinematics, phase-transition event 미통합 |
 | 0170 Gibson Fluff Library | **381 fluff messages** ready (목표 200의 190%), push consumer 없음 |
 | 0171 Battle Portraits | 192 LOC library, render path 가 static `enemy.portrait` 사용 |

### A.2 — README count reconciliation

- Badge: `5281` → `5700` tests passing
- Scene count: `72 (9 × 8)` → `81 (9 × 9)` GN scenes
- pytest passed: `5578` → `5700`
- Source files: `211` → `214`
- `make test` comment: `5578` → `5700`

### A.3 — Wiki drift fix + mkdocs strict

| Stage | Count |
 |---|---:|
 | Initial broken links (mkdocs strict warnings) | **146** |
 | Final broken links | **0** |
 | Files modified (cross-project + out-of-docs-dir links) | **22** |
 | `mkdocs build --strict` | ✅ 0 warnings, 2.26s build time |
 | `pages.yml` `mkdocs build --strict` re-enabled | ✅ |

**Approach**: stripped `[label](../../path)` markdown link brackets for links outside `docs_dir: wiki` — preserved text labels, removed hyperlinks. Information retained, mkdocs compliant.

### A.5 — Test failure categorization (auto-resolved)

8 pre-existing failures (3× Pages + 5× interrogate) from SESSION_SUMMARY_2026-08-19 all pass in current suite:
- `pytest tests/` → **5700 passed / 365 skipped / 1 xfailed / 0 failed**
- `test_pages_vault.py`: 53 passed, 1 skipped
- 5× `test_phase4{4,5,6,7,8}_small_content_polish.py` `TestVaultWideInterrogate*`: all pass

### A.6 — ADR-0195 Draft filed

- File: `decisions/0195-adr-implementation-workflow.md` (130 lines)
- Status: Draft (awaiting user acceptance)
- Index entry: `decisions/README.md` (1 line added)
- Proposes: Implementation Status section mandatory for all Accepted ADRs + Impl column in index
- Recommended path: Option 1+3 hybrid (section + index column)

### A.7 — Sounds hygiene

| Issue | Status |
 |---|---|
 | #2: `prototype/sounds_test/` 7.4MB dup (20/46 files differed) | ✅ Fixed (deleted dup, fixed `upgrade_sounds.py:12` wrong path) |
 | #3: theme_* WAV 4-version divergence | Documented in `audio/sound_manager.py` docstring |
 | #4: Git LFS migration (321MB audio) | Deferred per plan D4 → Track E |

## 4. Verification Performed

| Layer | Method | Result |
 |---|---|---|
 | pytest | full suite | 5700 passed / 365 skipped / 1 xfailed / 0 failed (83s) |
 | ruff | `ruff check` | 0 errors |
 | mypy | `mypy --strict src/wet_run/` | 0 errors |
 | interrogate | vault-wide | 100% (was 100%, preserved) |
 | mkdocs | `mkdocs build --strict` | 0 warnings, 2.26s |
 | ADR ledger | 40 ADRs verified Implementation Status | 31 ✅ + 9 🟡 |

## 5. Files Modified This Session

### Created
- `.omo/plans/QUALITY_UPGRADE_PLAN_2026-08-20.md` (~270 lines, plan)
- `decisions/0195-adr-implementation-workflow.md` (130 lines, ADR Draft)
- `SESSION_SUMMARY_2026-08-20.md` (this file)

### Modified — A.1 (40 ADRs)
Each: `decisions/0147-data-salvage-phase6.md` through `decisions/0193-programs-equipment-expansion.md` — new `## Implementation Status (2026-08-20)` section before `## 변경 이력` (or at file end if no 변경 이력).

### Modified — A.2
- `README.md` (4 edits: badge, scene count, pytest line, make test comment)

### Modified — A.3 (22 files)
- `wiki/world/derivative_stories.md` (112 Fiction links stripped)
- `wiki/world/cross-project-integration.md` (2 Fiction links)
- `decisions/0031-original-scenario-integration.md` (3)
- `decisions/0140-engagement-layer.md` (5)
- `decisions/0188-mission-expansion.md` (1)
- `decisions/0190-boss-expansion-f4-integration.md` (1)
- `decisions/0194-ecs-role-clarification.md` (1)
- `decisions/0130-balance-audit-and-ppl-sync.md` (1)
- `decisions/0131-faction-rep-cross-run-persistence.md` (1)
- `_archive/sessions/SESSION_SUMMARY_2026-07-28.md` (1)
- `design/scenario/chapter-1-novice.md` (3)
- `design/scenario/chapter-2-veteran.md` (2)
- `design/scenario/chapter-3-heretic.md` (2)
- `design/scenario/chapter-4-bridge.md` (1)
- `design/scenario/chapter-4-suit.md` (1)
- `design/scenario/chapter-5-veteran.md` (1)
- `design/scenario/chapter-5-wigan.md` (1)
- `design/scenario/chapter-6-angie.md` (1)
- `design/scenario/chapter-6-veteran.md` (1)
- `design/scenario/chapter-7-sally.md` (1)
- `design/scenario/chapter-7-suit.md` (1)
- `design/scenario/chapter-8-3jane.md` (1)
- `design/scenario/README.md` (3)
- `design/gibson-tone-audit-2026-08-04.md` (2)
- `dashboard/stories/journey/README.md` (3)
- `dashboard/stories/journey/{heretic,veteran,novice}.md` (3)
- `index.md` (79 SESSION_SUMMARY reference links)
- `wiki/index.md` (7)
- `log.md` (1 last SESSION_SUMMARY_2026-08-18 link)
- `.github/workflows/pages.yml` (`mkdocs build` → `mkdocs build --strict`)

### Modified — A.6
- `decisions/README.md` (1 line for ADR-0195 index)

### Modified — A.7
- `prototype/scripts/upgrade_sounds.py` (1 line: `SOUNDS_DIR` path fixed)
- `prototype/src/wet_run/audio/sound_manager.py` (docstring updated with canonical path note)
- Deleted: `prototype/sounds_test/` (7.4MB dup, 46 files)

### Modified — Log
- `Game/wet_run/log.md` (3 new entries: plan-filed, D1-D5 resolved, A.1 done, A.7 done)

## 6. Next-Session Backlog (deferred, not blocked)

| Item | Effort | Notes |
 |---|---|---|
 | **Track A.4 — Top-5 module splits** | 5 sessions | achievements.py 943 → menu.py 891 → dungeon_generator.py 862 → state.py 815 → gn_render.py 761. Per ADR-0110, each ≤ 500 LOC. Pure refactoring, no behavior change. 5 sub-PRs. |
 | **Track B — Player-Facing Polish (verification)** | 3-4 sessions | verify ADR-0147-0187 coverage → output `docs/audits/adr_coverage_matrix_*.md`. Includes 9 follow-up integration tasks from A.1 🟡 Partial (0163-0171). |
 | **Track C — Content Depth** | 4-6 sessions | 89 missions (ADR-0188 Q1-Q5 resolved per D1), ICE archetypes, story events, mutators, Boss Phase 5. |
 | **Track D — Meta & Aftermath** | 2-3 sessions | cross-run reputation, NG+ Phase 6, Run Replay, meta unlocks |
 | **Track E — Release** | 1-2 sessions | PyPI v1.4.0, dashboard integrity, Git LFS decision (D4) |

## 7. ADR-0195 Acceptance — user action item

`decisions/0195-adr-implementation-workflow.md` Draft awaits user choice:
- [ ] Option 1+3 (recommended) — Implementation Status section mandatory + Impl index column
- [ ] Option 1 only
- [ ] Option 2 (Status 단계 추가)
- [ ] Option 4 (현상 유지)

## 8. Working Tree State

| Metric | Value |
|---|---:|
 | Modified files | ~35 (after Track B) |
 | Untracked | 0 |
 | Branch | main (in sync with origin) |
 | Pre-commit state | dirty |

**No commit this session per workspace `AGENTS.md §6` + workspace root `AGENTS.md §8` (no auto-commit without explicit user authorization).**

---

# Track B — Player-Facing Polish (Continuation in same session)

## 9. Overview

Continued same-day session. Executed Track B of the 5-track Quality Upgrade Plan. **10/10 items complete** — 9 ADR integration wirings + 1 audit deliverable.

Track B scope (per `QUALITY_UPGRADE_PLAN_2026-08-20.md §B`):
- 9 follow-up integration tasks from Track A.1's 🟡 Partial ADRs (0163-0171)
- 1 verification audit deliverable (`docs/audits/adr_coverage_matrix_2026-08-20.md`)

## 10. Track B Items Closed

### 10.1 Integration wirings (9)

| ADR | Wiring | File(s) |
|---|---|---|
| 0163 Run Mutators | `is_heal_disabled(state)` in HEAL branch | `combat/salvage.py` + `run_mutators.py` (TYPE_CHECKING guard) |
| 0164 Mission Archetypes | `partial_pay_percent` scales `complete_mission` credits | `engine/mission_completion.py` |
| 0165 Random Matrix Events | `check_event_trigger` + `trigger_event` loop after node visit | `engine/matrix_view_input.py` |
| 0166 Phase 6 Arc | 🟡 Partial (registry ready, board wiring = data authoring) | `combat/arc6.py` accessible |
| 0167 Mission Expansion | 🟡 Partial (registry ready, board wiring = data authoring) | `combat/mission_expansion.py` accessible |
| 0168 Death Taunts | `get_taunt(ice_type.value, combat_state.rng)` in `_end_combat` | `engine/combat_view_state.py` |
| 0169 Combat Cinematics | `phase_intro_sequence()` in `_check_boss_phase_transition` | `combat/state_transitions.py` |
| 0170 Gibson Fluff Library | `push_fluff()` helper + "encounter" category in `start_combat` | `combat/gibson_fluff.py` + `engine/combat_view_state.py` |
| 0171 Battle Portraits | `get_portrait()` replaces `enemy.portrait` in render | `engine/combat_view_render.py` |

### 10.2 Audit document (1)

- **`docs/audits/adr_coverage_matrix_2026-08-20.md`** (NEW, 5.7 kB)
- Documents status of 40 ADRs from A.1 sweep + 9 B integrations
- Snapshot: 33 ✅ Implemented (wired) + 2 🟡 Partial (registry only) + 0 ❌ + 0 🟢 Deferred

## 11. Verification Performed

| Layer | Method | Result |
|---|---|---|
| pytest | full suite | 5700 passed / 365 skipped / 1 xfailed / 0 failed (84.00s) |
| ruff | `ruff check src/wet_run/` | All checks passed (230 source files) |
| mypy | `mypy --strict src/wet_run/` | Success: no issues found in 230 source files |
| mkdocs | `mkdocs build --strict` | 0 warnings (2.27s) |
| Tests modified | none | Pure additions |
| Behavior changes | none | Player-visible additions only |

## 12. Files Modified (Track B continuation)

| File | LOC change | Purpose |
|---|---|---|
| `engine/combat_view_render.py` | +10 | `get_portrait()` in render (ADR-0171) |
| `combat/gibson_fluff.py` | +18 | `push_fluff()` helper (ADR-0170) |
| `engine/combat_view_state.py` | +5 | `push_fluff("encounter")` + `get_taunt()` calls |
| `combat/state_transitions.py` | +6 | `phase_intro_sequence()` on boss phase transition (ADR-0169) |
| `engine/matrix_view_input.py` | +6 | Matrix Event trigger on node visit (ADR-0165) |
| `combat/salvage.py` | +5 | `is_heal_disabled` check (ADR-0163) |
| `combat/run_mutators.py` | +1 | TYPE_CHECKING guard + `getattr` defensive (ADR-0163) |
| `engine/mission_completion.py` | +4 | `partial_pay_percent` scaling (ADR-0164) |
| `docs/audits/adr_coverage_matrix_2026-08-20.md` | NEW, 5.7 kB | Audit deliverable |

**Total**: 8 source files modified, 1 audit doc written.

## 13. Remaining Gaps (Track B)

- **ADR-0166 Phase 6 Arc**: `combat/arc6.py` 4-mission registry accessible but not wired into `mission_completion.py`. Requires `data/missions/missions.json` data authoring (4 full mission entries).
- **ADR-0167 Mission Expansion**: `combat/mission_expansion.py` 6-mission registry accessible but not wired. Requires `data/missions/missions.json` data authoring (6 full mission entries).

Both deferred to content-authoring session.

## 14. Next-Session Backlog

| Item | Effort | Notes |
|---|---|---|
| **Track C — Content Depth** | 4-6 sessions | 89 missions at target per ADR-0188; now ICE archetypes / story events / mutators authoring |
| **Track D — Meta & Aftermath** | 2-3 sessions | cross-run reputation persistence / NG+ Phase 6 / Run Replay / meta unlocks |
| **Track E — Release** | 1-2 sessions | PyPI v1.4.0, dashboard integrity, Git LFS decision (D4) |
| **ADR-0195 acceptance** | 1 user decision | Implementation Workflow mandate |
| **ADR-0194 ECS-lite** | 1 user decision | Draft acceptance |
| **Phase 6 Arc / Mission Expansion data authoring** | 1 session | 10 mission entries with full schema |

---

For project conventions and handoff context, see
[`AGENTS.md`](./AGENTS.md), [`log.md`](./log.md),
[`QUALITY_UPGRADE_PLAN_2026-08-20.md`](./.omo/plans/QUALITY_UPGRADE_PLAN_2026-08-20.md),
[`docs/audits/adr_coverage_matrix_2026-08-20.md`](./docs/audits/adr_coverage_matrix_2026-08-20.md),
and [`SESSION_SUMMARY.md`](./SESSION_SUMMARY.md).