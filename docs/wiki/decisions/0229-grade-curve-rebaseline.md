# ADR-0229: Grade 난이도 곡선 재기준화 (re-baseline) — ADR-0211 의 per-grade win-rate target 은 대체된다

**상태**: Accepted
**날짜**: 2026-10-29
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — 밸런스 프로세스 결정, ADR-0228 후속 항목 4 종결)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0161 — ICE personality archetypes](./0161-ice-personality-archetypes.md), [ADR-0211 — ICE grade scaling](./0211-ice-grade-scaling.md), [ADR-0212 — grade 기반 ICE encounter 배선](./0212-grade-driven-ice-encounters.md), [ADR-0224 — Encounter band 커버리지 확대](./0224-encounter-band-coverage.md), [ADR-0225 — Encounter band 재캘리브레이션](./0225-encounter-band-recalibration.md), [ADR-0226 — Non-damaging ICE 스킬 효과를 구현한다](./0226-non-damaging-ice-skill-effects-implemented.md), [ADR-0227 — ICE 아키타입 일관성 검토](./0227-ice-archetype-consistency-review.md), [ADR-0228 — ICE 아키타입 동작 배선](./0228-ice-archetype-behavior-wiring.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-29 에 결정·구현·검증까지 완료되었다.
>
> **이 ADR 은 behavior 를 바꾸지 않는다. calibration 배열의 값은 하나도
> 바뀌지 않았다.** `ENCOUNTER_HP_BY_GRADE` = `[75, 86, 141, 165, 165, 165]`,
> `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` = `[50, 130, 8, 0, 0, -20]` — **그대로다.**
>
> **바뀐 것은 "무엇이 목표인가" 다.** ADR-0211 의 per-grade win-rate target 은
> **지금 달성된 곡선**으로 대체되고, 대신 **drift policy** 가 세워진다 — 즉
> "이 곡선을 앞으로 무엇의 기준으로 지키는가" 라는 규칙.
>
> **ADR-0211 은 Accepted 이며 immutable 하다 (`AGENTS.md` §6).** 따라서
> ADR-0211 파일은 **수정하지 않았다.** 대체 관계는 **이 ADR 과
> `decisions/README.md` 의 인덱스** 에 기록했다.

## 컨텍스트 (Context)

### ADR-0228 이 남긴 후속 항목 4

ADR-0228 (ICE 아키타입 동작 배선) 은 후속 항목 4 에 이렇게 적었다:

> **반복되는 재캘리브레이션 churn** — 연속된 기능 단계 (band 확대 ADR-0224,
> 스킬 효과 ADR-0226, archetype 데이터 ADR-0227, 그리고 이번 crit) 가
> **각각** ADR-0211 곡선을 움직였고, **두 global lever 로는 항상 되돌릴 수
> 없었다.** ADR-0211 target 을 **한 번 re-baseline** 할지, **per-ICE
> calibration knob** 이 필요한지 검토할 것. **이것은 정당한 프로세스
> 결정이며 말로 남겨서는 안 된다.**

**이 ADR 은 그 후속 항목 4 를 종결한다.** 답은 "**한 번 re-baseline 한다**" 다.

### churn 의 실측 — 네 번의 연속 이동

ADR-0211 은 opening-deck 곡선을 이 per-grade target 으로 calibrate 했다:
`g1 100.0 / g2 88.8 / g3 73.0 / g4 47.4 / g5 42.4 / g6 0.0`.
이후 **네 개의 연속된 기능 단계** 가 각각 그 곡선을 움직였다. 실측값:

| 단계 | 무엇이 바뀌었는가 | 이동 (opening deck) | 대응 |
| --- | --- | --- | --- |
| **ADR-0224** | encounter band slot 1–3 교체 (스킬/아키타입 커버리지) | **g2 −11.4pp** (88.8 → 77.4), **g3 +6.0pp** (73.0 → 79.0), **g5 −10.4pp** (42.4 → 32.0) | ADR-0225 가 재캘리브레이션 |
| **ADR-0226** | non-damaging ICE 스킬 효과 구현 (`shield`/`heal`/`regen`/`buff`) | **g4 +0.2pp** (48.8 → 49.0) | 재캘리브레이션 불필요 |
| **ADR-0227** | ICE 아키타입 데이터 교정 (`hosaka_defender` → `defensive`) | **g3 +16.6pp** (73.1 → 89.7) | g3 HP cap 155 → 141 + dmg bonus 0 → +8% |
| **ADR-0228** | `getCritBonus` 배선 (`aggressive` ICE crit) | **g4 −9.7pp** (49.0 → 39.3), **g5 −7.4pp** (43.1 → 35.7) | 재캘리브레이션 제안만·미적용 |

**네 단계 중 세 단계가 ±3pp 를 벗어났다.** 그리고 ADR-0227 의 g3 +16.6pp 는
**단조 비증가 invariant 까지 깨뜨렸다** (g3 89.7% > g2 88.6%).

### 왜 per-feature 추격을 멈춰야 하는가 — 두 레버의 제약 (실측)

이 churn 을 지속할 수 없게 만든 것은 **레버의 구조**다. 두 레버는
**step function** 이고 **cliff** 를 가진다.

1. **HP cap 은 상한이 있다.** `iceHpForGrade` 의 단조 비감소 invariant
   (`keeps HP monotonic non-decreasing across grades for every band id`,
   `web/tests/ice_scaling.test.ts`) 때문에 `c3 <= c4 = 165` 다. ADR-0227 이
   실측했다: `c3 = 165` 에서 g3 은 **76.3%** — 73.0% target 에서 **+3.3pp**,
   즉 ±3pp 창 **밖**이다. `155..165` 사이의 어떤 cap 값도 창 안에 떨어지지
   않는다.
2. **dmg bonus 는 계단 함수다.** `floor((tier * 3 + armor) * (1 + pct / 100))`
   는 g3 band 의 auto-attack base (14/15/13/13) 위에서 `+14%` 미만에서 **두 개의
   도달 가능한 벡터만** 만든다 — `(14,15,13,13)` at 0%, `(15,16,14,14)` at +8%.
   중간 `+7%` step 은 **no-op** (839/1100 wins, 0% 와 동일) 이고, `+8%` 은
   **cliff** 다 — `c3 = 165` 에서 g3 을 76.3% → **51.5%** (−24.8pp) 로 떨어뜨린다.
   **사이의 도달 가능한 값이 없다.**
3. **두 레버는 항상 같이 움직인다.** band 안의 slot 교체 (ADR-0225 가 한 것) 가
   세 번째 lever 다 — 그것도 **catalog 를 건드리지 않고** slot id 하나만 바꾸는
   것으로 제약된다 (ADR-0228 의 후속 항목 1: "g5 archetype gap").

**요약: 목표 곡선에 도달할 수 있는 점이 이산적이고, 그 점이 이동할 때마다
새 target 을 다시 쓰는 것 외에 선택지가 없다.** 그리고 그 "다시 쓰기" 가
**매 기능 단계마다 반복**됐다.

### 근본 사실 — 엔진의 난이도는 실제로 변했다

**이 곡선은 목표를 어긴 게 아니라, 게임이 다른 게임이 됐다.** ADR-0224 는
ICE 스킬 시스템을 플레이에 노출했고, ADR-0226 은 그 스킬의 효과를 실제로
발사시켰고, ADR-0227 은 catalog 의 아키타입을 자기 이름과 일치시키고,
ADR-0228 은 `aggressive` ICE 가 crit 하도록 배선했다. **이것은 모두
ADR-0216 계열의 "dead combat path" 결함을 고친 작업이다** — 되돌리면
dead path 가 되살아난다. 그러므로 "예전 곡선을 되찾는다" 는 선택지는
**기능을 되돌리는 것**과 같았고, 그것은 선택지가 아니었다.

## 고려한 옵션

### Option 1: 한 번 re-baseline 한다 — 현 달성 곡선을 새 기준선으로 삼는다 (선택)

- **설명**: 지금 달성된 곡선 (opening deck `100.0 / 88.6 / 73.1 / 39.3 /
  35.7 / 0.0`) 을 **새 baseline** 으로 선언한다. ADR-0211 의 per-grade
  win-rate target 은 이 ADR 에 **대체(superceded)** 된다. 대신 **drift
  policy** 를 세운다 — 앞으로의 drift 를 무음으로 허용하지 않고, 감지되면
  그 change 자신의 ADR 이 **명시적으로 re-baseline 하거나** 되돌려야 한다.
- **장점**:
  - **churn 이 끝난다.** 앞으로의 기능 단계는 "예전 수치를 되찾을 것인가" 를
    재검토하지 않는다.
  - **기준선이 실측과 일치한다.** ADR-0211 의 target 은 더 이상 어긋난 숫자가
    아니다 — 현재 곡선과 **정확히 같다.**
  - **기능을 되돌릴 필요가 없다.** dead combat path 결함 수정은 그대로 산다.
  - **drift policy 가 다음 churn 을 방지한다** — 무음 drift 를 금지하고
    invariant 를 hard 로 유지한다.
- **단점**:
  - **"목표" 와 "달성치" 의 거리가 사라진다.** baseline 은 더 이상
    "되어야 하는 수치" 가 아니라 "여기서부터 시작하는 수치" 다. 그래서
    drift policy 가 그 빈자리를 메워야 한다.
  - **ADR-0211 의 숫자 (88.8 / 73.0 / 47.4 / 42.4) 는 더 이상 유효하지 않다.**
    다른 문서가 그 숫자를 인용하면 함께 갱신해야 한다.
- **Pillar 정합**:
  - P3 (The Flatline): ✅ 검증 가능한 기준선 + drift policy 로 밸런스
    프로세스가 규칙이 되었다.
  - P4 (The Build): ✅ 측정값과 문서가 다시 일치한다.

### Option 2: per-ICE calibration knob 을 도입한다 (ADR-0228 후속 항목 4 의 다른 절반)

- **설명**: 두 개의 global 배열 대신, ICE 또는 band slot 별로 knob 을 둔다.
  그러면 target 에 개별 도달할 수 있어 per-feature 추격이 이론적으로 가능해진다.
- **단점**:
  - **새 subsystem 이다.** knob 의 단위 (per-ICE? per-slot? per-grade-per-ICE?)
    가 정의되지 않았다. calibration surface 의 크기가 6 grade × 4 slot 으로
    늘고, 무엇을 조정하면 무엇이 움직이는지 **예측 불가능**해진다.
  - **지금 필요한 문제가 아니다.** 지금의 문제는 "곡선을 유지하는 법" 이지
    "곡선을 세밀하게 조율하는 법" 이 아니다.
  - **ADR-0211 의 두 레버는 이미 충분하다** — 부족한 것은 **목표** 였다.
  - **추가 후속으로 남긴다** (per-ICE knob 이 정말 필요해지는 시점 = grade 별
    encounter identity 를 바꿔야 할 때).
- **Pillar 정합**: P4 관점으로는 과한 설계.

### Option 3: 현상 유지 — ADR-0211 target 을 그대로 둔다

- **설명**: 아무것도 하지 않는다. g4/g5 는 ±3pp 창 밖이지만, 그건
  "문서화된 예외" 로 둔다.
- **단점**:
  - **ADR-0228 의 후속 항목 4 가 미해결로 남는다.** 그리고 그 미해결은
    다음 기능 단계마다 다시打开된다 — 이게 바로 churn 이다.
  - **ADR-0211 은 immutable 이므로 "문서화된 예외" 를 거기에 쓸 수 없다.**
    그러니 **어디에 쓰지?** — 이것 자체가 Option 3 의 구조적 결함이다.
  - **기준선과 실측의 괴리가 계속 widen 된다.**
- **Pillar 정합**: 실패 (기록된 후속 항목을 실행하지 않는다).

### Option 4: ADR-0211 을 수정한다 (target 표를 고쳐서 새 수치를 넣는다)

- **설명**: ADR-0211 파일의 target 표를 새 수치로 덮어쓴다.
- **단점**:
  - **금지된다.** ADR-0211 은 Accepted 이며 immutable 하다 (`AGENTS.md` §6).
    **이 ADR 은 ADR-0211 을 수정하지 않았다.**
- **Pillar 정합**: 실패 (프로세스 위반).

## 추천 (Recommendation)

**Option 1.** 기록된 사실은 이것이다 — **기능이 4번 연속 곡선을 움직였고,
2개의 레버는 step function 이며 cliff 가 있어 항상 되돌릴 수 없었다.**
이것은 "curve chasing" 이 실패한 것이 아니라 **curve chasing 이
구조적으로 불가능한 문제** 라는 뜻이다. 그리고 엔진의 난이도는 실제로
변했다 (ICE 시스템이 이제 real 이다). 그러므로 **한 번 재기준화** 하고,
앞으로는 **drift policy** 로 규율한다.

**Option 2 (per-ICE knob) 는 후속으로 남긴다.** 지금은 필요하지 않다.

## 사용자 결정 (Decision)

**2026-10-29 — 한 번 re-baseline 하기로 결정했다.** 구현 완료·검증됨.

- [x] **Option 1 — 한 번 re-baseline (현 달성 곡선 = 새 baseline)** — **채택·구현됨**
- [ ] Option 2 — per-ICE calibration knob 도입 (후속으로 남김)
- [ ] Option 3 — 현상 유지 (ADR-0211 target 그대로)
- [ ] Option 4 — ADR-0211 파일 수정 (금지 — immutable)

### 결정된 내용

1. **새 baseline 선언** — 지금 달성된 곡선 (아래 「새 기준선」) 이 앞으로의
   비교 기준이다.
2. **ADR-0211 의 per-grade win-rate target 은 superseded** — 수치는
   `g2 88.8 / g3 73.0 / g4 47.4 / g5 42.4` 이며 더 이상 유효하지 않다.
3. **ADR-0211 의 메커니즘은 그대로 유효하다** — 아래 「superseded 아닌 것」 참조.
4. **drift policy 를 세운다** — 아래 「drift policy」 참조.
5. **ADR-0211 파일은 수정하지 않았다.** 대체 관계는 이 ADR 과
   `decisions/README.md` 인덱스에 기록했다 (README 의 0211 행 Status 칸 →
   `**Superseded by ADR-0229**`).
6. **calibration 배열의 값은 미변경이다** — 두 배열 모두 byte-identical.

## 새 기준선 (The New Baseline)

### Opening deck — 여기가 기준선이다

`npm run balance` (opening deck, 100 runs/mission) — **2026-10-29 실측.**

| grade | **새 baseline (per-grade target)** | ADR-0211 target (superseded) | residual |
| --- | --- | --- | --- |
| **g1** | **100.0%** | 100.0% | — |
| **g2** | **88.6%** | 88.8% | — |
| **g3** | **73.1%** | 73.0% | — |
| **g4** | **39.3%** | 47.4% | — |
| **g5** | **35.7%** | 42.4% | — |
| **g6** | **0.0%** | 0.0% | — |

**단조 비증가 (monotonic non-increasing) 성립:**
`100.0 ≥ 88.6 ≥ 73.1 ≥ 39.3 ≥ 35.7 ≥ 0.0` ✓

**이 여섯 개의 수가 baseline 이다.** 앞으로의 모든 비교는 이 수치를
기준으로 한다.

### PPL (developed) deck — 기준선이지만 **target 이 아니다**

`npm run balance -- --deck ppl` (100 runs/mission) — **2026-10-29 실측.**

| grade | **PPL baseline (reference)** | ADR-0228 대비 |
| --- | --- | --- |
| g1 | 100.0% | 0.0pp |
| g2 | 77.9% | 0.0pp |
| g3 | 99.6% | −0.4pp |
| g4 | 84.8% | −4.2pp |
| g5 | 44.4% | 0.0pp |
| g6 | 28.3% | −3.0pp |

**PPL 곡선은 reference 이다 — target 이 아니다.** (drift policy §C 참조.)
PPL 곡선은 **비단조**다 (g2 77.9 < g3 99.6) — 이것은 **deck artifact** 다.
`deckForGrade` 가 g2 에서는 tier≤2 card 만 tiering 하고 g3 에서 tier-3
payload/exploit/goliath 로 점프하기 때문이다. 두 deck 의 곡선은 하나의 ICE
knob 아래 함께 움직이므로 이것을 고치려면 deck 정의를 바꿔야 한다
(mechanics change — 범위 밖).

## superseded 인 것 / 아닌 것

### ❌ superseded — ADR-0211 의 per-grade win-rate target

- opening deck 의 per-grade 목표 수치: `g2 88.8 / g3 73.0 / g4 47.4 / g5 42.4`.
- "±3pp 이내면 안偏离한다" 는 **target 잔차** 기준의 근거. (ADR-0229 의
  drift policy 가 그 자리를 대체한다.)
- ADR-0211 target 을 인용하는 **다른 문서** 가 있다면 함께 갱신해야 한다.

### ✅ 유효 — ADR-0211 의 메커니즘 (이건 그대로 살아있다)

**ADR-0211 의 수는superseded 지만, 메커니즘은 유효하다.** 아래는 전부
그대로 존속한다.

1. **HP cap 메커닉** — `iceHpForGrade` 의 `min(natural HP, cap)`. cap 은
   natural HP **위**에 있으면 no-op 이므로, cap 이 **살아 있는지**가
   메커닉의 존재 여부다. 현재 max cap 은 165 (g4/g5/g6) 이고
   `ENCOUNTER_HP_BY_GRADE` 는 **단조 비감소**다.
2. **damage bonus 곡선** — `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`. auto-attack
   (`tier * 3 + armor`) 에만 적용되고 **스킬 피해에는 적용되지 않는다**는
   비대칭, boss phase 가 이 bonus 를 건너뛴다는 규칙, grade 별
   `+50 / +130 / +8 / 0 / 0 / −20` 값 — **전부 유효하다.**
3. **grade-driven encounter scaling** — `ENCOUNTER_ICE_BY_GRADE` 와
   `encounterIceIdForGrade`, seed 기반 결정적 rotation, slot 0 의 immutable
   성질 — **전부 유효하다.**
4. **climax 는 opening deck 에 이길 수 없다**는 설계 의도 — g6 0.0% 가
   baseline 이므로 **여전히 성립한다** (아래 drift policy §B).

## drift policy (drift 가 다시 churn 이 되지 않게 하는 규칙)

이 절이 이 ADR 의 실체다. **baseline 은 "목표" 가 아니라 "비교 기준" 이므로,
무엇을 언제 어떻게 지키는지** 가 규칙으로 명시되어야 한다.

### §A — 변화 알림 규칙 (no silent drift)

> **A1.** 어떤 변경이 **opening deck 의 어떤 grade든 baseline 대비 ±3pp 를
> 초과**로 움직이면, 그 변경은 **둘 중 하나**를 해야 한다:
> **(i) 되돌린다** — calibration 배열 / band / combat path 를 조정해 그 grade 를
> ±3pp 창 안에 다시 넣는다, **또는**
> **(ii) 명시적으로 re-baseline 한다** — 그 변경 자신의 ADR 이 새 baseline
> 을 선언하고, 이동한 grade 의 before/after 실측 표를 포함한다.
>
> **A2.** ±3pp 창 안의 이동 (1pp, 2pp 등) 은 **보고만 하면 된다** —
> re-baseline 은 필요 없고, drift 는 ADR 의 balance 표에 before/after 로
> 적는다. (음성 이동은 무시하지 않는다. **기록만** 한다.)
>
> **A3.** §A 의 판정은 **항상 `npm run balance` (opening deck, 100
> runs/mission) 실측**으로 한다. 추론이 아니라 측정이다. 측정 rerun 은
> deterministic 이다 (seed 고정) — 두 번 실행해 같은 값이 나오지 않으면
> 그것 자체가 조사 대상이다.
>
> **A4.** **calibration 배열의 값 자체를 바꾸는 변경** (HP cap, dmg bonus,
> band slot) 은 §A1 과 별개로 **그 변경 ADR 의 Implementation Status 에
> before/after 밸런스 표를 반드시 포함**한다. 배열을 바꾼 변경은
> re-baseline 여부와 무관하게 측정 결과를 남긴다.

### §B — 불변식 (hard invariants — 이건 타협 대상이 아니다)

> **B1.** **opening 곡선은 단조 비증가 (monotonic non-increasing) 이어야
> 한다:** `g1 ≥ g2 ≥ g3 ≥ g4 ≥ g5 ≥ g6`. **어떤 변경도 이걸 깨면 안 된다.**
> 깨면 그 변경은 즉시 되돌려야 한다 — re-baseline 으로도 **이 불변식은
> 재기준화할 수 없다** (baseline 은 반드시 이 shape 다).
>
> **B2.** **g6 은 baseline 근처 (0.0%) 에 머문다.** opening deck 가 climax 를
> 이길 수 없다는 것 (ADR-0211 의 핵심 설계 의도) 이 깨지면 안 된다. 허용
> 범위는 **0.0% ~ 5.0%** 다 — 이 범위를 벗어나면 §A1 적용.
>
> **B3.** **`ENCOUNTER_HP_BY_GRADE` 는 단조 비감소 (monotonic
> non-decreasing) 이어야 한다:** `c1 ≤ c2 ≤ ... ≤ c6`. 이건 이미
> `web/tests/ice_scaling.test.ts` 의
> `keeps HP monotonic non-decreasing across grades for every band id` 가
> assert 한다 — **이 test 는 계속 살아있어야 하고** (§A1 의 (i) "되돌린다"
> 경로가 이 상한 때문에 불가능해질 수 있다: `c3 ≤ c4`).
>
> **B4.** **HP cap 의 최대값은 165 이다.** cap 이 natural HP 위로 올라가면
> ADR-0211 의 cap 메커닉이 **no-op 으로 소멸한다** — 그 상태는 허용되지
> 않는다. (ADR-0225 가 실제로 cap 560 시도를 기각했다: PPL g5 44.4% →
> 100.0%, +55.6pp.)
>
> **B5.** **두 레버는 계단 함수다 — 그리고 그 cliff 는 알고 있다.**
> `floor((tier * 3 + armor) * (1 + pct / 100))` 이므로 도달 가능한 값이
> 이산적이다. grade 의 승률을 fine-tune 하려고 "조금만" 바꾸는 시도는
> **cliff 를 넘겨서 ±3pp 창을 통째로 건너뛸 수 있다.** §A1 의 (i) 경로가
> 불가능하면, 그 사실 자체를 ADR 에 기록하고 (ii) re-baseline 로 간다.

### §C — PPL 곡선은 reference 다

> **C1.** **PPL 곡선은 target 이 아니다.** ADR-0225 가 요구한 "PPL g5 ≤ 45%"
> 같은 조건은 **superseded** 다. PPL 수치는 **기준선(reference)** 으로만
> 쓰인다.
>
> **C2.** **PPL 곡선의 이동은 반드시 그 변경의 ADR 에 명시되어야 한다.**
> (opening 곡선이 ±3pp 창 안에 있더라도) PPL 의 어떤 grade 든 5pp 이상
> 움직였다면, 그 변경 ADR 은 **PPL before/after 표** 를 포함해야 한다.
> (PPL 은 developed deck 의 성격을 반영하므로 여기가 무음으로 움직이면
> 플레이 경험이 조용히 바뀐다.)
>
> **C3.** **PPL 이 비단조인 것은 허용된다** (g2 77.9 < g3 99.6). 이것은
> deck artifact 다 (§ 새 기준선 참조). **PPL 단조성을 목표로 삼지 마라** —
> 그것을 목표로 삼으면 opening 곡선까지 함께 움직인다.

### §D — 이 policy 자체의 변경

> **D1.** 위 규칙 (§A/§B/§C) 을 바꾸려면 **새 ADR** 이 필요하다. §B 의
> 불변식은 **이 ADR 로도 완화할 수 없다** — 그것은 B1 (단조성) 와 B3
> (HP 단조성) 때문이고, 이 둘은 re-baseline 으로도 재기준화되지 않는다.

### 한눈에 보기

| 규칙 | 내용 | 강도 |
| --- | --- | --- |
| **A1** | opening grade 가 baseline 대비 ±3pp 초과 → 되돌리거나 자기 ADR 에서 re-baseline | 강제 |
| **A2** | ±3pp 이내 이동 → 보고만 (ADR 에 before/after) | 강제 |
| **A3** | 판정은 항상 `npm run balance` 실측 (추론 금지) | 강제 |
| **A4** | calibration 배열 변경은 §A1 과 별개로 밸런스 표 필수 | 강제 |
| **B1** | opening 곡선 단조 비증가 | **불변식** |
| **B2** | g6 ∈ [0.0%, 5.0%] | **불변식** |
| **B3** | `ENCOUNTER_HP_BY_GRADE` 단조 비감소 | **불변식** |
| **B4** | max HP cap ≤ 165 | **불변식** |
| **B5** | 레버는 step function — cliff 를 인식하고, 안 되면 re-baseline | 강제 |
| **C1** | PPL 은 reference, target 아님 | 강제 |
| **C2** | PPL 이동은 변경 ADR 에 명시 | 강제 |
| **C3** | PPL 비단조는 허용 — 목표로 삼지 말 것 | 강제 |
| **D1** | policy 변경은 새 ADR 필요 (§B 불변식은 불가) | 강제 |

## 결과 (Consequences)

### 긍정적 영향

- **churn 이 끝났다.** "이 기능을 넣었으니 curve 를 다시 맞추자" 가 더 이상
  기본 절차가 아니다.
- **기준선과 실측이 정확히 일치한다.** drift 를 발견하려면 **기존 수치를
  비교할 필요 없이** ADR-0229 의 표와 비교하면 된다.
- **ADR-0211 의 메커니즘은 손상되지 않았다.** cap, dmg bonus 곡선,
  grade-driven encounter scaling — 전부 그대로.
- **dead combat path 수정은 손상되지 않았다.** ADR-0224/0226/0227/0228 의
  기능 작업이 되돌아가지 않는다.
- **다음 churn 을 막는 규칙이 생겼다.** §A1 (무음 drift 금지) +
  §B (불변식) + §C (PPL 명시).

### 부정적 영향 / 수용한 비용

- **"목표" 와 "실측" 의 거리가 사라졌다.** baseline 은 "되어야 하는 수치" 가
  아니라 "비교 기준" 다. 그래서 §A1 의 "되돌리기" 경로가 필요하다 — 그렇지
  않으면 baseline 은 현재 곡선의 단순 복제가 되어 무의미해진다.
- **ADR-0211 의 네 숫자 (88.8 / 73.0 / 47.4 / 42.4) 는 이제 죽은 수치다.**
  그것을 인용하는 문서가 있으면 갱신해야 한다 (이 ADR 작성 시점에
  `web/tests/` 안에서 그 수치를 assert 하는 test 는 **없었다** — 실측 확인).
- **per-ICE calibration knob 은 여전히 없다.** grade 별 band identity 를
  바꿔야 하는 시점이 오면 그때 별도 ADR 로 다룬다.

### 후속 항목 (이번 ADR 범위 밖)

1. **per-ICE calibration knob** — Option 2. 필요해질 때까지 미룬다.
2. **PPL 곡선의 비단조** — deck 정의(`deckForGrade`) 문제다. mechanics
   change 이므로 별도 ADR 대상.
3. **ADR-0228 의 후속 항목 1 (g4/g5 재캘리브레이션)** — **이 ADR 로
   닫힌다.** g4/g5 의 현재 곡선 (39.3% / 35.7%) 이 §A1 (i) 경로가
   **불가능하다**는 실측 frontier 때문에 (§B5: 계단 함수 + cliff) 재보정이
   아니라 re-baseline 이 정답이었다. §B2 (g6 0.0%) 과 §B1 (단조성) 은
   유지된다.
4. **ADR-0227 의 잔여 항목** — 모호한 스킬 분류 10종, 잔여 inert 효과
   (`detect`/`silence`/`slow`/`stun`/`debuff`), catalog gap (tier-1 피해
   스킬 없음 / 스킬을 carry 하는 `stealth` ICE 없음 / `support` 는 9 종).
   이 ADR 의 범위 밖이며 **곡선과 무관하다.**
5. **ADR-0228 의 후속 항목 2/3** — `shouldTargetAlly` (per-target 스킬
   해석), `getAlarmMultiplier` (trace alarm accrual loop + 스킬을 carry 하는
   `stealth` ICE). **곡선을 움직일 수 있는 변경**이므로, 구현 시점에
   §A1 을 반드시 적용한다.

### 관계 — immutable 규칙 준수

**ADR-0211 은 Accepted 이며 immutable 하다 (`AGENTS.md` §6).**
따라서 **supersession 은 이 ADR 과 인덱스에 기록한다.** ADR-0211 파일은
**한 글자도 수정하지 않았다.** `decisions/README.md` 의 0211 행 Status 칸을
`**Superseded by ADR-0229**` 로 바꾼 것은 **인덱스의 상태 표기** 갱신이지
ADR 본문 수정이 아니다. (README 의 상태 범례가 이미
"**Superseded by ADR-XXXX**: 새 결정으로 대체됨" 을 명시한다.)

ADR-0211 / 0212 / 0216 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 /
0228 도 Accepted 이며 immutable 하므로 **하나도 수정하지 않았다.**

## Implementation Status (2026-10-29)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:

**신규 파일**

- `web/../docs/wiki/decisions/0229-grade-curve-rebaseline.md` — **이 ADR.**
  새 baseline (opening 6 grade + PPL 6 grade) + drift policy §A/§B/§C/§D
  + supersession 기록.

**수정된 파일**

- `docs/wiki/decisions/README.md` — **2곳만**:
  (a) 0211 행의 Status 칸 → `**Superseded by ADR-0229**`.
  (b) 0229 행 신규 추가 (0228 행 다음, 6-컬럼 동일 format).
  **다른 행은 하나도 바뀌지 않았다.**
- `web/src/core/ice_scaling.ts` — **docstring 만** 갱신 (module header +
  `ENCOUNTER_HP_BY_GRADE` + `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`).
  두 calibration 배열의 **리터럴은 byte-identical** — `git diff` 로 실측 확인.

**미변경 (실측)**

- `web/src/core/ice_scaling.ts` — `ENCOUNTER_HP_BY_GRADE` =
  `[75, 86, 141, 165, 165, 165]`, `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` =
  `[50, 130, 8, 0, 0, -20]`, `ENCOUNTER_ICE_BY_GRADE` — **전부 미변경.**
- `web/src/data/ice_types.json` — 97 ICE row + `skill_defs` 88 entry **미변경.**
- `web/src/core/ice_ai.ts`, `web/src/core/ice_crit.ts`,
  `web/src/core/ice_skills.ts`, `web/src/core/state_actions_combat.ts`,
  `web/src/core/combat_engine.ts` — **미변경.**
- `web/tests/ice_scaling.test.ts` — **미변경** (assertion 약화·skip·삭제 0건).
- ADR-0211 / 0212 / 0216 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 /
  0228 — **미수정** (immutable).

**밸런스 (재측정 — 변경 없음 확인)**

`npm run balance` (opening deck, 100 runs/mission):

| grade | win-rate | baseline 일치 |
| --- | --- | --- |
| g1 | 100.0% | ✓ |
| g2 | 88.6% | ✓ |
| g3 | 73.1% | ✓ |
| g4 | 39.3% | ✓ |
| g5 | 35.7% | ✓ |
| g6 | 0.0% | ✓ |

`npm run balance -- --deck ppl` (100 runs/mission):

| grade | win-rate | baseline 일치 |
| --- | --- | --- |
| g1 | 100.0% | ✓ |
| g2 | 77.9% | ✓ |
| g3 | 99.6% | ✓ |
| g4 | 84.8% | ✓ |
| g5 | 44.4% | ✓ |
| g6 | 28.3% | ✓ |

**게이트**

- `npm test` — **0 failures.**
- `npx tsc --noEmit` — **0 errors.**
- `npx eslint src/core/ice_scaling.ts --ext ts` — **0 errors.**
- `python3 scripts/audit_vault.py` (workspace root) — **CLEAN.**

**Notes**:

- **이 ADR 은 behavior 를 바꾸지 않는다.** 두 calibration 배열의 리터럴이
  byte-identical 이므로 측정 결과는 그대로다 — 위 두 밸런스 표가 그 증거다.
- **test 를 약화·skip·삭제하지 않았다.** `web/tests/ice_scaling.test.ts` 는
  **한 줄도 수정하지 않았다.** `web/tests/` 전체에서 ADR-0211 의 target 수치
  (88.8 / 73.0 / 47.4 / 42.4) 를 assert 하는 test 는 **없었다** (실측
  grep) — `ice_scaling.test.ts` 의 ADR-0211 언급은 전부 **comment** 다
  (line 99, 186, 275: 메커니즘의 출처를 가리키는 주석). baseline 수치를
  assert 하는 새 test 는 이번 ADR 의 범위 밖이다 (값이 고정되면 그 test
  자체가 또 하나의 churn source 다 — §A1 의 (i) 경로를 막을 수 있으므로
  남겨둔다).
- **`Game/wet_run/log.md` 는 수정하지 않았다** (오케스트레이터 소유).
- **임시 파일을 남기지 않았다.**

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `docs/wiki/decisions/0229-grade-curve-rebaseline.md` — **신규** (이 ADR)
- `docs/wiki/decisions/README.md` — 0211 행 Status 칸 + 0229 행 신규
- `web/src/core/ice_scaling.ts` — docstring 3개 (module header + 두 상수)

### 이번 결정으로 변경되지 않은 항목

- `web/src/core/ice_scaling.ts` — 두 calibration 배열, `ENCOUNTER_ICE_BY_GRADE`,
  `iceHpForGrade`, `iceDmgBonusPctForGrade`, `encounterIceIdForGrade`,
  `clampGrade`, `missionGradeOf`, `missionSeedOf`
- `web/src/data/ice_types.json` — 97 ICE row + `skill_defs` 88 entry
- `web/src/core/ice_ai.ts`, `web/src/core/ice_crit.ts`,
  `web/src/core/ice_skills.ts`, `web/src/core/ice_combat_effect_apply.ts`,
  `web/src/core/state_actions_combat.ts`, `web/src/core/combat_engine.ts`
- `web/tests/` — **전체 미변경**
- `Game/wet_run/log.md` — 오케스트레이터 소유
- ADR-0211 / 0212 / 0216 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 /
  0228 — **미수정** (immutable)

## 관련 결정

- ADR-0211 (ICE grade scaling) — **이 ADR 이 그 per-grade win-rate target 을
  대체한다.** HP cap / damage bonus 곡선 / grade-driven encounter scaling
  메커니즘은 **그대로 유효하다.** **ADR-0211 은 수정하지 않았다** (immutable).
- ADR-0225 (Encounter band 재캘리브레이션) — g5 slot 교체 + cap 유지의 owner.
  그 §1 의 "±3pp 허용 오차" 기준은 **superseded** — ADR-0229 §A 가 대체한다.
  **ADR-0225 는 수정하지 않았다** (immutable).
- ADR-0228 (ICE 아키타입 동작 배선) — **이 ADR 이 그 후속 항목 4 를
  종결한다** ("ADR-0211 target 재기준화 vs per-ICE calibration knob").
  후속 항목 1 (g4/g5 재캘리브레이션) 도 §B5 의 실측 frontier 때문에
  re-baseline 으로 닫힌다. **ADR-0228 은 수정하지 않았다** (immutable).
- ADR-0224 / 0226 / 0227 — churn 을 만든 네 단계 중 앞의 셋. 그 기능은
  산다 — 되돌리지 않는다. **수정하지 않았다** (immutable).
- ADR-0195 (Accepted ADR Implementation Status Workflow) — 이 ADR 의
  Implementation Status 형식의 owner. **수정하지 않았다** (immutable).

## 변경 이력

- 2026-10-29: Draft 작성 (ADR-0228 후속 항목 4 — 재기준화 vs per-ICE knob)
- 2026-10-29: **Accepted (Option 1 — 한 번 re-baseline)** — 구현 완료·검증.
  새 baseline = 현 달성 곡선 (opening `100.0 / 88.6 / 73.1 / 39.3 / 35.7 /
  0.0`, PPL reference `100.0 / 77.9 / 99.6 / 84.8 / 44.4 / 28.3`).
  **drift policy §A/§B/§C/§D 세움.** ADR-0211 의 per-grade target 은
  superseded, 메커니즘은 유효. **calibration 배열의 값은 미변경**
  (byte-identical) — 이 ADR 은 behavior 를 바꾸지 않는다.
  기존 assertion 은 하나도 약화·skip·삭제하지 않았다
  (`web/tests/` 전체 미변경).
