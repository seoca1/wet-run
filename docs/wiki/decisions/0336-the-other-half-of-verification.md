# ADR-0336: 검증의 나머지 절반 — 실 Jev · gear 골든 · prettier 게이트

**상태**: Accepted (오너: *"검증도구 ADR 모두 후속 진행해줘"*)
**날짜**: 2026-11-19
**결정자**: 사용자
**우선순위**: P1 (검증 인프라)

## 컨텍스트 (Context)

ADR-0335 가 검증을 단일 러틴으로 묶었지만, "정직하게 남긴 것" 목록이 남아 있었다. 오너가 그 후속을
전부 진행하라고 위임했다:

1. 실 Jev(보정) 배선 — 러틴은 로컬 advisory 만 돌렸다.
2. prettier 게이트 — `prettier --check` 가 139 파일에서 실패(유지된 불변식이 아니었음).
3. ROADMAP 자동 검사 — 역사 서술 때문에 strict path check 는 노이즈, 그러나 현재 수치는 드리프트했다.
4. gear-worn 골든 — `balance.golden.json` 은 bare runner 한정.
5. mutation 기본 셋 협소 — 6 변이뿐.

## 결정 (Decision)

1. **실 Jev 우선 배선** — `wet_run_verify.py --jev` 가 `scripts/jev-call.sh`(OpenRouter,
   보정됨)를 **먼저** 호출하고, 실패/키 없음일 때만 `jev-local-call.sh`(로컬·미보정)로 폴백한다.
   파서가 두 형식(`{"noul":0.1}` / `answer=no p=…  [local-uncalibrated]`)을 모두 읽고 `calibration`
   필드에 출처를 적는다. **여전히 advisory — 게이트 아님.**
2. **ROADMAP counts-only 검사** — `check_doc_claims.py` 에 `--counts-only` 추가. 기본 가이드는
   AGENTS.md(전체) · README.md(전체) · **ROADMAP.md(numbers only)**. ROADMAP 의 역사 서술 경로는
   건너뛰되 현재 수치는 드리프트 시 실패.
3. **mutation 셋 확장** — 6 → **10 변이**(combo window · armor bypass cap · stagger · alarm tick 추가) +
   기본 테스트 셋 10 파일(adr0320 · status · combat_status_feedback · idle_tick · adr0327). 결과 **10/10 KILLED**.
4. **gear 골든 게이트** — `gear_curve_probe.ts` 의 계산을 `gearCurve()` 로 추출(import 무부작용, `--json`
   지원). 신규 `gear_baseline.ts` + `gear.golden.json`(encounter/mission × 5 세트 × 6 등급).
   `npm run gear:golden` / `gear:check`. 러틴에 **1b 게이트**로 편입.
5. **prettier 정규화 + 게이트 승격** — `.prettierrc.json`(printWidth 100, AGENTS.md 의도)로 **138 파일**
   정규화(`+1079/−3323`). `ci.yml` 에 format 검사 추가(실 게이트), delegation 의 format 단계는
   advisory 표기 제거. `.prettierrc.json` 은 이제 강제된다.

## 결과 (Consequences)

- **러틴 = 게이트 9종 + advisory Jev**: `python3 scripts/wet_run_verify.py --full` →
  balance · **gear** · tests · audit · doc_claims · prose · briefings · links · lang + Jev(실).
- **실 Jev 확인**: `answer=null p=0.21 calibration=primary source=jev-call.sh`, exit 0(러틴 불변).
- **mutation 10/10 KILLED**(6/6 → 10/10, armor-bypass-off 는 adr0327 테스트로 커버).
- **gear 골든**: bare 미션 행 `100/100/83/83/26/42` 가 기록 기준선과 일치, bare 제외 4 세트도 고정.
- **prettier 게이트**: `prettier --check "src/**/*.{ts,tsx}"` → *All matched files use Prettier code style!*
  이후 typecheck 0 · lint 0 · build OK · vitest **4444** pass 유지.
- **ROADMAP 수치 자동 검사 편입** → ADR 범위 드리프트가 즉시 드러남(0334→0335 교정).
- **워크스페이스 무변경**: `check_doc_claims.py`(wet_run)·러틴만.

## Implementation Status (2026-11-19)

**Status**: ✅ Implemented

**Evidence**:
- `scripts/wet_run_verify.py` — 실 Jev 우선 · gear 게이트(1b) · `_parse_jev`
- `Game/wet_run/scripts/check_doc_claims.py` — `--counts-only`, ROADMAP 기본 편입
- `web/scripts/mutation_spike.ts` — 10 변이 / 10 테스트 파일
- `web/scripts/gear_curve_probe.ts` — `gearCurve()` 추출 · `--json` · import 무부작용
- `web/scripts/gear_baseline.ts` · `gear.golden.json` · `package.json`(`gear:golden`/`gear:check`)
- `web/.prettierrc.json` + 138 src 파일 정규화 · `.github/workflows/ci.yml`(format 게이트)
- `Game/wet_run/ROADMAP.md` — ADR 범위 0001–0335 교정

**Notes**: prettier 정규화는 대규모(138 파일) — 이후 포맷 드리프트는 이제 CI 가 막는다. 실 Jev 는
보정됐지만 여전히 advisory(§6 자동 게이트 아님). mutation 은 기본 셋 밖 변이를 못 잡을 수 있다.

## 영향 받는 항목

- `scripts/wet_run_verify.py`, `Game/wet_run/scripts/check_doc_claims.py`
- `Game/wet_run/web/scripts/{mutation_spike,gear_curve_probe,gear_baseline}.ts`
- `Game/wet_run/web/src/**` (포맷), `web/.prettierrc.json`
- `.github/workflows/ci.yml`, `delegation-verification.yml`
- `docs/design/verification-framework.md`, `AGENTS.md`, `README.md`, `ROADMAP.md`

## 관련 결정

- ADR-0333 (메타 감사) · ADR-0334 (실패할 수 없는 검사기) · ADR-0335 (단일 러틴)
- ADR-0326 (방어 단계) · ADR-0327 (programPower) · ADR-0328 (장비 재조정) — gear 골든이 지키는 대상

## 변경 이력

- 2026-11-19: Accepted (후속 5건: 실 Jev · ROADMAP · mutation · gear 골든 · prettier 게이트)
