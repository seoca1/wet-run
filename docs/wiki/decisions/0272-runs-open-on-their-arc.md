# ADR-0272: 런이 자기 프레임으로 시작한다 — arc별 인트로 비트

**상태**: Accepted
**날짜**: 2026-11-04
**결정자**: 오너 ("프롤로그부터 엔딩까지 스토리의 일관성" → "응 수정해줘.")
**우선순위**: P1 (서사 일관성)
**관련**: [ADR-0271 — 평범한 런의 엔딩](./0271-declare-the-plain-endings.md) · [ADR-0269 — 엔딩이 런을 되돌아보게](./0269-the-ending-looks-back.md) · [ADR-0032/0040 — 그래픽 노블](./0032-graphic-novel-mode.md) · [ADR-0251 — 어포던스 진실성](./0251-truthful-program-affordance-and-combat-integrity-rules.md)

> **런에는 시작이 없었다.** 미션 선택 → 보드. 그리고 이야기는 **엔딩에서야** 다시 말했다.
> 프롤로그(27씬)는 별도 모드라 런과 만나지 않는다. 그래서 런의 arc 와 엔딩의 arc 는 같았지만,
> 플레이어는 **자기가 무슨 이야기 안에 있는지 시작할 때 듣지 못했다.**

## 컨텍스트 (Context)

측정(ADR-0270/0271):

| 사실 | 값 |
|---|---|
| 그래픽 노블 프롤로그 | **27씬** (3 자키 × 9) — 메뉴의 **별도 모드**, 런과 무연결 |
| 런의 시작 | 미션 선택 → 매트릭스. **서사 비트 0** |
| 런의 arc | 미션의 `arc` (1–5) — 엔딩 선택이 **같은 필드**를 쓴다 |
| 스켈레톤이 정의한 Arc 1 이벤트 | `"First Jack" (vision) — 자키의 첫 잭인 묘사, 깁슨 톤 도입` ← **설계에는 있는데 게임에는 없음** |

즉 결함은 "프롤로그가 런과 안 이어진다"가 아니라 **"런에 프롤로그가 없다"** 였다. 스켈레톤은 이미
그 비트를 Arc 1 이벤트로 이름 붙여 두었다.

## 결정 (Decision)

**런을 시작할 때 그 arc 의 프레임 비트를 한 화면 보여준다.**

```ts
// web/src/renderer/run_intro.ts — 표시 전용. GameState 에 없다.
export const RUN_INTRO: Readonly<Record<ArcId, readonly string[]>> = {
  1: ["FIRST JACK", "The deck is cold in your hands.", "…"],
  2: ["THE SPRAWL", "The city files everything. Tonight it files you.", "…"],
  3: ["CORPORATE ICE", "Their walls are older than your hands.", "…"],
  4: ["THE AIS", "Something in there is awake, and pretending not to be.", "…"],
  5: ["THE CHOICE", "One last run. After this the Sprawl decides what you were.", "Go."],
};
```

- **arc 는 미션에서 온다**(`mission.arc`) — **엔딩과 같은 필드**. 그래서 *프레임과 결말이 같은 arc 를 공유*한다.
  (실측: `aleph_fragment` arc 4 → 인트로 `THE AIS` → 엔딩 `STANDING ORDER`, ARC 4.)
- **런 시작에만**: `launchSelected` 에서만 설정한다. **CONTINUE 는 설정하지 않는다** — 재개된 런은 이미 이야기 중이다.
- **아무 키로 닫힌다**: 첫 키를 소비하지만 **애니메이션 대기가 아니다**(ADR-0251 의 금지 대상은 애니메이션이 입력을 막는 것).
  ADR-0261 이 이미 "고르고, ENTER 로 진행"이라는 화면-대기 박자를 정당화했다 — 같은 종류다.
- **표시 전용**: 저장 필드 0, 리듀서 무접촉, 밸런스 무접촉, 정적 텍스트(시계·애니메이션 없음).
- **문구는 새로 썼다**(ADR-0270 규칙). 40열까지 감싸서 넘치지 않는다.

## 결과 (Consequences)

- **하나의 흐름**: `인트로(arc)` → 런 → `엔딩(arc)` → `런 요약`. 같은 arc 가 세 지점을 묶는다.
- **첫 키가 게임으로 새지 않는다**: 실측으로 닫힌 뒤 `currentNodeIndex` 가 0 그대로(ENTER 가 보드 이동이 되지 않음).
- **재개는 조용하다**: CONTINUE 로 들어온 런은 인트로를 다시 보지 않는다(컨트롤러 전용 상태라 저장/복원에 없다).

### 불변

- 그래픽 노블 모드(27씬·3자키) **무변경**. 인트로는 그것을 대체하지 않는다.
- `GameState`·저장 슬롯·리듀서·밸런스 하네스 **무변경**.
- 엔딩 선택·카탈로그(ADR-0271) **무변경**.

## Implementation Status (2026-11-04)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/renderer/run_intro.ts` (신규) — `RUN_INTRO`(5 arc) · `runIntroWidth` · `wrapIntroLines` · `renderRunIntro`.
- `web/src/main.ts` — `runIntroArc`(컨트롤러 전용), `launchSelected` 에서 설정, `draw()` 가 런 화면 대신 인트로를 그리고,
  입력 핸들러가 첫 키를 소비한다(**CONTINUE 경로에는 없음**).
- `web/tests/run_intro.test.ts` (5) — arc 5개 모두 존재, 제목·본문·종료 줄, **40열 래핑**, 3레이아웃 무溢出,
  소스 배선(`launchSelected` 에서만 설정, 첫 키 소비, 인트로 렌더 호출).
- **실브라우저**: 80×50·40×60 에서 인트로 표시(`THE AIS` / `PRESS ANY KEY`) → 첫 키 → 매트릭스,
  `currentNodeIndex 0` 유지(키 미누출). 스크린샷 `docs/design/ending-run-2026-11-04/intro-*.png`.
- vitest **186 files / 4043 tests** · tsc 0 · eslint 0 errors · build PASS ·
  `check_no_novel_prose.py` **261 문자열 · 8단어 일치 0**.

**Notes**:

- 인트로는 **미션의 arc** 를 따른다. 같은 arc 의 미션은 같은 비트를 공유한다(의도 — arc 가 단위).
- 문구는 arc 당 2~3줄로 짧게 유지했다. 늘리면 40열에서 화면을 넘긴다(테스트가 잡는다).

## 열린 질문

- **(a) 그래픽 노블 프롤로그와의 관계.** 27씬 프롤로그는 여전히 별도 모드다. 완전한 캠페인 프레임이 생기면
  자키 선택(케이/실/카스) → 그 자키의 9씬 → 런 → 엔딩이 하나가 된다. 지금은 **arc 단위 비트**로 그 자리를 지킨다.
- **(b) 인트로 문구의 분량/톤.** arc 당 한 화면이 적절한지, 첫 런에만 보여줄지(현재는 매 런).
- **(c) 런 시작 외의 비트.** 구역 진입·보스 접근·마지막 노드 이정표(감사 #5b)는 아직 없다.

## 영향 받는 항목

- `web/src/renderer/run_intro.ts` (신규) · `web/src/main.ts` · `web/tests/run_intro.test.ts` (신규)

## 관련 결정

- ADR-0271 (엔딩 arc) · ADR-0269 (엔딩 요약 — 인트로와 짝을 이룬다) · ADR-0032/0040 (그래픽 노블 — 별도 모드) ·
  ADR-0251 (표시 전용 원칙) · ADR-0261 (화면-대기 박자의 선례)

## 변경 이력

- 2026-11-04: 오너 "응 수정해줘." → arc별 인트로 비트 · 실브라우저 3레이아웃 확인.