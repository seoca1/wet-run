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
