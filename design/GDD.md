# Game Design Document (GDD)

> **Last updated**: 2026-08-27 (Phase 18 docs audit + v1.4.0 reflection + wet_run-web Tier 4 + ADR-0209)
> **Version**: v1.4.0 (Python) + Tier 4 + ADR-0209 (wet_run-web)

## 1. Concept

**One-liner**: 사이버스페이스에서 콘솔 카우보이로 플레이하는 로그라이크.

**Hook**: 죽으면 끝. 그러나 더 좋은 데크, 프로그램, construct로 돌아와서 더 어려운 시스템에 침투한다.

**Setting**: 윌리엄 깁슨 스프롤 3부작. 보스턴-애틀랜타 메트로폴리스와 L5 궤도 식민지.

**Tone**: 거칠고, 어둡고, 명료한 사이버펑크.

**주인공 (Player Character)**: 소설에 출현하지 않은 새로운 decker. 핸들(별명)만 플레이어가 선택. meatspace는 절대 시각화되지 않음 — 게임의 *유일한* 시각적 공간은 cyberspace (ADR-0009).

**meatspace 전달 방식**: 뉴스 / 이야기 (Story Archive). 의뢰 briefing, 의뢰 결과, 월드 뉴스, faction 움직임, construct 대화가 텍스트로 전달되며 메인 메뉴에서 다시 볼 수 있음.

**언어 (i18n)**: 영어 1차 (Gibson 톤 직접 보존) + 한글 보조 번역/자막. 표시 모드: Off (영어만) / Subtitle (영어+한글) / Replace (한글만). 모든 in-game 텍스트는 `data/i18n/en.json` (1차) + `data/i18n/ko.json` (보조)에서 로드 (ADR-0010).

**Reference**:
- Neuromancer / Count Zero / Mona Lisa Overdrive (world, lore)
- Caves of Qud / Cogmind (mechanics reference — 사이버 + 로그라이크)
- Hacknet / Bitburner (해킹 + 게임)
- Netrunner TCG (해킹 미학)
- (반대) Cyberpunk 2077 / Shadowrun (톤 회피)

## 2. Player Experience

플레이어가 게임 중 느끼는 것:

- **데이터가 흐르는 매트릭스 안에서 항해** — 시각적으로 강렬
- **ICE의 압박** — 시간이 지날수록 위험 증가
- **도구의 진화** — 매 런 새로운 프로그램을 손에 넣음
- **의뢰의 결과** — 죽음 또는 보상, 둘 다 명확
- **거친 미래** — 깁슨 톤의 비관적 매력

## 3. Game Structure

### 한 런의 구조
- **Deck Select (Phase 15)**: 런 시작 시 데크 사이즈 선택 — LIGHT (6 slots, +50% AP regen, -10% cooldowns) / STANDARD (8 slots, balanced, default) / HEAVY (10 slots, -30% AP regen, +15% cooldowns). 자키의 런-스타일 결정.
- **Job Board**: 3~7개 의뢰 중 선택 (Phase 16: `JobBoard.select_weighted` 가 reputation / NG+ / chain unlocks 반영해 추천 의뢰 편향)
- **Prep**: 데크/프로그램/웨웨어 로드
- **Infiltration**: 메트스페이스 → 매트릭스 진입
- **Matrix Run**: 미션 수행 (Phase 17: F.4 보스 phase 진입 시 1.5s yellow→phase color 블렌드, `BossPhaseTracker.get_damage_multiplier()` 가 데미지에 반영)
- **Extraction**: 매트릭스 이탈
- **Reward**: 보상 획득 또는 death (Phase 16: 성공 시 `record_run_completed` telemetry trigger — opt-in 한정)

### 메타 진행
- 새 데크 unlock (Ono-Sendai Cyberspace 7, SAMSARA 등)
- 새 프로그램 unlock (Goliath, Kraken, Wisp, Wardrone 등)
- 새 construct unlock (Dixie 류, 픽스처 AI)
- 의뢰 라인 / 클라이언트 진행 (light, optional)

### Phase 15-17 신규 시스템 (런 사이 흐름)

| 시스템 | 설명 | Phase |
|---|---|---|
| **Deck Size Picker** | NEW RUN 시작 시 LIGHT/STANDARD/HEAVY 3종 선택. AP regen / cooldown modifier 로 런 스타일을 결정 | 15 |
| **Telemetry Opt-In** | SETTINGS 의 toggle (`state.telemetry_opt_in`). off 시 모든 telemetry event 가 no-op (방어적 double-guard) | 15 |
| **Wetware Stacking Display** | EQUIPMENT 화면에 동일 wetware ID 다중 보유 시 누적 보너스 표시 (`equipment/wetware_stacking.py::stack_wetware`) | 15 |
| **Endings Browser** | 메뉴에서 EndingRenderer 진입, 해금된 엔딩 scene 을 ASCII 카드로 열람 (ADR-0192) | 15 |
| **Performance HUD** | F-key 토글. `PerfTracker` 가 FPS / tick 시간 표시 (개발자 + alpha tester 용) | 15 |
| **F.4 Boss Phase UI** | 보스 phase 진입 시 1.5초 yellow → phase color 블렌드. `CombatState.phase_change_ms` + `phase_change_color` 기록. 데미지는 `BossPhaseTracker.get_damage_multiplier()` 반영 | 15 + 17 |
| **Random Rules UI** | Hub ENTER 시 `JobBoard.select_weighted` 가 발동한 `rule_id` 를 `state.last_rule_id` 에 기록. Mission Details side panel 에 `Rule: <rule_id>` 주석. 디버그용 `_append_active_rules` 활성 룰 목록 | 16 + 17 |
| **Telemetry Summary Screen** | 메뉴 8번째 옵션 STATS. `OPTION_STATS=9`, opt-in off 시 dimmed. `render_telemetry_summary()` 가 `aggregate_death_rates` / `aggregate_kill_counts` / `aggregate_deck_distribution` / `aggregate_mutator_choices` 표시 | 17 |
| **Endings Persistence** | `ending_choice` 가 save metadata 에 직렬화, `restore_state()` 가 복원 (legacy save 호환) | 16 |

**Telemetry event firing sites** (Phase 16, opt-in 한정):
- `engine/death.py::trigger_death` → `record_death` + `record_run_completed` (failed run)
- `engine/reward_view.py::return_to_hub_from_reward` → `record_run_completed` (successful run)
- `engine/combat_view_state.py::start_combat` → `record_boss_reached` (boss ICE)
- `engine/menu.py::handle_deck_select_input` → `record_deck_chosen` (ENTER 확정 시)
- `engine/mission_completion.py::complete_mission` → `record_mission_completed`

### 난이도 모드 (Difficulty Modes)

> **Cycle 4 polish (2026-08-03, ADR-0140 partial)**: 런 시작 시 difficulty modifier를 선택하여 Pillar 3 (The Flatline)의 무게를 조절. v1.1.0에서 Hardcore 모드 1종만 출시; 향후 확장 예정 (v1.2.0+).

**현재 모드**:

| 모드 | 설명 | Pillar 영향 | 구현 |
| --- | --- | --- | --- |
| **Normal** (default) | ADR-0040 death/restart cycle 그대로 — DEATH_SUMMARY에서 new_jockey/same_jockey/hall_of_dead/menu 선택 가능. | Pillar 3 (기본) | `state.hardcore_mode = False` |
| **Hardcore** | 1-life permadeath — revival 경로 모두 차단. DEATH 시 PERMANENT DEATH 화면 → MENU 직접 라우팅. | Pillar 3 (강화) | `state.hardcore_mode = True` |

**Hardcore mode 동작 (자세한 명세)**: [`scenario/death-restart.md §6.5 Hardcore Mode Override`](scenario/death-restart.md)

**선택 시점**: 런 시작 시 (character select 직전 또는 settings에서). 런 중 토글 불가.

**Ephemerality** (Pillar 4 준수): AppState() 재생성 시 자동 reset. meta_state에 저장되지 않음.

**향후 확장** (v1.2.0+ backlog):
- 적 강화 모드 (ZDR +1~2)
- 자원 감소 모드 (시작 HP/AP 감소)
- Iron Man (Hardcore + 자동저장 비활성화)
- Custom Ruleset (multiplier 조합)

## 4. Core Systems

자세한 명세는 `systems/` 참조. 모든 시스템이 문서화됨 (2026-07-08 기준).

| 시스템 | 문서 | 상태 | ADR |
| --- | --- | --- | --- |
| 전투 (RT-MS) | `systems/combat.md` | **완료** | ADR-0003, ADR-0014 |
| 사이버스페이스 / 해킹 | `systems/hacking.md` | **완료** | ADR-0005 |
| 미션 | `systems/missions.md` | **완료** | ADR-0017 |
| 진행 (메타) | `systems/progression.md` | **완료** | ADR-0008 |
| 경제 (재화) | `systems/economy.md` | **완료** | — |
| 인벤토리 / 장비 | `systems/inventory.md` | **완료** | — |
| 대화 / NPC | `systems/dialogue.md` | **완료** | — |
| 절차적 생성 | `systems/procgen.md` | **완료** | ADR-0005 |
| Story Archive | `systems/story-archive.md` | **완료** | ADR-0009 |
| i18n | `systems/i18n.md` | **완료** | ADR-0010 |
| Crafting | `systems/crafting.md` | **완료** | ADR-0015 |
| Jockey Avatar | `systems/avatar.md` | **완료** | ADR-0016 |
| Animations | `systems/animations.md` | **완료** | ADR-0018 |
| Aftermath & Subtitles | `systems/aftermath.md` | **완료** | ADR-0019 |
| ASCII Portraits | `systems/ascii-portraits.md` | **완료** | ADR-0011 |
| Difficulty Rating (PPL & ZDR) | `systems/difficulty-rating.md` | **완료** | ADR-0012 |
| Story Events | `systems/story-events.md` | **완료** | ADR-0013 |
| 탐험 / Fog of War | `systems/exploration.md` | **완료** | ADR-0020 |
| Grade Progression | `systems/grade-progression.md` | **완료** | — |
| Plot Skeleton | `story_skeleton.md` | **완료** | ADR-0031 |

## 5. Content Pillars

### 의뢰 유형 (구현됨)

| 유형 | 설명 | 구현 |
|------|------|------|
| **Data Extraction** | 파일/데이터 탈취 (가장 흔함) | ✅ |
| **Sabotage** | 시스템 파괴 | ✅ |
| **Construct Retrieval** | AI construct 추출 | ✅ |
| **Surveillance** | 정보 수집 | ✅ |
| **Black Ops** | 다른 자키 해킹/제거 | ✅ (limited) |
| **ICE Bypass** | 방어선 뚫기 | ✅ |
| **Counter-Intelligence** | 흔적 지우기 | ✅ |

실제 미션 예시: `missions.json` (209 missions, 5 zones 균형; ADR-0206 wiring + ADR-0208 random_weight)

### 적 유형 (구현됨)

| 유형 | 설명 | 구현 |
|------|------|------|
| **ICE** | probe, watchdog, bulldog, asp, hellhound 등 97 types | ✅ |
| **Black ICE** | 치명적, trace 진행 | ✅ |
| **Boss ICE** | Wintermute, T-A Prime 3-phase | ✅ (ADR-0050) |
| **Hostile Deckers** | NPC 자키 (limited) | ✅ |
| **AIs / Constructs** | 보스급 (Dixie, Loa) | ✅ |

### 의뢰인/세력 (구현됨)

| 세력 | 설명 | 구현 |
|------|------|------|
| **The Finn** | Fixer — 주요 중개인 | ✅ |
| **Tessier-Ashpool (T-A)** | corporate, Deep zone | ✅ |
| **Hosaka** | corporate, Core zone | ✅ |
| **Sense/Net** | corporate, Surface/Mid zone | ✅ |
| **Yakuza** | 일본 마피아, Mid zone | ✅ |
| **Lo Teks** | 궤도 난민 | ✅ |
| **Panther Moderns** | 자키 게릴라 | ✅ (limited) |

## 6. 결정된 사항 (Decided)

### 핵심 결정 (ADR-0001 ~ ADR-0020)

| ADR | 제목 | 상태 |
|-----|------|------|
| ADR-0001 | 엔진/프레임워크 (libtcod + Python) | **Accepted** |
| ADR-0002 | 비주얼 스타일 (Pure ASCII) | **Accepted** |
| ADR-0003 | 전투 시스템 (RT-MS) | **Accepted** |
| ADR-0004 | 코드 아키텍처 (ECS-lite) | **Accepted** |
| ADR-0005 | 사이버스페이스 표현 (노드 그래프) | **Accepted** |
| ADR-0006 | 런 구조 (로그라이크 vs 로그라이트) | **Accepted** |
| ADR-0007 | 플랫폼 타겟 (macOS + Windows) | **Accepted** |
| ADR-0008 | 진행 / 레벨업 시스템 | **Accepted** |
| ADR-0009 | Story / News 전달 시스템 | **Accepted** |
| ADR-0010 | i18n + Content Pipeline | **Accepted** |
| ADR-0011 | ASCII Portraits | **Accepted** |
| ADR-0012 | Combat Difficulty (PPL & ZDR) | **Accepted** |
| ADR-0013 | Story Events System | **Accepted** |
| ADR-0014 | Data Salvage (전투 보상) | **Accepted** |
| ADR-0015 | Material & Crafting System | **Accepted** |
| ADR-0016 | Jockey Avatar | **Accepted** |
| ADR-0017 | Mission-Material Integration | **Accepted** |
| ADR-0018 | Combat Animation | **Accepted** |
| ADR-0019 | Combat Aftermath & Subtitles | **Accepted** |
| ADR-0020 | Fog of War + Exploration | **Accepted** |

### Phase 6~7 결정 (ADR-0030 ~ ADR-0061)

| ADR | 제목 | 상태 |
|-----|------|------|
| ADR-0030 | GitHub Utilization Plan | **Accepted** |
| ADR-0031 | Original Scenario Integration | **Accepted** |
| ADR-0032 | Graphic Novel Auto-Play Mode | **Accepted** |
| ADR-0040 | Death & Restart Cycle | **Accepted** |
| ADR-0041~0044 | Graphic Novel Content Expansion | **Accepted** |
| ADR-0046~0049 | Graphic Novel Endings + Saves | **Accepted** |
| ADR-0050 | Boss ICE System (Wintermute + T-A) | **Accepted** |
| ADR-0051 | Mission Story Metadata | **Accepted** |
| ADR-0052 | Short Story Expansion Plan | **Accepted** |
| ADR-0060 | Dungeon Exploration Redesign | **Accepted** |
| ADR-0061 | Novel Integration Architecture | **Accepted** |

### Phase 8~10 결정 (ADR-0090 ~ ADR-0102)

| ADR | 제목 | 상태 |
|-----|------|------|
| ADR-0090 | Salvation Phase Integration | **Accepted** |
| ADR-0101 | Fiction Metadata Backfill | **Accepted** |
| ADR-0102 | v1.0.0-beta.1 Release | **Accepted** |

자세한 것은 `decisions/README.md` 참조.

### Plot Skeleton (주요 줄기 뼈대)

상세: `design/story_skeleton.md`

- **5 arcs**: First Run → The Sprawl → Corporate Ice → The AIs → The Choice
- **9 endings**: 3 chars × 3 endings (A/B/C) — Sprawl Returns, AI Awakens, Lo Tek, Flatline
- **초반 우선**: Arc 1 (1-3 jobs) — Phase 5에서 우선 구현
- **반복 보강**: 무한 side content, faction 뉴스, world events

**Content pillar totals (v1.4.0, 2026-08-26)**:
- 209 missions (5 zones 균형; ADR-0206 Arc6 + Expansion wiring)
- 97 ICE types (incl. 14 skill effects + 15 skill animations)
- 9 jockeys / 29 endings (9 × A/B/C + salvation)
- 81 GN scenes (12 prologue + 9 × 8 endings + epilogue)
- 30 programs (ADR-0193 expansion)
- 150+150 = 300 short stories (EN + KO)
- 16 stages / 18 chapter states / 4 objectives
- 5 NPCs / 14 dialogues / 51 lines
- **wet_run-web**: 30 missions / 30 ICE / Tier 4 (ADR-0207) + IDB save (ADR-0209)
- 8 node kinds / 8 zone depths

### 디자인 영향 (Accepted 결정으로 제약)
- **Pillar 2 (The Matrix)**: ASCII 노드 그래프 + *유일한* 시각적 공간
- **Pillar 3 (The Flatline)**: 스탯 고정 = 한 자키의 무게
- **Pillar 4 (The Build)**: 자키 등급 + unlock + Story Archive로 표현
- **Pillar 5 (The Style)**: 깁슨 톤 + ASCII + mediated world + 다국어
- **콘텐츠**: 데이터 주도, 초반 우선, plot bones 사전 정의

### 미해결 / 열린 질문 (2026-07-08 기준, partial update 2026-08-03)

| 질문 | 상태 | 비고 |
|------|------|------|
| 한 런의 목표 길이 (30/60/90분) | ⏳ 열린 질문 | 플레이어 피드백 필요 |
| 한국어 톤 가이드 (깁슨 한국어 차용) | ⏳ 열린 질문 | ADR-0010 참조 |
| Arc trigger 조건 (등급/unlock/선택) | ✅ 해결 (ADR-0031) | 챕터 JSON + arc 데이터로 구현 |
| Hub 표현 | ✅ 해결 | 텍스트 메뉴 + cyberspace construct |
| Story Archive 카테고리/검색 | ✅ 해결 (ADR-0009) | 4 카테고리 + StoryEvents로 확장 |
| Construct companion (Dixie-as-ally) | ⏳ 열린 질문 | 현재 dialogue only (core_loop.md) |
| New Game+ / Hardcore mode | ⏳ 열린 질문 | Phase 10+ (core_loop.md) |
| Pillar 4 — Grade 5→6 growth 1.20× | ⏳ 열린 질문 | ADR-0130 v1.1.0+ follow-up |
| Pillar 5 — 보상 곡선 공식 vs 실제 55~96% | ⏳ 열린 질문 | ADR-0130 v1.1.0+ follow-up |
| Construct 동료 시스템 | ✅ 해결 (limited) | Dixie Flatline dialogue만 구현 |

## 7. Living Spec

이 문서는 살아있는 스펙이다. 매 디자인 결정은 `decisions/`에 ADR로 기록되고, 본 문서와 `systems/`가 그에 따라 갱신된다.

### 동기화 규칙
- 새 시스템 추가 시 `systems/`에 명세 작성
- 명세 변경 시 `testcases/`에 시나리오 추가
- 의뢰 유형 추가 시 `missions.md`에 명세
- 적 추가 시 `combat.md`에 명세

## 8. 비-기둥 (회피)

`pillars.md` 참조. 명시적으로 만들지 않을 것들:

- Loot grind, Multiplayer, Skins, Daily login, Infinite scaling, Prestige, Mobile/F2P

---

## 9. Phase 18 Audit Trail

Phase 15-17 동안 추가된 6개 engine 통합 (deck picker / telemetry opt-in / wetware stacking / F.4 boss phases / random rules / endings persistence) 와 3개 UI 노출 (F.4 phase UI / random rules UI / telemetry stats) 이 본 문서에 반영됨.

**이전 known issues**:
- ~~Content totals 가 v1.0.0 (2026-08-03) 기준~~ → 2026-08-27 갱신: v1.4.0 (209 미션, 97 ICE, 29 엔딩) 으로 통일.
- 로드맵 항목 `Hardcore mode` (Phase 4 polish) 은 §3 Game Structure 에서 별도 다룸.

**후속 예정** (Phase 19+):
- Phase 14 에서 wired 되지 않은 `integrate_with_game_loop` per-tick profiler (ADR-0184 partial) — gameplay 영향 없이 보류.
- Run mutator UI (mutator selection 결과만 telemetry 집계, 현재는 보너스 선택 메뉴만 노출).
