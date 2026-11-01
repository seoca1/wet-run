# ADR-0249: Matrix 오퍼레이션 보드 — 한 화면 기하 기반 보드, 목록은 선택 노드 상세 카드로 강등

**상태**: Accepted
**날짜**: 2026-11-01
**결정자**: 사용자 (프로젝트 오너) — 2026-11-01 종합 권고의 승자 방향 승인
**우선순위**: P2 (The Matrix — 경로·위험 결정의 표현, The Style 접점)
**관련**: [ADR-0005 — 사이버스페이스 표현](./0005-cyberspace-representation.md) · [ADR-0060 — 던전 탐색 재설계](./0060-dungeon-exploration-redesign.md) · [ADR-0103 — 던전 전용 모드](./0103-dungeon-only-mode.md) · [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md) · [ADR-0185 — 저장 마이그레이션](./0185-save-migration-v2.md) · [ADR-0195 — 구현 상태 기록](./0195-adr-implementation-workflow.md) · [ADR-0237 — UI 화면 구성·Green Grid](./0237-ui-composition-and-visual-direction.md) · [ADR-0239 — 밸런스 기준선](./0239-vfx-spawn-rng-decoupling.md) · [ADR-0246 — 던전의 역할과 런 인터랙션](./0246-dungeon-role-and-run-interaction.md) · [ADR-0247 — Manus 제2 의견](./0247-dungeon-role-supplement-manus-second-opinion.md) · [Manus 개념 패스](../../design/matrix-directions-2026-11-01/manus-concepts.md) · [Oracle 검증·종합](../../design/matrix-directions-2026-11-01/oracle-review-and-synthesis.md) · [디자인 기둥](../../design/pillars.md)

> **확정: Matrix는 한 화면의 기하 기반 오퍼레이션 보드로 그린다.** 생성기가 배치한 방 좌표에
> 방을 그리고, `@`가 현재 위치를 지속적으로 차지하며, 간선은 `MatrixNode.adjacent`만을 권위로
> 그린다. **목록은 주 상호작용에서 내려와 선택 노드 상세 카드가 된다.**
> **이것은 ADR-0246 B안(던전 = 런 전체)이 아니다. B는 계속 보류다.**
> 회로판형 ICE 결정 화면(개념 패스 안 3)은 이번 범위 밖이다.

## 컨텍스트 (Context)

- 오너는 플레이 테스트에서 Matrix 목록 구조가 읽기 어렵다고 지적했고, 목록 가독성 개선
  (`06658a12`) 뒤에 **"목록 화면 말고 아예 다른 방향으로 게임 느낌나게"** 를 요청했다.
- Manus 개념 패스와 Oracle 교차검증이 **같은 승자**(한 화면 기하 기반 보드)와 **같은 위험**
  ("던전 모양으로 꾸민 노드 목록" / "동사를 싣지 않은 표현은 ADR-0060의 실수 반복")을 지목했다.
- **지금 안전한 이유**: ADR-0246 A가 이미 결정층을 출하했다 — 인접 목적지를 화살표로 고르고
  Enter로 이동하는 경로 선택(슬라이스 1)과 PROBE / BYPASS / BREACH / JACK OUT(슬라이스 2).
  따라서 이번 공간화는 **이미 존재하는 결정을 구현화**하며, 결정 없이 공간만 바꾼 ADR-0060의
  실패를 반복하지 않는다. 반대로 반복 플레이에서 지배 경로·동사가 드러나면 보드가 구제하지
  못한다 — 그것은 여전히 결정 밀도·밸런스 문제다.
- 생성 공간은 **7×5 ~ 15×10** 이다 (`dungeon_layout.ts`의 `GRID_BY_GRADE`). 그래서 전체 위상이
  80×50 / 60×40 / 40×60 모두 한 화면에 들어간다. 카메라·스크롤은 필요 없다.
- `dungeonToMatrix`는 `Room`의 `x, y, w, h, label`을 버리고 그래프만 남겼다. 새 생성기가 아니라
  **버린 기하를 보존**하는 것이 가장 작은 변경이다.

## 사용자 결정 (Decision)

- [x] **한 화면 · 기하 기반 오퍼레이션 보드를 채택한다.** 노드는 생성 좌표의 방, 간선은 권위 있는
  경로선, `@`는 지속 토큰, 보스는 상시 `◆`.
- [x] **목록을 주 상호작용에서 강등한다.** 안정 ID와 노드 상세는 **선택 노드 상세 카드**로 유지한다.
- [x] **입력 의미는 바꾸지 않는다.** 화살표 = 인접 목적지 강조, Enter = 이동 확정
  (`applyMatrixAction`). 보드는 같은 상태를 그릴 뿐이다. 조우 동사 층도 그대로다.
- [x] **ADR-0246 B는 보류 유지.** 런을 타일 걷기로 바꾸지 않는다.
- [ ] 회로판형 ICE 결정 화면(안 3) — **범위 밖**, 별도 결정 대상.

### 협상 불가 결정층 규칙 8개 (종합 §3 그대로)

| # | 공간화의 실패 | 규칙 |
| --- | --- | --- |
| 1 | 안개가 합법 경로를 숨김 | **현재 인접·간선은 항상 표시.** Probe/SCAN은 위협 *상세*만 숨긴다, 위상은 절대 아님 |
| 2 | 스크롤이 보스·대안을 숨김 | **전체 위상이 한 화면.** 보스는 **상시 `◆`** (나침반 힌트 아님) |
| 3 | 이동이 선택을 대체 | **화살표 = 선택, Enter = 확정.** 최근접/보스방향 자동 선택 금지 |
| 4 | 도착이 내용을 자동 처리 | 도착이 **동사 오버레이를 열 수는 있으나 기본 선택·자동 실행 없음** |
| 5 | 미니맵이 진짜 결정면이 됨 | **별도 미니맵 금지** — 보드가 세계이자 조작면 |
| 6 | 그림이 연결을 발명 | **`MatrixNode.adjacent`가 권위.** 간선 없는 복도 금지, 간선 누락 금지 |
| 7 | 색이 의미를 지움 | `@` · `◆` · 간선 스타일 · `NEW/SEEN/CLEAR` · 선택 글리프 **병기** |
| 8 | 걷기가 복도세를 만듦 | **한 번의 확정된 간선 이동 = 한 번의 경로 행동.** 결정 사이에 빈 타일 걸음 금지 |

### 삭제할 것 / 유지할 것

| 구분 | 항목 |
| --- | --- |
| **삭제** | 목록을 주 상호작용으로 쓰는 구조: `▸ YOU ARE HERE` 블록, `REACHABLE NOW` 상자, **`DEPTH / ZONES (not routes)` 스택과 그 범례** (`Nxx = node ID, not travel order`, `▸ here → route ✓ seen + clear · new`, 깊이별 ID 토큰) |
| **유지** | 안정 노드 ID(`N01` 형식), 노드 상세(ID · zone · ICE 개수 · 이벤트 · 보상 · 상태) → **선택 노드 상세 카드**. `MATRIX — CYBERSPACE` 제목, ADR-0237 프레임, 하단 조작 안내, 선택적 ICE 미리보기 |

### 짓지 않을 것

- 미니맵, 카메라, 스크롤, FOV 자원화, LOS 인지 AI, 스트리밍
- **런을 타일로 걷기** (ADR-0246 B, 보류)
- 독립 크롤러는 ADR-0246 C를 위해 남기되, 그 규칙(이동의 자동 해결 등)을 런에 들여오지 않는다.

## 수락 증거 (Acceptance evidence)

이 결정의 구현은 다음을 모두 보여야 완료다.

1. **전후 캡처** — 실제 `renderMatrix` 그리드를 게임의 `AsciiRenderer`로 그린 PNG와 원문 텍스트,
   80×50 / 60×40 / 40×60, 시작·분기·보스 상태. 보관 위치:
   [`docs/design/matrix-operation-board-2026-11-01/`](../../design/matrix-operation-board-2026-11-01/README.md).
2. **규칙 테스트** — 테스트 가능한 규칙마다 구현 전 실패 → 구현 후 통과. 추가로: 모든 인접에
   간선이 있고 인접 없는 간선이 없음, 모든 현재 노드에서 `◆` 존재, 선택 이웃 강조, 상세 카드가
   목록의 노드 상세를 유지.
3. **레이아웃 회귀** — 33 노드 그래프·이웃 5개까지, 세 레이아웃에서 모든 인접·목표·선택 표시,
   레일 무결, 넘침 없음.
4. **밸런스 byte-identical** — 렌더러·데이터 표시만 바뀌므로 `npm run balance` 양 덱 stdout이
   ADR-0239 기준선과 동일 (opening `100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0`,
   PPL `100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7`).
5. **E2E green** — 기존 Playwright 전체 (demo-screenshots 제외).

## 결과 (Consequences)

- **좋아지는 것**: 위치·보스·대안 경로가 공간으로 읽힌다. 경로 선택이 행 커서가 아니라 연결된 방을
  타게팅하는 조작이 된다. 결정층(경로·동사)은 그대로라 표현이 결정을 대체하지 않는다.
- **비용**: 간선 배선(복도 라우팅)이라는 새 렌더 로직. 생성 그래프에는 멀리 떨어진 방을 잇는 간선이
  있어 고등급 그래프는 교차가 많다 — 현재 위치에서 출발하는 경로선만 실선/굵은선으로 강조하고 나머지는
  점선으로 낮춘다.
- **열린 위험**: 오너 만족은 스크린샷이 아니라 **상호작용으로만** 확인된다. 짧은 이동 피드백(이동
  애니메이션)은 이번 슬라이스에 없다. 화살표 순환 순서는 공간 방향이 아니라 리듀서의 인접 순서이며,
  이번 결정은 그 의미를 바꾸지 않는다 (카드의 `ROUTES` 줄이 그 순서를 명시).
- 세이브 스키마 불변: Matrix는 세이브에 저장되지 않고 미션 seed로 재생성되므로 기존 세이브도 로드 시
  기하를 얻는다. `site`는 선택 필드라 기하가 없는 손수 만든 행렬은 결정적 대체 배치를 쓴다.

## Implementation Status (2026-11-01)

**Status**: ✅ Implemented (이번 슬라이스 범위: 보드 · 상세 카드 · 기하 보존). 이동 애니메이션과 안 3은 범위 밖.

**Evidence**:
- `web/src/core/types.ts` — `MatrixSite { x, y, w, h, label }`와 선택 필드 `MatrixNode.site?`. 게임플레이는 읽지 않는다.
- `web/src/core/dungeon/dungeon.ts` (`dungeonToMatrix`) — 생성된 `Room`의 `x, y, w, h, label`을 `site`로 보존. ICE 승격 경로는 `{...n}` 복사로 그대로 유지. RNG 소비·노드 순서·인접 불변.
- `web/src/renderer/matrix_board_layout.ts` — 방 중심을 보드 좌표로 스케일(가로 ≤5, 세로 ≤3 배, 1칸 배선 여백). 모든 노드에 `site`가 없거나 겹치면 결정적 대체 배치(진입점 BFS 층 = 열, 맞지 않으면 8열 뱀 모양).
- `web/src/renderer/matrix_board_routes.ts`, `web/src/renderer/min_heap.ts` — 인접 1개당 복도 1개, 직교 A*. 방을 통과하지 않고, 양 끝 방이 아닌 방을 가리키지 않으며, 다른 복도와 평행으로 겹치지 않고, 방에서 떨어진 곳에서만 직각 교차. 현재 위치와 무관하게 행렬·보드 기하마다 한 번 계산(메모이즈) — 이동해도 보드가 움직이지 않는다.
- `web/src/renderer/matrix_board.ts` — 방 토큰 `[·]` / `#·#`(미해결 ICE 벽) / `@` / `◆` / `>·<`(타깃) / `◆@◆`(보스 위의 현재 위치), 상태 `·`/`✓`/`+` = NEW/SEEN/CLEAR. 복도 3종: 타깃 `━┃┏┓┗┛`, 경로 `─│┌┐└┘`, 연결 `┄┆╭╮╰╯`. 색은 보조일 뿐 모든 의미가 글리프로도 읽힌다. 2줄 범례.
- `web/src/renderer/matrix_nodes.ts` — 선택 노드 상세 카드(현재 노드, 타깃 또는 안내, ICE·보상·이벤트, 방 라벨, `ROUTES (n)` 화살표 순서, `◆ OBJECTIVE: BOSS` 위치·상태). 카드에서 캐시 이벤트는 `◆` 대신 `¤`(이 화면의 `◆`는 보스 전용).
- `web/src/renderer/matrix.ts` — `renderMatrix` 시그니처·순수성 불변(선택적 cleared 인자 포함). 제목·프레임·하단 안내·ICE 미리보기 유지. `DEPTH / ZONES` 스택과 범례 삭제.
- 리듀서·조우 동사·가격·튜닝·RNG·`status.ts`·크롤러·VFX 무변경. 화살표 순환 순서 불변이므로 `web/e2e/menu-nav.ts` 헬퍼도 무변경.
- 검증: 규칙 테스트 13개 HEAD에서 **13 failed → 13 passed**; `npm test` **167 files / 3754 passed**; typecheck 0; lint 0 errors(기존 keyboard.ts:14 warning 1); build 124 modules; 3132-case 스트레스(33 노드·이웃 5, 미배선 0); 양 덱 balance stdout byte-identical (ADR-0239 기준선); E2E **82 passed / 4 skipped / 0 failed**.
- 검증 수치·전후 캡처·시각 QA는 [증거 README](../../design/matrix-operation-board-2026-11-01/README.md)에 기록.

**Follow-up — 행동 가독성 (2026-11-01, 같은 날 오너 플레이 피드백)**: 보드는 목록보다 낫다고 확인됐으나 "어떻게 해야 하는지 알아보지 못하겠다". 규칙 8개 내에서 렌더러·온보딩 힌트만 변경:
- `matrix_nodes.ts` — `ROUTES (n): ↓1 N01  ↓2 N08 …`: 각 입력을 목적지로 명시(↓k = ArrowDown k회, 타깃이 있으면 타깃 기준 `>N01  ↓1 …`; 리듀서 순환과 동일). 40열에서는 둘째 줄로 감싼다(잘리지 않음). 정지 상태 카드 첫 줄 = `▸ PRESS ↓ OR ↑ TO PICK A ROUTE`(방 이름 없음 → 선택 아님), 타깃이 있으면 첫 줄 = 타깃, 그 아래 상세, 그다음 `@`. 카드 높이 8행 유지.
- `core/state/onboarding.ts` + `matrix.ts` + `run_screen.ts` + `main.ts` — ADR-0235 combat-entry 힌트와 같은 모듈·패턴의 1회 Matrix 진입 힌트(`shouldShowMatrixEntryHint`, 컨트롤러 플래그 `matrixEntryHintShown`). 경로가 있는 첫 보드에서 카드 아래 표시, 그 화면에서의 첫 입력으로 사라지고 다시 나오지 않는다.
- 리듀서·선택 의미·화살표 순서·동사·가격·튜닝·RNG 무변경; 기본 타깃 없음 규칙 테스트로 재확인. 신규 `web/tests/matrix_affordance.test.ts` **20 failed → 20 passed**; `npm test` **168 files / 3774 passed**; typecheck 0; lint 0 errors(기존 warning 1); build PASS; 양 덱 balance byte-identical(ADR-0239 기준선); E2E **82 passed / 4 skipped / 0 failed**. 증거: [matrix-affordance README](../../design/matrix-affordance-2026-11-01/README.md).

**Notes**: LSP는 TypeScript 서버 미설치로 실행하지 않았다(CLI `tsc --noEmit`이 타입 게이트). 캔버스 화면이라 행별 포커스 링·의미론적 접근성 트리는 여전히 없다(상속된 결함, 이번에 해결하지 않음).

## 영향 받는 항목

- 코드: 위 Evidence의 파일. 테스트: `web/tests/matrix_board.test.ts`(신규), 목록 구조를 고정하던 `matrix_structure` / `matrix_render` / `matrix_frame` / `matrix_route_choice` / `nav_index` 단언을 보드·카드 동등 단언으로 이관.
- 문서: 이 ADR, [ADR 색인](./README.md), [증거](../../design/matrix-operation-board-2026-11-01/README.md), `log.md`.
- 변경하지 않음: ADR-0005 / 0060 / 0103 / 0237 / 0246 / 0247 / 0248의 결정 내용.

## 변경 이력

- 2026-11-01: 작성 — 오너가 종합 권고의 승자(한 화면 기하 기반 보드, 목록 → 상세 카드) 승인. Accepted. 같은 날 첫 슬라이스 구현 상태 기록.
