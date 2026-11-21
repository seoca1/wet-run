# ADR-0333: 검증 도구는 스스로를 검증해야 한다 — 밸런스 golden 게이트 + mutation spike

**상태**: Accepted (오너: *"추천 순서대로 하고 검증 도구들을 구조화 정리해줘"*)
**날짜**: 2026-11-18
**결정자**: 사용자
**우선순위**: P1 (검증 인프라)

## 컨텍스트 (Context)

세션마다 반복된 주장 — *"`npm run balance` 는 byte-identical"*, *"게이트 7종 CLEAN"* — 을 실제로
점검한 결과, **검증 도구 절반이 검증을 하지 않고 있었다**:

- `web/scripts/balance_compare.ts` (`npm run balance:compare`) — 출력 정규식이
  `/Grade (\d+): ([\d.]+)%/g` 인데 harness 는 그런 형식을 **한 번도 출력하지 않는다**(표 형식).
  매치 0건 → `results[deck] = {}` → **모든 변경에 "No regression detected"**, exit 0.
  게다가 PR 회귀 게이트(`game-balance-test.yml` `regression-check`)가 이 도구를 돌리고 있었다.
- `scripts/wet_run_verify.py --full` (AGENTS.md §3.1-4 가 시키는 canonical 검증) — `jev_check()` 는
  `p = 0.75` **하드코딩**, `balance_check()` 는 2026-10-14 수기 `metrics.json` 을 **읽기만** 한다.
  항상 exit 0. 실행할 때마다 `log.md` 를 오염시킨다.
- 그래서 "byte-identical" 은 **사람이 두 터미널 출력을 눈으로 비교**하는 것에 의존했고, 자동 회귀
  게이트는 사실상 **0개**였다.

한편 나머지 도구들(`check_doc_claims.py` · `audit_vault.py` · `check_no_novel_prose.py` ·
`import_briefings.py --check` · `npm run balance` 자체)은 실측으로 진짜임을 확인했다.

## 결정 (Decision)

**검증 도구를 "진짜"와 "연극"으로 구분하고, 밸런스 회귀를 자동 게이트로 만든다.**

1. **`balance_compare.ts` 폐기** → [`web/scripts/balance_baseline.ts`](../../../web/scripts/balance_baseline.ts) 신설.
   - harness 출력을 파싱해 `opening|veteran|heretic` 3덱의 등급별 곡선을
     [`balance.golden.json`](../../../web/scripts/balance.golden.json) 으로 **기록**한다.
   - `npm run balance:golden` = 기록, `npm run balance:check` = 대조.
     - 기본은 **엄격**(어느 방향이든 드리프트면 exit 1) — 사람의 "byte-identical" 의식을 대체한다.
     - `--allow-improvement` 는 **하락만** 실패시킨다(CI 회귀 게이트용).
   - 위험한 `git stash` / `git checkout main` 을 **제거**한다(golden 이 baseline 이므로 브랜치 전환이 불필요).
2. **CI PR 회귀 게이트 복구** — `regression-check` 가 `npm run balance:check -- --allow-improvement` 를 돌린다.
3. **`mutation spike` 추가** — [`web/scripts/mutation_spike.ts`](../../../web/scripts/mutation_spike.ts)
   (`npm run mutation`). 전투 엔진 상수의 의미를 하나씩 뒤집어, "초록불"이 실제로 깨질 수 있는지 본다.
   이는 **진단 도구이지 게이트가 아니다**(살아남은 변이가 곧 테스트 구멍).
4. **`wet_run_verify.py` 는 이번에 손대지 않는다**(아래 남은 것) — 대신 `docs/design/verification-framework.md`
   에 "연극"으로 표기해 다음 세션이 신뢰하지 않게 한다.

## 결과 (Consequences)

- **드리프트 감지 실증**: `CRIT_CHANCE = 0.15 → 0.0` 을 주입하니 `balance:check` 가
  **18 drift / 9 regression**(예: heretic g5 66.1% → 56.1%)을 출력하고 실패했다. 이전 도구는 같은 변경에
  "No regression" 을 냈을 것이다.
- **mutation spike 첫 측정**: 6 변이 중 **5 KILLED / 1 SURVIVED**.
  - 생존: `AUTO_ATTACK_INTERVAL_MS = 2000 → 1000` — 이 상수의 **값을 고정하는 테스트가 없다**
    (참조하는 테스트는 상수를 import 해 쓰므로 값 변이에 면역).
- **기록 기준선 확정(golden)**: opening `100/100/100/97.1/70.6/47.0` · veteran `100/100/100/96.0/69.4/46.3`
  · heretic `100/100/100/95.2/66.1/42.3` (runs=100). 이전에는 opening 만 인용됐다.
- **검증**: `npm run balance:check` 통과 · `tsc --noEmit` 0 error · `eslint scripts/` 0 error.
- **알려진 한계**: golden 은 **bare runner**(장비·소비·시장 배선은 no-op)를 잰다 — 장비 착용 곡선은
  `npm run gear` 가 따로 담당한다. mutation spike 는 기본 테스트 셋이 좁아, 셋 밖에서만 잡히는 변이는
  SURVIVED 로 보일 수 있다(`--tests` 로 넓힐 것).
- **남은 것**: `wet_run_verify.py` 실배선 또는 폐기 · `check_doc_claims.py` 를 ROADMAP/README 로 확장 ·
  `mixed_language_audit.py` 를 소스(`.py`/`.ts`)로 확장 · 생존 변이(`AUTO_ATTACK_INTERVAL_MS`) 테스트 추가.

## Implementation Status (2026-11-18)

**Status**: 🟡 Partial

**Evidence**:
- `web/scripts/balance_baseline.ts` — golden 기록/대조, 정규식 수정, git 전환 제거
- `web/scripts/balance.golden.json` — 3덱 × 등급 곡선 (runs=100)
- `web/scripts/mutation_spike.ts` — 6 변이 진단
- `web/package.json` — `balance:golden` · `balance:check` · `balance:compare`(호환 별칭) · `mutation`
- `.github/workflows/game-balance-test.yml` — `regression-check` → `balance:check --allow-improvement`
- `docs/design/verification-framework.md` — 도구 인벤토리(진짜/연극 구분)

**Notes**: `wet_run_verify.py` · claim checker 확장 · 혼용 감사 확장은 미착수(위 "남은 것").

## 영향 받는 항목

- `web/scripts/` (검증 스크립트 계층)
- `.github/workflows/game-balance-test.yml`
- `docs/design/verification-framework.md`
- `AGENTS.md` §3.1 / §6 (명령 안내)

## 관련 결정

- ADR-0328 (장비 재조정 — 곡선을 인용하는 쪽)
- ADR-0195 (Implementation status 워크플로우)
- ADR-0211 / ADR-0229 (grade curve rebaseline — 재기록이 필요한 전례)

## 변경 이력

- 2026-11-18: Accepted (검증 도구 메타 감사 → B/A/C 순으로 구현)
