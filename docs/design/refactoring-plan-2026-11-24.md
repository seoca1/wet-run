# wet_run 리팩토링 계획 — 2026-11-24

> **전제**: 이 저장소는 `balance.golden.json` · `gear.golden.json` · vitest 238/4459 ·
> mutation 39/39 이라는 **회귀 가드**를 이미 갖고 있다. 리팩토링은 **동작을 바꾸지 않는
> 것이 목적**이므로, 각 단계는 "골든 byte-identical + 테스트 green" 을 통과 조건으로 삼는다.
> 밸런스 수치는 **이 계획에서 건드리지 않는다**(그건 ADR 의 영역).
>
> 근거: 2026-11-24 코드 조사(파일 LOC·중복·죽은 코드·결합도) + 단일 검증 러틴 9/9 pass.

## 0. 현재 기준선 (2026-11-24 측정)

| 항목 | 값 |
|---|---|
| 러틴 | **9/9 pass** (balance · gear · tests · audit · doc_claims · prose · briefings · links · lang) |
| vitest | 238 files / **4459 pass** / 0 fail |
| typecheck / lint | 0 error (lint 경고 1 — `input/keyboard.ts:14` `any`, 기존) |
| 소스 규모 | `src/` 33,365 LOC · `tests/` 53,776 LOC · `scripts/` 3,434 LOC |
| 최대 모듈 | `src/main.ts` **2,568 LOC** (code 2,069) — 나머지 상위는 763 이하 |

---

## 1. 왜 리팩토링이 필요한가 (측정된 문제 3가지)

1. **중복이 값을 두 곳에 둔다** — RNG 구현이 5~6벌, 장비 스탯 병합이 2벌,
   미션 id 해시가 5벌. 그중 하나는 **비트 규약이 다르다**(`seed | 0` vs `seed >>> 0`)
   → 음수 시드에서 잠재적 불일치.
2. **god 함수 2개가 전투 코어에 있다** — `processEnemyTurns` 327줄, `useProgram` 308줄.
   둘 다 골든/전투 테스트로 고정돼 있어 **바꾸기 전에 쪼개야** 안전해진다.
3. **새 필드 하나에 5곳을 손으로 고친다** — 저장 슬롯 필드 목록이 3벌로 존재
   (`types.ts` · `state.ts` · `save/storage.ts`). 필드 추가/누락이 조용히 실패한다.

---

## 2. 단계 (위험 오름차순, 각 단계는 독립 커밋)

### Stage 0 — 죽은 코드 제거 (위험 없음, 가드 불필요)

| 항목 | 근거 | 규모 |
|---|---|---|
| 고아 렌더러 스텁 9개 | `src/renderer/{inventory,credits,shop,briefing,debug,pause,codex,journal,loading}.ts` — **인바운드 import 0** (직접 확인) | 63 LOC |
| 죽은 export | `grid.ts:135 drawRect` · `grid.ts:156 drawLine` · `state/prep.ts:82 prepAmountFor` · `state/campaign.ts:81 campaignMission` · `state/equipment_store.ts:84 LOADOUT_SLOTS` · `renderer/settings.ts:509 renderStorageQuota` · `combat/boss_phases.ts:89,172,189,206` | ~40 LOC |
| 과잉 export | `ice_scaling.ts:155 BOSS_GATE_CLEARS_BY_GRADE` · `:219 BOSS_ICE_BY_GRADE` — 모듈 내부에서만 사용 | export만 제거 |

**하지 말 것**: `combat_engine.ts:185 tickCombo` 는 죽은 코드처럼 보이지만
**ADR-0280 (c) 의 미해결 결정**이다(콤보 창이 턴제 전투에서 한 번도 작동한 적 없음).
삭제/구현은 오너 결정 — 정리 작업에 섞지 말 것.

**통과 조건**: `npm test` green · 러틴 9/9 (골든 이동 0).

---

### Stage 1 — 중복 제거 (낮음/중간 위험, 골든 가드)

#### 1a. RNG 단일화
- 현재: `dungeon.ts:60` · `event_matrix.ts:100` · `dungeon_crawler_generation.ts:19` ·
  `scripts/{play_policy,balance_sim,ending_distribution}.ts` — 같은 mulberry32 6벌.
  `graphic_novel_loaders.ts:102` 는 시드 없으면 `Math.random` 으로 떨어지는 변형.
- `withInt` 헬퍼도 `dungeon.ts:72` · `dungeon_crawler_generation.ts:38` 에 동일 복사.
- **비트 규약 차이**: `src` 는 `| 0`, `scripts` 는 `>>> 0` → 음수 시드에서 갈린다.
- **가드**: 던전 RNG는 `dungeonToMatrix` → 매트릭스 생성 → `balance_sim` 이 지난다.
  즉 **`npm run balance:check` + `npm run gear:check` 필수**.
- 주의: 규약을 통일하면 시드 결과가 바뀔 수 있다 → **바뀌면 골든이 잡는다**(그게 목적).

#### 1b. 장비 스탯 헬퍼 단일화
- `equipment.ts:147 addStats` 와 `set_bonus.ts:100 addStatsLocal` — 본문 동일(한쪽은
  `makeEquipStats`, 다른 쪽은 `Object.freeze` 인라인).
- `equipment.ts:72 makeEquipStats` 와 `equipment_catalog.ts:24` 의 private `s()` — 같은
  12필드 기본값 병합. **import 사이클을 피하려고 복제**한 것(코드에 주석으로 명시됨).
  → `EquipStats`/`makeEquipStats` 를 **leaf 모듈로 옮겨 사이클 자체를 제거**.
- **가드**: `npm run gear:check` (장비 스탯이 gear 골든을 만든다).

#### 1c. 미션 id 해시 — **통일하지 말고 문서화**
- 5벌: `dungeon_layout.ts:440`(`h*31+c`) · `dungeon_crawler_generation.ts:23`(같은 루프 인라인) ·
  `dungeon_crawler_core.ts:39 stringHashCode`(`(h<<5)-h+c`) · `equipment_drops.ts:37 hashString`(FNV-1a) ·
  `state_helpers.ts:88`.
- 이들은 **결정론적 시드를 만든다**. 통일하면 모든 기록 곡선이 이동한다(ADR-0321 전례).
- **결정**: 값이 같은 것만 합치고(`dungeon_layout` ≡ `crawler_generation`), 다른 것은
  "왜 다른가"를 한 줄씩 주석으로 남긴다. 통일은 별도 ADR + 골든 재기록.

#### 1d. crit 롤 중복
- `combat_engine.ts:172` 와 `ice_crit.ts:92` 가 **같은 공식**을 각자 계산.
- **위험 높음**(둘 다 전투 경로). 헬퍼 하나로 모으되 반드시 1:1 동일하게.
- 가드: `balance:check` + `tests/adr0320_effective_damage.test.ts` · `adr0321_attack_cases.test.ts`.

**통과 조건**: 골든 byte-identical · vitest green · 러틴 9/9.
**골든이 움직이면**: 그 변경은 리팩토링이 아니라 밸런스 변경이다 → 되돌리고 별도 ADR.

---

### Stage 2 — god 함수 분해 (중간 위험, 전투 코어)

| 함수 | 위치 | 줄 수 | 섞여 있는 책임 |
|---|---|---|---|
| `processEnemyTurns` | `combat/state_actions_combat.ts:263` | **327** | 보스 단계 배율(5단 삼항) · 스킬 선택 · 피해 계산 · 방어 감산(자동공격용 **거의 동일한 블록이 두 번**) |
| `useProgram` | `combat/state_actions_programs.ts:47` | **308** | 비용 검사 · 데미지 컨텍스트 · 실드 흡수 · 상태이상 2회 롤 · AoE/단일 분기 · SFX · 슬로우 |
| `processMonsterAi` | `dungeon/dungeon_crawler_core.ts:84` | 177 | 크롤러 전용 |
| `slotToGameState` | `state/state.ts:395` | 149 | 저장 → 상태 복원 + 43필드 수동 재구성 |

**방법**: 이름 있는 **순수 헬퍼 추출**(동작 무변경). 예:
`bossDamageMultiplier(phase)` · `mitigate(raw, armor, shield)` · `applyStatusProcs(state, target, rng)`.
두 번 복사된 방어 감산 블록을 **하나로** 만드는 것이 이 단계의 최대 실익.

**가드**: `npm run balance:check` · `npm run gear:check` · vitest ·
그리고 리팩토링 후 **`npm run mutation`(39/39 유지)** — 추출이 테스트 커버리지를 흐리면 여기서 드러난다.

---

### Stage 3 — 통합 레이어 (중간 위험, e2e 가드)

#### 3a. `main.ts` 분해 (2,568 LOC → 5~6 파일)
- `constructor` 426–808 (~383줄) · `handlePreGameInput` 1066–1416 (~351줄, 화면별 `if` 사다리) ·
  `draw` 1818–2076 (~259줄) · `boot()` 2484–2567.
- **주의**: `main.ts` 는 골든 하네스 import 그래프 **밖**이다(오케스트레이션 전용).
  그래서 밸런스 가드가 잡아주지 못한다 → **e2e(desktop 54 · mobile 58 · soak)가 유일한 가드**.
- 순서: 화면별 컨트롤러로 분리(입력 → 화면 → 액션), 상태 필드는 그대로 유지.

#### 3b. 저장 필드 단일 공급원
- 필드 목록이 3벌: `types.ts:450-493`(SaveSlot) · `state.ts:326-364`(쓰기) ·
  `save/storage.ts:226-248`(`isSaveSlot`) + `loadLegacy`/`parseSlot`.
- 제안: **필드 기술자(descriptor) 한 벌**에서 읽기/쓰기/검증을 파생 → 새 필드 추가가 한 곳.
- 가드: `tests/run_end_save.test.ts` + e2e `run_end_save` 드라이버.

---

### Stage 4 — 테스트 위생 (낮음 위험, 큰 churn 절감)

- 중복 fixture: `gridText` **11벌** · `loadDeck` **11벌** · `makeCombatState`/`combatState`/`buildCombatState` **21벌**.
- 이미 `tests/view_fixtures.ts`(사용 10/240) · `tests/encounter_test_helpers.ts`(22/240)가 있다 → **채택률을 올리는 것**이 목표.
- **큰 일괄 변경 금지**: 각 Stage 를 진행할 때 **그 영역의 테스트만** 옮긴다(리뷰 부담·회귀 위험 관리).

---

## 3. 하지 말 것 (명시)

- **밸런스 수치 변경** — 이 계획의 범위 밖(ADR-0339/0341 이 방금 확정).
- **미션 id 해시 통일** — 기록 곡선이 전부 이동. 별도 ADR 필요.
- **던전 크롤러의 in-place mutation 을 순수 리듀서로 전환** — 설계 변경이다.
  현재 `dungeon_crawler_*.ts` 만 상태를 직접 변이하고 나머지 `src/core` 는 순수하다.
  이건 ADR 로 결정할 문제(리팩토링 아님).
- **snake_case → camelCase 전면 개명** — `data_loaders`/`mission_ice` 경계의 정규화 지점이라
  개명하면 데이터 로더 계약이 흔들린다. 필요하면 **경계에서만** 정규화.
- **`tickCombo` 삭제** — ADR-0280 (c) 오너 결정.

---

## 4. 실행 순서와 예상

| 단계 | 규모 | 위험 | 가드 | 예상 |
|---|---|---|---|---|
| Stage 0 죽은 코드 | ~100 LOC 삭제, 9 파일 | 없음 | tests | 30분 |
| Stage 1a RNG | 6→1 모듈 | 중 | balance·gear 골든 | 2시간 |
| Stage 1b 스탯 헬퍼 | 3쌍 → 1쌍 | 중 | gear 골든 | 1시간 |
| Stage 1d crit 롤 | 2→1 | 중 | balance 골든 + 전투 테스트 | 1시간 |
| Stage 2 god 함수 | 2 함수 분해 | 중~높음 | 골든 + mutation | 반나절 |
| Stage 3a main.ts | 2,568 → 5~6 파일 | 중 | e2e | 1~2일 |
| Stage 3b 저장 필드 | 3벌 → 1벌 | 중 | save 테스트 + e2e | 반나절 |
| Stage 4 테스트 fixture | 240 파일 중 ~40 | 낮음 | vitest | Stage 별 분산 |

**각 단계의 완료 정의**: `npm run balance:check` + `npm run gear:check` byte-identical ·
`npm test` 238/4459 green · 러틴 9/9 · (Stage 2+) `npm run mutation` 39/39 유지.

## 6. 진행 상황

| Stage | 상태 | 결과 |
|---|---|---|
| 0 죽은 코드 | ✅ `60fd6b6b` | 스텁 9개 + 헬퍼 3개 삭제. 조사의 "죽은 export 11개" 중 **8개는 계보가 있어 보존**(ADR-0283·0318·0313(a)·PWA Tier7·0280(c)). |
| 1a RNG | ✅ `53e3b32d` | **6벌 → 1벌** (`src/core/rng.ts`). `\| 0` 과 `>>> 0` 은 비트 연산 특성상 **모든 시드에서 스트림 동일** → 골든 byte-identical 로 확인. |
| 1b 스탯 헬퍼 | ✅ `2fe6406d` | **3벌 → 1벌** (`equip_stats.ts` 리프) + `addStats` 2벌 → 1벌. import 사이클을 회피가 아니라 **제거**. |
| 1c 해시 주석화 | ✅ `095fc56c` | **합치지 않음**: 5벌이 전부 값이 다르고, 그중 하나는 자기 주석이 **거짓**이었다(정정). 코드 변경 0. |
| 1d crit 롤 | ✅ | `rollCritMultiplier(rng)` 하나로 — 소비 순서(rng 1회) 보존. |
| 2 god 함수 | ✅ `11697f9a` `72e3ffaf` `e3d10ad6` `8411b5e6` `b4c8714d` | **`processEnemyTurns` 327 → 218줄** (`applyEnemyHit` · `bossDamageMultiplierForPhase` · `resolvePlayerDeath` · `runEnemySkill`) · **`useProgram` 310 → 181줄** (`rollProgramDamage` · `effectiveArmorFor` · `rollProgramProcs` · `consumeMark` · `applyProgramOwnEffect` · `programStatusLines` · `buildProgramVfx`). **rng 소비 순서·단축 평가를 슬라이스마다 보존**(골든이 판정). |
| 3 main.ts · 저장 필드 | ⬜ | |
| 4 테스트 fixture | ⬜ | |

**Stage 1 종료 시점 확인**: 러틴 8/8 · vitest 238/4459 · typecheck 0 · lint 0 error ·
balance/gear 골든 byte-identical · **mutation 39/39 KILLED**(리팩토링이 테스트 커버리지를
약화시키지 않았음 — Stage 2 의 가드 기준선).

## 7. 열린 질문 (오너)

1. Stage 3a(`main.ts`)는 e2e 만이 가드다 — 브라우저 e2e를 러틴에 넣을 것인가?
   (`NEXT_SESSION_TODO` 의 `--e2e` 플래그 항목과 같은 결정)
2. 미션 id 해시 5벌을 "왜 다른가" 주석으로 고정할지, 아니면 통일 ADR 을 쓸지.
3. 던전 크롤러 mutation 스타일을 ADR 로 정리할지(순수 리듀서 전환은 별도 슬라이스).