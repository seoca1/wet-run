# ADR-0349: mutation 을 세이브 파이프라인까지 — 그리고 값이 안 잡힌 상수

**상태**: Accepted (오너: *"응 진행해"*)
**날짜**: 2026-11-22
**결정자**: 사용자 (AI 위임)
**우선순위**: P1 (검증)

## 컨텍스트 (Context)

mutation 셋이 전투·엔딩·경제·매트릭스·카드·팩션을 덮은 뒤(ADR-0333~0348), 세이브 파이프라인으로
넓힌다 — 압축 임계, 쿼터 밴드, 슬롯 수, 스키마 버전. 세이브는 게임 상태의 유일한 영속 경로라
조용히 망가지면 손실이 크다.

## 결정 (Decision)

**변이 4건 추가.**

- `compress.ts` `COMPRESSION_THRESHOLD_BYTES = 512 → 1024`
- `storage_quota.ts` `STORAGE_QUOTA_WARNING_PERCENT = 80 → 70`
- `storage.ts` `MANUAL_SLOT_COUNT = 3 → 2`
- `storage.ts` `CURRENT_SCHEMA_VERSION = 1 → 2`
- 기본 셋에 `compress` · `save_compression_size` · `storage_quota` · `storage` · `state_save` 테스트 추가.

## 결과 (Consequences)

- **27/27 KILLED.**
- **진짜 구멍 하나(이번엔 누락이 아니라 값)**: `quota-warn-band`(80→70)가 **SURVIVED** 였다.
  `storage_quota.test.ts` 는 임계를 **import 한 상수로** 검사한다 —
  `quotaLevel(STORAGE_QUOTA_WARNING_PERCENT)`. 경계와 값이 **함께 움직이므로**, 상수의 **값**을
  바꿔도 테스트가 통과한다. 즉 **임계의 값(80/95)은 아무 테스트도 고정하지 않았다.**
  - 픽스: 계약 테스트 한 줄 추가 — `expect(STORAGE_QUOTA_WARNING_PERCENT).toBe(80)` ·
    `...CRITICAL...).toBe(95)`. 추가하니 **KILLED**(1).
- **압축 임계·슬롯 수·스키마 버전은 즉시 KILLED**(1·4·9) — 이미 잘 고정돼 있다.
- **교훈 분류**: 이번 세션의 생존 변이는 두 종류였다.
  - **누락된 테스트 파일**(매트릭스 ADR-0345 · 카드 ADR-0348) → 셋을 넓히면 죽는다.
  - **상수를 import 해 값이 안 잡힘**(쿼터 밴드, 그리고 초기 `AUTO_ATTACK_INTERVAL_MS` ADR-0333) → 계약 테스트가 필요하다.
- 검증: mutation **27/27** · vitest **237 files / 4455 tests** · typecheck 0 · 러틴 8/8.

## Implementation Status (2026-11-22)

**Status**: ✅ Implemented

**Evidence**:
- `web/scripts/mutation_spike.ts` — 변이 4 + 세이브 테스트 5파일
- `web/tests/storage_quota.test.ts` — 밴드 값 계약 테스트(1)
- 실행: `npm run mutation` → **27/27 KILLED**

**Notes**: 남은 모듈(오디오·i18n·PWA 등)은 후속. "값 계약 테스트" 패턴을 다른 미고정 상수에도 적용 가능.

## 영향 받는 항목

- `web/scripts/mutation_spike.ts` · `web/tests/storage_quota.test.ts`

## 관련 결정

- ADR-0333 (mutation + `AUTO_ATTACK_INTERVAL_MS` 값 고정) · ADR-0345 · ADR-0348 (누락 테스트 파일)

## 변경 이력

- 2026-11-22: Accepted (세이브 파이프라인 확대 → 27/27; 값 미고정 상수 하나 픽스)
