# ADR-0211: ICE 난이도 스케일링 — grade 기반 HP/스탯 배선

**상태**: Accepted (Option 1)
**날짜**: 2026-09-24
**결정자**: 사용자 (2026-09-24: Option 1 선택)
**우선순위**: P1 (밸런스 정확성)
**관련**:
- [ADR-0199 — Wet Run Web MVP (Tier 1)](./0199-wetrun-web-mvp.md) — web 코드베이스 기준
- ADR-0210 — Combat VFX Effect Schema — 동일 세션 정합 작업 (canonical: `docs/architecture/0210-combat-vfx-effect-schema.md`)
- ADR-0012 — Combat Difficulty & Threat Level (PPL & ZDR)

## 컨텍스트 (Context)

`npm run balance` 하네스의 grade별 승률이 비단조(non-monotonic)로 나온다.

```
grade  missions  win-rate
1      2         50.5%
2      5         80.2%
3      7         43.4%
4      7         85.9%
5      9         100.0%
6      3         100.0%
```

2026-09-24 조사 결과, 이 비단조성은 **밸런스 수치 문제가 아니라 배선(wiring) 오류**다. 하네스는 grade 난이도가 아니라 **BSP 던전 위상(topology)** 을 측정하고 있었다.

근본 원인 (근거: `docs/diagnostics/balance-grade-curve-root-cause-2026-09-24.md`):

1. **ICE 선택이 grade를 무시한다.** `web/src/core/dungeon.ts:223-231` 은 일반 ICE 방에 `watchdog`(HP 100), 보스 방에 `wintermute`(HP 150)를 하드코딩한다. `ice_ids.json` 의 `hp_per_grade` 는 코드 경로에서 전혀 참조되지 않는다.
2. **로더가 ICE HP를 100으로 강제한다.** `web/src/core/data_loaders.ts:146` 의 `parseIce` 는 `const hp = 100;` 로 고정한다. `ice_types.json` 의 97개 항목이 가진 `hp_per_grade` / `defense` / `resistance` 는 dead data 다.
3. **하네스는 첫 점유 노드의 첫 ICE만 전투한다.** `web/scripts/balance_sim.ts:78` 의 `nodes.findIndex((n) => n.iceIds.length > 0)` 정책 때문에, 그 노드가 `watchdog`(HP 100)인지 `wintermute`(HP 150)인지는 순수하게 BSP 토폴로지 + `matrix_seed` 로 결정된다 — grade 와 무관.
4. **결과가 이분(bimodal)이다.** 5장 덱이 ~100-160 dmg 를 내므로 `watchdog` 는 죽고(H100) `wintermute` 는 살아남는다(P150). 33/33 미션이 100% 또는 2% 승률로 갈린다. G5 == G6 는 해당 12개 미션의 토폴로지가 우연히 겹친 결과다.
5. **grade 버킷팅**: 33개 미션 중 raw `grade` 필드를 가진 것은 0개다. `data_loaders.ts:80` 이 `grade_max` 로 폴백한다.

즉, 이 문제는 하네스에만 국한되지 않는다. 실제 게임에서도 **grade 가 ICE 난이도를 구동하지 않는다** — 던전이 항상 같은 ICE 를 같은 HP 로 배치한다.

## 고려한 옵션

### Option 1: 하네스만 grade 기반 HP 로 산출 (surgical)

- **설명**: `web/scripts/balance_sim.ts` 에서 하드코딩된 `node.iceHp[i]` 대신 `mission.grade_min`(또는 `grade_max`)과 `ice.hp_per_grade` 로 HP 를 계산한다.
- **장점**:
  - 약 5줄 변경. 데이터 파일 / 전투 상수 불변.
  - `ice_types.json` 의 `hp_per_grade` 를 활성화한다.
  - 하네스 이름("balance")과 실제 측정 대상이 일치하게 된다.
- **단점**:
  - 실제 게임 난이도는 여전히 고정 ICE 이다. 하네스와 게임이 계속 어긋날 수 있다.
  - 어떤 grade(min/max)를 쓸지, HP 공식을 어떻게 정의할지는 디자인 결정이다.
- **Pillar 정합**:
  - P1 (The Run): run 별 난이도 곡선 가시화에 기여.
  - P4 (The Build): 간접.

### Option 2: 던전 ICE 선택 자체를 grade 로 파라미터화 (근본 수정)

- **설명**: `web/src/core/dungeon.ts` 의 `dungeonToMatrix` 가 `missionGrade` 별로 ICE id/HP 세트를 다르게 배치하도록 한다 (예: grade 1-2 watchdog HP 80, grade 3-4 black HP 200, grade 5-6 wintermute_proxy HP 400).
- **장점**:
  - 게임과 하네스가 동일한 난이도 모델을 공유한다.
  - `hp_base` / `hp_per_grade` / `defense` / `resistance` 를 실제로 사용한다.
  - `parseIce` 의 HP 100 강제도 함께 정리해야 한다.
- **단점**:
  - `ice_types.json` 콘텐츠 설계 패스 + `parseIce` 수정 필요. 범위가 크다.
  - 기존 미션 난이도 밸런스를 재조정해야 한다.

### Option 3: 하네스 산출물 명칭/문서만 정정 (무변경)

- **설명**: 하네스 출력을 실제 측정 대상(grade 버킷 + 토폴로지 기반 ICE)에 맞게 재명명/문서화한다.
- **장점**:
  - 데이터 / 전투 코드 무변경. 오해 제거.
- **단점**:
  - 난이도 곡선을 제공하지 않는다. 근본 문제는 남는다.

## 추천 (Recommendation)

**Option 1 을 우선 적용**해 하네스를 정확하게 만든 뒤, **Option 2 를 후속 ADR 로 분리**해 게임 난이도 배선을 정식으로 설계할 것을 권장한다. Option 1 은 근거 기반으로 검증 가능한 최소 수정이고, Option 2 는 콘텐츠 설계 결정을 포함하므로 별도 판단이 필요하다.

## 사용자 결정 (Decision)

- [x] Option 1 — 2026-09-24 사용자 선택
- [ ] Option 2
- [ ] Option 3
- [ ] 기타: ___
- [ ] Defer (다음 단계로 미룸)

## 결과 (Consequences)

**2026-09-24 — Option 1 구현 완료, 단 곡선은 여전히 비단조.**

구현 내용:
- `web/scripts/balance_sim.ts` — `iceHpForGrade(ice, grade)` 추가. `hp_base + hp_per_grade * (grade - 1)` 로 grade 기반 HP 산출, `simulateCombat` 이 이를 encounter template 에 덮어씀.
- `web/src/core/data_loaders.ts` — `parseIce` 가 `hp_base` / `hp_per_grade` 를 `Ice` 로 노출 (기존에는 누락된 dead data 였음). 게임 경로의 `Ice.hp` (100 고정) 는 불변.
- `web/src/core/types.ts` — `Ice.hpBase?` / `Ice.hpPerGrade?` 추가.
- 테스트: `tests/balance_sim.test.ts` 에 grade 스케일링 + fallback 회귀 2건 추가.

**중요 — ADR 의 원래 진단이 부정확했음이 구현 중 확인됨.** 하네스가 실제로 사용하던 것은 `node.iceHp[i]` 가 아니라 `parseIce` 의 `Ice.hp` (전 ICE 100 고정) 였다. HP 를 grade 로 스케일해도 곡선이 거의 변하지 않은 이유는, 승패가 HP 가 아니라 **encounter template 의 정체성**으로 갈리기 때문:

| template | armor | grade1 HP | grade6 HP | opening deck 승률 |
| --- | --- | --- | --- | --- |
| `watchdog` (일반 ICE 방) | 1 | 50 | 100 | 100% |
| `wintermute` (보스 방) | 8 | 260 | 410 | 0% |

- 첫 ICE 보유 노드가 일반 ICE 방이면 `watchdog`, 보스 방이면 `wintermute` — 이는 순수 BSP 토폴로지가 결정하며 grade 와 무관하다.
- opening deck (~100-160 dmg) 은 `watchdog` (HP 50-100) 을 항상 처치하고, `wintermute` (armor 8 + HP 260-410) 은 항상 실패한다 → grade bucket 안에서 100%/0% 이분(bimodal).

따라서 **Option 1 은 필요조건이지만 충분조건이 아니다.** grade-난이도 곡선을 실제로 얻으려면 encounter 자체가 grade 로 결정되어야 한다 (Option 2). 또한 opening deck damage vs ICE HP/armor 스케일 자체의 재검토도 필요하다.

**후속**: Option 2 를 별도 ADR 로 진행할 것을 권장. 본 ADR 의 Option 2 섹션 + 위 표가 그 입력이 된다.

## Implementation Status (2026-09-24)

**Status**: ✅ Implemented (Option 1) — 단, 곡선 비단조는 미해결 (Option 2 필요)

**Evidence**:
- `web/scripts/balance_sim.ts` — `iceHpForGrade` + `simulateCombat` template HP override
- `web/src/core/types.ts` — `Ice.hpBase?` / `Ice.hpPerGrade?`
- `web/src/core/data_loaders.ts` `parseIce` — `hp_base` / `hp_per_grade` 노출 (게임 `Ice.hp=100` 불변)
- `web/tests/balance_sim.test.ts` — grade 스케일링 + fallback 회귀 2건
- `web/src/core/dungeon.ts:223-231,261` — ICE 방/보스 방 ICE id + HP 하드코딩 (Option 2 대상, 미변경)
- `web/src/core/state_actions.ts:572` — `defenderDefenseBonus: 0` 하드코딩 → ICE `armor` 미반영 (Option 2/별건)
- `web/src/core/starter_deck.ts:28` — `STARTER_DECK` dead code (별건)
- `docs/diagnostics/balance-grade-curve-root-cause-2026-09-24.md` — 전체 조사

**Notes**: Option 1 로 `hp_per_grade` 는 활성화됐으나, 실측 곡선 (50/80/43/86/100/100%) 은 거의 불변. 원인은 HP 가 아니라 encounter template 정체성 (watchdog armor 1 ↔ wintermute armor 8) 이 BSP 토폴로지로 결정되기 때문. 상세는 Consequences 참조.

## 영향 받는 항목

- `web/scripts/balance_sim.ts` (Option 1)
- `web/src/core/dungeon.ts`, `web/src/core/data_loaders.ts` (Option 2)
- `docs/design/systems/difficulty-rating.md` (PPL/ZDR 명세)
- `web/tests/balance_sim.test.ts`

## 관련 결정

- ADR-0199 (web MVP)
- ADR-0012 (PPL & ZDR)

## 변경 이력

- 2026-09-24: Draft 작성
- 2026-09-24: Evidence 보강 (ICE armor 미반영, `STARTER_DECK` dead code)
- 2026-09-24: Accepted (Option 1) + Option 1 구현. 진단 정정 — 실제 driver 는 `node.iceHp` 가 아니라 encounter template 정체성. 곡선 미해결 → Option 2 후속 권장.