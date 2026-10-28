# ADR-0225: Encounter band 재캘리브레이션 — 두 곡선을 동시에 되찾는다 (HP cap 을 살린 채)

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — dead combat path, ADR-0216/0219/0222/0223/0224 sibling)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0161 — ICE personality archetypes](./0161-ice-personality-archetypes.md), [ADR-0211 — ICE grade scaling](./0211-ice-grade-scaling.md), [ADR-0212 — grade 기반 ICE encounter 배선](./0212-grade-driven-ice-encounters.md), [ADR-0219 — non-damaging ICE 스킬 효과](./0219-non-damaging-ice-skill-effects.md), [ADR-0222 — ICE 스킬 메타데이터가 heuristic 에서 authored data 로 이동한다](./0222-ice-skill-metadata-as-data.md), [ADR-0223 — 스킬 분류 review pass](./0223-skill-classification-review.md), [ADR-0224 — Encounter band 커버리지 확대](./0224-encounter-band-coverage.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-27 에 결정·구현·검증까지 완료되었다.
> 구현 범위는 **밸런스 상수 2개 배열 + g5 의 slot 하나**다 —
> `ENCOUNTER_HP_BY_GRADE`, `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` 와
> `ENCOUNTER_ICE_BY_GRADE` 의 grade 5 slot 2.
>
> **첫 번째 재캘리브레이션 시도는 거부됐다.** 그 시도는 opening 곡선을
> ±3pp 안으로 되돌렸지만 **g5/g6 의 HP cap 을 165 → 560 으로 올림으로써**
> cap 메커닉 자체를 무력화했다 (PPL g5 44.4% → 100.0%, +55.6pp).
> 그 시도는 **revert** 됐다. 아래 「기각된 시도」 참조.
>
> **이 결정의 핵심은 slot 을 고친 것이다 — cap 이 아니다.**
> cap 은 최대 165 로 **살아있고**, `ENCOUNTER_HP_BY_GRADE` 는 단조 비감소다.
> **g5 는 더 이상 non-`aggressive` ICE 를 carry 하지 않는다.** 그대가
> archetype diversity 목표의 **명시적 trade** 다.

## 컨텍스트 (Context)

### ADR-0224 가 흔든 곡선

ADR-0224 는 encounter band 의 slot 1–3 을 교체해 ICE 스킬 시스템을 플레이에서
보이게 했다. 그副产品로 **ADR-0211 이 calibrate 한 opening-deck 곡선이 이동**했다.

| grade | ADR-0211 target | post-ADR-0224 | delta |
| --- | --- | --- | --- |
| g2 | 88.8% | 77.4% | **−11.4pp** |
| g3 | 73.0% | 79.0% | **+6.0pp** |
| g5 | 42.4% | 32.0% | **−10.4pp** |

사용자는 **recalibrate** 를 선택했다 (ADR-0224 의 Option 1).

### 기각된 첫 번째 시도 — HP cap 을 무력화했다

첫 재캘리브레이션은 opening 곡선을 ±3pp 안으로 되돌렸다. 하지만 그 방법이
**g5/g6 의 HP cap 을 165 → 560 (= `neuromancer` 의 natural HP)** 으로 올리는 것이었다.
`iceHpForGrade` 는 `min(natural HP, cap)` 이므로 cap 이 natural HP 위에 있으면
**cap 은 no-op** 이다 — 즉 **HP cap 메커닉이 사실상 비활성화**됐다.

이 메커닉은 ADR-0211 이 도입한 것이다: opening deck 에 climax 가 **이길 수 없게**
두면서도 개발된 deck 에는 **달성 가능하게** 만드는 장치다. 그 장치를 없앤 대가는
실측됐다.

| metric | before | after (기각된 시도) | delta |
| --- | --- | --- | --- |
| PPL g5 | 44.4% | **100.0%** | **+55.6pp** |

### 근본 원인 — 긴장은 단 하나의 slot 에서 왔다

frontier 실측은 두 개의 calibration lever 만으로는 **두 곡선을 동시에** 만족시킬 수
없음을 보여주었다.

| PPL g5 목표 | 가능한 opening g5 | residual |
| --- | --- | --- |
| ≤ 45% | 35.0% | **−7.4pp** |
| ≤ 50% | 38.2% | **−4.2pp** |
| = 100% | 43.4% | **+1.0pp** |

opening 곡선을 맞추려면 PPL g5 가 100% 가 될 수밖에 없었고, 그건 cap 을 죽이는
방법이었다. **근본 원인은 하나의 slot — g5 의 `ta_sentinel` (T4, `defensive`)** 이었다.
이 slot 을 opening deck 이 이길 수 있게 만들려면 cap 을 해체해야 했고, 그 결과
g5 grade 전체가 developed deck 에 대해 자명해졌다.

**결론: slot 을 고쳐야 한다. cap 이 아니라.**

## 고려한 옵션

### Option 1: g5 slot 을 교체하고 cap 을 살린다 (선택)

- **설명**: `ENCOUNTER_ICE_BY_GRADE` 의 grade 5 slot 2 를 `ta_sentinel` →
  `loa_entity` 로 교체한다. `loa_entity` 는 T3 `aggressive` skill-bearing ICE 다
  (`manifest_form` buff + `voodoo_curse` poison — poison 은 실제로 발사된다.
  ADR-0216 / ADR-0218 이 스킬 피해 를 live 로 만들었다). auto-attack profile 도
  ADR-0224 이전에 그 slot 이 차지하던 것과 같다 (5 auto-attack). 그러면 g5 의
  opener 가 이길 수 있는 band row 는 모두 cap 아래에 자연스럽게 들어오고,
  **flat 165 ceiling 만으로** grade 를 tune 할 수 있다.
- **장점**:
  - **HP cap 메커닉이 살아남는다.** max cap 165, `ENCOUNTER_HP_BY_GRADE` 단조 비감소.
  - **두 곡선이 동시에 복구된다.** opening 은 ±1.4pp, PPL g5/g6 은 byte-identical.
  - ADR-0224 가 얻은 스킬 시스템 가시성이 **보존된다** (g5 는 여전히 skill-bearing
    slot 3개를 갖는다).
- **단점**:
  - **g5 에 non-`aggressive` ICE 가 없다.** archetype diversity 는 g1–g4 와 g6 에서만
    성립한다 (g4 와 g6 는 둘 다 `ta_sentinel` 을 유지한다).
- **Pillar 정합**:
  - P3 (The Flatline): ✅ ADR-0224 가 연 skill surface 를 유지하면서 dead combat
    path 의 균형이 되살아난다.
  - P5 (The Style): ⚠️ g5 의 archetype diversity 는 포기한다 (명시적 trade).

### Option 2: g5/g6 의 cap 을 560 으로 올린다 (기각된 시도)

- **설명**: `ENCOUNTER_HP_BY_GRADE` 의 g4/g5/g6 을 168/560/560 으로 올린다.
  `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` 는 g5 −79, g6 −78.
- **장점**: opening 곡선을 ±3pp 안으로 되돌린다.
- **단점**:
  - **HP cap 이 무력화된다.** `iceHpForGrade` 의 `min(natural, cap)` 에서 cap 이
    natural HP 위라 no-op 이 된다 — ADR-0211 의 메커닉이 사라진다.
  - **PPL g5 44.4% → 100.0% (+55.6pp)** 실측. developed deck 에 g5 가 자명해진다.
  - **기각됐다.** 이 ADR 은 그 시도의 revert 를 포함한다.
- **Pillar 정합**: 실패 (calibration 의 목적 — climax 난이도 — 을 무너뜨린다).

### Option 3: g5 와 g6 의 archetype diversity 포기 (ADR-0224 Option 2)

- **설명**: g4 와 g6 은 유지하고 g5/g6 의 defensive slot 을 빼서 곡선을 복구한다.
- **단점**: 두 grade 에 non-`aggressive` ICE 가 0 이 된다. **이 ADR 의 결과와
  실질적으로 같다** (g5 가 diverse 하지 않다) — 그럼에도 cap 을 살리는 이 선택이
  더 낫다.
- **Pillar 정합**: 부분 실패 (cap 을 살리면서 diversity 하나를 잃는다).

### Option 4: 현상 유지 (no-op)

- **설명**: ADR-0224 의 곡선을 그대로 둔다.
- **단점**: ADR-0211 의 calibration 이 off-calibration 상태로 남는다. 사용자가
  recalibrate 를 선택했으므로 무효.
- **Pillar 정합**: 실패 (사용자의 결정을 실행하지 않는다).

## 추천 (Recommendation)

**Option 1.** 두 calibration lever (HP cap, dmg bonus)만으로는 두 곡선을 동시에
만족시킬 수 없다 — 그건 실측된 frontier 다. 세 번째 lever 를 도입해야 하는데,
여기서 세 번째 lever 는 **slot 교체** — 즉 **catalog 를 건드리지 않고 band 안에서
하나의 id 만 바꾸는 것**이다. 비용은 g5 의 archetype diversity 하나이고, 그건
ADR-0224 가 얻은 스킬 시스템 가시성 을 살리는 대가다.

## 사용자 결정 (Decision)

**2026-10-27 — slot 을 교체하는 방식으로 재캘리브레이션하기로 결정했다.** 구현 완료·검증됨.

- [x] **Option 1 — g5 slot 교체 + cap 유지** — **채택·구현됨**
- [ ] Option 2 — g5/g6 cap 을 560 으로 (기각된 시도 — revert)
- [ ] Option 3 — g5/g6 archetype diversity 포기
- [ ] Option 4 — 현상 유지 (no-op)

### 결정된 내용

1. **`ENCOUNTER_HP_BY_GRADE` → `[75, 86, 155, 165, 165, 165]`**
   - cap 을 보존하면서 작동한 두 조정 (g2 125→86, g3 140→155) 은 **유지**했다.
   - **g4/g5/g6 은 165 로 복원**했다 (기각된 시도의 168/560/560 은 revert).
   - max cap 은 165 이고 배열은 **단조 비감소**다 (g1 75 ≤ g2 86 ≤ g3 155 ≤ g4 165
     ≤ g5 165 ≤ g6 165).
2. **`ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` → `[50, 130, 0, 0, 0, -20]`**
   - **ADR-0211 original 값으로 복원**했다 (기각된 시도의 −79/−78 은 revert).
3. **`ENCOUNTER_ICE_BY_GRADE` — 오직 grade 5 slot 2 만 변경:**
   `ta_sentinel` → `loa_entity`.
   - 다른 모든 grade 와 slot 은 **미변경**이다.
   - **slot 0 은 모든 grade 에서 immutable** 이다 (ADR-0224 와 동일).
4. **`ice_scaling.ts` 의 calibration rationale docstring 이 재작성**되어 **현행
   configuration** 과 그 **실측 evidence** 를 기술한다.
   - 560 / −79 / −78 / 168 이 언급되는 곳은 **"이전 시도는 X 를 했고 Y 를 치렀다"**
     라는 **history** 뿐, 현행 상태에 대한 주장이 아니다.

### 변경된 band (BEFORE → AFTER)

| grade | BEFORE (post-ADR-0224) | AFTER |
| --- | --- | --- |
| g1 | `watchdog`, `sense_net_alert`, `wisp`, `hosaka_courier` | **미변경** |
| g2 | `spider`, `sense_net_spin`, `corporate_guard`, `loa_zombie` | **미변경** |
| g3 | `black`, `hosaka_defender`, `ice_dixie_echo`, `sense_net_reporter` | **미변경** |
| g4 | `goliath`, `sense_net_reporter`, `yakuza_enforcer`, `ta_sentinel` | **미변경** |
| g5 | `neuromancer`, `sense_net_reporter`, **`ta_sentinel`**, `yakuza_enforcer` | `neuromancer`, `sense_net_reporter`, **`loa_entity`**, `yakuza_enforcer` |
| g6 | `neuromancer`, `standard_ascended`, `ta_sentinel`, `aleph` | **미변경** |

## 결과 (Consequences)

### 실측 결과 — 두 곡선이 모두 만족된다

**Opening deck** (ADR-0211 target → measured → residual):

| grade | ADR-0211 target | measured | residual |
| --- | --- | --- | --- |
| g1 | 100.0% | **100.0%** | 0.0pp |
| g2 | 88.8% | **88.6%** | −0.2pp |
| g3 | 73.0% | **73.1%** | +0.1pp |
| g4 | 47.4% | **48.8%** | +1.4pp |
| g5 | 42.4% | **43.1%** | +0.7pp |
| g6 | 0.0% | **0.0%** | 0.0pp |

**6개 grade 전부 ±1.4pp 이내**다 (허용 오차는 ±3pp). 단조 비증가 (non-increasing) 유지.

**PPL (developed) deck** — post-ADR-0224 baseline 대비:

| grade | post-ADR-0224 | measured | delta |
| --- | --- | --- | --- |
| g1 | 100.0% | 100.0% | 0.0pp |
| g2 | 70.8% | **77.9%** | **+7.1pp** |
| g3 | 100.0% | **97.8%** | **−2.2pp** |
| g4 | 88.8% | 88.8% | 0.0pp |
| g5 | 44.4% | **44.4%** | **0.0pp** |
| g6 | 31.3% | **31.3%** | **0.0pp** |

**g5 와 g6 은 byte-identical** — PPL g5 의 **+55.6pp 회귀가 cap 을 살린 채 완전히
되돌아왔다.**

두 개의 이동은 모두 cap 변경에서 비롯되었고 둘 다 benign 이다.

- **PPL g2 +7.1pp — 더 쉬워짐.** g2 cap 125→86 이 `corporate_guard` 의 118 HP 를
  두 deck 모두에서 잘라낸다. PPL g2 는 그 docstring 이 이미 문제로 지적한
  **비단조 dip** 이었다.
- **PPL g3 −2.2pp — 아주 조금 더 어려워짐.** g3 cap 140→155 가 contest 를 높인다.

### 긍정적 영향

- **두 곡선이 복구되었다.** opening 은 모든 target 에서 ±1.4pp 이내, PPL g5/g6 은
  원위치.
- **ADR-0211 의 HP cap 메커닉이 살아있다.** max cap 165, 단조 비감소. climax 는
  opening deck 에 여전히 이길 수 없다 (g6 0.0%).
- **ADR-0224 가 얻은 스킬 시스템 가시성이 보존된다.** g5 는 여전히 skill-bearing
  slot 3개를 갖는다 (`sense_net_reporter`, `loa_entity`, `yakuza_enforcer`).
- **`loa_entity` 의 poison 이 실제로 발사된다** (`voodoo_curse`) — ADR-0216 / ADR-0218
  이 스킬 피해를 live 로 만든 결과가 g5 에서 관측된다.

### 부정적 영향 / 수용한 비용

- **g5 는 더 이상 non-`aggressive` ICE 를 carry 하지 않는다.** archetype diversity
  목표는 **g1–g4 와 g6 에서만** 성립한다 (g4 와 g6 는 둘 다 `ta_sentinel` 유지).
  **이것이 cap 을 지키기 위한 명시적 trade 다.**
- **PPL g2 가 +7.1pp, PPL g3 가 −2.2pp 이동했다** — cap 변경의 부수 효과.

### 후속 항목 (이번 ADR 범위 밖)

1. **g5 archetype gap** — 두 개의 global 배열로는 닫을 수 없었다. **세 번째 lever**
   가 필요하다: tier-appropriate 한 `defensive` skill-bearing ICE 를 authoring 하거나
   (slot 의 HP / damage profile 을 맞춰서), per-ICE calibration knob 을 추가하거나.
2. **ADR-0219 Option A** (shield / heal / regen / buff 메커닉 + magnitude authoring) —
   **여전히 연기 상태다.** g1 의 두 skill slot 은 여전히 구조적으로 발사 불가능하다
   (tier-1 ICE 에 피해를 주는 스킬이 없다).
3. **ADR-0223 의 10개 ambiguous skill 분류** — 여전히 미해결.
4. **Catalog authoring gap** — tier-1 피해 스킬 없음 / 스킬을 carry 하는 `stealth`
   ICE 없음 / `support` 는 0 종.

### 관계

이 결정은 **ADR-0224 가 흔든 곡선을 재캘리브레이션**하고, **ADR-0211 의 calibration
의도를 복원**한다. ADR-0211 / 0219 / 0222 / 0223 / 0224 는 Accepted 이며 immutable
하다 (`AGENTS.md` §6) — **수정하지 않았다.** 관계는 이 ADR 에 기록했다.

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:

- `web/src/core/ice_scaling.ts` — `ENCOUNTER_HP_BY_GRADE` 가
  `[75, 86, 155, 165, 165, 165]` (max cap 165, 단조 비감소),
  `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` 가 `[50, 130, 0, 0, 0, -20]`
  (ADR-0211 original 값) — 두 배열 모두 현행 configuration 을 기술한다.
- `web/src/core/ice_scaling.ts` — `ENCOUNTER_ICE_BY_GRADE` 의 **grade 5 slot 2 만**
  `ta_sentinel` → `loa_entity` 로 변경. 다른 모든 grade 와 slot 은 미변경,
  **slot 0 은 모든 grade 에서 immutable**.
- `web/src/core/ice_scaling.ts` — 모듈 header, `ENCOUNTER_HP_BY_GRADE`,
  `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`, `ENCOUNTER_ICE_BY_GRADE` docstring 이
  **measured per-grade 표와 residual** 로 갱신되었다. 560 / −79 / −78 / 168 은
  "이전 시도는 X 를 했고 Y 를 치렀다" 는 history 로만 남았다.
- `web/tests/ice_scaling.test.ts` — **assertion 2개 갱신, 1개는 더 엄격하게 복원.**
  **약화·skip·삭제된 assertion 은 없다.**
  - (a) `applies a negative ICE dmg modifier at the g6 climax` — 이전의
    `iceDmgBonusPctForGrade(5) < 0` + `< g4` 를 **`toBe(0)`** +
    `toBeLessThanOrEqual(g4)` 로 갱신. 이전 assertion 은 기각된 시도의 −79 를
    그대로 encode 하고 있었다.
  - (b) `gives every grade at least one non-aggressive ICE` →
    **"…except g5"** 로 개명. g5 는 **명시적으로 assert 되는 documented exception**
    이다 (`nonAggressive.length === 0` 이 skip 이 아니라 **pin** 된다). g1–g4 와 g6
    는 여전히 `> 0` 을 요구하고, g4/g6 의 `ta_sentinel` 커버리지도 여전히 assert 된다.
  - (c) `places a band ICE from the grade-5 set` — **assertion 변경 없음.** stale 한
    comment 만 정정되었고, assertion 은 **original 의 더 엄격한 fixed ceiling**
    `toBeLessThanOrEqual(165)` 로 **복원**됐다 (기각된 시도는 560 cap 을 수용하려고
    natural-HP bound 로 완화했었다).
- 게이트: `npm test` **125 files / 2958 tests, 0 failures**;
  `tsc --noEmit` **0 errors**; `eslint` **0 errors** (무관한 pre-existing warning 1건은
  `src/input/keyboard.ts`).
- 밸런스 (`npm run balance`, opening deck, 100 runs/mission): g1 100.0 → **100.0**
  (0.0pp) · g2 88.8 → **88.6** (−0.2pp) · g3 73.0 → **73.1** (+0.1pp) ·
  g4 47.4 → **48.8** (+1.4pp) · g5 42.4 → **43.1** (+0.7pp) · g6 0.0 → **0.0** (0.0pp).
  **6개 grade 전부 ±1.4pp 이내.**
- 밸런스 (`npm run balance -- --deck ppl`, 100 runs/mission): g1 100.0 (0.0pp) ·
  g2 70.8 → **77.9** (+7.1pp) · g3 100.0 → **97.8** (−2.2pp) · g4 88.8 (0.0pp) ·
  **g5 44.4 (0.0pp)** · **g6 31.3 (0.0pp)**.
- 두 밸런스 테이블 모두 재실행했고 **결정적(deterministic)** 이었다.

**Notes**:

- **diff 는 `web/` 2개 파일뿐이다** — `web/src/core/ice_scaling.ts` 와
  `web/tests/ice_scaling.test.ts`. 밸런스 상수 2개와 band 의 g5 slot 하나가
  유일한 실질 변경이다.
- **기각된 첫 번째 시도의 revert 가 이 ADR 의 일부다.** `ENCOUNTER_HP_BY_GRADE` 의
  168/560/560 과 `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` 의 −79/−78 은 **revert** 됐다.
  현재 상태에 그 값들이 남아있지 않다.
- **`ice_types.json` 은 미변경이다.** `loa_entity` 의 스킬 (`manifest_form` buff +
  `voodoo_curse` poison) 은 기존 catalog row 에 있었다 — 새로 저술한 것이 아니다.
- **ADR-0211 / 0219 / 0222 / 0223 / 0224 를 포함한 기존 ADR 은 하나도 수정하지
  않았다.** Accepted 결정은 immutable 이고 (`AGENTS.md` §6), 관계는 이 ADR 에
  기록했다.
- **g5 의 archetype gap 은 닫히지 않았다.** g5 는 여전히 all-`aggressive` 다. 닫으려면
  세 번째 lever 가 필요하다 (위 후속 항목 1).

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `web/src/core/ice_scaling.ts` — `ENCOUNTER_HP_BY_GRADE` (6 grade),
  `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` (6 grade), `ENCOUNTER_ICE_BY_GRADE`
  (grade 5 slot 2), 모듈 header + 세 상수의 docstring
- `web/tests/ice_scaling.test.ts` — assertion 2개 갱신 + 1개 comment 정정
  (test 이름 1개 개명)

### 이번 결정으로 변경되지 않은 항목

- `web/src/core/ice_scaling.ts` — `iceHpForGrade`, `iceDmgBonusPctForGrade`,
  `encounterIceIdForGrade` (slot 0 동작), `clampGrade`, `missionGradeOf`,
  `missionSeedOf`
- `web/src/data/ice_types.json` — 97 ICE row 와 `skill_defs` 88 entry 전부 **미변경**
- `web/src/core/state_actions_combat.ts` — enemy combat path, boss bonus skip 가드
- `web/src/core/ice_ai.ts` — `PERSONALITY_SKILL_PREFERENCE`, `selectSkillByPersonality`
- `web/src/core/ice_skills.ts` — damage 파생 규칙
- ADR-0211, ADR-0219, ADR-0222, ADR-0223, ADR-0224 를 포함한 기존 ADR — **미수정**
  (immutable)

### 후속 항목 (이번 ADR 범위 밖)

1. **g5 archetype gap** — tier-appropriate 한 `defensive` skill-bearing ICE authoring
   또는 per-ICE calibration knob. 두 개의 global 배열로는 불가능하다.
2. **ADR-0219 Option A** (shield / heal / regen / buff 메커닉 + magnitude authoring) —
   여전히 연기. g1 의 두 skill slot 이 live 가 되지 않는다.
3. **ADR-0223 의 10개 ambiguous skill 분류** — 여전히 미해결.
4. **Catalog authoring gap** — tier-1 피해 스킬 없음 / 스킬을 carry 하는 `stealth`
   ICE 없음 / `support` 0 종.

## 관련 결정

- ADR-0211 (ICE grade scaling) — **이번 결정이 복원한 calibration 의 owner.**
  HP cap 메커닉도 이 ADR 에서 도입됐다. **ADR-0211 은 수정하지 않았다** (immutable).
- ADR-0212 (grade 기반 ICE encounter 배선) — `ENCOUNTER_ICE_BY_GRADE` 가 encounter
  경로에 쓰이기 시작한 결정.
- ADR-0219 (non-damaging ICE 스킬 효과) — Option A 의 owner. Option A 는 여전히
  연기 상태다. **ADR-0219 는 수정하지 않았다** (immutable).
- ADR-0222 (ICE 스킬 메타데이터가 authored data 로 이동) — band 가 드러내야 하는
  데이터의 owner. **ADR-0222 는 수정하지 않았다** (immutable).
- ADR-0223 (스킬 분류 review pass) — 정정된 20 개의 분류가 플레이에서 보여야 한다.
  **ADR-0223 은 수정하지 않았다** (immutable).
- ADR-0224 (Encounter band 커버리지 확대) — **이 ADR 이 재캘리브레이션하는 결정.**
  ADR-0224 가 얻은 스킬 시스템 가시성은 보존되었다 (g5 slot 하나만 교체).
  **ADR-0224 는 수정하지 않았다** (immutable).
- ADR-0161 (ICE personality archetypes) — `defensive` / `stealth` preference list 의
  owner. **g5 에서는 더 이상 매칭 대상이 없다** (명시적 trade).
- ADR-0110 (모듈 사이즈 정책) — `ice_scaling.ts` 의 docstring 확장을 위한 참조.

## 변경 이력

- 2026-10-27: Draft 작성 + Accepted (g5 slot 교체 — `ta_sentinel` → `loa_entity`,
  HP cap 165 로 유지, dmg bonus ADR-0211 original 로 복원) — 구현 완료·검증.
  **첫 번째 시도 (cap 560 / −79 / −78) 는 기각·revert** — PPL g5 44.4% → 100.0%
  (+55.6pp) 회귀 때문. ADR-0224 가 흔든 곡선을 재캘리브레이션하고 ADR-0211 의
  calibration 의도를 복원. **g5 archetype gap 은 명시적으로 남아 있다.**
