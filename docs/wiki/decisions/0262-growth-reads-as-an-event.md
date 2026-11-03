# ADR-0262: 성장을 사건으로 만든다 — 터미널 커밋 + 도착 인수인계

**상태**: Accepted
**날짜**: 2026-11-03
**결정자**: 오너 선택 ("추천대로 구현해줘") — Manus 시안 + Jev 제약 게이트
**우선순위**: P1 (The Run — 성장의 재미, The Style — 피드백)
**관련**: [ADR-0261 — 획득 3박자](./0261-growth-moment-is-shown.md) · [ADR-0259 — 카드 보상](./0259-card-reward-growth.md) · [ADR-0251 — 어포던스 진실성 · 금지 목록](./0251-truthful-program-affordance-and-combat-integrity-rules.md) · [ADR-0236 — reduced-motion](./0236-accessibility-modes.md) · [ADR-0249 — matrix travel](./0249-matrix-operation-board.md)

> **이 ADR은 ADR-0261 의 3박자에 연출을 붙인다.** 오너가 "이벤트나 효과 시안은 마누스 도움을 받아도 된다"고
> 허용해, 실제 제약을 프롬프트로 주고 Manus 시안 4안을 받은 뒤 Jev 로 게이트해 **안1+안4**를 채택했다
> ([시안 원문](../../design/growth-direction-2026-11-03/README.md)). 리듀서·RNG·밸런스·저장 무변경.

## 컨텍스트 (Context)

ADR-0261 은 획득을 "정직하고 명확"하게 만들었지만 **연출은 텍스트 색 변화가 전부**였다.
카드를 얻는 순간이 사건처럼 느껴지지 않는다 — 오너가 명시적으로 "성장하는 재미는 중요하다"고 한 요소다.

또 하나의 결함을 발견했다: **매트릭스 화면은 `state.message` 를 렌더하지 않는다.**
ADR-0261 의 도착지 메시지(`Took Kraken. …`)는 매트릭스에서 **보이지 않는다** — 성장이 loot 화면과 함께
사라진다. 도착 인수인계는 이 구멍도 메운다.

## 결정 (Decision)

**안1 TERMINAL COMMIT + 안4 ARRIVAL: ROUTE HANDOFF 를 하나의 흐름으로 채택.**

```
① 커밋 (loot)                                ② 인수인계 (매트릭스 도착)
PROGRAM SLOT 01                              HUD:
> 1 VIRUS  [PIERCE 2]                          MATRIX
DATA LINK ............ OPEN                    Node 19/28
SIGNATURE ............ VIRUS                   + PROGRAM
DECK COMMIT ......... [##########] 100%          VIRUS
[+] PROGRAM ACQUIRED
HEAL applied → 100/100                       ENTER: continue
```

- 별도 옵션(B: 안1 단독 · C: 안4 단독 · D: 안3 `QUEUED` · E: 셋 다)을 검토했고, **A** 를 골랐다.
  근거: Manus 1위 · Jev choice **0.97 / conf 0.96** 가 독립적으로 같은 결론.
- **안2 GHOST TRACE 는 제외** — Jev noul **0.70**. `DECK[07]` 의 덱 슬롯 번호는 **게임 상태에 없는 값**이라
  어포던스 진실성 위반이다.
- **안3 COLD BOOT 은 조건부 기각** — noul **0.61**. `READY` 는 과대 주장이다(카드는 손패가 아니라
  **뽑기 더미**로 간다). 채택한다면 `QUEUED`/`STAGED` 로 바꿔야 하는데, 이번 흐름에는 넣지 않았다.
- 안1(noul 0.24)·안4(noul 0.18)는 통과.

## 결과 (Consequences)

### 형태 — 리듀서 무변경, 표시 전용 프레임 2개

`main.ts` 에 `matrixTravelFrame`(ADR-0249)과 **같은 종류**의 표시 전용·벽시계 상태를 둔다.
새 VFX 종류도, 이벤트 버스도, 리듀서 상태도, 저장 필드도 없다.

| 지점 | 하는 일 |
|---|---|
| `syncGrowthReveal(previous, next)` | 카드 획득 전환(`cardRewardTaken` 바뀜)에서 `lootCommit` 시작. loot→비-loot 전환에서 커밋을 정리하고, 매트릭스로 돌아갈 때만 `matrixArrival` 시작 |
| `draw()` | `resolveGrowthReveal` 로 그 프레임의 커밋 단계·도착 줄을 풀어 `renderRunScreen(..., growth)` 로 넘김 |
| render loop | 커밋 패널을 **단계가 바뀔 때만** 다시 그림(멈추면 정지). 도착 노트는 창이 지나면 스스로 지움 |

새 모듈 `web/src/renderer/growth_reveal.ts` — 순수 함수만: `lootCommitStage`(고정 단계), `commitBar`
(고정 막대), `lootCommitLines`(wide/compact), `drawLootCommit`, `beginMatrixArrival`,
`matrixArrivalActive`, `matrixArrivalLines`, `resolveGrowthReveal`.

### 하드 제약 준수

- **입력 락 없음**: ENTER 는 언제나 유효하다. 살아있는 실측에서 ENTER 응답 **9ms**.
- **대기 없음**: VFX 끝나기를 기다리지 않는다. 커밋 패널은 벽시계로 단계만 바뀌고, 플레이어의 ENTER 가 진행한다.
- **어포던스 진실성**: 커밋 패널은 리듀서가 **카드를 이미 덱에 넣은 뒤**에만 시작한다. `100%` 는 참인 사실이다.
  도착 노트는 **카드를 놓치지 않게** 이름을 다시 말한다 — 매트릭스가 `state.message` 를 안 그리던 구멍을 메운다.
- **reduced-motion**: 단계 연출은 사라지고 **최종 문구만** 남는다. 도착 노트는 생략된다(성장 자체는 이미 커밋됨).
- **색은 중복**: `PROGRAM SLOT` / `SIGNATURE` / `DECK COMMIT [####] 100%` / `[+] PROGRAM ACQUIRED` —
  글리프·텍스트만으로 판독된다.
- **한 화면**: 80×50 · 60×40 · 40×60 모두 그리드/HUD 초과 **0**. 40열은 compact 문구(`SLOT 01` / `COMMIT [####] 100%` / `[+] ACQUIRED`).
- **RNG 0 · 밸런스 byte-identical**: 표시 전용. opening `100.0/100.0/81.4/42.6/36.6/0.0`,
  PPL `100.0/100.0/99.3/84.1/44.4/27.3` (재측정 동일).
- **금지 목록 무위반**: 새 이벤트 버스·애니메이션 리듀서·영속 표시 큐·저장 연출 상태·`Math.random` 미리보기·
  카드 드래그·가로 스크롤·Y/N 확인·새 상태/타겟 없음.

### 발견·수정 (구현 중)

- **loot 화면은 입력당 한 번만 그린다.** 커밋 패널이 첫 단계에서 멈췄다 — 렌더 루프가 단계 변화 시에만
  다시 그리도록 고쳤다(정지 후 정지). 이 결함은 3레이아웃 정지 캡처로는 안 보이고 **실플레이에서만** 드러났다.
- **터치 보상 경로(`handleRewardButton`)가 `syncGrowthReveal` 을 안 거쳤다** — 터치 플레이어는 옛 색 변화만 봤다.
  같은 훅을 지나게 고쳤다.

## Implementation Status (2026-11-03)

**Status**: ✅ Implemented

**Evidence**:

- `web/tests/growth_reveal.test.ts` — 21 tests: 고정 단계 진행·클램프·reduced-motion 최종 단계 고정,
  커밋 바 고정 단계, wide/compact 문구와 40열 적합, 도착 노트 창(열림/만료), HUD 줄 폭,
  프레임 해석, 그리고 **소스 스캔**(`Math.random` 0 · `GameState`/`applyAction` 미접촉 · 타이머/큐 없음 ·
  `main.ts` 의 획득 전환 시작·loot 이탈 인수인계·루프 단계 진행).
- 3개 레이아웃 before/after 캡처(21 PNG + 21 쌍, `loot-commit`/`matrix-arrival` 포함) — 그리드/HUD 초과 0 —
  [`growth-reveal-2026-11-03`](../../design/growth-reveal-2026-11-03/).
- **실플레이(preview 127.0.0.1:5195, 독립 headless Chromium)**: 카드 획득 → `lootCommit` 설정(slot 1, name)
  → 단계 정착 → ENTER **9ms** 로 매트릭스 → 도착 노트 같은 이름 → +0.6s 표시 → +2.0s 소멸, 입력 살아있음
  (경로 선택됨) → **PASS**. reduced-motion 재실행: 커밋 패널은 **최종 문구로 즉시** 표시, 도착 노트 없음 → **PASS**.
  스크린샷·로그: `docs/design/growth-reveal-2026-11-03/live/`, `.../live-rm/`.
- vitest **181 files / 4006 tests passed** · tsc 0 · eslint 0 errors · build PASS.

**Notes**:

- 커밋 패널은 ENTER 전까지 화면에 남는다(정착 상태). 이는 의도다 — 플레이어가 자기 선택을 한 번 더 본다.
- VFX 시스템(`data_acquired` 등)은 **전투 화면 경로 전용**이라 손대지 않았다. loot/매트릭스는 자기 격자를
  매 프레임 새로 그린다.

## 열린 질문

- **(a) 안3 프로그램 기상.** `QUEUED`/`STAGED` 로 문구를 고치면 톤이 더 세진다(별도 슬라이스).
- **(b) 하네스 모델링.** `balance_sim` 이 loot 를 걷지 않아 성장의 힘을 못 잰다(ADR-0259/0261 과 동일).
- **(c) narrow-layout HUD 압착.** 매트릭스 HUD 도착 줄로 좁은 화면 HUD 가 더 빡빡해진다(기존 결함, HUD 재설계 스케일).

## 영향 받는 항목

- `web/src/renderer/growth_reveal.ts` — **신규** (커밋 패널 + 도착 노트, 순수 함수)
- `web/src/renderer/ending.ts` — `renderLootScreen(... commitFrame)`, HEAL 행 예약
- `web/src/renderer/run_screen.ts` — `growth: GrowthReveal | null`, 매트릭스 HUD 도착 줄
- `web/src/renderer/accessibility_modes.ts` — `MotionKind` 에 `reveal` 추가
- `web/src/main.ts` — 필드 3개(`lootCommit`·`matrixArrival`·`lootCommitStageShown`), `syncGrowthReveal`,
  `draw()` 해석, 루프 단계 진행·도착 만료
- `web/tests/matrix_affordance.test.ts` — `renderRunScreen` 소스 스캔 regex 를 추가 인자 허용으로

## 관련 결정

- ADR-0261 (3박자 — 이 ADR 이 그 연출이다) · ADR-0259 (보상) · ADR-0251 (규칙 + 금지 목록) ·
  ADR-0249 (matrix travel — 같은 표시 전용 선례) · ADR-0236 (reduced-motion)

## 변경 이력

- 2026-11-03: Manus 시안 4안 + Jev 게이트 → 오너 "추천대로" → Draft 작성
- 2026-11-03: Accepted — 구현 완료(실플레이 검증 포함)
