# ADR-0267: 문서가 코드와 어긋난 채 굳지 않게 — 주장 검사기

**상태**: Accepted
**날짜**: 2026-11-04
**결정자**: 오너 ("문서 및 구조에 대해 지금까지 해본적 없는 시각으로 검증해보고 싶어. jev ai, manus 등 도움도 받아줘")
**우선순위**: P2 (문서·구조 신뢰성)
**관련**: [ADR-0195 — ADR 구현 워크플로우](./0195-adr-implementation-workflow.md) · [ADR-0065 — Cross-project citation](./0065-cross-citation.md) · [ADR-0265 — 소크 하네스](./0265-combat-freeze-at-the-cost-cap.md) · [ADR-0266 — COST 상한 턴 패스](./0266-cost-cap-turn-pass.md)

> **진입점 문서가 코드를 따라가지 못한다.** 사흘 동안 ADR 9개(0258–0266)와 테스트 수백 개가 늘었는데
> `AGENTS.md` 는 "130 ADRs, 0001–0213", "107 files, 2654 tests" 에 멈춰 있었고, 이름 붙인 경로 27개 중
> **17개가 존재하지 않았다** — Fiction 위키 링크 8개는 상대경로가 한 단계 어긋나 **워크스페이스 밖**을 가리켰다.
> 워크스페이스 링크 감사는 그 내내 **CLEAN** 이었다. 검사가 못 보는 종류의 부패였다.

## 컨텍스트 (Context)

측정값(스크립트):

| 항목 | 감사 전 |
|---|---|
| 경로 | 27개 중 17개 없음 — Fiction 8(깊이 오류) · `starter_deck.ts`(ADR-0260 이 삭제) · `core/state.ts`(분할 이전) · `decisions/*`(이동) · `engine/*.py`(retired) · `SESSION_SUMMARY`/`CHARACTER_PATHS`(없음) |
| 수치 | "130 ADRs/0001–0213" → 185·266 · "107 files/2654 tests" → 182·4021 |
| ADR 네임스페이스 | 중복 6(0010·0048·0049 는 서로 다른 ADR / 0240·0242·0244 는 evidence) · **ADR-0065 가 폐기 선언된 루트 `decisions/` 에만 존재** · 인덱스는 파일 집합과 **정확히 일치**(건강) |
| 문서 | 362개. `docs/sessions`(13) · `docs/playtest`(3) · `docs/diagnostics`(1) 는 AGENTS.md 미언급 |
| 도구 | `audit_vault.py` **CLEAN** — 위키링크/stem 만 본다. 상대경로·수치 주장은 사각지대 |

**Manus**(정보구조 감사자, 측정값만 제공) 독립 감사: 신규 합류자가 답 못하는 질문 7개, 구조적 결함 Top 5
(정본/네임스페이스 불일치 · AGENTS.md 정확성 · 수치 불일치 · 도구 한계 · 시간축 부재), 가드레일 4개.
**Jev**: 1순위로 **claim-vs-reality 검사 0.97(conf 0.96)**; "숫자를 문서에서 빼라"는 **0.58 로 기각**(임계 미만);
ADR-0065 는 **이동 + 유효성 재판정 0.79(conf 0.74)**.

## 결정 (Decision)

### 1) 주장 검사기를 **실패하는 게이트**로 둔다 (Jev 1순위)

`scripts/check_doc_claims.py`:

| 검사 | 규칙 | 실패? |
|---|---|---|
| **경로** | AGENTS.md 의 백틱 경로가 문서/프로젝트/워크스페이스 루트 중 하나로 해석돼야 한다. 펜스 코드 제외 | **실패** |
| **수치** | ADR 수·최대 번호·테스트 파일 수 (+`--tests` 면 테스트 수). vitest 줄로 한정 | **실패** |
| **ADR 정본 위치** | 정본 디렉터리 밖의 ADR 파일 | **실패** |
| **인덱스 정합** | 파일 ↔ `docs/wiki/decisions/README.md` 행 | **실패** |
| **번호 중복** | 같은 번호의 서로 다른 ADR | 경고 |

**번호 중복이 경고인 이유**: 재번호는 Accepted ADR 을 인용한 모든 링크를 깨뜨린다. 자동 수정이 아니라
오너 결정이다. **수치를 지우지 않는 이유**: Jev 0.58 — 독자가 즉시 값을 보는 이점이 크고, 검사로 묶으면
드리프트는 이미 막힌다.

### 2) ADR-0065 를 정본으로 옮기고 유효성을 재판정한다 (Jev 0.79)

`decisions/ADR-0065-cross-citation.md` → `docs/wiki/decisions/0065-cross-citation.md`, 인덱스 등재,
`## Implementation Status` 로 참조 산출물 7/7 존재 확인(→ Accepted 유지). **결정 내용은 무변경**
(Accepted ADR immutable). 빈 루트 `decisions/` 제거.

### 3) 검사를 작업 의식에 연결한다

AGENTS.md §3.1 에 "**문서 주장 검사 — exit 0 필수**" 추가. 검사기는 새 정보를 만들지 않고
"문서가 코드와 어긋났다"는 사실만 보고하므로 advisory 가 아니라 **실패**가 맞다.

## 결과 (Consequences)

- 문서 수정: Fiction 깊이 **14곳**, 경로 6종, 수치 4곳. 사후 검사 **OK (106 paths, exit 0)**.
- 회귀 방지: 다음에 경로가 바뀌거나 테스트가 늘면 `check_doc_claims.py` 가 **실패**한다.
- **삭제로 정상화하지 않았다**(Manus "하지 말 것"): 경로는 고쳤고, 역사적 이름은 은퇴 목록에 **이유와 함께** 남겼다.

### 남긴 것 (오너 결정)

- **ADR 번호 중복 3건**(0010·0048·0049) — 별칭 ADR 또는 이력 표기 정책 필요.
- **evidence 사이드카 4개**가 ADR 네임스페이스를 공유(`NNNN-evidence.md`) — 규약 문서화 여부.
- **미문서화 디렉터리 3개**(`docs/sessions`·`playtest`·`diagnostics`) — 옮길지, AGENTS.md 에 적을지.
- **시간축/상태 표현**(Manus #5) — ADR 상태 이력 표준과 겹치는 큰 변경.

## Implementation Status (2026-11-04)

**Status**: ✅ Implemented (검사기·경로·수치·ADR-0065)

**Evidence**:

- `scripts/check_doc_claims.py` — 경로(3개 기준 해석) · 수치 · ADR 네임스페이스 · `--tests`.
  현재 `OK: 106 paths resolve; every checked count matches.` (exit 0). `--tests` 로 4021 확인.
- `AGENTS.md` — 186 ADRs/0266 · 182 files/4021 tests · Fiction `../../` · `state/state.ts` ·
  `docs/design/GDD.md` · `docs/wiki/decisions/template.md` · §3.1 검사 단계 추가.
- `docs/wiki/decisions/0065-cross-citation.md` — 정본 이동 + 인덱스 + Implementation Status(참조 7/7).
- `docs/design/docs-audit-2026-11-04/` — 감사 보고서 + Manus 원문(`manus-raw.json`, `manus-messages.json`).
- 검사기 개발 중 **오탐 2건**을 제거했다: 섹션 단위 추론이 Fiction 장을 통째로 "역사"로 오분류했고,
  Python 프로토타입의 `# 40 tests` 를 현재 스위트로 오독했다. 둘 다 **고치기 전 수치는 무효**.
- `AGENTS.md` 기준: 27개 경로 후보 중 17개 없음 → **0개**. 숫자 4곳 → **0곳**.

**Notes**:

- 검사기는 문서가 실제로 **지시**하는 경로만 본다. "삭제되었다"고 서술하는 역사적 이름은 은퇴 목록에
  이유와 함께 남기고 경고로만 출력한다(경고를 없애려면 목록에서 빼면 되고, 그러면 실패한다).
- 워크스페이스 `audit_vault.py` 는 그대로 유효하다(위키링크 담당). 이 검사기는 그 사각지대를 메운다.
- **부작용(의도된 것)**: ADR 을 하나 추가하면 AGENTS.md 의 "N ADRs, 0001–M" 두 값이 즉시 낡는다.
  이 ADR 자신을 추가하면서 실제로 그 줄을 187/0267 로 고쳐야 했다. 검사기가 강제하므로 드리프트는 없지만,
  ADR 생성마다 한 줄을 만져야 한다 — 이것이 부담이면 열린 질문 (e) 로 간다.

## 열린 질문

- (a) **번호 중복 정책.** 0010·0048·0049 를 별칭 ADR(`0065-a`, `-b`?)로 나눌지, 이력 표로만 남길지.
- (b) **evidence 사이드카 규약.** `NNNN-evidence-*.md` 로 통일할지, `docs/design/` 으로 뺄지.
- (c) **미문서화 디렉터리.** `docs/sessions`·`playtest`·`diagnostics` 의 정본 위치.
- (d) **CI 연결.** 현재는 수동 실행. `npm`/CI 단계로 묶을지(문서 편집 세션에서 자주 돌릴 필요는 없다).
- (e) **ADR 개수 주장의 유지비.** ADR 마다 "N ADRs / 0001–M" 을 고쳐야 한다. 대안은 `180+` 같은 하한 표기
  (검사기 규칙 추가) 또는 개수 주장 제거 — Jev 는 제거에 0.58 로 확답하지 않았다.

## 영향 받는 항목

- `scripts/check_doc_claims.py` (신규) · `AGENTS.md` · `docs/wiki/decisions/0065-cross-citation.md` (이동)
- `docs/wiki/decisions/README.md` (0065 행) · `docs/design/docs-audit-2026-11-04/` (신규)

## 관련 결정

- ADR-0195 (ADR 구현 워크플로우 — Status 섹션 규약) · ADR-0065 (이동한 ADR) · ADR-0265/0266 (사흘간의 변화가 드리프트를 만든 배경)

## 변경 이력

- 2026-11-04: 오너 요청 → 측정 → Manus 감사 → Jev 판정 → 검사기·경로·수치·ADR-0065 수정.