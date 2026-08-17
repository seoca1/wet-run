# System: Exploration (탐험 / Fog of War)

> **상위 결정**: `../../decisions/0020-fog-of-war-exploration.md` (Accepted, Draft)
> **관련**: ADR-0005 (Cyberspace), ADR-0011 (Portraits), ADR-0012 (PPL/ZDR), ADR-0017 (Mission)

## 목적

매트릭스 노드 그래프를 **부분 가시**로 표현. 자키는 매트릭스를 *한 번에* 보지 못하고, *한 노드씩* 발견. Pillar 5 (Style) — 깁슨의 "matrix is vast, you are small".

> **핵심**: "다 보이는데 무슨 결정?" → "한 단계씩, 모르는 것과 마주하는" 결정.

## 4단계 가시성

| Visibility | 표시 | 정보 | 색상 |
| --- | --- | --- | --- |
| `current` | 강조 박스 + `>` 마커 | 라벨, ZDR, PPL vs ZDR | 노란색 (highlight) |
| `adjacent` | 외곽선 박스 | kind (Data, ICE, Router) | 회색 |
| `discovered` | 박스 | 전체 | 흰색 (방문한 적 있음) |
| `unknown` | `?` placeholder | 없음 | 어두운 회색 |

### 가시성 결정 로직

```python
def visibility(graph, node_id) -> Visibility:
    if node_id == self.current:
        return CURRENT
    if node_id in self.discovered:
        return DISCOVERED
    if graph.is_connected(self.current, node_id):
        return ADJACENT
    return UNKNOWN
```

### 특수 노드

- **Entry 노드**: 시작 시 `discovered` (자기가 거기 있음)
- **Exit 노드**: *항상 보임* (도착해야 하므로) — ZDR은 진입 전 비공개
- **Construct 노드**: `?` (숨김) — *특정 조건* (Probe 사용, 사건 발동) 시에만 공개

## 노드 박스 렌더링

### Current (강조)

```
┌──────────┐
│  Entry   │   ← 노란색 (highlight)
│ =ZDR:1   │
└──────────┘
```

### Discovered (방문한 적 있음)

```
┌──────────┐
│  Data    │   ← 흰색
│ =ZDR:5   │
└──────────┘
```

### Adjacent (인접, 미방문)

```
┌──────────┐
│  ICE ?   │   ← 회색, kind만
│  ?       │
└──────────┘
```

### Unknown (안개)

```
┌──────────┐
│    ?     │   ← 어두운 회색
│          │
└──────────┘
```

## 미니맵 (Top-Right)

```
┌──────────────┐
│     Map      │
│  ┌─────────┐ │
│  │ ● E  ?  │ │
│  │  ?  ?  │ │
│  │   ● X  │ │
│  └─────────┘ │
│  Path: E→R₀ │
└──────────────┘
```

- `●` discovered (or current)
- `?` unknown
- `X` exit (always shown)
- 현재 위치: `●` 강조

## Breadcrumb (Bottom)

```
Path: E → R₀ → I₀   (방문한 순서, 회색)
```

## Probe Program (ADR-0003 확장)

- **T1 program**, 1 AP
- 인접 노드 1개의 **ZDR** 공개
- 사용 후 `scanned` 표시
- 인접 노드 ZDR / status (TOUGH, DEADLY, ...) 표시

### Without Probe

인접 노드: kind만 (Data, ICE, Router). ZDR/status 비공개.

### With Probe

인접 노드: kind + ZDR + status. 자키가 위험 수준 판단 가능.

## ExplorationState 데이터

```python
@dataclass
class ExplorationState:
    current: str                    # 현재 노드 ID
    discovered: set[str]            # 방문한 적 있는 노드들
    scanned: set[str]               # Probe로 정찰한 노드들
    path: list[str]                 # 방문 경로 (breadcrumb)
```

### 메서드

- `visit(node_id)`: 이동. `discovered` + `path` 갱신
- `probe(node_id)`: `scanned`에 추가
- `visibility(graph, node_id)`: Visibility 반환
- `is_visible(graph, node_id)`: bool
- `adjacent_to_current(graph)`: 현재 인접 노드 ID 목록
- `discoverable_now(graph)`: 이동 가능한 노드 ID 목록

## 연결선 (Edge) 렌더링

| 가시성 | 표시 |
| --- | --- |
| 둘 다 visible | `─` / `│` / `└` / `┘` (L-shape) |
| 한쪽만 visible | **숨김** (안개) |
| 둘 다 unknown | 숨김 |

## Phase 범위

### Phase 5 (현재)

- `ExplorationState` 모듈 구현 (순수 데이터)
- `matrix_view.py` 확장 (fog 렌더링)
- 미니맵 / breadcrumb 표시
- 단위 테스트

### Phase 6+

- Probe program의 실제 효과 (UI에서 사용)
- 미니맵 인터랙션 (확대, 클릭)
- "Scanned" 영구 표시
- 안개 해제 이벤트 (특정 construct 발견 등)

### Phase 7+

- 안개 *애니메이션* (reveal 효과, 페이드)
- 사운드 (탐험 시 whisper)

## Pillar 정합

- **P1 (The Run)**: 한 런 안의 *방랑* — 자키가 매트릭스를 *탐험*.
- **P2 (The Matrix)**: 매트릭스 안의 *데이터*를 발견 — Pillar 2 정합.
- **P3 (The Flatline)**: 안개로 인한 *불확실성* → 위험한 노드 회피의 *무게* 강화.
- **P4 (The Build)**: Probe 같은 *탐색 도구* — Pillar 4 표현.
- **P5 (The Style)**: 깁슨의 "matrix is vast, you are small" — *작고 헤매는* 자키.

## 구현 가이드 (Phase 5+)

### `matrix/exploration.py`

```python
@dataclass
class ExplorationState:
    current: str
    discovered: set[str] = field(default_factory=set)
    scanned: set[str] = field(default_factory=set)
    path: list[str] = field(default_factory=list)

    def visit(self, node_id: str) -> None: ...
    def probe(self, node_id: str) -> None: ...
    def visibility(self, graph, node_id) -> Visibility: ...
```

### `engine/matrix_view.py` 확장

```python
def render_matrix(console, t, state, layouts, exploration=None):
    if exploration is None:
        # legacy: full visibility
        ...
    else:
        # fog of war rendering
        for node in matrix.nodes:
            vis = exploration.visibility(matrix, node.id)
            if vis is Visibility.UNKNOWN:
                # skip or render `?`
                continue
            # render node with appropriate style
            ...
```

## 관련 문서

- `decisions/0020-fog-of-war-exploration.md` — ADR
- `decisions/0005-cyberspace-representation.md` — 노드 그래프
- `decisions/0003-combat-system.md` — Probe program
- `decisions/0011-ascii-portraits.md` — 박스 렌더링
- `decisions/0012-difficulty-rating.md` — ZDR/PPL
- `decisions/0060-dungeon-exploration-redesign.md` — Dungeon Mode (Phase 1-2)
- `decisions/0061-novel-integration-architecture.md` — Novel hooks (Phase 5)
- `design/systems/hacking.md` — 매트릭스
- `testcases/systems/exploration.md` — TC-EXP 시나리오

---

## Phase 1-2 확장 (ADR-0060)

Phase 1-2 (ADR-0060) 는 매트릭스 탐험에 두 가지 큰 변경을 도입했습니다.

### Phase 1 — Dungeon Mode (D 키)

`engine/state.py: AppState.dungeon_mode: bool = False` 플래그 도입.
**`D` 키** 로 매트릭스 화면에서 2-D BSP 그리드 보기로 토글.
`engine/app.py` 의 키 핸들러 + `engine/dungeon_view.py` 의
`render_dungeon_matrix()` 가 상태를 읽어 그리드를 그립니다.

토글 시 status panel 의 `WHERE` 행이 변경:

```
Screen: MATRIX              ← 기존 평면 그래프
Screen: MATRIX (DUNGEON MODE)  ← 토글 후
```

### Phase 2 — ProceduralDungeonGenerator (BSP)

`matrix/dungeon_generator.py: ProceduralDungeonGenerator` 가
**BSP (Binary Space Partitioning)** 트리로 매 런마다 다른 미로를
생성합니다:

| 파라미터 | 기본값 | 효과 |
|---|---|---|
| `min_leaf_size` | `2` | 재귀 깊이 (작을수록 방이 많음) |
| `room_padding` | `1` | 복도 통과용 보더 |
| `seed` | (필수) | RNG 시드 |
| `mission_grade` | `1` | 1-5, 그리드 크기 결정 |
| `character_ref` | `"veteran"` | dead-end 분기 + ICE/NPC 밀도 |

같은 `(seed, grade, ref)` = 동일 레이아웃 (재현 가능).

```python
from wet_run.matrix.dungeon_generator import ProceduralDungeonGenerator

gen = ProceduralDungeonGenerator(min_leaf_size=2, room_padding=1)
graph = gen.generate(seed=42, mission_grade=1, character_ref="veteran")
# 6-12 노드 + Kruskal MST 연결
```

생성된 그래프는 `state.matrix` 에 attach 되어 `dungeon_view.render_dungeon_matrix()`
가 그리드 좌표 `_get_room_position()` 으로 위치를 결정합니다.

**관련 데모**:
```bash
PYTHONPATH=src .venv/bin/python scripts/play_dungeon_mode.py
```

자세한 검증 절차: `docs/DUNGEON_*.md` (3개) + `decisions/0060-dungeon-exploration-redesign.md`.
