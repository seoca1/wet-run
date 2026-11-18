# ADR-0332: `extraEffect` 는 실행되지 않는다 — whitelist resolver

**상태**: Accepted (오너 결정: *"extraEffect resolver 계속"*)
**날짜**: 2026-11-18
**결정자**: 사용자
**우선순위**: P1 (전투 · 안전)

## 컨텍스트 (Context)

제안서 §4 의 마지막 미배선 스탯: *"`extraEffect` | 카드/장비 발동 시 `resolveExtraEffect(effect, context)`라는
**whitelist resolver**만 호출. **임의 문자열 실행 금지**."*

`extraEffect` 는 카탈로그에 **자유 텍스트**로 저작되어 있다("Immune to flatline (one revive per run)",
"Heals 2 HP per turn (poison immune)", …). 아무도 읽지 않았으므로 지금까지는 표시용 문자열이었고,
그것이 곧 **안전 규칙**이 필요하다는 뜻이다 — 문자열이 코드가 되면 안 된다.

## 결정 (Decision)

**whitelist resolver 를 만들고, 두 동작을 배선한다** ([`extra_effects.ts`](../../../web/src/core/state/extra_effects.ts)):

- **`resolveExtraEffects(effect)`** 는 저작된 **marker → 동작 id** 표만 본다. 표에 없는 문자열은 **아무 일도 하지 않는다**.
- 매칭은 **부분 문자열**이다 — `addStats` 가 장비 여러 개의 효과를 `", "` 로 이어 붙이므로, 한 문자열이 여러 동작을
  가리킬 수 있다.
- 동작 6종을 **이름만** 등록한다: `revive_once` · `nano_regen` · `matrix_stealth` · `matrix_speed` · `zion_support` ·
  `ice_omniscience`. **이번에 배선한 것은 둘**:
  - **`revive_once`** (MASTER_BODY) — 플랫라인 직전에 최대 HP **30%** 로 한 번 살아난다. **런당 1회**
    (`state.reviveUsed`, 계약 다리 사이에도 유지).
  - **`nano_regen`** (NANO_HIVE) — 매 enemy phase **2 HP** 회복.
- 나머지 4종은 **이름만** 등록되어 inert 다(각자 훅이 필요한 별도 슬라이스).

## 결과 (Consequences)

- **문자열은 코드가 아니다**: 표에 없는 `extraEffect` 는 아무 효과가 없다(테스트가 hostile 문자열을 고정).
- **기록 기준선 byte-identical**: `npm run balance` **100/100/100/97.1/70.6/47.0** — 하네스는 `EMPTY_LOADOUT` 이라
  `extraEffect` 가 비어 있고, 두 동작 모두 발동하지 않는다.
- **검증**: vitest **236 files / 4443 tests**(신규 `adr0332_extra_effects` 7) · typecheck/lint 0 error · build OK · 게이트 7종 CLEAN.
- **남은 것**: `matrix_stealth` · `matrix_speed` · `zion_support` · `ice_omniscience` 훅(각각 매트릭스/전투 경로) ·
  AP 자원 · 플레이어 스킬 · 시장 가격·소비 아이템 수치 확정(오너) · 장비 파워↔난이도 동시 설계(오너).
