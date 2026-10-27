# ADR-0224: Encounter band 커버리지 확대 — ICE 스킬 시스템이 플레이에서 보이게 된다 (ADR-0219 후속 항목 3)

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — dead combat path, ADR-0216/0219/0222/0223 sibling)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0161 — ICE personality archetypes](./0161-ice-personality-archetypes.md), [ADR-0211 — ICE grade scaling](./0211-ice-grade-scaling.md), [ADR-0212 — grade 기반 ICE encounter 배선](./0212-grade-driven-ice-encounters.md), [ADR-0219 — non-damaging ICE 스킬 효과](./0219-non-damaging-ice-skill-effects.md), [ADR-0222 — ICE 스킬 메타데이터가 heuristic 에서 authored data 로 이동한다](./0222-ice-skill-metadata-as-data.md), [ADR-0223 — 스킬 분류 review pass](./0223-skill-classification-review.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-27 에 결정·구현·검증까지 완료되었다.
> 구현 범위는 **encounter band 의 slot 1–3 교체 하나**다 —
> `ENCOUNTER_ICE_BY_GRADE` 의 각 grade 에서 slot 1–3 을 skill-bearing ICE 와
> archetype diversity 를 우선하는 id 로 다시 골랐다.
>
> **재캘리브레이션은 적용하지 않았다.** ADR-0211 이 calibrate 한 밸런스 곡선이
> 지금은 off-calibration 이다 (g2 −11.4pp, g5 −10.4pp, g3 +6.0pp). 그 곡선을
> 다시 맞추는 일은 **사용자 결정이 남아 있다** — 아래 「제안된 재캘리브레이션」 참조.
> **`ENCOUNTER_HP_BY_GRADE`, `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`, `iceHpForGrade`,
> `ice_types.json` 은 하나도 바뀌지 않았다.**
>
> **ADR-0219 Option A 도 구현하지 않았다.** effect 메커닉도 magnitude 도 없다.
> g1 의 skill slot 은 Option A 가 ship 될 때까지 **구조적으로 발사 불가능**하다.

## 컨텍스트 (Context)

### ADR-0219 가 남긴 세 번째 항목

ADR-0219 는 "남은 gap (4) — encounter band 커버리지 확대" 를 별도 항목으로
기록했다 (band 확대는 밸런스 결정이므로 별도 ADR 대상이라고 명시).
ADR-0222 는 `skill_defs` 88 entry 를 authoring 했고 (Option D),
ADR-0223 은 그 88 entry 중 20 개를 정정했다 (분류 review).
**둘 다 하지만, 그 결과가 플레이에서 보이지 않았다.**

### 왜 보이지 않았는가 — band 의 실측

`ENCOUNTER_ICE_BY_GRADE` (`web/src/core/ice_scaling.ts`) 가 `dungeonToMatrix` 가
grade 별 encounter ICE 를 고를 때 쓰는 표다. 변경 전 표는 이랬다:

```
1: ["watchdog", "spider", "wisp", "zombie"]
2: ["spider", "raven", "surveillance", "chinese_ice"]
3: ["black", "goliath", "raven", "ai_whisper"]
4: ["goliath", "ai_whisper", "hellhound", "morrison_echo"]
5: ["neuromancer", "revelation", "loa_entity", "hellhound"]
6: ["neuromancer", "wintermute", "ice_neuromancer_warden", "aleph"]
```

24 slot / 18 unique id 였지만, **스킬을 가진 채로 band 에 걸린 것은 2 slot 뿐**이었다
— `loa_entity` (g5) 와 `aleph` (g6). 둘 다 `aggressive` archetype 였다.

즉 ADR-0222 가 authoring 한 스킬 메타데이터와 ADR-0223 이 정정한 20 개의
분류, 그리고 ADR-0219 Option A 의 발사 조건 (`damage > 0`) — **이 모든 것이
band 가 고르지 않는 catalog row 위에 앉아 있었다.** 데이터는 정확하지만
게임이 그 행을 만나지 않는다.

### archetype 시스템도 마찬가지였다

ADR-0219 는 `PERSONALITY_SKILL_PREFERENCE` 의 `defensive` / `support` entry 가
cosmetic 이라고 기록했다. band 안에 `defensive` ICE 는 있었지만
(`watchdog` @ g1, `ice_neuromancer_warden` @ g2–g4) **둘 다 `skills: []`** 이라
preference 매칭 자체가 일어나지 않았다. `stealth` ICE (`wisp` @ g1,
`ice_dixie_echo` @ g3) 도 마찬가지였다.

### 밸런스는 calibrate 되어 있고 evidence-backed 다

ADR-0211 은 `ENCOUNTER_HP_BY_GRADE` 와 `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` 를
`npm run balance --runs 100` evidence 로 튜닝했다. 각 상수의 docstring 에
per-grade win-rate 가 남아 있고, 그 표가 이 ADR 의 변경 전 기준선이다.

```
grade  missions  win-rate  mean-turns  mean-HP-end
1      4         100.0%    2.5         91.7
2      16        88.8%     4.4         35.7
3      11        73.0%     6.1         24.0
4      10        47.4%     6.6         5.0
5      9         42.4%     5.9         5.7
6      3         0.0%      5.3         0.0
```

이 표를 흔들면 **design 결정**이 된다. 그래서 band 확대는 ADR-0219 가 남긴
"별도 ADR" 대상이었고, 이 ADR 이 그 결정이다.

## 고려한 옵션

### Option 1: slot 1–3 을 skill-bearing + archetype-diverse 로 교체 (선택)

- **설명**: 각 grade 의 slot 1–3 을 다시 고른다. 우선순위는 (a) 스킬을 가진 ICE,
  (b) archetype diversity (grade 당 최소 1 개의 non-`aggressive` ICE).
  제약은 다섯 개다:
  1. **slot 0 은 모든 grade 에서 immutable.** `encounterIceIdForGrade(grade, undefined)`
     가 `band[0]` 을 돌려주는 legacy 계약 (테스트로 pin 됨) 이다.
  2. 각 grade 의 tier band 안에 머문다 (g1 T1, g2 T1–T2, g3 T2–T3, g4 T3–T4,
     g5 T3–T5, g6 T4–T6).
  3. grade 당 id 4개를 유지한다.
  4. `ENCOUNTER_HP_BY_GRADE`, `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`,
     `iceHpForGrade`, `ice_types.json` 의 어떤 row 도 건드리지 않는다.
  5. 교체한 slot 의 **grade 에서 HP** 와 **auto-attack 피해** (`tier*3 + armor`)
     가 원래 slot 에 최대한 가깝게 match 되도록 고른다.
- **장점**:
  - 스킬 시스템이 **플레이에서 도달 가능**해진다. ADR-0222 / ADR-0223 의 결과가
    처음으로 관측된다.
  - archetype 시스템이 6개 grade 전부에서 발동한다.
  - slot 0 immutability 덕분에 **기존 caller 와 테스트의 고정 id 가 그대로 살아있다.**
  - slot 1–3 은 seed 로 회전하는 부분이므로, 고정 caller 를 깨지 않는다.
- **단점**:
  - **밸런스 곡선을 움직인다.** ADR-0211 의 calibration 이 off-calibration 이 된다.
  - **재캘리브레이션이 필요**하다 — 이 ADR 범위 밖이고 별도 결정이다.
- **Pillar 정합**:
  - P3 (The Flatline): ✅ dead combat path 의 **reach** 가 처음으로 확보된다.
  - P5 (The Style): ✅ archetype 가 flavor 로서가 아니라 실제 선택으로 작동한다.

### Option 2: 밸런스를 무시하고 catalog 전체를 끌어와 band 를 크게 넓힌다

- **설명**: tier band 제약을 버리고, 각 grade 에 skill-bearing ICE 를 가능한 한
  많이 넣는다 (예: g1 에 T2 ICE 포함).
- **단점**:
  - tier band 를 깨면 `iceHpForGrade` 의 cap 이 무의미해지고, ADR-0211 이 튜닝한
    HP 예산이 무너진다.
  - g1 에 T2 를 넣으면 opening deck 과의 타이밍이 뒤집혀 **가장 쉬워야 하는 grade**
    가 어려워진다.
  - skill-bearing T1 ICE 가 2종뿐이라 애초에 g1 을 넓힐 실체가 없다.
- **Pillar 정합**: 실패 (calibrated curve 를 근거 없이 흔든다).

### Option 3: band 는 두고, catalog 의 skill 정의만 손본다

- **설명**: band 를 바꾸지 않고 `ice_types.json` 의 ICE row 를 고쳐 band 안의
  ICE 에 스킬을 붙인다.
- **단점**:
  - **`ice_types.json` 의 row 를 건드린다** — 이번 결정의 명시적 제약 위반이다.
  - 기존 ICE 의 flavor (dmg_base, hp_base, personality) 를 다시 조정해야 해서
    diff 가 catalog 전체로 번진다.
  - ADR-0211 / ADR-0212 가 calibrate 한 표의 의미를 바꾼다.
- **Pillar 정합**: 실패 (diff 범위와 결정의 성격이 어긋난다).

### Option 4: 현상 유지 — band 는 2 slot 만 스킬을 가진다

- **설명**: 아무것도 안 한다.
- **단점**: ADR-0219 의 남은 항목 (3) 이 영영 미해결로 남는다. ADR-0222 / ADR-0223
  의 결과는 계속 플레이에서 관측되지 않는다.
- **Pillar 정합**: 실패 (기록된 후속 항목을 실행하지 않는다).

## 추천 (Recommendation)

**Option 1.** slot 0 immutability 라는 안전장치가 있어 기존 caller 를 깨지 않고,
tier band 안에서만 움직이므로 calibrated HP 예산도 유지된다. 밸런스 이동은
**결과**이지 **사유**가 아니다 — 그리고 그 이동은 별도 결정으로 다룰 수 있다.

## 사용자 결정 (Decision)

**2026-10-27 — slot 1–3 교체로 band 커버리지를 확대하기로 결정했다.** 구현 완료·검증됨.
**재캘리브레이션은 적용하지 않았다** (사용자 결정 대기).

- [x] **Option 1 — slot 1–3 교체 (skill-bearing + archetype-diverse)** — **채택·구현됨**
- [ ] Option 2 — tier band 무시하고 넓히기
- [ ] Option 3 — catalog row 를 손보다
- [ ] Option 4 — 현상 유지 (no-op)

### 결정된 내용

1. **slot 1–3 만 교체했다.** slot 0 은 6개 grade 전부 **byte-identical** —
   `watchdog` @ g1, `spider` @ g2, `black` @ g3, `goliath` @ g4,
   `neuromancer` @ g5/g6.
2. **grade 당 id 는 4개를 유지한다.** (기존 규칙과 동일)
3. **tier band 를 유지한다.** g1 T1, g2 T1–T2, g3 T2–T3, g4 T3–T4, g5 T3–T5,
   g6 T4–T6.
4. **`ENCOUNTER_HP_BY_GRADE`, `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`,
   `iceHpForGrade`, `ice_types.json` 의 어떤 ICE row 도 건드리지 않았다.**
5. **재캘리브레이션은 하지 않았다.** ADR-0211 의 곡선은 지금 off-calibration 이다.
   되돌릴지 다시 맞출지는 **사용자 결정**이다.
6. **ADR-0219 Option A 는 여전히 연기 상태다.** effect 메커닉도 magnitude 도 없다.
7. **ADR-0211 / 0219 / 0222 / 0223 을 포함한 기존 ADR 은 하나도 수정하지 않았다.**
   Accepted 결정은 immutable 이다 (`AGENTS.md` §6). 관계는 이 ADR 에 기록한다.

### 변경된 band (BEFORE → AFTER)

| grade | BEFORE | AFTER |
| --- | --- | --- |
| g1 | `watchdog`, `spider`, `wisp`, `zombie` | `watchdog`, **`sense_net_alert`**, `wisp`, **`hosaka_courier`** |
| g2 | `spider`, `raven`, `surveillance`, `chinese_ice` | `spider`, **`sense_net_spin`**, **`corporate_guard`**, **`loa_zombie`** |
| g3 | `black`, `goliath`, `raven`, `ai_whisper` | `black`, **`hosaka_defender`**, `ice_dixie_echo`, **`sense_net_reporter`** |
| g4 | `goliath`, `ai_whisper`, `hellhound`, `morrison_echo` | `goliath`, **`sense_net_reporter`**, **`yakuza_enforcer`**, **`ta_sentinel`** |
| g5 | `neuromancer`, `revelation`, `loa_entity`, `hellhound` | `neuromancer`, **`sense_net_reporter`**, **`ta_sentinel`**, **`yakuza_enforcer`** |
| g6 | `neuromancer`, `wintermute`, `ice_neuromancer_warden`, `aleph` | `neuromancer`, **`standard_ascended`**, **`ta_sentinel`**, `aleph` |

**slot 0 은 모든 grade 에서 바뀌지 않았다** (`watchdog` / `spider` / `black` /
`goliath` / `neuromancer` / `neuromancer`).

### 커버리지 결과

| metric | BEFORE | AFTER |
| --- | --- | --- |
| band slot 중 스킬을 가진 것 | **2 / 24** | **16 / 24** |
| 도달 가능한 unique skill-bearing band id | **2** | **11** |
| 스킬 보유 ICE 가 있는 grade | 2 (g5, g6) | **6 / 6** |
| non-`aggressive` ICE 가 있는 grade | 2 | **6 / 6** |
| *발사 가능한* (피해를 주는) 스킬 보유 ICE 가 있는 grade | 2 | **4 / 6** (g3–g6) |

## 결과 (Consequences)

### 긍정적 영향

- **스킬 시스템이 플레이에서 도달 가능해졌다.** 24 slot 중 16 slot, unique id 11종,
  6개 grade 전부. ADR-0222 가 authoring 한 스킬 메타데이터와 ADR-0223 이 정정한
  20 개의 분류가 처음으로 band 안의 row 위에 앉는다.
- **archetype 시스템이 발동한다.** 6개 grade 전부가 non-`aggressive` ICE 를
  하나 이상 포함한다. `defensive` preference list 에 매칭 대상이 생겼다.
- **ADR-0219 후속 항목 (3) 이 실행되었다.** Option A 의 선행 조건이 여전히
  미충족이지만, Option A 가 ship 되면 **그 결과가 보인다** — 지금은 보이지 않는다.
- **slot 0 immutability 덕분에 기존 caller 와 테스트가 깨지지 않았다.** seed 없는
  호출은 여전히 legacy 고정 id 를 받는다.

### 부정적 영향 / 수용한 비용

- **ADR-0211 의 밸런스 곡선이 off-calibration 이다.** g2 −11.4pp, g5 −10.4pp,
  g3 +6.0pp. 이 ADR 는 그 사실을 고치지 않는다 — **아래 재캘리브레이션은
  제안만 하고 적용하지 않았다.**
- **g1 의 skill slot 은 지금 발사 불가능하다.** 구조적 한계 (아래 참조).
- **stealth archetype 는 여전히 skill 을 carry 하지 않는다.** catalog authoring
  없이는 불가능하다.

### 밸런스 — plain하게

`npm run balance` (opening deck, 100 runs/mission) BEFORE → AFTER:

| grade | BEFORE | AFTER | delta |
| --- | --- | --- | --- |
| g1 | 100.0% | 100.0% | **0.0pp** |
| g2 | 88.8% | 77.4% | **−11.4pp** |
| g3 | 73.0% | 79.0% | **+6.0pp** |
| g4 | 47.4% | 48.8% | +1.4pp |
| g5 | 42.4% | 32.0% | **−10.4pp** |
| g6 | 0.0% | 0.0% | 0.0pp |

**두 band 가 5pp 이상 움직였다: g2 와 g5.** secondary metric
(`--deck ppl`, 100 runs/mission) 는 g1 0.0 / g2 −1.5 / g3 +3.5 / g4 −0.4 /
g5 0.0 / g6 0.0 이었다.

**원인은 slot 을 하나씩 되돌려 격리했다** (추측이 아니라 실측).

- **archetype-diversity (방어형) slot 이 g2 −15.6pp, g5 −10.4pp 를 만든다.**
  - g2: `corporate_guard` — HP 84 → 118.
  - g5: `ta_sentinel` — auto-damage 12 → 19.
  - 근본 원인: **tier 에 맞는 `defensive` + skill-bearing ICE 는 aggressive peer 보다
    `hp_base` / `defense` 가 대체로 높다.** 이 catalog 에서 tier-appropriate 한
    defensive skill-bearing ICE 를 고르면 그 비용은 피할 수 없다.
- **피해량 profile 을 match 한 skill-bearing slot 은 각각 1.4pp 이하**였다.
- **g3 의 +6.0pp 는 `hosaka_defender` 의 auto-damage 15 vs `goliath` 의 17** 때문이다
  — T2–T3 skill-bearing ICE 중 15 를 넘는 것이 없다, 즉 tier 를 벗어나지
  않으면 피할 수 없다. **주의: g3 는 더 짧고 더 피가 나는 전투가 되었다**
  (mean-HP-end 24.0 → 15.7), 단순히 쉬워진 것이 아니다.

> **이것은 ADR-0211 이 calibrate 한 곡선이 이제 off-calibration 이라는 뜻이다.**
> 그 재캘리브레이션은 **PROPOSED 이지만 NOT applied** 다 (이 작업은 band id
> 변경으로 제한되었다).

### 제안된 재캘리브레이션 (NOT applied — 사용자 결정 필요)

- **Option 1 (권장) — recalibrate.**
  - **g2**: `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` 를 130 → ~60 시도.
    **HP cap 을 올리는 것은 쓸모없다** — 118 은 이미 g2 의 125 cap 아래에
    있으므로, **dmg bonus 만이 실제로 작동하는 lever** 다.
  - **g5**: 0 → ~−10% 시도. cap 은 이미 단조 floor (165) 에 있다.
- **Option 2 (대안) — g2 와 g5 에서 defensive-archetype 요구를 포기한다.**
  - g4 와 g6 은 비용 없이 유지하고 (그 grade 의 defensive slot 은 이득).
  - g2 ≈ 82.2% (defensive 대신 skill-bearing aggressive T2 slot 을 넣을 때)
    와 g5 ≈ 43.1% 로 회복된다.
  - 대가: 그 두 grade 에는 non-`aggressive` ICE 가 **0** 이 된다.
- **추천은 Option 1 이다.** 이동은 *calibration* 문제이지 *design* 문제가 아니다 —
  더 어려운 defensive ICE 는 **합법적으로 catalog 의 일부**다. 다만 **어느 쪽이든
  사용자의 밸런스 결정**이다.

### 구조적 한계 (기록 — coverage 가 도달할 수 있는 상한을 정의한다)

1. **tier-1 ICE 에 피해를 주는 스킬이 없다.** 유일한 두 T1 skill-bearing ICE
   (`hosaka_courier` = buff×2, `sense_net_alert` = debuff×2) 는 0-damage 다.
   combat path 는 `damage > 0` 인 스킬만 발사한다 (ADR-0219 Option B).
   따라서 **g1 의 두 skill slot 은 오늘 구조적으로 발사 불가능**하며, Option A 가
   ship 될 때만 live 가 된다. **이를 우회하려고 magnitude 를 지어내지 않았다.**
2. **catalog 전체의 `stealth` ICE 는 어떤 스킬도 carry 하지 않는다**
   (5개 row 전부 `skills: []`). 따라서 "stealth with skills" slot 은
   **catalog authoring 없이는 불가능**하다.
3. **`support` archetype 는 ICE 가 0종**이다. 그 preference list 는 도달 불가다.
4. **ICE 의 스킬 피해는 자기 row 의 `dmg_base` 에서 파생된다** (`dmg_base + tier*2`),
   그것은 **auto-attack 보다도 큰** 경우가 많다. 그래서 band 에 skill-bearing ICE 를
   넣는 일은 **실제 전투 효과**를 갖는다 — 그것이 이 변경을 재캘리브레이션과
   분리할 수 없는 이유다.

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

> **단, band 교체만 구현됐다.** **재캘리브레이션은 적용하지 않았다.**
> ADR-0211 의 밸런스 곡선은 지금 **off-calibration** 이다 (g2 −11.4pp,
> g5 −10.4pp, g3 +6.0pp). 되돌릴지 재캘리브레이션할지는 **사용자 결정**이다.

**Evidence**:

- `web/src/core/ice_scaling.ts` — `ENCOUNTER_ICE_BY_GRADE` 의 **slot 1–3 이 grade 별로
  재작성**되었다. **slot 0 은 6개 grade 전부 byte-identical** (`watchdog` / `spider` /
  `black` / `goliath` / `neuromancer` / `neuromancer`).
- `web/src/core/ice_scaling.ts` — 모듈 docstring 과 `ENCOUNTER_ICE_BY_GRADE` table
  docstring 이 갱신되었다: 새 의도 (skill coverage / archetype coverage / tier band)
  와 **"slot 0 은 legacy pin 이다"** 라는 보존 note 를 함께 기록.
- `web/tests/ice_scaling.test.ts` — 신규 `describe("encounter band coverage")`
  블록, **7 tests**. 이 중 **3 tests 가 discriminating** 이다 — band 를 이전
  표로 되돌리면 다음 3 개가 실패한다 (실측):
  - `gives every grade at least one skill-bearing ICE`
  - `gives every grade at least one non-aggressive ICE`
  - `covers the skill-bearing catalog in play`
  나머지 4 개는 **guard test** 다 — slot-0 immutability, id 정확히 4개,
  tier band membership, catalog 내 존재를 pin 한다.
- `web/tests/ice_scaling.test.ts` — **기존 테스트를 약화·skip·삭제하지 않았다.**
  diff 는 **추가 112줄, 삭제 0줄** (`git diff --stat`). 이전 band 의 내용을 pin 하던
  기존 assertion 은 하나도 없었다.
- 게이트: `npm test` **125 files / 2958 tests, 0 failures** (2951 + 신규 7);
  `tsc --noEmit` **0 errors**; `eslint` **0 errors** (무관한 pre-existing warning 1건
  은 `src/input/keyboard.ts`).
- 밸런스 (`npm run balance`, opening deck, 100 runs/mission) BEFORE → AFTER 실측:
  g1 100.0 → 100.0 (0.0pp) · g2 88.8 → 77.4 (**−11.4pp**) · g3 73.0 → 79.0 (**+6.0pp**) ·
  g4 47.4 → 48.8 (+1.4pp) · g5 42.4 → 32.0 (**−10.4pp**) · g6 0.0 → 0.0 (0.0pp).
- 밸런스 (`npm run balance -- --deck ppl`, 100 runs/mission): g1 0.0 · g2 −1.5 ·
  g3 +3.5 · g4 −0.4 · g5 0.0 · g6 0.0.
- 원인 격리 (slot 하나씩 이전 표로 되돌려 실측): g2 slot 2 되돌림 → 77.4 → 90.5,
  g5 slot 2 되돌림 → 32.0 → 43.1, g3 slot 1 되돌림 → 79.0 → 73.0.
- 커버리지 실측 (`ice_types.json` 97 row 기준): band slot 중 스킬 보유 **16 / 24**,
  unique skill-bearing band id **11**, 스킬 보유 ICE 가 있는 grade **6 / 6**,
  non-`aggressive` 가 있는 grade **6 / 6**, 발사 가능한 (피해 스킬 보유) grade
  **4 / 6** (g3–g6).
- catalog 실측: 97 row 중 44 row 가 skill-bearing. `stealth` 5 row **전부**
  `skills: []`. `support` **0 row**. T1 skill-bearing 은 `hosaka_courier` /
  `sense_net_alert` 2종이고 둘 다 0-damage effect (`buff` / `debuff`).
- **미변경 확인** — `ENCOUNTER_HP_BY_GRADE`, `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`,
  `iceHpForGrade`, `ice_types.json`, `skill_defs` 는 **모두 미변경**이다
  (`git diff` 로 실측).

**Notes**:

- **diff 는 `web/` 2개 파일뿐이다** — `web/src/core/ice_scaling.ts` (+48 / −8,
  주석 docstring 위주) 와 `web/tests/ice_scaling.test.ts` (+112 / −0, 신규 describe
  블록만). 밸런스 상수와 `ice_types.json` 은 **미변경**이다.
- **재캘리브레이션은 적용하지 않았다.** `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` 의
  g2 (130) 와 g5 (0) 값은 **그대로**다. 곡선은 off-calibration 상태로 남는다.
- **ADR-0219 Option A 는 구현하지 않았다.** effect 메커닉도 magnitude 도 없다.
  combat path (`web/src/core/state_actions_combat.ts`), `web/src/core/ice_ai.ts`,
  `web/src/core/ice_skills.ts`, `web/src/core/types.ts` 는 **모두 미변경**이다.
- **ADR-0211 / 0219 / 0222 / 0223 을 포함한 기존 ADR 은 하나도 수정하지 않았다.**
  Accepted 결정은 immutable 이고 (`AGENTS.md` §6), 관계는 이 ADR 에 기록했다.
- **g1 은 스킬을 발사하지 못한다.** 두 T1 skill-bearing ICE 의 스킬이
  0-damage (`buff` / `debuff`) 이고 combat path 는 `damage > 0` 만 발사한다.
  **이를 가우려고 magnitude 를 저술하지 않았다.**
- **stealth 스킬 slot 은 존재하지 않는다.** catalog 의 `stealth` 5 row 전부가
  `skills: []` 다. `support` 도 0 row 다.

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `web/src/core/ice_scaling.ts` — `ENCOUNTER_ICE_BY_GRADE` 의 slot 1–3 (6개 grade),
  모듈 docstring, table docstring
- `web/tests/ice_scaling.test.ts` — 신규 `describe("encounter band coverage")`
  블록 7 tests (추가만, 기존 assertion 무변경)

### 이번 결정으로 변경되지 않은 항목

- `web/src/core/ice_scaling.ts` — `ENCOUNTER_HP_BY_GRADE`, `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`,
  `iceHpForGrade`, `iceDmgBonusPctForGrade`, `encounterIceIdForGrade` (slot 0 동작)
- `web/src/data/ice_types.json` — 97 ICE row 와 `skill_defs` 88 entry 전부 **미변경**
- `web/src/core/state_actions_combat.ts` — enemy combat path
- `web/src/core/ice_ai.ts` — `PERSONALITY_SKILL_PREFERENCE`, `selectSkillByPersonality`
- `web/src/core/ice_skills.ts` — damage 파생 규칙
- ADR-0211, ADR-0219, ADR-0222, ADR-0223 를 포함한 기존 ADR — **미수정** (immutable)

### 후속 항목 (이번 ADR 범위 밖)

1. **밸런스 재캘리브레이션 결정** (Option 1 vs Option 2) — **사용자 소유.**
2. **ADR-0219 Option A** (shield / heal / regen / buff 메커닉 + magnitude authoring) —
   지금은 **관측 가능**해졌다. ship 되면 g1 의 skill slot 이 live 가 된다.
3. **Catalog authoring gap** — T1 피해 스킬 없음 / stealth 스킬 ICE 없음 /
   `support` ICE 0종.
4. **ADR-0223 의 10개 ambiguous skill 분류** — 여전히 미해결.

## 관련 결정

- ADR-0211 (ICE grade scaling) — **이번 변경이 흔든 calibration 의 owner.**
  그 곡선은 지금 off-calibration 이다. **ADR-0211 은 수정하지 않았다** (immutable).
- ADR-0212 (grade 기반 ICE encounter 배선) — `ENCOUNTER_ICE_BY_GRADE` 가 encounter
  경로에 쓰이기 시작한 결정.
- ADR-0219 (non-damaging ICE 스킬 효과) — **Option A 의 owner.** 이 ADR 은 그
  후속 항목 (3) — encounter band 커버리지 확대 — 을 실행한다. **ADR-0219 는
  수정하지 않았다** (immutable).
- ADR-0222 (ICE 스킬 메타데이터가 heuristic 에서 authored data 로 이동한다) —
  band 가 드러내야 하는 데이터의 owner. **ADR-0222 는 수정하지 않았다** (immutable).
- ADR-0223 (스킬 분류 review pass) — 정정된 20 개의 분류가 플레이에서 보여야
  한다. **ADR-0223 는 수정하지 않았다** (immutable).
- ADR-0161 (ICE personality archetypes) — `defensive` / `stealth` preference list 의
  owner. 이제 매칭 대상이 생겼다.
- ADR-0110 (모듈 사이즈 정책) — `ice_scaling.ts` 의 docstring 확장을 위한 참조.

## 변경 이력

- 2026-10-27: Draft 작성 + Accepted (slot 1–3 교체 — skill coverage +
  archetype diversity, tier band 유지, slot 0 immutable) — 구현 완료·검증.
  ADR-0219 후속 항목 (3) 실행. **재캘리브레이션은 PROPOSED 이나 NOT applied**
  (사용자 결정 대기) — ADR-0211 곡선이 off-calibration 상태로 기록됨.
