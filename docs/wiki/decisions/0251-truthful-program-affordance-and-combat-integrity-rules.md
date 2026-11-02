# ADR-0251: 진실한 프로그램 어포던스 + 누락된 전투 피드백 — 그리고 전투 무결성 규칙 8개

**상태**: Accepted
**날짜**: 2026-11-02
**결정자**: 사용자 (프로젝트 오너) — "추천대로 하자" (Oracle 합성의 추천: 슬라이스 A → 슬라이스 B)
**우선순위**: P2 (The Flatline — 전투 화면의 이해·선택과 가시적 효과)
**관련**: [Oracle 검증 + 합성](../../design/combat-directions-2026-11-02/oracle-review-and-synthesis.md) · [Manus 8안](../../design/combat-directions-2026-11-02/manus-concepts.md) · [ADR-0243 — 숫자키 repeat 정책](./0243-digit-key-repeat-policy.md) · [ADR-0239 — VFX RNG 분리·재기준화](./0239-vfx-spawn-rng-decoupling.md) · [ADR-0231 — combat log](./0231-combat-feel-top3-vfx-log-raf.md) · [ADR-0234 — 상태 HUD](./0234-effect-visibility-status-hud.md) · [ADR-0248 — COST / TRACE](./0248-alarm-meter-naming.md) · [ADR-0195 — 구현 상태 기록](./0195-adr-implementation-workflow.md)

> **이 ADR은 Oracle 합성이 고른 두 슬라이스만 결정한다.** 그 뒤의 어떤 것(제한적 READABLE IMPACT, TARGET FIRST, 선택-확인 모델)도 범위 밖이다.
> **ADR-0243의 결정 내용은 바꾸지 않는다.** "숫자 1회 = 카드 1장 실행"은 그대로이고, 이 ADR은 선택 상태를 추가하지 않는다.

## 컨텍스트 (Context)

### 오너 요청과 승인

전투 화면에서 플레이어가 (1) 손패의 각 프로그램이 무엇을 하는지 이해하고 고를 수 있어야 하고, (2) 효과가 보여야 한다.
Manus가 8안을 냈고([manus-concepts.md](../../design/combat-directions-2026-11-02/manus-concepts.md)), Oracle이 코드·Accepted ADR 대조로
중복·충돌·실현성을 판정한 뒤 "진실한 프로그램 라벨 → 누락 이벤트 피드백" 순서를 추천했다([합성](../../design/combat-directions-2026-11-02/oracle-review-and-synthesis.md)).
오너가 "추천대로 하자"로 승인했다.

### 측정된 현재 상태 (HEAD `6b959c27`)

| 관찰 | 근거 |
| --- | --- |
| 손패는 `[id.slice(0,4)]` 한 줄뿐 — COST·대상 정보 없음 | `combat_grid.ts:237-252` (HEAD); 실제 빌드 `HAND:  [back] [barr] [boos] [cloa] [deco]` ([before trace](../../design/combat-affordance-2026-11-02/live/before-trace.json)) |
| 40×60에서는 **다섯 번째 슬롯이 아예 그려지지 않는다** | 같은 trace, 모바일: 덱 5장, 캔버스 `[back] [barr] [boos] [cloa]` 4개 |
| 터치 버튼 라벨도 `1.back` 형태, `aria-label` 없음 | `touch.ts` `updateProgramRow` (HEAD) |
| 터치 확인 표시 `> N.xxxx`가 **플레이 후의 손패**를 읽어 다른 카드를 이름 붙였다 | `main.ts` `composeCombatOverlays` (HEAD): `this.state?.deck[handIndex]` (1-기반 인덱스로 0-기반 배열, 그것도 카드 제거 후) |
| 모든 프로그램은 같은 `tier * 5` 피해 경로, burn/slow는 보편 난수 프로크, 런타임 `Program`에 role·저작 damage 없음 | 합성 "Manus 가정 교정" |
| `status_apply` 렌더러는 있으나 스폰되지 않음 | `combat_vfx_render_combat.ts:189` |
| 상태 만료는 조용히 버려짐 | `status.ts:60` `tickStatus`, 그 외 slow·vulnerable 소비, 실드 파괴, 적 턴 `tickIceEffects` |
| `SFX_IDS`의 `phase_change`·`boss_intro`·`credit_gain`·`credit_spend`·`heal`·`loot_drop`·`death`는 배선 0건 | `audio/manager.ts:33-48`, `grep` 결과 0 |

## 결정 (Decision)

### 슬라이스 A — 진실한 프로그램 어포던스 (정보만)

1. **세로·번호 손패.** 한 슬롯 = 한 줄. 런타임 필드만:
   ```text
   1 STRIKE    COST +3  → 41/100   TARGET ICE
   2 SPLIT     COST +8  → 46/100   TARGET ALL ICE
   3 WISP      COST +8  → BLOCKED  TARGET ICE
   ```
   40열(내부 34칸)에서는 범례 아래 짧은 줄: `HAND        COST AFTER    TARGET` / `1 BACKDOOR  +2   40/100   ICE`.
2. **한 정의, 두 소비자.** 신규 순수 모듈 `core/combat/program_affordance.ts`의 `programAlarmCost`(유효 COST, `double_alarm` ×2, floor)와 `COST_LIMIT`(100), `programHitsAllIce`(`aoe`)를 **리듀서 `useProgram`이 그대로 사용**한다. 라벨과 실제 청구가 갈라질 수 없다. 동작은 바이트 단위로 같다(아래 증거).
3. **BLOCKED = 리듀서의 거절과 정확히 같은 조건** (`alarm + cost > 100`). 100/100은 BLOCKED가 아니다. BLOCKED 줄은 단어 + 회색 잉크(규칙 6).
4. **슬롯 번호 = 입력 순서.** 줄 N은 `resolveProgramSelection`이 숫자 N에 매핑하는 바로 그 프로그램이다. 카드가 빠져도 남은 줄의 위치는 그대로다(5슬롯 예약).
5. **터치도 같은 줄.** `updateProgramRow`는 같은 어포던스 행을 받아 버튼마다 `1 COST+2 / BACKDOOR / → 2/100 / ICE` 4줄과 같은 사실의 `aria-label`을 쓴다. 44px 하한·`data-hand-index` 콜백·120ms 디바운스 불변. 오버레이가 떠 있는 동안 캔버스는 손패 띠를 비워 둔다(버튼 밑에 글자가 겹치지 않게; `handOnOverlay`).
6. **터치 확인 표시는 실제로 친 카드를 이름 붙인다** (`pressedProgramName`, 플레이 전에 읽음).
7. **표시하지 않는 것**: role, 저작 damage / damage_bonus, effect 텍스트, 설명, 킬 확률, 결정적 상태 주장. JSON `role`은 로드하지 않는다(로드하면 `combat_engine.ts:165`의 역할 기반 크리가 활성화되는 밸런스 변경).
8. **입력 의미 불변.** 숫자 1–9는 즉시 실행, 선택·확인·취소 단계 없음, 선택 상태 없음. ADR-0243 그대로.

### 슬라이스 B — 누락된 피드백 (축 2 잔여분)

1. **상태 부여**: 프로그램 프로크로 상태가 실제로 붙는 곳(`useProgram`)에서 기존 `status_apply` VFX를 스폰한다(`[ICE BURN+SLOW applied]`). 같은 사실을 전투 로그 한 줄(`ICE BURN+SLOW on`)로도 남긴다. ICE가 스스로 거는 shield / regen / buff는 ADR-0231부터 전용 VFX가 있으므로 중복 스폰하지 않는다.
2. **상태 종료**: 플레이 한 번 사이에 사라진 효과(틱 만료, slow·vulnerable 소비, 실드 파괴)와 적 턴 `tickIceEffects`의 만료를 전투 로그 한 줄로 남긴다(`ICE BURN off`, `ICE2 REGEN off`). 로그는 HUD에 인쇄되며 감소된 모션의 영향을 받지 않는다(규칙 7). 판정은 입력 전후 효과 목록의 (대상, ICE, 종류) 개수 차이 — 제거 방식과 무관.
3. **음원**: 각 ID를 이름 그대로의 실제 사건에만 연결한다(순수 함수 `pickEventSfx`, 컨트롤러의 기존 두 디스패치 지점에서 `pickTransitionSfx`로 호출).

   | ID | 사건 |
   | --- | --- |
   | `boss_intro` | 보스 페이즈가 설정된 채 전투가 시작됨(보스 노드 BREACH, `encounter_verbs.ts:253`) |
   | `phase_change` | 전투 중 보스 페이즈 상승 — 기존의 죽은 `VICTORY` 분기(`main.ts`) 대체 |
   | `credit_gain` | `player.credits` 증가(승리 보상·업적) |
   | `loot_drop` | 재료 수 증가(처치 시 루트) |
   | `heal` | 살아 있는 플레이어 HP 증가(루트 화면 15% 회복) |
   | `death` | 플레이어 HP 0 도달(FLATLINE). 잭아웃은 죽음이 아니다 |
   | `credit_spend` | **미배선** — 게임 내 어떤 행동도 `player.credits`를 줄이지 않는다(`purchaseItem`은 호출자 0). 사건을 지어내지 않는다 |

4. **만들지 않은 것**: 새 이벤트 버스, 애니메이션 리듀서, 영속 표시 큐, 저장되는 VFX·선택 상태. 로그·VFX는 기존 `combatLog`(저장 제외)와 `vfxInstances`에 들어간다.

### 전투 무결성 규칙 (구현 게이트)

[합성](../../design/combat-directions-2026-11-02/oracle-review-and-synthesis.md)의 8개 규칙을 이 ADR의 **구현 게이트**로 채택한다. 이후의 모든 전투 화면 작업은 이 8개를 통과해야 한다.

1. **한 번의 확정 = 한 장의 프로그램 실행.** 선택과 취소는 카드·COST·RNG·시계·턴을 소비하지 않는다.
2. **상태는 즉시 커밋되고, 애니메이션은 증거일 뿐 권위가 아니다.** VFX는 상태를 지연·역행·차단할 수 없다.
3. **밸런스 계약은 byte-identical.** 미리보기·표시 경로는 게임플레이 RNG 0회, `Date.now`를 진행시키지 않는다.
4. **입력 락아웃·조용한 손실 없음.** 모든 입력은 VFX 중에도 유효하다.
5. **어포던스는 진실을 말한다.** 라벨은 그 입력이 실제로 하는 일만 말하고, 죽은 JSON 필드를 진실로 쓰지 않는다.
6. **색은 중복이어야 한다.** 모든 구분에 텍스트/글리프/형태가 함께 있다.
7. **reduced-motion은 정보를 보존한다.** 최종 값·델타 텍스트·상태 라벨은 남는다.
8. **모든 지원 그리드에서 한 화면.** 80×50 / 60×40 / 40×60에서 카메라·스크롤·잘린 레일 없음.

### 결정하지 않은 것 — 선택-확인 모델

**선택 후 확인(select-then-confirm) 모델은 결정되지 않았다.** 그것은 ADR-0243의 "숫자 1회 = 카드 1장"을 대체하는 일이며,
일시 필드 `selectedProgramIndex`, 리듀서의 select/confirm/cancel, 키보드·터치·게임패드 재작성, e2e 재작성이 필요하다.
**별도의 오너 결정과 새 ADR이 필요하다.** 이 ADR은 그 방향을 추천하지도, 막지도 않는다.

## 대안과 기각 (Alternatives)

| 안 | 판정 (합성 기준) |
| --- | --- |
| 1-1 PROGRAM INSPECT 전체(2단계 상호작용) | 정보 계층만 채택(슬라이스 A). 확인 단계는 ADR-0243 충돌 — 보류 |
| 1-2 CARD RAIL | 40×60에서 스크롤/랩 없이 불가 — 규칙 8 위반, 기각 |
| 1-3 TARGET FIRST | 진실한 적용성 모델이 없음 — 대기 |
| 1-4 COMMAND DECK (Y/N) | 키 입력만 늘림 — 기각 |
| 2-2 COMBAT LEDGER | 이미 출시(ADR-0231) — 삭제 |
| 2-4 READABLE IMPACT | 슬라이스 B 다음 후보 — 이 ADR 범위 밖 |
| role/damage를 라벨에 표시 | 런타임이 보증하지 못하는 주장 — 규칙 5 위반, 기각 |

## 결과 (Consequences)

### 긍정적

- 숫자를 누르기 전에 그 슬롯이 무엇을 쓰고 어디에 닿는지, 쓸 수 있는지를 안다. 40×60에서 잘리던 다섯 번째 슬롯이 보인다.
- 라벨과 청구가 같은 함수라 이후의 COST 변경이 라벨을 거짓으로 만들 수 없다.
- 상태가 붙고 떨어지는 순간이 로그에 남는다. 음원 6개가 실제 사건에 붙었다.

### 부정적 / 수용한 비용

- **결정타는 COST를 청구하지 않는다(기존 동작, 이번에 발견).** `useProgram`의 승리 분기(`state_actions_programs.ts`, `victoryMessage` 반환부)는 `player.alarm`을 갱신하지 않는다. 그래서 마지막 ICE를 쓰러뜨리는 플레이에서는 라벨의 `→ N/100`이 실제보다 높다(과대 표시, 과소 아님). 킬 예측은 금지(규칙 5·크리 RNG)이므로 라벨이 이를 미리 알 수 없다. 동작 보존 지시에 따라 바꾸지 않았다 — 열린 질문 (a).
- 모바일에서는 캔버스 손패 띠를 터치 버튼이 차지한다(같은 사실). 데스크톱·비터치 좁은 창은 캔버스 줄을 그대로 쓴다.
- 손패가 5장보다 많으면 위로 늘어난다(현재 손패 크기는 5 고정이라 도달 불가).

### 발견했지만 범위 밖 (변경하지 않음)

- `tickIceEffects`(`ice_combat_effects.ts:191`)는 앞쪽 효과를 제거한 뒤 원래 인덱스로 `removeEffect`/`replaceEffect`를 계속 호출한다. 적 효과가 2개 이상이고 앞의 것이 만료되면 다른 효과가 잘못 갱신·복제된다(재현: shield(1)·powered(3)·regen(3) → `powered 3, powered 2, regen 2`). 상태 메커닉 변경이므로 이 ADR에서 고치지 않는다 — 열린 질문 (b). 종료 로그는 개수 차이로 판정하므로 이 결함과 무관하게 실제로 사라진 효과만 보고한다.
- 40×60에서 ICE HP 줄 끝이 잘린다(`50/` — 기존), 전투 진입 힌트 문장(62자)이 40열 레일을 덮는다(기존). 이 슬라이스의 손패·로그와는 무관.

## 열린 질문

- **(a) 결정타의 COST.** 마지막 ICE를 쓰러뜨리는 플레이도 COST를 청구해야 하는가? 그렇다면 리듀서 수정 + 밸런스 측정(ADR-0229 §A1)이 필요하다. 아니라면 라벨에 "결정타는 청구 없음"을 표기할지.
- **(b) `tickIceEffects` 인덱스 결함** 수정 여부(상태 메커닉, 밸런스 접촉 가능).
- **(c) 선택-확인 모델**(ADR-0243 대체) — 오너 결정 대기.

## Implementation Status (2026-11-02)

**Status**: ✅ Implemented (미커밋·미스테이징)

**Evidence** — [combat-affordance-2026-11-02](../../design/combat-affordance-2026-11-02/README.md):
- `web/src/core/combat/program_affordance.ts` (신규) — `programAlarmCost` / `COST_LIMIT` / `programHitsAllIce` / `programAffordances` / 행 포맷 / `combatHandRow`
- `web/src/core/combat/state_actions_programs.ts` — 같은 헬퍼로 청구·상한·AoE 판정; 상태 부여 VFX + on/off 로그
- `web/src/core/combat/state_actions_combat.ts` — 적 턴 ICE 효과 종료 로그(`logMessages`·`anyEnemyAttacked` 불변)
- `web/src/core/status.ts` — `endedStatuses` / `statusEventLine(s)`
- `web/src/core/combat/combat_sfx.ts` — `pickEventSfx` / `pickTransitionSfx`
- `web/src/renderer/combat_grid.ts`, `run_screen.ts`, `core/state/onboarding.ts`, `input/touch.ts`, `main.ts`
- 테스트: 신규 `program_affordance.test.ts`(22) · `combat_status_feedback.test.ts`(11) · `combat_event_sfx.test.ts`(12), `combat_grid.test.ts` +9, `touch.test.ts` +2 (fixture 형식 변경). HEAD 대비 **29 failed / 16 passed + 2 suite load 실패**, 헬퍼만 HEAD에 추가 시 **43 failed / 43 passed**(COST·상한·슬롯 테스트가 HEAD 리듀서에서도 통과 = 헬퍼가 원래 청구와 같다는 증명) → 이후 **86 passed**
- `npm test` **174 files / 3914 passed / 0 failed** (기준 171 / 3857); typecheck 0; lint 0 errors(기존 `keyboard.ts:14` warning); build PASS
- 밸런스: opening / PPL 모두 HEAD 실행본 및 ADR-0239 기준선 사본과 `cmp` byte-identical
- 실제 빌드(5195) 키 trace: 표시된 숫자 → 그 줄 하나 제거 → 표시된 COST만큼 증가, `double_alarm` + 상한 시나리오에서 `+6 → 100/100` 수락·`BLOCKED` 거절(무소비)
- 전체 84개 손패 행(18 after 프레임) fixture 대조 0 실패, width check 18/18
- E2E 82 passed / 4 skipped / 0 failed (최종 빌드 `index-B_nl8RTM.js`; 이전 빌드 1회차는 `idle_alarm.spec.ts:48` 30초 타임아웃 1건 — 단독 2회 26.9s/27.1s 통과, 이후 전체 실행 2회 통과. README 참조)
- 시각 QA: 읽기 전용 explore 서브에이전트 리뷰 REVISE(좁은 행에서 AFTER와 TARGET 사이 공백 1칸) → 열 1칸 확장으로 수정·재캡처. 사람 디자인 리뷰어는 없었다

**Notes**: 슬라이스 B의 테스트 일부 기대값은 red 실행 뒤 로그 형식을 "종류별 줄" → "대상별 한 줄(`ICE BURN+SLOW on`)"로 바꾸며 수정했다(HUD 4줄 안에 들어가도록). 최종 테스트 파일로 HEAD에 대해 다시 red를 실행한 결과가 위 수치다.

## 변경 이력

- 2026-11-02: 작성 — 오너 "추천대로 하자". Accepted. 슬라이스 A·B 구현 및 Implementation Status 기록. 선택-확인 모델 미결정 명시. ADR-0243 결정 내용 불변.
