# ADR-0017: Mission-Material Integration (미션-재료 통합)

**상태**: Accepted (auto-converted 2026-08-05, user-confirmed)
**날짜**: 2026-06-18
**결정자**: 사용자
**우선순위**: P1
**상위 결정**: ADR-0009 (Story), ADR-0010 (i18n), ADR-0013 (Events), ADR-0014 (Data Salvage), ADR-0015 (Crafting), ADR-0016 (Avatar)

## 컨텍스트

사용자 결정 (2026-06-18):
> "미션 중에는 재료 수집 전달도 연계되면 좋겠어. 메뉴에서 레시피와 재료 현황도 동시에 보여야 하며 도형적이면 좋겠어."

요구:
- 미션과 *재료 수집/전달* 연계
- Hub 메뉴에서 *레시피* + *재료 현황* 동시 표시
- *도형적* 표현 (graphical)

기존:
- 미션 = 단순 데이터 추출/ICE 격파 (ADR-0010, story_skeleton)
- Crafting UI 미구현 (Phase 6+ 예정)
- Hub = 텍스트 의뢰 목록만

## 결정

### 1. Mission Types with Material Integration

미션의 *목표*에 재료 수집/전달을 포함. 6가지 미션 타입.

| 타입 | 목표 | 보상 |
| --- | --- | --- |
| `extract_data` | 데이터 노드 추출 | data_fragment + credits |
| **`collect_material`** | **특정 재료 N개 수집** | **credits + 추가 재료** |
| **`deliver_material`** | **픽서에게 재료 N개 전달** | **credits + unlock** |
| **`craft_item`** | **특정 아이템/프로그램 제작** | **credits + tier upgrade** |
| `hunt` | 적 N개 처치 | ice_shard + credits |
| `salvage` | 격파 후 부품 회수 | combat_module 등 + credits |

### 2. Mission Data Structure (확장)

`data/missions/missions.json`에 `secondary_objectives`와 `material_rewards` 추가.

```json
{
  "id": "ice_run",
  "title": "Ice Run",
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
```

### 3. Visual Hub Menu (도형적)

Hub 화면을 *도형적*으로 재구성. 4개 패널.

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
  ICE Shard      ▓▓▓░░ 3/5    T1 Program  ·W·
  Data Fragment  ▓▓░░░ 2/4      needs: 1×module
  ROM Echo       ▓░░░░ 1/3    T2 Program  :H:
  Wetware Chip   ░░░░░ 0/2      needs: 2×module
  Biosoft Agent  ░░░░░ 0/1    T3 Program  |G|
                                  needs: 3×module
                                  READY ✓

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

### 4. Recipe Tree View (도형적)

레시피를 *트리*로 시각화. 어떤 재료를 모아야 하는지 *한눈에*.

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

`[▓▓▓░░ 3/2]` 표기: `▓` (have) / `░` (need) + `3/2` (have/need). `READY ✓`는 모두 충족 시.

### 5. Material Drop Display (전투 / 노드)

전투 승리 또는 노드 추출 시 *드롭* 시각화.

```
═══════════════════════════════════════════════════════
  ICE 격파 — Data Salvage
═══════════════════════════════════════════════════════
  [Salvage]

  ICE Shard        +1  [▓▓▓░░]  3/5
  Data Fragment    +1  [▓░░░░]  1/4

  > HEAL    +20% HP (T1 = +20, T3 = +30)
    SKIP    no reward
═══════════════════════════════════════════════════════
```

## 결과 (Consequences)

### Pillar 정합

- **P1 (The Run)**: 미션이 *재료 수집의 목표*를 제공. 한 런 = 수집 + 조합의 사이클.
- **P2 (The Matrix)**: 재료 = 매트릭스 안의 데이터. 미션 안에서 *수집*. Pillar 2 정합.
- **P3 (The Flatline)**: 미션 실패 (자키 사망) = 수집한 재료 손실 (Pillar 3 + ADR-0015 Option A).
- **P4 (The Build)**: 미션 = 재료의 *안내*. 자키가 *어떤 도구를 모을지* 결정.
- **P5 (The Style)**: 깁슨 톤, 픽서 construct의 *의뢰 briefing*.

### 기존 ADR 영향

- **ADR-0010 (i18n)**: 미션 텍스트 i18n. 보강.
- **ADR-0013 (Events)**: Story events = 미션의 *부가 이벤트*. 보강.
- **ADR-0015 (Crafting)**: Mission types = Crafting *연결*. 보강.
- **ADR-0016 (Avatar)**: Hub에 Avatar 표시. 보강.
- **`missions/mission.py`**: `Mission` 데이터 클래스 확장.

### 디자인 영향

- **`design/systems/missions.md`** (신규) — 미션 시스템 명세
- **`design/systems/crafting.md`** 확장 — Hub 통합, 트리 뷰
- **`design/systems/avatar.md`** 확장 — Hub 표시
- **`testcases/systems/mission-material.md`** (신규) — TC-MISMAT-001~010

### 구현 영향 (Phase 6+)

- `missions/mission.py` 확장 — `primary_objective`, `secondary_objectives`, `rewards`
- `engine/hub.py` 확장 — 4-패널 Hub (Avatar, Materials, Recipes, Job Board)
- `engine/crafting_view.py` (신규) — 트리 뷰 렌더링
- `engine/animations.py` (신규) — 보너스: ASCII 애니메이션 헬퍼

### Phase 5 범위

- **데이터 + 문서만**: 미션 JSON 확장, design 명세, test cases
- **UI 없음**: Phase 6+

### Phase 6+ 범위

- Hub 4-패널 UI
- Recipe 트리 뷰
- Mission 진행 추적 (objective counter)
- Material drop 시각화 (combat + node)
- Mission complete 보상 표시

## 향후 결정

- 미션 진행도 표시 (목표 N/M)
- 미션 실패 조건 (시간 초과? 등)
- Recipe 트리 깊이 제한 (T5까지? 더 깊게?)
- Material drop 확률 (보상 곡선)
- Mission unlock 트리 (어떤 미션이 어떤 미션을 unlock?)

## 영향 받는 항목

- `design/systems/missions.md` (신규)
- `design/systems/crafting.md` (확장)
- `design/systems/avatar.md` (확장)
- `decisions/0015-crafting-system.md` (연계)
- `decisions/0016-jockey-avatar.md` (연계)
- `data/missions/missions.json` (확장)
- `testcases/systems/mission-material.md` (신규)

## 관련 결정

- ADR-0010 (Accepted) — i18n
- ADR-0013 (Accepted) — Story Events
- ADR-0014 (Accepted) — Data Salvage
- ADR-0015 (Accepted) — Crafting
- ADR-0016 (Accepted) — Jockey Avatar

## 변경 이력

- 2026-06-18: Draft 작성

### Auto-conversion Confirmation (2026-08-05)

본 ADR은 사용자 결정 (질의 응답으로 confirm, 2026-08-05)에 의해 auto-convert 완료. 증거 기반 검증 통과.

**구현 증거 (2026-08-05)**: `missions/{board,mission}.py` + `engine/mission_completion.py` + 111 미션의 `story.source`/`material` 메타데이터. 미션-재료 연결 + 4-panel Hub (Materials/Recipes/JobBoard/Avatar).

**변경 후 immutable**: 본 ADR 의 결정 사항은 변경 불가. 향후 수정 필요 시 신규 ADR 작성 (AGENTS.md §8).
