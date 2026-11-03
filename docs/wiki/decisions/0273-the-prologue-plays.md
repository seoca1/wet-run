# ADR-0273: 그래픽 노블이 실제로 재생된다 + 프롤로그가 런으로 이어진다

**상태**: Accepted
**날짜**: 2026-11-04
**결정자**: 오너 ("프롤로그부터 엔딩까지 스토리의 일관성" → "계속.")
**우선순위**: P0 (프롤로그가 재생되지 않음 — 블로킹) + P1 (서사 흐름)
**관련**: [ADR-0272 — 런이 arc 프레임으로 시작](./0272-runs-open-on-their-arc.md) · [ADR-0032/0040 — 그래픽 노블](./0032-graphic-novel-mode.md) · [ADR-0263 — 죽음 화면(같은 "문서화만 되고 배선 안 됨" 계열)](./0263-defeat-screen-must-be-escapable.md) · [ADR-0261 — 화면-대기 박자](./0261-growth-moment-is-shown.md)

> **프롤로그가 재생되지 않았다.** 그래픽 노블 화면은 **자기 푸터에 키맵을 인쇄**하고 있었지만
> (`ENTER: skip dialogue | P: pause | ESC: exit`), `main.ts` 는 **아무 키도 라우팅하지 않았다**:
> `graphic_novel` 이 화면 제외 목록에 없어 `handleStubInput` 으로 새었고, 그래서 **ENTER 는 곧바로 메뉴**였다.
> 모드는 **한 프레임에서 얼어붙어** 있었다 — 플레이어 API(`tick`·`skip`·`advance`·`pause`)는 완비돼 있었는데
> **배선만 없었다.**

## 컨텍스트 (Context)

실측(수정 전, 실브라우저):

```
진입 → scene_index 0, dialogue_index 0, paused false
6초 후 → idx 0, dlg 0            ← 자동 진행 없음
ENTER → screen = "menu"          ← 진행이 아니라 이탈
TAB   → paused false             ← 일시정지 안 됨
```

코드 사실:

| 사실 | 근거 |
|---|---|
| 그래픽 노블 화면이 **자기 키맵을 인쇄**한다 | `graphic_novel_screen.ts` 푸터 |
| `main.ts` 에 **그 키를 받는 분기가 없다** | `state === null` → `handlePreGameInput` (menu/mission_select/far_grid_hub/settings 만) |
| 게다가 `graphic_novel` 이 **스텁 제외 목록에 없다** | 입력이 `handleStubInput` 으로 → `confirm` 이면 `screen = "menu"` |
| 플레이어 API 는 **완비** | `tick(p, ms)` · `skipCurrentDialogue` · `advanceDialogue` · `advanceScene` · `togglePause` |
| 대사 길이 | `duration_ms` 12,000–18,000 (**첫 씬 합계 166초**) — 자동 연출이 원래 느리다 |

즉 **"문서화된 키가 동작하지 않는다"** — ADR-0263(죽음 화면)과 같은 계열의 결함이다.

## 결정 (Decision)

### 1) 키를 배선한다 (그리고 푸터를 실제 키로 고친다)

`handleGraphicNovelInput` — 화면이 인쇄하는 그대로:

| 키 | 동작 |
|---|---|
| `ENTER` / `Space` | 타이핑 중이면 그 페이지를 끝내고, 끝났으면 다음 대사 → 다음 씬으로 |
| `TAB` | 일시정지 / 재개 |
| `ESC` / `Q` | 모드 종료(타이틀) → **문구를 실제 키로 정정**(`P`/`S` 는 `KEYBOARD_MAPPING` 에 없어 도달 불가였다) |

`graphic_novel` 을 **스텁 제외 목록에 추가**해 입력이 스텁으로 새지 않게 한다.

### 2) 자동 재생을 **벽시계**로 (표시 전용)

렌더 루프에서 `tick(player, deltaMs)` 를 돌리고, 이벤트가 있을 때만 다시 그린다.
`matrixTravelFrame`·`pressFeedback` 과 같은 **표시 전용·벽시계** 계층이다 — 리듀서·저장 무접촉.
렌더는 **플레이어에서 직접** 파생한다(입장 시점 스냅숏은 낡는다).

### 3) 완료하면 **런으로 넘긴다**

`player.done` 이면 ENTER 가 `mission_select` 로 간다 — 프롤로그의 마지막 씬이 문자 그대로
**"THE NEXT JACK"**(`scene_case_epilogue`)이므로, 다음 잭은 **플레이어**다.
그 런은 arc 인트로(ADR-0272)로 시작해 arc 엔딩(ADR-0271)과 런 요약(ADR-0269)으로 닫힌다.

## 결과 (Consequences)

- **하나의 흐름**: `프롤로그(그래픽 노블) → ENTER → 미션 선택 → 발사 → arc 인트로 → 런 → 엔딩(arc) → 런 요약 → 타이틀`.
- 프롤로그가 **읽히고 진행된다** — 자동(12~18초/대사) + ENTER 로 넘기기, TAB 정지, ESC 이탈.
- 화면이 **실제로 동작하는 키만** 인쇄한다(ADR-0251 §5).

### 불변

- 리듀서·`GameState`·저장 슬롯·밸런스 하네스 **무접촉**(그래픽 노블은 런 밖 별도 모드).
- 씬 데이터(`scenes.json`)·플레이어 API·그래픽 노블 렌더 레이아웃 **무변경**.
- `tick` 외의 진행 경로(ENTER 로 넘기기)를 **막지 않는다** — 입력은 언제나 유효하다.

## Implementation Status (2026-11-04)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/main.ts` — `handleGraphicNovelInput` · `exitGraphicNovel` · `startRunFromGraphicNovel` ·
  루프의 `gnTick(player, deltaMs)` · 렌더가 플레이어에서 직접 파생 · 스텁 제외 목록에 `graphic_novel`.
- `web/src/renderer/graphic_novel_screen.ts` — `done` 플래그, 푸터를 실제 키로 정정,
  완료 시 `ENTER: start a run | ESC: exit`.
- `web/tests/graphic_novel_screen.test.ts` — 푸터 정정 + **완료 시 런 시작 안내** 케이스.
  테스트 픽스처가 원작 첫 문장 조각("The sky above the port.")을 쓰고 있어 중립 문구로 교체했다.
- **실브라우저**: `ENTER` → `dialogue_index 0→1` + **화면 유지** · `TAB` → `paused true` · `ESC` → 타이틀 ·
  `ENTER` 21회 → `done=true`(씬 5/5) → `ENTER` → **`mission_select`** → 발사 → arc 인트로.
- vitest **186 files / 4043 tests** · tsc 0 · eslint 0 errors · build PASS ·
  `check_no_novel_prose.py` **1729 문자열 · 0건**(검사 범위에 `web/tests` 추가).

**Notes**:

- 자동 진행이 **느린 것은 데이터의 연출 값**이다(대사당 12–18초). 바꾸면 씬 데이터를 손대는 별도 결정이다.
- `graphicNovelState` 의 `currentText` 는 더 이상 렌더에 쓰이지 않는다(플레이어에서 파생). 스냅숏은 입장 시점 기록으로만 남는다.

## 열린 질문

- **(a) 자키 선택.** 그래픽 노블은 `novice` 체인(5씬)으로 시작한다. 27씬(3자키 × 9) 중 어느 체인을 플레이할지는
  아직 런 흐름에서 고르지 않는다(메뉴의 캐릭터별 진입은 ADR-0032 시절 설계).
- **(b) 프롤로그 진행 저장.** 모드 진행은 저장되지 않는다(`SAVED_PROGRESS` 화면은 현재 코드에 없다) — 매번 처음부터.
- **(c) 런과 자키의 연결.** 지금은 "프롤로그 → 런"이 **흐름**으로만 이어진다. 자키가 런의 대사·엔딩 톤에
  영향을 주려면 런 상태에 자키가 들어가야 한다(저장 스키마 변경).
- **(d) 대사 길이.** 12–18초 자동 + ENTER. 첫 런에만 자동을 끄거나 짧게 할지는 별도 결정.

## 영향 받는 항목

- `web/src/main.ts`
- `web/src/renderer/graphic_novel_screen.ts`
- `web/tests/graphic_novel_screen.test.ts`
- `scripts/check_no_novel_prose.py` (검사 범위에 `web/tests` 추가)

## 관련 결정

- ADR-0272 (런 인트로 — 프롤로그 다음에 오는 비트) · ADR-0032/0040 (그래픽 노블 모드) ·
  ADR-0263 (문서화만 되고 배선 안 된 화면 — 같은 결함 계열) · ADR-0251 (화면은 실제 결과를 말한다)

## 변경 이력

- 2026-11-04: 오너 "계속." → 키 배선 · 벽시계 자동 재생 · 완료 시 런 시작 · 실브라우저 확인.