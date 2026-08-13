# 게임 저장 데이터 구조 & 진행 현황 추적

**문서 상태**: DRAFT
**Created**: 2026-06-23
**Purpose**: 저장 구조 + 챕터 클리어 조건 검증
**Phase 19 audit (2026-08-13)**: ending_choice persistence (Phase 16, ADR-0192) + telemetry_opt_in (Phase 15, ADR-0184) + telemetry_session 직렬화 추가. CJK 잔재 청소 (Section 5의 '~映射' / Section 6의 '~的 Stage' 두 군데).

---

## 1. 저장 데이터 구조 (JSON)

```json
{
  "version": "0.1.0",
  "saved_at": "2026-06-23T...",
  "elapsed_seconds": 480,

  "run_state": {
    "current_stage": "jack_out",
    "completed_stages": ["meet_npc", "extract_data", "defeat_ice"],
    "pending_advance": true,
    "current_target_node": "ice1",
    "last_visited_node": "data1",
    "mission_id": "first_jack",
    "started_at_ms": 0,
    "chapter_state": "IN_CHAPTER_1",
    "current_phase_index": 2
  },

  "mission": {
    "id": "first_jack",
    "title": "First Jack",
    "fixer": "finn",
    "arc": 1,
    "grade_min": 1,
    "grade_max": 1,
    "matrix_seed": 42,
    "zone": "surface",
    "rewards": {
      "credits": 500,
      "materials": {"data_fragment": 2}
    }
  },

  "app_state": {
    "character_id": "novice",
    "chapter_id": "chapter_novice",
    "inventory": {"data_fragment": 2, "ice_shard": 1},
    "credits": 500,
    "current_node_id": "data1",
    "defeated_nodes": ["ice1"],
    "extracted_nodes": ["data1"],
    "mission_progress": {"extract_data": 1, "defeat": 1},
    "player_grade": 1,
    "matrix": { ... }
  },

  "metadata": {
    "player_grade": 1,
    "screen": "matrix",
    "credits": 500,
    "data_recovered": 2,
    "ending_choice": "A",
    "telemetry_opt_in": false,
    "deck_size": "standard",
    "telemetry_session": {
      "session_id": "uuid-v4",
      "events": [],
      "opt_in": false
    }
  }
}
```

---

## 2. 주요 필드 설명

### run_state (진행 상태)

| 필드 | 타입 | 설명 | 챕터 진행 |
|------|------|------|-----------|
| `current_stage` | Stage enum | 현재 스테이지 | MEET_NPC → EXTRACT_DATA → DEFEAT_ICE → JACK_OUT → REWARD → DEBRIEF → COMPLETE |
| `completed_stages` | list[Stage] | 완료된 스테이지들 | 클리어 조건과 직접 연관 |
| `chapter_state` | ChapterState enum | 챕터 진행 상태 | PROLOGUE → IN_CHAPTER_1 → CHAPTER_1_COMPLETE → ... → ENDING_A/B/C |
| `current_phase_index` | int | 현재 Phase 인덱스 | 0~4 (케이 Ch1의 경우 WAIT→BRIEFING→JACK_IN→EXTRACT→DEBRIEF) |
| `mission_id` | str | 현재 미션 ID | 미션 선택과 연관 |
| `current_target_node` | str | 현재 타겟 노드 | 매트릭스 탐색과 연관 |
| `last_visited_node` | str | 마지막 방문 노드 | 노드 방문 추적 |

### app_state (게임 상태)

| 필드 | 타입 | 설명 | 진행 추적 |
|------|------|------|----------|
| `character_id` | str | 캐릭터 ID | novice/veteran/heretic |
| `chapter_id` | str | 챕터 ID | chapter_novice 등 |
| `inventory` | dict | 인벤토리 | 아이템 획득 추적 |
| `credits` | int | 크레딧 | 화폐/보상 추적 |
| `defeated_nodes` | set[str] | 격파한 노드 | 전투 진행 추적 |
| `extracted_nodes` | set[str] | 추출한 노드 | 데이터 추출 진행 추적 |
| `mission_progress` | dict[str,int] | 미션 진행도 | objective별 카운트 |
| `completed_missions` | set[str] | 완료된 미션들 | 반복 방지 |
| `player_grade` | int | 플레이어 등급 | 1~5, 미션 잠금 해제 |

---

## 3. 챕터 클리어 조건

### 현재 구조 (Stage 기반)

```
챕터 클리어 조건:
  - current_stage == COMPLETE
  - OR 모든 required_stages 완료
```

### 케이 Ch1 예시

```
Phase 0 (WAIT):     stage = PENDING → MEET_NPC 완료
Phase 1 (BRIEFING):  stage = MEET_NPC → NPC 대화 완료
Phase 2 (JACK_IN):  stage = MEET_NPC → MATRIX 진입 + Wisp T1 우회
Phase 3 (EXTRACT):  stage = EXTRACT_DATA → 데이터 추출 + Watchdog 격파
Phase 4 (DEBRIEF):  stage = JACK_OUT → 잭아웃 → REWARD → DEBRIEF → COMPLETE
```

### 챕터 전환 로직 (play.py)

```python
# CHAPTER_1_COMPLETE 진입 시:
if rs.chapter_state is ChapterState.CHAPTER_1_COMPLETE:
    rs.start_chapter_2()           # → IN_CHAPTER_2
    state.chapter_cutscenes_seen = set()  # 컷신 트래킹 리셋

# CHAPTER_2_COMPLETE 진입 시:
if rs.chapter_state is ChapterState.CHAPTER_2_COMPLETE:
    rs.start_chapter_3()           # → IN_CHAPTER_3
```

---

## 4. 진행 추적 메커니즘

### Stage 진행

```
RunState.current_stage:     Stage (PENDING → MEET_NPC → EXTRACT_DATA → DEFEAT_ICE → JACK_OUT → REWARD → DEBRIEF → COMPLETE)
RunState.completed_stages: tuple[Stage, ...]  (완료된 스테이지 목록)
```

### Chapter 진행

```
RunState.chapter_state:        ChapterState (PROLOGUE → IN_CHAPTER_1 → CHAPTER_1_COMPLETE → IN_CHAPTER_2 → ...)
RunState.current_phase_index:   int (0~4, 현재 Phase)
```

### 미션 진행

```
AppState.mission_progress:    dict[str, int]  (objective_type → count)
AppState.defeated_nodes:       set[str]         (격파한 ICE 노드)
AppState.extracted_nodes:      set[str]         (추출한 데이터 노드)
AppState.completed_missions:   set[str]         (완료한 미션 ID)
```

### 보상/아이템

```
AppState.credits:             int              (현재 크레딧)
AppState.inventory:            dict[str, int]   (아이템별 수량)
AppState.player_grade:         int              (1~5, 등급)
```

### Phase 16 이후 — ending_choice + telemetry_opt_in (ADR-0192 + ADR-0184)

```
AppState.ending_choice:       str              ("A" | "B" | "C" | "" — pending, ADR-0192)
AppState.telemetry_opt_in:    bool             (False default, Phase 15)
AppState.deck_size:           str              ("light" | "standard" | "heavy", ADR-0178)
AppState.telemetry_session:   TelemetrySession | None  (옵트인 사용 시, ADR-0184)
```

**저장 동작** (`engine/save_manager.py`):
- `ending_choice` (string) → `metadata["ending_choice"]` *via* `_serialize_metadata` (line 502-509, Phase 16, ADR-0192).
- `player_grade`, `screen` — 기존 Phase 5-7 era.
- `inventory`, `credits`, `current_node_id`, `defeated_nodes`, `extracted_nodes`, `mission_progress`, `reputation`, `matrix` — `_serialize_app_state` (line 471-500).
- *현 구현*: `telemetry_opt_in` / `deck_size` / `telemetry_session` 는 *metadata* 와 *app_state* 양쪽에 미저장 — **세션 ephemeral** by design (Pillar 4 ".ephemeral session preference"). 옵트인 사용자의 *세션 내* 동작만 telemetry, *cross-run* 보존은 *`ending_choice` 만*.

**복원 동작** (`engine/save_manager.py::restore_state` — line 546):
- `metadata["ending_choice"]` → `state.ending_choice` (legacy save = 빈 string default, *line 570-573*).
- 나머지 (`telemetry_opt_in` / `deck_size` / `telemetry_session`) — *fresh AppState() default* 로 fallback (각 필드의 default 값).

**마이그레이션 정책**:
- *Legacy save* (Phase 15 이전) — `ending_choice` 미저장 → default 빈 string. `telemetry_opt_in` / `deck_size` / `telemetry_session` 모두 default.
- *Phase 16+ save* — `ending_choice` 만 metadata 에 보존. *ephemeral* 필드는 각 세션 본다.

**의도적 비-저장** (Pillar 4 정합):
- `telemetry_opt_in` — 사용자가 *매 런* 명시적 결정 (Pillar 4 "ephemeral session preference").
- `deck_size` — 런 *시작* 시 결정, *across-run* 보존 불필요 (Pillar 1 "fresh run").
- `telemetry_session` — 세션 종료 시 폐기 (Pillar 5 "abstract meta").

**Cross-reference**: [`design/scenario/death-restart.md ## 6.6`](death-restart.md) — telemetry wiring + ending_choice 의 DEATH flow 통합.

---

## 5. 문제점: 챕터 vs Stage 이중 구조

### 현재 이슈

1. **Stage 시스템**: MEET_NPC → EXTRACT_DATA → DEFEAT_ICE → JACK_OUT → REWARD → DEBRIEF → COMPLETE
2. **Chapter Phase 시스템**: WAIT → BRIEFING → JACK_IN → EXTRACT → DEBRIEF

**두 시스템이 별도로 운영됨**:
- `current_stage`는 미션 기반 Stage
- `current_phase_index`는 챕터 기반 Phase
 - **두 시스템은 직접 매핑 없음**

### 검증 필요 사항

| 검증 항목 | 현재 상태 | 비고 |
|---------|---------|------|
| ChapterState → current_phase_index 동기화 | ❓ 미검증 | start_chapter_N() 호출 시 reset_phase() 실행 확인 |
| Stage → Phase 매핑 | ❓ 미검증 | phase 0이 stage PENDING과 연관되는지 |
| 챕터 완료 조건 | ❓ 미검증 | current_stage == COMPLETE이면 챕터 완료인지 |

---

## 6. 다음 검증 체크리스트

- [ ] 케이 Ch1 실행 시 `current_phase_index`가 0→1→2→3→4로 진행하는지
- [ ] 챕터 완료 시 `chapter_state`가 CHAPTER_N_COMPLETE로 전환되는지
- [ ] Phase 전환 시 `current_stage`가 예상 Stage와 일치하는지
- [ ] `reset_phase()`가 챕터 시작 시 올바르게 호출되는지

---

## 7. 관련 파일

| 파일 | 설명 |
|------|------|
| `src/roguelike_sprawl/run/state.py` | RunState, ChapterState 정의 |
| `src/roguelike_sprawl/engine/state.py` | AppState 정의 (ending_choice, telemetry_opt_in, deck_size, telemetry_session) |
| `src/roguelike_sprawl/engine/save_manager.py` | 저장/로드 로직 (_serialize_metadata, restore_state) |
| `src/roguelike_sprawl/engine/save_progress.py` | ProgressSummary 생성 |
| `src/roguelike_sprawl/combat/telemetry.py` | TelemetrySession / record_* (ADR-0184) |
| `scripts/play.py` | 챕터 전환 로직 |

---

## 8. Phase 19 Audit Trail (2026-08-13)

Phase 19 audit 결과 — Phase 15-17 사이클에서 추가된 4개 필드 (`ending_choice`, `telemetry_opt_in`, `deck_size`, `telemetry_session`) 가 metadata 직렬화에 누락되어 본 Section 2 의 JSON 예시 + Section 4 trace 에 추가.

### 추가된 섹션

- **Section 1 (JSON 예시)**: `metadata` 객체의 4개 필드 (`ending_choice`, `telemetry_opt_in`, `deck_size`, `telemetry_session`).
- **Section 4 (Phase 16 이후)**: 4개 신규 AppState 필드 + 직렬화/복원 trace + 마이그레이션 정책.
- **Section 7 (관련 파일)**: `combat/telemetry.py` 추가.

### 청소

- **CJK 잔재 청소**: Section 5 의 `~没有直接映射` → `두 시스템은 직접 매핑 없음`, Section 6 의 `~的 Stage` → `예상 Stage` (2 군데).

### 검증 위치

- `tests/unit/test_endings_persistence.py` (8 tests) — ADR-0192 round-trip.
- `tests/unit/test_telemetry_triggers.py` (21 tests) — ADR-0184 이벤트 트리거.
- `tests/unit/test_phase16_random_rules_engine_integration.py` (7 tests) — ADR-0188.

### 의도적 비-변경

- Phase 5-7 era 의 *stage vs phase 이중 구조* (Section 5) — unchanged. 현 *분석* 만 보존.
- 챕터 클리어 조건 (Section 3) — unchanged.
- `current_stage` ↔ `current_phase_index` 매핑 *미검증* 항목 (Section 5, 6) — unchanged (legacy unresolved).
