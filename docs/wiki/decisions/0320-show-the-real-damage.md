# ADR-0320: 실피해를 보여주고, 맞은 것을 느끼게 한다

**상태**: Accepted
**날짜**: 2026-11-18
**결정자**: 사용자 (오너 지시: *"실피해를 드러낼 뿐 아니라 이펙트로 확 느껴지게 해야 성장 욕구를 자극할 수 있을 거야"*)
**우선순위**: P1 (성장 · 피드백)

## 컨텍스트 (Context)

ADR-0319 로 회복이 자동이 되면서 **전리품 정지가 성장의 자리**가 됐다. 그런데 성장이 **보이지 않았다.**

플레이어 카드의 피해는 `tier × 5` 에서 **ICE 의 armor 를 통째로 빼는** 구조다(`state_actions_programs.ts` → `combat_engine.ts`). 그래서 **같은 카드도 상대에 따라 값이 완전히 다르다** — 실측(armor 9 기준):

| 카드 | tier | armor 0 | armor 9 |
| --- | --- | --- | --- |
| `strike` | 1 | 4-6 | **1** |
| `goliath` | 3 | 12-18 | 5-11 |
| `exploit` (armor 50% 무시) | 3 | — | 9-15 |
| `kraken` | 5 | 20-30 | 13-23 |
| 고유 | 6 | 24-36 | 17-29 |
| `kraken` **콤보 5(×2.0)** | 5 | — | **31-50** |

**화면에는 아무것도 없었다.** 손패는 `1 STRIKE COST +1 TARGET ICE` 만 말했고, ICE 는 HP 만 보여줬으며, `strike` 가 **1** 을 때린 순간과 `kraken` 이 **23** 을 때린 순간의 연출이 **완전히 같았다**(같은 `ice_hit` 플래시 + 같은 크기의 숫자). 그래서 armor 는 보이지 않는 규칙이었고, 덱의 성장은 **느낄 수 없는 숫자**였다.

## 결정 (Decision)

**⑴ 실피해를 드러낸다. ⑵ armor 를 숫자로 만든다. ⑶ 맞은 것을 크기에 따라 다르게 느끼게 한다.**

### ⑴ 손패 행에 실피해 열 (ADR-0251 rule 5 준수)

- 각 행이 **그 카드가 지금 조준한 ICE 에게 넣을 피해 범위**를 말한다: `2 STRIKE +1  1` · `4 KRAKEN +4  13-23`.
- **범위인 이유**: `calculateDamage` 가 0.8~1.2 변동을 곱한다. 한 숫자는 거짓말이 된다.
- **크리티컬은 범위에 넣지 않는다** — 15% 스파이크를 섞으면 흔한 경우가 거짓처럼 보인다. 크리는 자기 연출을 가진 별개 사건이다.
- **킬 예측이 아니다**(rule 5): "얼마나 세게 때리는가"지 "끝난다"가 아니다.
- 콤보도 반영한다(`COMBO_BONUSES[playerCombo+1]`) — 다음 타격의 콤보는 지금 쌓이는 콤보다.
- 좁은 화면(40열)에서는 **TARGET 열을 피해가 대신한다**(둘 다는 안 들어간다). 전지역 카드는 `*` 로 표시하고, 범례가 `DMG` 로 바뀐다.

### ⑵ ICE 줄에 armor

- 이름 줄이 `> [1] ALEPH  A7` 로 끝난다. 이름이 먼저 양보한다 — armor 가 카드의 값을 바꾸는 쪽이다.
- 40열에서는 이름을 잘라 넣는다(가드가 잘림을 감시).

### ⑶ 연출이 피해에 비례한다

| 상황 | 이전 | 이후 |
| --- | --- | --- |
| armor 가 먹은 타격(피해 ≤1) | `ice_hit` 플래시 + `HIT! -1` | **`armor_block`** — 전폭 플래시 **없음**, `✧ … ✧` + `ARMOR — STRIKE absorbed`, 떠오르는 숫자 대신 회색 `ARMOR` |
| 큰 타격(≥20) | 화면 정지 | **캔버스 흔들림 3px**(플레이어 피격은 2px) — **넣은** 타격이 **맞은** 타격보다 크게 |
| 작은 타격 | 흔들림 없음 | 흔들림 없음(작은 타격이 조용해야 흔들림이 의미를 가진다) |

새 VFX 종류 `armor_block` 은 `pickProgramVfxKind` 가 `damage <= 1` 인 공격 카드에 대해 반환한다(방어/서포트 카드는 제외 — 그건 애초에 타격이 아니다).

## 결과 (Consequences)

- **무영향**: `npm run balance` **byte-identical**(100/100/100/98.9/83.9/32.3). VFX 는 RNG 를 쓰지 않고(`import_vfx` 는 결정적), 흔들림은 기존 인스턴스에서 파생되며, 손패 행은 표시 전용이다.
- **검증**: vitest **225 files / 4346 tests**(ADR-0320 신규 13) · typecheck 0 · lint 0 errors · story trace 3다리 완주 · e2e 통과.
- **접근성**: 터치 라벨과 aria 라벨이 같은 사실(피해 범위)을 말한다(`touchAffordanceLines` · `affordanceAriaLabel`).

### ⚠️ 함께 찾은 결함 두 개

1. **전투 화면이 ADR-0300 텍스트 잘림 가드 밖에 있었다.** 가드는 `renderRunScreen` 을 쓰는데, 그 함수의 `switch (state.runPhase)` 에 **`combat` 케이스가 없다**(전투는 `renderCombatScreen` 이다). 그래서 가드가 전투에서 **아무것도 렌더하지 않고 통과**하고 있었다 — 즉 40열에서 전투 텍스트가 잘려도 아무도 몰랐다.
2. **그 결과로 ICE HP 바가 40열에서 잘린다**: `healthBar` 는 **고정 12칸**(대괄호 포함 14자)인데 ICE 열이 20에서 시작해 가용 폭이 18자뿐이라 `165/165` 의 숫자가 사라졌다. **수정**: 바가 가용 폭에 맞춰 줄어든다(`barCells = clamp(room - 숫자 - 3, 3, 12)`). 가드는 이제 `renderCombatScreen` 으로 전투를 실제로 렌더한다.

## Implementation Status (2026-11-18)

**Status**: ✅ Implemented

**Evidence**:
- `web/src/core/combat/damage_preview.ts` — `effectiveDamageFor` · `formatDamageRange`(순수, 리듀서와 같은 순서)
- `web/src/core/combat/program_affordance.ts` — `damage` 열 · 두 가지 행 모양 · `COMPACT_HAND_HEADER_DMG`
- `web/src/renderer/combat_grid.ts` — ICE `A{n}` · 손패 피해 열 · **HP 바 폭 맞춤**
- `web/src/core/state/state_helpers.ts` — `pickProgramVfxKind` → `armor_block`
- `web/src/renderer/screen_shake.ts` — `ICE_HIT_SHAKE_MIN_DAMAGE` · `ICE_HIT_SHAKE_MAGNITUDE_PX`
- `web/src/renderer/floating_damage.ts` · `combat_vfx_render_combat.ts` — `blocked` 분기 · `armor_block` 프레임
- `web/tests/adr0320_effective_damage.test.ts` — 13 tests(armor 계산 · **리듀서가 낼 수 있는 모든 굴림을 범위가 포함** · 화면 표시 · 연출)
- `web/tests/adr0300_no_text_is_cut_off.test.ts` — 전투 케이스가 `renderCombatScreen` 을 쓰도록 수정(가드가 실제로 렌더하게)

**Notes**: 피해 범위는 **크리를 제외**한다(별개 연출). 40열에서는 TARGET 열을 피해가 대신하고 전지역 카드는 `*`. 이 ADR 은 **표시 전용**이라 밸런스 곡선을 움직이지 않는다 — 성장 계획(`docs/design/growth-plan-2026-11-18.md`)의 P1-1/P1-2 를 부분적으로 이행한다.

## 관련 결정

- ADR-0251 — 손패 행은 화면이 할 일을 말한다 (rule 5: 킬 예측 금지)
- ADR-0257 — 카드의 효과를 행에 적는다 (이 문서가 피해를 더한다)
- ADR-0300 — 맞지 않는 줄은 빌드를 실패시킨다 (이 문서가 **전투를 가드 안에 넣는다**)
- ADR-0231 — VFX 스폰은 RNG 중립 (이 문서의 새 종류도 그렇다)
- ADR-0319 — 전투 후 회복은 자동 (성장 자리를 비웠다)
- ADR-0318 (f) · ADR-0319 — 등급이 아니라 **armor** 가 관문

## 변경 이력

- 2026-11-18: Accepted (오너 지시) + 구현 + 전투 텍스트 가드 결함 2건 수정
