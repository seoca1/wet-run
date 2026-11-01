# ADR-0244: 시간 게이트 아군 `Dixie` — 유휴 시계 진행이 난이도 곡선을 뒤집는다

**상태**: Accepted (옵션 2, N=2; 옵션 3 제외)
**날짜**: 2026-11-01
**결정자**: 프로젝트 오너 (2026-11-01 구현 요청)
**우선순위**: P2 (The Flatline — 밸런스 정확성. **ADR-0240 후속**, ADR-0229 §A1 접점)
**관련**: [ADR-0240 — 유휴 압력 + 알람 누적 루프](./0240-idle-pressure-and-alarm-loop.md) · [ADR-0229 — Grade 난이도 곡선 재기준화](./0229-grade-curve-rebaseline.md) · [ADR-0239 — VFX spawn 의 RNG 결합 해소](./0239-vfx-spawn-rng-decoupling.md) · [ADR-0148 — Combat Depth Expansion (companion skills)](./0148-combat-depth-expansion.md) · [ADR-0003 — 전투 시스템 (RT-MS)](./0003-combat-system.md)

> **이 ADR 은 ADR-0240 구현 중 발견한 결함을 기록한다.** ADR-0240 자체의 결정은 유효하며
> 구현·검증을 마쳤다 (`9e24f45`). 이 문서는 그 측정 과정에서 드러난 **별개의 문제** —
> 아군 `Dixie` 의 공격이 벽시계에 게이트되어 있다 — 를 다룬다.
>
> **옵션 2 구현 완료.** N=2로 기존 2000ms/턴 기준선을 보존했다. 옵션 3은 채택하지
> 않았으며 하네스 cadence는 불변이다. 측정·열린 질문 처리는 아래 Implementation Status가
> 현행 기록이다. 아래 컨텍스트의 시계 게이트와 산술은 수정 전 진단이다.

## 컨텍스트 (Context)

### 문제 — 하네스 시계를 조금만 바꾸면 곡선이 뒤집힌다

ADR-0240 의 §A1 측정 중, `balance_sim.ts` 의 유휴 단계를 켜면 (입력 없이 시계만 진행)
**승률이 오른다**는 것을 발견했다. 이는 "유휴를 처벌한다" 는 설계 의도와 반대다.

하네스 유휴 루프 (`web/scripts/balance_sim.ts:145-152`) 는
`clock = idleSinceMs + 10_000` 부터 10초 간격으로만 tick 하므로, `--idle-ms` < 10초는
**시계만 진행시키고 알람은 절대 올리지 않는다**. 이 분리로 cadence 효과와 알람 효과를
독립 측정했다 (opening deck, 100 runs/mission, 53 missions, seeds 1-100).

| `--idle-ms` | 시계/턴 | 알람 | g1 | g2 | g3 | g4 | g5 | g6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 (기준선) | 2000ms | 0 | 100.0 | 88.3 | 70.5 | 39.5 | 36.2 | 0.0 |
| 1000 | 3000ms | **0** | 100.0 | **100.0** | **98.9** | **64.0** | **44.1** | **1.0** |
| 3000 | 5000ms | 0 | 100.0 | 100.0 | 98.9 | 64.0 | 44.1 | 1.0 |
| 6000 | 8000ms | 0 | 100.0 | 100.0 | 98.9 | 64.0 | 44.1 | 1.0 |
| 8000 | 10000ms | 0 | 100.0 | 100.0 | 98.9 | 64.0 | 44.1 | 1.0 |
| 10000 | 12000ms | 최대 5 | 100.0 | 100.0 | 93.4 | 55.3 | 40.4 | 0.0 |

### 원인 — 확정: 아군 `Dixie` 의 3초 시간 게이트

`web/src/core/combat/state_actions_combat.ts:375-382` — `processEnemyTurns` 안에서
플레이어 아군 `Dixie` 가 **ICE(적)에게** 피해를 준다:

```js
if (currentMs - state.dixieLastAttackMs >= DIXIE_ATTACK_INTERVAL_MS) {          // 3000
  const dixieDmg = DIXIE_BASE_DAMAGE + state.playerCombo * DIXIE_SYNERGY_BONUS; // 8 + combo*3
```

`first_contact` (g3, seed 1) 턴별 산술이 **정확히 일치**한다 (프로그램 자체 피해 10 / 10 / 28 / 5):

| turn | Dixie 간격 | idle=0 (2000ms/턴) | idle=1000 (3000ms/턴) |
| --- | --- | --- | --- |
| t0 | 첫 턴 | 10 + Dixie(combo 1 → 11) = **21** | 동일 **21** |
| t1 | 2000 vs 3000 | **10** (2000 < 3000 → 불발) | 10 + Dixie(combo 2 → 14) = **24** |
| t2 | 4000 | 발동 **28** | 발동 **28** |
| t3 | 2000 vs 3000 | **5** (불발) | 5 + Dixie(combo 4 → 20) = **25** |

이것이 관측을 **전부** 설명한다:

1. **임계값이 2000 ↔ 3000 사이** — `>= 3000` 게이트. 기준선(정확히 2000ms/턴)에서는 Dixie 가
   **격턴**만 발동한다.
2. **포화** — 간격이 3000 을 넘으면 매 턴 발동 → 3000 · 5000 · 8000 · 10000 이 byte-identical.
3. **RNG 무죄** — Dixie 는 `Math.random` 을 쓰지 않는다. 난수 값 시퀀스가 두 시나리오에서
   byte-identical 한 이유다.
4. **플레이어 HP 불변** — Dixie 는 적을 때리지, 플레이어를 때리지 않는다.
5. **턴 수 감소** — Dixie 피해가 적을 더 빨리 죽인다.
6. **알람은 원인이 아니고 오히려 되돌린다** — `--idle-ms 10000`(알람 최대 5)은 알람이 없을
   때(8000)보다 수치를 낮춘다 (g3 98.9 → 93.4, g4 64.0 → 55.3).

### 왜 이것이 중요한가

- **하네스 기준선이 실제 플레이를 대표하지 않는다.** 사람의 입력 간격은 대개 3초 이상이므로
  실제 플레이에서는 Dixie 가 **매 턴** 발동한다. 기준선(2000ms/턴)은 Dixie 가 **격턴**만
  발동하는 곡선이다 — 즉 **현 곡선은 실제보다 어렵다**.
- **시간 게이트 아군은 "느린 플레이 = 유리" 를 만든다.** Dixie 피해가 `playerCombo` 에
  비례하므로 (combo 를 쌓을수록 커짐) 느리게 플레이할수록 더 강해진다. 유휴 압력 (P7)
  설계와 정면 충돌한다.
- **하네스 기준선이 게이트 경계에 걸쳐 있다.** 기준선은 정확히 `AUTO_ATTACK_INTERVAL_MS`
  (2000ms) 만큼만 시계를 진행시킨다 — Dixie 임계(3000) 바로 아래다. 따라서 이후 **모든
  시간 관련 밸런스 측정이 경계값 위에 서 있다.**
- **실시간 요소의 의도 범위가 불명하다.** ADR-0003 (RT-MS) 은 실시간 자동 공격을 포함하므로
  *일부* 시간 의존은 의도일 수 있다. Dixie 의 3초 게이트가 그중 무엇인지 확인되지 않았다.

## 고려한 옵션

| # | 옵션 | 내용 | 비용 |
| --- | --- | --- | --- |
| 1 | **현상 유지 + 문서화** | 기록만 하고 코드는 그대로 | 0 (코드) / 기준선이 경계에 남음 |
| 2 | **`Dixie` 를 턴 기반으로** | 시간 게이트를 턴 카운트로 바꾼다 (예: N 플레이어 턴마다 발동) | 게임플레이 변경 → **§A1 재기준화 필수** |
| 3 | **하네스 cadence 를 실제 입력 속도로** | 측정 시계를 2000ms 대신 현실적 값 (예: 4000-5000ms) 으로 | 측정 도구 변경 → 기존 기준선 재측정 |
| 4 | ~~실제 게임 영역 확인~~ | **완료** — 사람 cadence 는 대개 ≥3초 → 실제 플레이는 Dixie 매 턴 발동 | — |

## 추천 (Recommendation)

**작성 당시 권고: 2 + 3. 최종 오너 결정: 2만 채택, N=2, 3은 범위 제외.**

1. **2 — `Dixie` 를 턴 기반으로.** 예: `매 N 플레이어 턴마다 발동` (또는 `매 N 적 턴마다`).
   그러면 "언제 입력했는가" 가 Dixie 기여를 바꾸지 않는다 — RT-MS 라면 결과는 "몇 턴을
   썼는가" 에 달려야 하고 "각 입력 사이에 몇 ms 가 흘렀는가" 에 달리면 안 된다.
   `DIXIE_ATTACK_INTERVAL_MS` 는 export 되어 설계 정합 테스트가 참조하므로 함께 갱신한다.
2. **3 — 하네스 cadence 정정.** 기준선이 게이트 경계 바로 아래(2000ms)에 있는 것은
   우연이며 측정을 취약하게 만든다. 실제 입력 속도에 맞춘 cadence 로 옮긴다.
3. **1 은 채택하지 말 것** — 기준선이 경계에 남으면 이후 시간 관련 측정이 신뢰를 잃는다.
4. **N 의 값과 cadence 의 값은 이 ADR 이 정하지 않는다** — 구현 시 실측과 함께 정해 기록한다
   (ADR-0240 이 튜닝 수치에 대해 취한 방식과 동일).

## 수락 증거 (Acceptance evidence)

- **비교 기준선**: ADR-0239 §재기준화 결과 (opening `100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0`,
  PPL `100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7`).
- **판정 (핵심 회귀)**: 옵션 2 를 택하면 `--idle-ms 0` 과 `--idle-ms 1000` 의 곡선이 **같아져야
  한다** — 현재 g2 +11.7pp · g3 +28.4pp · g4 +24.5pp 차이가 제거되어야 한다.
- **측정**: `cd web && npm run balance` + `npm run balance -- --deck ppl`, 6 grade 전부,
  `--idle-ms 0 / 1000 / 10000`. ADR-0229 §A1/§A2/§B1/§B2/§C2 를 적용한다.
- **테스트**: **시계를 바꿔도 결과가 바뀌지 않는다**는 단위 테스트 (동일 상태 + 다른 `Date.now()`
  → 동일 결과). 이 테스트는 **지금은 실패해야** 한다 (결함의 pin). 옵션 2 구현 후 통과해야 한다.
- **설계 정합**: `DIXIE_*` 상수를 참조하는 설계 정합 테스트 (`state_actions_combat.ts:40` 주석이
  "design-conformance suite" 를 언급) 를 함께 갱신한다.

## Open questions

- **(a) 발동 규칙** — 턴 기반으로 바꾼다면 규칙은? 매 N 플레이어 턴 / 매 N 적 턴 / combo 임계
  도달 시? Dixie 피해가 `playerCombo` 에 비례하므로 combo 규칙과의 상호작용을 정해야 한다.
- **(b) 실제 cadence 분포** — 사람 입력 간격의 실제 분포 (중앙값·분산). 옵션 3 의 cadence 값
  근거. 원하면 실제 플레이 계측 (telemetry, ADR-0184) 으로 확인 가능.
- **(c) 의도된 것인가** — Dixie 의 3초 게이트가 의도인가? ADR-0148 (companion skills) 이
  실시간 동반자 공격을 의도했다면 옵션 1 도 가능하다. 다만 "느린 플레이가 유리" 는 별도로
  판단해야 한다.
- **(d) 기준선의 지위** — 옵션 2 로 재기준화하면 ADR-0239 의 새 기준선이 다시 superseded 된다.
  ADR-0229 의 "재기준화는 명시적 ADR 로만" 원칙을 따른다.
- **(e) 다른 시간 게이트** — 같은 패턴이 다른 곳에도 있는가? `counterWindowOpenMs` 는 쓰기만
  되고 읽히지 않는 **죽은 필드**로 확인됐다. 나머지 `Date.now()` 비교는
  `state_actions_combat.ts:144` (`AUTO_ATTACK_INTERVAL_MS` 적 턴 게이트) 하나뿐이며, 이는
  적 턴을 *발동*시키는 게이트라 Dixie 와 성격이 다르다 (기준선 2000ms 에서도 매 턴 발동).

## 결과 (Consequences)

**최종 결정**: 옵션 2, N=2. 다음 항목은 작성 당시 예상이며, 재기준화 예상은
실측으로 기각됐다: no-idle 양 덱 전 grade 0.0pp, ADR-0239 기준선은 그대로 유효하다.

### 결정이 확정하게 될 것 (권고 채택 시)

- **Dixie 기여가 입력 속도와 무관해진다** → "언제 입력했는가" 가 곡선을 바꾸지 않는다.
- **하네스 기준선이 게이트 경계에서 벗어난다** → 이후 시간 관련 측정이 신뢰를 얻는다.
- **실제 플레이와 측정이 정합한다** → 현 곡선은 실제보다 어렵다는 왜곡이 해소된다.
- **한 번 더 재기준화된다** (ADR-0239 → 이 ADR).

### 긍정적 영향

- ADR-0240 의 "지속 유휴가 이득" 역전이 사라진다 (알람이 원인이 아니므로).
- 유휴 압력 (P7) 의 실제 효과가 처음으로 **알람 효과만** 측정 가능해진다.
- "느린 플레이 = 유리" 라는 설계 모순이 제거된다.

### 부정적 영향 / 수용한 비용

- **또 한 번의 곡선 이동** — ADR-0239 재기준화 직후이므로 이중 재기준화 부담이 있다.
- **Dixie 의 체감이 바뀐다** — 실시간 동반자 느낌이 턴 기반으로 바뀌면 전투 리듬이 달라진다
  (ADR-0003 RT-MS 와의 정합 재확인 필요).
- **cadence 값 선택의 자의성** — 옵션 3 의 값은 실제 분포 (b) 없이는 근사다.

## 영향 받는 항목

### 구현 시 변경될 항목 (예정)

- `web/src/core/combat/state_actions_combat.ts` — Dixie 게이트와 `DIXIE_*` 상수
- `web/scripts/balance_sim.ts` — cadence (옵션 3) + 시간 불변성 회귀 테스트
- `web/tests/` — 신규 시간 불변성 테스트, 설계 정합 테스트 갱신
- `docs/wiki/decisions/README.md`, `log.md`

### 변경되지 않는 항목

- ADR-0240 의 결정·구현·수락 증거 (유효하다)
- ADR-0229 / 0239 본문 (immutable; 재기준화는 이 ADR 로 기록)
- `core/status.ts` — ADR-0239 (b) 로 게임플레이 확정, 이 ADR 범위 밖

## Implementation Status (2026-11-01)

**Status**: ✅ Implemented — 옵션 2, **N=2**. 재기준화 없음, 옵션 3 미적용.

**Evidence**:
- `web/src/core/combat/state_actions_combat.ts:44` — 단일 빈도 튜닝 상수
  `DIXIE_ATTACK_EVERY_N_PLAYER_TURNS = 2`, 피해 상수 8/3 불변.
- `web/src/core/combat/state_actions_combat.ts:71`, `:142` — 성공한 `use_program`마다
  카운트, N 도달 시 첫 생존 ICE에게 `8 + playerCombo × 3`, 공격 후 0으로 초기화.
  적의 2000ms gate **밖**에서 처리하므로 빠른 연속 입력도 플레이어 턴으로 센다.
  적 공격 → Dixie 순서와 defeat 판정은 유지한다.
- `web/src/core/types.ts:203` — `dixieLastAttackMs`는 미사용 legacy로 명시해 유지,
  새 `dixiePlayerTurnsSinceAttack` 필드 추가.
- `web/src/core/state/state.ts:124`, `:366` — 새 런/로드 모두 N−1로 초기화하여
  **첫 턴 발동, 이후 3·5·7번째**라는 기존 no-idle 위상을 보존한다.
- `web/tests/companion.test.ts:56` — 동일 상태/고정 RNG + Date.now 3000/4000 비교.
  수정 전 실제 실패(적 HP **45 vs 34**), 수정 후 통과. `:97`은 동일 시각의 연속
  5회 플레이에서 Dixie 피해 **11/0/17/0/23**과 counter **0/1/0/1/0** 검증.
  실패한 프로그램·선택·타겟 변경·idle tick은 턴을 세지 않는다.
- `web/tests/balance_sim.test.ts:34` — 두 덱 × 53 미션에서 idle 0/1000 결과 전체
  일치 회귀. 기존 ADR-0239 exact-baseline 테스트도 그대로 통과.
- `web/tests/save_load_roundtrip.test.ts:29` — 실제 storage save/load → matrix resume
  round-trip. **SaveSlot에는 기존 timestamp도 새 counter도 없다.** 기존 버전의
  슬롯을 그대로 읽고, 기존 전투 재시작 계약대로 counter=N−1, timestamp=0으로 복원.
  schema/version/migration 변경이 필요 없으며 새 필드를 saves에 요구하지 않는다.
- `web/tests/design_conformance.test.ts:151` — 기존 Dixie expected-failure 3건을
  현행 combat.md의 N=2/8/+3에 대한 정상 conformance 검사로 전환.
  9개 combat fixture의 예전 timestamp 억제를 counter=0으로 교체했으며 assertion은
  삭제·완화하지 않았다. VFX 구현 파일은 수정하지 않았다.
- `docs/design/systems/combat.md:106` — 현재 Web 규칙과 retired Python 기록을 구분.
- [실측 raw stdout 18개 표](./0244-implementation-evidence.md) — 3 N × 2 덱 × 3 idle.

**Notes**: N=2는 기존 하네스에서 격턴이던 Dixie만 시간 독립으로 만든다. N=1은
아래처럼 큰 난이도 이동을 일으키는 별도 balance/re-baseline 결정이므로 **출하하지 않는다**.
AUTO_ATTACK_INTERVAL_MS=2000, ALARM_TICK_INTERVAL_MS=10000, IDLE_ALARM_TUNING,
하네스 cadence, 피해 공식, status/VFX 구현, calibration과 금지 ADR는 모두 불변.

### 측정: N × 덱 × 유휴 (win-rate %, g1–g6)

각 행을 실제 CLI로 별도 실행했다. 53 missions / 97 ICE types / **100 runs/mission**,
seed 1–100, mission 수 4/16/11/10/9/3. N=2 → N=1 → N=3 측정 후 **2로 복원**.
명령은 `npm run balance -- --idle-ms {0,1000,10000}` 및 `--deck ppl` 추가.
입력 속도를 바꾸는 옵션 3이나 새 하네스 튜닝 플래그는 추가하지 않았다.

| N | Opening idle-ms | g1 | g2 | g3 | g4 | g5 | g6 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 (미채택) | 0 | 100.0 | 100.0 | 98.9 | 64.0 | 44.1 | 1.0 |
| 1 | 1000 | 100.0 | 100.0 | 98.9 | 64.0 | 44.1 | 1.0 |
| 1 | 10000 | 100.0 | 100.0 | 93.4 | 55.3 | 40.4 | 0.0 |
| **2 (채택)** | **0** | **100.0** | **88.3** | **70.5** | **39.5** | **36.2** | **0.0** |
| **2** | **1000** | **100.0** | **88.3** | **70.5** | **39.5** | **36.2** | **0.0** |
| 2 | 10000 | 100.0 | 88.3 | 48.4 | 7.4 | 11.7 | 0.0 |
| 3 (미채택) | 0 | 100.0 | 92.4 | 45.6 | 19.1 | 17.2 | 0.0 |
| 3 | 1000 | 100.0 | 92.4 | 45.6 | 19.1 | 17.2 | 0.0 |
| 3 | 10000 | 100.0 | 92.4 | 32.5 | 1.5 | 5.4 | 0.0 |

| N | PPL idle-ms | g1 | g2 | g3 | g4 | g5 | g6 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 (미채택) | 0 | 100.0 | 100.0 | 99.6 | 95.2 | 45.6 | 33.3 |
| 1 | 1000 | 100.0 | 100.0 | 99.6 | 95.2 | 45.6 | 33.3 |
| 1 | 10000 | 100.0 | 100.0 | 97.8 | 91.3 | 44.1 | 4.0 |
| **2 (채택)** | **0** | **100.0** | **79.1** | **98.9** | **83.0** | **44.4** | **24.7** |
| **2** | **1000** | **100.0** | **79.1** | **98.9** | **83.0** | **44.4** | **24.7** |
| 2 | 10000 | 100.0 | 79.1 | 94.2 | 77.7 | 44.1 | 0.0 |
| 3 (미채택) | 0 | 100.0 | 83.8 | 95.2 | 64.6 | 44.4 | 17.0 |
| 3 | 1000 | 100.0 | 83.8 | 95.2 | 64.6 | 44.4 | 17.0 |
| 3 | 10000 | 100.0 | 83.8 | 86.1 | 59.1 | 43.8 | 0.0 |

### 핵심 수락: idle 0 vs 1000 나란히 (N=2)

| Grade | Opening 0 | Opening 1000 | Δpp | PPL 0 | PPL 1000 | Δpp |
| --- | --- | --- | --- | --- | --- | --- |
| g1 | 100.0 | 100.0 | 0.0 | 100.0 | 100.0 | 0.0 |
| g2 | 88.3 | 88.3 | 0.0 | 79.1 | 79.1 | 0.0 |
| g3 | 70.5 | 70.5 | 0.0 | 98.9 | 98.9 | 0.0 |
| g4 | 39.5 | 39.5 | 0.0 | 83.0 | 83.0 | 0.0 |
| g5 | 36.2 | 36.2 | 0.0 | 44.4 | 44.4 | 0.0 |
| g6 | 0.0 | 0.0 | 0.0 | 24.7 | 24.7 | 0.0 |

**양 덱 모두 win-rate뿐 아니라 stalled / mean-turns / mean-HP-end / p5/p95도
모두 동일**하다 (raw stdout). N=1/3에서도 각각 idle 0/1000이 전 metric 동일하다.
10000은 알람을 실제로 올리므로 같아야 하는 조건이 아니며, 이제 유휴 이득이 아니라
압력이 관측된다. 아래 §B1 stress 한계는 당시 측정이며, 현재는 ADR-0240의
피해/레벨 5%→4% 후속 튜닝으로 해소됐다 (Dixie N=2 불변).

### ADR-0229 정책 판정 (ADR-0239 대비)

| 덱 / no-idle | g1 | g2 | g3 | g4 | g5 | g6 |
| --- | --- | --- | --- | --- | --- | --- |
| Opening before (0239) | 100.0 | 88.3 | 70.5 | 39.5 | 36.2 | 0.0 |
| Opening N=2 after | 100.0 | 88.3 | 70.5 | 39.5 | 36.2 | 0.0 |
| Opening N=2 Δpp | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Opening N=1 alternative | 100.0 | 100.0 | 98.9 | 64.0 | 44.1 | 1.0 |
| Opening N=1 Δpp | 0.0 | +11.7 | +28.4 | +24.5 | +7.9 | +1.0 |
| Opening N=3 Δpp | 0.0 | +4.1 | −24.9 | −20.4 | −19.0 | 0.0 |
| PPL before (0239) | 100.0 | 79.1 | 98.9 | 83.0 | 44.4 | 24.7 |
| PPL N=2 after | 100.0 | 79.1 | 98.9 | 83.0 | 44.4 | 24.7 |
| PPL N=2 Δpp | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| PPL N=1 alternative | 100.0 | 100.0 | 99.6 | 95.2 | 45.6 | 33.3 |
| PPL N=1 Δpp | 0.0 | +20.9 | +0.7 | +12.2 | +1.2 | +8.6 |
| PPL N=3 Δpp | 0.0 | +4.7 | −3.7 | −18.4 | 0.0 | −7.7 |

- **§A1/A2**: shipped N=2 no-idle 전 grade **0.0pp**. ±3pp 초과 없음, 보고만,
  **재기준화 없음**. N=1은 최대 **+28.4pp**, N=3은 최대 **−24.9pp**이므로
  둘 다 §A1의 되돌리기/명시적 re-baseline이 필요하다. 두 실험값 모두 복원했다.
- **§B1**: N=2 기본/1000 opening `100 ≥ 88.3 ≥ 70.5 ≥ 39.5 ≥ 36.2 ≥ 0`, PASS.
  N=1/3의 no-idle도 단조다. **단, sustained 10000의 N=2/3은 FAIL**:
  N=2 `g4 7.4 < g5 11.7`, N=3 `1.5 < 5.4`. N=1 stress는 단조다.
  이 표는 기본 곡선의 §B1 통과를 **모든 유휴 분포의 통과로 일반화하지 않는다**.
  stress 실패를 재기준화로 면책하지 않는다. 입력 조건을 달리한 alarm pressure의
   grade별 비대칭이 남았다. **후속 해소 (2026-11-01)**: ADR-0240 §Implementation
   Status의 성분 분리·grid로 피해/레벨만 5%→4% 변경, N=2 sustained opening
   **100.0 / 88.3 / 49.3 / 25.2 / 12.4 / 0.0**, §B1 PASS.
   양 덱 no-idle 기준선·idle 0=1000은 그대로다. 이 절의 기존 5% 표는 역사적 측정이다.
- **§B2**: opening g6은 모든 측정에서 0.0–1.0%, 허용 0–5% 이내.
- **§C2**: 양 덱 before/after와 대안 전체 공개. N=1 PPL g2 **+20.9pp**,
  g4 **+12.2pp**, g6 **+8.6pp**; N=3 g4 **−18.4pp**, g6 **−7.7pp**.
  shipped N=2 no-idle 전부 0.0pp. PPL 비단조는 §C3대로 허용한다.
- N=2 sustained 10000 vs no-idle drift: opening **0/0/−22.1/−32.1/−24.5/0pp**,
  PPL **0/0/−4.7/−5.3/−0.3/−24.7pp**. §A2 창 안이라는 주장은 하지 않는다.
  §A3 기본 CLI 조건은 보존했으며 stress 표는 새 baseline으로 선언하지 않는다.

### Open questions 처리

- **(a) RESOLVED**: 성공한 플레이어 프로그램 턴 기준, N=2, 첫 턴 발동. 적 턴/프레임/
  combo 임계 규칙은 아니다. combo는 기존 피해 공식에만 사용한다.
- **(b) OPEN / Deferred**: 실제 cadence telemetry는 수집하지 않았다. 옵션 3은 범위 밖.
- **(c) RESOLVED for this decision**: 오너가 실시간 gate 대신 플레이어 턴 gate를 선택.
  원래 3초가 의도였는지에 대한 역사적 근거는 추가로 주장하지 않는다.
- **(d) RESOLVED**: N=2 실측 0.0pp라 ADR-0239는 superseded 되지 않는다.
- **(e) UNCHANGED / out of scope**: 확정 진단의 적 auto-attack gate=2000ms와
  dead `counterWindowOpenMs`는 그대로. status/VFX 및 다른 시간 경로는 감사·수정하지 않았다.
- **별도 잔여 항목 해소**: 위 5% 튜닝의 10000ms §B1 실패는 ADR-0240 후속
  4% 튜닝으로 해결됐다. 이 gate 수정 당시에는 알람/grade retuning을 섞지 않았으며,
  후속 진단·raw 출력은 [ADR-0240 지속 유휴 증거](./0240-sustained-idle-evidence.md)에 분리했다.

### 검증 결과

- `npm run typecheck`: exit 0, **0 errors**.
- `npm run lint`: exit 0, **0 errors / 1 pre-existing warning** (`input/keyboard.ts:14`).
- `npm test`: **159 files / 3623 tests passed / 0 failures** (+6 tests).
  save round-trip/storage/property-save/압축 tests 포함. 기존 jsdom audio play/load notices만 존재.
- `npm run build`: exit 0, **118 modules**, Vite 5.4.21, 464ms.
- 지정한 IPv4 strictPort preview + `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195
  npx playwright test --ignore-snapshots --grep-invert demo-screenshots`:
  **76 passed / 4 skipped / 0 failed (4.7m)**, retries 비활성, preview 종료.
- LSP: TypeScript server 미설치, 과거 설치 거절 상태여서 **실행 불가**. 우회/설치 없음;
  compiler 통과를 LSP clean이라고 주장하지 않는다.
- 커밋·stage 없음. repo-wide format 없음 (편집한 7 TS 파일만 Prettier).

## 관련 결정

- ADR-0240 — 이 결함을 발견한 작업. 그 §Open questions (m) 과 증거 §부록이 원자료다.
- ADR-0148 — companion skills 의 원 결정. Dixie 가 여기서 왔을 가능성이 크다 (실시간 동반자).
- ADR-0229 — drift policy 와 "재기준화는 명시적 ADR 로만" 원칙.
- ADR-0239 — 현재 기준선의 보유자 (이 ADR 이 채택되면 supersede 된다).
- ADR-0003 — RT-MS. "실시간" 의 범위를 정의하므로 (c) 의 근거가 된다.

## 변경 이력

- 2026-11-01: **Accepted / ✅ Implemented (옵션 2만, N=2)** — 첫 턴 + 격턴 위상 보존,
  양 덱 no-idle 0.0pp, idle 0/1000 전 metric 수렴, 18개 raw 실측표, save 호환,
  red→green 회귀 및 typecheck/lint/3623 tests/build/76 E2E 검증. 옵션 3 제외.
  (a)/(c)/(d) 종결, (b)/(e) 유지. sustained idle §B1 실패는 별도 미해결로 명시.
- 2026-11-01: 작성 (Draft) — ADR-0240 구현 중 발견한 시계 의존 결함. **원인을 실측으로
  확정** (아군 `Dixie` 의 3초 게이트, 턴별 산술 일치). 옵션 4 (실제 게임 영역) 는 분석으로
  해소 — 사람 cadence 는 대개 ≥3초이므로 실제 플레이는 Dixie 매 턴 발동이며, 기준선은
  격턴 발동이라 실제보다 어렵다. 권고: 옵션 2 (턴 기반) + 옵션 3 (cadence 정정).
  구현 없음.
