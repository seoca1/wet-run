# ADR-0271: 평범한 런의 엔딩을 **선언**한다 — `status_quo`·`control` 보강

**상태**: Accepted
**날짜**: 2026-11-04
**결정자**: 오너 ("계속." — ADR-0270 열린 질문 (a) 승인)
**우선순위**: P1 (서사 일관성)
**관련**: [ADR-0270 — 원작 문구 금지 + 엔딩 선택 고정](./0270-no-novel-prose.md) · [ADR-0269 — 엔딩 화면](./0269-the-ending-looks-back.md) · [ADR-0199 — 단일 미션 범위](./0199-wetrun-web-mvp.md) · [ADR-0090 — Salvation Phase](./0090-salvation-phase-integration.md)

> **ADR-0270 은 "선택이 배열 순서다"를 고정만 했다.** 원인은 남아 있었다: arc 2·4 에 `status_quo` 엔딩이
> 없고 arc 5 에 `control` 엔딩이 없어서, 평범한/부유한 런이 `arcEndings[0]` 로 떨어졌다.
> 그 결과 **미션 하나 끝낸 런이 "The AIs are free. What have you done?"** 로 끝났다. 이제 선언한다.

## 컨텍스트 (Context)

ADR-0270 측정(코드 + 실측):

| arc | 없던 카테고리 | 그 결과 (폴백 `arcEndings[0]`) |
|---|---|---|
| 2 | `status_quo` | `arc2_ghost_dancer` (**transcendence**) — 평범한 런이 초월 |
| 4 | `status_quo` | `arc4_liberation_front` (**liberation**) — "The AIs are free" |
| 5 | `control` | `arc5_neuromancer` (**transcendence**) — 부유한 런이 초월 |

`resolveEnding` 의 분기: `hpPct<=0 → sacrifice` · `hpPct>0.75 && credits>5000 → control` ·
`missionsCompleted>=3 → liberation` · else `status_quo`. **`sacrifice` 는 실전에서 도달 불가**(hp 0 이면 런이 이미 죽음),
`liberation` 은 `missionsCompleted` 가 항상 1 이라 도달 불가. 즉 **실제로 쓰이는 분기는 `control` 과 `status_quo`** 다.

## 결정 (Decision)

**세 엔딩을 추가한다.** 카탈로그 29 → **32**.

| id | arc | category | 이름 | 한 줄 |
|---|---|---|---|---|
| `arc2_status_quo` | 2 | status_quo | **Small Time** / 생계형 | "You kept the lights on and your name out of the files. The city has bigger files to keep." |
| `arc4_status_quo` | 4 | status_quo | **Standing Order** / 현행 유지 | "Nothing woke. Nothing merged. You took the money and left the question where you found it." |
| `arc5_control` | 5 | control | **The Quiet Hand** / 조용한 손 | "You did not break the machine. You bought a chair at its table, and the change is small and yours." |

- **분포**: 7 / 7 / 6 / 6 / 6 = **32**. 스켈레톤 `docs/design/story_skeleton.md` 를 **v1.4.1** 로 올린다.
- **폴백은 남긴다**(`?? arcEndings[0]`): `sacrifice` 처럼 실제로 도달하지 않는 카테고리를 위한 안전망.
  다만 이제 **평범한 런과 부유한 런은 폴백에 의존하지 않는다**.
- **문구는 새로 썼다** — ADR-0270 의 규칙대로 원작 문장 인용 없음(검사기로 확인).
- **선택은 여전히 고정된다**: `ending_selection.test.ts` 가 arc 별 평범/부유 런의 엔딩 id 를 못 박는다.

## 결과 (Consequences)

- **평범한 런** (미션 1회·중간 HP·적은 크레딧): arc 2 → `Small Time`, arc 4 → `Standing Order` (**"The AIs are free" 사라짐**),
  arc 1/3/5 는 기존 그대로.
- **부유한 런** (HP>75%·5000cr↑): arc 5 → `The Quiet Hand` (초월 엔딩 폴백 제거), arc 1–4 는 기존 `control`.
- **실브라우저 확인**: `aleph_fragment`(arc 4) 완주 → `STANDING ORDER / Nothing woke. Nothing merged…`
  (수정 전: `LIBERATION FRONT / The AIs are free. What have you done?`).

### 불변

- `resolveEnding` 의 **분기 순서·조건 무변경**(데이터만 보강).
- 기존 29개 엔딩의 id·문구·카테고리 **무변경**.
- 밸런스·리듀서 상태·저장 무변경(엔딩은 표시).

## Implementation Status (2026-11-04)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/core/combat/ending_resolver.ts` — `arc2_status_quo` · `arc4_status_quo` · `arc5_control`.
- `docs/design/story_skeleton.md` — **32개 (v1.4.1)** + 추가 이유.
- `web/tests/design_conformance.test.ts` — 32 / **7·7·6·6·6**.
- `web/tests/ending_resolver.test.ts` — 총 32, arc 별 개수(2→7, 4→6, 5→6).
- `web/tests/ending_selection.test.ts` — 평범 런: arc2 → `arc2_status_quo`, arc4 → `arc4_status_quo`;
  부유 런: arc1–5 모두 `control`, arc5 는 `arc5_control`; 모든 arc 에 `status_quo` 존재(누락 `[]`).
- `scripts/check_no_novel_prose.py` — 새 문구 포함 **254 문자열, 8단어 일치 0**.
- 실브라우저 완주(84스텝): 엔딩 화면 `STANDING ORDER` + 런 요약.
- vitest **185 files / 4038 tests** · tsc 0 · eslint 0 errors · build PASS.

**Notes**:

- 이 ADR 은 ADR-0270 의 "새 엔딩을 만들지 않는다"를 **뒤집는다**. 0270 은 카탈로그를 스켈레톤 계약으로
  보존하려 했고, 그 계약을 **v1.4.1 로 개정**하는 것이 이 ADR 의 결정이다(그래서 신규 ADR).

## 열린 질문

- **(a) `requiresFaction`/`requiresChoice` 배선.** 어떤 엔딩도 선언하지 않아 두 분기가 죽어 있다.
  팩션 점수는 이미 살아 있으므로(`onMissionComplete`) 엔딩에 선언만 하면 분기가 살아난다. 선택(choice)은 시스템이 필요.
- **(b) `missionsCompleted >= 3`.** 다중 미션 런(캠페인)이 없어 도달 불가. 캠페인이 생기면 살아난다.
- **(c) arc 4 의 `sacrifice` 부재.** hp 0 으로 엔딩에 도달하는 경로가 없어 실질 문제는 아니지만, 경로가 생기면 필요하다.
- **(d) 프롤로그 → 런 연결.** 프롤로그는 여전히 별도 모드(27씬)이고 런과 이어지지 않는다(ADR-0270 (d)).

## 영향 받는 항목

- `web/src/core/combat/ending_resolver.ts` · `docs/design/story_skeleton.md` ·
  `web/tests/design_conformance.test.ts` · `web/tests/ending_resolver.test.ts` · `web/tests/ending_selection.test.ts`

## 관련 결정

- ADR-0270 (원작 문구 금지 + 선택 고정 — 이 ADR 이 그 열린 질문 (a) 를 닫는다) · ADR-0269 (엔딩 화면) ·
  ADR-0199 (단일 미션 범위) · ADR-0090/0192 (Salvation Phase · 엔딩 통합)

## 변경 이력

- 2026-11-04: 오너 "계속." → status_quo 2개 · control 1개 추가 · 카탈로그 32 · 스켈레톤 v1.4.1 · 실브라우저 확인.