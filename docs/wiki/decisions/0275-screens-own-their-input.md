# ADR-0275: 화면은 자기 입력을 소유한다 — 스텁 목록의 반전

**상태**: Accepted
**날짜**: 2026-11-04
**결정자**: 오너 ("계속.") — ADR-0274 열린 질문 (d)
**우선순위**: P2 (구조 — 같은 결함의 재발 방지)
**관련**: [ADR-0274 — 런은 자키의 것이다](./0274-the-run-belongs-to-someone.md) · [ADR-0273 — 프롤로그가 재생된다](./0273-the-prologue-plays.md) · [ADR-0263 — 죽음 화면](./0263-defeat-screen-must-be-escapable.md)

> **같은 결함을 한 세션에 두 번 밟았다.** 입력 핸들러가 **제외 목록**을 인라인으로 들고 있어서,
> 새 화면을 그 목록에 넣지 않으면 입력이 `handleStubInput` 으로 새고 **ENTER 가 곧바로 타이틀**로 나갔다.
> 그래픽 노블(ADR-0273)과 자키 선택(ADR-0274)이 연달아 그랬다 — 화면은 멀쩡히 그려지고 **키만** 이상해서
> 매번 왕복이 필요했다.

## 컨텍스트 (Context)

```ts
// 이전
if (
  this.screen !== "menu" && this.screen !== "mission_select" &&
  this.screen !== "tutorial" && this.screen !== "settings" &&
  this.screen !== "dungeon" && this.screen !== "pause" &&
  this.screen !== "graphic_novel" && this.state === null
) { this.handleStubInput(action); return; }
```

- **부정형 열거**라 "빠뜨리면 조용히 스텁"이 된다. 실패가 **조용하고**, 증상이 화면이 아니라 키에 나타난다.
- 같은 세션에서 두 번 발생(0273·0274). 세 번째를 막는 것이 이 ADR 의 목적이다.

## 결정 (Decision)

**긍정형 집합으로 뒤집는다.**

```ts
/** Pre-game screens that handle their own keys. A screen missing from this set
 *  is a stub: no run state, ENTER returns to the title. */
const SCREENS_WITH_INPUT: ReadonlySet<ScreenKind> = new Set([
  "menu", "mission_select", "jockey_select", "tutorial",
  "settings", "dungeon", "pause", "graphic_novel",
]);

if (this.state === null && !SCREENS_WITH_INPUT.has(this.screen)) {
  this.handleStubInput(action); return;
}
```

- **추가 지점이 하나**가 된다: 화면을 만들면 그 집합에 넣는다(그리고 핸들러를 쓴다).
- 이미 제외되던 화면들의 **동작은 불변**(같은 집합).

## 결과 (Consequences)

- 새 화면을 빠뜨리면 **여전히 스텁**이지만, 이제 그 사실이 **이름 붙은 한 곳**에 모여 있어 리뷰에서 보인다.
- 이 세션의 두 결함(0273·0274)은 원인이 같았고, 그 원인은 이제 구조적으로 한 곳에 있다.

### 불변

- 모든 화면의 키 동작 **불변**(집합은 이전 제외 목록과 동일).
- 리듀서·저장·밸런스 무접촉.

## Implementation Status (2026-11-04)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/main.ts` — `SCREENS_WITH_INPUT` 집합 + 부정형 열거 제거.
- 실브라우저 재확인: `NEW RUN → jockey_select → mission_select → 발사(jockey=veteran) → 인트로 → 보드`.
- vitest **187 files / 4050 tests** · tsc 0 · eslint 0 errors · build PASS.

**Notes**:

- 테스트는 이 집합을 강제하지 않는다(화면 추가는 사람의 결정). 대신 **한 곳**에 모으는 것이 목적이다.

## 열린 질문

- **(a) 자동 검사.** "핸들러가 있는 화면은 집합에 있어야 한다"를 소스 스캔으로 강제할 수 있다
  (핸들러 메서드 이름과 화면 키를 대조). 지금은 리뷰에 의존한다.
- **(b) 화면 등록의 일반화.** 화면별 핸들러를 표(맵)로 두고 조회하는 형태가 더 나을 수 있다 —
  지금은 `if` 사슬 + 집합이다.

## 영향 받는 항목

- `web/src/main.ts`

## 관련 결정

- ADR-0273 · ADR-0274 (같은 결함의 두 사례) · ADR-0263 (문서화만 되고 배선 안 된 또 다른 사례)

## 변경 이력

- 2026-11-04: 오너 "계속." → 긍정형 집합으로 반전 · 실브라우저 재확인.
