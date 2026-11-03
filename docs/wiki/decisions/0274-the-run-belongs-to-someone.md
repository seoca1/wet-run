# ADR-0274: 런은 자키의 것이다 — 선택과 저장, 그리고 표시

**상태**: Accepted
**날짜**: 2026-11-04
**결정자**: 오너 ("프롤로그부터 엔딩까지 스토리 일관성" → "계속.")
**우선순위**: P1 (서사 일관성) · P2 (저장 스키마)
**관련**: [ADR-0273 — 프롤로그가 런으로 이어진다](./0273-the-prologue-plays.md) · [ADR-0261 — 선택 필드 추가 선례](./0261-growth-moment-is-shown.md) · [ADR-0185 — 세이브 마이그레이션](./0185-save-migration-v2.md) · [ADR-0272 — 런 인트로](./0272-runs-open-on-their-arc.md) · [ADR-0269 — 엔딩 요약](./0269-the-ending-looks-back.md)

> **런이 누구의 것인지 말하지 않았다.** 프롤로그는 자키별 이야기인데(`scene_case_*`/`scene_sil_*`/`scene_kas_*`,
> 플레이어의 `CharacterId` = `novice`/`veteran`/`heretic`), ADR-0273 이 프롤로그를 미션 선택으로 넘긴 뒤
> 런은 **익명**으로 시작했다. 방금 읽은 이야기가 런에도 엔딩에도 흔적을 남기지 않았다.

## 컨텍스트 (Context)

| 사실 | 값 |
|---|---|
| 프롤로그 | 자키별 9씬 × 3 (`case`/`sil`/`kas` = `novice`/`veteran`/`heretic`) |
| 런의 자키 | **없음** — 런 인트로도 엔딩 요약도 "누구"를 말하지 않았다 |
| 저장 | 자키를 담을 필드 없음 |

## 결정 (Decision)

### 1) 런 시작에 **자키 선택**을 둔다

`NEW RUN` → **`jockey_select`** → `mission_select` → 런.

- `ScreenKind` 에 `jockey_select` 추가. 화면: `WHO IS JACKING IN` · 3행(`1 CASE` / `2 SIL` / `3 KAS`) + 선택된 자키의 한 줄 소개 · `↑↓: pick | ENTER: jack in`.
- 키: `↑↓` 선택, `ENTER` 확정(→ 미션 선택), `ESC` 타이틀.
- 이름·소개의 단일 출처는 `JOCKEYS` 표(`web/src/core/state/jockey.ts`).

### 2) 자키를 **선택 필드**로 저장한다 (ADR-0261 패턴)

```ts
// GameState.jockeyId?: string | null   ·   SaveSlot.jockeyId?: string
...(state.jockeyId ? { jockeyId: state.jockeyId } : {}),   // stateToSaveSlot
jockeyId: slot.jockeyId ?? null,                            // slotToGameState
isOptionalId(v.jockeyId)                                    // isSaveSlot
```

- **`version` 1 유지** — 구 슬롯은 필드가 없어도 로드되고 `null` 로 복원된다(마이그레이션 불필요).
- 값 검증은 기존 `isOptionalId`(비어 있지 않은 문자열) 재사용.

### 3) 표시로만 쓴다 (밸런스 무접촉)

| 지점 | 표시 |
|---|---|
| 런 인트로 | 제목 아래 `<HANDLE> JACKS IN` (예: `SIL JACKS IN`) |
| 엔딩 요약 | `SIL — Aleph Fragment` |

- 덱·스탯·전투 수치·엔딩 선택에 **영향 없음**. 자키는 "누구"만 말한다.

## 결과 (Consequences)

- **캠페인 흐름 완성**: `프롤로그(자키 이야기) → 자키 선택 → 미션 → 런(인트로가 자키를 말함) → 엔딩(요약이 자키를 말함) → 타이틀`.
- **밸런스 byte-identical**(위 표는 표시 전용) — `npm run balance` 재측정으로 확인.
- **저장 호환**: 구 슬롯 로드 가능, 새 슬롯은 자키를 기억.

### 발견 — 같은 함정을 두 번 밟았다

입력 핸들러의 **스텁 화면 제외 목록**이 열거형이라, `jockey_select` 을 추가하지 않으면 ENTER 가
`handleStubInput` 으로 새어 **곧바로 메뉴로 나간다**(ADR-0273 의 `graphic_novel` 과 **정확히 같은 함정**,
이번 세션에서 두 번 발생). 이 목록은 **명시적 화면 집합**이어야 한다(아래 열린 질문 (d)).

## Implementation Status (2026-11-04)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/core/state/jockey.ts` (신규) — `JOCKEYS` · `jockeyHandle` · `isJockeyId`.
- `web/src/renderer/jockey_select.ts` (신규) — 선택 화면(3자키 + 소개 + 키 안내), 40열 적합.
- `web/src/core/types.ts` — `ScreenKind` 에 `jockey_select`, `GameState.jockeyId`, `SaveSlot.jockeyId`.
- `web/src/core/state/state.ts` · `web/src/save/storage.ts` — 저장/복원/검증(선택 필드).
- `web/src/renderer/run_intro.ts` · `ending.ts` · `run_screen.ts` — 인트로·요약에 자키 표시.
- `web/src/main.ts` — 선택 화면 라우팅·입력·렌더, `launchSelected` 에서 `jockeyId` 설정, 스텁 제외 목록에 추가.
- `web/tests/jockey.test.ts` (6) — 표/이름, 저장 왕복 + **구 슬롯은 `null`**, 선택 화면 렌더(40열), 인트로·요약 표시.
- **실브라우저**: `NEW RUN → jockey_select → (SIL) → mission_select → 발사(jockey="veteran") → 인트로 "SIL JACKS IN" → 보드`;
  완주(80스텝) 후 엔딩 요약 `SIL — Aleph Fragment`. 스크린샷 `00-jockey-select.png`·`01b-run-intro.png`·`06-ending.png`.
- vitest **187 files / 4050 tests** · tsc 0 · eslint 0 errors · build PASS · 두 검사기 exit 0 ·
  밸런스 `100.0/100.0/78.4/38.9/33.4/0.0` **불변**.

**Notes**:

- 인트로/요약은 자키가 없으면(`null`) **이전과 똑같이** 그린다 — 구 슬롯·CONTINUE 호환.
- 자키 표의 id 는 그래픽 노블 플레이어의 `CharacterId` 와 같아서, 프롤로그와 런이 **같은 어휘**를 쓴다.

## 열린 질문

- **(a) 자키가 런에 실제로 영향?** 지금은 표시 전용이다. 덱·스탯·전용 대사·엔딩 분기에 영향을 주려면
  밸런스 재측정과 저장 스키마 확장이 따른다(오너 결정).
- **(b) 자키 선택과 프롤로그 체인.** 프롤로그 모드는 여전히 `novice` 체인으로 시작한다(자키 선택과 별개).
  선택한 자키의 체인을 그대로 재생하는 것이 자연스럽다.
- **(c) 프롤로그 진행 저장.** 모드 진행은 저장되지 않아 매번 처음부터다.
- **(d) 스텁 화면 제외 목록.** 열거형이라 화면을 추가할 때마다 같은 함정이 생긴다.
  "자기 핸들러를 가진 화면"의 명시적 집합으로 바꾸는 것이 옳다.
- **(e) 자키 표시의 밀도.** 인트로에 `SIL JACKS IN` 한 줄, 요약에 `SIL — 미션` 한 줄. 더 넣을지는 화면 예산 문제.

## 영향 받는 항목

- `web/src/core/state/jockey.ts` (신규) · `web/src/renderer/jockey_select.ts` (신규) ·
  `web/src/core/types.ts` · `web/src/core/state/state.ts` · `web/src/save/storage.ts` ·
  `web/src/renderer/run_intro.ts` · `web/src/renderer/ending.ts` · `web/src/renderer/run_screen.ts` ·
  `web/src/main.ts` · `web/tests/jockey.test.ts` (신규)

## 관련 결정

- ADR-0273 (프롤로그 → 런) · ADR-0261 (선택 필드 선례 — 저장 호환) · ADR-0185 (세이브 마이그레이션) ·
  ADR-0272/0269 (인트로·엔딩 요약 — 자키가 붙는 두 지점)

## 변경 이력

- 2026-11-04: 오너 "계속." → 자키 선택·저장 필드·표시 · 실브라우저 전 구간 확인 · 밸런스 불변 확인.