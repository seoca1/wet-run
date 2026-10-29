# ADR-0228: ICE 아키타입 동작 배선 — 하나는 살렸다, 둘은 서브시스템이 필요하다 (ADR-0227 후속 #4)

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — dead combat path, ADR-0216/0219/0222/0223/0224/0225/0226/0227 sibling)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0161 — ICE personality archetypes](./0161-ice-personality-archetypes.md), [ADR-0211 — ICE grade scaling](./0211-ice-grade-scaling.md), [ADR-0219 — non-damaging ICE 스킬 효과](./0219-non-damaging-ice-skill-effects.md), [ADR-0223 — 스킬 분류 review pass](./0223-skill-classification-review.md), [ADR-0224 — Encounter band 커버리지 확대](./0224-encounter-band-coverage.md), [ADR-0225 — Encounter band 재캘리브레이션](./0225-encounter-band-recalibration.md), [ADR-0226 — Non-damaging ICE 스킬 효과를 구현한다](./0226-non-damaging-ice-skill-effects-implemented.md), [ADR-0227 — ICE 아키타입 일관성 검토](./0227-ice-archetype-consistency-review.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-27 에 결정·구현·검증까지 완료되었다.
> 구현 범위는 **하나의 아키타입 동작만**이다 — `getCritBonus` (`aggressive` 의
> +5% crit).
>
> **핵심은 이것이다: 나머지 셋은 배선이 아니라 서브시스템이 필요했다.**
> ADR-0227 은 `personality` 를 데이터 정합하게 만들었지만, 그 결과로 아키타입은
> **스킬 선택에 영향을 주는 반쪽짜리 시스템**으로 남았다. `ice_ai.ts` 에
> 문서화된 네 개의 동작 중 하나만 실제 시스템이 그 위에 있었다.
>
> **결론: "배선한다"는 말은 서브시스템을 세우는 것을 포함하지 않는다.**
> 이 ADR 은 **먼저 조사하고, 실제로 존재하는 것만 배선한다** 는 규칙을 세우고,
> 네 개 동작 각각을 **배선 / 서브시스템 필요 / 이미 배선됨** 으로 판정했다.

## 컨텍스트 (Context)

### ADR-0227 이 남긴 것

ADR-0227 은 `ice_types.json` 의 97 row 중 12 row 의 `personality` 를 교정해
아키타입 표를 데이터 정합하게 만들었다. 그리고 그 ADR 의 후속 항목 4 는 이
문장이었다:

> archetype 의 미배선 동작들 (`getCritBonus` +5% crit, `shouldTargetAlly`,
> `getAlarmMultiplier` ×0.5, `shouldDefensiveAct`) — 문서화되어 있으나
> web build 에서 소비되지 않는다.

**"소비되지 않는다"는 것은 무엇을 뜻하는가?** 그 점이 이 ADR 의 출발점이다.
`web/src/core/ice_ai.ts` 는 네 개의 동작을 **export 한다** — 그리고
`web/tests/ice_ai.test.ts` 는 그 넷을 **테스트한다**. 그러나 **production
code 의 어느 곳도 그 결과를 읽지 않는다.** 즉 테스트는 "이 함수가 이런 값을
반환한다"를 고정할 뿐, **플레이어에게 아무observable한 차이가 없다**는 것을
고정한다.

### 왜 이게 결함인가 — "테스트가 있는 dead path" 패턴

이 워크스페이스가 지금까지 추적해 온 결함 유형은 **"데이터는 있는데 소비자가
없다"** 다. ADR-0216 (`skills` drop), ADR-0220 (`personality` drop),
ADR-0221 (`aggression` drop), ADR-0222 (`skill_defs` 의 heuristic → authored),
ADR-0223 (분류 오류) 가 그랬다.

아키타입 동작들은 **한 단계 다른 결함**이다. 데이터는 있고 테스트도 있다.
**소비하는 경로 (consumer path) 가 없다.** 데이터는 파이프라인에 흘러들지만
마지막에 아무것도 바꾸지 않는다. 그래서 아키타입은 현재 **스킬 선택에만**
영향을 준다. 그 외의 세 동작 — crit, ally targeting, alarm speed — 은
**문서상 존재하고 테스트로 고정되지만 플레이에는 없다.**

### 질문은 "배선할까" 가 아니라 "배선할 수 있는가" 다

`getCritBonus` 를 `state_actions_combat.ts` 에서 부르려면 두 가지가
필요하다: (1) 호출할 지점, (2) crit 이라는 개념 자체. `getAlarmMultiplier` 를
부르려면 (1) 호출할 지점, (2) **alarm 이라는 진행 중인 수치** 가 필요하다.
(2) 가 없으면 (1) 은 존재할 수 없다 — 배율을 걸 대상이 없다.

그래서 이 ADR 은 네 동작 각각에 대해 **"그 동작이 걸려들 시스템이 실제로
존재하는가"** 를 먼저 조사했다. 존재하는 것만 배선하고, 존재하지 않는 것은
**"미배선 — 서브시스템 필요"** 로 판정해 back log 에 남긴다.

## 고려한 옵션

### Option 1: 조사 우선 — 실재하는 것만 배선한다 (선택)

- **설명**: 네 동작 각각의 **기반 시스템 존재 여부**를 먼저 조사한다.
  crit 시스템이 있으면 crit 을 배선하고, 대상 지정 시스템이 있으면 대상
  지정이 아니라 **대상 지정의 부재 자체**를 보고하고, 이미 배선돼 있으면
  **중복 배선하지 않는다.** 존재하지 않는 시스템은 "만든다"가 아니라
  **back log 로 명시한다.**
- **장점**:
  - **정직하다.** "배선했다"고 말할 수 있는 것과 "아직 없다"고 말해야 하는
    것이 명확히 갈린다.
  - **범위가 작고 검증 가능하다.** 새 서브시스템을 세우지 않는다.
  - **재현 가능하다.** 조사 대상이 네 개로 고정되어 있고, 각 판정의 근거가
    production code 의 특정 지점이다.
  - **이미 배선된 것을 다시 배선하지 않는다** — `shouldDefensiveAct` 은
    ADR-0226 이 이미 연결했다.
- **단점**:
  - **아키타입 시스템은 여전히 부분적이다.** 세 동작 중 하나만 살았다.
  - **back log 에 서브시스템 2건이 추가된다.**
- **Pillar 정합**:
  - P3 (The Flatline): ✅ crit 이 dead path 에서 벗어나 실제 전투에 닿는다.
  - P4 (The Build): ✅ 기존 모듈을 부풀리지 않고 새 모듈 하나로 격리한다.
  - P5 (The Style): ✅ archetype 가 이름과 행동 사이의 간극을 좁힌다.

### Option 2: 네 동작을 전부 배선한다 — 필요한 서브시스템도 만든다

- **설명**: `shouldTargetAlly` 를 위해 per-target 스킬 해석을 만들고,
  `getAlarmMultiplier` 를 위해 trace alarm accrual 루프를 만든다. 그 위에서
  네 동작을 모두 배선한다.
- **단점**:
  - **이 ADR 의 범위를 완전히 벗어난다.** per-target 스킬 해석은 enemy combat
    path 의 구조를 바꾸는 작업이고, alarm accrual 루프는 alarm 이라는
    **게임 시스템**을 새로 세우는 작업이다. 둘 다 "아키타입 동작 배선"이
    아니다.
  - **밸런스에 추가 변수를 만든다.** 다른 grade 의 추가 메커닉이 동시에
    켜진다 — 0224/0225/0226/0227 이 반복해 온 재캘리브레이션 churn 이
    여기서 더 늘어난다.
  - **사용자 결정 없이.done 된다.** 밸런스를 흔드는 작업은 ADR-0224 / 0225 /
    0227 이 precedent 를 따라 별도 결정을 거쳤어야 한다.
- **Pillar 정합**: 실패 (범위 위반, 그리고 결정되지 않은 밸런스 영향).

### Option 3: 현상 유지 — 아무것도 배선하지 않는다

- **설명**: ADR-0227 의 후속 항목 4 를 닫지 않고 그대로 남긴다.
- **단점**:
  - **ADR-0227 이 명시적으로 남긴 후속 항목이 영영 미해결로 남는다.**
  - 네 동작의 미배선 사유가 **"모르겠다"가 아니라 "근본 시스템이 없다"** 로
    확정되지 않는다 — 그리고 그 확정 없이는 back log 도 정직하게 쓰일 수 없다.
- **Pillar 정합**: 실패 (기록된 후속 항목을 실행하지 않는다).

### Option 4: crit 만 배선하고 나머지는 언급하지 않는다

- **설명**: `getCritBonus` 만 배선한다. 나머지 셋에 대한 조사는 하지 않는다.
- **단점**:
  - **ADR-0227 후속 항목 4 의 절반만 닫는다.** 나머지 셋이 왜 미배선인지는
    여전히 모른다.
  - "배선할 수 없어서 안 했다"와 "조사하지 않아서 안 했다"가 구별되지 않는다.
- **Pillar 정합**: 부분 실패 (후속 항목 4 가 완전히 닫히지 않는다).

## 추천 (Recommendation)

**Option 1.** 네 동작은 **서로 다른 종류의 문제**다. `getCritBonus` 는
**시스템이 이미 있고 연결만 빠진** 경우이고, `shouldTargetAlly` /
`getAlarmMultiplier` 는 **시스템 자체가 없는** 경우이며, `shouldDefensiveAct`
는 **이미 연결된** 경우다. 이 셋을 같은 ADR 로 묶되 **판정을 달리 기록**하는
것이 정직하다.

## 사용자 결정 (Decision)

**2026-10-27 — 조사 우선, 실재하는 것만 배선하기로 결정했다.** 구현 완료·검증됨.

- [x] **Option 1 — 조사 우선, 실재하는 것만 배선** — **채택·구현됨**
- [ ] Option 2 — 네 동작 전부 배선 (서브시스템 신설 포함)
- [ ] Option 3 — 현상 유지 (no-op)
- [ ] Option 4 — crit 만 배선하고 나머지 언급 없음

### 결정된 내용

1. **`getCritBonus` — 배선.** crit 시스템이 이미 존재하므로 **behavior-local
   wire** 다. `aggressive` ICE 의 피해에 +5% crit 을 적용한다.
2. **`shouldTargetAlly` — 미배선, 서브시스템 필요.** enemy 경로에
   **per-target 스킬 해석이 없다.** roster 는 존재하지만 **모두 적대적**이다.
3. **`getAlarmMultiplier` — 미배선, 서브시스템 필요.** alarm 이 **두 종류**인데
   **어느 것도 trace accrual 루프가 아니다.** 의도된 훅 `tickAlarm` 의
   **프로덕션 호출자가 0** 이다.
4. **`shouldDefensiveAct` — 이미 배선됨 (ADR-0226).** 중복 배선하지 않는다.
5. **밸런스 재캘리브레이션은 적용하지 않았다.** g4/g5 가 ±3pp 를 벗어났지만
   재보정은 **사용자 결정 사항**으로 남긴다 (아래 「재캘리브레이션 — 제안만,
   미적용」).

### 네 동작의 판정 (근거를 먼저 읽어라)

#### `getCritBonus` — 배선 (WIRED)

crit 시스템은 **존재한다.** `web/src/core/combat_engine.ts:161-179` 에
`critChance`, `CRIT_MULTIPLIER`, `isCrit` 가 있고, `DamageContext.attackerTeam`
이 이미 player/enemy 를 구분한다. **즉 "crit 이라는 개념" 의 부재는 이
장벽이 아니다.**

하지만 **enemy 경로는 crit 이 없었다.** enemy 피해는 `state_actions_combat.ts`
의 **두 지점에서 인라인**으로 계산되었고 **crit roll 이 전혀 없었다.**
그리고 `calculateDamage` 의 **프로덕션 호출자는 player 하나뿐** 이었다
(`web/src/core/state_actions_programs.ts:100`).

**결론: 새 서브시스템이 아니라 국소 배선이다.** 계산된 enemy 피해 위에
crit 을 modifier 로 얹으면 된다.

#### `shouldTargetAlly` — 미배선, 서브시스템 필요

멀티 ICE roster 는 존재한다 — `web/src/core/types.ts:179`
(`readonly iceRoster: ReadonlyArray<Ice>; // 1..N ICE in current combat
(multi-enemy)`). **그러나 그 roster 는 동시에 적대적인 ICE 의 집합이지
ally 가 아니다.**

**enemy 경로에는 per-target 스킬 해석이 없다.** roster 의 모든 ICE 는
**player 한 명을** 공격한다. 그리고 `shield` / `heal` / `regen` / `buff` 는
**자기 대상 전용** 이다 (`web/src/core/ice_combat_effect_apply.ts`).

**결론: 배선이 아니라 시스템 구축이 필요하다.** support ICE 가
부상당한 동료를 고르려면 (1) roster ICE 간의 관계 모델, (2) 대상 선택 규칙,
(3) 대상 지정 효과의 적용 경로가 필요하다. 그 중 어느 것도 지금 없다.

#### `getAlarmMultiplier` — 미배선, 서브시스템 필요

**alarm 이 두 종류인데, 둘 다 trace accrual 루프가 아니다.**

| 시스템 | 정체 | 근거 |
| --- | --- | --- |
| `player.alarm` (0–100) | **프로그램 비용 누산기** — program 을 쓰면 오르고, 죽으면 리셋 | `web/src/core/state_actions_programs.ts:58`, `:360` |
| `state.alarmLevel` / `lastAlarmTickMs` | **초기화만 되고 어떤 reducer 도 쓰지 않는다** | `web/src/core/state.ts:116-117`, `:342-343` (쓰기 지점 0) |

의도된 훅 `tickAlarm(…, iceAlarmSpeed)` 는 `web/src/core/combat_engine.ts:198`
에 존재하지만 **프로덕션 호출자가 0** 이다 — `web/tests/combat_engine.test.ts`
만 참조한다. **배율을 걸 대상 자체가 없다.**

**추가로 — 이 ADR 을 쓰면서 catalog 를 실측했고, 한 가지 정정을 기록한다.**
초기 검토는 "밴드에 `stealth` ICE 가 없다"고 정리했으나 **실측은 다르다.**
`ENCOUNTER_ICE_BY_GRADE` (`web/src/core/ice_scaling.ts:128-135`) 에
**`stealth` ICE 가 들어 있다** — g1 slot 2 의 `wisp`, g3 slot 3 의
`ice_dixie_echo` (둘 다 `personality: "stealth"`).

**그래도 결론은 바뀌지 않는다.** catalog 의 `stealth` ICE **5 종 모두**
`skills: []` 이다 (`wisp`, `ice_wisp_t1`, `ice_shadow_variant`,
`ice_ghost_grid`, `ice_dixie_echo`). 그러므로 배율이 걸 **동작** 자체가 없다 —
스킬이 없는 ICE 의 alarm 배율은 **아무 observable한 결과도 만들지 못한다.**
**필요한 것은 alarm accrual 루프 (여전히 필요) + 스킬을 carry 하는 `stealth`
ICE (여전히 필요) 둘 다다.**

#### `shouldDefensiveAct` — 이미 배선됨 (ADR-0226)

ADR-0226 이 **같은 `DEFENSIVE_HP_THRESHOLD` (0.5)** 를
`selectSkillByPersonality` 에 연결했다 — `web/src/core/ice_ai.ts` 의
`isAtOrAboveDefensiveThreshold` (`:209`) 와 `effectivePreference` (`:218`),
그리고 production 호출은 `web/src/core/state_actions_combat.ts` 다.
**중복 배선하지 않는다.**

## 구현된 것 (What was implemented)

### 신규 모듈 — `web/src/core/ice_crit.ts` (103 LOC)

`rollIceCrit(ice, damage, rng)` — **순수 함수**, **RNG 주입**, **모듈 상태 0**.

- **비-`aggressive` ICE 는 피해를 그대로 돌려주고 RNG 를 소비하지 않는다.**
  (그래서 deterministic enemy damage 가 정확히 보존된다.)
- **`aggressive` ICE 는 `AGGRESSIVE_CRIT_BONUS` (5%) 로 롤**하고, 명중하면
  **엔진 자신의 crit 배수 밴드 (~1.8–2.2×)** 를 적용한다
  (`CRIT_MULTIPLIER_MIN` / `CRIT_MULTIPLIER_MAX` 를 `combat_engine.ts` 에서
  import).

`AGENTS.md` §6 의 **모듈당 100–300 LOC** 권장 범위 안이다. 분할 근거는
**ADR-0110 선례**다 (순수 계산은 전용 모듈로).

### `web/src/core/ice_ai.ts` — 파라미터 타입 확장

`getCritBonus` 의 파라미터를 `Combatant` 에서 새 최소 인터페이스
**`PersonalityBearer`** 로 넓혔다. 이 함수는 `personality` **만** 읽는다.
production roster 타입 `Ice` 와 엔진 타입 `Combatant` 가 모두 이를 만족한다.
이는 파일의 기존 최소 인터페이스 패턴 (`SkillUser` / `UsableSkill`) 을 따른다.

### `web/src/core/state_actions_combat.ts` — 양쪽 enemy 피해 지점에 배선

**두 곳 모두** — 스킬 피해 지점과 auto-attack 지점 — 에 crit roll 을 넣고
`CRITICAL` 로그 마커를 붙였다. **기존 `damage > 0` 게이트는 보존**했다.

### 설계 노트 — enemy 를 `calculateDamage` 로 라우팅하지 **않은** 이유 (기록한다)

**enemy 를 `calculateDamage` 에 넣지 않았다.** 넣으면 두 가지가 함께 따라온다:

1. **0.8–1.2× 피해 variance** 가 **모든** enemy hit 에 붙는다 — 그러면
   enemy baseline 이 통째로 흔들리고, 밸런스 곡선이 재측정 대상이 된다.
2. **base `CRIT_CHANCE` (0.15)** 가 **모든** archetype 에 적용된다 — 그러면
   "`aggressive` **에게만** 붙는다"는 요건이 깨진다.

**대신 crit 을 이미 계산된 enemy 피해 위의 국소 modifier 로 적용**했다.
결과적으로 **enemy baseline 은 byte-identical** 이고 **`aggressive` 만 crit
을 얻는다.**

## 밸런스 — 이동을 있는 그대로 기록한다 (최소화하지 않는다)

### Opening deck (`npm run balance`, 100 runs/mission)

| grade | BEFORE | AFTER | delta |
| --- | --- | --- | --- |
| g1 | 100.0% | **100.0%** | 0.0pp |
| g2 | 88.6% | **88.6%** | 0.0pp |
| g3 | 72.8% | **73.1%** | +0.3pp |
| **g4** | **49.0%** | **39.3%** | **−9.7pp** |
| **g5** | **43.1%** | **35.7%** | **−7.4pp** |
| g6 | 0.0% | **0.0%** | 0.0pp |

### PPL (developed) deck (`npm run balance -- --deck ppl`, 100 runs/mission)

| grade | BEFORE | AFTER | delta |
| --- | --- | --- | --- |
| g1 | 100.0% | **100.0%** | 0.0pp |
| g2 | 77.9% | **77.9%** | 0.0pp |
| g3 | 100.0% | **99.6%** | **−0.4pp** |
| **g4** | **89.0%** | **84.8%** | **−4.2pp** |
| g5 | 44.4% | **44.4%** | 0.0pp |
| **g6** | **31.3%** | **28.3%** | **−3.0pp** |

### 판정

**g4 와 g5 가 5pp 넘게 움직였다.** opening 곡선은 여전히 **단조 비증가
(monotonic non-increasing)** 다 (100.0 ≥ 88.6 ≥ 73.1 ≥ 39.3 ≥ 35.7 ≥ 0.0).
**그러나 g4 (39.3%) 와 g5 (35.7%) 는 ADR-0211 target (47.4% / 42.4%) 의
±3pp 허용 오차를 벗어났다.**

### 원인

crit 은 `aggressive` ICE 마다 **≈ 5% × ≈ 2.0× ≈ +10% 기대 피해** 를 더한다.
g4/g5 band 는 **`aggressive` 가 지배적이다** — 실측으로 g5 의 4 slot 이
**전부** `aggressive` (`neuromancer`, `sense_net_reporter`, `loa_entity`,
`yakuza_enforcer`) 이고, g4 는 4 slot 중 3 slot 이 `aggressive` 다.

**이것은 메커니즘이 설계대로 작동한 것이지 결함이 아니다.**

### 재캘리브레이션 — 제안만, **미적용** (사용자 결정)

**g4/g5 의 `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` 를 낮춰서** 추가된 진입 피해를
되찾는 것이 제안이다. **적용하지 않았다** — 값 변경은 밸런스 결정이며
사용자 몫이다.

**주의 (추측이 아니라 실측 기반):** 이 레버는
`floor((tier * 3 + armor) * (1 + pct / 100))` 라는 **계단 함수**이고
**auto-attack 에만 적용된다 — 스킬 피해 에는 적용되지 않는다.** 그래서
crit 을 **부분적으로만** 상쇄한다. **그리고 도달 가능한 계단값이 ±3pp 안에
떨어지지 않을 수 있다** — 값을 확정하기 전에 **재측정 sweep** 이 필요하다.

**대안 레버:** crit 배수 밴드를 좁힌다 (현재 ~1.8–2.2, `combat_engine.ts`
에서 상속). **캘리브레이션 배열을 건드리지 않고** crit 의 크기만 줄인다.

## 결과 (Consequences)

### 긍정적 영향

- **아키타입 동작 하나가 실제로 live 다.** `aggressive` ICE 가 crit 한다.
- **나머지 셋이 모호함이 아니라 근거로 정리되었다.** "왜 안 되냐"의 답이
  "시스템이 없다"로 확정되었다.
- **`shouldDefensiveAct` 이 이미 배선됨이 확인되었다** — 중복 배선이 없다.
- **flaky 했던 `boss_ai.test.ts` 픽스처가 근본에서 고쳐졌다** —
  assertion 을 약화해서가 아니라 **under-specified 픽스처를 명시해서**.

### 부정적 영향 / 수용한 비용

- **crit 이 g4/g5 를 ±3pp 밖으로 밀어냈다.** 재캘리브레이션은 제안만 했고
  **미적용**이다.
- **`shouldTargetAlly` 와 `getAlarmMultiplier` 는 여전히 미배선** 이며
  **새 서브시스템이 필요하다** (per-target 스킬 해석; trace alarm accrual
  루프 + 스킬을 carry 하는 `stealth` ICE).
- **`stealth` ICE 는 밴드에 있다** (`wisp` @ g1, `ice_dixie_echo` @ g3) —
  하지만 **5 종 모두 `skills: []`** 이므로 배율을 걸 **동작** 이 없다.

### 후속 항목 (모두 기록한다)

1. **g4/g5 재캘리브레이션 결정** — 위의 두 레버 중 선택. **사용자 소유.**
   (선택 전에 재측정 sweep 이 필요하다.)
2. **`shouldTargetAlly`** — per-target 스킬 해석을 만들어야 한다. 오늘의
   roster 는 **전부 적대적** 이다.
3. **`getAlarmMultiplier`** — trace alarm accrual 루프가 필요하다
   (`tickAlarm` 이 의도된 훅) **AND** 스킬을 carry 하는 `stealth` ICE 가
   밴드에 있어야 **도달 가능**하다. 두 가지가 모두 필요하다.
4. **반복되는 재캘리브레이션 churn** — 연속된 기능 단계 (band 확대 ADR-0224,
   스킬 효과 ADR-0226, archetype 데이터 ADR-0227, 그리고 이번 crit) 가
   **각각** ADR-0211 곡선을 움직였고, **두 global lever 로는 항상 되돌릴 수
   없었다.** ADR-0211 target 을 **한 번 re-baseline** 할지, **per-ICE
   calibration knob** 이 필요한지 검토할 것. **이것은 정당한 프로세스
   결정이며 말로 남겨서는 안 된다.**
5. **이전부터 열려 있던 것들** — ADR-0223 의 모호한 스킬 분류 (10종),
   남은 inert 효과 (`detect` / `silence` / `slow` / `stun` / `debuff`),
   그리고 catalog gap (tier-1 피해 스킬 없음; 스킬을 carry 하는 `stealth`
   ICE 없음; `support` 는 9 종이지만 그 preference list 가 `buff` 를
   제외).

### 관계

이 ADR 은 **ADR-0227 의 후속 항목 4** 를 종결한다.

ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 은 **Accepted 이며
immutable** 하다 (`AGENTS.md` §6) — **수정하지 않았다.** 관계는 이 ADR 에
기록했다.

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:

**신규 파일**

- `web/src/core/ice_crit.ts` — **103 LOC**. `rollIceCrit(ice, damage, rng)`.
  **순수 함수**, **RNG 주입**, **모듈 상태 0**. 비-`aggressive` 는 피해를
  그대로 반환하고 **RNG 를 소비하지 않는다**. `aggressive` 는
  `AGGRESSIVE_CRIT_BONUS` (5%) 로 롤하고, 명중하면 엔진 자신의 crit 배수
  밴드 (`CRIT_MULTIPLIER_MIN`~`CRIT_MULTIPLIER_MAX`) 를 적용한다.
- `web/tests/ice_crit.test.ts` — **신규 10 test.**
  **10개 중 2개가 discriminating** 이다 — 배선을 되돌리면 정확히 2개가
  실패하고 8개가 통과한다. 관측된 실패 메시지:
  `expected '>>> Watchdog attacks: 4 dmg' to contain 'CRITICAL'`
  (auto-attack 경로) 그리고
  `expected '>>> Watchdog uses Hit: 12 dmg' to contain 'CRITICAL'`
  (스킬 경로). **음성 test 5개** (비-`aggressive` archetype, crit miss) 는
  **부재**를 단언하므로 양쪽 상태에서 **모두 통과**한다.
  이 test 들은 helper 가 아니라 **production reducer**
  (`applyCombatAction`) 를 구동한다.

**수정된 파일**

- `web/src/core/ice_ai.ts:346-348` — 신규 최소 인터페이스 `PersonalityBearer`.
  `:354` — `getCritBonus` 의 파라미터가 `Combatant` → `PersonalityBearer` 로
  **넓어졌다** (이 함수는 `personality` 만 읽는다).
- `web/src/core/state_actions_combat.ts` — **양쪽 enemy 피해 지점**에 crit
  roll 배선 + `CRITICAL` 로그 마커. 스킬 경로와 auto-attack 경로 모두.
  **기존 `damage > 0` 게이트는 보존**했다.
- `web/tests/boss_ai.test.ts` — `makeIce` 픽스처가 `personality: "defensive"`
  를 **명시**한다 (아래 근거).

**픽스처 변경 1건의 근거 (약화가 아니다)**

`web/tests/boss_ai.test.ts` 의 `makeIce` 는 이전에 `personality` 를
**생략**했다. 그래서 `coercePersonality(undefined) === "aggressive"` 를
**조용히 상속**했다 — 그리고 이 test 들은 **정확한 데미지 동등성**을 단언하므로,
crit 을 live 로 만든 뒤 **불규칙하게 실패**했다.

- **실측 (unfixed 픽스처)**: 40회 실행 중 **7회 실패** (두 번의 독립 측정에서
  동일). 실측 crit률은 `AGGRESSIVE_CRIT_BONUS` 와 부합한다 — production
  reducer 를 20 000회 구동한 프로브에서 **4.86%**, 독립 RNG 프로브에서
  **5.60%**.
- **실측 (수정 후)**: 40회 실행 중 **0회 실패**. **전체 스위트 8회 연속 clean**.
- **왜 근본 고침인가**: **production 의 97 중 97 catalog ICE row 가 명시적
  `personality` 를 carry 한다** (실측: `aggressive` 68 / `defensive` 15 /
  `support` 9 / `stealth` 5, 누락 0). 즉 픽스처가 **production 대비
  under-specified** 했다.
- **약화가 아니다**: `defensive` 는 crit 하지 않으므로 **기대값은 그대로**
  이고, assertion 은 **약화되지 않았다** — **결정화**되었다. **skip · 삭제 ·
  완화된 assertion 은 하나도 없다.**

**밸런스 (재측정값 — `npm run balance`, opening deck, 100 runs/mission)**

- g1 100.0 → **100.0** (0.0pp) · g2 88.6 → **88.6** (0.0pp) ·
  g3 72.8 → **73.1** (+0.3pp) · **g4 49.0 → 39.3 (−9.7pp)** ·
  **g5 43.1 → 35.7 (−7.4pp)** · g6 0.0 → **0.0** (0.0pp).
- 단조 비증가 유지: 100.0 / 88.6 / 73.1 / 39.3 / 35.7 / 0.0.
  **g4 (39.3%) 와 g5 (35.7%) 는 ADR-0211 target (47.4% / 42.4%) 의 ±3pp
  허용 오차 밖.**

**밸런스 (`npm run balance -- --deck ppl`, 100 runs/mission)**

- g1 100.0 → **100.0** · g2 77.9 → **77.9** ·
  g3 100.0 → **99.6** (−0.4pp) · **g4 89.0 → 84.8 (−4.2pp)** ·
  g5 44.4 → **44.4** · **g6 31.3 → 28.3 (−3.0pp)**.

**게이트**

- `npm test` — **127 files / 2986 tests, 0 failures.**
- `tsc --noEmit` — **0 errors**.
- `eslint src scripts --ext ts` — **0 errors** (pre-existing warning 1건은
  `web/src/input/keyboard.ts`).
- `npm run build` — **성공**.

**모듈 크기**

- `web/src/core/ice_crit.ts` **103 LOC** — `AGENTS.md` §6 의 **100–300 LOC**
  권장 범위 안.
- `web/src/core/ice_ai.ts` **377 LOC**, `web/src/core/state_actions_combat.ts`
  **436 LOC**. 새 로직은 **집중된 모듈**에 산다 — 기존 파일을 부풀리지
  않는다 (**ADR-0110 선례**).

**Notes**:

- **diff 는 `web/` 5개 파일뿐이다** — `web/src/core/ice_ai.ts`,
  `web/src/core/state_actions_combat.ts`, `web/tests/boss_ai.test.ts`
  (수정) + `web/src/core/ice_crit.ts`, `web/tests/ice_crit.test.ts` (신규).
- **`web/` 아래의 다른 파일은 하나도 바뀌지 않았다.** `ice_scaling.ts`,
  `ice_types.json`, `ENCOUNTER_ICE_BY_GRADE`, `ENCOUNTER_HP_BY_GRADE`,
  `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`, `matrix_navigation.ts`,
  `save/storage.ts`, `package.json` — **모두 미변경** (실측).
- **ADR 은 하나도 수정하지 않았다.** Accepted 결정은 immutable 이고
  (`AGENTS.md` §6), 관계는 이 ADR 에 기록했다.
- **재캘리브레이션은 적용하지 않았다.** calibration 배열 2개와 band 는
  **미변경**이다. 재보정은 **제안만** 하고 값 결정은 사용자에게 남긴다.
- **`shouldTargetAlly` 와 `getAlarmMultiplier` 는 배선하지 않았다.**
  `shouldDefensiveAct` 도 **배선하지 않았다** (ADR-0226 이 이미 했다).

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `web/src/core/ice_crit.ts` — **신규** (103 LOC)
- `web/src/core/ice_ai.ts` — `PersonalityBearer` 인터페이스 신설,
  `getCritBonus` 파라미터 타입 확장
- `web/src/core/state_actions_combat.ts` — 양쪽 enemy 피해 지점의 crit roll
  + `CRITICAL` 로그 마커
- `web/tests/ice_crit.test.ts` — **신규** (10 test)
- `web/tests/boss_ai.test.ts` — `makeIce` 픽스처의 `personality` 명시 (결정화)

### 이번 결정으로 변경되지 않은 항목

- `web/src/core/ice_scaling.ts` — `ENCOUNTER_HP_BY_GRADE` ([75, 86, 141,
  165, 165, 165]), `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` ([50, 130, 8, 0, 0,
  −20]), `ENCOUNTER_ICE_BY_GRADE` — **전부 미변경**
- `web/src/data/ice_types.json` — 97 ICE row 와 `skill_defs` 88 entry **전부
  미변경**
- `web/src/core/combat_engine.ts` — `calculateDamage`, `tickAlarm`,
  `CRIT_MULTIPLIER_MIN` / `CRIT_MULTIPLIER_MAX` **미변경**
- `web/src/core/ice_ai.ts` — `shouldTargetAlly`, `getAlarmMultiplier`,
  `shouldDefensiveAct`, `PERSONALITY_SKILL_PREFERENCE`,
  `selectSkillByPersonality` **미변경**
- `web/src/core/matrix_navigation.ts`, `web/src/save/storage.ts`,
  `web/package.json` — **미변경**
- ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 을 포함한 기존 ADR
  — **미수정** (immutable)

### 후속 항목 (이번 ADR 범위 밖)

1. g4/g5 재캘리브레이션 결정 (dmg bonus 하향 vs crit 배수 밴드 축소) —
   **사용자 소유**
2. `shouldTargetAlly` — per-target 스킬 해석
3. `getAlarmMultiplier` — trace alarm accrual 루프 + 스킬을 carry 하는
   `stealth` ICE
4. ADR-0211 target 재기준화 vs per-ICE calibration knob — **프로세스 결정**
5. ADR-0223 의 모호한 10종 / 잔여 inert 효과 / catalog gap

## 관련 결정

- ADR-0227 (ICE 아키타입 일관성 검토) — **이 ADR 이 그 후속 항목 4 를
  종결한다.** **ADR-0227 은 수정하지 않았다** (immutable).
- ADR-0226 (Non-damaging ICE 스킬 효과를 구현한다) — **이 ADR 이 "이미
  배선됨" 으로 판정한 `shouldDefensiveAct` 의 owner.** 같은
  `DEFENSIVE_HP_THRESHOLD` 를 selection 에 연결했다. **ADR-0226 은 수정하지
  않았다** (immutable).
- ADR-0161 (ICE personality archetypes) — 네 개의 archetype 동작 정의의
  owner. **ADR-0161 은 수정하지 않았다** (immutable).
- ADR-0211 (ICE grade scaling) — 재캘리브레이션 대상 곡선과 ±3pp 허용 오차의
  owner. **ADR-0211 은 수정하지 않았다** (immutable).
- ADR-0110 (모듈 사이즈 정책) — 신규 모듈 `ice_crit.ts` 분리의 근거.
  **ADR-0110 은 수정하지 않았다** (immutable).

## 변경 이력

- 2026-10-27: Draft 작성 (ADR-0227 후속 #4 — 네 archetype 동작의
  배선 가능성 조사, 실재하는 것만 배선)
- 2026-10-27: **Accepted (Option 1 — 조사 우선, 실재하는 것만 배선)** —
  구현 완료·검증. `getCritBonus` **배선**, `shouldTargetAlly` /
  `getAlarmMultiplier` 는 **서브시스템 필요로 판정**, `shouldDefensiveAct`
  는 **이미 배선됨으로 확인**. **밸런스는 g4/g5 가 ±3pp 를 벗어났고
  재캘리브레이션은 제안만 · 미적용** (사용자 결정). 기존 assertion 은 하나도
  약화·skip·삭제하지 않았다 — flaky 픽스처를 **명시**해서 **결정화**했다.
