# ADR-0335: 검증 러틴은 한 명령이다 — 단일 진입점과 남은 정직성

**상태**: Accepted (오너: *"위임할테니 검증 루틴을 전반적으로 구조적으로 개선해줘"*)
**날짜**: 2026-11-18
**결정자**: 사용자
**우선순위**: P1 (검증 인프라)

## 컨텍스트 (Context)

ADR-0333 이 "연극"을 가려내고 ADR-0334 가 죽은 도구를 치웠지만, 검증은 여전히 **여덟 개의 명령을 손으로
순서대로 치는 일**이었다. 사람이 순서를 잊거나 하나를 건너뛰면 "게이트 7종 CLEAN" 같은 주장이 다시
근거를 잃는다. 개선 여지도 남아 있었다:

- Jev 영역은 ADR-0334 에서 "미배선"으로 정직해졌지만, 실제 §6 가드는 여전히 안 돌았다.
- `check_doc_claims.py` 는 `AGENTS.md` 만 검사 → `README.md` 의 `2654 tests` 가 조용히 틀려 있었다.
- `mixed_language_audit.py` 는 `*.md` 만 → 소스 안의 CJK 혼용(과거 `wet_run_verify.py` 의 사례)을 못 봤다.
- mutation spike 의 유일 생존 변이 `AUTO_ATTACK_INTERVAL_MS` 를 고정하는 테스트가 없었다.
- CI 가 같은 스위트를 `ci.yml`·`delegation-verification.yml`·`game-balance-test.yml` 에서 **세 번** 돌렸다.

## 결정 (Decision)

**루틴을 단일 진입점으로 만들고, 남은 정직성 구멍을 닫는다.**

1. **`scripts/wet_run_verify.py` = 단일 러틴 (v3)** — 위치 독립(`__file__` 로 워크스페이스 탐색),
   게이트를 순서대로 실행, 하나라도 실패하면 **exit 1**. 영역: balance · (tests) · audit · doc_claims ·
   no_novel_prose · briefings · links · lang · **Jev(advisory)**. `--tests`/`--full`/`--log`/`--out`.
2. **Jev 실배선(advisory 전용)** — `--jev` 가 `scripts/jev-local-call.sh noul` 을 **실제로 호출**한다.
   입력은 `git diff --stat HEAD`(변경 없으면 `no_change`). 출력은 `answer`·`p`·`calibration` 표기.
   로컬·미보정이므로 **게이트로 쓰지 않는다**(`9_` 접두, 실패 집계 제외).
3. **claim checker 다중 가이드** — 기본 = `AGENTS.md` + `README.md`(`--guide` 반복 가능). `is_vitest_line`
   대소문자 무시. `README.md` 의 `2654→4444 tests`, `107→236 파일` 교정. ROADMAP 은 역사 서술이라 제외.
4. **혼용 감사 소스 확장** — `--root` + `--source`(`.py`/`.ts`/`.tsx`/`.js`). 기본은 md 전용(워크스페이스
   전체 소스 스캔은 667 오탐 — Foreign Language 생성기·테스트 픽스처). 러틴은 `--root Game/wet_run --source`.
5. **mutation 구멍 봉합** — `combat_engine.test.ts` 에 `AUTO_ATTACK_INTERVAL_MS === 2000` 계약 테스트.
   결과 **6/6 KILLED**.
6. **CI 정리** — `game-balance-test.yml` 의 무검증 `balance-test` job 삭제(게이트는 `balance-regression`);
   `delegation-verification.yml` 을 **수동 전용**(`workflow_dispatch`)으로 바꿔 자동 중복 제거; format 단계는
   `continue-on-error`(advisory)로 강등.
7. **prettier 게이트는 채택하지 않는다** — `prettier --check` 가 **139 파일**에서 실패(유지된 불변식이
   아니었음). 의도 폭을 명시하는 `.prettierrc.json`(printWidth 100)만 추가하고, 일괄 재포맷은 별도 결정으로 남긴다.

## 결과 (Consequences)

- **한 명령으로 검증**: `python3 scripts/wet_run_verify.py --full` → 게이트 **8/8 pass**, advisory Jev
  (`answer=no p=0.1 [local-uncalibrated]`), exit 0. 실패 시 exit 1(파이프라인 사용 가능).
- **문서 드리프트 봉합**: README 수치 교정 + 검사 대상 편입 → `README.md` 도 이제 자동 검사된다.
- **mutation 6/6 KILLED**(이전 5/6).
- **CI 중복 제거**: 자동 게이트 = `ci.yml` + `game-balance-test.yml`; delegation 은 수동.
- **정직하게 남긴 것**: prettier 139 파일 미게이트 · Jev advisory(보정 아님) · ROADMAP 자동 검사 제외 ·
  golden bare runner 한정 · mutation 기본 셋 협소.
- **워크스페이스 변경**: `mixed_language_audit.py` 에 `--root`/`--source` (하위 호환; 기본 동작 동일).

## Implementation Status (2026-11-18)

**Status**: ✅ Implemented

**Evidence**:
- `scripts/wet_run_verify.py` — v3 단일 러틴(게이트 8 + advisory Jev, exit code)
- `Game/wet_run/scripts/check_doc_claims.py` — 다중 가이드(AGENTS+README), 대소문자 무시
- `scripts/mixed_language_audit.py` — `--root`/`--source`
- `Game/wet_run/web/tests/combat_engine.test.ts` — cadence 계약 테스트(mutation 6/6)
- `.github/workflows/game-balance-test.yml` · `delegation-verification.yml` · `ci.yml`
- `Game/wet_run/web/.prettierrc.json` — printWidth 100(게이트 아님)
- `Game/wet_run/README.md` · `ROADMAP.md` — 수치/경로 교정

**Notes**: 실 Jev(보정) 배선 · prettier 일괄 재포맷 여부 · ROADMAP 자동 검사는 오너 결정/별도 작업.

## 영향 받는 항목

- `scripts/wet_run_verify.py`
- `Game/wet_run/scripts/check_doc_claims.py`, `scripts/mixed_language_audit.py`
- `Game/wet_run/web/tests/combat_engine.test.ts`, `web/.prettierrc.json`
- `.github/workflows/*.yml`
- `docs/design/verification-framework.md`, `AGENTS.md`, `README.md`, `ROADMAP.md`

## 관련 결정

- ADR-0333 (검증 도구 메타 감사 — golden · mutation)
- ADR-0334 (실패할 수 없는 검사기는 검사기가 아니다)
- ADR-0010 (검증 파이프라인 — 이 스크립트의 기원)

## 변경 이력

- 2026-11-18: Accepted (단일 러틴 + 정직성 5종 봉합 + CI 정리)
