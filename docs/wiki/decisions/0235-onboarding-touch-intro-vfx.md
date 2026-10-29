# ADR-0235: 온보딩 자동 표시 + 터치 인게임 피드백 + 전투 진입 연출 (`ice_intro`)

**상태**: Accepted
**날짜**: 2026-10-30
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P2 (The Style — 제안 문서 P11 / P12 / P15)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0195 — Accepted ADR Implementation Status Workflow](./0195-adr-implementation-workflow.md), [ADR-0210 — Combat VFX Effect Schema](./0210-combat-vfx-effect-schema.md), [ADR-0214 — 모바일 터치 대상 WCAG 최소 크기 충족](./0214-adr-mobile-touch-target-size.md), [ADR-0229 — Grade 난이도 곡선 재기준화](./0229-grade-curve-rebaseline.md), [ADR-0231 — Combat-feel top-3 반영](./0231-combat-feel-top3-vfx-log-raf.md), [ADR-0232 — Combat-feel tier 2 반영](./0232-combat-feel-tier2-shake-damage-sfx.md), [ADR-0234 — ADR-0226 효과 가시화 + 상태 effect HUD](./0234-effect-visibility-status-hud.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-30 에 결정·구현·검증까지 완료되었다.
>
> **이 ADR 은 밸런스를 바꾸지 않는다.** 12개 grade 전부 **0.0pp drift** —
> ADR-0229 baseline 과 **byte-identical** 하다. §A1 은 발동하지 않았다.
>
> **이 ADR 의 진짜 내용은 "무엇을 넣었느냐" 가 아니라 "기존 인프라가
> 얼마나 준비돼 있었느냐" 다.** 세 제안 **전부** 기존 렌더러·기존
> localStorage 플래그·기존 VFX kind 위에서 구현됐다. **새 VFX kind 0건,
> 새 튜토리얼 시스템 0건, 새 스키마 0건.**

## 컨텍스트 (Context)

`docs/design/combat-feel-and-interaction-proposal.md` (§2) 의 P11 / P12 /
P15 를 반영한다. ADR-0232 가 tier 2 (P1 / P3 / P5) 를 처리하고, ADR-0234 가
P6 / P14 를 처리한 뒤 남은 **밸런스 무관** 항목들이다.

| 제안 | 무엇이 없었나 | 근거 |
| --- | --- | --- |
| **P11** | 튜토리얼 자동 표시 + 전투 진입 힌트 | `renderer/tutorial.ts:9` 의 주석은 "Shown once on first boot" 라고 적혀 있지만 **코드는 first-boot 시 호출되지 않았다** — 메뉴에서 수동 진입만 가능. 전투 첫 화면에 "1-9 = 프로그램 사용" 안내가 없음 | `main.ts` (boot 경로), `renderer/tutorial.ts:151-183` |
| **P12** | 터치 프로그램 버튼 인게임 피드백 | 입력 지연은 없었다 (`touch.ts:180-186` 이 `pointerdown` 에 발화). 그러나 **인게임 반응 표시가 0건** — 유일한 신호는 CSS `:active` 뿐이라 손을 떼면 사라짐 | `input/touch.ts:177-188` |
| **P15** | 전투 진입 연출 (`ice_intro`) | `ice_intro` ("INCOMING: <ICE>" + scanning 배너) **렌더러가 완성돼 있으나 spawn 호출 0건** — 전투 시작이 "메뉴 → 전투 화면 즉 전환"으로 느껴짐 | `renderer/combat_vfx_render_scene.ts:19-52`, `core/state_helpers.ts:240` |

### 이 ADR 의 질문

**세 가지를 기존 인프라만으로 구현할 수 있는가?** 답은 "세 항목 모두
**그대로 있었고 연결만 빠져 있었다**" 다. 그리고 그 "연결" 을 **테스트
가능하게** 만들려면 `main.ts` 를 **수정해야** 했다 — `main.ts` 는 import
시점에 self-boot 하므로 vitest 의 `node` env 에서 **불가**. ADR-0234 의
추출 패턴(`renderer/combat_grid.ts` / `renderer/status_hud.ts`) 이 이 ADR 의
구조적 근거다.

## 결정에 이르게 된 근거

### P11 — 온보딩: 튜토리얼 자동 표시 + 전투 진입 힌트

- `web/src/core/onboarding.ts` (신규, 109 LOC) — 순수 모듈.
  `shouldAutoShowTutorial` (`:65`) 이 **부팅 시 튜토리얼 진입 여부**를
  결정하고, `isTutorialCompleted` (`:34`) / `markTutorialCompleted` (`:47`) 가
  플래그를 읽고 쓴다.
- **플래그 키는 기존 그대로** `wetrun_tutorial_completed` —
  `renderer/tutorial.ts:154` 가 읽고 `:178` 이 쓴다. **새 플래그 0건.**
  `renderer/tutorial.ts` 는 **한 줄도 수정하지 않았다.**
- **부팅 경로 배선** — `main.ts:1901-1903`:
  ```ts
  if (shouldAutoShowTutorial(localStorage)) {
    game.enterTutorial();
  }
  ```
  `enterTutorial` (`main.ts:1805`) 이 기존 `resetTutorial()` +
  `createTutorialOverlay()` 를 호출한다. **새 튜토리얼 시스템 0건.**
- **전투 진입 힌트** — `COMBAT_ENTRY_HINT_LINES`
  (`onboarding.ts:71`), 2줄:
  `1-9: USE PROGRAM` / `ICE first. You first. Alarm 100 is a flatline.`
  `combatEntryHintRows` (`onboarding.ts:90`) 가 배치 행을 계산한다 —
  `HAND:` 행 **위**, `ice_intro` 배너 밴드(행 1·2·3·5) **아래**.
  `main.ts:1345` 의 `composeCombatOverlays` 가 격자에 그린다.

### P12 — 터치: 인게임 프로그램 버튼 피드백

- `web/src/core/touch_feedback.ts` (신규, 103 LOC) — 순수 상태 기계.
  `pressProgramButton` (`:53`) 이 press 를 받아
  `deadlineMs = now + PRESS_FEEDBACK_MS` (400ms) 를 새 상태를 반환하고,
  `expirePressFeedback` (`:70`) 가 벽시계로 만료를 판단한다.
- **타이머를 쓰지 않는다** — 만료는 **호출자가 공급한 벽시계 timestamp**
  로만 판단한다. 그래서 결정론적으로 테스트 가능하고, `Math.random` 을
  **한 번도 소비하지 않는다** (RNG-neutral).
- **인게임 표시** — `main.ts:1775-1780` 의 `handleProgramButton` 가 press 를
  기록하고, `main.ts:1361-1368` 의 `composeCombatOverlays` 가
  `> 3.back` 형태의 라벨을 격자에 그린다.
- **만료는 VFX 루프가 담당** — `main.ts:1688-1696`. VFX 조기 반환
  (`state.vfxInstances.length === 0`) **보다 앞에서** 검사하므로 VFX 가
  하나도 없을 때에도 acknowledgement 가 반드시 사라진다.
- **탭 응답 경로 검증** — `input/touch.ts` 의 프로그램 행은
  `window.wetrun` 전역을 **거치지 않고** 직접 콜백을 받는다
  (`updateProgramRow` 의 `onProgramPress` 파라미터, `touch.ts:153-155`).
  **이유:** `window.wetrun` 은 `boot()` 이 **게임 시작 뒤**에 대입한다
  (`main.ts:1905`). 그 사이의 탭은 **조용히 버려졌다.**
- **디바운스 250ms → 120ms** — `PROGRAM_PRESS_DEBOUNCE_MS`
  (`touch.ts:142`). 중복 `pointerdown` → `click` 합성은 여전히 걸러지되
  **의도적 연타**는 통과한다.
- `:focus-visible` 스타일 추가 (`touch.ts:188-190`) — 키보드 접근성.

### P15 — 전투 진입 연출 (`ice_intro`)

- `web/src/core/combat_entry_vfx.ts` (신규, 31 LOC) — 순수 결정 모듈.
  `iceIntroPayload` (`:16`) 가 ICE 이름을 담고, `ICE_INTRO_BANNER_ROWS`
  (`:31`) 가 배너 밴드(행 1·2·3·5)를 선언한다 — P11 의 힌트 배치가 이
  밴드와 겹치지 않도록 하는 근거.
- **spawn 은 `state_actions_phases.ts` 의 `applyApproachAction` 안** —
  `phase: "approach"` → `phase: "combat"` 전이 지점이다. 행렬 진입 경로는
  `runPhase: "combat"` / `phase: "approach"` 를 만든 뒤 **동일한** 전이로
  도착하므로 **spawn 지점은 하나면 충분**하다.
- **`import_vfx_deterministic` (RNG 0 draw)** — `import_vfx` 는 id 를
  `Math.random` 에서 뽑는다. 밸런스 하네스는 `Math.random` 을 시드하므로
  **새 `import_vfx` 호출 하나가 calibrated curve 를 조용히 이동시킨다.**
  (ADR-0231 §결함 1 이 정확히 이 문제였다.)

## 구현 중 발견한 실제 결함

> **이 절이 이 ADR 의 실체다.** 제안 문서에는 없는, **구현해야만 드러나는**
> 결함 두 개다.

### 1. `window.wetrun` 전역 대입이 부팅보다 늦다 — 탭이 조용히 버려진다

P12 의 입력 경로는 `pointerdown` 에 발화하므로 **지연은 없었다** — 제안
문서가 이미 그렇게 적었다. 그러나 **경로가 있었다고 해서 그 경로가 항상
도달 가능한 것은 아니었다.**

`input/touch.ts` 의 프로그램 행 핸들러는 `window.wetrun?.handleProgramButton(idx)`
를 호출한다. 그런데 `window.wetrun` 은 `boot()` 안에서 **`game.start()` 뒤에**
대입된다 (`main.ts:1905`):

```ts
if (loading) loading.style.display = "none";
if (shouldAutoShowTutorial(localStorage)) { game.enterTutorial(); }   // ← P11 추가
game.start();
(window as unknown as { wetrun: Game }).wetrun = game;                  // ← 여기서야 대입
```

게임패드 overlay 는 `Game` **생성자**에서 mount 되므로 (`main.ts:509-512`)
버튼은 `window.wetrun` 대입 **이전에도** 이미 DOM 에 있다. 그 창(window)에
들어온 탭은 `?.` 로 **조용히 무시**됐다.

**해결:** `updateProgramRow` 가 `onProgramPress` 콜백을 직접 받도록 바꿨고,
`main.ts:1635-1640` 가 `(handIndex) => this.handleProgramButton(handIndex)` 를
넘긴다. 전역 fallback 은 **호출자가 콜백을 주지 않을 때만** 쓴다 (레거시
호환). **입력 경로가 자기 참조에 의존하지 않게** 되었다.

### 2. VFX 조기 반환이 acknowledgement 만료를 삼킨다

P12 acknowledgement 의 만료는 렌더 루프가 담당한다. 그런데 `main.ts` 의
`loop` 는 VFX 인스턴스가 하나도 없으면 **즉시 return** 한다:

```ts
const state = this.state;
if (state === null || state.vfxInstances.length === 0) return;
```

acknowledgement 이 생긴 순간은 **플레이어가 프로그램 버튼을 누른 직후**이고,
그 시각에 살아있는 VFX 인스턴스가 없을 수 있다 (예: 프로그램 사용 직후
VFX 가 모두 만료된 직후). 그러면 acknowledgement 은 **영원히 화면에 남는다** —
벽시계 deadline 은 이미 지났는데 아무도 확인하지 않으므로.

**해결:** 만료 검사를 VFX 조기 반환 **보다 앞으로** 옮겼다
(`main.ts:1688-1696`). 만료가 실제로 발생하면 `draw(false)` 로 한 프레임
갱신하고 반환한다.

## 고려한 옵션

### Option 1 — 기존 인프라 위에서 세 가지를 구현하고, 추출된 순수 모듈로 테스트한다 (선택)

- **설명**: P11 / P12 / P15 를 구현한다. 새 VFX kind · 새 튜토리얼
  시스템 · 새 스키마는 **0건**. 테스트 불가능한 결정은 `core/` 의 순수
  모듈로 추출하고, `main.ts` 의 **배선**은 소스 텍스트 검사로 회귀 고정한다.
- **장점**: 밸런스가 증명 가능하게 무변경이다 (12 grade 전부 0.0pp).
  테스트가 실제로 회귀를 잡는다 (fail-before 문서화). 추출된 세 모듈이
  모두 250 LOC 정책 안이다.
- **단점**: `main.ts` 의 배선은 **소스 텍스트 검사**로만 고정된다 —
  런타임 동작을 직접 실행한 것이 아니다. `main.ts` 가 self-boot 하므로
  **다른 방법이 없다** (ADR-0234 가 같은 이유로 추출 패턴을 택했다).
- **Pillar 정합**: P11 (The Style) ✅ · P12 (The Style) ✅ ·
  P15 (The Style) ✅ — 셋 다 플레이어의 **체감** 과다.

### Option 2 — `main.ts` 에 인라인으로만 구현한다 (기각)

- **설명**: 추출 모듈 없이 `main.ts` 안에 직접 쓴다.
- **단점**: **`main.ts` 는 import 시점에 self-boot 하므로 vitest 의
  `node` env 에서 import 가 불가능하다.** 테스트할 수 없다. 이 ADR 의
  전제 자체가 사라진다.
- **Pillar 정합**: 실패 (검증 불가능).

### Option 3 — P12 의 debounce 를 그대로 둔다 (기각)

- **설명**: 250ms 를 유지한다.
- **단점**: 제안 §P12 ③ 이 지적한 **연타 입력 누락**이 그대로 남는다.
  120ms 로 완화하면 중복 합성(`pointerdown` → `click`)은 여전히 걸러진다.
- **Pillar 정합**: 실패 (제안 미반영).

## 추천 (Recommendation)

**Option 1.** 세 항목 모두 **기존 인프라의 연결**이며, 연결이 빠진
상태였다. 추출된 순수 모듈은 결정이 테스트 가능하고, 밸런스 수치에는
관여하지 않는다. 발견된 두 결함(`window.wetrun` 전역 의존, VFX 조기
반환에 의한 만료 삼킴)은 **문서화하고 고치는 쪽이 낫다** — 그대로 두면
입력이 조용히 사라지고 UI가 멈춘다.

## 사용자 결정 (Decision)

**2026-10-30 — P11 / P12 / P15 를 구현하되, 구현 중 발견한 두 개의 실제
결함도 함께 해결하기로 결정했다.** 구현 완료·검증됨.

- [x] **Option 1 — 기존 인프라 위에서 세 가지 구현 + 결함 2건 해결** — **채택·구현됨**
- [ ] Option 2 — `main.ts` 인라인 구현 (테스트 불가)
- [ ] Option 3 — debounce 250ms 유지

### 결정된 내용

1. **P11 — 튜토리얼 자동 표시.** `core/onboarding.ts` (신규) +
   `main.ts:1901` 의 boot 배선. 플래그 키는 **기존**
   `wetrun_tutorial_completed` 그대로. `renderer/tutorial.ts` 는 **미변경**.
2. **P11 — 전투 진입 힌트.** `COMBAT_ENTRY_HINT_LINES` 2줄, `HAND:` 행 위 ·
   `ice_intro` 배너 밴드 아래에 배치. 런당 1회.
3. **P12 — 인게임 press feedback.** `core/touch_feedback.ts` (신규, 벽시계
   deadline, RNG 0 draw). `main.ts` 의 `handleProgramButton` 가 기록하고
   `composeCombatOverlays` 가 격자에 그린다.
4. **P12 — 탭 응답 경로.** `updateProgramRow` 가 `onProgramPress` 콜백을
   직접 받는다 — `window.wetrun` 전역 의존 제거. debounce 250ms → **120ms**.
   `:focus-visible` 추가.
5. **P15 — `ice_intro` spawn.** `state_actions_phases.ts` 의
   `applyApproachAction` 전이에서 **1건**. `import_vfx_deterministic` —
   **RNG draw 0건**.
6. **새 VFX kind 0건 · 새 스키마 0건 · 새 튜토리얼 시스템 0건.**
7. **밸런스 무변경** — 12 grade 전부 0.0pp drift.
8. **기존 ADR 은 하나도 수정하지 않았다.** Accepted 결정은 immutable 이다
   (`AGENTS.md` §6). 관계는 이 ADR 에 기록했다.

## 결과 (Consequences)

### 긍정적 영향

- **첫 실행 플레이어가 튜토리얼을 본다** — 주석이 말하던 대로.
- **전투 첫 화면에 "1-9 = 프로그램" 이 보인다** — "뭘 해야 하는지" 모호함이
  해소된다.
- **터치 탭이 게임 안에서 확인된다** — `> 3.back` 이 400ms 동안 격자에
  뜬다. 손을 떼도 CSS `:active` 와 무관하게 남는다.
- **연타가 먹는다** — 120ms 디바운스.
- **전투 시작에 "막" 이 생긴다** — `INCOMING: <ICE>` + `[ scanning... ]`.
- **추출된 세 모듈이 재사용 가능한 infra** 다 — 다음 제안 (P7 / P8 / P10)
  이 같은 패턴을 쓴다.

### 부정적 영향 / 수용한 비용

- **부팅 경로가 바뀌었다** — 첫 실행 플레이어는 메뉴가 아니라 **튜토리얼**
  로 먼저 진입한다. e2e 13개 스펙이 이미 `wetrun_tutorial_completed` 를
  사전 설정하므로 **통과한다** (직접 확인: `e2e/*.spec.ts` 전수 grep).
- **`main.ts` 의 배선은 소스 텍스트 검사로만 고정된다.** 런타임 동작을
  직접 실행한 것이 아니다 (아래 「검증 한계」).
- **press feedback 의 만료는 VFX 루프가 담당한다.** VFX 루프가 멈춘
  상황 (탭 백그라운드 등)에서는 acknowledgement 이 남을 수 있다 —
  `stop()` 에서 리셋한다.
- **`main.ts` 가 1863 → 1964 LOC 로 101 LOC 증가** — ADR-0110 권장 범위
  안이지만 추세는 좋지 않다 (ADR-0234 가 139 LOC 를 줄였다).

### 후속 항목

1. **P7 / P8** — idle-turn pressure · crit threshold coupling.
   **밸런스를 건드린다** — ADR-0229 §A1 drift check 필요. **별도 ADR.**
2. **P10** — accessibility wiring (reduced-motion 과 shake·feedback 결합).
3. **P6 잔여** — ADR-0234 가 glyph 로 처리했으나 아이콘 의미 강화 여지.
4. **`main.ts` 를 부트 가능한 컴포넌트로 분리** — self-boot 이 테스트
   가능성의 구조적 천장이다. `main.ts` 가 커질수록 값어치가 크다.
5. **나머지 미스폰 VFX** — `player_hit` 외 잔여 kind (P2 / R12).

### 관계 — immutable 규칙 준수

ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 / 0228 / 0229 /
0230 / 0231 / 0232 / 0233 / 0234 은 Accepted 이며 immutable 하므로
**하나도 수정하지 않았다** (`AGENTS.md` §6). 관계는 이 ADR 에 기록했다.

## Implementation Status (2026-10-30)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:

**신규 파일 — 6개 (소스 3 + 테스트 3)**

- `web/src/core/onboarding.ts` — **P11.** `TUTORIAL_COMPLETED_KEY` (`:25`),
  `isTutorialCompleted` (`:34`), `markTutorialCompleted` (`:47`),
  `shouldAutoShowTutorial` (`:65`), `COMBAT_ENTRY_HINT_LINES` (`:72`),
  `combatEntryHint` (`:78`), `combatEntryHintRows` (`:90`),
  `combatEntryHintFits` (`:103`). **109 LOC.**
- `web/src/core/touch_feedback.ts` — **P12.** `PRESS_FEEDBACK_MS` (`:22`),
  `IDLE_PRESS_FEEDBACK` (`:33`), `hasPressFeedback` (`:39`),
  `pressProgramButton` (`:53`), `expirePressFeedback` (`:70`),
  `pressFeedbackLabel` (`:80`), `isPressFeedbackLive` (`:97`).
  **103 LOC.**
- `web/src/core/combat_entry_vfx.ts` — **P15.** `iceIntroPayload` (`:16`),
  `ICE_INTRO_DURATION_TICKS` (`:22`), `ICE_INTRO_BANNER_ROWS` (`:31`).
  **31 LOC.**
- `web/tests/onboarding.test.ts` — **25** 개 `it()` (플래그 읽기/쓰기 ·
  first-boot 1회성 · storage 장애 생존 · 힌트 배치/겹침 · **`main.ts` 배선
  소스 검사 5건**).
- `web/tests/touch_feedback.test.ts` — **17** 개 `it()` (state 기계 ·
  라벨 · **RNG 0 draw**).
- `web/tests/combat_entry_vfx.test.ts` — **11** 개 `it()` (payload · 배너
  밴드 · spawn 1건/지속시간 · 행렬 경로 · **RNG 0 draw** · 결정성).

**변경된 파일 — 4개 (소스 3 + 테스트 1)**

- `web/src/main.ts` — **P11 + P12 배선.** import (`:40-53`),
  `combatEntryHintShown` / `pressFeedback` 필드 (`:320`, `:322`),
  `enterTutorial()` (`:1805`), `composeCombatOverlays()` (`:1345`),
  전투 렌더 경로 배선 (`:1604`), `updateProgramRow` 콜백 (`:1635`),
  press feedback 만료 (`:1688`), `handleProgramButton` 기록 (`:1775`),
  `stop()` 리셋 (`:1816`), boot 시 튜토리얼 자동 진입 (`:1901`).
  **1863 → 1964 LOC.**
- `web/src/input/touch.ts` — **P12.** `PROGRAM_PRESS_DEBOUNCE_MS` (`:142`),
  `updateProgramRow` 의 `onProgramPress` 파라미터 (`:153-155`),
  per-button 디바운스 (`:201`), `:focus-visible` (`:188`).
  **288 → 313 LOC.**
- `web/src/core/state_actions_phases.ts` — **P15.** `import_vfx_deterministic`
  import (`:20`), `iceIntroPayload` import (`:24`), `applyApproachAction` 의
  `ice_intro` spawn 1건. **382 → 398 LOC.**
- `web/tests/touch.test.ts` — **P12.** 프로그램 행 describe 8건 추가
  (콜백 수신 · pointerdown 즉시 발화 · 디바운스 중복 거부 · 창 경과 후
  수락 · 120ms 값 · 전역 fallback). **6 → 14 tests.**

**테스트**

- `npm test` — **136 files / 3234 tests, 0 failures.** (ADR-0233 시점 133
  files / 3173 tests → **+3 files, +61 tests**.)
- **신규 assertion 은 변경 전 반드시 실패함을 확인했다.** 복원은 **수동**
  했다 (Python 패치로 파일 백업/복원) — `git checkout` / `git stash` 는
  쓰지 않았다.

  | revert 대상 | 실패 수 | 구체 |
  | --- | --- | --- |
  | P15 `ice_intro` spawn 제거 | **5** | spawn 1건 · payload · duration · 행렬 경로 · 중복 spawn |
  | P12 `touch.ts` 배선 제거 (디바운스 + 콜백) | **5** | 콜백 수신 · pointerdown 발화 · 중복 거부 · 창 경과 수락 · 120ms 값 |
  | P11 `main.ts` boot 배선 제거 | **2** | `shouldAutoShowTutorial(localStorage)` · `game.enterTutorial()` |

  위 세 revert 는 **동시에** 적용했을 때 **7 failures** (`onboarding` 2 +
  `touch` 5) 로 관측되었다 (`combat_entry_vfx` 5건은 별도 revert 에서 관측).

- **밸런스 — 12 grade 전부 0.0pp drift (byte-identical)**

  `npm run balance` (opening deck, 100 runs/mission):

  | grade | win-rate | ADR-0229 baseline |
  | --- | --- | --- |
  | g1 | 100.0% | ✓ 일치 |
  | g2 | 88.6% | ✓ 일치 |
  | g3 | 73.1% | ✓ 일치 |
  | g4 | 39.3% | ✓ 일치 |
  | g5 | 35.7% | ✓ 일치 |
  | g6 | 0.0% | ✓ 일치 |

  `npm run balance -- --deck ppl` (100 runs/mission):

  | grade | win-rate | ADR-0229 baseline |
  | --- | --- | --- |
  | g1 | 100.0% | ✓ 일치 |
  | g2 | 77.9% | ✓ 일치 |
  | g3 | 99.6% | ✓ 일치 |
  | g4 | 84.8% | ✓ 일치 |
  | g5 | 44.4% | ✓ 일치 |
  | g6 | 28.3% | ✓ 일치 |

  mean-turns · mean-HP-end · p5/p95 를 포함한 **모든 컬럼** 이 baseline 과
  byte-identical 하다.

- **RNG draw count — 0.** catalog 53 mission 전체의 combat-entry 전이를
  계수하는 probe 로 측정: **`Math.random` draw 0건.** `ice_intro` spawn 은
  `import_vfx_deterministic` 이므로 RNG 를 소비하지 않는다.

**게이트**

- `npx tsc --noEmit` — **0 errors.**
- `npx eslint src --ext ts` — **0 errors** (pre-existing warning 1건은
  `web/src/input/keyboard.ts:14` — 손대지 않았다).
- `npm run build` — **성공.**

**검증 한계 (정직하게 명시한다)**

- **vitest 는 `main.ts` 를 import 하지 않는다.** `main.ts` 는 import 시점에
  self-boot 하므로 `node` env 에서 **불가**다. 따라서:
  - `main.ts` 의 **배선**은 **소스 텍스트 검사**로만 고정된다
    (`tests/onboarding.test.ts` 의 "P11 — main.ts wiring" describe 5건).
    **런타임 동작을 직접 실행한 것이 아니다.**
  - 실제 브라우저에서 튜토리얼이 자동으로 뜨는지 **관찰하지 못했다.**
- **Playwright e2e 를 실행하지 못했다** — 브라우저와 live URL 이
  필요하다. e2e 13개 스펙이 `wetrun_tutorial_completed` 를 사전 설정한다는
  사실은 **grep 으로 확인**했지만, 스펙을 **실행하지 않았다.**
- **실제 canvas 렌더링을 실행하지 않았다.** `ice_intro` 배너 · combat
  hint · press feedback 라벨이 화면에 **어떻게 보이는지**는 관찰된
  사실이 아니다. 행/열 배치는 **계산** 만 검증했다.
- **화면 위 연출을 관찰하지 못했다.** `INCOMING: <ICE>` 가 "적 탐지" 로
  읽히는가는 **taste 판단** 이다 (제안 §4.4 가 이 분류를 명시한다).
- **터치 실기기 테스트를 하지 못했다.** `pointerdown` 경로는 jsdom
  합성 이벤트로만 검증했다 — 실제 터치 하드웨어에서의 지연· multitouch
  동작은 미검증이다.
- **LSP diagnostics 를 사용할 수 못했다** (daemon socket unreachable).
  그래서 **repo 가 자체로 mandate 한 gate 인 `tsc --noEmit` (strict) 이
  권위** 다.

**Notes**:

- **기존 assertion 을 하나도 약화·skip·삭제하지 않았다.** 추가만 했다.
- **`GameState` 는 변경하지 않았다.** hint · press feedback · tutorial
  상태는 모두 **렌더/입력 계층**에 있다.
- **`web/src/data/effects.json` / `effects.d.ts` — 미변경.** VFX kind
  추가 0건이므로 schema bump 가 필요 없었다.
- **`web/src/data/ice_types.json`, `missions.json`, `programs.json` —
  미변경.** calibration 배열 (`ENCOUNTER_HP_BY_GRADE`,
  `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`) 도 미변경.
- **damage 공식 · combat 수치 · encounter band · `skill_defs` ·
  `effects.json` — 미변경.**
- **`web/src/renderer/settings.ts` / `vfx.ts` / `status_hud.ts` /
  `combat_grid.ts` / `web/src/audio/` — 미변경.**
- **`web/src/renderer/tutorial.ts` — 미변경.** 기존 localStorage 플래그와
  기존 `createTutorialOverlay` / `resetTutorial` 를 그대로 사용했다.
- **`Game/wet_run/log.md` 는 수정하지 않았다** (오케스트레이터 소유).
- **`docs/wiki/decisions/README.md` 는 수정하지 않았다** (오케스트레이터가
  인덱스 행을 추가한다).
- **ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 / 0228 /
  0229 / 0230 / 0231 / 0232 / 0233 / 0234 를 포함한 기존 ADR 은 하나도
  수정하지 않았다.**
- **임시 파일을 남기지 않았다** (검증용 probe 와 백업은 모두 삭제).
- **re-calibration 은 하지 않았다.** ADR-0229 §A1 미발동 (grade 이동 0) →
  **re-baseline 불필요.** §B hard invariant 전부 성립, §A4 해당 없음
  (calibration 배열 미변경).

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `docs/wiki/decisions/0235-onboarding-touch-intro-vfx.md` — **신규**
  (이 ADR)
- `web/src/core/onboarding.ts` — **신규** (P11)
- `web/src/core/touch_feedback.ts` — **신규** (P12)
- `web/src/core/combat_entry_vfx.ts` — **신규** (P15)
- `web/src/main.ts` — P11 + P12 배선
- `web/src/input/touch.ts` — P12 (콜백 경로 · 디바운스 · focus-visible)
- `web/src/core/state_actions_phases.ts` — P15 (`ice_intro` spawn 1건)
- `web/tests/onboarding.test.ts` — **신규** (25 tests)
- `web/tests/touch_feedback.test.ts` — **신규** (17 tests)
- `web/tests/combat_entry_vfx.test.ts` — **신규** (11 tests)
- `web/tests/touch.test.ts` — P12 프로그램 행 describe 8건 추가

### 이번 결정으로 변경되지 않은 항목

- `web/src/core/state.ts`, `types.ts`, `combat_engine.ts`, `ice_ai.ts`,
  `ice_scaling.ts`, `ice_crit.ts`, `ice_skills.ts`, `state_actions.ts`,
  `state_actions_combat.ts`, `state_actions_programs.ts`,
  `ice_combat_effects.ts`, `ice_combat_effect_apply.ts`, `combat_models.ts`,
  `boss_phases.ts` — **전부 미변경**
- `web/src/core/state_helpers.ts` — **미변경** (`import_vfx_deterministic`
  을 *사용*했을 뿐, 수정하지 않았다)
- `web/src/renderer/combat_vfx.ts`, `combat_vfx_core.ts`,
  `combat_vfx_render_scene.ts`, `combat_vfx_render_combat.ts` — **미변경**
- `web/src/renderer/combat_grid.ts`, `status_hud.ts`, `vfx.ts`,
  `settings.ts`, `menu.ts`, `tutorial.ts` — **미변경**
- `web/src/audio/` — **전부 미변경**
- `web/src/data/effects.json`, `effects.d.ts`, `ice_types.json`,
  `missions.json`, `programs.json` — **미변경**
- `GameState` / `SaveSlot` 인터페이스 — **미변경** (schema bump 없음)
- `Game/wet_run/log.md` — 오케스트레이터 소유
- `docs/wiki/decisions/README.md` — 오케스트레이터 소유 (인덱스 행 추가)
- `docs/design/combat-feel-and-interaction-proposal.md` — **미변경**
  (제안 문서는 오케스트레이터 소유)
- ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 / 0228 / 0229 /
  0230 / 0231 / 0232 / 0233 / 0234 — **미수정** (immutable)

## 관련 결정

- ADR-0229 (Grade 난이도 곡선 재기준화) — **drift policy 의 owner.** 이
  ADR 의 0.0pp drift 로 §A1 미발동, re-baseline 불필요. §B hard invariant
  전부 성립. **ADR-0229 는 수정하지 않았다** (immutable).
- ADR-0231 (Combat-feel top-3 반영) — `import_vfx_deterministic` 의
  **출생** ADR. 이 ADR 은 그 helper 를 **신규 spawn site** 에서 사용했다 —
  **helper 의 정의는 바꾸지 않았다.** **ADR-0231 은 수정하지 않았다**
  (immutable).
- ADR-0232 (Combat-feel tier 2 반영) — **직전 sibling.** P1 / P3 / P5 를
  처리했다. 이 ADR 의 `main.ts` 배선 방식 (순수 모듈 추출 + 배선) 은
  ADR-0232 의 구조를 그대로 따른다. **ADR-0232 는 수정하지 않았다**
  (immutable).
- ADR-0234 (ADR-0226 효과 가시화 + 상태 effect HUD) — **`main.ts` 를
  줄인** ADR. 이 ADR 는 `main.ts` 를 **줄이는 대신** 순수 모듈 3개를
  **추가**했다 (추출 패턴의 재사용). **ADR-0234 는 수정하지 않았다**
  (immutable).
- ADR-0233 (오디오 ducking + SFX rate 변조 + 마스터 볼륨) — P13. 이 ADR
  은 오디오를 건드리지 않았다. **ADR-0233 은 수정하지 않았다** (immutable).
- ADR-0214 (모바일 터치 대상 WCAG 최소 크기 충족) — 터치 타깃 크기의
  owner. 이 ADR 는 **크기를 바꾸지 않았다** (debounce 와 `:focus-visible`
  만). **ADR-0214 는 수정하지 않았다** (immutable).
- ADR-0210 (Combat VFX Effect Schema) — 27개 kind canonical taxonomy 의
  owner. 이 ADR 은 kind 를 **추가하지 않았다** (`ice_intro` 는 이미
  있었다). **ADR-0210 은 수정하지 않았다** (immutable).
- ADR-0195 (Accepted ADR Implementation Status Workflow) — 이 ADR 의
  Implementation Status 형식의 owner. **수정하지 않았다** (immutable).
- ADR-0110 (모듈 사이즈 정책) — 신규 모듈 3개가 모두 250 LOC 권장 범위
  안이다 (109 / 103 / 31 LOC). `main.ts` 는 1863 → 1964 LOC 로 101 LOC
  증가. **ADR-0110 은 수정하지 않았다** (immutable).
- `docs/design/combat-feel-and-interaction-proposal.md` — 이 ADR 이 그
  제안의 **P11 / P12 / P15** 를 반영한다. 나머지 제안은 미반영.

## 변경 이력

- 2026-10-30: Draft 작성 (combat-feel 제안 문서 — P11 온보딩, P12 터치
  피드백, P15 전투 진입 연출)
- 2026-10-30: **Accepted (Option 1 — 기존 인프라 위에서 세 가지 구현 +
  결함 2건 해결)** — 구현 완료·검증. P11 은 `core/onboarding.ts` (순수
  first-boot 게이트 + 전투 진입 힌트) + `main.ts` boot 배선 (기존
  `wetrun_tutorial_completed` 플래그 재사용, `renderer/tutorial.ts`
  무변경), P12 는 `core/touch_feedback.ts` (벽시계 deadline, RNG 0 draw) +
  `input/touch.ts` 의 직접 콜백 경로 (`window.wetrun` 전역 의존 제거) +
  디바운스 250ms→120ms + `:focus-visible`, P15 는
  `state_actions_phases.ts` 의 `applyApproachAction` 에서
  `import_vfx_deterministic` 로 `ice_intro` 1건 spawn. **구현 중 2개의 실제
  결함 발견** — ① **`window.wetrun` 전역 대입이 부팅보다 늦어 그 창에서
  온 탭이 조용히 버려짐** (직접 콜백 경로로 해결), ② **VFX 조기 반환이
  acknowledgement 만료를 삼켜 UI가 멈출 수 있음** (만료 검사를 조기 반환
  앞으로 이동). **12 grade 전부 0.0pp drift**, RNG draw count **0**,
  `npm test` 136 files / 3234 tests 0 failures (+3 files / +61 tests).
  신규 assertion 의 **fail-before 를 문서화** (P15 5건 · P12 5건 · P11 2건).
  **P7 / P8 및 나머지 제안은 미반영** — re-calibration 은 하지 않았다.
