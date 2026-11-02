# ADR-0255: 카드가 이름대로 동작한다 — 오프닝 5장의 실제 효과 배선

**상태**: Accepted
**날짜**: 2026-11-03
**결정자**: 오너 승인 (2026-11-02 "추천대로 해줘" — ①B 실제 효과 배선 + ②A 결정타 COST 0 유지)
**우선순위**: P1 (The Flatline — 스킬을 이해하고 고르는 것, The Build — 메커니즘)
**관련**: [ADR-0251 — 진실한 프로그램 어포던스 + 전투 무결성 규칙](./0251-truthful-program-affordance-and-combat-integrity-rules.md) · [ADR-0254 — 어포던스 진실성](./0254-affordance-truth-and-effect-honesty.md) · [ADR-0256 — 카드 효과 밸런스 재기준선](./0256-card-effects-balance-rebaseline.md) · [ADR-0229 — grade curve 재기준선](./0229-grade-curve-rebaseline.md) · [ADR-0239 — VFX RNG 결합 해소(기준선)](./0239-vfx-spawn-rng-decoupling.md)

> **이 ADR은 ADR-0251 규칙 5("화면이 약속하는 동작은 반드시 진실이어야 한다")를 카드에 적용한다.**
> ADR-0243(숫자키 1회 = 카드 1장 실행)은 변경하지 않는다.

## 컨텍스트 (Context)

ADR-0251이 손패를 **진실하게** 만들었지만(라벨이 실제 COST·타겟을 말함), 카드가 **무엇을 하는지**는 여전히 가짜였다.
웹 티어 리듀서는 모든 프로그램에 `baseDamage = program.tier * 5` 하나만 적용하고, 카탈로그의
설명문만 다른 효과를 약속했다.

| 카드 | tier | 설명문이 약속 | 실제 |
|---|---|---|---|
| Backdoor | 2 | "약한 피해지만 방어구를 뚫는다" | tier×5 피해, 방어구 관통 없음 |
| Barrier | 3 | "한 번의 큰 방어막" | tier×5 피해, 방어막 없음 |
| Boost | 2 | "동료가 3턴간 30% 더 강해진다" | tier×5 피해, 강화 없음 |
| Cloak | 2 | "3턴간 회피를 높인다" | tier×5 피해, 회피 없음 |
| Decoy | 2 | "미끼가 적의 시선을 돌린다" | tier×5 피해, 미끼 없음 |

오너 판정: "스킬 효과 즉시 인지는 미흡(→ #4)". 5종 손패가 전부 같은 일을 하는 상태였다.

## 고려한 옵션

### Option 1 — 이름을 지킨다 (라벨만 정직하게, 효과 미배선)
ADR-0254가 이미 채택한 상태. 게임의 핵심 약속("기술을 이해하고 고른다")은 여전히 비어 있다.

### Option 2 — 카드마다 다른 효과를 배선한다 (선택)

#### 이니셔티브 5개 — 기계는 이미 있는 것만 쓴다

| 카드 | 효과 | 쓰인 기존 기계 |
|---|---|---|
| **Backdoor** | 공격이 **ICE 방어구 2점**을 무시 | 피해 수식의 `defenderDefenseBonus` 스케일 |
| **Barrier** | **2점 흡수 풀**, 2턴 | `shield` 종류 상태효과(ICE 쪽에 이미 있음) + 플레이어 대상 reader 신설 |
| **Boost** | 플레이어 공격 **+2 피해**, 2턴 | `powered` 종류 상태효과(이미 있음) |
| **Cloak** | 받는 피해 **−15%**, 2턴 | `evasive` 종류 상태효과 신설(플레이어 전용) |
| **Decoy** | 다음 타격의 **50%** 를 미끼가 흡수, 1턴 | `evasive` 종류(수치만 다름) |

**신규 표면은 `evasive` 한 종류뿐**이다. `shield`·`powered`는 이미 존재했고, 플레이어 측
방어 계층(`player_mitigation.ts`)은 ICE→플레이어 피해 경로에 얹는 얇은 계층이다.
`role`·`damage` 같은 죽은 JSON 필드는 **읽지 않는다**(ADR-0251/Oracle 경고).

#### 왜 방어구는 "점"인가
ICE 방어력은 **flat 차감**이다(`dmg = max(0, dmg - armor)`, 최종 최소 1). 실측 방어력은
tier 1 평균 1.0 → tier 6 평균 10.5다. 그래서 **비율 관통은 의미가 없다** — 방어력 3이면
30%는 0.9점이라 바닥에 반올림되어 사라진다. **절대값(점)** 관통이 이 모델에 맞는다.

#### 왜 모든 카드가 피해를 주는가
오프닝 손패는 `loadDeck`가 id 정렬 앞 5개(backdoor/barrier/boost/cloak/decoy)를 고른다.
지원 카드가 피해를 0으로 주면 오프닝 손패의 공격 카드가 **1장**이 되어 플레이어가 싸울 수 없다.
따라서 이 손패 구성에서는 **피해 + 효과**가 유일하게 성립하는 형태다.
(손패를 큐레이션해 공격 카드를 늘리는 것은 별도 과제 — 아래 "남은 항목".)

#### 효과 지속시간은 왜 2턴인가
한 전투는 6~7턴이다. 3턴 효과는 전투의 절반을 덮어 너무 강하다. 2턴이 "한 사이클"의
길이로 실용적이다.

## 사용자 결정 (Decision)

[x] **Option 2** — 카드마다 다른 효과를 배선한다
[ ] Option 1
[ ] Option 3 (지원 카드가 피해를 0)

### 결정 ② — 결정타 COST

[x] **Option A** — 결정타는 COST 0을 유지한다. 리듀서를 바꾸면 밸런스 수치가 바뀌고,
밸런스는 오너 결정 사항이다(Jev 확신도 0.19 — 사실상 동률).
화면에는 "마지막 적을 쓰러뜨리는 카드는 COST 없음" 이라는 **규칙**을 알린다.

## 결과 (Consequences)

### 바뀐 것

- `web/src/core/combat/program_effects.ts` (신규) — 효과 명세의 **단일 진실 공급원**.
  라벨·설명문·리듀서가 전부 여기서 파생되어, 카드의 말이 동작과 어긋날 수 없다(규칙 5).
- `web/src/core/combat/player_mitigation.ts` (신규) — 플레이어 측 흡수 풀·회피.
- `web/src/core/combat/state_actions_programs.ts` — 관통 적용, 카드 효과 적용(상태 틱 **이후**).
- `web/src/core/combat/state_actions_combat.ts` — ICE→플레이어 피해 2곳에 방어 계층.
- `web/src/core/data_loaders.ts` — 설명문을 효과 명세에서 파생.
- `web/src/core/types.ts` · `web/src/renderer/vfx.ts` — `evasive` 종류와 글리프 `E`.
- `web/scripts/balance_sim.ts` — PPL 덱 선택이 효과 인식(같은 tier 안에서 공격 카드가 우선).

### 밸런스

재기준선은 [ADR-0256](./0256-card-effects-balance-rebaseline.md) 에서 명시 수용한다.

| 곡선 | 이전 | 이후 |
|---|---|---|
| opening | 100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0 | 100.0 / 100.0 / 97.5 / 53.4 / 44.1 / 0.3 |
| PPL | 100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7 | 100.0 / 100.0 / 99.3 / 84.1 / 44.4 / 27.3 |

## Implementation Status (2026-11-03)

**Status**: ✅ Implemented

**Evidence**:

- `web/tests/program_effects.test.ts` (신규, 7건) — 5개 효과의 동작과 "평범한 카드는 효과 없음"을 고정.
  관통은 방어력 5 → 3, 방어력 2 는 전부 관통됨(상한)도 확인.
- `web/tests/program_catalog_text.test.ts` — 설명문이 **기계에서 파생**됨을 고정(손으로 못 쓴다).
- `web/tests/balance_sim.test.ts` — 새 기준선을 고정(ADR-0256).
- vitest **179 files / 3956 tests passed** · typecheck 0 · eslint 0 errors · build PASS.
- 밸런스 — [balance-opening.txt](../../design/card-effects-2026-11-03/balance-opening.txt),
  [balance-ppl.txt](../../design/card-effects-2026-11-03/balance-ppl.txt).
- **효과 off 대조군** — 효과를 전부 끄면 곡선이 **기준선과 정확히 일치**(100.0/88.3/70.5/39.5/36.2/0.0)
  하므로, 곡선 이동은 오직 효과에서 온다(부수 변경은 밸런스 중립).

**Notes**:

- 오프닝 g2·g3 이 100% 로 오른 것이 최대 이동이다. 원인은 **오프닝 손패 5장 중 4장이 효과 카드**라는
  점이다 — 곡선 이동이 효과가 아니라 손패 구성에서 증폭된다. 손패를 큐레이션해 공격 카드를
  늘리면(예: 3공격+2지원) 이동이 줄 수 있다 — 아래 "남은 항목".
- 효과 수치는 `PROGRAM_EFFECTS` 한 표에 있다. 오너가 조정하면 그 표만 고치면 된다.

## 열린 질문

- **(a) 오프닝 손패 구성.** 5장 중 4장이 지원 카드다. 큐레이션(공격 3 + 지원 2)으로 바꾸면
  곡선 이동이 줄고 게임의 도입도 나아진다. 별도 결정.
- **(b) 나머지 25개 프로그램.** 카탈로그의 나머지는 여전히 평범한 공격이고 설계 의도는
  `plannedDescription` 에 남아 있다. 효과 배선은 카드마다 판단이 필요하다.
- **(c) 결정타 COST 규칙 안내.** 라벨/설명에 "마지막 적을 쓰러뜨리는 카드는 COST 없음" 을 넣는 위치 결정.

## 영향 받는 항목

- `web/src/core/combat/program_effects.ts` (신규) · `web/src/core/combat/player_mitigation.ts` (신규)
- `web/src/core/combat/state_actions_programs.ts` · `web/src/core/combat/state_actions_combat.ts`
- `web/src/core/data_loaders.ts` · `web/src/core/types.ts` · `web/src/renderer/vfx.ts`
- `web/scripts/balance_sim.ts` · `web/tests/` (신규 1 + 갱신 2)

## 관련 결정

- ADR-0251 (규칙 5) · ADR-0254 (표시 정합) · ADR-0256 (밸런스 재기준선) · ADR-0229 (재기준선 절차) ·
  ADR-0239 (기준선) · ADR-0243 (변경 금지)

## 변경 이력

- 2026-11-03: Draft 작성
- 2026-11-03: Accepted — 오너 승인(2026-11-02). 구현 완료.
