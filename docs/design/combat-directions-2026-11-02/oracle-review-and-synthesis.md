# Oracle 검증 + 합성 — 전투 화면 인터랙션 (이해·선택 + 가시적 효과)

> 출처: Oracle (read-only) 검증, 2026-11-02. 세션 `ses_e64c283bcffeA57xg6yJQp7GTL`.
> 검증 대상: [`manus-concepts.md`](./manus-concepts.md) (Manus 8안, `task SgZpe9qegQaHjJSSHUkuVR`).
> Oracle은 read-only이므로 이 파일은 오케스트레이터가 Oracle 출력을 그대로 옮겨 저장했다.
> **이 문서는 채택 전 게이트다.** 여기 적힌 규칙을 만족하지 못하는 안은 구현하지 않는다.

**Effort**: 첫 슬라이스 Short · 전체 Inspect 인터랙션 Medium (오너 결정 후) · **Confidence: High** (코드 + Accepted ADR 직접 확인 기반).

---

## Bottom line

**`PROGRAM INSPECT`를 먼저 구현하되, 제안된 2단계 상호작용이 아니라 "진실한 프로그램 라벨"부터 시작한다.**
효과(가시적) 쪽은 **`SIGNAL BURST`의 누락 이벤트 부분집합**을 먼저, 그 뒤 제한적인 `READABLE IMPACT`.
**`COMBAT LEDGER`는 이미 존재하므로 삭제한다.**

---

## 중복·충돌·실현성 판정

| 안 | 판정 | 실현성 및 필요한 작업 |
|---|---|---|
| **1-1 `PROGRAM INSPECT`** | **DUPLICATE + CONFLICT** | ADR-0003의 메뉴/화살표/Enter/취소 모델과 Matrix 규칙 3의 select→confirm 패턴을 반복한다. 그러나 최신 [ADR-0243](../../wiki/decisions/0243-digit-key-repeat-policy.md)의 "**숫자 1회 = 카드 1장 실행**"과 **충돌**한다. 전체 구현은 일시적 `selectedProgramIndex`, 리듀서의 select/confirm/cancel, 렌더러 상세, 키보드·터치·게임패드 변경이 필요하다. 상태는 **세이브에서 제외되는 일시 필드**가 바람직하며 스키마 버전 증가 없음. 하네스는 `use_program`을 직접 보내므로(`balance_sim.ts:136`) 그 액션을 건드리지 않으면 **byte-identical 유지 가능** |
| **1-2 `CARD RAIL`** | **CONFLICTS (as written)** | 수동 ASCII 카드는 가능하지만 카드 툴킷이 없다. 현재 캔버스는 짧은 ID 한 줄만 그린다(`combat_grid.ts:237`). 가로 카드 4장은 **40×60에서 스크롤/랩 없이는 불가** → "스크롤 없음" 계약 위반. 선택 상태·입력 재작성도 동일하게 필요 |
| **1-3 `TARGET FIRST`** | **NEW** | 기존 `activeIceIndex` + `Tab` 순환이 재사용 가능(`state_actions_combat.ts:112`). 타겟 분석은 새 상태 없이 가능. 그러나 **"적용 가능/조건부/불가"는 불가** — 적용성 모델이 없고 모든 프로그램이 같은 피해 경로를 탄다. 표시 전용이면 Short, 실제 적용성/효과면 Large + 밸런스 민감 |
| **1-4 `COMMAND DECK`** | **DUPLICATE + CONFLICT** | `PROGRAM INSPECT` + 터미널 문구 + Y/N 바인딩. ADR-0003 중복, Enter/Space 확인 및 ADR-0243의 즉시 실행과 충돌. 선택 상태·새 키 매핑·터치/게임패드 정합·e2e 재작성 필요. **Y/N 계층은 버린다** |
| **2-1 `EVENT GRAMMAR`** | **DUPLICATE + 새 잔여** | 분류·지속·오버레이·전투 로그·타겟 글리프·떠오르는 피해·보스 페이즈 VFX는 ADR-0210/0231/0232/0234로 **이미 존재**. 새 작업은 **상태 부여·만료·COST/크레딧/루트 델타·누락 음향**뿐. `status_apply`는 이미 렌더 구현이 있고(`combat_vfx_render_combat.ts:189`), 만료는 **조용히 버려진다**(`status.ts:60`). 새 영속 상태·이벤트 버스 불필요 |
| **2-2 `COMBAT LEDGER`** | **DUPLICATE — 이미 출시됨** | `combatLog`는 이미 최신순·상한 8(`types.ts:173`), HUD가 최근 4줄 표시(`state.ts:231`). 저장에서 의도적 제외. **백로그에서 삭제** |
| **2-3 `SIGNAL BURST`** | **DUPLICATE + 유효 잔여** | 일반 피격/사망/승리·보스 페이즈 신호는 이미 존재(`state_actions_combat.ts:438`). **누락은 상태 부여/만료 + 미배선 음원**(`manager.ts:33`) — 작고 유용한 잔여 슬라이스. 세이브/상태 형태 변경 없음 |
| **2-4 `READABLE IMPACT`** | **NEW** | 컨트롤러/렌더러의 **표시용 스냅샷·데드라인**이며 `GameState`가 아니다. 권위 있는 숫자(HP/COST)는 **즉시 스냅**하고, **뒤따르는 바/고스트 세그먼트/명시적 `-21`·`COST +12` 마커만** 애니메이션. `COST 44` 같은 중간 숫자는 **거짓 상태**이므로 권위 값으로 표시 금지. 세이브 변경 없음, reduced-motion은 즉시 스냅 |

### 숨은 밸런스 위험

**표시하려고 JSON `role`을 로드하지 마라.** `parseProgram`은 현재 `role`과 `damage`를 **버린다**(`data_loaders.ts:212`). `role`을 로드하면 `combat_engine.ts:165`의 **역할 기반 크리 확률**과 다른 VFX/SFX가 **활성화**된다 — 이는 메타데이터 배선이 아니라 **게임플레이·밸런스 변경**이다.

---

## 전투 무결성 규칙 (Combat Integrity Rules)

1. **한 번의 확정 = 한 장의 프로그램 실행.** 선택과 취소는 카드·COST·RNG·시계·턴을 **소비하지 않는다.** 확인 1회가 정확히 카드 1장을 제거하고, COST를 1회 적용하고, 적/Dixie 처리를 1회 진행한다.
2. **상태는 즉시 커밋되고, 애니메이션은 증거일 뿐 권위가 아니다.** 리듀서 상태와 최종 숫자는 입력 액션에서 갱신된다. VFX는 뒤따를 수 있으나 그 상태를 지연·역행·차단할 수 없다.
3. **밸런스 계약은 byte-identical.** 미리보기·표시 경로는 게임플레이 RNG를 **0** 소비하고 `Date.now`를 진행시키지 않는다. 오너가 밸런스 ADR로 명시 수용하지 않는 한 opening/PPL 출력은 byte-identical이어야 한다.
4. **입력 락아웃·조용한 손실 없음.** 모든 수용된 키보드/터치/게임패드 액션은 VFX 중에도 계속 유효하다. 애니메이션이 다음 결정을 큐잉·삼킴·리다이렉트할 수 없다.
5. **어포던스는 진실을 말한다.** 모든 footer/키 힌트는 현재 상태에서 그 입력이 하는 일을 서술한다. 미리보기 값은 **살아있는 메커니즘에서** 파생되고, 불확실성을 표기하며, **죽은 JSON 필드를 게임플레이 진실로 재사용하지 않는다.**
6. **색은 중복(redundant)이어야 한다.** 역할·상태·타겟·위험·변화는 색 외에 텍스트/글리프/형태가 필요하다.
7. **reduced-motion은 정보를 보존한다.** 흔들림·히트스톱·떠오르는 이동·보간은 사라지되 **최종 값·델타 텍스트·상태 라벨은 남는다.**
8. **모든 지원 그리드에서 한 화면.** 80×50 / 60×40 / 40×60 모두 컨트롤·선택 타겟·손패 매핑·최종 피드백을 유지하고, 카메라 이동·스크롤·잘린 레일이 없어야 한다.

---

## 순위와 승자

**축 1**: `PROGRAM INSPECT` > `TARGET FIRST` > `COMMAND DECK` > `CARD RAIL`
- Inspect의 **정보 계층**을 먼저 구현한다.
- confirm 모델은 **오너가 ADR-0243 대체 여부를 결정할 때까지 보류**한다.
- TARGET FIRST는 프로그램에 **진실한 타겟/효과 구분**이 생길 때까지 대기.
- COMMAND DECK는 키 입력만 늘리므로, CARD RAIL은 레이아웃 적대적 은유이므로 **버린다**.

**축 2**: `SIGNAL BURST` > 제한적 `READABLE IMPACT` > `EVENT GRAMMAR` > `COMBAT LEDGER`
- SIGNAL BURST의 **누락 이벤트**를 먼저.
- 그 뒤 **진실한 델타/뒤따르는 바**만.
- EVENT GRAMMAR는 새 하위 시스템이 아니라 **무결성 명세**로 취급.
- COMBAT LEDGER는 ADR-0231이 이미 출시했으므로 **버린다**.

---

## 최고 레버리지 첫 슬라이스

**진실한 런타임 필드만으로** 세로·번호 손패를 렌더한다.

```text
1 STRIKE   COST +3 → 41/100   TARGET ICE
2 SPLIT    COST +8 → 46/100   TARGET ALL ICE
3 WISP     COST +8 → BLOCKED  TARGET ICE
```

**아직 표시하지 않는다**: `role`, 저작된 `damage`, `effect`, 설명, 킬 확률, 결정적 상태 주장.

**파일**
- 신규 `web/src/core/combat/program_affordance.ts` — 순수 함수: 유효 COST, 사용 후 COST, 차단, 타겟 라벨
- `web/src/core/combat/state_actions_programs.ts` — **같은 COST 헬퍼를 재사용** (동작 보존)
- `web/src/renderer/combat_grid.ts` — 237–252행의 짧은 ID 행을 세로 목록으로 교체
- `web/src/main.ts`, `web/src/input/touch.ts` — 같은 어포던스 행을 터치 버튼에 공급
- `web/tests/program_affordance.test.ts`, `combat_grid.test.ts`, `touch.test.ts`

**red → green 테스트**
1. 일반 및 `double_alarm` COST 라벨이 리듀서 청구·상한 거절과 **정확히 일치**
2. 슬롯 순서 `1..N`이 입력이 쓰는 프로그램과 동일
3. `aoe`면 `ALL ICE`, 아니면 `ICE`
4. 세 그리드 모두 레일과 모든 슬롯 유지, 오버플로 없음
5. 터치 라벨·`aria-label`이 캔버스 의미와 일치하며 44px 타겟·인덱스 콜백 보존

**수용 증거**: unit/typecheck/lint/build green · opening/PPL 밸런스 stdout **byte-identical** · 전체 e2e green · 3개 레이아웃 before/after 캡처 · **표시된 숫자를 누르면 정확히 그 행과 그 COST가 소비됨을 수동 증명**

---

## 이건 짓지 마라 (Do Not Build)

- 새 이벤트 버스, 애니메이션 리듀서, 영속 표시 큐
- 저장되는 프로그램 선택·트윈·VFX 상태
- `Math.random`을 호출하거나 실제 리듀서를 추측 실행하는 피해 미리보기
- 메커니즘 정합 전의 JSON `role`·`damage`·`damage_bonus`·설명·effect 기반 UI
- 보간된 존재하지 않는 상태를 권위 값으로 표시하는 HP/COST 숫자
- 또 하나의 전투 원장
- 가로 스크롤, 카드 드래그, 덱 재배열, 카드 위젯 툴킷
- Y/N 명령 문법 또는 모든 일상 행동의 확인 절차
- 입력 락, 애니메이션 큐, "VFX 끝날 때까지 대기"
- UI를 정당화하기 위한 새 상태/타겟/적 의도 메커니즘
- UI 수정이라는 명목의 밸런스 조정·재기준화
- 리듀서 안의 추가 오디오/DOM/벽시계 부작용

---

## Manus 가정 교정 (Corrections)

- **선택 모델이 없다** — 숫자 입력은 `use_program`으로 직접 해소된다(`state.ts:186`).
- **카드 UI가 없다** — `[id.slice(0,4)]` + 별도 HTML 터치 버튼뿐이다.
- 런타임 `Program`에 **`role`·저작 `damage`·`damage_bonus`가 없다**(`types.ts:59`).
- **저작된 프로그램 효과는 구현되지 않았다** — 모든 프로그램이 `tier * 5` 피해를 쓴다(`state_actions_programs.ts:81`). **Shield·Probe·Wisp도** 현재 그 경로를 탄다.
- **Burn·slow는 보편적 난수 프로크**이며 프로그램별 결정적 효과가 아니다(`state_actions_programs.ts:144`).
- **Combat Ledger는 누락이 아니다** — 최근 4줄이 이미 렌더된다.
- **보스 페이즈 시각 피드백은 누락이 아니다** — 전용 **음향만** 미배선이다.
- "기존 스킬별 색/SFX"는 런타임 프로그램이 `role`을 나르지 않아 **대부분 도달 불가**하다.
- 목업의 `ARC_LANCE`·`PATCH`·`SPLIT`·`GHOST`는 **예시**이며 현재 카탈로그/런타임 계약이 아니다.
- Manus는 COST가 에너지 풀이 아니라 **알람 누적**임을 **정확히** 파악했다.
