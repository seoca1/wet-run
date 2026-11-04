# ASCII 로그라이크 카드배틀: 자키 정체성 설계안

## 전제와 설계 원칙

현재 문제는 덱의 전투력이 사실상 `tier 합계 × 5`로 결정된다는 점이다. 따라서 이번 안에서는 먼저 세 시작 덱의 티어 합을 모두 **11**로 맞춘다.

- 세 덱 모두 5장
- 세 덱 모두 방어 카드 1장 이상
- 공격 피해의 유일한 경로는 여전히 `tier × 5`
- 새 난수, 애니메이션 대기, 턴 큐, 파티 시스템을 추가하지 않음
- 새로 추가하는 상태는 정수 카운터 또는 불리언뿐이며, 전부 상한이 있음
- 한 전투에서 동시에 유지할 수 있는 새 상태의 최대 수는 `intel_turns 3`, `virus_turns 2`, `rewind_active 1`이다

효과 카드가 서로 충돌할 때는 다음 순서로 계산한다.

1. `virus_armor_down`을 ICE 방어도에서 차감한다.
2. `exploit`이면 남은 방어도의 50%만 적용한다: `floor(armor * 0.5)`.
3. `scan`의 정보 효과가 켜져 있으면 방어도 1을 추가 차감한다.
4. 기존 `backdoor`의 `pierce 2`를 적용한다.
5. 최종 피해는 항상 `program.tier * 5`이다.

이 순서를 고정하면 어떤 카드 조합도 추가 피해 경로를 만들지 않는다.

---

## A. 먼저 구현할 효과 우선순위

### 1. `exploit` — 우선순위 1

- **정확한 메커니즘:** 해당 프로그램의 피해 계산에서 ICE 방어도의 50%만 적용한다.
- **수치:** `effective_armor = floor(current_armor * 0.5)`.
- **지속/스택:** 해당 카드의 이번 해결에만 적용. 스택 불가.
- **피해 제한:** 피해는 계속 `tier 3 × 5 = 15`; 방어도만 계산 방식이 달라진다.
- **의사코드:**

```ts
(player, ice, program) => {
  const armor = Math.max(0, ice.armor - ice.virus_armor_down);
  const effectiveArmor = program.id === "exploit" ? Math.floor(armor * 0.5) : armor;
  return resolveFixedDamage(program.tier * 5, effectiveArmor);
}
```

- **왜 정체성을 만드는가:** 티어가 높은 공격이 아니라, 방어도가 높은 ICE를 상대하는 **방어도 무시형 침투**를 만든다.

### 2. `scan` — 우선순위 2

- **정확한 메커니즘:** 사용 즉시 `intel_turns = 3`으로 설정한다. `intel_turns > 0`인 동안 플레이어 프로그램의 유효 방어도를 1 낮춘다.
- **수치:** 방어도 `-1`, 지속 `3턴`.
- **지속/스택:** 재사용 시 `intel_turns = 3`으로 갱신하며 누적하지 않는다. 최대 3.
- **피해 제한:** 추가 피해 없음.
- **의사코드:**

```ts
(player, ice, program) => {
  player.intel_turns = 3;
  const intelPierce = player.intel_turns > 0 ? 1 : 0;
  return resolveFixedDamage(program.tier * 5, Math.max(0, ice.armor - intelPierce));
}
```

실제 피해 계산 시에는 위 공통 순서에 따라 `scan`을 적용한다. 카드를 낸 턴에도 정보 효과가 적용된다.

- **왜 정체성을 만드는가:** 한 장의 강한 공격이 아니라, 먼저 정보를 확보하고 3턴 동안 모든 공격의 질을 바꾸는 **준비형 운용**을 만든다.

### 3. `rewind` — 우선순위 3

- **정확한 메커니즘:** 사용 즉시 현재 COST를 0으로 만들고, 해당 플레이어 턴이 끝날 때까지 `rewind_active = 1`로 둔다.
- **수치:** 현재 COST `→ 0`, 지속 `현재 턴 종료까지 1턴`.
- **지속/스택:** 재사용 불가. 이미 `rewind_active = 1`이면 카드가 해결되지 않는다.
- **주의:** 다음 턴부터 COST는 정상 누적된다. 상한 100 자체를 바꾸지 않는다.
- **의사코드:**

```ts
(player, ice, program) => {
  if (program.id === "rewind" && player.rewind_active === 0) {
    player.alarm = 0; player.rewind_active = 1;
  }
  return resolveFixedDamage(program.tier * 5, ice.armor);
}
```

`rewind` 자체도 프로그램이므로 카드의 고정 피해는 정상적으로 `1 × 5`를 적용한다. 턴 종료 시 `rewind_active = 0`으로 되돌린다.

- **왜 정체성을 만드는가:** 비용이 낮은 카드만 고르는 것이 아니라, COST가 위험 구간에 들어가기 직전에 리셋해 **알람 관리 자체를 공격 자원으로 바꾸는 운용**을 만든다.

### 4. `virus` — 우선순위 4

- **정확한 메커니즘:** 적중 시 ICE에 `virus_turns = 2`, `virus_armor_down = 1`을 부여한다.
- **수치:** 방어도 `-1`, 지속 `2개의 ICE 턴`; 피해는 즉시 카드의 `tier × 5`만 발생.
- **지속/스택:** 재사용 시 `virus_turns = 2`로 갱신하고 `virus_armor_down`은 1을 초과하지 않는다. 여러 바이러스의 방어도 감소 중첩 금지.
- **의사코드:**

```ts
(player, ice, program) => {
  if (program.id === "virus") {
    ice.virus_turns = 2; ice.virus_armor_down = 1;
  }
  return resolveFixedDamage(program.tier * 5, ice.armor - ice.virus_armor_down);
}
```

각 ICE 턴 종료 시 `virus_turns -= 1`; 0이 되면 `virus_armor_down = 0`이다.

- **왜 정체성을 만드는가:** 즉시 큰 수를 내는 대신, 한 번의 적중으로 다음 2턴의 방어 계산을 유리하게 만드는 **누적 압박형**을 만든다. 별도 DoT 피해는 없으므로 단일 피해 경로를 지킨다.

### 5. `surge` — 우선순위 5

- **정확한 메커니즘:** 카드 사용 직전 COST가 50 이하이면 이번 카드의 실제 비용을 1로, 51 이상이면 카탈로그 비용인 2로 계산한다.
- **수치:** `ap_cost 2 → 조건부 1`; 조건 경계 `COST <= 50`.
- **지속/스택:** 매 사용마다 독립 판정. 상태를 남기지 않는다.
- **의사코드:**

```ts
(player, ice, program) => {
  const cost = program.id === "surge" && player.alarm <= 50 ? 1 : program.ap_cost;
  player.alarm += cost;
  return resolveFixedDamage(program.tier * 5, ice.armor);
}
```

- **왜 정체성을 만드는가:** 저알람 구간에서 반복적으로 압박하고, 위험 구간에서는 정상 비용으로 전환되는 **템포/저비용 공격**을 만든다.

### 6. `shield` — 우선순위 6

- **정확한 메커니즘:** 다음 ICE 공격 한 번의 피해에서 4를 차감한다.
- **수치:** 피해 `-4`, 1회성.
- **지속/스택:** `shield_charges`는 최대 1. 재사용해도 1을 초과하지 않는다.
- **의사코드:**

```ts
(player, ice, program) => {
  if (program.id === "shield") player.shield_charges = 1;
  return resolveFixedDamage(program.tier * 5, ice.armor);
}
```

ICE 공격 시 `blocked = min(incoming_damage, 4)`를 차감하고 `shield_charges = 0`으로 만든다.

- **왜 정체성을 만드는가:** `decoy`의 1턴 50% 감소와 달리, 적 공격의 큰 한 번을 정확히 흡수하는 **예측 가능한 단발 방어**를 만든다.

### 7. `heal` — 우선순위 7

- **정확한 메커니즘:** 플레이어 HP를 3 회복하되 최대 HP를 넘지 않는다.
- **수치:** `HP += 3`, `HP <= maxHP`.
- **지속/스택:** 즉시 1회. 전투당 사용 제한은 새로 추가하지 않는다.
- **의사코드:**

```ts
(player, ice, program) => {
  if (program.id === "heal") player.hp = Math.min(player.maxHp, player.hp + 3);
  return resolveFixedDamage(program.tier * 5, ice.armor);
}
```

- **왜 정체성을 만드는가:** 방어도나 COST가 아니라 런 중 손실 HP를 회복하는 **소모전형**을 만들지만, 전투 승률에 미치는 영향이 커질 수 있어 우선순위를 낮춘다.

### 구현 보류

`probe`, `decrypt`는 `scan`/`backdoor`와 기능 중복이 커서 1차 구현에서 보류한다. `wardrone`의 “retaliation”은 별도 반격 피해 경로가 되기 쉬우므로 현재 엔진 제약에서는 구현하지 않는다. `inspire`, `ward`, `echo`, `trace`, `salvage`는 현재 단일 플레이어 전투 또는 보드 처리만으로는 효과 측정 정의가 불명확하다.

---

## B. 세 자키 정체성 제안

세 덱의 티어 합은 모두 11이다. 따라서 시작 시점의 정적 공격량은 동일하다.

| 자키 | 5장 시작 덱 | 티어 합 | 방어 카드 | 정체성 |
|---|---|---:|---|---|
| CASE | `scan, exploit, boost, barrier, decoy` | 11 | `barrier`, `decoy` | 정보 확보 후 강화 효과를 겹치는 **준비형 침투** |
| SIL | `rewind, exploit, cloak, barrier, decoy` | 11 | `cloak`, `barrier`, `decoy` | COST를 리셋하고 회피로 버티는 **알람 생존형** |
| KAS | `strike, exploit, virus, surge, decoy` | 11 | `decoy` | 방어도를 낮추고 저비용으로 몰아치는 **감염 템포형** |

### CASE

- `scan`이 3턴 동안 방어도 1을 낮춘다.
- `boost`는 기존 구현 그대로 공격에 +2를 2턴 적용한다.
- `exploit`은 방어도 절반 적용이다.
- `barrier`, `decoy`로 준비 턴의 생존성을 확보한다.

**다르게 하는 것:** 첫 턴에 무조건 가장 높은 티어를 내는 것이 아니라, `scan → exploit/boost` 순서로 3턴 창을 만든다. 이 덱의 핵심 지표는 `scan 이후 3턴 내 공격 성공률`과 `scan이 제공한 총 방어도 감소량`이다.

### SIL

- `rewind`는 현재 COST를 0으로 만든다.
- `cloak`은 기존 구현 그대로 15% 회피를 2턴 적용한다.
- `barrier`, `decoy`를 함께 사용해 위험 턴을 넘긴다.
- `exploit`은 공격 전환 수단이지만, 이 덱의 차별점은 공격력이 아니라 COST와 피격 관리다.

**다르게 하는 것:** COST 100에 도달하기 전에 `rewind`를 사용해 블록 턴을 회피하고, `cloak`/`barrier`/`decoy`로 ICE 공격의 기대 손실을 낮춘다. 핵심 지표는 `blocked-turn rate`, `rewind 사용 후 생존 턴 수`, `전투 종료 시 잔여 HP`다.

### KAS

- `virus`가 ICE 방어도를 2 ICE 턴 동안 1 낮춘다.
- `surge`는 COST 50 이하에서 실제 비용이 1이다.
- `strike`는 저비용 기본 카드로 남겨 바이러스와 surge 사이의 빈 턴을 채운다.
- `decoy`는 공격적 운용의 실패 턴을 한 번 보정한다.

**다르게 하는 것:** 한 번의 고티어 카드로 끝내는 것이 아니라 `virus → surge/strike` 순서로 2턴의 방어도와 비용 우위를 이용한다. 핵심 지표는 `virus 부여 후 2 ICE 턴 동안의 평균 유효 방어도`, `surge의 평균 실제 비용`, `턴당 공격 횟수`다.

---

## C. 예상 곡선과 위험 후보

정확한 승률 숫자는 아직 코드를 실행하지 않았으므로 제시하지 않는다. 아래는 현재 측정값을 기준으로 한 **방향 가설**이며, 수치 예측이 아니다.

| 덱 | 3등급 | 4등급 | 5등급 | 가설 근거 | 확신도 |
|---|---|---|---|---|---|
| CASE 준비형 | 상승 | 상승 | 상승 가능성 | `scan`과 `exploit`이 방어도 높은 ICE에서 유리하고, 티어 합은 기존 CASE보다 1 높다 | 중 |
| SIL 알람 생존형 | 상승 또는 유지 | 상승 | 상승 가능성 | `rewind`가 COST 100 블록 턴을 줄이고, 기존 3종 방어 효과와 결합한다 | 중하 |
| KAS 감염 템포형 | 유지 또는 소폭 상승 | 상승 | 상승 가능성 | `virus`의 방어도 감소가 고등급 ICE에서 상대적으로 커지고 `surge`가 반복 사용 비용을 줄인다 | 중 |

### 함정/과강 후보

- **함정 후보: KAS의 `virus`가 ICE 턴 시작 기준으로만 적용되는 경우.** 실제 카드 사용 직후의 공격에 적용되지 않으면 3등급에서 체감 효과가 없고, `surge`만 남아 현재 덱과 거의 같아진다.
- **과강 후보: SIL의 `rewind`.** `alarm = 0`이 너무 자주 가능하면 COST 상한이 사실상 무력화될 수 있다. `rewind` 사용률, 블록 턴 감소량, 승률 상승폭을 별도 감시해야 한다.
- **과강 후보: CASE의 중첩 계산.** `scan`, `exploit`, `boost`를 모두 공격 피해 증가로 구현하면 단일 피해 경로를 위반하거나 방어도 높은 ICE에서 과도한 상승이 생긴다. `scan`과 `exploit`은 피해량이 아니라 유효 방어도만 바꿔야 한다.
- **확정 판정 불가:** 기존 100 runs/mission 결과만으로는 제안 덱의 승률을 산술적으로 추정할 수 없다. 반드시 동일 시드의 `balance` 실행 결과로 판정한다.

---

## D. 검증 계획

### 1. 실행할 조합

```bash
npm run balance -- --deck-ids scan,exploit,boost,barrier,decoy
npm run balance -- --deck-ids rewind,exploit,cloak,barrier,decoy
npm run balance -- --deck-ids strike,exploit,virus,surge,decoy
```

동일 조건에서 현재 기준 덱도 다시 실행한다.

```bash
npm run balance -- --deck opening
npm run balance -- --deck veteran
npm run balance -- --deck heretic
```

각 실행은 기존 규칙대로 등급별 100 runs/mission, 고정 시드를 사용한다.

### 2. 필수 기록 지표

승률만 기록하면 원인을 알 수 없으므로 다음을 등급별·덱별로 기록한다.

- 승률: 3/4/5등급, 각 100 runs
- 평균 전투 승리율과 평균 런 길이
- COST 100 도달 횟수와 `blocked-turn rate`
- 카드별 평균 사용 횟수와 첫 사용 턴
- `rewind` 사용 전후 평균 COST
- `scan`/`virus`가 실제로 유효했던 공격 수
- 공격별 평균 유효 방어도
- ICE 처치까지 걸린 플레이어 턴 수
- 전투 종료 시 평균 HP와 평균 잔여 방어 효과
- `shield`, `barrier`, `decoy`, `cloak`이 막은 피해량

### 3. 실패 판정 기준

다음 중 하나라도 충족하면 1차안은 실패로 판정한다.

1. 세 제안 덱의 3등급 승률 최대-최소 차이가 **5%p 초과**.
2. 어느 한 제안 덱이 3등급에서 기존 CASE `78.4%`보다 **2%p 이상 낮음**.
3. 어느 한 제안 덱의 3등급 승률이 기존 CASE보다 낮고, 4·5등급에서도 방어도/알람/생존 지표의 보상 우위가 없음.
4. 어떤 덱이 기존 PPL 5장 기준 5등급 `44.4%`를 **5%p 이상 초과**하면서, 해당 상승이 단순히 COST 상한 우회 또는 방어도 계산 버그에서 발생함.
5. `rewind`가 포함된 SIL에서 blocked-turn rate가 기존 SIL 대비 **50% 이상 감소**하고, 동시에 3등급 승률이 **8%p 이상 상승**.
6. `virus`의 방어도 감소가 1을 초과하거나, 바이러스가 추가 피해를 발생시켜 `tier × 5` 단일 피해 규칙을 깨뜨림.
7. 카드별 효과가 시드가 아닌 난수에 의존하거나, 같은 입력 상태에서 실행 결과가 달라짐.

### 4. 조정 순서

실패 시 티어를 먼저 바꾸지 않는다. 다음 순서로 메커니즘 수치만 조정한다.

1. `rewind`: COST 초기화 여부를 유지한 채 사용 가능 횟수와 실제 적용 턴을 확인한다.
2. `virus`: 방어도 감소 지속을 2 ICE 턴에서 1 ICE 턴으로 축소한다.
3. `scan`: 방어도 `-1`은 유지하고 지속을 3턴에서 2턴으로 축소한다.
4. `surge`: COST 50 경계를 50에서 40으로 낮춘다.
5. 그래도 3등급 격차가 해결되지 않을 때만 카드 교체를 검토한다.

---

## E. 하지 말 것

- 효과가 없는 `planned_description`을 실제 효과로 간주하지 않는다.
- `boost`를 문서의 “30% 3턴”으로 구현하지 않는다. 현재 구현 기준은 **공격 +2, 2턴**이다.
- `barrier`를 문서에 없는 수치로 바꾸지 않는다. 현재 구현 기준은 **shield 2, 2턴**이다.
- `exploit`, `virus`, `surge`에 별도 추가 피해를 붙이지 않는다. 모든 피해는 계속 `tier × 5`여야 한다.
- `virus`를 매 턴 별도 DoT로 만들지 않는다. 방어도 계산만 바꾼다.
- `wardrone`의 retaliation을 현재 엔진에 억지로 넣지 않는다. 반격 피해는 단일 피해 경로와 충돌한다.
- COST 상한을 높이거나, 카드 블록을 무시하거나, ESC/ENTER의 실패 규칙을 바꾸지 않는다.
- `rewind`를 무제한 반복 사용 가능하게 만들지 않는다. 한 번의 사용으로 현재 턴만 리셋한다.
- `scan`/`virus`/`exploit`의 방어도 감소를 중첩시켜 음수 방어도를 만들지 않는다. 최종 방어도 하한은 0이다.
- 방어 카드가 없는 전용 덱을 만들지 않는다. 각 시작 덱은 최소 1장의 방어 카드를 유지한다.
- 승률이 높아 보인다는 이유만으로 정체성을 판정하지 않는다. 3등급 최대-최소 `5%p` 규칙과 COST·생존·유효 방어도 지표를 함께 본다.

## 결론

1차 구현은 `exploit → scan → rewind → virus → surge → shield` 순서가 적절하다. 세 시작 덱은 모두 티어 합 11로 맞추고, CASE는 정보/준비, SIL은 알람/생존, KAS는 방어도 감소/템포를 담당한다. 이 구조는 숫자 교환으로 약해지는 함정을 피하면서도, 각 덱이 실제로 다른 카드 순서와 상태 지표를 요구하게 만든다. 단, 승률 곡선은 코드 실행 전 확정할 수 없으므로 위 실패 기준을 통과한 경우에만 채택한다.
