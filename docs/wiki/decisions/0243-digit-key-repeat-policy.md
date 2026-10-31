# ADR-0243: 숫자키 OS auto-repeat 정책 — 프로그램 선택 숫자키만 repeat 를 무시한다 (X4)

**상태**: Accepted
**날짜**: 2026-10-31
**결정자**: 사용자 (프로젝트 오너) — 2026-10-31 결정 (ADR-0238 추천 번들 채택)
**우선순위**: P2 (The Flatline — 입력 정책. **ADR-0238 분할 4건 중 하나, 밸런스와 무관 · 다른 분할과 독립**)
**관련**: [ADR-0238 — 밸런스·입력 결정 요청](./0238-balance-and-input-decision-request.md) · [ADR-0183 — Accessibility (Colorblind 3 Modes, Text Size, Input Remapping)](./0183-accessibility.md) · [ADR-0197 — Gamepad / Controller Input Support](./0197-gamepad-controller-input-support.md) · [UI 개편 트리아지 (2026-10-31)](../../design/ui-overhaul-triage-2026-10-31.md) · [Combat-feel 제안서 (2026-10-29)](../../design/combat-feel-and-interaction-proposal.md)

> **이 ADR 은 ADR-0238 의 분할 결과다.** ADR-0238 의 **X4** 절과 §사용자 결정
> (2026-10-31) 을 구현 단위로 옮긴다.
>
> **구현은 시작하지 않았다.** 이 ADR 작성 중 `web/` 아래 파일은 수정·실행하지
> 않았다.
>
> **의존 순서**: 다른 분할 ADR (0240 / 0241 / 0242) 과 **독립**이다. 밸런스 항목이
> 아니므로 ADR-0229 §A1 판정 대상이 아니다.

## 컨텍스트 (Context)

### 문제 — 숫자키를 누르고 있으면 프로그램이 연타된다 (트리아지 X4)

트리아지 §1.3 X4: "숫자키 OS auto-repeat 차단 (M6) — ❌ not started — (현 상태)
`web/src/input/keyboard.ts:71-72` — modifier 조합일 때만 repeat 무시 — FEEL R4 가
'별도 판단'으로 남김 → 입력 정책 결정 필요".

현재 상태:

- `web/src/input/keyboard.ts:71-72` — `:71` 주석 + `:72`
  `if (event.repeat && (event.ctrlKey || event.metaKey)) {` (2026-10-31 작업 트리에서
  `:72` 직접 확인). 즉 **modifier 조합일 때만** repeat 를 무시한다.
- 숫자키 `1`–`9` 는 `select_program` 에 매핑된다 (`web/src/core/types.ts:467-475`,
  `Digit1`–`Digit9` 는 `keyboard.ts:26-34` — ADR-0238 인용).
- 전투에서 `select_program` 은 `use_program` 으로 해석된다
  (`web/src/core/state/state.ts:167-176` `resolveProgramSelection` — ADR-0238 인용).
- 그래서 Combat-feel 제안서 M6 의 지적대로, 숫자키 하나를 길게 누르면 OS repeat 마다
  프로그램이 한 장씩 나간다 — 손패 소모 + 적 턴 트리거.

### 지켜야 할 기존 동작

`web/tests/keyboard_locale.test.ts:106-109` — `"bare (non-modifier) Enter on repeat
still fires confirm"` (2026-10-31 직접 확인). bare Enter 의 repeat 는 confirm 을
발사해야 한다. 화살표 repeat 는 메뉴 스크롤에 쓰인다.

### 하네스는 이 변경을 측정하지 못한다

ADR-0238 §B: 하네스는 `KeyboardInput` 을 거치지 않고 reducer 에 액션을 직접 넣으므로
(`web/scripts/balance_sim.ts` 의 `applyAction` 구동) `npm run balance` 는 X4 의 영향을
측정하지 못한다 — **0.0pp 는 확인용 정합성 점검일 뿐 근거가 아니다.**

## 사용자 결정 (Decision)

**2026-10-31, 프로젝트 오너 직접 결정** (ADR-0238 §사용자 결정 그대로).

- [x] **X4-2 채택 — 프로그램 선택 숫자키 (`1`–`9` / `Digit1`–`Digit9`) 의
  `event.repeat` 만 무시한다** (`web/src/input/keyboard.ts:71-72` 의 repeat 처리 확장).
- [x] **Enter · 화살표 repeat 는 그대로** — 기존 테스트 `keyboard_locale.test.ts:106-109`
  가 계속 성립한다.
- [x] **X4-5 — 단독 ADR 로 분리** (이 문서).
- 채택하지 않은 것: X4-1 현상 유지, X4-3 이동키 외 전부 repeat 무시 (`:106-109` 의
  bare Enter 동작을 바꿔야 함), X4-4 시간 디바운스 (튜닝 수치가 하나 더 생기고,
  누르고 있으면 여전히 연타됨).

### 채택 이유

1. **문제에 정확히 맞는 가장 좁은 변경이다** — 숫자키 연타만 막고 다른 키는 건드리지
   않는다 (ADR-0238 X4 트레이드오프).
2. **프로그램 한 장은 턴 하나이고, 턴은 결정이어야 한다** — Combat-feel 제안서 R4 의
   논리 (hold-to-repeat 입력 큐 기각) 와 같다 (ADR-0238 X4 추천).
3. **이동과 확인의 repeat 는 메뉴 조작 편의다** — 유지한다. 기존 테스트와 충돌이 없다.

## 수락 증거 (Acceptance evidence)

ADR-0238 X4 수락 증거를 그대로 따른다.

- **테스트** — `web/tests/keyboard_locale.test.ts` 에 세 케이스:
  1. `Digit1` repeat 는 무시된다 (액션 없음)
  2. repeat 아닌 `Digit1` 은 `select_program` 을 발사한다
  3. 기존 `:106-109` (bare Enter repeat 는 confirm 발사) 가 그대로 통과한다
- **브라우저 스모크** — 전투에서 숫자키를 길게 눌러 프로그램이 한 번만 나가는지 확인.
- **밸런스** — `npm run balance` 0.0pp (정합성 점검일 뿐 근거가 아님, 위 §컨텍스트).

## 결과 (Consequences)

**2026-10-31 결정 기준.** 아직 구현 전이므로, 아래는 결정이 확정한 것과 예상이다.

### 결정이 확정한 것

- **키보드 숫자키 1 회 누름 = 프로그램 1 장** — 누르고 있어도 연타되지 않는다.
- **Enter · 화살표 repeat 불변** — 메뉴 스크롤과 확인 반복은 지금과 같다.
- **적용 채널은 키보드뿐** — 게임패드 · 터치 정책은 이 ADR 이 바꾸지 않는다
  (Open questions (f)).

### 긍정적 영향

- 의도치 않은 연속 플레이 (손패 소모 + 적 턴 트리거) 가 사라진다.
- 기존 테스트를 고칠 필요가 없다.

### 부정적 영향 / 수용한 비용

- **다른 "한 번만" 액션은 여전히 repeat 가능** — 예를 들어 확인 계열은 repeat 된다
  (ADR-0238 X4-2 행). 의도한 범위다.
- **입력 채널 간 정책 불일치** — 키보드는 repeat 차단, 터치는 디바운스 (프로그램 버튼
  120ms, D-pad 250ms), 게임패드는 별도 경로로 남는다 (Open questions (f)).
- **입력 리매핑과의 관계** — ADR-0183 의 입력 리매핑으로 `select_program` 이 다른 키에
  묶이는 경우의 처리는 구현 시 확인이 필요하다 (Open questions (i)).

### 후속 항목

1. 구현: `keyboard.ts` 의 repeat 처리에 숫자키 조건 추가 + 테스트 세 케이스.
2. 브라우저 스모크.
3. `docs/design/` 의 입력 사양 갱신 (`AGENTS.md` §3.2 단계 3).

## Implementation Status (2026-10-31)

**Status**: ❌ Not started

**Evidence**:
- `web/src/input/keyboard.ts:71-72` — modifier 조합일 때만 repeat 무시 (확장 대상)
- `web/src/input/keyboard.ts:26-34` — `Digit1`–`Digit9` 매핑
- `web/src/core/types.ts:467-475` — `1`–`9` → `select_program`
- `web/src/core/state/state.ts:167-176` — `select_program` → `use_program` 해석 (`resolveProgramSelection`)
- `web/tests/keyboard_locale.test.ts:106-109` — bare Enter repeat 는 confirm 발사 (유지 대상)
- `web/src/input/touch.ts:142` — 터치 프로그램 버튼 120ms 디바운스 (참고, 범위 밖)

**Notes**: `keyboard.ts:72` 와 `keyboard_locale.test.ts:106-109` 는 2026-10-31 작업
트리에서 직접 확인했다. `keyboard.ts:26-34` · `types.ts:467-475` · `state.ts:167-176` 은
ADR-0238 Evidence (HEAD `0217c0a`) 인용이고, `touch.ts:142` 는 트리아지 P12 인용이다.
구현 없음 — 테스트 수는 측정하지 않았다.

## Open questions

> 문자 표기: (f) 는 ADR-0238 의 문자를 그대로 이월했다. 새 질문은 ADR-0238 의
> (a)–(h) 와 겹치지 않도록 (i) 부터 붙였다.

- **(f) 입력 채널 통일** (ADR-0238 에서 이월) — 이 정책을 게임패드 (ADR-0197) 와
  터치 (D-pad 250ms, 프로그램 버튼 120ms — 트리아지 P12, `touch.ts:142` · `:286`) 에도
  나중에 맞출 것인가? 맞춘다면 "누르고 있어도 1 회" 를 공통 규칙으로 할지, 채널별
  디바운스를 유지할지.
- **(i) 리매핑된 키** — ADR-0183 의 입력 리매핑으로 `select_program` 이 숫자키가 아닌
  키에 묶였을 때도 repeat 를 무시할 것인가? 즉 판정 기준이 "물리 키 `Digit1`–`Digit9`"
  인가, "`select_program` 으로 해석되는 키" 인가.

## 영향 받는 항목

### 이 결정으로 변경된 항목

- `docs/wiki/decisions/0243-digit-key-repeat-policy.md` — **신규** (이 ADR)
- `docs/wiki/decisions/0238-balance-and-input-decision-request.md` — 상태 → Superseded
- `docs/wiki/decisions/README.md` — 인덱스 행 추가

### 구현 시 변경될 항목 (예정)

- `web/src/input/keyboard.ts`
- `web/tests/keyboard_locale.test.ts`

### 변경되지 않는 항목

- `web/` 전체 — 이 ADR 작성 시 **미수정**
- `web/src/input/touch.ts`, 게임패드 입력 경로 — (f) 결정 전까지 불변
- Accepted ADR 본문 (0183 / 0197) — immutable

## 관련 결정

- ADR-0238 — 이 ADR 의 원 결정 요청 (X4 절, §사용자 결정, §결과). 이 ADR 로 대체됨.
- ADR-0197 — 게임패드 입력. (f) 의 대상 채널.
- ADR-0183 — 입력 리매핑. (i) 의 대상.
- [`docs/design/ui-overhaul-triage-2026-10-31.md`](../../design/ui-overhaul-triage-2026-10-31.md) —
  §1.3 X4, §1.2 P12 (터치 디바운스), §2.1, §3 6단계.
- [`docs/design/combat-feel-and-interaction-proposal.md`](../../design/combat-feel-and-interaction-proposal.md) —
  M6 (문제 제기), R4 (hold-to-repeat 기각).

## 변경 이력

- 2026-10-31: 작성 — ADR-0238 분할 (X4). **Accepted** (오너 결정: X4-2 숫자키 repeat 만
  무시 · X4-5 단독 ADR). Implementation Status ❌ Not started. 열린 질문 (f) 이월,
  (i) 신설. 구현 없음.
