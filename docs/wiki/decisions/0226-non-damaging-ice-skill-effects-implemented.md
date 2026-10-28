# ADR-0226: Non-damaging ICE 스킬 효과를 구현한다 (ADR-0219 Option A — `defensive` / `support` 가 더 이상 cosmetic 이 아니다)

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — dead combat path, ADR-0216/0219/0222/0223/0224/0225 sibling)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0161 — ICE personality archetypes](./0161-ice-personality-archetypes.md), [ADR-0216 — derived ICE skill metadata](./0216-derived-ice-skill-metadata.md), [ADR-0218 — ICE skill selection fallback](./0218-ice-skill-selection-fallback.md), [ADR-0219 — non-damaging ICE 스킬 효과](./0219-non-damaging-ice-skill-effects.md), [ADR-0222 — ICE 스킬 메타데이터가 authored data 로 이동한다](./0222-ice-skill-metadata-as-data.md), [ADR-0223 — 스킬 분류 review pass](./0223-skill-classification-review.md), [ADR-0224 — Encounter band 커버리지 확대](./0224-encounter-band-coverage.md), [ADR-0225 — Encounter band 재캘리브레이션](./0225-encounter-band-recalibration.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-27 에 결정·구현·검증까지 완료되었다.
> 구현 범위는 **ADR-0219 의 Option A** — `shield` / `heal` / `regen` / `buff` 네 개의
> 효과 계열과 그 magnitude authoring, 그리고 combat path 배선이다.
>
> **핵심은 이것이다: `defensive` / `support` archetype 가 더 이상 cosmetic 이 아니다.**
> ADR-0219 가 Option B (selection 일관성만) 를 채택하고 Option A 를 연기했을 때,
> `PERSONALITY_SKILL_PREFERENCE` 의 `shield` / `heal` / `regen` / `buff` 항목은
> **관측 불가능한 의도 표기**였다. 지금은 실제 전투 semantics 를 가진다.
>
> **재캘리브레이션은 하지 않았다 — 필요하지도 않았다.** 밸런스 이동은
> **단 하나의 grade 에서 +0.2pp** 뿐이었다 (실측, 아래 Evidence).

## 컨텍스트 (Context)

### ADR-0219 가 남긴 것

ADR-0219 는 non-damaging ICE 스킬 효과의 운명을 결정했다. 채택된 것은
**Option B (Consistency-only)** — `selectSkillByPersonality` 가 combat path 가
발사할 수 있는 스킬 (`damage > 0`) 만 반환하도록 제한했을 뿐, 효과 자체는
구현하지 않았다. 그 ADR 은 추천안에서 **B → D → A 순차**를 명시했다:

1. **B** — selection 일관성만 (채택·구현됨, ADR-0219)
2. **D** — 88개 스킬 메타데이터를 authored data 로 (채택·구현됨, ADR-0222)
3. **A** — 효과 메커닉 구현 + magnitude authoring + 밸런스 재측정 (이번 ADR)

D 는 ADR-0222 가 실행했고 (88 entry `skill_defs`), 그 사이
ADR-0223 이 20 개의 `effect` 분류를 정정했고, ADR-0224 가 encounter band 의
slot 1–3 을 교체해 스킬 시스템을 플레이에 노출했고, ADR-0225 가 그 곡선을
재캘리브레이션했다. **연쇄의 마지막 조각이 남아 있었다.**

### 남아 있던 gap — 구조적으로 발사 불가능한 효과

ADR-0219 가 기록한 그대로:

- production combat path 의 발사 조건은 `selectedSkill.damage > 0` 이다
  (`web/src/core/state_actions_combat.ts`).
- `damage` 는 loader 가 **파생**한다 — non-damaging effect 면 0
  (`web/src/core/ice_skills.ts:200`).
- 따라서 `shield` / `heal` / `regen` / `buff` 를 가진 스킬은 **발사 자체가
  불가능**했다. `usedSkill` 가 false 로 남고 plain auto-attack 으로 fall through 한다.
- `PERSONALITY_SKILL_PREFERENCE` 의 `defensive` / `support` 상위 선호는 **전부**
  발사 불가 effect 다 (`web/src/core/ice_ai.ts:163-171`).

ADR-0222 / 0223 이 데이터 정합성을 해결했고 ADR-0224 / 0225 가 밸런스를
안정시켰으므로, **남은 것은 메커닉 그 자체였다.**

### 데이터는 준비되어 있었다 — magnitude authoring 만 남았다

ADR-0222 가 만든 `skill_defs` 에는 `name` / `effect` / `cooldown_ms` 가 있고,
**값이 없었다** — `shield` 가 몇을 흡수하는지, `heal` 이 몇을 회복하는지에 대한
source data 가 없었다. ADR-0223 이 20 개의 분류를 정정하며
`shield` / `heal` / `regen` / `buff` 의 소속을 확정했다. **이제 그 계수만 저술하면
메커닉이 붙는다.**

### Enemy 측 상태 — shield 를 표현할 곳이 없었다

`StatusEffectKind` union (`web/src/core/types.ts:243-257`) 에 `shield` 가 없었다.
`StatusEffectInstance` 에는 어느 ICE 의 효과인지 가리킬 필드도 없었다.
parallel collection 을 새로 만드는 것은 두 개의 source of truth 를 만드는 일이다 —
**기존 `statusEffects` 배열을 확장하는 쪽**을 택했다.

## 결정 (Decision)

### `shield` — 흡수 풀 하나

- **ICE 당 하나의 흡수 풀.** 기존 `statusEffects` 배열 안의
  `kind: "shield"` instance 로 저장한다. `magnitude` = 남은 흡수 HP,
  `remaining` = enemy tick 단위 남은 수명.
- **들어오는 player 피해는 HP 에 닿기 전에 풀만큼 감소한다.** 남는 부분만 HP 에
  닿는다 (`web/src/core/state_actions_programs.ts:129`).
- **풀은 흡수한 만큼 줄고, 소진되면 제거된다** — `docs/testcases/combat/depth.md`
  TC-DEPTH-005 ("Shield status 가 consumed (제거)") 참조.
- **재시위는 풀에 더하지만 수명은 갱신한다** (duration 이 늘어나지 않는다) —
  `docs/testcases/combat/depth.md` TC-DEPTH-004 ("state.shield = 2, wisp duration
  refresh (5s from now)") 참조.
- **수명 3 tick = 6000 ms.** 1 tick 은 enemy turn 하나, 즉
  `AUTO_ATTACK_INTERVAL_MS` (`web/src/core/combat_engine.ts:10` — 2000 ms) 한 창이다.
- **Burn / DoT 피해는 풀을 우회한다.** 그것은 "incoming player damage" 가 아니다 —
  `status.ts` 의 tick 경로로 들어온다.

### `heal` — 즉시 회복, `maxHp` 상한

즉시 HP 를 회복하되 **절대 `maxHp` 를 넘지 않는다.**

### `regen` — tick 당 회복, `maxHp` 상한

enemy tick 마다 `healPerTick` 만큼 회복한다. `maxHp` 상한. **수명 4 tick = 8000 ms.**

### `buff` — flat 공격력 보너스

ICE 의 **스킬 피해와 auto-attack 양쪽**에 붙는 flat 보너스. **수명 3 tick.**
**grade / boss multiplier 적용 *뒤* 에 더한다** — 임시 buff 가 모든 grade 에서
동일한 flat 금액만큼의 가치를 갖게 하기 위해서다
(`web/src/core/state_actions_combat.ts:304`).

### Magnitude 는 authored data 다

`skill_defs` (`web/src/data/ice_types.json`) 에 `magnitude` 를 저술한다:

```
magnitude = dmg_base(owner) × multiplier
```

multiplier 는 **shield 2 / heal 2 / regen 1 / buff 1**. 여러 owner 를 가진 스킬은
**`dmg_base` 가 가장 높은 owner 가 canonical** 이다.

**28 entry 를 저술했다** — shield 9 / buff 17 / heal 1 / regen 1.

| skill id | effect | owner (`dmg_base`) | magnitude |
| --- | --- | --- | --- |
| `vault_guard` | shield | `ta_sentinel` (7) | **14** |
| `defense_grid` | shield | `hosaka_defender` (6) | **12** |
| `fortress_mode` | shield | `goliath_ascended` (10) | **20** |
| `data_preserve` | heal | `sense_net_archive` (4) | **8** |
| `undead_resilience` | regen | `loa_zombie` (3) | **3** |
| `ai_negotiate` | buff | `wintermute_proxy` (18) | **18** |

loader 는 **잘못된 `magnitude` 에 throw 한다** (`web/src/core/ice_skills.ts:136`) —
ADR-0222 가 "미지의 skill id 는 throw" 로 세운 원칙과 같은 취급이다.

### Selection policy — 발사 가능한 스킬의 정의가 넓어진다

`selectSkillByPersonality` 은 스킬을 **발사 가능 (fireable)** 으로 볼 때
**다음 중 하나**를 만족해야 한다:

1. **피해를 준다** (`damage > 0`) — **기존 게이트는 그대로 보존된다.** 아니면
2. 그 effect 가 **구현된 계열** (`shield` / `heal` / `regen` / `buff`) 이고
   **그 archetype 의 preference list 가 그 effect 를 지목한다.**

2번의 archetype 절이 핵심이다 — `shield` 스킬을 가진 `aggressive` ICE 는 flavor 다.
`aggressive` / `stealth` 의 list 는 구현된 계열을 **아무것도 지목하지 않으므로**
그들의 행동은 **변하지 않는다.** `defensive` / `support` 만 이들을 지목한다.

**fallback 은 *피해를 주는* 스킬을 선호한다** — 그래서 `loa_entity`
(`manifest_form` buff + `voodoo_curse` poison) 은 여전히 공격한다.

### `defensive` 에는 두 regime 이 있다

ADR-0161 은 DEFENSIVE archetype 를 *"prefer shields when HP < 50%"* 로 정의한다.
무조건적 선호를 그대로 쓰면 **shield 스킬을 가진 defensive ICE 가 영원히
shield 만 치고 공격하지 않게 된다.** 그래서:

- **`DEFENSIVE_HP_THRESHOLD` 이상**이면 **싸우러 간다** (피해 스킬 우선).
- **미만**이면 **shield / heal / regen / buff** 를 우선한다.

`DEFENSIVE_HP_THRESHOLD` (`web/src/core/ice_ai.ts:310` — 0.5) 와
`shouldDefensiveAct` 은 이미 repo 에 있었다. 이번에 그 **의미가 실제 발사에
연결되었다.**

### State — 기존 배열을 확장한다

parallel collection 을 만들지 않고 **기존 `statusEffects` 배열**을 확장했다.

- `StatusEffectKind` 에 `"shield"` 추가 (기존 member 는 변경 없음).
- `StatusEffectInstance` 에 optional `iceIndex` 와 `tickSource` 추가.
  - `iceIndex` 는 **roster slot** 이다 — catalog id 가 아니다. roster 는 **같은 id 를
    두 마리** 담을 수 있고, encounter band 가 node 에 id 가 부족하면 id 를 반복해서
    채운다. `web/tests/tick_kill_loot.test.ts` 가 이걸 증명한다.
  - `tickSource` — `"player"` 가 default (역사적 동작), ICE 가 시전한 효과는
    `"enemy"`.
- `tickStatus` 는 **enemy-sourced 효과를 건너뛴다** (`web/src/core/status.ts:63`).
  `tickIceEffects` 가 enemy turn 에서 그들을 진전시킨다.
- roster 의 ICE 는 이제 **`maxHp` 를 carry 한다** (`web/src/core/state_actions_phases.ts:73`).
  catalog row 에는 `maxHp` 가 없다 — HP 는 `hp_base` / `hp_per_grade` 에서
  파생되니까. heal cap 의 기준이 이것이다.
- reducer 는 **pure 이고 deterministic** 이다 — module-level mutable state 없음.

### 수용한 trade-off — per-skill magnitude 는 owner 의 개별 능력을 무시한다

`skill_defs` 는 **스킬 단위**인데 ICE 의 위력은 **row 단위**다. 그래서 고정된
per-skill magnitude 는 owner 의 개별 강도를 무시한다. 예를 들어 `construct_proxy`
는 tier 4/5/6 (dmg_base 9/12/13/18) 이 소유하는데 **단일 값 18** 을 갖는다 —
**tier-4 owner 는 과하게 buff** 된다.

load-time derivation 대신 authoring 을 택한 이유는 ADR-0222 의 방향이
**"authored data, not heuristics"** 이기 때문이다. 파생하면 다시 heuristic 이 되고,
그것은 ADR-0222 가 폐기한 것이다.

## 결과 (Consequences)

### 실측 — 밸런스 이동은 한 grade 의 +0.2pp 뿐이다

**Opening deck** (`npm run balance`, 100 runs/mission) — BEFORE (ADR-0225) → AFTER:

| grade | BEFORE | AFTER | delta |
| --- | --- | --- | --- |
| g1 | 100.0% | 100.0% | 0.0pp |
| g2 | 88.6% | 88.6% | 0.0pp |
| g3 | 73.1% | 73.1% | 0.0pp |
| **g4** | **48.8%** | **49.0%** | **+0.2pp** |
| g5 | 43.1% | 43.1% | 0.0pp |
| g6 | 0.0% | 0.0% | 0.0pp |

**PPL (developed) deck** (`npm run balance -- --deck ppl`, 100 runs/mission):

| grade | BEFORE | AFTER | delta |
| --- | --- | --- | --- |
| g1 | 100.0% | 100.0% | 0.0pp |
| g2 | 77.9% | 77.9% | 0.0pp |
| g3 | 97.8% | 97.8% | 0.0pp |
| **g4** | **88.8%** | **89.0%** | **+0.2pp** |
| g5 | 44.4% | 44.4% | 0.0pp |
| g6 | 31.3% | 31.3% | 0.0pp |

나머지 column (turns, HP-end, stalled, p5/p95) 은 **동일**하다 — 유일한 예외는
PPL g4 의 p95 (26 → 29).

### 왜 그렇게 작은가 — 실측

**reach 가 작다.** `ta_sentinel` (`defensive`, `vault_guard` shield, magnitude 14) 이
**g4 band slot 3** 이고, **24-slot band 전체에서 archetype 가 구현된 계열을 지목하는
유일한 ICE** 다.

나머지 band slot 들의 효과 스킬은 `aggressive` ICE 의 것이라 **설계대로 inert** 다:

| band slot | personality | 구현 계열 스킬 |
| --- | --- | --- |
| g1 slot 3 `hosaka_courier` | `aggressive` | `packet_route` buff, `priority_delivery` buff |
| g2 slot 1 `sense_net_spin` | `aggressive` | `alibi_construct` buff |
| g2 slot 3 `loa_zombie` | `aggressive` | `undead_resilience` regen |
| g3 slot 1 `hosaka_defender` | `aggressive` | `defense_grid` shield |
| g5 slot 2 `loa_entity` | `aggressive` | `manifest_form` buff |
| g6 slot 3 `aleph` | `aggressive` | `aleph_fragment` buff |

### 재캘리브레이션은 하지 않았고, 필요하지도 않았다

**calibration 배열과 band 는 그대로다.** `ENCOUNTER_HP_BY_GRADE` 와
`ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` 는 **미변경**이고, `ENCOUNTER_ICE_BY_GRADE` 도
미변경이다.

g4 의 49.0% 는 ADR-0211 target (47.4%) 대비 **+1.6pp** 로, ADR-0225 가 세운
**±3pp 허용 오차 안**이며, opening 곡선은 **단조 비증가 (monotonic non-increasing)** 를
유지한다.

### 긍정적 영향

- **`defensive` archetype (와, ICE 가 존재하는 한 `support`) 가 더 이상 cosmetic 이
  아니다.** `shield` / `heal` / `regen` / `buff` 가 실제의 테스트된 전투 semantics 를
  갖는다.
- **magnitude 가 authored data** 다 — 계산된 heuristic 이 아니다.
- **밸런스 영향이 실측으로 측정되었고 무시 가능했다** (+0.2pp, 한 grade) — 그래서
  재캘리브레이션이 필요 없었다.
- **reducer 는 pure 이고 deterministic** 이다.

### 부정적 영향 / 수용한 비용

- **per-skill magnitude 가 owner 의 개별 강도를 무시한다** (위 trade-off).
- **`aggressive` / `stealth` ICE 가 우연히 shield / buff / regen 스킬을 가져도
  그 효과들은 설계대로 inert** 하다 — 그래서 catalog 스킬이 아직 여러 개 발사 불가
  상태로 남는다.
- **`detect` / `silence` / `slow` / `stun` / `debuff` 는 여전히 미구현** 이다.

### 여전히 inert 인 효과 (남은 범위)

`detect`, `silence`, `slow`, `stun`, `debuff`, `stagger`, `counter`, `vulnerable`,
`bleed`, `fatigue`, `confused`, `terrified`.

`detect` / `silence` / `slow` 는 **alarm / information system** 소속이지 combat
status 가 아니다 (ADR-0219 열린 질문 3) — 그래서 **보고만 되고 구현되지 않으며**,
그 스킬들은 여전히 발사 불가 상태다. 나머지는 이번 세 개의 계열
(shield / heal / regen / buff) 범위 밖이다.

### 후속 항목 (모두 기록한다)

1. **reach 가 여전히 작다** — band 안에서 새 메커닉을 실제로 발동시키는 ICE 는
   **`ta_sentinel` 하나뿐** 이다. 넓히려면 band 를 건드리거나, `aggressive` /
   `stealth` ICE 에게 **그 archetype 가 실제로 쓸 스킬**을 주어야 한다. 둘 다
   밸런스 결정이다.
2. **per-owner magnitude** — per-skill 단순화를 (스킬, owner) 조합별 authoring 이나
   load-time derivation 으로 풀 수 있지만, 후자는 ADR-0222 의 방향과 모순된다.
3. **남은 inert 효과들** (`detect` / `silence` / `slow` / `stun` / `debuff`), 그리고
   `detect` / `silence` / `slow` 가 alarm / information system 소속인지.
4. **ADR-0223 의 10개 ambiguous skill 분류** — 여전히 미해결.
5. **Catalog gap** — tier-1 피해 스킬이 없다 (그래서 g1 의 skill slot 은 여전히
   발사 불가), 스킬을 carry 하는 `stealth` ICE 가 없다, `support` 는 0 종이다.

### 관계

이 ADR 은 **ADR-0219 Option A 를 실행한다.** 연쇄는
**B (0219) → D (0222) → 분류 review (0223) → band (0224) → 재캘리브레이션 (0225)
→ A (이번)** 로 완성된다.

ADR-0219 / 0222 / 0223 / 0224 / 0225 는 **Accepted 이며 immutable** 하다
(`AGENTS.md` §6) — **수정하지 않았다.** 관계는 이 ADR 에 기록했다.

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:

**새 모듈 2개**

- `web/src/core/ice_combat_effects.ts` — **215 LOC**. 풀 / 보너스 reader
  (`iceShieldPool`, `iceAttackBonus`), `healIce` (`maxHp` 상한),
  `absorbIceDamage`, `tickIceEffects`, `clearIceEffects`.
- `web/src/core/ice_combat_effect_apply.ts` — **184 LOC**. effect 별 적용
  (`applyShield` / `applyHeal` / `applyRegen` / `applyBuff`).
- 둘 다 `AGENTS.md` §6 의 **모듈당 100–300 LOC** 권장 범위 안이다. 분할은
  **ADR-0110 선례**를 따른다 (상태 helper 와 per-effect 적용을 분리).
- `web/src/core/state_actions_combat.ts` — **369 → 418 LOC**.

**수정된 파일**

- `web/src/core/ice_ai.ts:180` — `IMPLEMENTED_NON_DAMAGE_EFFECTS`
  (`shield` / `heal` / `regen` / `buff`). `:193` —
  `DEFENSIVE_HEALTHY_PREFERENCE`. `:209` —
  `isAtOrAboveDefensiveThreshold`. `:275` — `fireable` 술어.
  `:298` — fallback 이 **피해 스킬을 우선**한다.
- `web/src/core/ice_skills.ts:63` — `IceSkillDef.magnitude`. `:136` — 잘못된
  `magnitude` 에 **throw**.
- `web/src/core/types.ts:257` — `StatusEffectKind` 에 `"shield"` 추가 (기존 member
  무변경). `:296` — `StatusEffectInstance.iceIndex`. `:298` —
  `StatusEffectInstance.tickSource`. `:89` — `Ice.skills[].magnitude`.
- `web/src/core/state_actions_combat.ts:243` — 스킬 피해에 buff 보너스. `:258` —
  non-damaging 스킬이 효과로 발사되는 경로. `:304` — auto-attack 에 buff 보너스
  (grade / boss multiplier **뒤**). `:318` — `tickIceEffects` 호출.
- `web/src/core/state_actions_programs.ts:129` — shield 가 **player 피해를 HP 전에**
  흡수. `:354` — 흡수량 표기.
- `web/src/core/state_actions_phases.ts:73` — roster ICE 가 `maxHp` 를 carry.
  `:83` — encounter 진입 시 ICE 효과 제거.
- `web/src/core/status.ts:63` — `tickStatus` 가 enemy-ticked 효과를 skip.
- `web/src/data/ice_types.json` — **`magnitude` 필드 28개 추가뿐.** `name` /
  `effect` / `cooldown_ms` 는 **미변경**, ICE row **97개 전부 미변경**.

**테스트**

- `web/tests/ice_combat_effects.test.ts` — 신규 **17 test**.
  **17개 중 16개가 discriminating** 이다 — 신규 모듈 2개를 no-op 으로 stub 하여
  검증했다. 관측된 실패 메시지:
  `expected +0 to be 20`, `expected 95 to be 100`, `expected 30 to be 42`,
  `expected 95 to be 98` 등.
  **양쪽 상태에서 모두 통과하는 유일한 test 는 의도적인 guard test**
  ("leaves every unimplemented effect inert") 다.
- **기존 assertion 변경 1건** — `web/tests/ice_ai.test.ts`
  `"prefers shield for defensive personality"` 를 **두 개로 split** 했다:
  - `"prefers shield for a wounded defensive personality"` (hp 20/50 → shield)
  - `"prefers the attack for a healthy defensive personality"` (hp 50/50 → attack)
  - 근거: ADR-0161 (Accepted) 은 DEFENSIVE 를 *"prefer shields when HP < 50%"* 로
    정의하고, repo 에 이미 `DEFENSIVE_HP_THRESHOLD` + `shouldDefensiveAct` 가 있다.
    이전 assertion 은 **무조건적** 선호를 encode 했고, Option A 아래에서는 **건강한
    defensive ICE 가 영원히 shield 만 치고 공격하지 않게** 만든다. 이 변경은 suite 를
    **강화**한다 (명시된 두 regime) — 이전 의도를 삭제하지 않는다.
- **개발 중 깨진 기존 test 2건은 약화가 아니라 올바르게 고쳐졌다:**
  - `web/tests/boss_ai.test.ts` "boss deals bonus damage in phase 4" — phase-4
    minion 이 spawn turn 에 행동하고 있었다. 이제 working roster 가
    **minion append 이전의 roster** 에서 시작한다.
  - `web/tests/tick_kill_loot.test.ts` — roster id 충돌. identity 가 catalog id 에서
    **roster slot index** 로 옮겨갔다.
  - 두 test 파일은 **이 ADR 에서 수정되지 않았다** — production 코드가 고쳐졌다.
- 게이트: `npm test` **126 files / 2976 tests, 0 failures**;
  `tsc --noEmit` **0 errors**; `eslint` **0 errors**
  (무관한 pre-existing warning 1건은 `web/src/input/keyboard.ts`).

**밸런스** (`npm run balance`, 100 runs/mission, opening deck): g1 100.0 → **100.0**
· g2 88.6 → **88.6** · g3 73.1 → **73.1** · **g4 48.8 → 49.0 (+0.2pp)** ·
g5 43.1 → **43.1** · g6 0.0 → **0.0**.

**밸런스** (`npm run balance -- --deck ppl`, 100 runs/mission): g1 100.0 → **100.0**
· g2 77.9 → **77.9** · g3 97.8 → **97.8** · **g4 88.8 → 89.0 (+0.2pp)** ·
g5 44.4 → **44.4** · g6 31.3 → **31.3**. PPL g4 의 p95 만 26 → 29 로 이동했다.

**Notes**:

- **재캘리브레이션은 하지 않았고 필요하지 않았다.** calibration 배열 2개와 band 는
  **미변경**이다. g4 49.0% 는 ADR-0211 target 47.4% 대비 **+1.6pp** 로 ADR-0225 가
  세운 ±3pp 허용 오차 안이고, opening 곡선은 단조 비증가를 유지한다.
- **밸런스 이동이 작은 이유는 reach 다** (추측이 아니라 실측). `ta_sentinel` 이
  24-slot band 안에서 archetype 가 구현된 계열을 지목하는 **유일한 ICE** 이다.
  나머지 band 의 효과 스킬은 `aggressive` ICE 의 것이라 **설계대로 inert** 하다.
- **`ice_types.json` 의 변경은 `magnitude` 28개뿐이다.** `name` / `effect` /
  `cooldown_ms` 는 손대지 않았고, ICE row 97개는 그대로다.
- **`docs/testcases/combat/depth.md` 는 prototype-era 문서이며 미변경이다.** 이번
  구현은 그 문서의 TC-DEPTH-004 / TC-DEPTH-005 를 **의도 근거로 참조**했지만
  현행 계약으로 승격시키지는 않았다.
- **ADR-0219 / 0222 / 0223 / 0224 / 0225 를 포함한 기존 ADR 은 하나도 수정하지
  않았다.** Accepted 결정은 immutable 이고 (`AGENTS.md` §6), 관계는 이 ADR 에
  기록했다.

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `web/src/core/ice_combat_effects.ts` — **신규** (215 LOC)
- `web/src/core/ice_combat_effect_apply.ts` — **신규** (184 LOC)
- `web/src/core/ice_ai.ts` — fireable 규칙, `IMPLEMENTED_NON_DAMAGE_EFFECTS`,
  defensive HP threshold
- `web/src/core/ice_skills.ts` — `IceSkillDef.magnitude` + 검증
- `web/src/core/types.ts` — `StatusEffectKind` += `shield`;
  `StatusEffectInstance` += `iceIndex` / `tickSource`; `Ice.skills[].magnitude`
- `web/src/core/state_actions_combat.ts` — non-damaging 발사 경로, buff 보너스,
  `tickIceEffects`
- `web/src/core/state_actions_programs.ts` — shield 가 player 피해를 HP 전에 흡수
- `web/src/core/state_actions_phases.ts` — roster ICE `maxHp`; encounter 진입 시
  ICE 효과 제거
- `web/src/core/status.ts` — `tickStatus` 가 enemy-ticked 효과를 skip
- `web/src/data/ice_types.json` — `magnitude` 28개
- `web/tests/ice_combat_effects.test.ts` — **신규** (17 test)
- `web/tests/ice_ai.test.ts` — assertion 1건 split (test 2개로)

### 이번 결정으로 변경되지 않은 항목

- `web/src/core/ice_scaling.ts` — `ENCOUNTER_HP_BY_GRADE`,
  `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`, `ENCOUNTER_ICE_BY_GRADE` **전부 미변경**
- `web/src/data/ice_types.json` — `skill_defs` 의 `name` / `effect` /
  `cooldown_ms`, ICE row 97개
- `web/src/core/combat_engine.ts` — `AUTO_ATTACK_INTERVAL_MS` (2000 ms)
- `web/tests/boss_ai.test.ts`, `web/tests/tick_kill_loot.test.ts` — **미수정**
  (production 코드가 고쳐졌다)
- ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 를 포함한 기존 ADR — **미수정**
  (immutable)

## 관련 결정

- ADR-0219 (non-damaging ICE 스킬 효과) — **이 ADR 이 실행하는 결정.** Option A 의
  owner. **ADR-0219 는 수정하지 않았다** (immutable).
- ADR-0216 (derived ICE skill metadata) — sibling. `skill_defs` 가 대체한
  derivation 의 owner.
- ADR-0218 (ICE skill selection fallback) — sibling. 이 ADR 이 그 fallback 위에
  effect 발사 경로를 얹었다.
- ADR-0222 (ICE 스킬 메타데이터가 authored data 로 이동) — **이 ADR 가 소비하는
  데이터의 owner.** magnitude authoring 은 이 ADR 의 방향("authored data, not
  heuristics")을 그대로 따른다. **ADR-0222 는 수정하지 않았다** (immutable).
- ADR-0223 (스킬 분류 review pass) — **이 ADR 가 소비하는 분류의 owner.**
  **ADR-0223 은 수정하지 않았다** (immutable).
- ADR-0224 (Encounter band 커버리지 확대) — **이 ADR 가 측정된 band 의 owner.**
  **ADR-0224 는 수정하지 않았다** (immutable).
- ADR-0225 (Encounter band 재캘리브레이션) — **이 ADR 가 측정된 calibration 의
  owner.** ±3pp 허용 오차 기준을 세웠다. **ADR-0225 는 수정하지 않았다** (immutable).
- ADR-0161 (ICE personality archetypes) — `defensive` HP threshold 의 owner.
  *"prefer shields when HP < 50%"* 정의가 이번에 실제 발사에 연결되었다.
- ADR-0110 (모듈 사이즈 정책) — 신규 모듈 2개 분할의 근거.

## 변경 이력

- 2026-10-27: Draft 작성 (ADR-0219 Option A 실행 — `shield` / `heal` / `regen` /
  `buff` 메커닉 + magnitude authoring + band 밸런스 재측정)
- 2026-10-27: **Accepted (Option A 실행)** — 구현 완료·검증. `shield` / `heal` /
  `regen` / `buff` 가 실제 전투 semantics 를 갖는다. `magnitude` 28 entry 저술.
  밸런스 영향은 **단일 grade +0.2pp** 로 측정되었고 **재캘리브레이션은 불필요**했다.
  기존 assertion 1건은 split 되었고, 깨졌던 기존 test 2건은 production 코드 차원에서
  올바르게 고쳐졌다. **ADR-0219 Option A 의 잔여 범위**
  (`detect` / `silence` / `slow` / `stun` / `debuff` 와 catalog gap) 은 후속 항목으로
  남아 있다.
