# ADR-0334: 실패할 수 없는 검사기는 검사기가 아니다 — 검증 도구 정리

**상태**: Accepted (오너: *"정리하고 개선 방안도 제시해줘"*)
**날짜**: 2026-11-18
**결정자**: 사용자
**우선순위**: P1 (검증 인프라)

## 컨텍스트 (Context)

ADR-0333 이 검증 도구 7종을 실측해 "연극"을 가려냈고, 남긴 숙제가 세 가지였다:
`wet_run_verify.py` 의 가짜 초록불, 그 스크립트만 읽던 `metrics.json`, 그리고 링크 검사기 중복.

실측으로 확정한 사실:

- `scripts/wet_run_verify.py` — `jev_check()` 가 `p=0.75` 를 **하드코딩**, `balance_check()` 는 수기
  `metrics.json` 을 읽기만, `log.md` 를 실행마다 오염, **항상 exit 0**.
- `web/src/game/metrics.json` — 2026-10-14 수기. 저장소 전체에서 이 파일을 읽는 코드는 위 스크립트뿐
  (`grep` 소비자 0). `actual_sample` 은 재현 불가.
- `scripts/tools/audit_sprawl.py` — `find_broken_links.py` 와 ROOT/EXCLUDE/strip/정규식이 사실상 동일한데,
  `main()` 에 `sys.exit` 가 없어 **깨진 링크가 있어도 exit 0**. 실패할 수 없는 검사기.

## 결정 (Decision)

**세 가지를 정리한다.**

1. **`scripts/wet_run_verify.py` 재작성** — 영역별로 정직하게:
   - `audit` → 실 `scripts/audit_vault.py` 실행, 종료코드 반영 (유지).
   - `balance` → `Game/wet_run/web` 에서 **실 `npm run balance:check`** 를 돌려 golden 과 대조 (수기 JSON 읽기 제거).
   - `jev` → **미배선**. 점수를 지어내지 않는다. 키 없으면 `advisory_no_key`(p=None), 키가 있어도
     `not_wired` 로 보고하고 `scripts/jev-local-call.sh` 를 가리킨다.
   - `log.md` 기록은 `--log` 를 준 경우에만.
   - **종료코드**: audit 또는 balance 가 실패하면 1 (게이트로 쓸 수 있게).
2. **`web/src/game/metrics.json` 삭제** — 소비자 0, 재현 불가.
3. **`scripts/tools/audit_sprawl.py` 삭제** — 실패할 수 없고(`sys.exit` 부재) 중복. 단일 로컬 검사기로
   `find_broken_links.py`(exit 1, file:line 상세)를 남긴다. 고아 검사는 워크스페이스 `audit_vault.py` 가 담당.
   `scripts/tools/README.md` 에 삭제 사유를 남긴다.
4. **CI 호환 유지** — `balance_baseline.ts` 가 `web/test-results/balance-summary.txt` 도 쓰게 해서,
   `game-balance-test.yml` 의 PR 코멘트 단계가 계속 동작하게 한다.

## 결과 (Consequences)

- **거짓 초록불 제거**: `wet_run_verify.py --full` 은 이제 balance 가 golden 과 어긋나면 **exit 1**.
  Jev 는 p 를 내놓지 않는다(미배선을 미배선이라 한다).
- **삭제**: `metrics.json`(1263 bytes) · `audit_sprawl.py`(4819 bytes).
- **동작 확인(재작성 후)**: `--full` 이 `audit=clean`, `balance=pass`, `2_jev=not_wired(p=None)` 를 보고.
- **ADR 총계**: **254 ADR (0001–0334)**.
- **남은 것(개선 방안, 문서화만)**: Jev 실배선 · `check_doc_claims.py` 를 ROADMAP/README 로 확장 ·
  `mixed_language_audit.py` 를 소스(`.py`/`.ts`)로 확장 · CI 잡 중복 통합(`delegation-verification.yml`
  이 `ci.yml` 을 재실행) · `AUTO_ATTACK_INTERVAL_MS` 값 고정 테스트 · `delegation-analysis/` 노후화 확인.

## Implementation Status (2026-11-18)

**Status**: ✅ Implemented (1~4 전부; 개선 방안은 별도)

**Evidence**:
- `scripts/wet_run_verify.py` — 하드코딩 p 제거 · 실 balance 대조 · `--log` 옵션 · 종료코드
- `web/src/game/metrics.json` — 삭제
- `scripts/tools/audit_sprawl.py` — 삭제, `scripts/tools/README.md` 에 사유 기록
- `web/scripts/balance_baseline.ts` — `test-results/balance-summary.txt` 기록(CI 코멘트 호환)
- `docs/design/verification-framework.md` — D 표를 "조건부/이력"으로 갱신, gap 7건

**Notes**: Jev 실배선과 CI 잡 통합은 오너 결정/별도 작업으로 남긴다.

## 영향 받는 항목

- `scripts/wet_run_verify.py`
- `web/src/game/` (삭제)
- `scripts/tools/` (삭제·README)
- `docs/design/verification-framework.md`
- `AGENTS.md` §2 / §3.1 / §6

## 관련 결정

- ADR-0333 (검증 도구 메타 감사 — golden 게이트 · mutation spike)
- ADR-0010 (검증 파이프라인 — 이 스크립트를 처음 정의)

## 변경 이력

- 2026-11-18: Accepted (3종 정리 + 개선 방안 문서화)
