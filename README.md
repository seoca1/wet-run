# Dashboard — Page ↔ Data Source Map

각 dashboard 페이지가 어떤 데이터/문서와 동기화되어 있는지 정리.
`docs/` 의 게임 시스템 변경 시, 해당 페이지를 함께 갱신.

---

## 🤖 자동 동기화 (build_dashboard.py)

`../tools/build_dashboard.py` 가 게임 데이터를 읽어
`dashboard/data/{combat,novel,story,cyberspace,journey}_stats.json` 를 생성.
대시보드 페이지는 런타임에 이 JSON 을 `fetch()` 해서
`data-stat="..."` 셀을 자동 갱신합니다.

```bash
prototype/.venv/bin/python tools/build_dashboard.py
```

| Stat JSON | 데이터 소스 | 사용하는 페이지 |
|---|---|---|
| `combat_stats.json`     | `prototype/data/combat/ice_types.json` (29 ICE), `effects.py:15 animations`, `programs.json` | `combat.html` (5 카드) |
| `novel_stats.json`      | `Fiction/.../short-stories/*.md` (30 stems), `novel/hooks.py:HookKind` | `novel.html` (6 카드) |
| `story_stats.json`      | `prototype/data/missions/missions.json` (47), `story/chapters/*.json` (12) | `stories-browse.html` / `stages.html` |
| `cyberspace_stats.json` | `prototype/data/cyberspace/worlds.json` (2 worlds / 4 sectors / 6 servers), `matrix/node.py:NodeKind` (8) + `ZoneDepth` (4) | `cyberspace.html` (5 카드) |
| `journey_stats.json`    | hardcoded (novice/veteran/heretic credits) | `journey/*.html` |
| `index_stats.json`      | `pytest --collect-only` (tests_total), `prologue_data.json` (lines), `event_dialogues.json` (npcs), `stage_structure.json` (stages/missions) | `index.html` (Project Status 패널) |
| `character_stats.json`  | `design/story/characters.md` (9 캐릭터 × 5 attributes) | `story.html` (캐릭터 카드 age / deck / weapon / origin / job) |
| `run_stats.json`        | `prototype/src/run/state.py` Stage / ChapterState / ObjectiveKind enum | `stages.html` (Stage enum count) + `story.html` (endings count) |
| `data_index.json`       | 위 8 파일의 인덱스 | (참조용) |

각 페이지는 fallback 으로 정적 HTML 값을 가지고 있어,
빌드 스크립트 없이도 모든 페이지가 정상 표시됩니다.

---



---

## Top-level index

| 페이지 | 동기화 소스 | 자동 / 수동 | 메모 |
|---|---|---|---|
| `index.html` | `<status>` JS fetch: `prologue_data.json`, `event_dialogues.json`, `stage_structure.json` | 자동 (런타임 fetch) | 사이드바 15 카드 / Phase 진행 status. |
| `data/play_game.json` | 미션 15 + 챕터 15 + 엔딩 2 + 캐릭터 3 + 단편 HTML 링크 | auto-gen 스크립트 없음 — `play.html` 갱신 시 함께 수동 | Play (Beta) 단일 페이지 데이터. |

---

## Character / Story / System

| 페이지 | 동기화 소스 | 자동 / 수동 | 메모 |
|---|---|---|---|
| `story.html` | 캐릭터 3명 (Case/Sil/Kas) — `<div class="character-card">` 정적 디자인. 챕터 카드 21개는 JS 동적 렌더 (inline). | 혼합 | **character-card 부분 정적**. 예: 나이/데크/무기/동기/인용구 — 디자인 콘텐츠. |
| `stories-browse.html` | `Fiction/derivative/sprawl-trilogy/short-stories/*.md` (29 stems) → 58 HTML | 자체 generator (`prototype/scripts/generate_story_html.py`) | **통계 동기화 완료**: 29/58/29/29/0 (commit b91b7cc). 2026-07-10 stories.html → stories-browse.html 합병. |
| `stories/journey/{novice,veteran,heretic}.md\|html` | 시뮬레이션 시나리오 (정적). Missions 데이터와 직접 동기화 없음 (별도 합산). | 정적 | novice 20,050 / veteran 27,500 / heretic 20,100 cr (디자인 값). |
| `stories/short-stories/{en,ko}.html` | 단편 본문 (58개) | `generate_story_html.py` | 자동 생성. 다시 실행 시 replace. |
| `stories/episode-reader.html` | 챕터 카드 인덱스 — `chapters/{case,sil,kas,...}.json` (9 자키) | 정적 | 9 챕터 × 2 (EN+KO) = 18 카드. 2026-07-08 story_read.html → stories/episode-reader.html 이동. |

---

## Mechanic (게임 메카니즘)

| 페이지 | 동기화 소스 | 자동 / 수동 | 메모 |
|---|---|---|---|
| `combat.html` | ICE 5 등급 (Standard/Watchdog/Goliath/Black/Construct) — `combat/ice_types.json` (29 entries, 5 등급만 표시). 스킬 14 effects — `combat/effects.py:SKILL_EFFECT_ANIMATIONS`. | 정적 | 5 ICE / 14 effects 디자인 확정 (outdated 아님). |
| `cyberspace.html` | World/Sector/Server 계층 | 정적 | 2 worlds / 4 sectors / 6 servers / 8 nodes — 디자인 값. `cyberspace/world.py` 의 데이터와 비교 검증 안 됨. |
| `equipment.html` | 8 슬롯 / 6 등급 / 9 기술 | 정적 | `equipment.json` 부재 — `equipment/` 패키지에서 코드 검토 필요. |
| `sound.html` | 6 카테고리 / 27 사운드 / 5 테마 — `audio/config.py` `SoundCategory` / `audio/sound_manager.py` (런타임 등록) | 정적 | 런타임 자동 등록, dashboard 페이지 정적. |
| `graphic-novel.html` | 12 씬 자동재생 — `data/scenes/{case,sil,kas}/{01..04}.json` (12 파일) | 정적 | 카드 인덱스 + 씬 재생. inline JSON 들어 있음. |
| `achievements.html` | 27 업적 (탐험/전투/경제/엔딩/메타) | 정적 | 코드상 정의 (`achievements/achievements.py`) 와 dashboard 카드 비교 필요. |

---

## System (운영)

| 페이지 | 동기화 소스 | 자동 / 수동 | 메모 |
|---|---|---|---|
| `stages.html` | `<div class="stage-flow" data-stage-src="../design/systems/stage_structure.json">` | **자동 (런타임 fetch)** | 9 stages / 8 transitions / 29 missions. 헤더 텍스트 동기화 완료 (commit b91b7cc). mission 카드는 fetch 동적. |
| `settings.html` | 6 사운드 카테고리 + 키 바인딩 | 정적 | dashboard 페이지. `audio/config.py` 와 비교 검증 필요. |
| `player.html` | 5 grades / 8 ICE types / 3 tiers | 정적 | `combat/ppl.py` 데이터와 비교. |

---

## ADR / Dungeon / Novel

| 페이지 | 동기화 소스 | 자동 / 수동 | 메모 |
|---|---|---|---|
| `dungeon.html` | `docs/DUNGEON_*.md` (3 파일) — ADR-0060 대시보드 | 정적 | **dead link 3개 수정** (commit b91b7cc) — `../Game/...` → `../...`. |
| `novel.html` | `decisions/006[01]-*.md` + README — ADR-0061 대시보드 | 정적 | **dead link 3개 수정** (commit b91b7cc). |
| `play.html` | `<script>fetch('data/play_game.json')</script>` — 인터랙티브 챕터 데모 | 자동 (fetch) | 15 챕터 × 15 미션 × 2 엔딩. |

---

## Documents (related)

| 파일 / 디렉토리 | 용도 |
|---|---|
| `decisions/0060-dungeon-exploration-redesign.md` | ADR-0060 (Dungeon Redesign) |
| `decisions/0061-novel-integration-architecture.md` | ADR-0061 (Novel Integration) |
| `docs/DUNGEON_*.md` (3개) | Dungeon 설계 명세 |
| `prototype/data/missions/missions.json` | 미션 29개 소스 (verify_story_links 가 참조) |
| `prototype/data/story/chapters/{case,sil,kas}.{json,md}` | 챕터 본문 + excerpt |
| `prototype/data/combat/ice_types.json` | 29 ICE entries |
| `prototype/data/combat/programs.json` | 프로그램 카탈로그 |
| `design/systems/stage_structure.json` | 9 stages + 8 transitions + 29 missions (commit 89f156c) |
| `Fiction/derivative/sprawl-trilogy/short-stories/` | 65 단편 MD (29 × en+ko + lang) |

---

## Quick-Links (index.html footer)

| 링크 | 파일 | 검증 |
|---|---|---|
| `../design/story/characters.md` | ✓ | |
| `../design/story/prologue.md` | ✓ | |
| `../design/story/prologue_data.json` | ✓ | |
| `../design/story/event_dialogues.json` | ✓ | |
| `../design/systems/stage_structure.json` | ✓ | |
| `../ROADMAP.md` | ✓ | |
| `../AGENTS.md` | ✓ | |

---

## 변경 이력 (Dashboard)

- **2026-06-30 (commit b91b7cc)** — Dead links (dungeon 3 / novel 3 / story 2) + stats sync (stages 26→29 / stories 32→29).
- **2026-06-30 (commit 89f156c)** — `stage_structure.json` missions 26→29 (3 추가: flatline_call, sally_returns_arc3, sally_sandii_3am).
- **2026-06-30** — Dashboard `data-status` audit + `dashboard/README.md` 작성.

---

## Dashboard Update Log (2026-07-25)

- **search_index.json**: Fixed novelette indexing bug. Previously only Bridge novelettes were processed; Blue Ant and Sprawl novelettes were excluded by missing directory constants. Added `SPRAWL_NV_EN_DIR`, `SPRAWL_NV_KO_DIR`, `BLUE_ANT_NV_EN_DIR`, `BLUE_ANT_NV_KO_DIR` constants and updated the for-loops in `load_all_stories()` and the trilogy classification in `gen_search_index()`. Result: search_index grew from 218 → 226 entries (all 7 novelettes now indexed in EN+KO).
- **game_facts.json**: Refreshed via `sync_dashboard_facts.py`.
- **All 10 dashboard JSON stats**: Regenerated via `build_dashboard.py`.
- **story HTML**: Regenerated for all short-stories via `markdown_to_story_html.py` (both EN and KO). Novelettes are NOT currently rendered to HTML — would require extending `markdown_to_story_html.py` to handle the `novelettes/` directories.

## Current Coverage

- EN stories: 113 (84 Sprawl ss + 86 = ... — see search_index)
- KO stories: 113
- Search index: 226 entries
- Short-stories HTML: 222 files (111 × 2 langs) in `stories/short-stories/`
- Novelette HTML: 14 files (7 × 2 langs) in `stories/novelettes/` — auto-generated as of 2026-07-25

## Updated CI Workflow (2026-07-25)

`.github/workflows/dashboard-build.yml` `Generate story HTML pages` step was generalized from explicit per-trilogy/per-lang calls to a loop over all 3 trilogies × short-stories + novelettes × EN + KO. Future content additions automatically get HTML pages without CI changes.
