# ADR-0246: 던전의 역할과 런 인터랙션 — A → C, 던전은 아이템 미니게임

**상태**: Accepted
**날짜**: 2026-11-01
**결정자**: 사용자 (프로젝트 오너) — 2026-11-01 직접 결정
**우선순위**: P2 (The Matrix — 경로·위험 결정, The Build / The Flatline 접점)
**관련**: [ADR-0005 — 사이버스페이스 표현](./0005-cyberspace-representation.md) · [ADR-0060 — 던전 탐색 재설계](./0060-dungeon-exploration-redesign.md) · [ADR-0103 — 던전 전용 모드](./0103-dungeon-only-mode.md) · [ADR-0185 — 저장 마이그레이션](./0185-save-migration-v2.md) · [ADR-0195 — 구현 상태 기록](./0195-adr-implementation-workflow.md) · [ADR-0229 — 밸런스 판정 정책](./0229-grade-curve-rebaseline.md) · [ADR-0240 — 유휴 압력·알람](./0240-idle-pressure-and-alarm-loop.md) · [디자인 기둥](../../design/pillars.md) · [핵심 루프](../../design/core_loop.md)

> **확정: 던전의 역할은 C안 — 선택적 아이템 미니게임. 순서는 A → C다.**
> 런의 경로·위험 결정을 먼저 만들고 그 결정 어휘를 작은 던전 안에서 재사용한다.
> **B안 — 던전이 런 전체가 되는 방향은 보류이며 기각이 아니다.**
> **구현은 ❌ Not started.** 이 문서는 이전 단일 방향 Draft를 오너의 실제 결정으로
> 다시 쓴 것이다. 코드·테스트·ADR-0005/0060/0103 본문은 변경하지 않는다.

## 컨텍스트 (Context)

### 런의 문제 — 노드는 있지만 결정점이 없다

| 현재 동작 | 근거 | 사라진 결정 |
| --- | --- | --- |
| MATRIX 이동은 보스 방향 BFS 자동 라우팅 | `web/src/core/state/state_actions_phases.ts:97-149` — `nextHopToward(matrix, currentNodeIndex, bossNode)` | 분기 선택·조우 건너뛰기·조우 거절이 없음 |
| 보상은 확인만 가능하고 이후 자동 전진 | `web/src/core/state/state_actions_phases.ts:172-245` | 보상 뒤 다음 목적지를 고르지 못함 |

[ADR-0005](./0005-cyberspace-representation.md)는 노드를 “명확한 위치 / **결정점**”으로
정의했고 “한 노드 = 한 결정”을 의도했다. 현재 그 결정점은 구현되지 않았다.
따라서 화면을 던전으로 바꾸는 것보다 **플레이어가 어디로, 어떤 위험을 감수하며 갈지
고르게 하는 것**이 먼저다. [핵심 루프](../../design/core_loop.md)의 발견·해킹·회피·전투·후퇴도
자동 이동으로는 성립하지 않는다.

### 던전의 문제 — 이동 느낌과 목적을 구분한다

기존 `DUNGEON CRAWL`은 별도 메뉴이며 런에 통합되지 않는다
(`web/src/renderer/menu_main.ts:41-51`, `web/src/main.ts:1011-1023`).
이동 느낌을 살리는 것과 현재 크롤러의 자동 해결·무효 보상·부활 규칙을 채택하는 것은 다르다.
오너는 던전을 없애지 않되 **추가 아이템을 얻는 짧고 독립된 부가 활동**으로 역할을 한정했다.
현재 크롤러의 결함과 교체 조건은 아래 C안 계약에 기록한다.

## 4안 비교표 + 결정 (Decision)

비용은 상대 규모이며 일수 추정이 아니다. 기둥 번호는 [디자인 기둥](../../design/pillars.md)을 따른다.

| 안 | 역할·효과 | 비용·위험 | 기둥 정합 | 오너 결정 |
| --- | --- | --- | --- | --- |
| **A. 런 인터랙션 개선 — 경로/위험 결정** | 노드 그래프 유지. 인접 목적지를 명시적으로 고른 뒤 Probe / Bypass / Breach / Jack out 선택. 가장 작은 변경으로 주도권을 주므로 효과가 가장 큼 | **중간** — 그래프·이벤트·프로그램·전투·런 자원 재사용. 정보·비용·전이 연결 필요 | **P1/P2/P3/P4** — 한 런의 결정점, 매트릭스 경로, 위험 수용·거절, 도구별 대응 | **먼저 진행** |
| **B. 던전 = 런 전체** | 런 전체를 공간적으로 표시된 던전에서 이동하며 이벤트·보스를 만남 | **큼** — 생성기는 공유되지만 런 렌더러·입력·결정·상태 이월·저장 호환 필요 | P1/P2 강화 가능. P3는 죽음 종결, P4는 실효 보상 조건. 공간 표시만으로 결정이 생기지 않음 | **보류** — A와 C가 루프를 입증한 뒤 재검토. 기각 아님 |
| **C. 던전 = 아이템 미니게임** | 선택적·유계 부가 활동에서 추가 아이템 획득. 건너뛰면 아이템 기회만 포기 | **작음** — 짧은 범위와 기존 기반 재사용 전제. 보상 공급·실패 비용 계약 필요 | **P4 직접 강화** — 숫자가 아닌 도구. 런이 가장 약한 기둥을 보완. P2 부합, **P3 조건부**. P1은 유계·선택성으로 보호 | **던전의 역할로 채택**, A 다음 |
| **D. 던전 제거 / 디버그 샌드박스 격리** | 플레이 루프에서 제거하거나 개발용으로만 유지. Oracle의 권고 | **작음** — 진입·격리 정리 비용. 이동 느낌과 아이템 획득 공간을 포기 | P1/P3 위반 경로 차단, P2 중립. P4 강화는 없음 | **미채택** — C가 목적을 부여하므로 유지. 단, C 계약을 지킬 수 없으면 **올바른 대체 경로** |

### 확정한 두 트랙

- [x] **트랙 A** — 런 인터랙션을 먼저 개선한다. 인접 노드를 직접 고르고 통과 방식을 결정한다.
- [x] **트랙 C** — 던전을 추가 아이템 획득용 미니게임으로 유지·재정의한다.
  **진행에 필수가 아니다. 건너뛰기의 비용은 추가 아이템을 얻지 못하는 기회비용이며 처벌이 아니다.**
- [x] **순서 A → C** — A의 결정 어휘와 상태 전이를 C가 재사용한다.
- [x] **B 보류 / D 미채택** — B를 지금 구현하지 않으며, C 계약 미달 시 D로 돌아간다.

### A안의 결정 어휘

먼저 **어느 인접 노드로 갈지** 고르고, 그다음 **어떻게 통과할지** 고른다.

| 행동 | 의미 | 아직 정하지 않은 것 |
| --- | --- | --- |
| `Probe` | 정확한 위협 정보를 드러냄 | 정보 획득 비용·노출 범위 |
| `Bypass` | 더 큰 비용 또는 줄어든 보상을 감수하고 전투 회피 | 대체 비용·보상 감소량·성공 조건 |
| `Breach` | 전투를 치르고 온전한 보상 획득 | 전투·보상 연결의 세부 수치 |
| `Jack out` | 런을 포기하고 이탈 | 정산·손실의 구체 규칙 |

서로 다른 이름으로 같은 강제 전투를 실행하면 A가 아니다. 새 자원 없이 기존 런 자원·도구를
사용하며, 구체 수치와 성공 조건은 열린 질문으로 남긴다.

### B안 분석 보존 — 런은 이미 공간 배치된 던전이다

이전 Draft의 재사용 분석은 **보류안 B의 근거**로 보존한다. 지금의 구현 지시가 아니다.

| 이미 있는 정보·경로 | B안에서 재사용할 수 있는 것 |
| --- | --- |
| `web/src/core/dungeon/dungeon.ts:29-37` — `Room = { id, x, y, w, h, roomType, label }` | 실제 방 좌표·크기·종류·라벨 |
| `web/src/core/dungeon/dungeon_layout.ts:411` — `ProceduralDungeonGenerator` | 런은 `matrix.ts`를 통해 사용하고 크롤러도 가져옴. **생성기는 이미 공유됨** |
| `dungeon.ts`의 `dungeonToMatrix` → `web/src/core/types.ts:315-329`의 `MatrixNode` | 변환 때 **`x/y/w/h/label`을 버리고 그래프만 남김**. 새 생성기보다 버린 정보를 보존하는 접근 가능 |
| `MatrixNode`의 `zone`, `iceIds`, `iceHp`, `reward`, `adjacent`, `eventKind` | 깊이·위협·보상·연결과 combat / discovery / trap / cache / rest / merchant 조우 |
| `dungeon.ts`의 `roomType === "exit"` | 이미 `isBoss` / `wintermute`로 연결되는 보스 방 |

B는 생성된 방·통로를 직접 이동하고 조우 때 Probe / Bypass / Breach / 이탈을 고르는 모델이다.
HP·TRACE·보상·덱은 같은 런에 이월하고 보상 뒤 같은 위치로 돌아온다. 기존 `ZoneDepth`·`roomType`을
위험 대역으로 쓰고, BFS가 아니라 생성된 분기를 거쳐 보스 방에 도달한다.
이는 [ADR-0060](./0060-dungeon-exploration-redesign.md)의 탐색과
[ADR-0103](./0103-dungeon-only-mode.md)의 **던전이 MATRIX의 유일한 렌더러/입력**이라는
원래 결정에 가깝지만, **웹 포트는 그 통합을 구현하지 않았다**.

재검토 시에도 이전 분석의 6조건은 필요하다: **자동 해결 대신 결정 / 죽음은 종결 /
런 상태 이월 / BSP 연결·분기 유지 / FOV와 발각·AI 정보 규칙 일치 / 실효 보상**.
현재 크롤러는 모든 방을 첫 방에 연결하고 (`dungeon_crawler_generation.ts:192-209`),
FOV가 표시 전용이며 AI가 LOS를 무시한다 (`dungeon_crawler_core.ts:85-135`).
생성기 공유는 비용을 줄이는 근거이지 이 공백이 해결됐다는 증거가 아니다.
geometry 보존·런 표시·입력·저장 호환까지 필요하므로 **전체 비용은 여전히 크다**.

## C안 계약 — 4조건

**네 조건을 모두 만족해야 C다.** 별도 게임을 유지한 채 이름만 아이템 미니게임으로 바꾸지 않는다.

| 조건 | 지켜야 할 계약 | 왜 필요한가 / 현재의 반례 |
| --- | --- | --- |
| **1. 유계** | 방 두어 개, 수초~1분 규모. 짧고 독립된 부가 활동으로 끝남 | 한 런 안의 부가 활동이 **두 번째 게임**으로 커지는 것을 막음. 정확한 방 수·시간 상한은 미정 |
| **2. 위험 결정이 실재** | 진입/건너뛰기를 고르고 내부에서도 A의 동사를 재사용한 실제 선택. 이동만으로 자동 전투·자동 수령 금지 | 현재 `web/src/core/dungeon/dungeon_crawler_actions.ts:334-347`은 부딪히면 자동 공격. 픽업 자동 적용·함정 자동 발동·문 자동 열기·계단 자동 하강까지 이동이 해결함. 걷기와 결정·해결을 분리해야 함 |
| **3. 런의 진짜 아이템을 내놓는다** | 프로그램 / wetware / 재료 / 크레딧을 실제 런 상태에 반영. **전투 보상과 차별화** | `web/src/core/dungeon/dungeon_crawler_types.ts:30-46`의 health potion / energy cell / data chip / weapon / armor는 별도이며 대체로 실효가 약한 세트. `dungeon_crawler_actions.ts:116-121`의 weapon·armor 처리 본문은 비어 있음. 전투도 이미 크레딧·재료를 주므로 같은 보상을 더 주기만 하면 중복 |
| **4. 죽음/실패에 실질 비용** | 비치명이라면 아이템 기회 상실·HP 손실·TRACE 상승 등 실제 손실. 치명적이라면 **어디서 죽을 수 있는지와 런 종결을 명시** | `web/src/core/dungeon/dungeon_crawler_actions.ts:49-67`은 죽으면 HP를 절반으로 복구. **P3 “죽음에 진짜 무게” 위반**이며 게임 오버 검사도 좀처럼 발동하지 않게 함. 이를 계승하지 않음 |

**건너뛰기와 진입 후 실패는 다르다.** 건너뛰기에는 진행 손실·강제 피해·벌금을 붙이지 않는다.
진입하기로 한 뒤의 실패 비용과 치명성은 사전에 알려야 한다. 비치명/치명 중 어느 정책인지,
손실 수치와 보상 차별화 방식은 아직 정하지 않았다.

## 측정 공백 — 아이템 공급은 현재 밸런스 하네스에 보이지 않는다

> **핵심 위험: 전투 밖에서 얻은 전력은 현재 `npm run balance`로 검증할 수 없다.**
> 전투 기준선 0.0pp를 C의 보상 안전성이나 ADR-0229 §A1 통과 증거로 제시해서는 안 된다.

`web/scripts/balance_sim.ts:77-125`는 이동을 건너뛰고 전투 노드에 배치하며,
`:131-158`은 전달받은 **고정 덱**으로 전투만 해결한다. PPL 모드도 등급별 덱을 고를 뿐
탐색 중 아이템 획득·덱 변경을 모델링하지 않는다 (`:56-70`).
따라서 C가 과도한 아이템 공급원이 되어도 하네스는 그 전력 증가를 보지 못한다.
[ADR-0229 §A1](./0229-grade-curve-rebaseline.md)의 전후 측정 규율을 무시하는 것이 아니라,
**측정 대상이 빠져 있다는 공백을 별도로 해소**해야 한다.

필수 완화책:

1. **보상 예산을 제한한다.** 런당 획득 상한을 두거나, 특정 자원의 유일한 공급처로 C를 한정한다.
   어느 방식·어느 자원·얼마인지는 미정이다. 무제한 반복 수급을 허용하지 않는다.
2. **효과를 다른 방법으로 검증한다.** ego-lite 실제 플레이 패스, 플레이테스트 또는 새 하네스 모드로
   C 진입/건너뛰기와 획득 전후의 도구·자원·다음 조우 결과를 비교한다. 방법 선택과 구현은 미착수다.
3. **증거를 분리한다.** 기존 전투 코드 변경의 §A1 전후 표와, C 보상이 런 전체에 주는 영향의
   증거를 따로 제출한다. 기존 하네스가 낼 수 없는 §A1 결과를 주장하지 않으며 자동 재보정도 하지 않는다.

## 선행 조건

### TRACE 통합 — 새 자원보다 먼저

`player.alarm`은 0–100 프로그램 비용 누산기이고 `alarmLevel`은 0–5 유휴 알람이다.
플레이어에게 두 개의 서로 다른 “위험”처럼 읽히는 상태에서 새 자원을 더하지 않는다.
**먼저 하나의 가시 위험 계기로 통합**해야 한다. 표시만 덮는 것이 아니라 두 값의 관계·효과를
정해야 하며 구체 병합 방식은 미정이다.
[ADR-0240 열린 질문 (k)](./0240-idle-pressure-and-alarm-loop.md#open-questions)와 연결한다.

### A의 첫 슬라이스 — 그래프 분기 하나를 실제 선택으로

**주도권을 만드는 최소 변경은 분기 하나다.** 전체 탐색 화면이나 B/C를 먼저 만들지 않는다.

- 인접한 **두 목적지**의 위협·보상·TRACE 비용을 보여 준다. Probe로 드러낼 정확한 정보와
  기본 표시의 경계는 별도로 정한다.
- **선택 + 확인**을 요구한다. 확인만 누르면 같은 경로로 흘러가는 동작은 불가하다.
- **그 분기에서** 보스 방향 BFS 자동 라우팅과 보상 후 자동 전진을 제거한다.
- 고정 seed에서 두 목적지를 각각 골라 다른 경로·조우·위험/보상 결과가 나는지 검증한다.
  **이 슬라이스를 검증한 뒤에만 B 또는 C를 만든다.** B는 그 이후에도 보류 상태이며 별도 재검토가 필요하다.

## 순서와 근거

1. **TRACE 관계를 먼저 정리**한다 — 새 위험 자원을 늘리지 않고 같은 위험 언어를 쓴다.
2. **A의 분기 하나 → A의 결정 어휘 검증** — 경로 선택과 Probe / Bypass / Breach / Jack out의
   서로 다른 결과를 기존 그래프·이벤트·전투·런 자원으로 입증한다.
3. **그다음 C** — 검증된 어휘를 짧은 던전 안에서 재사용하고 네 계약과 보상 예산을 검증한다.
4. **A와 C가 루프를 입증한 뒤 B 재검토 가능** — 던전이 런 전체가 되어야 한다는 결론은 내리지 않았다.
   C의 계약을 지킬 수 없다면 D가 올바른 대체 경로다.

**C부터 만들면 고립된 미니게임을 다시 만든다.** A는 본 런의 가장 큰 공백을 최소 변경으로 메우고,
C에 필요한 결정 어휘를 생산한다. C는 런의 약한 P4를 도구 획득으로 직접 보완한다.

## 수락 증거 (Acceptance evidence)

**전부 미실행 — 향후 구현의 수락 기준이지 이번 문서 작업의 실측 결과가 아니다.**

| 검증 축 | 제출할 증거 | 통과 기준 |
| --- | --- | --- |
| TRACE 통합 | 프로그램 사용·유휴 전후의 위험 표시와 상태 전이 기록 | 하나의 가시 위험 계기, 두 누산 값의 관계 설명. 새 위험 자원 추가 없음 |
| A 최소 분기 | 같은 seed에서 두 인접 목적지를 각각 선택·확인한 재현과 회귀 테스트 | 정보가 보이고 실제 경로·조우 결과가 다름. 해당 분기 BFS·보상 후 자동 전진 없음 |
| A 결정 어휘 | 같은 조우의 Probe / Bypass / Breach / Jack out 전이 비교 | 정확한 위협 공개 / 비용·보상 교환으로 회피 / 전투·온전한 보상 / 포기·이탈이 구별됨 |
| C 선택성·유계 | 진입/건너뛰기 비교와 방 수·소요 시간 기록 | 수초~1분·방 두어 개 범위. 건너뛰어도 진행 가능하며 추가 아이템 기회 외 처벌 없음 |
| C 내부 결정 | 내부에서 다른 대응을 고른 재현·회귀 테스트 | A 어휘 재사용. 걷기만으로 자동 전투·자동 보상 해결 없음 |
| C 보상 실효·차별화 | 획득 전후 런 아이템·자원·덱 효과와 다음 조우 기록, 전투 보상 비교 | 실제 런에 반영되고 전투 보상과 다른 목적이 있음. 빈 weapon/armor 처리 재사용 없음 |
| C 실패 비용·P3 | 실패·HP 경계·치명성 안내와 런 결과 재현 | 선언한 손실이 적용됨. 죽음 뒤 HP 절반 복구 없음. 치명적 죽음은 런 종결 |
| 보상 예산·측정 공백 | 런당 상한 또는 특정 자원 공급 제한 검증 + 실제 플레이/새 하네스 전후 비교 | 무제한 아이템 공급 없음. 전투 하네스 밖의 전력 변화를 실제 관측하며 §A1 증거와 혼동하지 않음 |
| 회귀·저장 | 구현 시 관련 테스트·기존 전투 기준선 전후 표·저장 왕복 기록 | 기존 전투 영향은 ADR-0229로 보고. 상태 추가 시 ADR-0185 호환 정책 명시 |

## 열린 질문

1. **TRACE 통합 세부 정책** — 두 값의 변환·효과·표시를 어떻게 통합할 것인가? ADR-0240 (k)는 여전히 미해결이다.
2. **A 비용·정보 규칙** — Probe 비용과 기본 정보, Bypass 비용·보상 감소·성공 조건, Jack out 정산은 무엇인가?
3. **C 경계·진입 위치** — 정확한 방 수·시간 상한·진입 빈도·런 복귀 위치는 무엇인가?
4. **C 보상 정체성·예산** — 전투 보상과 무엇이 다르고, 런당 상한과 특정 자원 유일 공급처 중 무엇을 쓸 것인가?
5. **C 실패·치명성** — 비치명 손실형인가, 어디서 치명적인가? HP·TRACE·아이템 기회의 손실 수치는 무엇인가?
6. **별도 측정 방법** — ego-lite 실제 플레이, 플레이테스트, 새 하네스 모드 중 어떤 방법과 비교 시나리오를 채택할 것인가?
7. **저장 호환·기존 크롤러 진입점** — 상태 이월·이어하기·메뉴 노출을 어떻게 정리할 것인가? B의 geometry 저장 문제는 보류안 재검토 때 다룬다.
8. **Manus second opinion** — 요청했으나 **현재 응답을 받거나 기록하지 않았다**. 자문 완료·동의·검증으로 취급하지 않는다.

## 영향 받는 항목

### 결정의 결과 (Consequences)

- 본 런은 노드 그래프를 유지하고 A에서 결정점을 복원한다. 런 전체 던전화는 현재 범위가 아니다.
- 던전에는 C의 목적과 경계를 부여한다. 별도 아이템 세트·자동 해결·HP 복구를 그대로 통합하지 않는다.
- 선택성·실패 비용·보상 예산을 모두 지켜야 하므로, 비용이 작다는 평가는 무조건적 재사용 승인이 아니다.
- [ADR-0005](./0005-cyberspace-representation.md)의 결정점은 A의 근거다.
  ADR-0060/0103의 원래 던전 방향은 B 분석과 연결하되 현재 웹 통합 승인으로 읽지 않는다.
  **세 ADR 본문과 상태는 그대로 둔다.**

### 구현 시 대상 — 이번에는 변경하지 않음

- `web/src/core/state/state_actions_phases.ts` — 인접 목적지 선택, 대응 선택, 해당 분기의 BFS·자동 전진 제거.
- `web/src/core/dungeon/dungeon_crawler_*.ts`, `web/src/renderer/dungeon.ts`, 입력·메뉴 연결 — 유계 C와 내부 결정.
- 런 아이템·보상·자원·TRACE 상태와 저장 경로 — 실제 효과·실패 비용·호환.
- `web/scripts/balance_sim.ts` 또는 별도 플레이 검증 — 측정 공백 해소 방법은 미정.
- 구현 시 관련 회귀 테스트와 `docs/design/GDD.md`·시스템 명세 동기화. B 전용 geometry 보존·런 타일 렌더러는 보류.

### 이번 문서 작업

- `docs/wiki/decisions/0246-dungeon-role-and-run-interaction.md` — 이름 변경·Draft 전면 재작성·Accepted 기록.
- `docs/wiki/decisions/README.md`, `log.md` — 새 링크·상태·결정 기록 동기화.
- **코드·테스트·기존 디자인 명세·밸런스 수치는 변경하지 않는다.** 커밋하지 않으며 최종 스테이징은 비워 둔다.

## Implementation Status (2026-11-01)

**Status**: 🟡 Partial

**Evidence — slice 1 (historical verification)**:
- `web/src/core/state/state_actions_phases.ts:49-64,118-148` — 화살표로 실제 인접 목적지를 강조하고 확인으로 이동. 보스/입구 BFS 자동 라우팅 제거; 후퇴도 같은 명시적 인접 선택.
- `web/src/core/state/state_actions_phases.ts:218-233` — 비보스 보상 확인은 현재 노드에 남고 목적지 강조를 해제. 기존 15% 회복 유지.
- `web/src/core/types.ts:188-189`, `web/src/renderer/run_screen.ts:36` — 일시적 선택 상태를 실제 런 렌더러에 전달. 저장하지 않으며 기존 상태/세이브의 필드 누락은 미선택으로 처리.
- `web/src/renderer/matrix.ts:83-90,113-115,191-240,290-299` — 현재 노드와 인접 후보를 목록 앞에 배치. 후보별 zone·ICE 개수(0 포함)·크레딧·eventKind를 확인 전에 표시; 방문한 이웃도 선택 가능. 좁은 화면은 충돌하는 현재 노드 보조 패널을 생략하고 후보 정보 유지.
- `web/tests/matrix_route_choice.test.ts` — 기존 코드에서 6개 회귀 실패 확인 후 구현. BFS가 고르지 않는 곁가지, 명시적 후퇴, 보상 후 위치·미선택, 동일 seed의 각 분기, 실제 화면의 선택 강조, 80×50/60×40/40×60 후보 정보 및 재확인 파밍 차단 검증(10 tests).
- `web/src/core/types.ts:192-194,432-433` — `clearedEncounterNodes?: ReadonlyArray<number>`를 런/SaveSlot에 추가. 방문은 전투 전 이동에서도 기록되므로 `visitedNodes`와 분리.
- `web/src/core/state/state.ts:164-176` — 두 전투 해결 경로의 공통 reducer 경계에서 `loot` 진입 시 현재 노드의 조우 완료를 기록. 전투 메커닉·보상 수식·RNG는 변경하지 않음.
- `web/src/core/state/state_actions_phases.ts:65-70` — 완료한 노드에서 목적지 미선택 확인은 안내만 반환하며 조우를 재생성하지 않음. 목적지를 선택한 이동은 여전히 가능.
- `web/src/core/state/state.ts:264,367`, `web/src/save/storage.ts:256-262`, `web/tests/save_load_roundtrip.test.ts:30-101` — 완료 목록 저장/복원 및 저장 경계 검증. 기존 version-1 세이브는 필드가 없어도 로드되며 빈 완료 목록으로 복원(ADR-0185); 저장/CONTINUE 후 재진입 차단·구형 슬롯·잘못된 목록 검증.
- `web/tests/matrix_route_choice.test.ts:145-214` — 노드 진입 → 전투 해결 → 보상 확인 → 재확인/프로그램 사용 시도. ICE HP 1/12 두 경우 모두 수정 전 `expected 'combat' not to be 'combat'` 실패 관측, 수정 후 통과; 추가 크레딧·재료 없음 단언.
- `web/tests/matrix_navigation.test.ts` — 53개 미션의 모든 노드/인접 선택에서 보스 경로·양방향 연결 유지, 명시적 선택+확인으로 보스 도달 검증.
- `web/e2e/menu-nav.ts:46`, `web/e2e/continue.spec.ts:194` — ICE까지 인접 경로를 선택+확인하도록 헬퍼/CONTINUE 입력 검증 갱신. 실제 이동 및 선택한 목적지 일치 단언 유지.
- `npm run typecheck`, `npm run lint`, `npm test`, `npm run build` — 타입 오류/린트 오류 0, 기존 keyboard 경고 1개, **161 files / 3658 tests** 통과(기존 3649 + 회귀 9), 빌드 통과. 별도 경로/저장 왕복 4 files / 39 tests 통과.
- `npm run balance`, `npm run balance -- --deck ppl` — opening `100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0`, PPL `100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7`; 수정 전후 양 덱 **전체 stdout을 `cmp`로 byte-identical 확인**. 아래 측정 한계와 구분한다.
- `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots` — `npx vite preview --port 5195 --strictPort --host 127.0.0.1`로 실행, **76 passed / 4 skipped / 0 failed** (4.5m), 재시도 없이 통과. preview 종료 후 5195 리스너 없음 확인.

**Evidence — slice 2 (fixed verbs, 2026-11-01)**:
- `web/src/core/state/encounter_verbs.ts:8-20,39-149` — 고정 PROBE / BYPASS / BREACH / JACK OUT 목록과 reducer. PROBE **8 COST**, BYPASS **60 COST** (아래 오너 가격 변경 반영), 기존 누산 상한 **100**을 한 상수 블록 `ENCOUNTER_VERB_COSTS`에서 공유. 초과 결제는 거절하고 이미 공개한 PROBE는 재청구하지 않는다. HP·TRACE 비용 및 새 화폐 없음.
- `web/src/core/state/encounter_verbs.ts:23-37,69-128` — PROBE의 정확한 ICE 식별자(catalog id)·HP는 BREACH와 같은 roster 계산을 사용한다(ICE_X2·최대 4개·기존 grade HP fallback 포함). BREACH는 기존 approach → combat·VFX 진입·보상 경로를 그대로 재사용. BYPASS는 전투·보상·회복 없이 현재 노드에서 이동 가능 상태로 돌아가며 완료 목록에 기록하지 않는다.
- `web/src/core/state/state_actions_phases.ts:44-96` — 현재 노드의 미완료 ICE를 해결하거나 이번 방문에서 BYPASS를 결제하기 전에는 출발 확인도 결정 메뉴를 연다. 목적지를 먼저 골라 무료로 떠나는 우회 차단. 이동하면 결제 통과 플래그를 초기화하여 재방문의 재통과도 무료가 아니다.
- `web/src/core/types.ts:190-197` — 메뉴 선택·공개 정보와 이번 방문의 통과 상태는 선택적 일시 필드. 저장 스키마를 늘리지 않으며 기존 세이브에서 누락 허용. 이동/로드 시 공개 정보·통과 허가는 유지하지 않는다. 기존 `clearedEncounterNodes` 저장 계약은 불변.
- `web/src/renderer/encounter.ts:12-90`, `web/src/renderer/run_screen.ts:26-45` — 기존 Green Grid 프레임에 자원·보상 → 네 동사와 가격/차단 상태 → 유료 위협 정보를 표시. 미완료 노드의 기존 CURRENT NODE HP 미리보기도 숨겨 무료 PROBE 누출 차단. 40×60 / 60×40 / 80×50에서 네 동사·정확한 HP 공개 회귀.
- `web/tests/encounter_verbs.test.ts:81-322` — **18 tests**: BYPASS 무전투·무보상·무회복·유료, PROBE 유료·정확한 ICE/HP·중복 청구 없음, BREACH 기존 전체 보상, 우회 후 이동·재방문·BREACH, 완료 노드 파밍 금지, 선택 없는 재확인 무효, 무료 출발 차단, COST 초과 거절/정확히 100 허용, 실제 프로그램 사용 여력 소진, ICE_X2 정보 일치. 구현 전 최초 13개 중 **12 failed / 1 passed**, 구현 후 전부 통과. 보상 fixture는 기존 기본 50 + 노드 75 = **125 credits**를 단언하며 수식은 변경하지 않았다.
- `web/tests/encounter_test_helpers.ts:4-10` 및 기존 전투 진입 회귀 — Enter-only setup 대신 실제 화살표+확인으로 BREACH 선택. 기존 전투·HP·보상·VFX·저장 단언 보존. 경로 도달성 fixture는 완료한 그래프를 걸어 경제와 분리하고, 별도 유료 통과/재방문 회귀가 새 계약을 검증한다.
- `web/e2e/menu-nav.ts:48-104`, `web/e2e/continue.spec.ts:192-217`, `web/e2e/encounter_verbs.spec.ts:19-114` — 결정 메뉴 진입·명시적 동사 선택 헬퍼. CONTINUE 후 미완료 노드 이동도 BYPASS를 결제한 뒤 기존 목적지 일치·실제 이동 단언을 유지. SFX / status / IDB / matrix / demo setup도 이 입력으로 이관. 새 브라우저 회귀는 무선택 재확인·PROBE→BYPASS·무보상·이동·네 방향 선택·기존 JACK OUT 결과를 검증.
- `web/scripts/balance_sim.ts:122-130` — 하네스는 그래프를 걷지 않지만 첫 전투 진입에 reducer confirm을 쓰므로, setup에 BREACH 선택 입력만 추가했다. **추가 clock/RNG 진행 없음**. 전투 루프·튜닝·RNG·결과 집계는 변경하지 않았다. 파일 자체가 무변경이라고 주장하지 않는다.
- 검증: `npm run typecheck` **0 errors**; `npm run lint` **0 errors / 기존 keyboard.ts:14 warning 1**; `npm test` **162 files / 3682 passed / 0 failed** (baseline 161 / 3664 + 새 파일 18 tests); `npm run build` 통과(119 modules). 편집한 src 파일만 Prettier write/check 통과, repo-wide format 없음. LSP는 TypeScript 서버 미설치·기존 설치 거절로 실행 불가이며 CLI 검증과 구분한다.
- 양 덱 수정 전후 **전체 stdout `cmp` exit 0 (byte-identical)**. Opening `100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0`, PPL `100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7`. 턴·HP·percentile도 동일. 이는 **전투 하네스 동작 보존** 증거이지 경로 경제 밸런스 증거가 아니다.
- 전체 E2E: 필수 IPv4 preview + `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots` → **80 passed / 4 skipped / 0 failed (4.4m)**. 최초 실행의 CONTINUE 무료 출발 가정과 신규 JACK OUT의 state-null 가정 수정 후 통과. 마지막 좁은 화면 힌트 줄바꿈만 짧게 바꾼 뒤 build + 새 동사 E2E **4 passed**로 캡처 갱신. 매 실행 finally에서 preview 프로세스 그룹 종료.

**Evidence — terminal BYPASS guard (2026-11-01)**:
- `web/src/core/state/state_actions_phases.ts:164-167`의 실제 완료 조건은 `node.isBoss || node.adjacent.length === 0`이다. 전투 뒤 loot 확인만 런을 완료하므로 이 조우는 BYPASS로 진행할 수 없다. `dungeon.ts:243-248`의 인접 목록은 양방향이며, 이웃 하나가 있는 비보스 곁가지는 후퇴가 가능하므로 차단하지 않는다.
- `web/src/core/state/encounter_verbs.ts`의 `bypassBlockReason`을 reducer와 `web/src/renderer/encounter.ts`가 공유한다. reducer는 결제·통과 플래그 설정 전에 거절하며 메뉴는 기존 순서를 유지하고 `BYPASS +60 COST BLOCKED`와 `Must BREACH to complete the run.` / `Must BREACH: no adjacent route.`를 선택 전에 표시한다. 가격 표시는 공유 상수를 읽으므로 오너 가격 변경도 반영한다. 선택 후 확인도 같은 이유로 거절한다. PROBE/BREACH/JACK OUT은 유지하고 PROBE 후 안내도 가능한 동사만 권한다.
- `web/tests/encounter_bypass_eligibility.test.ts` — 보스/인접 0개 직접 BYPASS 거절·무결제·미완료·통과 불가, 80×50/60×40/40×60 사전 안내, PROBE/JACK OUT, 실제 보스 이동 → BREACH → combat → loot → ending 및 비보스 terminal 완료를 검증한다. 수정 전 **8 failed / 24 passed**, 수정 후 기존 동사 회귀(정상 BYPASS·no-farming 포함)와 합쳐 **32 passed**.
- 최종 검증: `npm run typecheck` **0 errors**, `npm run lint` **0 errors / 기존 keyboard.ts:14 warning 1**, `npm test` **163 files / 3696 passed / 0 failed**, `npm run build` **119 modules** 통과. 첫 typecheck가 새 fixture의 필수 `arc` 누락을 발견해 보완한 뒤 통과했다. 편집한 src만 Prettier write/check; LSP는 서버 미설치·기존 설치 거절로 실행 불가.
- 양 덱 수정 전후 전체 stdout **`cmp` exit 0 (byte-identical)**: opening `100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0`, PPL `100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7` (ADR-0239 기준선 유지). 이는 전투 하네스만 검증한다.
- `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots` → **80 passed / 4 skipped / 0 failed (4.4m)**. 기존 5195 preview를 종료하지 않고 새 dist로 검증했다. 별도 브라우저 fixture에서 390/1440px 보스·인접 0개·일반 노드를 각각 캡처하고 실제 키로 BYPASS 확인: 앞 둘 COST 0 유지 + 이유 안내, 일반은 당시 가격으로 결제 (현행 60 검증은 아래 별도 기록). 사용자 play session은 조작하지 않았다. WCAG 전체 적합성은 주장하지 않는다.

**Evidence — E first slice: utility 카드로 결제하는 SCAN (2026-11-01)**:
- 범위는 [보충 ADR-0247 옵션 E](./0247-dungeon-role-supplement-manus-second-opinion.md#옵션-e--소모성-프로그램으로-만드는-노드-결정-계층)의 **정보 공개**부터다. 현재 선택한 미완료 ICE 노드의 정확한 위협을 드러내는 SCAN을 고정 동사 뒤에 겹친다. 인접 그래프 전체 스캔·노드 잠금·가짜 신호·추적 지연을 구현했다고 주장하지 않는다. BREACH/JACK OUT은 카드 없이 유지하고 고정 PROBE **8 COST** / BYPASS **60 COST** (가격 후속 변경 반영), terminal 차단·보상·완료 기록은 불변이다.

| 실제 catalog role / tier | 이번 encounter capability | catalog 근거 / 판단 |
| --- | --- | --- |
| `utility`: T1 `probe`, `scan`; T2 `decrypt`, `trace`; T3 `echo` | **SCAN** — 현재 조우의 정확한 ICE id/HP 공개, 손의 첫 matching 카드 소비 | `web/src/data/programs.json:29-35,122-138,151-168`: weakness/stats 공개, ICE protection 해독, 위치 추적, nearby ICE 탐지/유인이라는 정보·정찰 계열. Echo의 개별 유인 효과를 구현한 것이 아니라 공유 utility 역할을 정보 획득으로 해석했다. |
| `guard` T1–T4 | 새 capability 없음 | `programs.json:2-9,20-27,64-71,82-120,140-149`: 방어/회피. 새 deny 효과나 지속시간을 임의로 만들지 않음. |
| `strike` T1–T3 / `burst` T2·T3·T5 | 새 capability 없음 | `programs.json:11-18,37-62,73-80,170-208,267-285`: 공격 계열은 기존 combat 용도로 보존. |
| `support` T1–T2 | 새 capability 없음 | `programs.json:210-265`: 보조/회복 계열이며 미확정 시간·회복 수치를 encounter에 추가하지 않음. |

- **Tier 정책**: 실제 utility T1–T3 모두 같은 질적 정보 공개 도구다. tier 문턱·공개 개수·효과 배율·새 숫자 가격을 추가하지 않는다. 높은 tier는 combat에서 잃는 카드의 가치가 다를 뿐이다. 기존 다섯 role 외 새 role은 만들지 않았다.
- `web/src/core/state/encounter_verbs.ts:15-34,92-108` — 고정 네 동사의 순서 뒤 SCAN 추가. renderer/reducer가 `encounterScanProgram`을 공유해 **현재 손 `state.deck`의 첫 utility**만 결제 대상으로 삼는다. draw/discard/inventory 소유만으로는 사용 불가. 확인 시 해당 index의 카드 **한 장만** 제거하고 같은 객체를 `discardPile`에 append하며 `probed: true`를 설정한다. COST·HP·TRACE·보상·combo·turn·RNG는 건드리지 않고 새 카드를 뽑지 않는다. PROBE와 공개 상태를 공유해 공개 후 SCAN/PROBE의 재결제를 막는다.
- **공유 경계 보존**: `web/src/core/data_loaders.ts:212-242`의 `parseProgram`은 현재 `role`을 반환하지 않는다. combat은 `web/src/core/combat/state_actions_programs.ts:83-99`에서 optional role과 `countRoleSynergy` (`combat_engine.ts:224-231`)를 읽는다. loader에 role을 복원하면 damage/crit 분기까지 바뀔 수 있으므로, 이번에는 **encounter에서만 catalog id → authored role**을 조회한다. loader·Program 타입·combat 코드는 변경하지 않았다.
- **실제 교환 / 비지배성의 구조**: PROBE는 COST를 쓰고 combat 손패를 보존한다. SCAN은 COST 여력을 보존하지만 실제 combat 카드와 그 play의 damage/combo/Dixie 기회를 포기한다. `state_actions_programs.ts:49-65`의 같은 손에서 카드를 못 찾고, `state_actions_combat.ts:68-71,123-139`의 **기존 성공한 combat play 이후 재순환** 전에는 돌아오지 않는다. 영구 삭제나 전투 전체 사용 금지는 아니다. 탐색에서 손을 전부 소비해도 encounter 진입 시 자동 보충하지 않으므로 빈 손으로 BREACH할 위험이 있다. 따라서 SCAN을 무료 정보나 탐색 전용 카드로 만들지 않았다. 이는 구조 설명이며 정량 밸런스 입증은 아니다.
- `web/src/renderer/encounter.ts:42-103` — 기존 Green Grid 프레임·줄바꿈·색상 토큰·화살표/확인 유지. `SCAN PROGRAM` + `Discard <name> (T<tier>)` + combat 카드 상실 안내, 없으면 `SCAN NO UTILITY IN HAND`와 필요 역할 표시. 사용 불가 안내 행은 남기되 실행은 거절한다. 공개 뒤 `REVEALED` / no payment로 전환. `state_actions_phases.ts:143-148`의 기존 combat-only 안내도 SCAN과 일치시켰다.
- `web/tests/encounter_programs.test.ts:86-269` — **21 tests**. 실제 catalog utility 다섯 장 전부·네 비utility 역할·draw/discard/inventory-only 소유·중복 id 단일 소비·COST cap에서도 카드 결제·즉시 combat 재사용 거절·PROBE/SCAN 중복 청구 없음·고정 8/60 COST (가격 후속 변경 반영)·무보상/no-farming 검증. **수정 전 신규 16 failed / 5 passed, 기존 32 passed → 수정 후 합계 53 passed**는 당시 SCAN 구현 기록이다. 40×60 / 60×40 / 80×50에서 결제 카드·없음 상태·정확한 HP·입력 힌트가 프레임 내에 보임을 검증한다.
- `web/e2e/encounter_verbs.spec.ts:114-173` — real catalog 카드를 손에 넣는 fixture 후 실제 ↑/Enter로 SCAN 선택/결제, 손에서 제거·discard 이동·COST 불변, 무료 중복 PROBE, BREACH 후 손패 손실을 desktop/mobile 모두 검증한다. 최초 E2E 수집의 Node JSON import attribute 오류를 spec import에 `with { type: "json" }`로 보완했다. 기존 테스트 삭제/약화 없음.
- 검증: 편집한 **src 세 파일만** Prettier write/check, `npm run typecheck` **0 errors**, `npm run lint` **0 errors / 기존 keyboard.ts:14 warning 1**, `npm test` **165 files / 3731 passed / 0 failed** (baseline 164/3710 +21), `npm run build` **119 modules** 통과. TypeScript LSP는 미설치·기존 설치 거절로 실행 불가였으며 CLI 결과와 구분한다.
- `npm run balance` / `npm run balance -- --deck ppl`: 전후 전체 stdout **양 덱 `cmp` exit 0 (byte-identical)**이며 기존 slice-2 baseline 캡처와의 `cmp`도 모두 0. ADR-0239 opening **100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0**, PPL **100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7** 유지. `/Users/emilio/.openclaw/tmp/opencode/option-e-{opening,ppl}-{before,after}.txt`에 전체 stdout 보존. **`balance_sim.ts:77-81,100-130,136-161`은 그래프를 걷지 않고 고정 덱으로 BREACH하므로 E의 밸런스는 미검증이다. 이 결과는 combat harness 보존만 증명한다.**
- 필수 E2E 명령 `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots` → **82 passed / 4 skipped / 0 failed (4.6m)**. 새 spec의 desktop/mobile 2건 증가. **5195의 기존 preview를 kill/restart하지 않고 유지**했으며 rebuilt dist의 SCAN을 실제 브라우저와 E2E에서 확인했다.
- 별도 QA 브라우저에서 390×844 / 844×390 / 1440×1000의 unavailable/ready/revealed **9개 캡처** 및 실제 키 확인: 없는 카드는 거절, SCAN 후 손 `[strike]` / discard `[scan]` / COST 0 / probed true. 캡처는 `/Users/emilio/.openclaw/tmp/opencode/option-e-{390,844,1440}-{unavailable,ready,revealed}-after.png`, 전 편집 baseline은 `option-e-{390,1440}-before.png`. 실제 layout은 각각 40×60 / 80×32 / 100×60이며 요구된 세 grid 프리셋의 단위 검증과 구분한다. 사용자 play session 무조작. 기존 Canvas/작은 HUD의 접근성 한계가 있으며 WCAG 전체 적합성을 주장하지 않는다. 독립 read-only reviewer 호출 두 건은 도구의 `No assistant or tool response found` 오류로 결과를 얻지 못했으므로 독립 승인으로 기록하지 않는다.

**Evidence — 오너 가격 결정: BYPASS 60 (2026-11-01, 이전 가격 이연 종결)**:
- 오너가 **BYPASS 30 → 60**을 확정했다. PROBE **8**·상한 **100**·HP·TRACE·보상·회복·동사 의미는 그대로다. `web/src/core/state/encounter_verbs.ts:11`의 가격 한 값만 바꾸며 renderer는 같은 상수를 읽는다.
- 판단 입력은 오너의 **실제 play pass**와 전투당 g1–g5 약 **12 / 57 / 86 / 95 / 95 HP** 손실이다. 예전 BYPASS는 100 COST 중 30으로 g3–g5의 피해를 피하므로 저평가 가능성이 높았다. 서로 다른 자원(COST 대 HP 대 정보/보상)을 교환하는 **구조적 비지배성**은 유지되며 HP와 COST를 동일 단위로 취급하지 않는다.
- `log.md`의 기존 **decision-support | 동사 가격 평가 — Jev choice** 결과가 독립 입력이다: `keep_30` **0.03**으로 유지안 배제, `raise_45` **0.43** / `raise_60` **0.41**, confidence **0.29**로 사실상 동률. 자동 선택이나 60의 정량 검증이 아니라 **오너가 동률을 해소해 60을 선택**했다. 이번 구현에서 Jev를 재호출하지 않았다.
- **검증된 결과: 60은 BYPASS를 런당 최대 한 번의 자원으로 만든다.** `state_actions_programs.ts:59-62,382`와 `encounter_verbs.ts:121-129`는 COST를 더하고 초과 결제를 거절한다. `state/state.ts:255,287`은 저장/복원 시 그대로 보존하며, 감소 경로는 없고 `state_actions_phases.ts:259-265`의 same-jockey 사망 재시작만 0으로 초기화한다. 30이면 세 번(90), 45이면 두 번(90)이지만 60이면 한 번(60); 두 번째는 **120 > 100**이라 결제·통과 없이 거절된다. 다른 지출이 먼저 있으면 첫 BYPASS도 불가능할 수 있다.
- `web/tests/encounter_verbs.test.ts`의 새 회귀는 COST 0에서 첫 BYPASS 성공·60 결제 → 이동·재방문 → 두 번째 거절·60 유지·통과 허가 없음·무료 출발 불가를 실제 reducer 입력으로 검증한다. 기존 정확히 상한 허용/초과 거절 fixture는 BYPASS 전 COST **40/41**로 옮겨 경계 단언을 유지했다. 가격 단언·SCAN 고정 가격·E2E PROBE+BYPASS 합계는 각각 **60 / 60 / 68**로 갱신했다. 가격 변경 전 focused run은 **7 failed / 33 passed**로 새 계약의 실패를 확인했다.
- `web/scripts/balance_sim.ts:77-81,100-130,132-162`는 그래프를 걷지 않고 고정 덱으로 BREACH하는 단일 전투 하네스다. **byte-identical balance는 변경이 경로 경제에 국한됨과 combat harness 보존만 입증**하며, 새 가격 60의 밸런스를 검증하지 못한다. 새 가격의 실제 런 검증은 별개다.
- **가격 변경 검증**: `npm run typecheck` **0 errors**, `npm run lint` **0 errors / 기존 keyboard.ts:14 warning 1**, `npm test` **165 files / 3732 passed / 0 failed** (baseline 3731 + 회귀 1), `npm run build` **119 modules** 통과. 편집한 src 한 파일만 Prettier write/check 통과, repo-wide format 없음. recorder의 `node --test docs/playtest/ego-decision-recorder.test.mjs` **6 passed**. 실제 catalog 프로그램 **30개 전부 유한·비음수 비용 (최소 1)**임을 실행으로 확인했다. LSP 호출은 TypeScript 서버 미설치·기존 설치 거절로 진단 불가였으며 CLI typecheck와 구분한다.
- **양 덱 전체 stdout `cmp` exit 0**: 기존 ADR-0239 기준선 캡처 `option-e-{opening,ppl}-before.txt`와 새 `bypass60-{opening,ppl}.txt`를 `/Users/emilio/.openclaw/tmp/opencode/`에서 byte 비교했다. Opening **100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0**, PPL **100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7**, 턴·HP·percentile까지 동일. 가격 밸런스 검증으로 해석하지 않는다.
- **E2E**: `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots` → **82 passed / 4 skipped / 0 failed (4.5m)**, desktop/mobile 모두 새 **68 COST** 합계 단언 통과. rebuild 뒤 요청된 `npx vite preview --port 5195 --strictPort --host 127.0.0.1`는 **Port 5195 is already in use**로 새 기동을 거절했다. 기존 서버는 kill하지 않고 유지했고, 그 서버가 새 dist를 제공함을 E2E로 확인했다. 사용자 play session은 조작하지 않았다.

**Notes**: ADR-0195의 Status / Evidence / Notes 형식이다. **Accepted는 결정 완료이지 구현 완료가 아니다.**
첫 슬라이스의 **경로 결정**과 두 번째 슬라이스의 **고정 동사 결정** 위에 E의 **카드 결제 SCAN**을 겹쳤다. 경로 목록에서 ↓/→는 다음 후보, ↑/←는 이전 후보, Enter/Space는
강조한 목적지로 이동하며 이동 뒤에는 미선택으로 돌아간다. 미완료 ICE를 아직 통과하지 않았다면 출발 확인도 결정 메뉴를 연다.
메뉴도 **초기 선택 없음**이며 ↓/→는 PROBE → BYPASS → BREACH → JACK OUT → SCAN 순, ↑/←는 역순으로 순환한다.
Enter/Space로 강조한 동사만 실행한다. PROBE 후에는 같은 메뉴에서 다른 동사를 고르며,
BYPASS 뒤에는 현재 노드에서 인접 목적지를 다시 선택한다. 목적지 없는 확인으로 재개한 메뉴에서 BREACH도 가능하다.
BREACH 확인은 기존 approach로 진입하고 다음 확인이 교전한다. ESC/Q 및 메뉴의 JACK OUT은 기존 matrix 이탈 결과(`phase: menu`)를 유지한다.
**기존 한계 관측**: 이 결과는 컨트롤러의 state-null/제목 화면 복귀를 뜻하지 않는다. 현재 main.ts는 matrix를 계속 그리며, 이번 범위에서 JACK OUT 정책/컨트롤러를 재설계하지 않았다.
기존 목록·화살표·확인 입력을 재사용하여 새 단축키나 공간 지도를 추가하지 않았다.
실제 절차 생성 그래프는 DAG가 아니라 양방향 연결 그래프다 (`dungeon.ts:243-247`, `dungeon_layout.ts:444-447`).
막다른 곁가지에서도 방문한 이웃으로 돌아갈 수 있어 보스 도달성을 보존한다. 자발적 재방문은 허용하지만
자동 2-cycle이나 자동 목적지 선택은 없다. 모든 선택에서 보스 경로가 남는 것을 전 미션 회귀로 검증했다.
**검증이 발견한 파밍 구멍**: 보상 뒤 같은 노드에 남으면서 완료 상태가 없어서 확인만으로 전투·보상을 무한 반복할 수 있었다.
완료 목록을 기록/강제하여 막았다. `balance_sim.ts`는 그래프를 걷지 않고 조우를 직접 구성하므로 이 구멍을 볼 수 없다.
양 덱 0.0pp/byte-identical은 전투 기준선 보존 증거일 뿐 **런 보상 경제의 무결성 증거가 아니다**; 위 red/green 경로 회귀가 해당 결함의 검증이다.
구형 세이브에는 완료 이력이 없으므로 추측하여 방문 노드를 완료 처리하지 않는다. 누락은 빈 목록이며 이후 해결한 조우부터 기록/저장한다.
**가격의 의미/측정 한계**: PROBE 8은 작은 정보 투자, BYPASS 60은 COST 상한 100과 런 중 단조 증가 때문에 런당 최대 한 번만 쓸 수 있는 회피다.
BREACH는 이 추가 비용 없이 전투 피해 위험을 감수하고 기존 보상·salvage HEAL을 얻는다. 낮은 HP/위험한 ICE에서는 회피,
여력이 있거나 보상이 필요하면 전투가 이득인 구조이며 무료 이동 우회도 막았다. **8/60은 현행 가격이며 60은 오너 결정이지 비지배 전략의 정량적 실측 입증이 아니다**.
`balance_sim.ts`는 경로·연속 BYPASS·PROBE를 측정하지 않으므로 이 수치를 검증할 수 없다. [ego-lite 실제 플레이 절차](../../playtest/EGO_LITE_PLAY_CHECK.md)를
새 입력(경로 선택+확인 → 메뉴 → 동사 선택+확인)에 맞춰 실제 런에서 수행해야 한다. 이번에는 그 play pass를 실행하지 않았다.
메뉴 공개/통과 허가는 일시적이므로 이동·로드 뒤 다시 PROBE/BYPASS할 때 재결제되며, 완료 기록으로 오인하지 않는다.
TRACE 표시 통합(a)은 ADR-0248에서 Deferred이고 a0는 이름만 분리했으므로 단일 계기 선행 조건은 여전히 미충족이다.
E의 utility SCAN 첫 슬라이스만 구현했다. 나머지 E 예시, C 계약·보상 예산·측정 공백 해소는 미구현이며 **🟡 Partial**을 유지한다. 별도 던전의 독립 정리 2건은 ADR-0247의 상태 주석에 기록되어 있고 런 반영/격리 재정의는 남아 있다. 이번에는 크롤러·본문·기존 ADR-0005/0060/0103/0247/0248 결정을 변경하지 않았다.
LSP 서버는 미설치이며 기존 설치 거절을 존중하여 실행하지 못했다; TypeScript CLI 검증은 통과했다.
**검증 중 발견 (설계 관찰)**: E의 매핑은 실제 카탈로그에 존재함을 확인했다 — `programs.json` 의 role 분포는
`guard 8 · strike 8 · utility 5 · burst 3 · support 6` 이고 utility id 는 정확히 `probe · scan · decrypt ·
trace · echo` 다 (에이전트가 역할을 발명하지 않았다). **다만 오프닝 덱 5장은 전부 non-utility**
(`backdoor`=strike, `barrier`/`cloak`/`decoy`=guard, `boost`=support) 이므로 **새 런에서는 SCAN 이 한 번도
보이지 않는다**. Pillar 4("내가 뭘 할 수 있는가가 빌드에 달린다")에는 부합하지만, **발견 가능성(discoverability)**
문제다 — 유틸리티 프로그램을 얻기 전까지 플레이어는 E의 존재를 알 수 없다. 해소 방향(오프닝 덱에 유틸리티 1장
포함 / 덱 구성 화면에서 안내 / 그대로 두고 덱빌딩 보상으로만 노출)은 **오너 결정 대상**으로 남긴다.

## 변경 이력

- 2026-11-01: 초기 **Draft** — 던전 이동 기반 런이라는 단일 방향, 공간 정보 보존·6조건·조우 모델 추천을 기록. 오너 선택 전 문서였고 구현은 없었음.
- 2026-11-01: **오너 결정 반영 → Accepted**. 이전 단일 방향 Draft를 전면 재작성하고 역할에 맞게 파일명 변경.
  **A → C**, 던전 역할 C 채택·B 보류·D 미채택 및 계약 미달 시 대체 경로를 기록.
  B 분석 보존, C 4조건·아이템 측정 공백·TRACE 선행·최소 분기 수락 기준 추가.
  Manus 응답 미수신·미기록을 명시. 구현 **❌ Not started**, 코드·테스트 변경 없음.
