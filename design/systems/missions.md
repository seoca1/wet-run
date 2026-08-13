# System: Missions (미션 시스템 — 재료 연계)

> **상위 결정**: `../../decisions/0017-mission-material-integration.md` (Accepted, Draft), `../../decisions/0010-i18n-content-pipeline.md` (Accepted), `../../decisions/0013-story-events.md` (Accepted), `../../decisions/0015-crafting-system.md` (Accepted)
> **관련**: ADR-0006 (Run), ADR-0009 (Story), ADR-0014 (Data Salvage), ADR-0016 (Avatar)

## 목적

미션이 단순 *데이터 추출*이 아니라 *재료 수집/전달/제작*의 *안내*가 됨. 한 런 = 한 미션의 *수행 + 보상* 사이클. Pillar 4 (The Build)의 *직접적* 표현.

> **Hub 통합 (ADR-0017)**: Hub 화면이 *도형적*으로 표시. Avatar + Materials + Recipes + Job Board + Info Market.

## Mission Types

6가지 미션 타입. *재료 연계* 강화.

| 타입 | 목표 | 보상 |
| --- | --- | --- |
| `extract_data` | 데이터 노드 추출 | data_fragment + credits |
| **`collect_material`** | **특정 재료 N개 수집** | **credits + 추가 재료** |
| **`deliver_material`** | **픽서에게 재료 N개 전달** | **credits + unlock** |
| **`craft_item`** | **특정 아이템/프로그램 제작** | **credits + tier upgrade** |
| `hunt` | 적 N개 처치 | ice_shard + credits |
| `salvage` | 격파 후 부품 회수 | combat_module 등 + credits |

### 미션 예시

**Arc 1 — First Jack (튜토리얼)**:
- primary: `extract_data` — Sense/Net demo 파일 추출
- secondary: `defeat` — ICE 1개 격파
- reward: credits 500, data_fragment × 2

**Arc 1 — Ice Run (수집형)**:
- primary: `collect_material` — ice_shard × 5
- secondary: `defeat` — ICE 2개 격파
- reward: credits 500, data_fragment × 2

**Arc 1 — Delivery to Finn (전달형)**:
- primary: `deliver_material` — data_fragment × 3
- secondary: `extract_data` — 1개 데이터 노드
- reward: credits 800, upgrade_t1 × 1 (tier upgrade)

**Arc 2 — Craft Job (제작형)**:
- primary: `craft_item` — T1 Program 1개 제작
- secondary: `collect_material` — combat_module × 1
- reward: credits 1000, upgrade_t2 × 1

## Mission Data Structure

`data/missions/missions.json` 확장.

```json
{
  "ice_run": {
    "id": "ice_run",
    "title": "Ice Run",
    "fixer": "finn",
    "arc": 1,
    "grade_min": 1,
    "grade_max": 1,
    "primary_objective": {
      "type": "collect_material",
      "material": "ice_shard",
      "count": 5
    },
    "secondary_objectives": [
      {
        "type": "defeat",
        "enemy": "ice.standard",
        "count": 2
      }
    ],
    "rewards": {
      "credits": 500,
      "materials": {
        "data_fragment": 2
      }
    }
  }
}
```

## Visual Hub Menu (도형적)

Hub 화면 4-패널. *한눈에* 모든 정보.

```
═══════════════════════════════════════════════════════
  HUB: Cyberspace Construct
═══════════════════════════════════════════════════════
  [Avatar]  ◉P◉    PPL: 25  Grade: 1-up
            /|\
   ★W★:H:|P:
   ║DK7║

─────────────────────────────────────────────────────
  [Materials]              [Recipes]
  ICE Shard      ▓▓▓░░ 3/5    T1 Program  ·W·  READY ✓
  Data Fragment  ▓▓░░░ 2/4    T2 Program  :H:  need 1×mod
  ROM Echo       ▓░░░░ 1/3    T3 Program  |G|  need 5×mod
  Wetware Chip   ░░░░░ 0/2    T4 Program  ▓W▓  need 9×mod
  Biosoft Agent  ░░░░░ 0/1    T5 (Kraken) ★K★  need 14×mod

─────────────────────────────────────────────────────
  [Job Board]               [Info Market]
  > [1] Ice Run              T1 Program    100 cr
      collect 5 ice shards   T2 Program    300 cr
      reward: 500 cr         T3 Program    800 cr
    [2] Delivery to Finn     T4 Program   2000 cr
      deliver 3 fragments    T5 (Kraken)  N/A
      reward: 800 cr

─────────────────────────────────────────────────────
  [1-9] Job  [C] Craft  [M] Market  [ESC] Jack out
═══════════════════════════════════════════════════════
```

### Panel 1: Avatar (ADR-0016)

- 자키의 5-7행 스틱 피규어
- PPL, Grade 표시

### Panel 2: Materials (도형적)

- 각 재료 *5칸 게이지*: `▓` (have) / `░` (need)
- 카운트 표시: `3/5` (have/need)
- 색상: `▓` = 흰색, `░` = 회색

### Panel 3: Recipes (도형적)

- T1~T5 Program tree
- READY ✓ 표시 (충분한 재료)
- need N×mod 표시 (부족)

### Panel 4: Job Board + Market

- 의뢰 목록 (재료 수집/전달 명시)
- Info Market 가격 (T1~T4, T5 = N/A)

## Recipe Tree View (Crafting)

Crafting 메뉴 진입 시 *트리*로 시각화.

```
T5 Program: Kraken ★K★
═══════════════════════════════════════════════════════
                    ┌──────────────┐
                    │   Kraken     │
                    │   ★K★  T5    │
                    └──────┬───────┘
                           │
                  ┌────────┴────────┐
                  │                 │
            5× Combat Module    1× upgrade_t5
                  │
        ┌─────────┴─────────┐
        │                   │
  2× ICE Shard       1× Data Fragment
        │                   │
   [▓▓▓░░ 3/2]      [▓░░░░ 1/1]
   READY ✓           READY ✓
═══════════════════════════════════════════════════════
```

`[▓▓▓░░ 3/2]` 표기: filled/empty + count. `READY ✓`는 모두 충족.

## Mission 진행 추적

미션 중 (Matrix 화면) HUD에 진행도 표시.

```
Current: First Jack
[=========>         ] 3/5 ice_shard
[=>                  ] 1/2 ICE defeated
```

*5칸 게이지* + 카운트. 충족 시 *체크* 또는 *색상 변화*.

## Material Drop 표시 (Combat / Node)

전투 승리 또는 노드 추출 시 *드롭* 시각화.

```
═══════════════════════════════════════════════════════
  ICE 격파 — Data Salvage
═══════════════════════════════════════════════════════
  Drop:
  ICE Shard        +1  [▓▓▓░░]  3/5
  Data Fragment    +1  [▓░░░░]  1/4

  > HEAL    +20% HP (T1 = +20)
    SKIP    no reward
═══════════════════════════════════════════════════════
```

## Mission Complete 보상

미션 성공 시 Hub 복귀 + 보상 표시.

```
═══════════════════════════════════════════════════════
  ✓ MISSION COMPLETE
═══════════════════════════════════════════════════════
  Ice Run — collect 5 ice shards
  Completed in 4 minutes 12 seconds

  Rewards:
  Credits        +500
  Data Fragment  +2

  Updated materials:
  ICE Shard      [▓▓▓▓▓]  5/5 ← objective met
  Data Fragment  [▓▓░░░]  4/4

  Grade progress: 1-up (0/3 missions)
═══════════════════════════════════════════════════════
```

## 데이터 구조

### `data/missions/missions.json`

```json
{
  "first_jack": {
    "id": "first_jack",
    "title": "First Jack",
    "fixer": "finn",
    "arc": 1,
    "grade_min": 1,
    "grade_max": 1,
    "primary_objective": {
      "type": "extract_data",
      "data_id": "demo_file"
    },
    "secondary_objectives": [
      {
        "type": "defeat",
        "enemy": "ice.standard",
        "count": 1
      }
    ],
    "rewards": {
      "credits": 500,
      "materials": {
        "data_fragment": 2
      }
    }
  }
}
```

### `data/missions/objectives.json` (선택)

미션 진행 중 *추적* 로직.

## Pillar 정합

- **P1 (The Run)**: 미션 = 한 런의 *목표*와 *보상* 안내.
- **P2 (The Matrix)**: 재료 = 매트릭스 안의 데이터.
- **P3 (The Flatline)**: 자키 사망 = 미션 실패, 재료 손실 (Pillar 3 + ADR-0015).
- **P4 (The Build)**: 미션 = *재료 수집의 안내*. 가장 직접적 표현.
- **P5 (The Style)**: 깁슨 톤, 픽서 construct의 *의뢰 briefing*.

## 구현 가이드 (Phase 6+)

### `missions/mission.py` 확장

```python
@dataclass(frozen=True, slots=True)
class Objective:
    type: str  # "collect_material", "deliver_material", "extract_data", "defeat", "craft_item"
    material: str | None = None
    enemy: str | None = None
    count: int = 1
    data_id: str | None = None

@dataclass(frozen=True, slots=True)
class Rewards:
    credits: int
    materials: dict[str, int]  # material_id -> count

@dataclass(frozen=True, slots=True)
class Mission:
    id: str
    title: str
    fixer: str
    arc: int
    grade_min: int
    grade_max: int
    primary_objective: Objective
    secondary_objectives: tuple[Objective, ...]
    rewards: Rewards
    matrix_seed: int
    zone: ZoneDepth
```

### `engine/hub.py` 확장

- 4-패널 Hub (Avatar, Materials, Recipes, Job Board, Market)
- Recipe tree view (`engine/crafting_view.py`)
- Material drop display

## Phase 범위

### Phase 5 (현재)

- **데이터 + 문서만**: 미션 JSON 확장, design 명세, test cases

### Phase 6+

- Hub 4-패널 UI
- Recipe 트리 뷰
- Mission 진행 추적
- Material drop 시각화
- Mission complete 보상 표시

## 향후 결정

- 미션 진행도 표시 (목표 N/M 게이지)
- 미션 실패 조건 (시간 초과? 등)
- Recipe 트리 깊이 제한
- Material drop 확률
- Mission unlock 트리
- Secondary objective의 *보상 기여*

## 관련 문서

- `decisions/0017-mission-material-integration.md` — ADR
- `decisions/0010-i18n-content-pipeline.md` — i18n
- `decisions/0013-story-events.md` — Events
- `decisions/0015-crafting-system.md` — Crafting
- `decisions/0016-jockey-avatar.md` — Avatar
- `decisions/0060-dungeon-exploration-redesign.md` — Dungeon (Phase 1-2)
- `decisions/0061-novel-integration-architecture.md` — Novel (Phase 5)
- `design/systems/crafting.md` — Crafting 상세
- `design/systems/avatar.md` — Avatar 상세
- `testcases/systems/mission-material.md` — TC-MISMAT 시나리오

---

## Phase 3 확장 (ADR-0060) — Mission → Room 매핑

Phase 3 (ADR-0060 의 Phase 3 부분) 는 `data/missions/missions.json` 의
각 미션을 **RoomType 시퀀스** 로 변환합니다.

### 함수

```python
from roguelike_sprawl.matrix.mission_mapper import (
    missions_to_rooms, mission_to_graph,
)
from roguelike_sprawl.missions import JobBoard

board = JobBoard.load("data/missions/missions.json")
missions = tuple(board._missions.values())  # 16 entries (canonical)

# 개별 미션 → RoomType 리스트 (5..9 entries)
rooms = missions_to_rooms(missions[0], character_ref="veteran")
# → [ENTRY, NPC, DATA, ICE, ROUTER, EXIT] 같은 시퀀스

# 개별 미션 → MatrixGraph (BSP 와 통합)
graph = mission_to_graph(missions[0], character_ref="veteran")
# → 6-12 노드 + Kruskal MST
```

### 캐릭터별 편향

`character_ref` 는 NPC / ICE / ROUTER 의 추가 분배를 결정:

| `character_ref` | NPC | ICE | ROUTER |
|---|---|---|---|
| `"novice"` | +2 | +0 | +2 |
| `"veteran"` | +1 | +1 | +1 |
| `"heretic"` | +0 | +2 | +0 |

### Arc 타겟

`mission.arc` (1-3) 별 시퀀스 길이:

| Arc | 최소 | 최대 |
|---|---|---|
| 1 (novice) | 5 | 6 |
| 2 (veteran) | 6 | 7 |
| 3 (heretic) | 7 | 9 |

키워드 추출 (objective 텍스트) → `DATA` / `ICE` / `NPC` 룸 우선 배치,
부족분은 `ROUTER` 로 패딩.

**관련 데모**:
```bash
PYTHONPATH=src .venv/bin/python scripts/play_mission_mapping.py
```

---

## Phase 11 확장 (ADR-0188) — Mission Type Expansion

Phase 11 introduces 5 new mission types + mission chains. All extensions are **additive** (existing 111 missions unchanged).

### New Mission Types

See `mission-types.md` for full taxonomy. Summary:

| 타입 | 메카닉 | 조건 | 보상 |
| --- | --- | --- | --- |
| `investigation_complete` | 다단계 증거 수집 (no combat) | scan/decrypt programs | CRED + reputation + program |
| `survive_n_waves` | N waves 방어 + NPC 보호 | shield/defense programs | CRED + programs + meta |
| `extraction_AND_defeat` | 동시 2 objective | multi-task capability | CRED × 2 + combo bonus |
| `extract_data` (high-risk variant) | 시간 제한 (120s) + construct_loss | T3+ programs | CRED × 3 + T5 program |
| `reach_target_AND_extract_data` | stealth only (no combat) | cloak/decrypt programs | CRED + cloaking_program |

### Mission Chains (ADR-0188, mission-chains.md)

8 chains of 3-5 missions each. Unlock mid-game, unique rewards, higher stakes.

**ta_succession chain** (sample, 5 missions):
1. `ta_investigate_3jane_initiative` (investigation) — intro
2. `ta_defend_straylight_perimeter` (defense) — escalation (midpoint save)
3. `ta_dual_objective_ashpool_vote` (dual-objective) — climax
4. `ta_extract_aleph_chip` (extraction_v2) — revelation
5. `ta_stealth_construct_chamber` (stealth) — resolution

Chain reward: `ta_construct_full` + reputation +25 + 50000 credits + achievement `succession_complete`.

### Zone Distribution (Post-Phase 11 Target)

| Zone | Phase 10 | Phase 11 Target | Delta |
|---|---|---|---|
| surface | 32 | 35+ | +3 |
| mid | 11 | 35+ | +24 |
| deep | 36 | 36 | 0 |
| core | 12 | 30+ | +18 |
| ta | 8 (now 13) | 35+ | +22 |
| freeside | 7 | 30+ | +23 |
| tokyo (Bridge) | 3 | 10+ | +7 |
| soho (Blue Ant) | 2 | 10+ | +8 |

**Current state (2026-08-08)**: 116 missions (was 111), TA zone: 13 (was 8). Phase 11 in progress.

### 데이터 스키마 확장

`Mission` dataclass added fields:
- `is_chain_mission: bool` — chain participation flag
- `chain_id: str | None` — chain identifier
- `chain_order: int | None` — position in chain

`Objective` dataclass added fields:
- Investigation: `evidence_required`, `evidence_types`
- Defense: `wave_count`, `wave_intensity`, `must_survive`, `node_hp_min`
- Dual-objective: `extract_spec`, `defeat_spec`, `time_limit_seconds`, `objective_lock`
- Extraction_v2: `time_limit_seconds`, `penalty_on_failure`
- Stealth: `detection_threshold`, `no_combat_allowed`, `target_id`, `alert_max`, `logging_max`

`MissionChain` dataclass (new):
- `chain_id`, `chain_name`, `chain_type`, `chain_arc`
- `unlock_condition`, `missions`, `chain_reward`, `chain_failure`
- `chain_midpoint_save`, `chain_estimated_time_minutes`

### 상호 운용성 (Interoperability)

- **기존 111 missions**: 0 변경, 그대로 작동
- **신규 5 missions**: TA zone, chain 통합 (ta_succession)
- **확장 5+ types**: `investigation_*, defeat_*, dual_*, extraction_v2, stealth_*`
- **체인**: 1 chain (ta_succession) + 7 plans (faction 3 + character 3 + story 2)

### 검증

- `make test`: 33 passed (10 legacy + 23 new = 100%)
- `make lint`: ruff check clean
- `make typecheck`: mypy strict 0 errors
- Schema: additive, no breaking changes

---

## Phase 16-17 확장 — Random Rules Engine + UI Wiring

Phase 11 의 19 random selection rules 가 **실제 게임 흐름**에 통합되었다.

### Engine Wiring (Phase 16)

`JobBoard.select_weighted(state)` 가 Round 4 에서 정의되었으나 호출되지 않던 상태였다. Phase 16 에서 Hub 진입 흐름에 wired:

- **Hub ENTER (no mission in flight)**: `engine/hub.py::handle_hub_input` 이 `ENTER` 키를 받으면 `JobBoard.select_weighted(state)` 호출 → 추천 의뢰의 cursor 위치로 점프. 결과적으로 reputation / NG+ / chain unlock 상태를 반영한 *bias* 가 적용된 cursor 이동.
- **Number-key fallback**: 의뢰 범위 밖 숫자 입력 시 `select_weighted` 가 모든 available mission 에 대해 weighted pick → 결과 미션으로 cursor 이동.
- **상태 기록**: 발동된 rule 의 ID 가 `state.last_rule_id: str` 에 저장 (UI 표시용).

### UI Display (Phase 17)

Hub Mission Details side panel 이 `state.last_rule_id` 를 읽어 다음과 같이 표시:

```
──────────────────────────────────────────────────────
  Mission Details
──────────────────────────────────────────────────────
  Ice Run
  Zone: SURFACE  Grade: 1-up  PPL: 12 vs ZDR 8
  Status: MATCH (1.5x)
  
  Objective: collect 5 ice shards
  
  Rule: surface_grade1_finn_bias   ← random rule 주석 (Phase 17)
  
  Reward: 500 credits, 2× data_fragment
──────────────────────────────────────────────────────
```

**디버그용 active rules listing**: `_append_active_rules` 헬퍼가 Hub 화면 푸터에 현재 발동 가능한 모든 rule 을 한 줄씩 표시 (개발자 + alpha tester 용). 일반 사용자에게는 off.

### Pillar 정합

- **P1 (The Run)**: 한 런 = 한 미션의 무게 유지. Random rules 는 *어떤 미션을 추천할지* 만 결정 — 미션 결과에는 영향 없음.
- **P4 (The Build)**: 메타 진행 (reputation, NG+) 의 *soft* 반영. 자키 등급 / unlock 상태가 자연스럽게 Hub 추천에 반영.
- **P5 (The Style)**: rule ID 의 깁슨 어휘 — `surface_grade1_finn_bias`, `faction_rep_yakuza_locked`, `ng_plus_chain_unlock` 등. 픽서 construct 의 *직관적 추천*.

### 테스트 커버리지

- `tests/unit/test_phase16_random_rules_engine_integration.py` (7 tests) — Hub ENTER / number-key fallback 이 `select_weighted` 호출, 가중치 차이가 cursor 에 반영
- `tests/unit/test_random_rules_ui.py` (256 LOC) — Hub side panel 의 `Rule: <rule_id>` 표시, opt-in / opt-out 케이스

### 관련 문서

- `mission-types.md` — 5 new types 상세
- `mission-chains.md` — chain 메카닉
- `decisions/0188-mission-expansion.md` — ADR (Accepted)
- `testcases/missions/new-types.md` — 6 testcases
- `prototype/tests/unit/test_mission_types_v2.py` — 23 new tests
