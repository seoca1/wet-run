# System: Cyberspace / Hacking (사이버스페이스 / 해킹)

> **상위 결정**: `../../decisions/0005-cyberspace-representation.md` (Accepted)
> **관련**: ADR-0003 (RT-MS), ADR-0008 (Item Tier), ADR-0009 (Story), ADR-0011 (Portraits), ADR-0012 (PPL/ZDR), ADR-0013 (Events)

## 목적

매트릭스(사이버스페이스)를 게임 안에서 **노드 그래프**로 표현. 플레이어는 노드 사이를 이동하며 데이터, ICE, construct, 출구를 탐색한다. Pillar 2 (The Matrix)와 Pillar 5 (The Style)를 모두 만족.

> **Pillar 2 (강화, ADR-0009)**: 매트릭스가 *유일한* 시각적 공간. Hub / 픽서 대화 / 의뢰 briefing 모두 매트릭스 안의 텍스트 인터페이스로 표현됨. meatspace는 절대 시각화 X.

## 매트릭스 구조

### 노드 (Node)

매트릭스의 한 지점. 종류에 따라 행동 / 보상 / 위험이 다름.

| Kind | ID 컨벤션 | 설명 | ZDR 추가 |
| --- | --- | --- | --- |
| `entry` | `E_*` | 진입점 (의뢰 시작) | base |
| `exit` | `X_*` | 탈출점 (의뢰 종료) | base |
| `router` | `R_*` | 분기점, 데이터 흐름 | base |
| `data` | `D_*` | 데이터 노드 (탈취 가능) | base |
| `system` | `S_*` | 시스템 노드 (해킹 대상) | base |
| `ice` | `I_*` | ICE 노드 (전투) | base + ice_modifier |
| `construct` | `C_*` | construct (대화) | base |
| `core` | `N_*` | 코어 노드 (깊이 끝) | base |

각 노드는 다음을 가진다:
- `id`: 고유 문자열 (예: `E_first_jack`)
- `kind`: `NodeKind`
- `label`: 표시 이름 (예: "Entry", "Sense/Net Router")
- `zone`: `ZoneDepth` (surface / mid / core / ta)
- `ice`: `IceKind` (none / standard / watchdog / black)
- `alarm`: `AlarmLevel` (low / medium / high / critical)
- `faction`: `Faction` (none / hosaka / maas / sense_net / ta)

### 간선 (Edge)

노드 사이의 연결. 한 방향이거나 양방향. 그래프는 **DAG** (방향성 비순환) — 더 깊은 노드로만 진행.

```
@dataclass(frozen=True, slots=True)
class Edge:
    src: str  # source node id
    dst: str  # destination node id
```

### 그래프 (MatrixGraph)

```
@dataclass(frozen=True, slots=True)
class MatrixGraph:
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    entry_id: str  # 시작점
```

API:
- `get(node_id) -> Node | None`
- `neighbors(node_id) -> list[Node]` — 인접한 노드
- `is_connected(src, dst) -> bool`
- `exits() -> list[Node]` — `NodeKind.EXIT` 노드
- `count() -> int`
- `__contains__(node_id) -> bool`

## Zone & Base ZDR

매트릭스의 깊이 = 위험도.

| Zone | Base ZDR | 설명 |
| --- | --- | --- |
| `surface` | 1-3 | 진입점, 평이. 학습 구간 |
| `mid` | 4-8 | 중간 zone. 기업 일반 |
| `core` | 9-15 | 깊은 zone. 위험 |
| `ta` | 20-30 | Tessier-Ashpool Straylight |

**Base ZDR 표** (generator가 zone에서 자동 선택):

| Zone | Base 선택 |
| --- | --- |
| surface | 1 |
| mid | 5 (4-8 중) |
| core | 12 (9-15 중) |
| ta | 25 (20-30 중) |

## ICE & Alarm & Faction Modifiers

자세한 공식은 `difficulty-rating.md` 참조. 요약:

**ICE Modifier**:
- `none`: +0
- `standard`: +2 (per ICE)
- `watchdog`: +1
- `black`: +10

**Alarm Modifier**:
- `low`: +0
- `medium`: +3
- `high`: +5
- `critical`: +10

**Faction Modifier**:
- `none` / 기타: +0
- `hosaka`: +2
- `maas`: +3
- `sense_net`: +4
- `ta`: +5

## ZDR 계산

```
ZDR = base_zone + ice_modifier + alarm_modifier + faction_modifier
```

`difficulty-rating.md` 의 `calculate_zdr(node)` 함수 사용.

## PPL (Player Power Level)

런 시작 시 loadout에서 계산. 자세한 것은 `difficulty-rating.md`.

```
PPL = (deck_tier * 3) + sum(program_tier) * 2 + wetware_tier + (construct_tier * 3 if construct else 0)
```

## Status (PPL vs ZDR)

| Ratio (PPL / ZDR) | Status | 색상 | 의미 |
| --- | --- | --- | --- |
| > 1.5 | SAFE | green | 압도적 우위 |
| 1.0 - 1.5 | MATCH | cyan | 균등 |
| 0.75 - 1.0 | TOUGH | yellow | 불리 |
| 0.5 - 0.75 | DEADLY | red | 매우 위험 |
| < 0.5 | FUTILE | dark_red | 자살행위 |

**회피 메카닉 (ADR-0012, soft difficulty)**:
- ZDR 표시 → 플레이어 결정
- 경로 우회 가능
- 강제 진입 없음
- DEADLY/FUTILE 진입 시 명시적 경고

## 절차적 생성 (Phase 5: 단순)

`MatrixGenerator.generate(seed, mission_grade)`:
- seed 기반 deterministic 생성 (테스트 가능)
- mission_grade = 자키 등급 (1-5)
- 등급이 높을수록 큰 그래프 + 더 깊은 zone

### Phase 5 단순 알고리즘 (Surface 한정)

`mission_grade=1` 의 경우:
- 노드 수: 5-7
- 구조: 1 entry → 2-3 routers → 1-2 data + 1 ice → 1 exit
- 모두 `ZoneDepth.SURFACE` (base=1)
- ICE: standard 1개
- Alarm: low
- Faction: sense_net (1개만, modifier +4)

### 향후 (Phase 6+)

- Mid / Core / TA zone 생성
- 더 복잡한 그래프 (분기, backtrack)
- multiple ICE per node
- Alarm 동적 변화 (런 중)

## 그래프 레이아웃 (렌더링용)

`compute_layout(graph)`:
- BFS from entry, 각 노드의 layer (BFS 깊이) 계산
- Layer 내에서는 node id 알파벳 순으로 row 할당
- col = 2 + layer * 18 (최대 80 컬럼)
- row = 12 + index * 8 (최대 50 row)

각 노드 박스: 폭 12, 높이 4 (`+----+`, label, ZDR, decoration).

연결선: libtcod `console.print`로 `─`, `│`, `┌`, `┐`, `└`, `┘` 직접 그리기.

## 탐색 미시 루프

```
[Node 도착]
  |  ZDR 표시 + Status 색상
  |  현재 노드 라벨 + description
  v
[Player 결정]
  | - 화살표 키: 인접 노드로 이동
  | - ENTER: 노드 진입 (action menu)
  | - ESC: 잭 아웃 (Hub로 복귀)
  v
[이동 / 진입 / 잭아웃]
```

**이동 비용** (Phase 5+: ADR-0005):
- 노드 간 이동: 1 BW
- 위험 zone: trace 위험 증가
- Phase 5에서는 단순 표시 (BW 추적은 다음 세션)

## 노드 진입 (Action Menu)

Phase 5에서는 **placeholder** (combat은 미구현). 노드 진입 시:
- 데이터 노드: "extract data" (성공: 보상 추가)
- ICE 노드: "engage" (Phase 5+ RT-MS 전투)
- Exit: "jack out"
- Construct: "communicate"
- System / Router: "scan"

## Pillar 정합

- **P1 (The Run)**: 한 런 = 한 미션 = 한 매트릭스
- **P2 (The Matrix)**: 유일한 시각적 공간 — meatspace는 표시 X
- **P3 (The Flatline)**: ZDR 표시, 회피 가능
- **P4 (The Build)**: PPL = 도구 (장비 티어)
- **P5 (The Style)**: Pure ASCII, 노드 그래프 미학

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
    "objective": "Extract the demo file from Sense/Net subsidiary.",
    "matrix_seed": 42,
    "zone": "surface",
    "reward_tier": 1,
    "reward_credits": 500
  }
}
```

## 향후 결정

- 노드 그래프 생성 알고리즘 (BSP, WFC, 단순 random)
- 노드 간 이동 비용 (BW/AP)
- 깊이 시스템 수치
- 미니맵 표현 (그래프 전체 보기)
- Alarm 동적 변화 메카닉
- Trace 위험 시스템
- 다중 phase 의뢰
- Combat / Action menu (Phase 5 다음 세션)

## 관련 문서

- `decisions/0005-cyberspace-representation.md` — ADR
- `decisions/0009-story-news-system.md` — Hub 텍스트 인터페이스
- `decisions/0012-difficulty-rating.md` — PPL & ZDR
- `decisions/0011-ascii-portraits.md` — 노드 portrait
- `decisions/0013-story-events.md` — 매트릭스 이벤트
- `design/systems/difficulty-rating.md` — PPL/ZDR 상세
- `design/systems/story-events.md` — 매트릭스 이벤트
- `design/core_loop.md` — 매트릭스 미시 루프
- `design/GDD.md` — 매트릭스 게임 구조
