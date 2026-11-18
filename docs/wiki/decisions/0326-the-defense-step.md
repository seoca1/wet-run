# ADR-0326: 방어 단계가 생겼다 — 장비가 전투에 닿는다

**상태**: Accepted (오너 결정: *"커밋 + 스탯 배선"*)
**날짜**: 2026-11-18
**결정자**: 사용자
**우선순위**: P0 (성장 · 전투)

## 컨텍스트 (Context)

장비 스탯 12개 중 **9개를 아무도 읽지 않았다**(ADR-0322/0325 시점 실측). 그중 핵심은 **플레이어 방어 단계의 부재**였다 —
ICE의 피해가 **곧바로 HP로** 들어왔고, 사이에 있는 것은 shield pool 하나뿐이었다.

```
ICE hit → (shield pool) → HP          # defense / iceResistance 가 죽은 숫자
```

그래서 ADR-0325 가 장비에 **소유와 획득 경로**를 줬어도, 장비는 여전히 **전투에 닿지 않았다.**
그리고 하네스(`npm run balance`)는 `EMPTY_LOADOUT` 으로 런을 만들기 때문에 **장비 효과는 한 번도 측정된 적이 없었다.**

## 결정 (Decision)

**⑴ 방어 단계를 고정 순서로 배선한다** ([`player_mitigation.ts`](../../../web/src/core/combat/player_mitigation.ts)):

```
raw → iceResistance(%) → defense(flat) → shield pool → HP
```

- `iceResistance` 는 퍼센트(상한 **75%** — 장비가 면역을 만들 수 없다), `defense` 는 그 뒤의 flat 감산.
- **카드의 armor 경로와 분리**한다(공격 측 `attack_resolution.ts` 는 무변경).
- `shield pool` 은 기존 status-effect pool(ADR-0255)을 그대로 쓴다.

**⑵ `hpBonus` · `shieldBonus` 는 run 시작에 적용한다** ([`equipment_stats.ts`](../../../web/src/core/state/equipment_stats.ts)) —
`applyPrep` 과 같은 형태(hpBonus 는 maxHP 상향 후 채움, shieldBonus 는 `shield` status effect).

**⑶ 하네스에 loadout 훅을 추가한다** — `simulateCombat`/`runSuite` 에 **기본 `EMPTY_LOADOUT`** 파라미터(무변경) +
`npm run gear` 프로브([`gear_curve_probe.ts`](../../../web/scripts/gear_curve_probe.ts)).

## 결과 (Consequences)

- **기록된 기준선은 byte-identical**: `npm run balance` **100/100/100/97.1/70.6/47.0**. 하네스는 bare runner 를 재므로
  방어 단계가 그 곡선을 건드리지 않는다(빈 loadout = no-op). 곡선 이동은 **장비를 착용했을 때만** 일어난다.
- **측정 발견 — 장비가 곡선을 무너뜨린다** (`npm run gear`, 페어 시드, 비-보스 교전 1회/미션, `win% / HP 잔존 %`):

  | loadout | g1 | g2 | g3 | g4 | g5 | g6 |
  | --- | --- | --- | --- | --- | --- | --- |
  | bare (기록 기준선) | 100/78 | 100/71 | 100/69 | 100/53 | 88/51 | 87/43 |
  | T1 street+eyes+gloves | 100/94 | 100/83 | 100/84 | 100/71 | 100/70 | 100/62 |
  | T2 corp+subdermal+ninja+boots | 100/100 | 100/100 | 100/100 | 100/96 | 100/91 | 100/82 |
  | T4 arasaka+body | 100/100 | 100/100 | 100/100 | 100/100 | 100/100 | 100/100 |
  | T6 master+zion | 100/100 | 100/100 | 100/100 | 100/100 | 100/100 | 100/100 |

  카탈로그 스탯은 **읽히지 않는 시스템**을 전제로 저작되어 과대하다. 이건 배선 결함이 아니라 **오너 결정**이다 —
  스탯을 낮출지, 난이도를 장비에 맞춰 스케일할지. (T1 조차 offense 스탯만으로 g6 를 87/43 → 100/62 로 올린다.)
- **검증**: vitest **231 files / 4411 tests**(신규 `adr0326_player_defense` 15) · typecheck/lint 0 error · build OK.
- **남은 것**: `apBonus` · `apRegenBonusPct` · `programPower` · `grantsSkillId` · `extraEffect` **5종 미배선**
  (`apBonus`·`programPower` 는 g5/g6 를 가장 크게 흔든다 — 곡선 측정 필수). `shieldBonus` 는 state 필드 없이 status effect 로 구현했다.
