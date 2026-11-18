# ADR-0327: programPower는 armor를 뚫는다 — 마지막 읽히는 스탯

**상태**: Accepted (오너 결정: *"programPower 배선 + 재조정"*)
**날짜**: 2026-11-18
**결정자**: 사용자
**우선순위**: P0 (성장 · 전투)

## 컨텍스트 (Context)

ADR-0326 이 방어 축을 배선한 뒤, 읽히지 않는 장비 스탯 5종이 남았다. 확인해 보니 **그중 4종은 "미배선"이 아니라
서브시스템 부재**였다:

| 스탯 | 상태 |
| --- | --- |
| `programPower` | ✅ 배선 가능 — 카드↔ICE 상호작용 |
| `apBonus` · `apRegenBonusPct` | ❌ **AP 자원 자체가 없다** — 활성 모델은 `COST`(alarm)+hand size. `combat_models.ts` 의 prototype `Combatant.ap` 는 활성 게임이 안 씀 |
| `grantsSkillId` | ❌ **플레이어 skill 시스템 없음** — `state.skillCooldowns` 는 감소만 되고 아무도 스킬을 발동하지 않는다 |
| `extraEffect` | ❌ **resolver 없음** — 임의 문자열 실행 금지라 whitelist 해석기 신설 필요 |

그래서 `programPower`(덱 아이템의 정체성)만 먼저 배선한다. AP·스킬·효과는 별도 서브시스템 슬라이스다.

## 결정 (Decision)

**`programPower` 는 ICE armor 의 일부를 **무시**한다** ([`combat_engine.ts`](../../../web/src/core/combat/combat_engine.ts)
`programPowerArmorBypassPct`, [`state_actions_programs.ts`](../../../web/src/core/combat/state_actions_programs.ts),
[`damage_preview.ts`](../../../web/src/core/combat/damage_preview.ts)):

```
effectiveArmor = floor( max(0, armor − piercePoints) × (armorKeptPct/100) × (100 − powerBypassPct)/100 )
```

- `powerBypassPct = min(programPower, 60)` — **상한 60%** 라 최상위 덱도 armor 를 완전히 지우지 못한다.
- **카드의 base damage(`tier * 5`)는 건드리지 않는다** — armor 적용량만 줄인다. ADR-0320/0304 의 카드 가치 계약 유지.
- `damage_preview.ts` 도 같은 순서를 써서 **화면과 실제 플레이가 어긋나지 않는다**.

## 결과 (Consequences)

- **9종 live**: `attackBonus` · `critBonusPct` · `damageBonusPct` · `defense` · `hpBonus` · `shieldBonus` ·
  `iceResistance` · `programPower` (+ 파생 세트 보너스). 덱 아이템(`STARTER_DECK`·`CORPORATE_DECK`·`MILITECH_DECK`·
  `GHOST_DECK`·`MASTER_DECK`·`ZION_TRODES`·`KEREZNIKOV`)이 처음으로 전투에 기여한다. `apBonus`-only 인 `STARTER_HEADWARE` 만 남는다.
- **기록 기준선 byte-identical**: `npm run balance` **100/100/100/97.1/70.6/47.0** (EMPTY_LOADOUT → programPower 0 → no-op).
- **검증**: vitest **232 files / 4417 tests**(신규 `adr0327_program_power` 6) · typecheck/lint 0 error · build OK.
- **⚠️ 재조정 필요**: programPower 가 live 가 되자 장비가 **더 강해졌다** — `npm run gear` 에서 T1 만으로도 미션 완주율이
  전 등급 100% 가 된다(programPower 15% bypass 만으로). 장비 파워 재조정은 후속(같은 스레드).
- **남은 것**: AP 자원 · 플레이어 스킬 · `extraEffect` resolver — 각각 별도 서브시스템.
