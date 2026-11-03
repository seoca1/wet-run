# ADR-0270: 원작 문구를 쓰지 않는다 + 엔딩 선택을 우연에 맡기지 않는다

**상태**: Accepted
**날짜**: 2026-11-04
**결정자**: 오너 ("프롤로그부터 엔딩까지 스토리의 일관성도 체크하고 싶어. Fiction 의 파생소설과 연관된 게 맞지? **소설 원작 문구는 안들어가게끔** 하고 싶어.")
**우선순위**: P1 (법적/정책 + 서사 일관성)
**관련**: [ADR-0269 — 엔딩이 런을 되돌아보게](./0269-the-ending-looks-back.md) · [ADR-0065 — Cross-project citation](./0065-cross-citation.md) · [ADR-0199 — Tier 4 범위](./0199-wetrun-web-mvp.md) · [ADR-0267 — 문서 주장 검사기](./0267-doc-claims-must-match-reality.md)

> **원작 문장이 게임에 들어 있었다.** `scenes.json` 의 두 씬(한/영)이 뉴로맨서 첫 문장
> ("the color of television, tuned to a dead channel")을 그대로 인용했다. 한 씬은 그 문장을
> **메타적으로 언급**하는 형태였지만, 인용은 인용이다.
>
> 그리고 **평범한 런이 "The AIs are free" 로 끝났다.** arc 4 에 `status_quo` 엔딩이 없어
> `arcEndings[0]` 로 떨어졌기 때문이다 — 선택이 서사가 아니라 **배열 순서**가 정했다.

## 컨텍스트 (Context)

### A. 원작 문구

| 위치 | 내용 |
|---|---|
| `web/src/data/scenes.json` `scene_case_jackin.dialogue[0]` (en/ko) | "The world goes **the color of television, tuned to a dead channel** …" |
| `web/src/data/scenes.json` `scene_case_disappear.dialogue[2]` (en/ko) | "… the Chiba sky is **the color of television, tuned to a dead channel** — a phrase he has heard…" |

`Fiction/wiki` 는 원작 인용을 **출처와 함께 보관**한다(예: `works/neuromancer.md` 의 blockquote).
그래서 그 위키가 **원작 문구 코퍼스**가 될 수 있다 — 게임 텍스트와 대조하면 인용을 기계적으로 찾을 수 있다.

### B. 엔딩 선택 (프롤로그 → 엔딩 일관성)

측정:

| 사실 | 값 |
|---|---|
| 프롤로그 씬 | **27** (3 자키 × 9) — 런과 분리된 모드 |
| 미션 | 53, arc 1–5 (20/14/8/7/4) |
| 엔딩 카탈로그 | **29** (7/6/6/5/5) — `docs/design/story_skeleton.md` 계약 |
| `requiresFaction` / `requiresChoice` 를 선언한 엔딩 | **0개** → `resolveEnding` 의 두 분기 **죽은 코드** |
| `missionsCompleted` | `applyTerminalLoot` 이 **항상 1** → `>= 3` (liberation) 분기 **도달 불가** |
| `status_quo` 엔딩이 없는 arc | **2, 4** → 폴백 `arcEndings[0]` |
| `control` 엔딩이 없는 arc | **5** → 같은 폴백 |

그 결과 **평범한 런**(중간 HP·적은 크레딧·미션 1회 — 이 티어가 만들 수 있는 유일한 형태)은:

```
arc1 → arc1_wage_slave (status_quo)          ✅
arc2 → arc2_ghost_dancer (transcendence)     ⚠️ 배열 순서
arc3 → arc3_neutrality (status_quo)          ✅
arc4 → arc4_liberation_front (liberation)    ⚠️ 배열 순서 → "The AIs are free. What have you done?"
arc5 → arc5_unknown (status_quo)             ✅
```

## 결정 (Decision)

### A. 원작 문구 금지 + **검사기**로 강제

- **규칙**: 게임의 사용자 노출 텍스트는 원작의 문장을 **인용하지 않는다**. 용어(ICE·deck·construct·wetware·console cowboy)와 톤은 그대로 쓰되, **문장은 새로 쓴다.** 패러프레이즈·암시는 허용.
- **검사기**: `scripts/check_no_novel_prose.py` — `web/src` 의 사용자 노출 문자열(데이터 JSON + TS 문자열 리터럴, 주석 제외)과 `Fiction/wiki` 의 **따옴표 안 원작 문장**을 비교해 **8단어 연속 일치**를 찾으면 **exit 1**.
  - 8단어를 기본으로 한 이유: 6단어에서는 `"i used to think that was"` 같은 **일반 문구**가 걸린다(실측). 8은 인용만 잡는다.
- **수정**: 두 씬(한/영)을 **패러프레이즈**했다. 이미지("신호가 죽은 화면")는 남기고 **원작 어휘는 제거**.
  한국어 씬에 섞여 있던 영어 `television` 도 함께 정리됐다(워크스페이스 §7 혼용 규칙).

### B. 엔딩 선택을 **고정**한다 (새 엔딩은 만들지 않는다)

- 카탈로그는 스켈레톤 계약(29/7·6·6·5·5)이므로 **추가하지 않는다.**
- 대신 **평범한 런의 엔딩을 arc 별로 못 박는 테스트**를 둔다(`ending_selection.test.ts`):
  배열 순서를 바꾸거나 엔딩을 추가하면 **어떤 이야기가 나가는지 조용히 바뀌지 않는다.**
- `status_quo` 가 없는 arc 를 **명시적으로 기록**한다(2·4). 이는 "의도된 폴백"이 아니라
  **추적되는 사실**이다 — 오너가 원하면 그때 엔딩을 추가한다(스켈레톤 변경).

## 결과 (Consequences)

- 게임 텍스트에 **원작 문장 0건** (252개 문자열 검사, 8-gram). 재발하면 검사기가 막는다.
- 엔딩이 **배열 순서에 의존한다는 사실**이 테스트로 고정됐다. 바꾸려면 테스트를 고쳐야 한다(의식적 결정).
- `requiresFaction`/`requiresChoice` 죽은 분기와 `missionsCompleted>=3` 도달 불가는 **문서화**됐다(코드는 무변경).

### 불변

- 엔딩 카탈로그 **29개·분포·id** 무변경(스켈레톤 계약).
- `resolveEnding` 의 분기 순서·폴백 로직 무변경(관측 결과만 고정).
- 밸런스·리듀서 상태·저장 무변경.

## Implementation Status (2026-11-04)

**Status**: ✅ Implemented (규칙·검사기·문구 수정·선택 고정)

**Evidence**:

- `scripts/check_no_novel_prose.py` — 8-gram 검사. 현재 `OK: 252 user-facing strings`.
  6-gram 으로 돌리면 일반 문구 우연 일치 1건(`"i used to think that was"`)이 나온다 → 기본 8 의 근거.
- `web/src/data/scenes.json` — 인용 2건(한/영 4문자열) 패러프레이즈.
- `web/tests/ending_selection.test.ts` (8) — arc 별 평범 런의 엔딩 고정, `status_quo` 없는 arc = **[2, 4]**,
  control 분기 도달성, 폴백이 undefined 를 내지 않음.
- 측정: 프롤로그 27씬 · 미션 arc 1–5 · 엔딩 29(7/6/6/5/5) · `requiresFaction/Choice` 0개 · `missionsCompleted` 항상 1.
- vitest **185 files / 4038 tests** · tsc 0 · eslint 0 errors.

## 열린 질문

- **(a) arc 2·4 에 `status_quo` 엔딩을 추가할 것인가.** 스켈레톤(29개) 변경이다. 지금은 평범한 런이
  transcendence/liberation 으로 끝나 **서사적으로 과장**된다.
- **(b) `requiresFaction`/`requiresChoice` 를 실제로 배선할 것인가.** 팩션 점수는 이미 살아 있는데(`onMissionComplete`)
  어떤 엔딩도 그것을 선언하지 않아 분기가 죽어 있다. 선택(choice) 시스템도 없다.
- **(c) `missionsCompleted >= 3` 분기.** 다중 미션 런(캠페인)이 없어 도달 불가. 캠페인이 생기면 살아난다.
- **(d) 프롤로그와 런의 연결.** 프롤로그는 3자키 × 9씬의 **별도 모드**이고 런과 이어지지 않는다
  (런은 미션 선택에서 시작). "프롤로그 → 엔딩"을 하나의 흐름으로 만들려면 캠페인 프레임이 필요하다.

## 영향 받는 항목

- `scripts/check_no_novel_prose.py` (신규) · `web/src/data/scenes.json` ·
  `web/tests/ending_selection.test.ts` (신규) · `AGENTS.md` (§3.1 검사 단계)

## 관련 결정

- ADR-0065 (Fiction ↔ wet_run 인용 무결성 — 이 ADR 은 **원작 문장**을 다룬다) · ADR-0267 (문서 검사기) ·
  ADR-0269 (엔딩 화면) · ADR-0199 (단일 미션 런 범위 — `missionsCompleted: 1` 의 근거)

## 변경 이력

- 2026-11-04: 오너 요청 → 측정 → 인용 4문자열 수정 · 검사기 · 엔딩 선택 고정.