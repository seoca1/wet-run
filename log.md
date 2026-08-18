## [2026-08-18] chore(rename-cleanup) | Dashboard + prototype — ROGUELIKE SPRAWL → Wet Run (5 atomic commits)

**Status**: ✅ 완료 — Project Rename scope A (commit `ae83d00`) 가 `wiki/` `design/` 까지만 적용됐고 dashboard + prototype 일부 (chrome / story metadata / i18n / demos) 가 누락됐던 잔존 영역 정리. **232 파일**, **5 atomic commits**. 0 test change, 0 regression. GitHub Pages push 전에 정합성 확보.

### Sweep 결과

사용자 결정 (sweep 범위 + 보존 영역): **전면 (dashboard + prototype)**, **이름=Wet Run**, **메타 문서 보존 (log/CHANGELOG/README/SESSION_*/_archive)**, **decisions/0032 Accepted immutable 보존**.

| 영역 | 정정 전 | 정정 후 |
|---|---|---|
| dashboard chrome `<h1>` (index, missions) | `🌆 ROGUELIKE SPRAWL` | `🌆 Wet Run` |
| dashboard chrome UI labels (back-nav `◀ Roguelike`, current `🌆 Roguelike`) | 5 sites (combat/cyberspace/sound/settings/missions/index) | 0 |
| dashboard story game-integration path (`Game/roguelike_sprawl/...`) | 213 .html | `Game/wet_run/...` (perl -pi sweep) |
| prototype i18n `app.title` (en/ko/ja/zh.json) | `ROGUELIKE SPRAWL` | `Wet Run` |
| prototype demo banners (6 demos) | `ROGUELIKE SPRAWL` banner | `Wet Run` banner |
| prototype/scripts/git-hooks/pre-commit (docstring) | `validate roguelike_sprawl ↔ Fiction` | `validate wet_run ↔ Fiction` |

### 보존 (사용자 결정)

- `decisions/0032-graphic-novel-mode.md` (1 line) — Accepted immutable 규약
- `log.md` (9 hits), `CHANGELOG.md` (4), `README.md` (5), `SETUP_LOG.md` (1)
- `SESSION_SUMMARY*.md`, `SESSION_HANDOVER*.md`, `_archive/sessions/*`, `_archive/audits/*`
- `prototype/CHANGELOG.md` (1 hit), meta `<meta name="keywords">` 의 `roguelike, cyberpunk, gibson, sprawl` (장르/설정 SEO)
- 인게임 subtitle (`'A roguelike based on William Gibson's Sprawl trilogy'` 등): `'roguelike'`=장르, `'Sprawl'`=깁슨 3부작 — 사실 관계 명제, 변경 X

### Commits (5 atomic, chronological)

| # | Hash | Files | Type |
|---:|---|---:|---|
| 1 | `2e6d161` | 2 | `fix(dashboard): chrome <h1> titles — ROGUELIKE SPRAWL → Wet Run` |
| 2 | `3f00b6a` | 6 | `fix(dashboard): chrome UI labels — Roguelike → Wet Run` |
| 3 | `28ea7bf` | 213 | `fix(dashboard): story game-integration paths — roguelike_sprawl → wet_run` |
| 4 | `b755ad1` | 4 | `fix(prototype): i18n app.title — ROGUELIKE SPRAWL → Wet Run (4 langs)` |
| 5 | `0d4f8c3` | 7 | `fix(prototype): demo banners + pre-commit hook — ROGUELIKE SPRAWL → Wet Run` |

### 검증

- `grep -rln 'roguelike[\s_\-]?sprawl|ROGUELIKE SPRAWL' dashboard/ prototype/data/i18n/ prototype/scripts/{demo,visual,full,headless,combat_effects}_*.py prototype/scripts/git-hooks/pre-commit` → **0 hits**
- `python3 -c "import json; json.load(open(file))"` × 4 i18n 파일 → **all OK**
- `python3 -c "import ast; ast.parse(open(file))"` × 6 demo .py → **all OK**
- 파일 인코딩 보존 (UTF-8 HTML), file count unchanged
- 보존 영역 (decisions/0032, log.md, CHANGELOG.md, README.md, SETUP_LOG.md, _archive/, SESSION_SUMMARY*.md, prototype/CHANGELOG.md) — 그대로 유지 확인

### 인용

- ADR style: AGENTS.md §9 (작업 종료 체크리스트 — log.md 기록)
- Rename history: commit `ae83d00 chore(rename): Roguelike Sprawl → Wet Run (project-wide display name)`
- 사용자 의사결정: "A. 전면 / Wet Run (대문자 그대로) / 기록 보존 / 0032 보존"

---

## [2026-08-17] feat+chore(polish) | Phase 50 — Small content + polish

**Status**: ✅ 완료 — 1 content addition (Screw's Last Bargain event) + 1 modules polished (mission_completion docstring) + 10 forward-compat allowlist updates (Phase 40..49). Commit `80e5d3b`. 13 files, +218/-14, **5604 passed** (+13 over Phase 49 baseline 5591), 365 skipped, 1 xfailed.

### 1. Content addition: general_event_screws_last_bargain

`prototype/data/story/events.json` 에 `general_event_screws_last_bargain` 신규 엔트리 추가 (53 → 54 events). Gibson-flavored Arc 5 late-arc Screw's Last Bargain from the Freeside black-market fixer — 깁슨 원작의 *Mona Lisa Overdrive* / *Count Zero* 의 Freeside orbit 여권조작꾼 Screw 가 주인공에게 마지막 거래 제안 (Freeside passport in exchange for a 'contested memory'). 위태/시바 / Zion 모두와 다른 Freeside 의 마지막 톤 (shaky):

- **Category**: general, trigger: `node_enter`, trigger_condition: `arc_5_progress >= 70 AND random < 0.04 AND NOT has_status:screw_bargain_seen`
- **Mood**: shaky, location: matrix_freeside_orbit, arc: 5, tier: 5, pillar: memory
- **Dialogue**: SCREW VOICE 메시지 5개 ("Hey, kid. Last time I cut a deal like this, the buyer ended up in a vat." / "Freeside passport, L5 orbit clearance, no questions. Cost: a memory." / "Not the boring ones. The ones you still flinch at. That's the going rate.") + CONSOLE blackmarket log
- **Choice**: Pay the memory price (screw_pass_unlocked, freeside_clearance_+2, zion_affinity_-1, contested_memory_relinquished_2_runs) vs Walk — your memories are not for sale (freeside_walked, safe_jackout, identity_marker_high, maas_+1)
- **Reward**: 0 credits + 120 XP + screw_freeside_charm
- **Consequence**: screws_last_bargain_branch (unique — global branch-id sweep)
- **Faction affinity**: freeside_clearance +2 AND maas +1 (pay-bargain yields Freeside orbit passage + Maas protective approval of the refused bargain; walk-on yields the inverse — no orbit passage but Maas oath of contested memory protection)
- **메타데이터**: phase 50 → 51, total_events 53 → 54, total_chains 6 unchanged

Phase 49 의 Zion Last Broadcast event (Arc 5 late-arc, Maelcum wisdom transmission, zion_affinity + ta_rep affinity) 와 동일 arc-prefix + tone-pair — Phase 49 가 "Zion dread 의 reggae broadcast" (warm) 였다면, Phase 50 은 "Freeside black-market 의 passport bargain" (shaky). 둘 다 Arc 5 late-arc construct-passage pre-auth, 둘 다 last-message 모티프. Phase 49-50 가 "마지막 거래/전송" 의 짝.

### 2. Polish — 1 modules (mission_completion docstring)

**`engine/mission_completion.py`** — `complete_mission()` docstring 확장. 기존 2줄 docstring 을 완전한 API contract 로 확장:

- 기존: "Award rewards and mark mission as complete." (2줄)
- 신규: explicit `Args:` (state / mission) + `Side effects:` 섹션 (Credits / XP / Faction / completed_missions / items — 5 항목 명시) + silent no-op on non-Mission callers note
- 기존 silent no-op 동작 (return without effect for non-Mission callers) 유지 — contract 자명화

### 3. Forward-compat allowlist (10 forward-compat updates + bug fix)

Phase 40..49 테스트의 `metadata["phase"] in (...)` allowlist 에 "50" 추가 (9 forward-compat updates + Phase 49 자체 forward-compat):

- **Bug fix (incidental)**: `test_phase49_small_content_polish.py` 의 metadata fixture 가 `dict.get('phase', '49', '50')` 로 잘못 작성되어 있었음 — Python `dict.get()` 는 max 2 args. `dict.get('phase', '49')` 로 수정 (default 만).

### 4. test_phase50_small_content_polish.py (13 tests 신규)

- **`TestScrewsLastBargainEvent`**: 11 tests
  - test_event_present
  - test_event_metadata (arc/tier/pillar/location/mood)
  - test_event_trigger (arc_5_progress >= 70, NOT has_status:screw_bargain_seen)
  - test_event_dialogue (SCREW, Freeside reference)
  - test_event_choice_a_screw (screw_pass_unlocked, freeside_clearance_+2, zion_affinity_-1, contested_memory_relinquished_2_runs)
  - test_event_choice_b_maas (maas_+1, maas_oath_2_runs, identity_marker_high)
  - test_event_faction_affinity (freeside_clearance == 2, maas == 1)
  - test_event_rewards (screw_freeside_charm, xp 120)
  - test_event_arc_5_partner (screws_last_bargain_branch)
  - test_event_branch_is_unique
- **`TestScrewsLastBargainBranchUniqueness`**: 1 test
  - test_branch_id_unique_across_events (global branch-id sweep — 다른 events 와 branch id 충돌 없음 검증)
- **`test_phase_50_metadata_present`** + **`test_phase_50_total_events_at_least_53`**: 2 tests
  - Phase 50 metadata 가 존재하고 total_events >= 53 (screw 추가 후 54)

### Validation

| Gate | Status | Notes |
|---|---|---|
| `make format` | ✅ | 변경 없음 |
| `make lint` (ruff) | ✅ | All checks passed |
| `make typecheck` (mypy strict) | ✅ | Success: no issues found in 211 source files |
| `make test` (pytest) | ✅ | **5604 passed** (+13 over Phase 49 baseline 5591), 365 skipped, 1 xfailed (pre-existing perf-tracker flake) |
| interrogate | ✅ | 100.0% (Phase 49 plateau preserved) |
| `audit_vault.py` | ✅ | 0 broken (CLEAN, 67 false-positive artifacts) |
| `dashboard_pipeline_audit.py` | ✅ | 0 errors |
| `mixed_language_audit.py` | ✅ | 0 violations |

### 5. Out-of-scope (preserved)

- `raw/` 수정 안 됨
- Accepted ADR 수정 안 됨
- 다른 프로젝트 손대지 않음
- Push 안 함

### 6. Forward-compat (테스트 패턴 일관성)

Phase 40..49 테스트의 `metadata["phase"] in (...)` allowlist 에 "50" 추가 (10 forward-compat updates, 9 single-line + 1 bug fix in Phase 49). 메타데이터 phase bump 가 이전 phase 테스트를 깨뜨리지 않도록.

### 7. Cumulative Phase 47..50

- Phase 47 (Hosaka Archive Audit): Gibson Sense/Net archive dialogue, Arc 4 mid-arc
- Phase 48 (Dixie Flatline Memory): Gibson dead-ROM construct, Arc 4 mid-arc
- Phase 49 (Zion Last Broadcast): Gibson Maelcum reggae dread, Arc 5 late-arc warm
- Phase 50 (Screw's Last Bargain): Gibson Freeside black-market, Arc 5 late-arc shaky

---

## [2026-08-17] feat+chore(polish) | Phase 49 — Small content + polish

**Status**: ✅ 완료 — 1 content addition (Zion Last Broadcast event) + 1 modules polished (wetware_stacking docstring) + 10 forward-compat allowlist updates (Phase 39..48). Commit `533244c`. 13 files, +214/-10, 5591 passed (+13 over Phase 48 baseline 5578).

### 1. Content addition: general_event_zion_last_broadcast

`prototype/data/story/events.json` 에 `general_event_zion_last_broadcast` 신규 엔트리 추가 (53 → 54 events). Gibson-flavored Arc 5 late-arc Maelcum broadcast from the Zion dreadnaught ST. JOHN OF THE NIGHT SKY — 깁슨 원작의 *Neuromancer* / *Mona Lisa Overdrive* 에서 Case 를 Zion 궤도로 데려다 주는 reggae dread 조종사 Maelcum 이, 후배 자키에게 마지막 wisdom / memory 를 broadcast 로 전달. 따뜻한 톤(warm), ZION_ORBIT_RELAY 의 dreadnaught broadcast:

- **Category**: general, trigger: `node_enter`, trigger_condition: `arc_5_progress >= 60 AND random < 0.04 AND NOT has_status:zion_broadcast_seen`
- **Mood**: warm, location: matrix_zion_orbit, arc: 5, tier: 5, pillar: memory
- **Dialogue**: MAELCUM VOICE 메시지 5개 + CONSOLE broadcast source log
- **Choice**: Receive the broadcast (zion_affinity_+2, ta_rep_+1, zion_wisdom_unlocked, memory_archive_+1) vs Let it pass — the matrix does not need another ghost (safe_jackout, identity_marker_low, wintermute_-1, broadcast_silenced_marker)
- **Reward**: 0 credits + 110 XP + zion_mother_charm
- **Consequence**: zion_last_broadcast_branch (unique — global branch-id sweep)
- **Faction affinity**: zion_affinity +2 AND ta_rep +1
- **메타데이터**: phase 49 → 50, total_events 53 → 54, total_chains 6 unchanged

### 2. Polish — 1 modules (wetware_stacking docstring)

**`equipment/wetware_stacking.py`** — `stack_wetware()` docstring 확장. Args: 섹션 추가 (augment_ids + unknown IDs silently ignored note), Stacking rules 섹션 유지.

### 3. Forward-compat allowlist (10 forward-compat updates)

Phase 39..48 테스트의 `metadata["phase"] in (...)` allowlist 에 "49" 추가.

### 4. test_phase49_small_content_polish.py (13 tests 신규)

TestZionLastBroadcastEvent (11), TestZionLastBroadcastBranchUniqueness (1), test_phase_49_metadata + total_events (2).

### Validation

- make format: 변경 없음
- make lint (ruff): All checks passed
- make typecheck (mypy strict): 211 source files, 0 errors
- make test (pytest): 5591 passed (+13), 365 skipped, 1 xfailed (pre-existing)
- audit_vault.py: 0 broken (CLEAN)
- dashboard_pipeline_audit.py: 0 errors
- mixed_language_audit.py: 0 violations

### 5. Push 상태

8 commits ahead of origin (Phase 48 baseline + Phase 49). User action: GH_TOKEN rotation 후 `git push origin main`.

---

## [2026-08-17] feat(dashboard+rename) | Post-rename game + dashboard surface update

**Status**: ✅ 완료 — 게임 코드 + 대시보드 chrome + dashboard data rebuild. 3 commits (`581486d`, `c668aa5`, `bf809c5`). 567 files changed cumulatively. 5577 passed, ruff ✅, mypy strict ✅, audit_vault.py CLEAN.

### 1. Game core display name (5 files)

게임 윈도우 + About screen 에 표시되는 게임 이름 일관성 강화. 이전 commit (`ae83d00`)에서 디렉토리/Python 패키지명은 변경됐지만, 사용자에게 직접 보이는 게임 이름은 일부 남아 있었음.

| 파일 | 변경 |
|---|---|
| `prototype/src/wet_run/__init__.py` | docstring `"Roguelike Sprawl"` → `"Wet Run"` |
| `prototype/src/wet_run/settings.py` | `GAME_NAME = "Roguelike Sprawl"` → `"Wet Run"` |
| `prototype/src/wet_run/engine/config.py` | `SCREEN_TITLE = "Roguelike Sprawl"` → `"Wet Run"` (게임 윈도우 title) |
| `prototype/src/wet_run/audio/__init__.py` | docstring |
| `prototype/src/wet_run/audio/sound_manager.py` | docstring |

사용자가 게임 시작 시 보는 윈도우 titlebar는 이제 `Wet Run` 으로 표시.

### 2. Dashboard HTML chrome (548 files)

대시보드 전체 (`dashboard/`) 의 HTML chrome (검색엔진/소셜 메타) + 게임 내 러닝 텍스트 외곽 갱신:

- **521 short-story HTML**: `<title>` suffix `"— Roguelike Sprawl"` → `"— Wet Run"`
- **17 dashboard 페이지** (index, character-graph, cyberspace, search, mission-flow, stories-browse, player, missions, library, jokey, combat, dungeon, play, sound, settings, graphic-novel, reading-stats): canonical URL, og:url, og:image, twitter:image URL의 `roguelike-sprawl` → `wet-run`
- **footer chrome**: `"Roguelike Sprawl — Derivative Fiction"` → `"Wet Run — Derivative Fiction"` (521 footer)
- **print footer**: 단편 e-book print footer 갱신

Q3 정책 (historical 보존) 준수 — `_archive/`, `CHANGELOG.md`, `SETUP_LOG.md`, **단편 본문(prose content)** 의 cross-references는 그대로 유지.

### 3. Dashboard data + scripts (3 files)

| 파일 | 변경 |
|---|---|
| `dashboard/data/data_index.json` | `"repo": "/Users/emilio/projects/Projects/Game/wet_run"` |
| `dashboard/data/run_stats.json` | `"source": "prototype/src/wet_run/run/state.py"` (build_dashboard.py 재실행으로 자동 갱신) |
| `dashboard/scripts/import_minimax_track.sh` | `SND` 절대 path |

### 4. Test contract updates (3 files)

이전 commit들에서 변경된 chrome/suffix에 맞춰 test contract 갱신:

- `prototype/tests/integration/test_dashboard_integrity.py`: `title_clean.replace(" — Roguelike Sprawl", "")` → `" — Wet Run"`
- `prototype/tests/integration/check_dashboard.py`: 동일 contract
- `prototype/tests/unit/test_settings_data.py`: `assert GAME_NAME == "Wet Run"`

### 5. Code-side references (6 files, commit `c668aa5`)

prototype 코드/스크립트에서 남아있던 옛 이름 reference 일괄 정리:

- `prototype/Makefile`: `uv run roguelike-sprawl` → `uv run wet-run`
- `prototype/scripts/combat_grades_demo.py`: 헤더 배너
- `prototype/scripts/demo_full_flow.py`: console title
- `prototype/scripts/generate_story_html.py`: HTML title + footer templates
- `prototype/tests/unit/test_dashboard_meta.py`: expected OG URL (`seoca1.github.io/wet-run/`)
- `design/systems/stage_structure.json`: `"module": "wet_run.data_fragment"`

### 6. Dashboard data rebuild (13 files, commit `bf809c5`)

`tools/build_dashboard.py` 실행으로 13 stats JSON 모두 최신 게임 데이터로 재생성:

- character_stats, combat_stats, cyberspace_stats, data_index, design_system
- event_dialogues_stats, faction_stats, index_stats, journey_stats
- library_stats, mission_stats, run_stats, stages_stats

**Notable updates**:
- `library_stats.json`: `stories_with_mission_link` 189 → **236** (47 new)
- `library_stats.json`: `catalog_entries` 195 → **242** (47 new)
- `run_stats.json`: `_generated_at` 2026-08-13 → 2026-08-17 (refresh)
- `run_stats.json`: `source` path 자동 `wet_run` (template 자체가 이미 갱신됨)

### 7. Validation

| Gate | Status | Notes |
|---|---|---|
| `make test` | ✅ | 5577 passed, 365 skipped, 1 xfailed (pre-existing portrait 회귀, rename 무관) |
| `make lint` (ruff) | ✅ | All checks passed |
| `make typecheck` (mypy strict) | ✅ | 0 errors in 211 source files |
| `tools/audit_sprawl.py` | ✅ | 0 broken, 4 orphan (의도적 lore fragments) |
| `tools/find_broken_links.py` | ✅ | 0 broken |
| `python3 audit_vault.py` (workspace) | ✅ | CLEAN |

### 8. Pre-existing 이슈 (rename 무관)

- `tests/unit/test_armitage.py::TestArmitagePortraits::test_portraits_have_10x14_grid` — portrait actual size `[10, 12]` vs test expected `[10, 14]`. Phase 45 이후 data-driven 변경으로 보이며 본 세션 범위 외.

### 9. WetRun commit history (이번 세션)

```
bf809c5 feat(dashboard): rebuild stats JSON via build_dashboard.py
c668aa5 chore(rename): update remaining code references to Wet Run
581486d feat(rename): update game + dashboard display name to Wet Run
3dce6bb docs(wet_run): update GitHub URLs after repo rename
ae83d00 chore(rename): Roguelike Sprawl → Wet Run (project-wide display name)
```

### 10. Out of scope (preserved)

- 단편 HTML 본문 — 게임 내 러닝 텍스트이므로 보존 (Q3 default)
- `_archive/`, `CHANGELOG.md`, `SETUP_LOG.md` — historical
- `dashboard/stories/*.html` 단편 본문 cross-references
- GitHub repo URL — Q2 deferred 후속 (GH_TOKEN rotation 후 push)

### 11. Push 상태

**5 commits ahead of origin** (post-rename). GH_TOKEN rotation 후 user action:
- `git push origin main` (5 commits)

Total cumulative rename + dashboard update: ~580 files, 5 commits, 0 regressions, 0 broken wikilinks.

---
