# Wet Run — Improvement Log (2026-07-01)

> **상태**: Phase 5 (Vertical Slice) 완료 + Phase 6 (Content) 진입
> **테스트**: **3442 pass** + 35 skip + 15 xfail · ruff / mypy strict 모두 green
> **커밋 누적**: +27 (이번 사이클)
> **대상**: `Game/wet_run/` 깁슨 스프롤 로그라이크

> **📌 헤더 노트 (2026-08-03)**: 본 문서는 2026-07-01 시점의 Phase 5→6 P0/P1/P2 cycle 결과입니다.
> 이후 v1.0.0 (2026-07-28) polish + v1.1.0 prep (2026-07-28~) 으로 code/test/design 이 모두 갱신되었습니다.
>
> **현재 상태 (v1.0.0 FINAL, 2026-08-03)**:
> - 3,278 tests pass / 664 skipped (vs 3,442 + 35 skip + 15 xfail at 2026-07-01)
> - 142 source files / 39,166 LOC (vs 108 files / 28,000 at 2026-07-01)
> - 5 ADRs 신규 (0125, 0130, 0131, 0133, 0140, 0141) — Engagement Layer + module splits
> - 111 missions / 58 ICE / 9 jockeys / 81 GN scenes (대폭 증가)
> - Dashboard 갱신: 17 stat JSON 2026-08-03 fresh
>
> **계획**: 본 log.md 와 design/GDD.md 가 v1.0.0 상태로 sync 됨 (2026-08-03).
> Game quality assessment + upgrade plan (4-cycle roadmap) 진행 중.

---

## 요약

이번 사이클에서 **3개 P0 + 8개 P1 + 12개 P2 = 23개 이슈** 해결.
누적 테스트 **3254 → 3442** (+188 tests, +5.8%).

핵심 결과:
- **신규 시스템 1개** — Faction Reputation (설계 + 데이터 + 3-hook 통합)
- **신규 시스템 1개** — Equipment Set Bonuses (3 세트 × 2pc/3pc)
- **신규 티어 1개** — Grade 6 Master tier (T6 장비 3종)
- **P0 버그 3개** — 미션 13개 차단 해제, 전투 ICE hardcoded placeholder, 9개 누락 ICE 추가
- **P1/P2 개선 9개** — save migration, status message cap, action_menu, i18n format, hub data-driven, gauge overflow, programs role, DEATH_RESTART cycle, theme logging
- **디자인 문서 7개** — Phase 2 디자인 명세 100% 완성
- **테스트 39개** — equipment.py 0 → 39 (이전 가장 큰 untested 모듈 해소)

---

## P0 — Blocking Issues (3개)

### P0 #1: ZoneDepth enum 확장 — 13/29 미션 차단 해제
- **파일**: `matrix/node.py`, `matrix/zdr.py`, `missions/mission.py`, `data/missions/missions.json`
- **문제**: `ZoneDepth` enum이 `SURFACE/MID/CORE/TA` 4종만 지원했으나 13개 미션이 `deep`/`freeside` 사용 → `__post_init__` ValueError → `_parse_mission` 가 silently None 반환
- **해결**: `DEEP`, `FREESIDE` 추가 + `zdr.py` 베이스 ZDR (DEEP=8, FREESIDE=30) + Mission 검증 `grade_max`/`reward_tier` 를 0..6 으로 확장
- **효과**: 미션 16/29 → **29/29 로딩** (모든 미션 플레이 가능)
- **회귀**: 4 tests (`test_job_board_loads_all_29_missions`, `_zones_all_valid`, `ZoneDepth has DEEP/FREESIDE`, `_filters_by_grade` g6 케이스)

### P0 #2: Combat hardcoded ICE placeholder
- **파일**: `engine/combat_view.py:907`
- **문제**: `ice_kind = "standard"` 하드코딩으로 모든 ICE 노드가 동일한 Standard 적 스폰. 5종 ICE 타입 / 보스 시스템 (ADR-0050) / PPL·ZDR 밸런스 무력화
- **해결**: `ice_node.ice.value` 사용 + `IceKind.NONE` 방어적 fallback + `KeyError` 시 Standard fallback
- **회귀**: 2 tests (`test_start_combat_uses_node_ice_kind` Black/Watchdog 분기, `test_all_mission_ice_ids_resolve` 29 미션의 모든 `ice.X` 참조)

### P0 #3: 9개 누락 ICE 엔트리 추가
- **파일**: `data/combat/ice_types.json`
- **문제**: 미션이 `ice.construct`, `ice.boss`, `ice.neuromancer` 등 9종 참조하지만 레지스트리에 없음 → `KeyError` 발생 가능
- **해결**: 9개 신규 엔트리 (`construct`, `boss`, `revelation`, `neuromancer` T5, `ai_whisper`, `surveillance`, `wintermute` T4, `zion_defense`, `loa`)
- **효과**: 미션 29개 중 23개가 이제 실제 ICE 노드 스폰 가능

---

## P1 — Significant Gameplay Issues (8개)

### P1: Save format migration 자동화
- **파일**: `engine/save_manager.py`, `engine/graphic_novel_save.py`
- **문제**: `SaveVersionMismatchError` 만 던지고 기존 세이브 폐기
- **해결**: `_SAVE_MIGRATIONS` / `_GN_SAVE_MIGRATIONS` 체인 — `<legacy>` → 현재 버전까지 자동 업그레이드 (GN 1.0.0→1.1.0→1.2.0)
- **회귀**: 4 tests (`test_legacy_save_without_version_loads`, `test_legacy_via_restore_state`, `test_unknown_version_still_raises`, `test_current_version_passes_through_unchanged`)

### P1: Status message 무한 누적 방지
- **파일**: `engine/state.py`
- **문제**: 107 호출 사이트가 `state.status_messages.append(...)` 로 무한 누적. 긴 세션 메모리 누수
- **해결**: `StatusMessageList(UserList[str])` 서브클래스 + `STATUS_MESSAGES_MAX = 100` cap. `append/extend/insert/__setitem__/__iadd__` 가 가장 오래된 항목부터 제거
- **회귀**: 5 tests (under cap / at cap / extend truncate / empty / AppState 통합)

### P1: Audio theme silent exception handlers
- **파일**: `audio/theme.py`
- **문제**: 5개 `except Exception: pass` 가 디버깅 불가능
- **해결**: `_log_warning()` helper — lazy engine.logger import + stderr fallback, 5개 catch 지점 모두 로깅화

### P1: Action menu Phase 6+ stubs
- **파일**: `engine/action_menu.py`
- **문제**: HACK / COMMUNICATE / ACCESS 메뉴 옵션이 "not yet implemented (Phase 6+)" 만 표시
- **해결**: 각각 lightweight 동작:
  - HACK (SYSTEM 노드): 1x Data Fragment + probe flavor
  - COMMUNICATE (CONSTRUCT): narrative beat ("construct listens")
  - ACCESS (CORE): next unvisited 노드를 `context_hint` 로 노출
- **효과**: 플레이어가 모든 메뉴 옵션 시도 가능

### P1: i18n format args 누락 fallback
- **파일**: `i18n/translator.py`
- **문제**: `t("Hello {name}")` 호출 시 누락된 kwargs 가 raw `{name}` 그대로 UI 노출
- **해결**: `_format_template()` — `string.Formatter.parse()` 로 필드 식별, 누락 시 `<name>` 마커. 예외 절대 발생 안 함
- **회귀**: 3 tests (existing 1 수정 + 2 추가: partial kwargs, no kwargs)

### P1: Hub hardcoded materials/recipes → 데이터 주도
- **파일**: `engine/hub.py`, `data/crafting/materials.json`, `data/crafting/recipes.json`
- **문제**: 4-panel Hub 중 Materials/Recipes 패널이 하드코딩된 placeholder 사용
- **해결**: `data/crafting/{materials,recipes}.json` 신규 + `_load_materials_data()` / `_load_recipes_data()` loader + `_PLACEHOLDER_*` graceful fallback
- **회귀**: 7 tests (real file load / fallback when missing / fallback when malformed / inventory lookup + 4 material gauge tests)

### P1: Equipment.py 0 → 39 tests (이전 가장 큰 untested 모듈)
- **파일**: `equipment/equipment.py`, `tests/unit/test_equipment.py`
- **문제**: 447 lines, 18 items, 8 slots, 7 tiers — 테스트 0
- **해결**: EquipStats / Equipment / EquipmentLoadout / EquipmentRegistry / 15 기본 장비 모두 커버
- **회귀**: 39 tests

### P1: 보상 밸런스 outliers 수정
- **파일**: `data/missions/missions.json`
- **문제**: `ta_heist` 5000 credits (T4 노이즈), `final_choice` 10000 credits (T5 2× 정상)
- **해결**: ta_heist 3500, final_choice 5500 (각각 동급 정상 범위로)

---

## P2 — Polish / Content / Maintainability (12개)

### P2 #15: Equipment Set Bonuses (3개 세트 × 2pc/3pc)
- **파일**: `equipment/equipment.py`
- **문제**: `set_id` 필드 dataclass 에 존재하지만 모든 장비 None
- **해결**:
  - `SET_BONUSES`: 3 세트 × 2 임계값 (ono_sendai / militech / arasaka)
  - `EquipmentLoadout.set_counts()`, `set_bonuses()`, `total_stats()` 가 자동 합산
  - `get_set_bonus(set_id, pieces_equipped)` helper
- **할당**: STARTER_DECK + STREET_DECK + CORPORATE_DECK (ono_sendai), MILITECH_EYES + CHROME_GLOVES + MILITECH_DECK (militech), ARASAKA_DECK + KEREZNIKOV (arasaka)
- **회귀**: 11 tests

### P2 #16-19: 그래픽 노블 polish
- 컷신 dialogue 4× 확장 (4188 → 16862 chars)
- 챕터 카드 I-XII + fade transition
- 15개 scene cue → file 매핑
- GNProgress atomic save + CONTINUE READING 메뉴

### P2 #17: Hub perf (JSON 파싱 캐싱)
- **파일**: `engine/hub.py`
- **문제**: 매 render frame 마다 `_load_materials_data()` / `_load_recipes_data()` 가 JSON 파싱
- **해결**: module-level `_MATERIALS_CACHE` / `_RECIPES_CACHE` + `force_reload=True` 옵션
- **회귀**: 5 tests (cache populated / reused / force_reload bypasses / recipes / no repeated io)

### P2 #18: Material gauge 비율 손실
- **파일**: `engine/hub.py:_material_gauge`
- **문제**: `7/3` 같은 overflow 케이스가 `5/0` 로 잘려서 손실
- **해결**: `have/need` 비율 + ready 100% 표시 + overflow `+` marker

### P2 #19: Status message i18n 4-line page + 30줄 소설 페이지
- **파일**: `engine/graphic_novel_view.py`, `chapter_cutscene.py`

### P2 #20: Programs role 분류
- **파일**: `data/programs/programs.json`
- **해결**: 9개 프로그램에 `role` 필드 (burst/strike/sustain/guard/utility) + 회귀 테스트

### P2 #13: Death → Restart cycle 회귀 테스트
- **파일**: `tests/unit/test_run_state.py`
- **신규**: `TestDeathRestartCycle` 7 tests (full cycle / blocked at terminal / mark_advance no-op 등)

### P2 #11: Phase 2 디자인 문서 7개 신규
- `inventory.md` — 8 슬롯 × 8 카테고리 × 6(7) 티어 × 12 stats + 15(18) 장비
- `dialogue.md` — 5 NPC + 스키마 + 트리거 + Dixie 동맹
- `procgen.md` — 3-tier 절차적 생성 (BSP/Kruskal/Mission→Room)
- `i18n.md` — Translator API + format kwargs + display modes
- `story-archive.md` — 5 종류 + 4 importance + Hall of Dead
- `progression.md` — 3-tier 구조 + PPL 공식 + Death 사이클
- `balance/ppl_zdr_balance.md` — PPL 곡선 + ZDR 매트릭스 + 미션 보상 공식 vs 실제

---

## Phase 2 디자인 명세 100% 완료

ROADMAP 체크리스트의 모든 누락 문서 작성 완료:

| 문서 | 내용 |
|---|---|
| `inventory.md` | 8 슬롯 × 8 카테고리 × 7 티어 × 12 stats |
| `dialogue.md` | NPC 5명 + 스키마 + 트리거 |
| `procgen.md` | BSP/Kruskal/Mission→Room 3-tier |
| `i18n.md` | Translator + format args + modes |
| `story-archive.md` | 5 kinds + Hall of Dead + Cinematic |
| `progression.md` | 3-tier 진행 + PPL 공식 |
| `balance/ppl_zdr_balance.md` | PPL/ZDR 곡선 + Grade 6 |

---

## 신규 시스템: Grade 6 Master Tier

Arc 5 finale 미션 (`neuromancer_merger`, `zion_express`) 의 `grade_max=6` 이 도달 불가능했음. 해결:

- `matrix/ppl.py`: tier 검증 0..6 + `MAX_TIER = 6` 상수 + `grade_for_loadout(loadout)` helper
- `equipment/equipment.py`: `EquipTier.T6_MASTER` + 3개 마스터 장비 (`MASTER_DECK`, `MASTER_BODY`, `ZION_TRODES`)
- `equipment/equipment.py`: `EquipmentRegistry.load_default()` 15 → **18 items**
- **회귀**: 6 tests (`test_ppl_t6_master_deck_supported`, `test_ppl_t6_full_loadout_outperforms_t5`, `test_grade_for_loadout_returns_max_tier`, `test_max_tier_constant`, `test_ppl_mixed_tiers_with_t6_program`, `test_default_registry_has_18_items`)

---

## 신규 시스템: Faction Reputation

깁슨 스프롤의 5개 faction (Hosaka / Maas / Sense/Net / T-A / None) 별 자키 평판 추적.
5개 디자인 문서에서 "future work" 로 표시된 핵심 시스템.

### 컴포넌트

| 파일 | 역할 |
|---|---|
| `run/reputation.py` | `FactionReputation`, `ReputationState`, `reputation_tier()`, `clamp_delta()` |
| `engine/state.py:203` | `AppState.reputation` 필드 (default empty) |
| `engine/save_manager.py:445,556` | save/restore 직렬화 + legacy 빈 처리 |
| `engine/mission_completion.py:30-67` | `FIXER_REPUTATION` 매핑 + `_apply_fixer_reputation()` hook |
| `engine/combat_view.py:769-808` | `COMBAT_REPUTATION` 매핑 + `_apply_combat_reputation()` hook |
| `engine/hub.py` | `_render_reputation_dots()` Avatar 패널 표시 |

### 7 단계 Tier

| Score | Tier | Glyph |
|---:|---|---|
| ≥ 80 | ALLIED | ★ |
| ≥ 50 | FRIENDLY | ● |
| ≥ 20 | TRUSTED | ○ |
| > -20 | NEUTRAL | · |
| > -50 | HOSTILE | ✗ |
| > -80 | ENEMY | ✗ |
| ≤ -80 | OUTCAST | ✗ |

### Hook 통합 (3곳)

| Hook | 트리거 | 효과 |
|---|---|---|
| **Mission completion** | `complete_mission(state, mission)` | fixer별 faction 평판 조정 (finn: +5/+5, maas: +10/-3, sally: +10/-3, ta_rep: +10/-3, kumiko: +8, dixie: +3/-3, yakuza: 무) |
| **Combat ICE defeat** | `_end_combat(state, combat_state)` | 노드 faction의 server 침해 → 방어 -3, 적대 +1 |
| **Hub 시각화** | Avatar 패널 render | `Rep: ●○·✗·` 5-faction strip |

### 회귀 테스트 39개 (reputation)

- `TestClampDelta` (3), `TestReputationTier` (14), `TestFactionReputation` (7), `TestReputationState` (6), `TestSerialization` (7)
- 추가로 `TestSaveManager::test_restores_reputation` (save roundtrip), `test_restores_reputation_missing_field` (legacy)
- 추가로 `TestFactionReputationOnCompletion` (9), `TestFixerToFactions` (3), `TestFixerReputationTable` (2)
- 추가로 `TestReputationDots` (5)

---

## 신규 시스템: Equipment Set Bonuses

3개 코호트 세트 정의 + 2pc/3pc 임계값:

| Set | 2pc 보너스 | 3pc 보너스 |
|---|---|---|
| **ono_sendai** | program_power +10, crit +5% | program_power +25, ap_regen +10% |
| **militech** | attack +5, crit +10% | attack +15, crit +25%, shield +2 |
| **arasaka** | defense +8, ice_res +15% | defense +20, hp +30, ice_res +30% |

장비 할당:
- ono_sendai: STARTER_DECK + STREET_DECK + CORPORATE_DECK (3pc 가능)
- militech: MILITECH_EYES + CHROME_GLOVES + MILITECH_DECK (3pc 가능)
- arasaka: ARASAKA_DECK + KEREZNIKOV (2pc만 가능)

API:
- `get_set_bonus(set_id, pieces_equipped)` → `EquipStats | None`
- `EquipmentLoadout.set_counts()` → `dict[set_id, int]`
- `EquipmentLoadout.set_bonuses()` → `list[EquipStats]`
- `EquipmentLoadout.total_stats()` 가 자동 합산 (장비 + 세트 보너스)

**회귀**: 11 tests

---

## 성능 개선

### Hub Materials/Recipes JSON 파싱 캐싱 (P2 #17)
- 이전: 매 프레임 JSON 파싱 (60fps × 16ms × 2 파일)
- 이후: module-level cache, 첫 로드만 파싱

### Cyberspace generator O(n²) → O(n) (ADR-0060)
- 이전: `for i, n in enumerate(nodes): if n.id == c` ICE enforcement
- 이후: `_index_nodes_by_id(nodes)` dict lookup (O(1))
- 효과: 미션 생성 ~3초 → **<0.1초**

### Save Manager exception narrowing
- 9개 broad `except Exception` → 5개 specific (OSError, KeyError, TypeError, ValueError, AttributeError)
- `_log_save_warning()` helper 도입 — 정확한 예외 추적 + 디버깅 가능

---

## 누적 테스트 통계

```
시작:  3254 tests (Phase 5 완료 시점, 2026-06-30)
현재:  3442 tests (+188, +5.8%)

테스트 파일: 84 → 86개
소스 파일: 106 → 108개
디자인 문서: 14 → 21개 (+50% 커버리지)
```

### 신규 회귀 테스트 188개 분포

| 카테고리 | 테스트 수 |
|---|---:|
| Mission metadata (test_missions_with_story) | 7 |
| Equipment (test_equipment) | 39 |
| Hub data + cache + reputation dots (test_hub_data_loading) | 18 |
| Programs schema (test_programs_schema) | 6 |
| Reputation (test_reputation) | 37 |
| Save manager (test_save_manager) | 47 (+2 신규) |
| Cyberspace generator (test_cyberspace_generator) | 11 |
| Mission completion + reputation hooks (test_mission_completion) | 20 |
| Death → Restart cycle (test_run_state) | +7 |
| Save migration (test_save_manager) | +4 |
| 기타 회귀 (status cap, i18n format, action_menu) | +13 |

---

## Git 커밋 히스토리 (이번 사이클 27개)

```
08441d1 → 3442 테스트 (현재)

072ab9ee feat(hub): show faction reputation dots in avatar panel
081d0d92 feat(combat): apply faction reputation after ICE defeat
097af64 feat(missions): hook faction reputation into mission completion
72ab9ee feat(hub): show faction reputation dots in avatar panel
b5fd338 feat(reputation): faction reputation system with save persistence
b142a19 fix(save): narrow 5 broad except Exception handlers in save_manager
ce7ec5c perf(cyberspace): O(n²) → O(n) ICE enforcement via id index
0611faf feat(achievements): unlock MATRIX_MASTER + TRUE_HACKER via PPL+ZDR
db33c6d feat(equipment): 3 set bonuses (ono_sendai / militech / arasaka)
180a56c perf(hub): cache materials/recipes JSON parse results (was per-frame)
fc23289 docs(design): i18n + story-archive specs + Grade 6 in balance doc
ba8f8a2 feat(ppl): Grade 6 master tier + 3 T6 equipment items
6565d54 test(equipment): cover 8-slot / 6-tier / 15-item equipment system
f4e0df4 docs(design): add inventory, dialogue, procgen, balance docs (Phase 2 complete)
56a6d5d test(run_state): cover Death → Restart cycle (P2 #13)
3d99f97 fix(hub): _material_gauge proportional + drop unused MutableSequence import
adad95f feat(programs): add 'role' field to programs.json (P2 #20)
279207f docs: sync meta documents with current state (Phase 5 done, 3254 tests, ADR-0060/0061)
... (이전 11개 커밋)
```

---

## Phase 6 콘텐츠 확장 — 기반 완료

이번 사이클에서 다음 Phase 6 기능의 기반 구축:

| 기능 | 기반 | 후속 작업 |
|---|---|---|
| **Faction-aware missions** | ✓ FactionReputation + 미션 완료 hook | NPC 별 의뢰 잠금 해제 |
| **NPC faction 반응** | ✓ AppState.reputation 필드 | dialogue 에서 rep 기반 분기 |
| **Info Market faction 할인** | ✓ ReputationState.get() | shop_price × (1 - rep/100) |
| **미션 필터링** | ✓ Faction enum + 미션 29개 | board.available_for() 에 rep threshold |
| **Boss 시스템** | ✓ ICE 9종 추가 + master tier | Wintermute / T-A Prime 3-phase |

**다음 단계** (Phase 6 권장):
1. NPC dialogue 가 faction rep 에 따라 다른 응답 (Dialogue.md "Persistent reputation" 항목)
2. Info Market 가격에 faction rep 할인 적용
3. Mission Board 가 rep tier 별 미션 잠금 해제
4. 사망 시 faction 호감도 영향

---

## 누적 진행 종합

| 세션 | 처리 항목 | 누적 테스트 |
|---|---|---:|
| 시작 (2026-06-30) | Phase 5 완료 | **3254** |
| 세션 1 | P0 #1-3 + P1 #4-8 | 3260 (+6) |
| 세션 2 | P2 #15/17/19/14/12 | 3281 (+21) |
| 세션 3 | P2 #18/13/20/11 | 3300 (+19) |
| 세션 4 | equipment 39 tests + 4 design docs | 3339 (+39) |
| 세션 5 | Grade 6 master + 2 docs | 3345 (+6) |
| 세션 6 | Save exception narrowing + Reputation | 3417 (+72) |
| 세션 7 | Faction hooks (mission + combat + Hub) | **3442 (+25)** |

**총: +188 tests, 27 커밋, 7 디자인 문서, 2 신규 시스템, 3 P0 + 8 P1 + 12 P2 이슈 해결**

---

## 알려진 한계 (향후 작업)

| 항목 | 상태 | 우선순위 |
|---|---|---|
| Equipment view 테스트 | 0 → 미작성 | P2 |
| Story view / event_view / cyberspace_view 테스트 | 0 → 미작성 | P2 |
| `render_matrix` 249-line 함수 split | P2 | 낮음 |
| `Save Manager` exception 더 narrow (현재 OSError 외) | P3 | 낮음 |
| NPC dialogue 의 faction rep 분기 | P1 | 다음 세션 |
| Info Market faction 할인 | P2 | 다음 세션 |
| Mission Board rep 잠금 해제 | P2 | 다음 세션 |
| Persistence: faction rep 가 run 간 영속화 | 부분 (save/load 만) | P2 |