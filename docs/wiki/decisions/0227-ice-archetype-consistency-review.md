# ADR-0227: ICE 아키타입 일관성 검토 — 그리고 그것이 강제한 g3 재보정 (ADR-0226 후속)

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — dead combat path, ADR-0216/0219/0222/0223/0224/0225/0226 sibling)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0161 — ICE personality archetypes](./0161-ice-personality-archetypes.md), [ADR-0211 — ICE grade scaling](./0211-ice-grade-scaling.md), [ADR-0212 — grade 기반 ICE encounter 배선](./0212-grade-driven-ice-encounters.md), [ADR-0219 — non-damaging ICE 스킬 효과](./0219-non-damaging-ice-skill-effects.md), [ADR-0223 — 스킬 분류 review pass](./0223-skill-classification-review.md), [ADR-0224 — Encounter band 커버리지 확대](./0224-encounter-band-coverage.md), [ADR-0225 — Encounter band 재캘리브레이션](./0225-encounter-band-recalibration.md), [ADR-0226 — Non-damaging ICE 스킬 효과를 구현한다](./0226-non-damaging-ice-skill-effects-implemented.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-27 에 결정·구현·검증까지 완료되었다.
> 구현 범위는 **두 부분**이다 —
> (1) ICE `personality` 의 **데이터 정합성 교정 12건**, 그리고
> (2) 그 교정이 **강제한 grade 3 재캘리브레이션** (HP cap 155 → 141,
> auto-attack bonus 0 → +8%).
>
> **핵심은 이것이다: 아키타입 표는 데이터가 아니라 저술이다.**
> ADR-0226 은 `shield` / `heal` / `regen` / `buff` 를 실제 전투 semantics 로
> 만들었지만, **새 메커니즘이 발사되려면 그 ICE 의 archetype 가 그 효과를
> 지목해야 한다.** 그 조건이 만족되지 않은 채로 방치되어 있었다.
>
> **결론: 이것은 ADR-0223 의 결함 유형을 한 단계 위에서 재현한 것이다.**
> ADR-0223 은 `skill_defs` 의 `effect` 가 이름과 어긋나는 문제를 다뤘고,
> 이 ADR 은 `personality` 가 **자기 이름과 자기 스킬**과 어긋나는 문제를
> 다룬다. **그리고 그 교정 하나가 밸런스 곡선을 깨뜨렸다** — 그래서 Part 2
> 가 필요하다.

## 컨텍스트 (Context)

### ADR-0226 이 만들어 놓고 발사가 안 되던 메커닉

ADR-0226 은 `shield` / `heal` / `regen` / `buff` 네 계열의 메커닉을
구현하고 `skill_defs` 에 magnitude 28 entry 를 저술했다. 발사 조건은
**archetype gated** 이다:

> non-damaging 스킬이 발사되려면, **그 ICE 의 archetype 의 preference list 가
> 그 effect 를 지목해야 한다.** 구현된 계열을 지목하는 archetype 는
> `defensive` (`shield` / `heal` / `regen` / `buff`) 와 `support`
> (`heal` / `regen` / `shield`) 뿐이다 (`web/src/core/ice_ai.ts:164-171`).

이 게이트는 **의도**였다 — `aggressive` ICE 가 우연히 shield 스킬을 가져도
그 효과는 flavor 다. 문제는 **데이터가 게이트를 통과하지 못했다**는 것이었다.

### 실측 — 새 메커닉이 도달한 band slot 은 2개뿐이었다

ADR-0226 은 이 사실을 기록하면서 "reach 가 여전히 작다" 를 후속 항목으로
남겼다. 실측치는 이랬다:

| metric | ADR-0226 시점 |
| --- | --- |
| archetype 가 구현 계열을 지목하는 band slot | **2 / 24** |
| 그러한 **distinct ICE** | **1** (`ta_sentinel` @ g4 slot 3, g6 slot 2) |

나머지 band ICE 는 shield / buff / regen 스킬을 **소유하고 있었는데**
`aggressive` 로 저작되어 있었다. 즉 **이름도 스킬도 방어형인데 표에는
공격형이라고 적혀 있었다.**

### catalog 분포가 스스로 smell 을 냈다

`ice_types.json` 의 97 row 를 실측한 분포:

| personality | BEFORE | AFTER |
| --- | --- | --- |
| `aggressive` | **80** | 68 |
| `defensive` | 12 | 15 |
| `stealth` | 5 | 5 |
| `support` | **0** | 9 |

**80 / 97 이 `aggressive` 라는 것은 그 자체가 신호다.** ADR-0224 가 지적한
"`support` archetype 는 ICE 가 0 종" 이 여기서 이어진다 — `support` 의
preference list 가 dead 인 이유는 **catalog 에 `support` ICE 가 하나도
없어서**였다. 그리고 `defensive` 는 12 종이 있었는데 그 중 몇몇이
**공격형 데이터로 저작**되어 있었다.

### 이것은 ADR-0223 의 결함 유형이다

ADR-0223 은 `skill_defs` 88 entry 를 전수 검토해, **`id` 의 이름이 확실히
가리키는 메커닉과 `effect` 값이 다른 20 entry 를** 고쳤다. review 규칙은
4줄이었다. 그 review 의 대상이 `skill_defs` 였을 뿐, **방법론 자체는
재사용 가능하다.**

이 ADR 은 같은 방법을 `personality` 에 적용한다.

## 고려한 옵션

### Option 1: 명확한 불일치만 교정하고, 모호한 것은 기록한다 (선택)

- **설명**: 97 row 전수를 검토한다. `personality` 가 **그 ICE 의 자기 이름과
  자기 스킬**과 **모호함이 없이** 어긋나는 경우에만 고친다. 두 개 이상의
  읽기가 가능한 경우는 **고치지 않고 competing readings 를 함께 기록한다.**
  review 규칙은 다섯 개다:
  1. **기존 archetype 4개만 사용한다** (새 archetype 를 만들지 않는다).
  2. **`name` / `skills` / `skill_defs` / `aggression` / `dmg_base` /
     `hp_base` / `hp_per_grade` / `tier` / `defense` 는 건드리지 않는다.**
  3. **`personality` 만 바꾼다.**
  4. **공격적 identity 가 명확하거나 피해 스킬을 가진 ICE 는 `aggressive`
     로 둔다** (이동시키지 않는다).
  5. **모호한 이름은 변경하지 않고** competing readings 를 기록한다.
- **장점**:
  - ADR-0226 의 메커닉이 **실제로 도달 가능**해진다.
  - review 규칙이 5줄로 끝나므로 **재현 가능하고 감사 가능**하다.
  - 모호한 case 를 고치지 않는 것이 **design call 의 영역**으로 남는다.
  - **밸런스를 의도적으로 건드리지 않는다** (따로 결정하면 된다).
- **단점**:
  - 교정이 밸런스 곡선을 움직일 수 있다 (그래서 별도 결정이 필요하다).
  - 모호한 case 는 이번 review 로 해결되지 않는다.
- **Pillar 정합**:
  - P3 (The Flatline): ✅ ADR-0226 이 만든 메커닉의 reach 가 확보된다.
  - P4 (The Build): ✅ 손으로 관리하는 catalog 표의 신뢰도가 올라간다.
  - P5 (The Style): ✅ ICE 의 이름과 스킬, 그리고 archetype 가 어긋나지 않는다.

### Option 2: 최대 교정 — 이름이 방어적으로 읽히지 않으면 전부 비공격으로

- **설명**: `aggressive` 를 기본값으로 보고, `aggressive` 가 아닌 모든 ICE 를
  `defensive` 또는 `support` 로 옮긴다.
- **단점**:
  - **catalog 의 80/97 이 `aggressive` 라는 사실 자체를 무시한다.**
  - "Daemon" / "Inheritor" / "Terminal" / "Collector" 같은 **정체성이
    명확한 ICE 를 성격에 맞지 않는 archetype 로** 밀어 넣는다 — 그건
    데이터 정합이 아니라 **취향**이다.
  - `yakuza_assassin` / `yakuza_brute` 처럼 **피해 스킬을 가진 ICE** 가
    `support` 가 되면 그 archetype 의 설계 의미가 무너진다.
- **Pillar 정합**: 실패 (분류가 취향으로 바뀐다).

### Option 3: 현상 유지 — `aggressive` 분포를 그대로 둔다

- **설명**: 아무것도 안 한다.
- **단점**: **ADR-0226 의 새 메커닉이 계속 dead path 다.** 24 slot 중 2 slot.
  `support` 는 계속 0 종이고, 그 preference list 는 계속 도달 불가다.
  ADR-0226 이 기록한 후속 항목이 영영 미해결로 남는다.
- **Pillar 정합**: 실패 (기록된 후속 항목을 실행하지 않는다).

### Option 4: band 를 손댄다 — 아키타입 대신 encounter 구성을 고친다

- **설명**: `personality` 는 두고, `ENCOUNTER_ICE_BY_GRADE` 의 slot 을
  archetype 에 맞는 ICE 로 교체한다 (ADR-0224 와 같은 방식).
- **단점**:
  - **catalog 는 여전히 자기모순이다.** 플레이 밖의 ICE 는 여전히
    이름과 스킬이 어긋난 채 남는다 — **정합성 문제가 해결되지 않는다.**
  - ADR-0224 / 0225 가 이미 band 를 두 번 손봤다. 세 번째 band 편집은
    **밸런스를 반복해서 흔든다.**
  - **도달 가능한 ICE 수가 늘지 않는다** — 같은 수의 slot 에서 더 많은
    archetype 을 끌어낼 뿐이다.
- **Pillar 정합**: 실패 (증상을 치료하고 원인을 남긴다).

## 추천 (Recommendation)

**Option 1.** 이 ADR 의 대상은 **데이터 정합성**이다 — 이름과 스킬이 말하는
것을 archetype 가 말해야 한다. Option 2 는 분류를 취향으로 바꾸고,
Option 3 는 dead path 를 남기고, Option 4 는 증상만 치료한다.

**밸런스는 결과다.** 교정이 곡선을 흔들면 그것은 별도 결정의 대상이다 —
ADR-0224 가 그랬듯이, ADR-0225 가 그랬듯이.

## 사용자 결정 (Decision)

**2026-10-27 — 명확한 불일치만 교정하고, 그것이 강제한 g3 재캘리브레이션을
함께 적용하기로 결정했다.** 구현 완료·검증됨.

- [x] **Option 1 — 명확한 불일치만 교정 + 강제된 g3 재캘리브레이션** — **채택·구현됨**
- [ ] Option 2 — 최대 교정
- [ ] Option 3 — 현상 유지 (no-op)
- [ ] Option 4 — band 를 손보다

### 결정된 내용

1. **review 규칙 5개 (엄격히 적용).** 기존 archetype 4개만 사용 · `personality`
   외 필드 미변경 · 공격적 identity / 피해 스킬 보유 ICE 는 `aggressive`
   유지 · 모호한 이름은 변경하지 않고 기록.
2. **97 중 12 row 의 `personality` 를 교정했다.** 나머지 **85 row 는
   미변경**이다.
3. **`ice_scaling.ts` 의 두 calibration 배열을 g3 한 곳에서만 재보정했다.**
   `ENCOUNTER_HP_BY_GRADE[2]`: 155 → **141**,
   `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE[2]`: 0 → **+8**.
4. **ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 을 포함한 기존 ADR 은
   하나도 수정하지 않았다.** Accepted 결정은 immutable 이다 (`AGENTS.md` §6).
   관계는 이 ADR 에 기록했다.

### Part 1 — 교정된 12 row

**→ `defensive` (3)**

| ICE id | 근거 |
| --- | --- |
| `hosaka_defender` | 이름이 `*_defender` + `defense_grid` (shield) 소유 |
| `loa_zombie` | `undead_resilience` (regen) 소유 |
| `goliath_defensive` | 이름이 **literally "Goliath Defensive"** + shield 스킬 3종 |

**→ `support` (9)**

| ICE id | 근거 |
| --- | --- |
| `hosaka_courier` | `*_courier` + buff 2종, 공격 스킬 없음 |
| `sense_net_archive` | `*_archive` + heal + buff, 공격 스킬 없음 |
| `sense_net_informer` | `*_informer`, 공격 스킬 없음 |
| `hosaka_analyst` | `*_analyst`, 공격 스킬 없음 |
| `sense_net_spin` | `alibi_construct` (buff) 보유, 공격 스킬 없음 |
| `sense_net_alert` | broadcasting / alert 정체성, 공격 스킬 없음 |
| `hosaka_collector` | `*_collector` + buff 2종, 공격 스킬 없음 |
| `loa_priest` | "Priest" + shield + buff, 공격 스킬 없음 |
| `ice_cebu_pacific` | 이름이 literally "data courier", 공격 스킬 없음 |

### 의도적으로 고치지 않은 것 (기록한다)

**애매하지만 공격 정체성이 뚜렷한 ICE:**

| ICE id | 왜 두었는가 |
| --- | --- |
| `ta_daemon` | buff + detect kit 이지만 "Daemon" 은 적대적 호출자 정체성 |
| `ta_inheritor` | buff 2종 · 공격 스킬 없음, 그러나 "Inheritor" 는 **직함이 아니라 지원 역할** |
| `hosaka_terminal` | detect + silence 이지만 "Terminal" 은 **하드웨어 정체성** |
| `yakuza_collector` | debuff 전용, "Collector" 는 **자산 압류** 를 뜻함 |

**신호가 없는 ICE:**

| ICE id | 상태 |
| --- | --- |
| `morrison_echo` | `skills: []` — 신호 없음 |
| `zombie` | `skills: []` — 신호 없음 |
| `ice_loa_zombie` | `skills: []` — 신호 없음 |

**공격 스킬 보유 — `aggressive` 유지가 정답:**

| ICE id | 보유 스킬 |
| --- | --- |
| `sense_net_reporter` | `narrative_attack` (attack) |
| `yakuza_assassin` | `stealth_strike` (multi_hit), `critical_hit` (heavy_attack) |
| `yakuza_enforcer` | `enforce_contract` (attack), `debt_collect` (debuff) |
| `yakuza_brute` | `brutal_force` (multi_hit), `intimidation` (attack) |

### 주의 (기록한다) — `support` 의 선호 목록은 `buff` 를 지목하지 않는다

`PERSONALITY_SKILL_PREFERENCE` 의 **live `support` 목록**은
`["heal", "regen", "shield", "debuff", "detect"]` 다
(`web/src/core/ice_ai.ts:170`). **`buff` 가 없다.**

그 결과 buff-only support ICE 의 발화 경로는 **preference match 가 아니라
fallback** 이다: `usable` 이 비면 `pool = all skills` 가 되고, 그 뒤
`pool[0]` 이 선택된다 (`web/src/core/ice_ai.ts:283-284`, `:302`).

실측 (실제 selection 함수를 호출해 확인):

| ICE id | 선택된 스킬 | 경로 |
| --- | --- | --- |
| `hosaka_courier` | `packet_route` (buff) | **fallback** (`pool[0]`) |
| `hosaka_collector` | `data_archive` (buff) | **fallback** (`pool[0]`) |
| `sense_net_spin` | `narrative_warp` (debuff) | preference match (`debuff` 가 목록에 있음) |
| `hosaka_analyst` | `report_alert` (debuff) | preference match |
| `sense_net_informer` | `report_distribute` (debuff) | preference match |
| `sense_net_alert` | `media_alert` (debuff) | preference match |
| `sense_net_archive` | `data_preserve` (heal) | preference match |
| `loa_priest` | `spirit_guard` (shield) | preference match |
| `ice_cebu_pacific` | — (스킬 0개) | 선택 없음 |

**fallback 으로 발화하는 것은 `hosaka_courier` 와 `hosaka_collector` 뿐**이고,
나머지는 `debuff` / `heal` / `shield` preference match 다. 전부 발화는
**실제로 확인했다.**

### Part 2 — 교정이 강제한 g3 재캘리브레이션

`hosaka_defender` (g3 band slot 2) 가 `defensive` 로 바뀌면서 **공격 대신
12 point `defense_grid` shield 를 올린다** — 그리고 그 grade 의 opening
승률이 움직였다.

| | 값 |
| --- | --- |
| BEFORE (ADR-0226 확정 상태) | **73.1%** |
| AFTER (아키타입 교정만 적용) | **89.7%** |
| delta | **+16.6pp** |

이것은 두 가지 문제를 동시에 깼다:

1. **±3pp 허용 오차 위반.** ADR-0225 가 세운 허용 오차는 ±3pp 다.
   +16.6pp 는 그 밖이다.
2. **단조 비증가 invariant 파괴.** opening 곡선은
   `100.0 / 88.6 / 72.8 / 49.0 / 43.1 / 0.0` 처럼 단조 비증가여야 하는데,
   **g3 89.7% > g2 88.6%** 가 되었다.

**단조성 과 ±3pp 는 ADR-0211 / 0225 가 이미 결정한 제약이다.** 그래서
이 재캘리브레이션은 **새로운 결정이 아니라 기존 결정의 복원**이다.

### 재보정 — grade 3 한 곳만

| 상수 | BEFORE | AFTER |
| --- | --- | --- |
| `ENCOUNTER_HP_BY_GRADE[2]` | 155 | **141** |
| `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE[2]` | 0 | **+8** |

**두 배열의 다른 다섯 grade 는 byte-identical** 이다. band 도 그대로다.

### 결과 — 두 곡선 모두 복구

**Opening deck** (`npm run balance`, 100 runs/mission):

| grade | ADR-0211 target | BEFORE (ADR-0226) | AFTER | residual |
| --- | --- | --- | --- | --- |
| g1 | 100.0% | 100.0% | **100.0%** | 0.0pp |
| g2 | 88.8% | 88.6% | **88.6%** | −0.2pp |
| g3 | 73.0% | 73.1% | **72.8%** | **−0.2pp** |
| g4 | 47.4% | 48.8% | **49.0%** | +1.6pp |
| g5 | 42.4% | 43.1% | **43.1%** | +0.7pp |
| g6 | 0.0% | 0.0% | **0.0%** | 0.0pp |

**단조 비증가 회복**: 100.0 / 88.6 / 72.8 / 49.0 / 43.1 / 0.0.
**g3 의 residual −0.2pp 는 곡선 전체에서 가장 타이트하다.**

**PPL (developed) deck** — **6개 grade 전부 불변**:

| grade | BEFORE | AFTER |
| --- | --- | --- |
| g1 | 100.0% | 100.0% |
| g2 | 77.9% | 77.9% |
| g3 | 100.0% | 100.0% |
| g4 | 89.0% | 89.0% |
| g5 | 44.4% | 44.4% |
| g6 | 31.3% | 31.3% |

### 왜 두 레버 모두 필요한가 — 정직한 엔지니어링 상세

**어느 하나만으로는 허용 오차에 도달하지 못한다.** 둘 다 실측이다.

**HP 캡은 상한이 있다.** `c3 <= c4 = 165` — 이를 넘으면 같은 ICE 가 g3 에서
g4 보다 HP 를 더 많이 갖게 되고, 기존 test
`keeps HP monotonic non-decreasing across grades for every band id`
(`web/tests/ice_scaling.test.ts:73`) 가 거부한다. **최대 c3 = 165 에서
grade 는 76.3%** 로, 목표 대비 **+3.3pp** — 여전히 허용 오차 밖이다.
**155..165 구간 안에는 허용 오차 안으로 들어가는 캡 값이 없다.**

**dmg 보너스는 계단 함수다.** auto-attack 기반 (`tier * 3 + armor`) 은
g3 band 에서 **14 / 15 / 13 / 13** 이다. `floor(base * (1 + pct / 100))` 를
적용하면:

| pct | g3 band auto-attack 피해 |
| --- | --- |
| 0 | `(14, 15, 13, 13)` |
| +7 | `(14, 16, 13, 13)` — `hosaka_defender` 만 15 → 16 |
| +8 | `(15, 16, 14, 14)` — 네 row 전부 |

**+7% 단계는 증명된 no-op** 이다 (`hosaka_defender` 의 auto-attack 이 1점
오르는데 승수 하나도 안 바뀐다). **+8% 는 절벽(cliff)** 이다 — c3 = 165 에서
grade 가 **76.3% → 51.5%** (−24.8pp) 로 떨어지며, 사이에 도달 가능한 값이
없다. 즉 **최대 캡에서는 grade 를 허용 오차 창 안에 놓을 방법 자체가 없다.**

**캡을 낮춰야 창이 열린다.** +8% 를 적용한 상태에서 캡을 내리면 70–76%
구간을 걸어서 내려간다: **c3 = 142 → 71.5%, c3 = 141 → 72.8%,
c3 = 140 → 75.0%.** **141** 이 목표(73.0%) 에 가장 가깝다.

**전수 스캔** (cap 124..165 × pct 0..20) 은 **허용 오차 안의 구성을 13개**
찾았다. **그 중 `c3 >= 155` 인 것은 하나도 없다.** 이것이 141 을 택해야
했던 이유의 최종 근거다.

### 정직한 caveat — 이것은 **트레이드**다, 순수 난이도 상향이 아니다

g3 encounter ICE 는 이제 **HP 14 적고, auto-attack 이 1 더 세다.**
**순 난이도는 보존된다.** shield 도 여전히 의미가 있다 — **flat 12 를
3 tick 동안 흡수한다.** 그 shield 가 grade 를 자명하게 이기게 만들지
않을 뿐이다.

**만약 설계 의도가 g3 캡을 155 이상으로 유지하는 것이라면**, 정직한 선택지는
둘이다:

- (a) g3 을 **76.3%** 로 두고 **+3.3pp 편차를 수용**한다, 또는
- (b) `skill_defs` 의 `hosaka_defender` shield **magnitude** 를 재검토한다
  — **콘텐츠 결정이며 이 ADR 의 범위 밖**이다.

## 결과 (Consequences)

### 실측 — 커버리지가 2/24 → 4/24 로 늘었다

| metric | BEFORE | AFTER |
| --- | --- | --- |
| archetype 가 구현 계열을 지목하는 band slot | **2 / 24** | **4 / 24** |
| 그러한 **distinct ICE** | **1** (`ta_sentinel`) | **3** (`ta_sentinel`, `hosaka_defender`, `loa_zombie`) |

살아있는 slot:

| band slot | ICE | 발화하는 효과 |
| --- | --- | --- |
| g2 slot 3 | `loa_zombie` | `undead_resilience` (regen, magnitude 3) |
| g3 slot 1 | `hosaka_defender` | `defense_grid` (shield, magnitude 12) |
| g4 slot 3 | `ta_sentinel` | `vault_guard` (shield) |
| g6 slot 2 | `ta_sentinel` | `vault_guard` (shield) |

**두 개가 실제 band 전투에서 end-to-end 로 관측되었다.** 실제 reducer 를
구동해 `state.statusEffects` 를 관찰한 결과다:

- `hosaka_defender` → `{ kind: "shield", magnitude: 12, remaining: 2,
  target: "ice", iceIndex: 0, tickSource: "enemy" }`
- `loa_zombie` → `{ kind: "regen", magnitude: 3, remaining: 3, healPerTick: 3,
  target: "ice", iceIndex: 0, tickSource: "enemy" }`

**교정 전 데이터(`personality` 를 `aggressive` 로 되돌린 것)로는 둘 다
발사되지 않았다** — player 측 `burn` / `slow` 만 관측되었다. inspection 이
아니라 **실제 전투 경로** 다.

### 긍정적 영향

- **아키타입 시스템이 이제 데이터 정합적이다.** 이름 ↔ 스킬 ↔ archetype 가
  서로 모순하지 않는다.
- **ADR-0226 의 메커닉이 2 slot 에서 4 slot 으로, 1 distinct ICE 에서
  3 distinct ICE 로 늘었다** — inspection 이 아니라 end-to-end 로 검증했다.
- **두 곡선이 허용 오차 안으로 복구되었고 단조성이 유지된다.** g3 의
  residual 은 −0.2pp 로 곡선 전체에서 가장 타이트하다.
- **PPL 은 6개 grade 전부 그대로다.**
- **review 규칙이 5줄로 끝나 재현 가능하고 감사 가능하다.**

### 부정적 영향 / 수용한 비용

- **g3 수정은 순수 상향이 아니라 트레이드다** (HP 14 감소, auto-attack 1
  강화) — `c3 >= 155` 인 허용 오차 안 구성이 **존재하지 않기** 때문이다.
- **`support` 의 선호 목록이 `buff` 를 지목하지 않는다** — buff-only support
  ICE 는 fallback 경로로 발화한다.
- **`support` 는 여전히 드물다** (9 ICE). catalog 전체로 보면 `aggressive`
  68 / 97 이다.
- **archetype 의 다른 문서화된 동작은 여전히 web build 에 배선되지 않았다** —
  `getCritBonus` (+5% crit), `shouldTargetAlly`, `getAlarmMultiplier` (×0.5),
  `shouldDefensiveAct`. 이들은 `web/src/core/ice_ai.ts` 에 정의되어 있고
  **test 에서만 참조된다** — production code 에서 소비되지 않는다.

### 후속 항목 (모두 기록한다)

1. **g3 설계 긴장.** 캡을 141 로 낮추는 것은 트레이드다. 더 깨끗한 해법은
   `skill_defs` 의 `hosaka_defender` shield **magnitude** 재검토
   (콘텐츠 결정) 또는 **per-ICE calibration knob** 추가다.
2. **`support` 의 선호 목록이 `buff` 를 제외한다** — 포함해야 하는가?
   콘텐츠 / 디자인 호출이다.
3. **위 표의 애매한 ICE 들** (`ta_daemon`, `ta_inheritor`, `hosaka_terminal`,
   `yakuza_collector`, `morrison_echo`, `zombie`, `ice_loa_zombie`) 은
   여전히 검토되지 않았다.
4. **archetype 의 미배선 동작들** (`getCritBonus` +5% crit,
   `shouldTargetAlly`, `getAlarmMultiplier` ×0.5, `shouldDefensiveAct`) —
   문서화되어 있으나 web build 에서 소비되지 않는다.
5. **이전부터 열려 있던 것들** — ADR-0223 의 10개 ambiguous skill 분류,
   남은 inert 효과 (`detect` / `silence` / `slow` / `stun` / `debuff`),
   그리고 catalog gap (tier-1 피해 스킬 없음, 스킬을 carry 하는 `stealth`
   ICE 없음).

### 관계

이 ADR 은 **ADR-0223 의 review 패턴을 `personality` 에 적용한 것**이고,
**ADR-0226 의 archetype-gated firing 이 직접적으로 만든 결과**다.

ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 은 **Accepted 이며
immutable** 하다 (`AGENTS.md` §6) — **수정하지 않았다.** 관계는 이 ADR 에
기록했다.

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:

**Part 1 — 데이터 정합성 교정**

- `web/src/data/ice_types.json` — **`personality` 줄 정확히 12개 변경.**
  `git diff --numstat` = **12 insertions / 12 deletions**. diff 의 변경된
  24줄 **전부가 `"personality":` 줄** 다 (기계 검증 — 비-`personality` 변경
  줄 **0개**).
- `web/src/data/ice_types.json` — `name` / `skills` / `skill_defs` /
  `aggression` / `dmg_base` / `hp_base` / `hp_per_grade` / `tier` /
  `defense` **미변경**. 97 ICE row 중 **12 row 의 `personality` 만** 바뀌고
  나머지 **85 row 는 byte-identical**.
- `web/src/data/ice_types.json` — personality 분포 실측:
  BEFORE **aggressive 80 / defensive 12 / stealth 5 / support 0** (97 row)
  → AFTER **aggressive 68 / defensive 15 / stealth 5 / support 9** (97 row).
- `web/src/core/ice_ai.ts:164-171` — `PERSONALITY_SKILL_PREFERENCE` 의 live
  `support` 목록은 `["heal", "regen", "shield", "debuff", "detect"]` —
  **`buff` 를 지목하지 않는다** (미변경).
- `web/src/core/ice_ai.ts:283-284`, `:302` — fallback 경로 (`usable` 이 비면
  `pool = all skills`, 실패 시 `pool[0]`) **미변경**.
- **커버리지 실측**: archetype 가 구현 계열을 지목하는 band slot
  **2/24 → 4/24**, distinct ICE **1 → 3** (`ta_sentinel` → `ta_sentinel` +
  `hosaka_defender` + `loa_zombie`).
- **end-to-end 검증** (실제 reducer 구동, `state.statusEffects` 관찰):
  `hosaka_defender` 가 `defense_grid` (shield, magnitude 12, `tickSource:
  "enemy"`) 를 발사하고, `loa_zombie` 가 `undead_resilience` (regen,
  magnitude 3, `healPerTick: 3`, `tickSource: "enemy"`) 를 발사한다.
  **교정 전 데이터로는 둘 다 발사되지 않았다** (player 측 `burn` / `slow`
  만 관측).
- **fallback 경로 실측**: `hosaka_courier` → `packet_route` (buff),
  `hosaka_collector` → `data_archive` (buff) 가 fallback (`pool[0]`) 으로
  발화하고, `sense_net_spin` / `hosaka_analyst` / `sense_net_informer` /
  `sense_net_alert` 는 `debuff` preference match, `sense_net_archive` 는
  `heal`, `loa_priest` 는 `shield` preference match 다. `ice_cebu_pacific`
  는 스킬이 0개라 선택이 없다.

**Part 2 — g3 재캘리브레이션**

- `web/src/core/ice_scaling.ts:279` — `ENCOUNTER_HP_BY_GRADE` =
  `[75, 86, 141, 165, 165, 165]`.
- `web/src/core/ice_scaling.ts:381` — `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` =
  `[50, 130, 8, 0, 0, -20]`.
- **두 배열에서 index 2 만 변경** (기계 검증 — `git diff -U0` 의 비-comment
  변경 줄은 **배열 literal 두 줄뿐**이다: `155` → `141`, `0` → `8`).
  다른 다섯 grade 는 **byte-identical** 이다. band 도 **미변경**.
- `web/src/core/ice_scaling.ts` — docstring 갱신되어 **stale 한 주장이 남아있지
  않다.** 이전의 g3 bullet, "within ±1pp" 헤더 주장, 그리고 g4 의
  `48.8% / +1.4pp` 수치가 실측값 `49.0% / +1.6pp` 로 정정되었다.
- **밸런스** (`npm run balance`, opening deck, 100 runs/mission) BEFORE →
  AFTER: g1 100.0 → **100.0** (0.0pp) · g2 88.6 → **88.6** (0.0pp) ·
  g3 73.1 → **72.8** (−0.2pp) · g4 48.8 → **49.0** (+1.6pp) ·
  g5 43.1 → **43.1** (0.0pp) · g6 0.0 → **0.0** (0.0pp).
  **단조 비증가 회복** — 100.0 / 88.6 / 72.8 / 49.0 / 43.1 / 0.0.
- **밸런스** (`npm run balance -- --deck ppl`, 100 runs/mission):
  g1 100.0 → **100.0** · g2 77.9 → **77.9** · g3 100.0 → **100.0** ·
  g4 89.0 → **89.0** · g5 44.4 → **44.4** · g6 31.3 → **31.3**.
  **6개 grade 전부 동일.**
- **g3 auto-attack 기반 실측** — band `black` / `hosaka_defender` /
  `ice_dixie_echo` / `sense_net_reporter` 의 `tier * 3 + armor` =
  **14 / 15 / 13 / 13**. `floor(base * (1 + pct / 100))` 적용 결과:
  0% → `(14, 15, 13, 13)`, +7% → `(14, 16, 13, 13)`,
  +8% → `(15, 16, 14, 14)`.
- **iteration 로그** — HP 캡 sweep (155 → **89.7%**, 165 → **76.3%**),
  **+7% 는 no-op** (승수 동일), **+8% 는 cliff** (c3 = 165 에서
  76.3% → 51.5%), +8% 에서 캡 step-down (142 → 71.5%,
  **141 → 72.8%**, 140 → 75.0%). 전수 스캔 (cap 124..165 × pct 0..20) 은
  허용 오차 안 구성 **13개** 를 찾았고, **그 중 `c3 >= 155` 는 0개**였다.
- `web/tests/ice_scaling.test.ts:73` — **`keeps HP monotonic non-decreasing
  across grades for every band id`** 가 **수정 없이 통과**한다.

**게이트**

- `npm test` — **126 files / 2976 tests, 0 failures.** **약화·skip·삭제된
  assertion 은 없다.** 기존 `ice_scaling.test.ts` 의 invariant 들이 미변경으로
  통과한다.
- `tsc --noEmit` — **0 errors**.
- `eslint src scripts --ext ts` — **0 errors** (무관한 pre-existing warning 1건
  은 `web/src/input/keyboard.ts`).

**Notes**:

- **diff 는 `web/` 2개 파일뿐이다** — `web/src/data/ice_types.json`
  (+12 / −12, `personality` 줄만) 과 `web/src/core/ice_scaling.ts`
  (+115 / −22, 실질 변경은 **배열 literal 두 줄**이고 나머지는 전부
  docstring).
- **`web/` 아래의 다른 파일은 하나도 바뀌지 않았다.** effect 메커닉
  (`ice_combat_effects.ts` / `ice_combat_effect_apply.ts`),
  `ice_ai.ts`, `ice_skills.ts`, `types.ts`, `state_actions_combat.ts`,
  combat path 전부 **미변경**이다 — 이 ADR 은 **데이터와 calibration 만**
  건드렸다.
- **테스트 파일은 추가·삭제·수정하지 않았다.** 검증은 ad-hoc probe 로
  수행했고 probe 는 제거했다.
- **ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 을 포함한 기존 ADR 은
  하나도 수정하지 않았다.** Accepted 결정은 immutable 이고 (`AGENTS.md` §6),
  관계는 이 ADR 에 기록했다.
- **archetype 의 미배선 동작은 배선하지 않았다.** `getCritBonus`,
  `shouldTargetAlly`, `getAlarmMultiplier`, `shouldDefensiveAct` 는 여전히
  `web/src/core/ice_ai.ts` 에 정의만 있고 **web build 에서 소비되지 않는다**
  (test 에서만 참조된다).
- **g3 수정은 트레이드다** — 순수 난이도 상향이 아니다.

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `web/src/data/ice_types.json` — 97 row 중 **12 row 의 `personality` 값만**
  (defensive 3 / support 9). 다른 모든 필드와 85 row 는 미변경.
- `web/src/core/ice_scaling.ts` — `ENCOUNTER_HP_BY_GRADE[2]` (155 → 141),
  `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE[2]` (0 → +8), 모듈 header 와 두 상수의
  docstring.

### 이번 결정으로 변경되지 않은 항목

- `web/src/core/ice_scaling.ts` — `ENCOUNTER_ICE_BY_GRADE` (band 전체),
  `iceHpForGrade`, `iceDmgBonusPctForGrade`, `encounterIceIdForGrade`,
  `clampGrade`, `missionGradeOf`, `missionSeedOf`, 나머지 다섯 grade 의
  calibration 값
- `web/src/core/ice_ai.ts` — `PERSONALITY_SKILL_PREFERENCE`,
  `selectSkillByPersonality`, `IMPLEMENTED_NON_DAMAGE_EFFECTS`,
  `DEFENSIVE_HEALTHY_PREFERENCE`
- `web/src/core/ice_combat_effects.ts`, `web/src/core/ice_combat_effect_apply.ts`
  — effect 메커닉
- `web/src/core/ice_skills.ts`, `web/src/core/types.ts`,
  `web/src/core/state_actions_combat.ts` — damage 파생 규칙, combat path
- `web/src/data/ice_types.json` — `skill_defs` 88 entry 전부, 나머지 85 row
- `web/tests/` — **전체 미변경** (추가·삭제·수정 0)
- ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 을 포함한 기존 ADR —
  **미수정** (immutable)

### 후속 항목 (이번 ADR 범위 밖)

1. g3 설계 긴장 — `skill_defs` 의 shield magnitude 재검토 또는 per-ICE knob
2. `support` 의 선호 목록에 `buff` 를 포함할지
3. 애매한 ICE 7 종의 남은 검토
4. archetype 의 미배선 동작 4종
5. ADR-0223 의 ambiguous 10종 / 잔여 inert 효과 / catalog gap

## 관련 결정

- ADR-0223 (스킬 분류 review pass) — **같은 review 패턴의 원형.**
  `effect` 가 아니라 `personality` 에 적용한 것. **ADR-0223 은 수정하지 않았다**
  (immutable).
- ADR-0226 (Non-damaging ICE 스킬 효과를 구현한다) — **이 ADR 이 메커닉을
  도달 가능하게 만든 결정.** archetype-gated firing 규칙의 owner.
  **ADR-0226 은 수정하지 않았다** (immutable).
- ADR-0211 (ICE grade scaling) — **재보정 대상 곡선과 ±3pp 허용 오차의
  owner.** **ADR-0211 은 수정하지 않았다** (immutable).
- ADR-0224 (Encounter band 커버리지 확대) — band 의 owner. band 는 이번
  결정에서 **미변경**이다. **ADR-0224 는 수정하지 않았다** (immutable).
- ADR-0225 (Encounter band 재캘리브레이션) — **±3pp 허용 오차 기준을 세운
  결정.** 그 기준을 복원한 것이 Part 2 다. **ADR-0225 는 수정하지 않았다**
  (immutable).
- ADR-0161 (ICE personality archetypes) — 4개 archetype 와 `defensive` HP
  threshold 의 owner. **ADR-0161 은 수정하지 않았다** (immutable).
- ADR-0110 (모듈 사이즈 정책) — 신규 모듈 없음 (참조).

## 변경 이력

- 2026-10-27: Draft 작성 + Accepted (명확한 불일치만 교정 — 97 row 중
  `personality` 12건, defensive 3 / support 9) — 구현 완료·검증.
  **교정이 강제한 g3 재캘리브레이션** (HP cap 155 → 141, auto-attack bonus
  0 → +8%) 을 함께 적용했다 — g3 이 89.7% 로 튀어 ±3pp 허용 오차와 opening
  곡선의 단조 비증가 invariant 를 **둘 다** 깨뜨렸기 때문이다.
  커버리지 **2/24 → 4/24 slot** (distinct ICE 1 → 3), end-to-end 로 검증.
  기존 assertion 은 하나도 약화·skip·삭제하지 않았다.
  **g3 수정은 순수 상향이 아니라 트레이드** (HP 14 감소 + auto-attack 1
  강화) — `c3 >= 155` 인 허용 오차 안 구성이 존재하지 않기 때문이다.
