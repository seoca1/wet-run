# ADR-0215: Graph-directed matrix navigation (목표 지향 matrix 이동)

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P0 (The Matrix — 보스가 도달 불가능한 상태)
**관련**: [ADR-0060 — Dungeon Exploration Redesign](./0060-dungeon-exploration-redesign.md), [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md)

## 컨텍스트 (Context)

Property-based fuzzing (fast-check) 으로 mission matrix 를 생성해 reducer 를 돌린 결과,
**53/53 mission 어디에서도 보스(boss) 에 도달할 수 없었다.**

그런데 graph 자체는 멀쩡했다:
- **53/53 mission fully connected** — 모든 node 가 graph 안에서 서로 연결됨
- **53/53 mission 에 entry→boss path 존재** — 시작점에서 보스까지 경로가 있음

즉 **generator 가 아니라 reducer 의 navigation 규칙** 이 결함이었다.

### 결함 1 — `applyMatrixAction` 의 forward 이동

`applyMatrixAction` 은 forward 이동 시 `node.adjacent[0]` 으로 이동했다. 그리고
**모든** 생성된 mission 에서 node 0 부터의 `adjacent[0]` chain 은 **2-cycle `0 ↔ 1`** 이었다.
walker 는 up to 28 node 중 정확히 2개만 방문했고, 더 이상 progress 할 수 없었다.

### 결함 2 — `applyLootAction` 의 index 기반 진행

독립적으로 두 번째 결함이 있었다. `applyLootAction` 은 `currentNodeIndex + 1` 로 진행했는데,
이는 **ARRAY INDEX** 이지 graph adjacency 가 아니었다 — 일관되지 않은 평행 진행.
실무상 **0/53 mission 이 완료 가능**했다. loot `confirm` chain 이 node 1 에서 멈추는데
(node 1 이 ICE 를 carry), `confirm` 가 combat 으로 재진입해 버리기 때문이었다.

## 고려한 옵션

### Option 1: `adjacent[0]` fallback 유지 + dead-end 회피 (기각)

- **설명**: `adjacent[0]` 이 진행 불가일 때만 다른 neighbor 를 고른다.
- **단점**: 결함을 그대로 방치한다. `adjacent[0]` chain 이 2-cycle 인 mission 에서
  여전히 boss 에 도달하지 못한다. "가끔은 되기도 하고 안 되기도 하는" navigation 은
  플레이어 입장에서 최악의 상태다.
- **Pillar 정합**: P2 (The Matrix) — 실패.

### Option 2: index 기반 진행 유지 (`currentNodeIndex + 1`)

- **설명**: loot 경로를 forward 경로와 동일하게 index 증가로 통일.
- **단점**: adjacency 를 전혀 무시하므로 graph 구조가 무의미해진다. 어떤 mission 에서는
  boss 를 지나쳐 지나갈 수도 있다.
- **Pillar 정합**: P2 (The Matrix) — 실패.

### Option 3: **Goal-directed navigation (BFS shortest path)** (선택)

- **설명**: forward 는 `matrix.bossNode` 방향의 최단 경로, backward 는 `matrix.startNode` 방향의
  최단 경로를 따라 한 hop 씩 진행한다. 순수 helper 로 분리.
- **장점**:
  - 모든 mission / 모든 seed 에서 boss 도달 보장 (측정값 0/53 → 53/53)
  - 네 방향 의미가 "진행 / 후퇴" 로 명확히 살아남는다
  - reducer 는 순수 + 결정적 유지 (BFS neighbor 순서는 결정적 `adjacent` 배열에서 유도)
- **단점**:
  - cycle 있는 graph 에서 backward hop 은 forward hop 의 **literal inverse 가 아니다**
  - loot heal (max HP 15%) 이 재방문 node 에서 재발동 가능
- **Pillar 정합**:
  - P1 (The Run): 강화 — mission 의 목적지까지 실제로 갈 수 있게 됨
  - P2 (The Matrix): 핵심 정합 — node graph 표현이 실제로 작동
  - P4 (The Build): 신규 모듈 1개 (ADR-0110 가이드 준수)

### Option 4: graph 재설계 (연결성 강화, 새 generator)

- **설명**: generator 가 `adjacent[0]` chain 이 progress 하는 형태를 보장하도록 변경.
- **단점**: **generator 는 이미 정상이었다.** `connectAdjacent` (BSP leaf 위 Kruskal MST) +
  `addDeadEnds` (additive only) 가 연결성을 보장하고, `dungeonToMatrix` 도 올바른
  `startNode`/`bossNode` 을 보고했다. 결함이 없는 코드를 고치는 것은 scope creep 이다.
- **Pillar 정합**: P2 (The Matrix) — 불필요.

## 추천 (Recommendation)

**Option 3 (Goal-directed navigation)** — graph 가 이미 올바르므로 navigation 규칙만
바꾸는 것이 최소 diff 이면서 근본 원인(인덱스/무관한 neighbor 선택)을 제거한다.

## 사용자 결정 (Decision)

[ x ] Option 3 (Graph-directed matrix navigation) — 사용자가 명시적으로 승인,
코드는 이미 shipped 상태.

## 결과 (Consequences)

### 결정된 동작

Matrix navigation 은 **goal-directed** 로 전환한다:

- **forward** (`move_south`/`move_east`) — `MatrixNode.adjacent` 위 BFS 로 `matrix.bossNode`
  방향 최단 경로의 한 hop 전진
- **backward** (`move_north`/`move_west`) — `matrix.startNode` 방향 최단 경로의 한 hop 후퇴
- 순수 helper **`nextHopToward(matrix, from, target)`** (+ `pathLengthBetween`) 는 신규 모듈
  `web/src/core/matrix_navigation.ts` 에 위치하며, 경로가 없으면 `-1` 을 반환
- reducer 와 loot progression 모두 `-1` 을 **플레이어에게 보이는 메시지를 동반한 명시적 no-op**
  으로 처리 ("No route to the objective" / "No route back to the entry").
  **`adjacent[0]` fallback 은 의도적으로 없다** — 그 fallback 이 바로 결함이었고,
  되살리면 defect 를 조용히 재도입하게 된다
- `applyLootAction` 도 동일한 helper 로 전진하므로, walking 과 looting 이 하나의 일관된
  경로를 따라간다
- `makeInitialState` 는 `currentNodeIndex` 를 literal `0` 이 아니라 `matrix.startNode` 로 seed 한다
  (이전에는 `startNode` 가 항상 0 이었기에 우연히 같았는데, 그 동일성은 보장되지 않은
  사전순 sort 에 의존했다)
- renderer 의 `isAdjacent` 는 `index ± 1` 이 아니라 `node.adjacent.includes(i)` 로 파생한다

### Generator 는 변경하지 않음

`connectAdjacent` (BSP leaves 위 Kruskal MST) + `addDeadEnds` (additive only) 는 이미
연결성을 보장하고, `dungeonToMatrix` 는 이미 올바른 `startNode`/`bossNode` 을 보고했다.

### 같은 변경에서 함께 처리한 companion fix

`ice_x2` run mutator 가 **inert** 였다.
`baseCount = Math.min(node.iceIds.length * 2, 4)` 다음에 `node.iceIds.slice(0, baseCount)` 가
따라오는데, `slice` 는 **줄일 수만** 있고 node 는 정확히 1 개의 ice id 를 가지므로 roster 는
항상 1 이었고 multi-ICE combat 은 dead code 였다.

수정: node 의 ice id 를 cycle 시켜 `baseCount` 에 도달시킨다
(`Array.from({length: baseCount}, (_, i) => node.iceIds[i % node.iceIds.length])`) — 서로
구별되는 roster object 를 만든다. mutator 가 없으면 roster 길이는 그대로다.

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:
- `web/src/core/matrix_navigation.ts:97` — `nextHopToward` — boss/start 방향 최단 경로 한 hop (path 없으면 `-1`)
- `web/src/core/matrix_navigation.ts:117` — `pathLengthBetween` — 두 node 사이 최단 경로 길이
- `web/src/core/state_actions_phases.ts:110` — forward 이동 (`move_south`/`move_east`) 이 `nextHopToward(matrix, currentNodeIndex, matrix.bossNode)` 사용
- `web/src/core/state_actions_phases.ts:128` — backward 이동 (`move_north`/`move_west`) 이 `nextHopToward(matrix, currentNodeIndex, matrix.startNode)` 사용
- `web/src/core/state_actions_phases.ts:217` — `applyLootAction` 이 동일한 helper 로 전진 (index+1 제거)
- `web/src/core/state_actions_phases.ts:60` — `ice_x2` roster sizing (`baseCount`) 및 id cycling 수정
- `web/src/core/state.ts:112` — `currentNodeIndex: matrix.startNode` (literal `0` 대신)
- `web/src/renderer/matrix.ts:88` — `isAdjacent` 가 `node.adjacent.includes(i)` 로 파생
- `web/tests/matrix_navigation.test.ts` — 신규 12 테스트. reducer 레벨 forward-walk 회귀 테스트는 옛 `adjacent[0]` 코드에서 **FAIL** (revert 로 검증), `ice_x2` doubling 테스트는 옛 `slice()` 코드에서 **FAIL** (revert 로 검증)
- 측정: boss 도달 **0/53 → 53/53**, mean start→boss walk **17.57 → 3.58 hops**, max **34 → 6**
- `scripts/balance_sim.ts:115` — balance harness 는 ICE node 로 직행하고 combat 만 측정 (walk 하지 않음) → `npm run balance` 출력이 before/after **byte-identical**, per-grade win-rate band 영향 없음

**Notes**: `slotToGameState` 는 `SaveSlot` 이 matrix position 을 persist 하지 않아 여전히
`currentNodeIndex: 0` 을 복원한다 (mid-matrix save/restore 미해결). `buildMatrix` 의 linear
5-node variant 는 unit test 용으로 남겨두었으나 shipped game path 에서는 쓰이지 않는다.

## 영향 받는 항목

- `web/src/core/matrix_navigation.ts` — 신규 모듈 (goal-directed navigation helper)
- `web/src/core/state_actions_phases.ts` — forward/backward 이동, loot 진행, `ice_x2` roster
- `web/src/core/state.ts` — `makeInitialState` 의 `currentNodeIndex` seed
- `web/src/renderer/matrix.ts` — `isAdjacent` 파생 방식
- `web/tests/matrix_navigation.test.ts` — 신규 회귀 테스트 (12개)
- `web/src/core/matrix.ts`, `web/src/core/dungeon.ts` — generator 는 변경 없음 (확인만)

## 관련 결정

- ADR-0060 (Dungeon Exploration Redesign) — dungeon→Matrix adapter, `startNode`/`bossNode` 출처
- ADR-0110 (모듈 사이즈 정책) — 신규 모듈은 이 가이드를 따른다 (ADR-0110 §결과, web TypeScript 평균 100-300 LOC)
- ADR-0210 (Combat VFX Effect Schema)
- ADR-0211 (ICE 난이도 스케일링)
- ADR-0212 (grade 기반 ICE encounter 배선)

## 변경 이력

- 2026-10-27: Draft 작성 + Accepted (Option 3, Graph-directed matrix navigation) — 코드 shipped 상태
