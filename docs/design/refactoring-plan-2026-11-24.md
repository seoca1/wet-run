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
  **선행 조건(2026-11-24 완료)**: `python3 scripts/wet_run_verify.py --e2e` — 빌드 → `vite preview :5195`
  → Playwright(스냅샷·데모 스크린샷 제외). ADR-0340 이 남겨둔 "수동" 기본값은 유지하고
  플래그로만 돈다. `--full` 은 e2e 를 포함한다.
- 순서: 화면별 컨트롤러로 분리(입력 → 화면 → 액션), 상태 필드는 그대로 유지.

**3a 설계 (다음 세션용 — 2026-11-24 조사)**

`class Game` = **2,182줄(301–2482) · 53 메서드 · 68 필드**. 슬라이스 순서와 근거:

| 슬라이스 | 옮길 것 | 줄 수(대략) | 비고 |
|---|---|---|---|
| 3a-1 | 입력 사다리 — `handlePreGameInput`(351줄) + `handle{Crafting,Equipment,Dungeon,Settings,Pause,Stub,GraphicNovel}Input` | ~700 | `if (this.screen === …)` 사다리. **가장 큰 단일 덩어리**. → **완료**: 3a-1a(설정 187줄) · 3a-1b(핸들러 6종 ~150줄) · 3a-1c(사다리 167줄) · 3a-1d(그래픽 노블 44줄) — `src/app/{settings,screen,pre_game,graphic_novel}_input.ts` |
| 3a-2 | `draw`(259줄) + `drawPrep` | ~300 | 화면 라우팅 | → **3a-2 사전 화면 분기(129줄) + `drawPrep` 완료**; 라우터 본체는 상태 변이/저장 때문에 컨트롤러 잔류 검토 |
| 3a-3 | 런 수명주기 — `launchSelected`·`handleContinue`·`endRun`·`startDungeonCrawl`·`autosave`·`noteRunFinished`·`refreshSaveCache` | ~250 | 저장과 얽힘 → 3b(스키마) 이후가 안전 | → **완료** (`src/app/run_lifecycle.ts`); 소스-텍스트 테스트 3건을 공용 헬퍼로 이관 |
| 3a-4 | 루프 — `startLoop`·`start`·`stop`·`syncPhase`·`resizeRenderer`·`applyAccessibilitySettings` | ~200 | | → **대신 입력 파이프라인**(`constructor` 의 289줄 dispatcher 클로저)을 분리 → `src/app/game_input.ts`. 루프/라우터는 객체 수명주기·합성 루트라 잔류 검토 |
| 3a-5 | 접근자·버튼 핸들러(2266–2460) | ~200 | 남겨도 무방 |

**방법**: 메서드가 `this.<private field>` 를 광범위하게 쓰므로, 옮길 함수는 **host 인터페이스**를 받는다:

```ts
export interface PreGameHost { screen: ScreenKind; selectedMenuIndex: number; /* … */ launchSelected(): void }
export function handlePreGameInput(host: PreGameHost, action: GameAction): boolean
```
`Game` 이 구조적으로 이 인터페이스를 만족하면 되고, 필요한 필드는 `private` → `readonly`/`public` 로 좁혀 연다(한 번에 하나씩).
**하지 말 것**: 한 슬라이스에 파일 10개 이상 변경(AGENTS §6). 슬라이스마다 `--e2e` 를 돌린다(회당 ~6분).

#### 3b. 저장 필드 단일 공급원 ✅ (2026-11-24)
- 필드 목록이 3벌: `types.ts`(SaveSlot) · `state.ts`(쓰기) ·
  `save/storage.ts`(`isSaveSlot`).
- **구현**: 검증자의 단일 공급원 = `src/save/slot_schema.ts` (필드별 row: `required` + `check`).
  타입과 작성자는 각자의 자리에 남았다 — 작성자는 상태→슬롯 **매핑**이라 표로 파생할 수 없다.
  대신 `tests/save_slot_schema.test.ts` 가 셋을 묶는다: `Record<keyof SaveSlot, true>` 리터럴로
  타입에 필드가 늘면 **컴파일 실패**, 스키마 키와 일치 강제, 작성자 출력 키 ⊆ 스키마.
- **덤**: 작성자가 쓰지만 검증되지 않던 4필드(`campaignMissionIds`·`campaignCompleted`·
  `uniquePickDone`·`intelNodes`)를 별도 커밋으로 검사 추가 — 손상된 값이 `slotToGameState` 까지 갔다.
- 가드: `tests/run_end_save.test.ts` · `property_save_fuzz.test.ts` · 새 스키마 테스트.

---

### Stage 4 — 테스트 위생 (낮음 위험, 큰 churn 절감)

- 중복 fixture: `gridText` **11벌** · `loadDeck` **11벌** · `makeCombatState`/`combatState`/`buildCombatState` **21벌**.
- 이미 `tests/view_fixtures.ts`(사용 10/240) · `tests/encounter_test_helpers.ts`(22/240)가 있다 → **채택률을 올리는 것**이 목표.
- **큰 일괄 변경 금지**: 각 Stage 를 진행할 때 **그 영역의 테스트만** 옮긴다(리뷰 부담·회귀 위험 관리).
- **약화 방지 규칙 (2026-11-25 추가)**: 지역 fixture 를 공용으로 바꿀 때는 **동작이 같은지 먼저 기계적으로 확인**한다(본문 정규화 비교). 테스트는 `src/` 의 가드이므로, 조용히 약해져도 게이트가 초록으로 남는다 — mutation 도 `src/` 만 본다.
- **진행**: 4a `gridText` 10벌 → 1벌 완료. 남은 것 4b `loadDeck`(11) · 4c combat state(21).

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
`npm test` 239/4465 green · 러틴 9/9 · (Stage 2+) `npm run mutation` 39/39 유지.

## 6. 진행 상황

| Stage | 상태 | 결과 |
|---|---|---|
| 0 죽은 코드 | ✅ `60fd6b6b` | 스텁 9개 + 헬퍼 3개 삭제. 조사의 "죽은 export 11개" 중 **8개는 계보가 있어 보존**(ADR-0283·0318·0313(a)·PWA Tier7·0280(c)). |
| 1a RNG | ✅ `53e3b32d` | **6벌 → 1벌** (`src/core/rng.ts`). `\| 0` 과 `>>> 0` 은 비트 연산 특성상 **모든 시드에서 스트림 동일** → 골든 byte-identical 로 확인. |
| 1b 스탯 헬퍼 | ✅ `2fe6406d` | **3벌 → 1벌** (`equip_stats.ts` 리프) + `addStats` 2벌 → 1벌. import 사이클을 회피가 아니라 **제거**. |
| 1c 해시 주석화 | ✅ `095fc56c` | **합치지 않음**: 5벌이 전부 값이 다르고, 그중 하나는 자기 주석이 **거짓**이었다(정정). 코드 변경 0. |
| 1d crit 롤 | ✅ | `rollCritMultiplier(rng)` 하나로 — 소비 순서(rng 1회) 보존. |
| 2 god 함수 | ✅ `11697f9a` `72e3ffaf` `e3d10ad6` `8411b5e6` `b4c8714d` | **`processEnemyTurns` 327 → 218줄** (`applyEnemyHit` · `bossDamageMultiplierForPhase` · `resolvePlayerDeath` · `runEnemySkill`) · **`useProgram` 310 → 181줄** (`rollProgramDamage` · `effectiveArmorFor` · `rollProgramProcs` · `consumeMark` · `applyProgramOwnEffect` · `programStatusLines` · `buildProgramVfx`). **rng 소비 순서·단축 평가를 슬라이스마다 보존**(골든이 판정). |
| 3 main.ts · 저장 필드 | 🟡 진행 | 3b 완료: 저장 슬롯 **3벌 → 단일 스키마**(`save/slot_schema.ts`) + 작성자가 쓰지만 검증되지 않던 **4필드 검사 추가**. e2e 게이트(`wet_run_verify.py --e2e`) 추가 = `main.ts` 분해의 선행 조건. |
| 3a-1a 설정 입력 | ✅ `4a469645` | `handlePreGameInput` 의 `screen === "settings"` 분기(**187줄**) → `src/app/settings_input.ts` (host 인터페이스 `SettingsInputHost`, 248줄). `main.ts` **2,568 → 2,377줄**. 가드: e2e **106 pass** · vitest **239/4465** · 게이트 **9/9** · mutation **39/39**. **정규화 diff 로 이동만 확인**(바이트 동일 — 재작성 없음). `Game` 의 10개 멤버를 `private` → 공개(계획대로 "좁혀 연다"). |
| 3a-1b 화면 핸들러 | ✅ `970dfa9b` | 크래프팅·장비·던전·런타임 설정·일시정지·스텁 입력 **6종(~150줄)** → `src/app/screen_input.ts` (`ScreenInputHost`). `main.ts` **2,377 → 2,227줄**. 정규화 diff 로 6종 **전부 동일**(유일한 차이: `handleStubInput` 의 선두 주석이 doc 주석으로 이동). 런타임 설정 스텁은 `handleSettingsStubInput` 으로 개명(사전 설정 화면과의 혼동 방지). 가드: e2e **106 pass** · vitest **239/4465** · 게이트 **9/9** · mutation **39/39**. |
| 3a-1c 사전 입력 사다리 | ✅ `e23d459f` | `handlePreGameInput`(**167줄** — menu · jockey_select · briefing · prep · mission_select · far_grid_hub · 설정 분기) → `src/app/pre_game_input.ts` (`PreGameInputHost extends SettingsInputHost` — 설정 화면 멤버를 다시 선언하지 않는다). `BeatCard` 도 모듈로 이동. `main.ts` **2,227 → 2,056줄**. 정규화 diff **동일**(유일한 차이: 설정 위임이 `this` → `host`). 가드: e2e **106 pass** · vitest **239/4465** · 게이트 **9/9** · mutation **39/39**. |
| 3a-1d 그래픽 노블 입력 | ✅ `c810dbfa` | `handleGraphicNovelInput` + `exitGraphicNovel` + `startRunFromGraphicNovel` (**44줄**) → `src/app/graphic_novel_input.ts` (`GraphicNovelInputHost`). `main.ts` **2,056 → 2,006줄**. 정규화 diff **3/3 동일**. 가드: e2e **106 pass** · vitest **239/4465** · 게이트 **9/9** · mutation **39/39**. → **Stage 3a-1(입력 계층) 완료** (3a-1a~1d, `main.ts` 2,568 → 2,006). |
| 3a-2 사전 렌더링 | ✅ `fa8b25d5` | `draw` 의 **사전 화면 분기(129줄)** + `drawPrep`(28줄) + `formatMissionOption` → `src/app/pre_game_render.ts` (`PreGameRenderHost`). `main.ts` **2,006 → 1,827줄**. 정규화 diff **3/3 동일**(유일한 차이: 이동한 타입 주석의 상대 경로 `./core/i18n.ts` → `../core/i18n.ts`). **가드가 실제 결함을 잡음** — `tests/nav_index.test.ts` 가 `main.ts` **소스 텍스트**에서 `formatNavIndex` 호출을 찾고 있었다 → 새 위치를 가리키도록 수정(규약은 그대로, 위치만 이동). 가드: e2e **106 pass** · vitest **239/4465** · 게이트 **9/9** · mutation **39/39**. |
| 3a-2 잔여 (라우터) | ⬜ | `draw` 라우터 본체 — 비트카드/런인트로 오버레이 · 비전투 런(matrix/ending/loot) · 전투 경로. 프레임마다 `this.state` 를 변이하고 `autosave()`·`syncPhase()` 를 호출하므로 **컨트롤러에 남기는 것이 맞다**(오너 확인 대상). |
| 3a-3 런 수명주기 | ✅ `7703a69b` | `launchSelected`(60줄) · `handleContinue`(37) · `endRun`(15) · `startDungeonCrawl`(4) · `autosave`(13) · `noteRunFinished`(3) · `refreshSaveCache`(6) → `src/app/run_lifecycle.ts` (`RunLifecycleHost`, 265줄). 모듈명은 `startRun`/`continueRun`/`settleRun`/`autosaveRun`. `main.ts` **1,827 → 1,634줄**. 정규화 diff **7/7 동일**(유일한 차이: prettier 가 접은 두 호출의 **trailing comma** 2개). **소스-텍스트 테스트 3건이 위치에 묶여 있었다** → 공용 헬퍼 `tests/controller_source.ts` 신설(main.ts + `src/app/*` 를 한 덩어리로 읽는다)로 3건 수정, `growth_reveal` 은 `private` 접두사 고정도 함께 수정. 가드: e2e **106 pass** · vitest **239/4465** · 게이트 **9/9** · mutation **39/39**. |
| 3a-4 입력 파이프라인 | ✅ `018cb754` | `constructor` 안의 `handler` 클로저(**289줄**) + `handleContractPrepInput`(27줄) + `SCREENS_WITH_INPUT` → `src/app/game_input.ts` (`GameInputHost`, 413줄). `main.ts` **1,634 → 1,265줄**. 정규화 diff **2/2 동일**(차이는 prettier 줄바꿈뿐). **남은 소스-텍스트 테스트 6건도 공용 헬퍼로 이관** → 이제 `src/main.ts` 를 직접 읽는 테스트는 **0건**. 유일한 명명된 차이: 생성자의 지역 `resetIdle()` → `host.idleSinceMs = Date.now()`(같은 문장). 가드: e2e **106 pass** · vitest **239/4465** · 게이트 **9/9** · mutation **39/39**. |
| 3a-5 잔여 (루프·라우터) | ⬜ | `draw` 라우터(130줄) · `loop`/`start`/`stop`(113줄) · `syncPhase`/`resizeRenderer`/`applyAccessibilitySettings` · 접근자/E2E 훅 — **합성 루트 + 객체 수명주기**. 권고: 여기서 Stage 3a 종료(§7-6). |
| 4a `gridText` | ✅ | 중복 `gridText` **10벌 → 1벌** (`tests/view_fixtures.ts` 에 공용 추가). 3가지 파라미터 표기(4+3+3 파일)가 **본문은 완전 동일**이었다 → 이동 전 각 지역 본문을 정규화 비교해 **10/10 동작 동일**을 기계적으로 확인(테스트 약화 없음의 근거). `nav_index.test.ts` 는 `grid.get(x,y)` + 공백 패딩이라 **다른 함수** → 잔류. **`src/` 변경 0**(`git diff --name-only \| grep web/src` = 0) → e2e·mutation 은 재실행 대상이 아님. 가드: vitest **239/4465** · 게이트 **9/9**(`--tests`). |
| 4b `loadDeck` | ⬜ | **11벌** — 다음 슬라이스 |
| 4c combat state | ⬜ | `makeCombatState`/`combatState`/`buildCombatState` **21벌** — 가장 큰 덩어리, `tests/encounter_test_helpers.ts` 채택률 올리기 |
| 4 테스트 fixture | ⬜ | |

**Stage 1 종료 시점 확인**: 러틴 8/8 · vitest 238/4459 · typecheck 0 · lint 0 error ·
balance/gear 골든 byte-identical · **mutation 39/39 KILLED**(리팩토링이 테스트 커버리지를
약화시키지 않았음 — Stage 2 의 가드 기준선).

## 7. 열린 질문 (오너)

1. ~~Stage 3a(`main.ts`)는 e2e 만이 가드다 — 브라우저 e2e를 러틴에 넣을 것인가?~~
   → **해소 (2026-11-24)**: `wet_run_verify.py --e2e` 로 편입. `--full` 에 포함, 기본은 수동(ADR-0340).
2. 미션 id 해시 5벌을 "왜 다른가" 주석으로 고정할지, 아니면 통일 ADR 을 쓸지.
3. 던전 크롤러 mutation 스타일을 ADR 로 정리할지(순수 리듀서 전환은 별도 슬라이스).
4. **`draw` 라우터 본체를 옮길 것인가** (2026-11-25 신규) — 프레임마다 `state` 를 변이하고
   `autosave()`·`syncPhase()` 를 호출한다. 옮기면 ~45 멤버 host 뒤로 **영속화가 숨는다**.
   권고: 컨트롤러(합성 루트)에 남긴다. `loop`/`start`/`stop` 도 같은 성격(객체 수명주기).
5. ~~**`constructor` 의 입력 파이프라인**(dispatcher 클로저)을 분리할 것인가~~
   → **완료 (2026-11-25)**: 실측 **289줄**(예상 ~200 보다 컸다) → `src/app/game_input.ts`.
   `handleContractPrepInput`(27줄) · `SCREENS_WITH_INPUT` 도 함께. 라우터/루프와 달리
   **영속화를 하지 않는 계층**이라 깨끗하게 이동했다.
6. **남은 컨트롤러 코어를 어떻게 볼 것인가** (2026-11-25) — `main.ts` 1,265줄 중
   `constructor` ~90줄 · `draw` 라우터 130줄 · `loop` 113줄 · 접근자/E2E 훅 ~200줄.
   권고: **여기서 Stage 3a 를 끝낸다.** 남은 것은 합성 루트(생성/배선)와 객체 수명주기다.