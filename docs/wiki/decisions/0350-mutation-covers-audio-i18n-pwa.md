# ADR-0350: mutation 을 오디오·i18n·PWA 까지 — 또 값 미고정 상수

**상태**: Accepted (오너: *"계속"*)
**날짜**: 2026-11-22
**결정자**: 사용자 (AI 위임)
**우선순위**: P1 (검증)

## 컨텍스트 (Context)

mutation 셋이 전투·엔딩·경제·매트릭스·카드·팩션·세이브를 덮은 뒤(ADR-0333~0349), 남은 표면
(오디오·i18n·PWA)으로 넓힌다.

## 결정 (Decision)

**변이 3건 추가.**

- `audio/manager.ts` `BGM_DUCK_FACTOR = 0.8 → 0.5`
- `i18n.ts` `DEFAULT_I18N_STATE.language = "en" → "ko"`
- `pwa_manager.ts` `INITIAL_PWA_STATE.canInstall = false → true`
- 기본 셋에 `audio_ducking` · `i18n` · `pwa_manager` 테스트 추가(30 변이, 20 테스트 파일).

## 결과 (Consequences)

- **30/30 KILLED.**
- **또 값 미고정 상수**: `bgm-duck-factor`(0.8→0.5)가 **SURVIVED**. `audio_ducking.test.ts` 가
  `BGM_DUCK_FACTOR` 를 **import** 해 `duckFactorFor(...).toBeCloseTo(BGM_DUCK_FACTOR)` 로 검사하므로
  **경계와 값이 함께 움직인다** — 상수 **값(0.8)**은 아무도 고정하지 않았다(쿼터 밴드 ADR-0349 와 동일 유형).
  - 픽스: `expect(BGM_DUCK_FACTOR).toBe(0.8)` 한 줄. 추가하니 **KILLED**(1).
- **i18n·PWA 는 즉시 KILLED**(각 1) — 기본 상태 필드가 잘 고정돼 있다.
- **패턴 확정**: 생존 변이는 (a) 누락 테스트 파일 (b) 값 미고정 상수(테스트가 상수를 import). 후자는
  **계약 테스트**가 유일한 픽스다.
- 검증: mutation **30/30** · vitest **237 files / 4456 tests** · typecheck 0 · 러틴 8/8.

## Implementation Status (2026-11-22)

**Status**: ✅ Implemented

**Evidence**:
- `web/scripts/mutation_spike.ts` — 변이 3 + 오디오/i18n/PWA 테스트 3파일
- `web/tests/audio_ducking.test.ts` — `BGM_DUCK_FACTOR` 값 계약 테스트(1)
- 실행: `npm run mutation` → **30/30 KILLED**

**Notes**: 남은 모듈(그래픽 노블·던전 크롤러 등)은 후속. 값 미고정 상수는 계약 테스트로 계속 픽스.

## 영향 받는 항목

- `web/scripts/mutation_spike.ts` · `web/tests/audio_ducking.test.ts`

## 관련 결정

- ADR-0333 / ADR-0349 (값 계약 테스트) · ADR-0345 / ADR-0348 (누락 테스트 파일)

## 변경 이력

- 2026-11-22: Accepted (오디오·i18n·PWA 확대 → 30/30; 값 미고정 상수 하나 픽스)
