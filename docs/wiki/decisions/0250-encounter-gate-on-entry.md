# ADR-0250: 조우 게이트를 출구에서 입구로 — Matrix 이동 인터랙션 수정

**상태**: Accepted
**날짜**: 2026-11-02
**결정자**: 사용자 (프로젝트 오너) — "그래 C로 가자" 승인
**우선순위**: P2 (The Matrix — 경로·위험 결정)
**관련**: [상위 ADR-0246 — 던전의 역할과 런 인터랙션](./0246-dungeon-role-and-run-interaction.md) · [ADR-0247 — 던전 역할 보충](./0247-dungeon-role-supplement-manus-second-opinion.md) · [ADR-0236 — 접근성·모션](./0236-accessibility-and-motion.md) · [ADR-0195 — 구현 상태 기록](./0195-adr-implementation-workflow.md)

> **이 ADR은 ADR-0246의 조항 2건만 대체한다.** (1) "출발 확인이 결정 메뉴를 연다"(§Implementation Status, 242행),
> (2) "이번 방문의 통과 상태는 선택적 일시 필드"(같은 절, 243행).
> ADR-0246의 나머지 결정 — A → C, 던전 = 아이템 미니게임, 고정 동사 4종,
> PROBE 8 / BYPASS 60 / 상한 100, `clearedEncounterNodes` 저장 계약, 보스 우회 차단,
> 종결 노드 조건 — 은 **그대로다**. ADR-0246 본문은 수정하지 않는다.

## 컨텍스트 (Context)

### 오너 플레이 보고

> "이벤트가 끝나고 좌우 두군데 밖에 선택지가 없는데 계속 이벤트가 반복되서 빠져나오지 못했어."

이웃이 2개뿐인 노드에서, 이벤트를 겪은 뒤 **어느 쪽을 골라도 이벤트가 다시 뜨고 이동하지 못한다**는 보고다.

### 측정된 메커니즘 (재현 + 코드 대조)

| 관찰 | 근거 |
| --- | --- |
| ICE 노드에 **도착해도 이벤트가 열리지 않는다** | 이동 후 메시지 `Moved to mid — ENTER: encounter; arrows: route` |
| 그 노드에서 **출발 확인을 하면 결정 메뉴가 열린다** | `state_actions_phases.ts:56-65` → `"Uncleared ICE — choose how to cross."` (64행) |
| 조우 화면은 **동사를 확정하지 않으면 닫히지 않는다** | 실행 측정. 화면 닫기는 PROBE/BYPASS/BREACH/JACK OUT 중 하나의 확정으로만 가능 |
| 통과 허가는 **단일 슬롯·방문 단위·비저장** | `bypassedEncounterNodeIndex`는 선택적 일시 필드 (ADR-0246 243행). 다른 노드를 우회하면 이전 노드의 허가가 소멸 |
| 우회 재지불이 **사실상 불가** | BYPASS 60, 상한 100, 누산기는 단조 증가 → 런당 1회 |
| 화면이 **정반대를 약속한다** | `matrix.ts:210-211`이 경로 선택 시 `ENTER: travel | ↑↓: route | ESC: back`을 출력하지만, Enter는 이벤트를 연다 |

### 근본 원인

ICE 게이트가 **출구**에 달려 있다. 플레이어의 기대는 "이벤트는 노드에 **들어갈 때** 겪는 것"인데,
구현은 **나가려는 순간** 이벤트를 붙잡는다. 그래서

1. 들어올 때는 조용히 지나칠 수 있고,
2. 나가려는 입력이 전부 이벤트 재개로 소비되며,
3. 해결해도 그 허가가 방문 단위라 **두 번째 노드부터는 매번 다시 붙잡힌다**.

2-이웃 노드에서는 좌/우 어느 쪽을 골라도 같은 결과이므로 **무한 반복**으로 체험된다.

**하드 락은 아니다.** BREACH(COST 0)와 JACK OUT(런 포기)은 항상 가능하다. 문제는 (a) 그 사실을 화면이 알려주지 않고,
(b) 정상적으로 통과하려는 시도가 **이벤트 재개로만** 응답된다는 점이다.

## 결정 (Decision)

### 1. 게이트를 입구로 옮긴다

이동이 **ICE 미해결 노드에 도착**하면 그 이동이 확정된 직후 **조우 결정이 즉시 열린다**.
이동 자체는 성공한다(플레이어는 그 노드에 서 있다). 이벤트는 **도착의 결과**이지 출발의 조건이 아니다.

### 2. 해결한 노드는 런 동안 기억한다

전투로 깬 노드는 기존 `clearedEncounterNodes`가 이미 담당한다. BYPASS로 통과한 노드는
**런 스코프 집합** `bypassedEncounterNodes: ReadonlyArray<number>`에 기록한다.

`bypassedEncounterNodeIndex`(단일 슬롯, 방문 단위, 비저장)는 **제거한다.**

**"해결된 노드" = `clearedEncounterNodes` ∪ `bypassedEncounterNodes`.**

### 3. 출발은 자유롭다

해결된 노드에서의 이동 확인은 결정 메뉴를 **다시 열지 않는다.**
ADR-0246 242행의 "출발 확인이 결정 메뉴를 연다" 조항은 이 조항으로 대체된다.

### 4. 안티-익스플로잇은 보존된다

ADR-0246 242행이 막으려던 것은 "목적지를 먼저 골라 무료로 떠나기"였다. 입구 게이트는 그것을
**더 강하게** 막는다 — 조용히 지나가려 해도 **도착 즉시** 붙잡히기 때문이다.

ICE 하나의 비용은 여전히 **정확히 한 번**이다:

| 동사 | COST | 결과 |
| --- | --- | --- |
| BREACH | 0 | 전투 → 승리 시 `clearedEncounterNodes`에 기록 |
| BYPASS | 60 (런당 최대 1회) | 통과 + `bypassedEncounterNodes`에 기록. 보상·회복·완료 목록 기록 없음 (ADR-0246 241행 불변) |
| PROBE | 8 | 정보만. 노드를 해결하지 않는다 |
| SCAN | 유틸리티 프로그램 소모 | 정보만. 노드를 해결하지 않는다 |
| JACK OUT | 0 | 런 포기 |

해결하지 않은 노드에 다시 도착하면 다시 결정이 열린다 — 이것이 이 게이트의 목적이다.

### 5. 화면이 진실을 말한다

- **footer**는 Enter가 실제로 할 일을 표시한다. ICE가 미해결인 노드에서 `travel`이라고 **약속하지 않는다.**
- **거부/안내 메시지**는 탈출구를 명시한다: `BREACH: fight · BYPASS: 60 COST (once per run) · JACK OUT: abandon run`.
- **조우 화면**은 이 노드가 통과를 막는다는 사실을 한 줄로 고지한다.

### 6. 세이브 호환

새 필드는 **구 세이브에서 누락을 허용하고 빈 목록으로 복원한다** (ADR-0185 계약 유지).
저장 스키마 **버전을 올리지 않는다.** `clearedEncounterNodes`의 저장 계약은 불변이다.

## 대체 범위 (Superseded)

| ADR-0246 조항 | 이 ADR의 대체 |
| --- | --- |
| §Implementation Status 242행 — "현재 노드의 미완료 ICE를 해결하거나 이번 방문에서 BYPASS를 결제하기 전에는 출발 확인도 결정 메뉴를 연다 / 목적지를 먼저 골라 무료로 떠나는 우회 차단 / 이동하면 결제 통과 플래그를 초기화" | 결정 1·2·3 — 도착 게이트 + 런 스코프 기억 + 자유 출발. **의도(무료 통과 차단)는 결정 4로 보존** |
| §Implementation Status 243행 — "이번 방문의 통과 상태는 선택적 일시 필드 … 이동/로드 시 통과 허가를 유지하지 않는다" | 결정 2 — `bypassedEncounterNodes` 런 스코프. **`clearedEncounterNodes` 저장 계약은 불변** |

ADR-0246의 본문·결정·계약·동사·가격·보스 차단·종결 조건은 **변경하지 않는다.**
ADR-0246의 `## Implementation Status`에 이 ADR을 가리키는 주석을 추가하는 것만 허용한다 (ADR-0195).

## 대안과 기각 (Alternatives)

| 안 | 내용 | 판정 |
| --- | --- | --- |
| **A. 설명만 고친다** | footer·메시지가 규칙을 정확히 설명 | **기각** — 오너 판정: "A를 선택하면 문제 해결이 아니지 않아?" 막히는 사실은 그대로다 |
| **B. 게이트 제거** | 경로를 고르면 언제든 자유 이동 | **기각** — 익스플로잇(무료 통과)이 부활한다. ADR-0246 컨텍스트의 문제가 되돌아온다 |
| **C. 게이트를 입구로 (채택)** | 도착이 이벤트를 연다. 해결 노드는 런 동안 기억. 출발은 자유 | **채택** — 루프 제거 + 익스플로잇 차단 유지 + 기대와 일치 |

## 결과 (Consequences)

**얻는 것**

- 보고된 무한 반복이 사라진다.
- 게이트 위치가 플레이어 기대와 일치한다 ("이벤트는 들어갈 때 겪는 것").
- 상태가 단순해진다 — 방문 단위 임시 슬롯이 런 스코프 집합 하나로 바뀐다.
- 화면이 실제 동작을 약속하므로 어포던스 결함이 함께 닫힌다.

**감수하는 것**

- **도착 시 강제 결정**이 이동의 리듬에 한 박자를 더한다. 보드로 돌아가는 흐름이 끊길 수 있다.
  → 이 ADR의 **열린 위험**이며, 첫 슬라이스에서 실제 플레이로만 판정한다.
- 저장 필드가 1개 늘어난다 (구 세이브는 빈 목록으로 로드).
- BYPASS를 런 단위로 기억하므로, 우회한 노드는 **재방문 시 무료로 통과**된다.
  이는 의도다 — 비용은 이미 런당 1회로 지불됐다.

## 열린 질문

1. 입구 게이트로 인한 리듬 손실이 감당 가능한가 — 플레이로만 판정 (ADR-0249의 방식).
2. 도착 직후 결정을 열 때, 전투 진입 연출(있으면)과 어떻게 겹칠지.
3. PROBE/SCAN만 쓰고 노드를 떠난 뒤 다시 도착하면 결정이 다시 열린다 — 이 반복이 성가신가.

## Implementation Status (2026-11-02)

**Status**: ✅ Implemented (첫 슬라이스; 열린 위험 1·3은 플레이 판정 대기)

**Evidence**:
- `web/src/core/state/encounter_verbs.ts` — `encounterResolved` (= `clearedEncounterNodes` ∪ `bypassedEncounterNodes`), `encounterGates`, `encounterGateMessage`. BYPASS 확정 시 `bypassedEncounterNodes`에 현재 노드를 추가한다. 가격 상수·`bypassBlockReason`·PROBE/BREACH/SCAN/JACK OUT 불변.
- `web/src/core/state/state_actions_phases.ts` — 결정 1: 확인으로 이동한 목적지가 미해결 ICE면 **같은 반환 상태**가 이동(`currentNodeIndex`·`visitedNodes`·`turnCount`)과 `encounterDecision {selectedVerb: null, probed: false}`를 함께 담는다. 결정 3: 해결된 노드에서의 출발은 결정을 열지 않는다. 결정 4: 도착 없이 미해결 노드에 서 있는 경우(런 시작·CONTINUE)는 출발 확인이 여전히 결정을 연다. 종결 노드 완료 조건 불변.
- `web/src/core/types.ts`, `web/src/core/state/state.ts`, `web/src/save/storage.ts` — 결정 2·6: `bypassedEncounterNodes?: ReadonlyArray<number>`를 GameState/SaveSlot에 추가, `bypassedEncounterNodeIndex` 제거. 구 세이브 누락 시 `[]`, 잘못된 목록은 거절. 스키마 **version 1 유지**, `clearedEncounterNodes` 계약 불변.
- `web/src/renderer/matrix.ts` (`matrixFooter`), `encounter.ts`, `run_screen.ts` — 결정 5: footer는 Enter가 실제로 하는 일만 표시(미해결 노드 `ENTER: enter ICE | ICE blocks travel | ESC: back`, 미해결 목적지 `ENTER: enter ICE`, 자유 목적지만 `ENTER: travel`, 정지 시 `↑↓: pick route`). 도착 메시지 `Travel blocked. BREACH: fight. BYPASS: 60 COST (once per run). JACK OUT: abandon run.`는 HUD에서 단어 단위로 15자 이하로 감싼다(40×60 HUD 16열). 조우 화면은 `ICE blocks travel until resolved`를 한 번 표시.
- `web/src/renderer/matrix_travel.ts` — 도착이 결정을 여는 경우 220 ms 이동 애니메이션을 시작하지 않는다(조우 화면이 즉시 덮어 프레임이 보이지 않고, 지연 시 입력이 더 이상 조작하지 않는 보드를 보여 주게 됨). 자유 도착은 기존대로 애니메이션; 상태는 어느 경우든 같은 액션에서 확정.
- `web/tests/encounter_entry_gate.test.ts` — **28 tests, HEAD에서 26 failed / 2 passed → 28 passed** (통과 2건은 이미 성립하던 안티-익스플로잇 가드). 기존 테스트 7개 파일은 대체된 계약(ADR-0246 242·243행)을 담은 단언만 조정, 삭제 없음; 근거는 증거 README 표.
- 검증: typecheck 0, lint 0 errors(기존 keyboard.ts:14 warning), `npm test` **170 files / 3817 passed**, build PASS, 편집 src만 Prettier, 양 덱 balance stdout **byte-identical**(ADR-0239: opening 100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0, PPL 100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7), E2E **82 passed / 4 skipped / 0 failed**(5195 preview 유지), `e2e/menu-nav.ts` 무수정, `e2e/continue.spec.ts` 필드명 1줄.
- 증거: [matrix-entry-gate-2026-11-01](../../design/matrix-entry-gate-2026-11-01/README.md) — 7 사례 × 3 레이아웃 전후 캡처, 폭 검사 21/21, 대비 최소 10.15:1, 실제 브라우저 로그.

**Notes**: 우회한 노드는 보드에서 여전히 `#·#`로 그려진다(보드의 CLEAR = 전투 해결). 열린 질문 1(리듬)·3(PROBE/SCAN 후 재도착 반복)은 실제 플레이로만 판정한다. 결정 내용은 변경하지 않았다.

### 후속 슬라이스 — 탈출 불가 상태 제거 (2026-11-02)

**새 증거** (오너: "아직 못빠져나와." / 화면 "보드 + 'enter ICE' + 이벤트 반복"). 5195 빌드 실제 키 로그([before-trace](../../design/matrix-encounter-escape-2026-11-01/live/before-trace.txt)), 노드 1(이웃 2개):
- 키만 누르는 경로: 도착 → Enter = 안내만 → ↓ Enter = PROBE 8 결제 → Enter = **변화 없음** → ← = SCAN(유틸리티 없음) → Enter = **변화 없음**. `cur 1` 고정.
- (a) BYPASS 후 보드: **재현 안 됨** — footer `↑↓: pick route`, Enter 이동. 렌더러·리듀서 해결 판정 일치.
- (b) CONTINUE로 미해결 노드 복원: **재현됨** — 보드 + `ENTER: enter ICE | ICE blocks travel | ESC: back`, 모든 출발 시도가 결정을 다시 염(결정 4 문장의 출발 게이트).
- (c)(d) 세션 내 **ESC / JACK OUT 동사**: **재현됨** — 리듀서가 `phase: "menu"`만 바꾸고 `runPhase: "matrix"`를 남겨 같은 보드로 돌아오고, Enter가 같은 조우를 다시 염. footer가 ESC를 `back`이라 안내했다.

**변경** (결정 1~6 불변; 결정 4의 "도착 없이 서 있는 경우는 출발이 결정을 연다"라는 Implementation 서술을 "로드·런 시작을 도착으로 본다"로 바꿔 같은 안티-익스플로잇을 유지):
- `encounter_verbs.ts` — `openArrivalEncounter`(로드·런 시작·도착 공용), `runAbandoned`, 화살표 순환에서 유틸리티 없는 SCAN 제외(순서 불변), Enter 무선택/사용한 PROBE·SCAN에 출구를 명시하는 메시지.
- `state_actions_phases.ts` — 출발 게이트 제거(경로 확정 시 항상 이동), 경로 없이 Enter는 서 있는 미해결 ICE에 진입. `state.ts` `slotToGameState` — 복원이 결정을 엶(세이브-리로드 회피 불가). `main.ts` — 런 시작에 `openArrivalEncounter`, `runAbandoned`면 런 상태를 버리고 메인 메뉴.
- `encounter.ts` — `EXITS: BYPASS · BREACH · JACK OUT`, 행마다 `EXIT`/`INFO`, 출구 cyan, `Nothing selected — press ↓ to pick`, `ESC: jack out (abandon run)`. `matrix.ts` footer `ESC: jack out`.
- 테스트: 신규 `encounter_escape.test.ts` **HEAD 32 failed / 8 passed → 40 passed**. 기존 5개 파일의 대체된 계약 단언만 조정(삭제 없음; 증거 README 표). `npm test` **171 files / 3857 passed**, typecheck 0, lint 0 errors(기존 warning 1), build PASS, Prettier PASS, 양 덱 balance byte-identical(ADR-0239), E2E **82 passed / 4 skipped / 0 failed**(5195 유지), 폭 검사 27/27, 대비 최소 10.15:1.
- 결과: JACK OUT/ESC는 이제 실제로 런을 끝낸다(확인 단계 없음, 자동 저장 슬롯은 유지). 증거: [matrix-encounter-escape-2026-11-01](../../design/matrix-encounter-escape-2026-11-01/README.md).

### 후속 — 세이브 시점과 런 완료 (ADR-0252, 2026-11-02)

**새 증거** (오너: "맵에서 보스를 쓰러뜨린후 이동하려니 또 보스가 나와서 회복 못하고 패배하게 되던데."). 5195 실제 키 로그: 자동 저장이 전투 프레임에서만 돌아 보스 격파·loot·이동이 슬롯에 없었고(`clr [18]` vs 메모리 `[18,20]`), 엔딩은 입력을 영원히 붙잡았으며, 리로드 + CONTINUE가 결정 2·4대로 보스 결정을 열어 만피 재전투(`wintermute 140/140`, 잘못된 기반 ICE)를 강제했다.

**이 ADR에 대한 영향**: 결정 1~6 **불변**. "로드 = 도착"은 그대로 동작하며, 이제 세이브가 확정 상태를 담으므로 그 가정이 성립한다. 전투 중 저장 슬롯은 여전히 결정을 다시 열고(보스 BYPASS 차단 유지) — `run_end_save.test.ts`의 ADR-0250 가드 2개(HEAD·수정 후 모두 통과)와 실제 키 trace `boss-fight-reload`가 증거. 클리어된 종결 노드 슬롯은 loot 화면으로 복원되어 결정을 열지 않는다(해결된 노드이므로 회피가 아님).
- 상세·증거: [ADR-0252](./0252-run-end-and-save-timing.md), [run-end-and-save-2026-11-02](../../design/run-end-and-save-2026-11-02/README.md).

## 변경 이력

- **2026-11-02**: 신규. 오너의 "그래 C로 가자" 승인으로 Accepted. ADR-0246 조항 2건 대체, 나머지 불변.
