# Wet Run — Combat Feel & Interaction 제안서 (2026-10-29)

> **성격**: 조사 + 제안 (RESEARCH ONLY). 이 문서 작성 시점(`2026-10-29`)에서 `web/` 아래 어떤
> 게임 코드도 수정되지 않았다. 모든 제안은 후속 태스크가 실행할 수 있는 형태이며, 각 행은
> "현재 무엇이 없는가"의 근거를 `file:line` 으로 명시한다.
>
> **기준 코드**: `Game/wet_run` HEAD = `0eb1558` (docs(log): record grade curve re-baseline)
> **기준 테스트**: `cd web && npx vitest run` → **127 files / 2986 tests / 0 failures**
> **관련 결정**: ADR-0196(접근성), ADR-0201(Howler 오디오), ADR-0204(phase-aware BGM),
> ADR-0205(status VFX + HUD), ADR-0207(Tier4 SFX/애니메이션/glyph),
> ADR-0210(VFX effect schema), ADR-0226(ICE 비피해 효과), ADR-0228(archetype crit),
> ADR-0229(grade curve re-baseline + drift policy)
>
> **핵심 결론 (한 문장)**: 이 코드베이스는 *feel 인프라를 설계하고 렌더러까지 완성해 놓고
> 배선만 하지 않은 상태*다. 27개 VFX kind 중 10개는 렌더러·스키마·테스트까지 갖춰져 있으나
> **런타임에 한 번도 생성되지 않는다**. 여기에 더해 **게임 루프 자체가 없다** —
> 화면 갱신이 입력 이벤트에만 묶여 있어 애니메이션이 재생될 시간이 없다.

---

## 1. 현재 상태 요약 (Current-State Inventory)

아래는 "실제로 동작하는 것 / 정의만 있고 배선 안 된 것 / 아예 없는 것"의 3분할이다.
근거는 모두 `web/` 기준 `file:line`.

### 1.1 동작하는 것 (Working)

| 영역 | 내용 | 근거 |
| --- | --- | --- |
| VFX 스키마 | 27개 effect kind 의 canonical taxonomy (`category` / `duration_ms` / `color_hint` / `payload_shape`) | `web/src/data/effects.json:1`, `web/src/data/effects.d.ts:43-71` |
| VFX 인스턴스 모델 | `tick` / `duration` / `durationMs` / `elapsedMs` / `payload` / `payloadNum` + ms 정밀 만료 | `web/src/renderer/combat_vfx_core.ts:41-59`, `advanceVfxBy` `:129-145` |
| VFX 렌더러 | 27개 kind 전부에 ASCII 렌더러 구현 (combat 18종 / scene 9종) | `web/src/renderer/combat_vfx_render_combat.ts:17-373`, `web/src/renderer/combat_vfx_render_scene.ts:18-293` |
| VFX 합성 | grid overlay 합성 + 마지막 인스턴스 우선 | `web/src/renderer/combat_vfx.ts:77-114` |
| VFX 색상 | Gibson 15색 palette + `resolveColorHint()` (ADR-0210 토큰 매핑) | `web/src/renderer/palette.ts:12-62` |
| HP 바 / 상태 라벨 | `healthBar` / `healthColor` / `formatStatusLabel` / `hitFlashColor` (pure function) | `web/src/renderer/vfx.ts:9-39` |
| ICE defeat / player defeat ASCII 아트 | `ICE_DEFEAT_ART` / `PLAYER_DEFEAT_ART` + `centerArt()` | `web/src/renderer/vfx.ts:41-77` |
| 상태 glyph | 5종 단일 문자 (`burn`/`stun`/`slow`/`silence`/`vulnerable`) | `web/src/renderer/vfx.ts:80-94` |
| 오디오 매니저 | Howler 래퍼, BGM 20트랙 + SFX 24종, BGM/SFX 개별 볼륨 + localStorage 영속, mute, crossfade | `web/src/audio/manager.ts:10-58`, `:74-79`, `:238-303`, `:342-430` |
| phase-aware BGM | `PHASE_TO_SOUND` 6개 phase 매핑 + `playPhase()` crossfade | `web/src/audio/manager.ts:63-70`, `:228-236` |
| BGM 트랙 카탈로그 | 15개 트랙의 volume / fadeIn / fadeOut / loop 메타데이터 + 16개 전환 규칙 | `web/src/core/sound_system.ts:57-139`, `:147-187` |
| 프로그램 SFX dispatch | 역할 기반 SFX 선택 (`combat_skill_strike` / `_burst` / `_guard` / `_support` / `combat_block` / `combat_hit`) | `web/src/core/state_helpers.ts:88-107` |
| 이동 SFX | `movement_step` / `movement_node` | `web/src/core/state_helpers.ts:118-124` |
| 터치 입력 | pointer-coarse 자동 마운트 가상 패드 + 프로그램 버튼 행 | `web/src/input/touch.ts:279-288`, `:140-189` |
| 게임패드 입력 | rAF 폴링 + 버튼 edge 감지 (press only) | `web/src/input/gamepad.ts:94-135`, `:175-200` |
| 튜토리얼 | 6단계 오버레이, localStorage 완료 플래그, ESC 스킵 | `web/src/renderer/tutorial.ts:22-76`, `:151-183` |
| 키보드 매핑 | 방향/Enter/Space/Esc/Q/Tab/1-9 | `web/src/core/types.ts:449-469` |

### 1.2 정의만 있고 배선 안 된 것 (Defined but Unwired)

이 분류가 이 제안서의 핵심이다. **직접 실행해 보면 재현되는 사실**이다.

| # | 항목 | 상태 | 근거 |
| --- | --- | --- | --- |
| U1 | **`player_hit` VFX** — "!! DAMAGE !!" + 화면 흔들림 렌더러 | 렌더러·스키마·duration 테이블 전부 존재하나 **런타임 spawn 호출이 0건** | 렌더러 `web/src/renderer/combat_vfx_render_combat.ts:152-164` / 스키마 `web/src/data/effects.d.ts:163-172` / duration `web/src/core/state_helpers.ts:161-162`, `:223-224` / **spawn 호출 없음** |
| U2 | **`heal` / `debuff` / `stun` / `counter` / `lifesteal` VFX** | 5종 모두 렌더러 존재, spawn 호출 0건 | `combat_vfx_render_combat.ts:34-76`(`heal`), `:99-113`(`debuff`), `:114-134`(`stun`), `:318-336`(`counter`), `:337-357`(`lifesteal`) |
| U3 | **`ice_intro` / `ice_death` VFX** | "INCOMING: <ICE>" 스캔 배너 / "CONNECTION SEVERED" 배너 렌더러 존재, spawn 호출 0건 | `combat_vfx_render_scene.ts:19-52`, `:53-92` |
| U4 | **`defeat` VFX** | 렌더러 존재, spawn 호출 0건 (승리 `victory`만 spawn됨) | `combat_vfx_render_scene.ts:186-198` vs 실제 spawn `web/src/core/state_actions_programs.ts:347` |
| U5 | **`status_apply` VFX** | "[<status> applied]" + 진행 바 렌더러 존재, spawn 호출 0건 | `combat_vfx_render_combat.ts:189-207` |
| U6 | **`critical_hit` VFX** | 스폰은 되지만 **조건이 도달 불가능한 수준** — `damage >= 10` 하드코딩 | `web/src/core/state_actions_programs.ts:233-244` (thresholds `:65-66`, `:126-131` 참고) |
| U7 | **`core/accessibility.ts` 전체** | `reducedMotion` / `highContrast` / `colorblind` 헬퍼가 정의돼 있으나 **소비자가 0건** | 정의 `web/src/core/accessibility.ts:1-111` / grep 결과: `web/src/` 내 참조 없음 |
| U8 | **`tickAlarm` / 알람 누적 루프** | `combat_engine.ts` 에 존재하나 production caller 없음 — 알람은 프로그램 사용 시에만 정적 증가 | `web/src/core/ice_crit.ts:14-17` 가 이 사실을 명시 ("the web build has no alarm accrual loop") |
| U9 | **`getAlarmMultiplier` / `shouldTargetAlly` (ICE archetype)** | ADR-0161 의 4개 archetype 동작 중 2개가 미배선 | `web/src/core/ice_crit.ts:10-21` |
| U10 | **`resetTutorial()`** 는 배선됨이나 튜토리얼은 **첫 실행 자동 표시되지 않음** — 메뉴에서 수동 진입만 가능 | `web/src/main.ts:1155-1159`, `web/src/renderer/menu_main.ts:53` |
| U11 | **`renderHUD()` (1줄 HUD 바)** | dungeon/matrix 용으로 작성됐으나 전투 화면은 다른 경로(`buildHudLines`)를 씀 | `web/src/renderer/hud.ts:16-94` vs `web/src/core/state.ts:179-210` |
| U12 | **ADR-0226 ICE 효과 (shield/heal/regen/buff)의 시각·청각 표현** | 효과는 상태로 적용되지만 **메시지 문자열만** 남김 — VFX 0건, SFX 0건 | `web/src/core/ice_combat_effect_apply.ts:67`, `:82`, `:98-102`, `:126`, `:141`, `:166` (6개 지점 전부 `message` 만 반환) |
| U13 | **`player_hit` 사운드** | `SFX_IDS.DAMAGE` / `SFX_IDS.ATTACK` / `SFX_IDS.ICE_BREAK` 는 정의·파일 존재하나 combat 경로에서 호출 안 됨 | 정의 `web/src/audio/manager.ts:39-41` / 파일 `web/public/sounds/sfx/damage.wav`, `attack.wav`, `ice_break.wav` / 호출은 `web/src/main.ts:416-451` 에서 `COMBAT_HIT`/`VICTORY`/`DEFEAT` 만 |

### 1.3 아예 없는 것 (Missing)

| # | 항목 | 근거 |
| --- | --- | --- |
| M1 | **게임 루프 (render loop)** — `requestAnimationFrame` 기반 지속 갱신 루프가 없고, `draw()` 는 **입력 이벤트에서만** 호출된다. `setInterval`/`requestAnimationFrame` 호출은 `input/gamepad.ts:117` (패드 폴링)와 `core/performance.ts:11` (FPS 카운터) 뿐 | `web/src/main.ts` 전체 grep 결과 `setInterval` 0건, `requestAnimationFrame` 0건 / `draw()` 호출 64곳 전부 입력 핸들러 내부 (`main.ts:378` … `:1105`) |
| M2 | **히트스톱 (hit-stop)** — 명중 시 타임라인 정지 | `web/src/` 내 `hitStop` / `hit-stop` / `freeze` 개념 0건. `docs/design/systems/animations.md` 에는 설계만 존재 |
| M3 | **부유 데미지 넘버 (floating damage numbers)** | `web/src/renderer/` 내 데미지 숫자 오버레이 0건. 현재는 `HIT! -N` 텍스트(`combat_vfx_render_combat.ts:143-149`)와 HUD 바 색 변경(`main.ts:1700-1708`)만 |
| M4 | **화면 흔들림 (canvas offset shake)** | `combat_vfx_render_combat.ts:152-164` 의 `player_hit` 은 *격자 안*에서 문자를 좌우로 옮길 뿐, **canvas 자체를 offset 하지 않는다**. `AsciiRenderer.render()` 에 offset 인자가 없음 | `web/src/renderer/canvas.ts:105-113` |
| M5 | **입력 버퍼링 (input buffering)** | 플레이어 입력은 즉시 reducer 로 직행하며 큐/선입선출 없음 | `web/src/main.ts:409-452` (직접 `applyAction`) |
| M6 | **키 리필 디바운스 (숫자키 연타)** | `keyboard.ts` 는 `event.repeat` 를 modifier 조합일 때만 무시하고 숫자키 repeat 은 통과시킨다 → 1키 长押 시 프로그램 연타 가능 | `web/src/input/keyboard.ts:72-74` |
| M7 | **명중 사운드 레이어링 / 피치 변조 / ducking** | `playSfx()` 는 단일 Howl 을 그대로 재생 — rate/pitch 변조 없음, BGM ducking 없음, 레이어叠加 없음 | `web/src/audio/manager.ts:432-456` |
| M8 | **텍스트 스케일링 / 폰트 크기 옵션** | `AsciiRenderer` 의 cell size 는 breakpoint 로만 결정, 사용자 조절 불가 | `web/src/renderer/canvas.ts:25-44` |
| M9 | **색각 이상용 palette 선택 UI** | `PALETTE` 는 단일 고정값. `get_color_palette` 4모드 개념은 Python 레거시만 존재 | `web/src/renderer/palette.ts:12-48` / ADR-0196 `:11-24` |
| M10 | **reduced-motion 토글** | `prefersReducedMotion()` 정의만 있고 소비자 없음 (U7 동일) | `web/src/core/accessibility.ts:20-23` |

### 1.4 전투 카운트와 리듬 (Turn Cadence) — 현재 실측

| 항목 | 값 | 근거 |
| --- | --- | --- |
| 적 자동 공격 간격 | 2000 ms | `web/src/core/combat_engine.ts:10` (`AUTO_ATTACK_INTERVAL_MS = 2000`) |
| 적 턴 트리거 방식 | **플레이어가 프로그램을 사용해야만** 진행. `processEnemyTurns` 의 유일한 호출자는 `applyCombatAction` 의 `use_program` 분기 | `web/src/core/state_actions_combat.ts:64` (`drawHand(processEnemyTurns(result))`) — grep 결과 호출 1건 |
| 대기 방식 | 플레이어가 아무것도 안 하면 **적도 아무것도 안 함**. 가짜 idle threat 없음 | `state_actions_combat.ts:139-141` (`currentMs - lastEnemyAttackMs < AUTO_ATTACK_INTERVAL_MS` → early return) |
| 선공/선공 제어 | 없음 — 유저 입력 기반 턴 구조 | 동일 |
| 앨람 누적 | 프로그램 사용 시에만 정적 증가 (`program.cost` 만큼). 시간 기반 alarm tick 없음 | `web/src/core/state_actions_programs.ts:57-61`, `ice_crit.ts:14-17` |
| 콤보 윈도우 | 3500 ms (`COMBO_WINDOW_MS`) | `web/src/core/combat_engine.ts:21` |
| 상수 지연 | `STAGGER_DURATION_MS = 1500` | `web/src/core/combat_engine.ts:20` |

> **해석**: 이 구조는 "플레이어가 속도를 완전히 통제한다"는 점에서 의도된 설계로 보인다.
> 플레이어가 대기를 felt 하는 상황은 "적을 못 죽였을 때"다 — 그런데 그때 적도 아무것도 안 한다.
> 즉 **긴장감이 시간 압력이 아니라 체력/덱 상태로만** 표현된다. 2초짜리 `AUTO_ATTACK_INTERVAL_MS`
> 는 enemy turn 의 *단위*일 뿐 플레이어가 기다리는 시간이 아니다 (enemy turn 은 프로그램 1회 사용에
> 1회 발생하는 인stantaneous tick).

### 1.5 계획된 feel (Design Intent) — 구현되지 않은 설계 문서

`docs/design/systems/animations.md` 가 이 게임의 feel 설계를 이미 기술한다. 현재 구현과의
격차가 크다.

| 설계 문서 요구 | 설계 근거 | 현재 구현 |
| --- | --- | --- |
| 화면 흔들림 1-2px / 100-200 ms | `docs/design/systems/animations.md:171-174` | 미구현 (M4) |
| 화면 flash (치명타) | `docs/design/systems/animations.md:176-179` | 미구현 |
| 데미지 넘버 부유 (작은 흰색 `-5` / 큰 노란색 `-25`) | `docs/design/systems/animations.md:39`, `:62`, `:98-99` | 미구현 (M3) |
| 일반 공격 3프레임 × 80ms = 240ms, 무채색 | `docs/design/systems/animations.md:29-40` | 240 ms 맞음. 단 `attack` kind 의 색은 `YELLOW_AMBER` (`combat_vfx_render_combat.ts:28`) — "무채색" 규칙 위반 |
| 스킬 공격 6프레임 × 100ms = 600ms, 프로그램별 색 | `docs/design/systems/animations.md:42-63` | `heavy_attack` 900 ms (`state_helpers.ts:194-195`) — 600ms 규칙 위반 |
| 피격 4프레임 × 60ms = 240ms, red, 화면 흔들림 | `docs/design/systems/animations.md:115-131` | 미구현 (U1) — `player_hit` 스폰 없음 |
| 사망 7프레임 × 200ms + 1초 pause = 2.4 s, "FLATLINE. Static. Silence." | `docs/design/systems/animations.md:133-154` | `FLATLINE` 메시지는 존재 (`state_actions_combat.ts:386`) / `defeat` VFX 미스폰 (U4) / 2.4s 연출 없음 (M1) |
| ICE 격파 페이드아웃 | `docs/design/systems/animations.md:156-167` | `ice_death` VFX 미스폰 (U3) |
| 일반 = 무채색, 스킬 = 색채 ( 대비 원칙 ) | `docs/design/systems/animations.md:14-21` | `ice_hit` 는 `RED_BRIGHT` 로 행 전체를 덮음 (`combat_vfx_render_combat.ts:139-142`) — "일반 = 무채색" 위반 |

---

## 2. 개선 제안 — 우선순위 표

**정렬 기준**: 가치/비용 비율. 비용은 S(≤ 1 파일, ~50 LOC) / M(2-3 파일, ~150 LOC) / L(구조 변경).
모든 행의 "왜" 칸에는 `file:line` 근거가 들어 있다.

| # | 제안 | 왜 (현재 무엇이 부족한가) | 어떻게 (구체적 구현 접근) | 예상 효과 | 비용 | 리스크 | 검증 방법 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **P1** | **화면 흔들림 + 히트스톱을 실제 canvas 레벨로** | `player_hit` VFX 는 격자 문자만 흔들고 canvas 는 안 움직인다 (`combat_vfx_render_combat.ts:152-164`). `AsciiRenderer.render()` 에 offset 인자가 없다 (`canvas.ts:105-113`). 히트스톱 개념 자체가 없다 (M2). 설계 문서는 1-2px / 100-200ms 를 요구한다 (`animations.md:171-174`) | ① `AsciiRenderer.render()` 에 `shake?: {x:number;y:number}` 파라미터 추가 (`canvas.ts:105`). ② `GameState` 에 `shakeUntilMs` / `shakeMagnitude` 필드 추가. ③ 명중 시 reducer 가 설정 → `draw()` 가 잔여 시간 동안 offset 적용. ④ 히트스톱은 별도 phase 로 VFX 만 연장 (적 턴을 실제로 지연하지 말고 **연출로만** 40-60ms 정지) | 명중이 "따라온다" 느낌으로 바뀜. 캐노버스 2D 라벨이 사양이므로 비용 대비 효과 최대 | M | 캔버스 offset 이 HUD 텍스트와 어긋남. 히트스톱이 **적 턴 타이밍**을 건드리면 ADR-0229 drift 대상 — 반드시 연출 전용으로 격리 | e2e `web/e2e/tier55_vfx.spec.ts` 에 shake offset assertion 추가. `web/tests/vfx_ms_timing.test.ts` 가 존재하니 동일 패턴으로 shake duration 테스트 추가 |
| **P2** | **10개 미배선 VFX 배선 (특히 `player_hit`)** | 27개 kind 중 10개가 렌더러·스키마·duration 까지 갖췄으나 spawn 호출 0건 (§1.2 U1-U5). 특히 `player_hit` 이 없으므로 **피격 피드백이 화면에 전혀 없다** | `state_actions_combat.ts` 의 `processEnemyTurns` 안에서 `playerHp` 감소 지점마다 `import_vfx("player_hit", "", durationForKind("player_hit"))` 1건 추가 (`state_actions_combat.ts:255`, `:320`). 동등하게 `heal`/`shield`/`debuff`/`stun`/`status_apply`/`ice_intro`/`ice_death`/`defeat` 를 각 발생 지점에 spawn. **스키마/렌더러 수정은 0** — 이미 다 있다 | 플레이어가 받는 피해가 처음으로 보인다. ADR-0226 효과도 "보이는" 사실이 된다 | **S** | spawn 추가로 `vfxInstances` 배열이 늘어남 → `advanceVfxListBy` 비용. 무한정 append 되지 않도록 max 인스턴스 상한 필요 (`main.ts:1518`) | `web/tests/combat_vfx.test.ts` 가 kind 별 렌더링을 검증하므로 신규 테스트는 "어떤 상태 전이가 어떤 kind 를 spawn 하는가" 를 검증. `web/tests/status.test.ts` 에 player_hit spawn 케이스 추가 |
| **P3** | **부유 데미지 넘버** | 현재 데미지 표시는 `HIT! -N` 텍스트 한 줄 (`combat_vfx_render_combat.ts:143-149`) 뿐이고 위치가 고정 (2,1). 설계 문서는 색상·크기 분기를 명시한다 (`animations.md:39`, `:62`, `:98-99`) | `CombatVfxInstance` 에 `startRow`/`targetRow` 이미 존재 (`combat_vfx_core.ts:56-58`) → 데미지 넘버가 상승하며 사라지는 프레임을 `ice_hit` / `critical_hit` renderer 에 구현. `progress` 로 y 오프셋 보간. `attack` payload 에 program_name 이 실려 있으므로 (`effects.json` `attack.payload_shape.program_name`) 이름도 함께 표기 | "얼마나 아팠는지"가 눈으로 읽힘. crit/normal 구분 시각화 | M | 텍스트가 다른 HUD 라인과 겹칠 수 있음. `grid` 는 `setText` 로 덮어쓰므로 레이어 순서에 의존 | `web/tests/combat_vfx_v2.test.ts` 패턴을 따라 "특정 tick 에서 넘버 문자열이 존재하는가" 검증. 스크린샷은 `web/e2e/demo-screenshots.spec.ts` 참고 |
| **P4** | **Combat log / message 필드 확장** | `state.message` 는 단일 문자열 1줄이며, `processEnemyTurns` 는 **마지막 메시지 1건만** 남긴다 (`state_actions_combat.ts:417-420`: `logMessages[logMessages.length - 1]`). `useProgram` 도 단일 문자열 (`state_actions_programs.ts:361-363`). 적이 스킬→auto-attack→Dixie→status tick 을 한 턴에 여러 번 하면 앞선 이벤트가 전부 사라진다 | `GameState` 에 `combatLog: ReadonlyArray<string>` (최근 N건, cap 8) 추가. `buildHudLines` (`state.ts:179-210`) 의 하단에 최근 3줄 표시. `state.message` 는 "가장 최근 1줄" 로 유지 (기존 테스트 호환) | 플레이어가 "뭐가 일어났는지" 를 놓치지 않음. 특히 `CRITICAL` 마커 (`state_actions_combat.ts:257`, `:324`, `:328`) 와 ADR-0226 의 shield/heal/regen/buff 메시지 (`ice_combat_effect_apply.ts:67` 등) 가 살아남음 | M | HUD 줄 수 증가 → 좁은 화면(40 cols)에서 잘림. `renderHUD` 의 overflow 가드 (`hud.ts:69`) 를 combat HUD 에도 적용 필요 | `web/tests/sound_triggers.test.ts` 가 상태 전이 기반 predicate 를 검증하는 패턴을 쓰므로 같은 형태로 log 보존 테스트 추가. `web/tests/layout.test.ts` 에 좁은 폭 회귀 추가 |
| **P5** | **명중 SFX 레이어링 + 플레이어 피격 SFX** | 플레이어가 받는 피해에 대한 SFX 호출이 없다 (`main.ts:416-451` 은 `COMBAT_HIT`/`VICTORY`/`DEFEAT` 만). `SFX_IDS.DAMAGE` / `ATTACK` / `ICE_BREAK` 는 정의·파일 존재하나 미사용 (`audio/manager.ts:39-41`, `public/sounds/sfx/*.wav`) | `main.ts` 의 action 핸들러 안에서 `previous.player.hp > this.state.player.hp` 이면 `SFX_IDS.DAMAGE` 재생, ICE HP 감소면 `pickProgramSfxId` 결과와 **겹쳐** `COMBAT_HIT` 추가 (2음 동시 → 임팩트 두께). 어차피 `useProgram` 안에서도 이미 1회 재생하므로, **이중 재생 금지** 필요 | 플레이어 타격과 ICE 타격이 음색으로 분리. "나만 맞은 것" 이 즉시 들림 | **S** | SFX 가 2배로 들리면 노이즈. volume balancing 필요 | `web/tests/audio.test.ts` + `web/e2e/sound_triggers.spec.ts` 에 "플레이어 HP 감소 시 DAMAGE SFX 호출" 검증 추가 |
| **P6** | **ADR-0226 ICE 효과( shield/heal/regen/buff ) 가시화** | ADR-0226 의 4개 효과는 상태로 정확히 적용되지만 (`ice_combat_effect_apply.ts:47-183`), 반환값이 `message` 하나뿐이다 — VFX 0건, SFX 0건. 게다가 `STATUS_GLYPHS` 에 `shield`/`regen`/`powered` 항목이 없어서 (`vfx.ts:80-86`) **HUD glyph 로도 안 보인다**. 플레이어는 "적이 방패를 세웠다" 를 눈으로 알 수 없다 | ① `ice_combat_effect_apply.ts` 의 4개 함수가 `state` 와 함께 **VFX 배열** 을 반환하도록 확장 (`IceEffectOutcome` 에 `vfx` 필드 추가). ② `shield` → `shield` kind, `heal` → `heal` kind, `regen` → `regen` kind, `buff` → `buff` kind spawn — **4개 렌더러가 이미 존재** (`combat_vfx_render_combat.ts:34-76`, `:84-98`, `:306-317`). ③ `STATUS_GLYPHS` 에 `shield: "S"` 등 추가 — 단 `stun` 의 `"S"` 와 **충돌하므로** 기존 5자를 재배치해야 하고, 그건 `web/tests/vfx.test.ts:150` ("exposes 5 glyph mappings") 을 깨므로 테스트 갱신 필요 | 적의 방어 행동이 "전략적 예고" 가 됨. 카드게임식으로 "저것은 방패다" 를 읽게 됨. **ADR-0226 의 가치가 눈에 보이게 됨** | M | glyph 문자 재배치는 기존 테스트(`vfx.test.ts:149-161`)와 HUD 폭을 건드림. balancer 영향 없음 (표시 전용) | `web/tests/ice_combat_effects.test.ts` 에 "shield 적용 시 `shield` VFX spawn" 검증. `web/tests/vfx.test.ts` 의 glyph 개수 assertion 갱신 |
| **P7** | **적 행동 프리셋 (입력 유휴 시 시간 압력)** | 지금은 플레이어가 프로그램 안 쓰면 **적도 아무것도 안 한다** (`state_actions_combat.ts:135-141` 이 `use_program` 내부에서만 호출됨 — grep 결과 호출 1건). 긴장감이 "시간" 이 아니라 "HP/덱" 으로만 표현된다 | `use_program` 과 무관하게 **별도 tick source** 를 둬서, 플레이어 입력 없이 N 초가 지나면 적이 한 번 행동한다. 단 `AUTO_ATTACK_INTERVAL_MS = 2000` (`combat_engine.ts:10`) 를 바꾸지 말고 **"입력 없음 시에만"** 추가 tick 경로를 만들 것. 그러면 밸런스 수치는 그대로 두고 "아무것도 안 하면 적이 때린다" 는 압박만 추가 | 멍때리기가 손해가 됨. deck-building 로그라이크의 "턴 압박" 원칙 회복 | **L** | ⚠️ **전투 밸런스 변경** — 승률이 달라질 수 있으므로 **ADR-0229 §A1 drift check 필수** (`npm run balance -- --runs 100` before/after 실측, ±3pp 초과 시 되돌리거나 re-baseline) | `npm run balance` before/after 표를 ADR 에 첨부. `web/tests/balance_sim.test.ts` 는 결정성 invariant 유지. 새 idle-tick 테스트는 `fuzz_combat.test.ts` 와 함께 |
| **P8** | **`critical_hit` 임계값을 데미지 스케일에 연동** | `critical_hit` 는 `damage >= 10` 하드코딩 (`state_actions_programs.ts:233-244`). g1 ICE 는 3 tier × 5 = 15 기본 피해라 임계값을 자주 넘지만, 상위 등급/HP cap 이후엔 낮게 떨어진다 → **"치명타" 가 상대적으로 자주 발생하는 티어와 드문 티어가 갈린다**. 또 `calculateDamage` 의 실제 crit (`CRIT_CHANCE = 0.15`, `combat_engine.ts:16`) 과 이 VFX 임계값은 **완전히 별개** — 플레이어 진짜 crit이 나도 VFX crit이 안 뜰 수 있다 | ① `calculateDamage` 의 crit 여부를 `useProgram` 이 결과로 받아 (`state_actions_programs.ts:100` `dmgResult`) 실제 crit 시에만 `critical_hit` spawn. ② `damage >= 10` 하드코딩 제거 또는 상대 비율 (`damage >= maxHp * 0.15`) 로 교체 | "CRIT" 표시가 **진짜 치명타** 와 일치. 체감 신뢰도 상승 | M | ⚠️ **밸런스 영향 가능** — crit 판정 기준이 바뀌면 승률 이동. 실측 필수 | `web/tests/combat_engine.test.ts` + `npm run balance` before/after. `web/tests/design_conformance.test.ts` 의 crit 상수 assertion (`design_conformance.test.ts:43`) 유지 |
| **P9** | **게임 루프 도입 (rAF 기반 지속 갱신)** | 지금 `draw()` 는 입력 이벤트에서만 호출된다 (`main.ts` 내 `draw()` 64개 호출 전부 입력 핸들러 내부). 결과적으로 (a) VFX 인스턴스가 `advanceVfxListBy` 로 진행 (`main.ts:1516-1519`) 되려면 **다음 입력이 있어야** 진행된다 → 아이스킬 160ms 애니메이션이 **한 프레임만 보이고 멈춘다**. (b) `AUTO_ATTACK_INTERVAL_MS` 타이머도 돌지 않는다. `setInterval`/`requestAnimationFrame` 는 `input/gamepad.ts:117` 와 `core/performance.ts:11` 뿐 | `Game` 에 `requestAnimationFrame` 루프 추가. 루프 안에서: ① VFX advance + render ② 시간 기반 상태 tick (적 idle tick 은 P7 과 함께) ③ `draw()` 호출. **입력 이벤트는 상태를 바꾸기만 하고** 렌더는 루프가 담당. rAF 은 탭 비활성 시 자동 정지하므로 별도 pause 처리 불필요 | **모든 애니메이션이 실제로 재생된다.** 지금은 P2/P3 을 붙여도 "깜빡하고 멈춘다". **이 제안이 선행되지 않으면 P1-P6 의 효과가 절반 이하** | **L** | 루프 도입은 전부(레이아웃/오디오/테스트)에 영향. 과도한 CPU 점유 위험 → dirty-flag 로 렌더 스킵. `performance.ts` 이미 FPS 계측기가 있으니 재활용 | 기존 vitest 는 동기식이므로 영향 없음 (reducer 는 여전히 sync). `web/e2e/game.spec.ts` 의 진행 스텝 통과 확인. `npm run typecheck` + `npm test` |
| **P10** | **reduced-motion / 색각 이상 / 텍스트 스케일 지원** | `core/accessibility.ts` 의 `reducedMotion` / `highContrast` / `prefersReducedMotion()` 가 **소비자 0건** (`accessibility.ts:20-28`). `PALETTE` 는 단일 고정 15색 (`palette.ts:12-48`). ADR-0196 은 4모드 색각 palette 를 ADR-0183 으로 상속했다고 명시 (`0196:11-24`) 인데 web 구현 없음. 폰트/셀 크기는 breakpoint 로만 결정 (`canvas.ts:25-44`) | ① `settings.ts` 의 `SettingsField` 에 `reduced_motion` / `colorblind` / `text_scale` 추가 (`renderer/settings.ts:59-78`) — 필드 추가는 국소적. ② `accessibility.ts` 의 `prefersReducedMotion()` 을 `renderer/canvas.ts` 가 참조해 shake/flash 길이를 0 으로. ③ `PALETTE` 에 colorblind 변형 테이블 추가 + `resolveColorHint` 가 현재 팔레트를 받아 분기 (`palette.ts:55-62` — 이미 함수 형태라 변경점 작음). ④ 셀 크기에 `textScale` 배수 | 광각색覺 조건 플레이어 포함. reduced-motion 은 전정증 민감 플레이어 보호. **P1 의 shake 를 안전하게 만들 수 있는 선행 조건** | M | 팔레트 변형은 모든 화면의 looks 를 바꿈 → 회귀 스크린샷 다수 필요. `web/tests/accessibility.test.ts` 갱신 | `web/tests/accessibility.test.ts` (존재) 에 소비 wiring 테스트. `web/e2e/layout.spec.ts` 에 3모드 팔레트 스크린샷. `docs/design/ui-intuition-evaluation.md:29-33` 의 A3 (touch target) 항목도 같은 시점에 |
| **P11** | **온보딩: 튜토리얼 자동 표시 + 전투 첫 30초 안내** | 튜토리얼은 메뉴에서 **수동 진입만** 가능 (`main.ts:1155-1159`, `menu_main.ts:53`). `renderer/tutorial.ts:9` 주석은 "Shown once on first boot" 라고 적혀 있지만 **코드는 first-boot 시 호출되지 않는다** — 부목석과 주석이 불일치. combat 첫 진입에서 "1-9 를 눌러 프로그램 사용" 을 알려주는 오버레이가 없다 | ① `boot()` 에서 `localStorage` 의 `wetrun_tutorial_completed` 미존재 시 tutorial 화면 자동 진입. ② combat 첫 진입 시 1회성 인라인 힌트 ("1-9: USE PROGRAM / TAB: TARGET") 를 `renderGrid` 하단에 2줄 표시 (`main.ts:1690` message 줄 근처). ③ 기존 `tutorial.ts` 의 6단계는 그대로 활용 (combat 조작 항목은 이미 `tutorial.ts:51-59` 에 있음) | 첫 30초의 "뭘 해야 하는지" 모호함 해소. 신규 플레이어 이탈률 저하 | **S** | 튜토리얼 자동 진입이 기존 e2e 를 깨뜨릴 수 있음 (메뉴에서 바로 전투로 가정하는 스펙) — `web/e2e/game.spec.ts` / `menu.spec.ts` 확인 필요 | `web/e2e/smoke.spec.ts` + `game.spec.ts` 통과. 튜토리얼 자동 진입 시 e2e 가 tutorial 을 통과해야 하는 helper 추가 필요 |
| **P12** | **터치: 프로그램 버튼 즉시 반응 + 탭 피드백** | 터치 프로그램 버튼은 `pointerdown` 으로 즉시 발화 (`touch.ts:180-186`) — 지연 문제는 없다. 그러나 ① 버튼 눌림 피드백은 CSS `:active` 뿐이고 **게임 내 반응 표시는 없음** ② 가상 패드 D-pad 버튼 크기가 12-14vw (`touch.ts:38-55`) 로 물리적으로는 크지만 `docs/design/ui-intuition-evaluation.md:29-33` 가 지적한 "격자 셀 크기 대비" 문제는 남아 있음 ③ `pointerdown` handler 안에 `e.preventDefault()` 가 있고 250ms debounce 가 있어 (`touch.ts:258-264`) 연타 시 입력 누락 가능 | ① 터치 입력 경로에서 `handleProgramButton` (`main.ts:1586-1605`) 이 **VFX spawn 후 즉시 렌더** 되도록 — 현재는 `draw()` 호출하지만 VFX advance 가 다음 입력에 의존 (P9 의존). ② `lastFire` debounce 를 250ms → 120ms 로 완화 (터치 연타 = 의도된 rapid play 가능). ③ 버튼 `:active` 뿐 아니라 `:focus-visible` 스타일 추가 | 모바일 플레이의 입력 체감 개선 | S | debounce 완화는 오입력 증가 가능 | `web/tests/touch.test.ts` (존재) + `web/e2e/touch_input.spec.ts` 에 3연타 → 3회 발화 검증 |
| **P13** | **오디오: 볼륨 ducking + 레이어 + 마스터 볼륨** | `playSfx()` 는 Howl 을 그대로 재생 (`audio/manager.ts:432-456`) — pitch/rate 변조 없음. BGM 과 SFX 가 같은 볼륨軸을 쓰며 (각각 0.4 / 0.6 기본, `manager.ts:74-75`), combat 중 SFX 가 BGM 위로 묻힐 수 있음. 또한 마스터 볼륨 슬라이더가 없다 (BGM/SFX 2개만, `renderer/settings.ts:59-78`) | ① `playSfx()` 에 `rate` 파라미터 추가 (`howler` 의 `rate()` 지원) → 동일 SFX 를 0.92~1.08 사이로 변조해 반복 지루함 감소. ② combat phase 진입 시 BGM 볼륨을 20% duck (단 `crossfadeTo` 와 `fadeOutAndStop` 에 이미 fade 인프라 있음 — `manager.ts:238-303`). ③ settings 에 master 볼륨 1개 추가. ④ 명중 시 `COMBAT_HIT` + 짧은 고음 레이어 동시 재생 (P5 와 결합) | combat 의 사운드가 "층" 을 가짐. 반복 SFX 지루함 감소 | M | ducking 이 BGM 볼륨 영속 값(`wetrun_audio_bgm_volume`)을 덮으면 재접속 시 설정이 오염됨 — duck 는 **곱연산 오프셋** 으로 처리하고 저장하지 말 것. `rate` 변조는 Howler 기본값 변경이므로 되돌리기 쉬움 | `web/tests/audio.test.ts` + `web/tests/howler_integration.test.ts` 에 rate/duck 검증. `web/e2e/settings.spec.ts` 통과 |
| **P14** | **상태 effect HUD 전면 개편 (타겟별 + 턴 잔여)** | `formatStatusGlyph` 은 **5종만** 지원하고 (`vfx.ts:80-86`), `main.ts:1497` 이 `statusEffects.map(e => e.kind)` 로 **타겟 구분 없이** 전부 합쳐서 **활성 타겟 옆에만** 표시한다 (`main.ts:1736-1747`). 플레이어 자신에게 붙은 `burn`/`bleed` 와 ICE 에 붙은 `burn` 이 **같은 칸**에 섞인다. ADR-0226 의 `shield`/`regen`/`powered` 는 아예 매핑이 없어 **표시되지 않는다** | ① `STATUS_GLYPHS` 를 `player` / `ice` 2축으로 확장 (`vfx.ts:80-86`). ② `main.ts:1497` 에서 `(kind, target)` 쌍을 전달하고, 타겟별 glyph 을 **각 ICE 행 옆** 과 **플레이어 HP 행 옆** 에 각각 렌더. ③ `remaining` 턴 수를 glyph 옆에 소괄호로 표기 (`[B2]` = 2턴 남음). ④ ADR-0226 4종 glyph 추가 | "누가 무엇에 걸렸는가" 가 즉시 판독됨. 특히 자가 `burn` 이 방어 타이머와 별개로 표시되면 자기 관리 플레이 가능 | M | `web/tests/vfx.test.ts:149-161` 의 "5 glyph" assertion 갱신 필수. HUD 폭 초과 가능 (`formatStatusGlyph` 가 항상 붙으므로) | `web/tests/vfx.test.ts` 갱신 + `web/tests/status.test.ts` 에 target 분리 검증. `web/tests/layout.test.ts` 에 HUD 폭 회귀 |
| **P15** | **전투 진입 연출 (`ice_intro`) + 결과 페이로드 (`data_acquired`)** | `ice_intro` ("INCOMING: <ICE>" + scanning 배너) 렌더러가 완성돼 있으나 미스폰 (U3). `data_acquired` (gold particle burst) 도 미스폰 — matrix 진입 시 `state_actions_phases.ts:76-79` 는 `room_flash` 와 `data_acquired` 를 **둘 다** spawn 하는데, `data_acquired` 는 스폰된다 — 이건 정상. 문제는 전투 진입 시 `ice_intro` 가 없다는 것. 그 결과 전투 시작이 **메뉴 → 전투 화면 즉 전환**으로 느껴진다 | ① `state_actions_phases.ts` 의 combat 진입 분기에서 `import_vfx("ice_intro", iceName, durationForKind("ice_intro"))` 1건 추가. ② `ice_death` 를 승리 전이에 추가 (`state_actions_programs.ts:347` 의 `victory` 옆). ③ 두 개 모두 **렌더러 존재** → 스키마/렌더러 수정 0 | 전투 시작과 종료에 "막" 이 생김. 러닝의 호흡이 생김. 특히 `ice_intro` 의 scanning 배너가 "적 탐지" 라는 서사적 텍스트 → 깁슨 톤과 정합 | **S** | `ice_intro` 는 640 ms (`state_helpers.ts:229-230`) 동안 메시지 줄을 덮으므로, 전투 첫 메시지를 가릴 수 있음 — `main.ts:1690` 의 message 줄과 겹치지 않게 배치 필요 | `web/tests/combat_vfx.test.ts` 에 "combat 진입 시 `ice_intro` spawn" 검증. `web/e2e/boss_phase_vfx.spec.ts` 와 병행 |

### 2.1 축별 커버리지 확인

| 축 | 처리 |
| --- | --- |
| hit feedback | P1 (shake/hit-stop), P2 (`player_hit` 배선), P3 (데미지 넘버), P5 (SFX 레이어) |
| kill / victory payoff | P2 (`ice_death`/`defeat` 배선), P15 (`ice_intro`/`ice_death`), P4 (승리 보상 로그) |
| player damage reaction | P1 + P2 (`player_hit`), P5 (`DAMAGE` SFX), P10 (reduced-motion) |
| turn cadence / responsiveness | P9 (rAF 루프) — ⚠️ **루프가 없음은 이것 없이는 해결 안 됨**, P7 (입력 유휴 압박, ⚠️밸런스), P11 (첫 30초) |
| audio richness | P5 (피격 SFX), P13 (ducking/rate/레이어) |
| readability / information | P4 (combat log), P14 (상태 effect HUD) |
| status-effect legibility | P6 (ADR-0226 VFX), P14 (glyph + target 분리) |
| onboarding / first-run | P11 (튜토리얼 자동 + combat 힌트) |
| mobile / touch | P12 (터치 반응/디바운스) — ⚠️ P9 의존 (VFX advance) |
| accessibility | P10 (reduced-motion/색각/텍스트 스케일) |

---

## 3. 즉시 실행 가능한 상위 3개

### TOP 1 — P2: 10개 미배선 VFX 배선 (`player_hit` 포함)

- **가치**: 최대. 렌더러·스키마·duration·테스트가 **이미 전부 있다**. 새 코드는 "spawn 한 줄" 뿐이다.
- **첫 단계 (file-level)**:
  1. `web/src/core/state_actions_combat.ts` — `processEnemyTurns` 의 `playerHp` 감소 지점 2곳 (`:255` 스킬 피해, `:320` auto-attack) 바로 뒤에 `import_vfx("player_hit", "", durationForKind("player_hit"))` 를 추가하고, 반환对象的 `vfxInstances` 배열에 합친다 (현재 `:421-434` 의 boss-phase 조건부 분기 옆에).
  2. `web/src/core/state_actions_combat.ts` — player HP 0 분기 (`:382-400`) 에 `import_vfx("defeat", "", durationForKind("defeat"))` 추가.
  3. `web/src/core/state_actions_combat.ts` — boss phase 전환 로그 (`:172-175`) 옆에 `ice_death` 는 두지 말고, 승리 분기(`state_actions_programs.ts:347`) 에 `ice_death` 를 나란히 둔다.
  4. `web/src/core/ice_combat_effect_apply.ts` — `IceEffectOutcome` 에 `vfx: ReadonlyArray<CombatVfxInstance>` 필드 추가 후, 4개 적용 함수가 자기 종류의 kind (`shield`/`heal`/`regen`/`buff`) 를 채운다. **이 4개 렌더러는 이미 있다** (`combat_vfx_render_combat.ts:34-76`, `:84-98`, `:306-317`).
  5. `web/src/core/state_actions_combat.ts` — `applyIceNonDamageEffect` 호출부 (`:265-277`) 의 `outcome.vfx` 를 `state.vfxInstances` 에 합친다.
- **테스트 추가**: `web/tests/status.test.ts` (player_hit spawn), `web/tests/ice_combat_effects.test.ts` (shield/heal/regen/buff VFX spawn).
- **밸런스 영향**: **없음 (pure-additive)**. 순수 표시 계층이며 어떤 수치 계산에도 관여하지 않는다. `AUTO_ATTACK_INTERVAL_MS` (`combat_engine.ts:10`) 도, `ice_scaling.ts` 의 calibration 배열도 건드리지 않는다. → **ADR-0229 drift check 불필요.**
- **선행 의존성**: P9(루프) 없이는 "스폰은 되지만 한 프레임만 보인다". 그래도 **스폰 배선 자체는 P9와 독립**이므로 지금 바로 ship 가능.

### TOP 2 — P9: 게임 루프 도입 (rAF 기반 지속 갱신)

- **가치**: 이 문서에서 **다른 모든 제안의 전제 조건**. VFX 는 `advanceVfxListBy` (`main.ts:1518`) 로만 진행하는데, 이 호출은 `draw()` 안에 있고 `draw()` 는 입력에서만 불린다 → **모든 애니메이션이 정지 상태로 보인다**.
- **첫 단계 (file-level)**:
  1. `web/src/main.ts` — `Game` 클래스에 `private rafId: number | null` 필드 + `private startLoop()` / `private loop(now: number)` 메서드 추가. `start()` (`:1552-1554`) 에서 `startLoop()` 호출.
  2. `loop()` 안에서 (a) delta 계산 → (b) `this.state.vfxInstances = advanceVfxListBy(..., deltaMs)` → (c) **변화가 있을 때만** `this.draw()`.
  3. 입력 핸들러 (`main.ts:348-453`) 의 `this.draw()` 호출은 **상태 변경 직후 1회**로 유지 — 루프가 다음 프레임에 이어받는다. (즉시 반응성은 유지되고, 애니메이션만 루프가 돌게 된다.)
  4. `stop()` (`:1607-1616`) 에 `cancelAnimationFrame` 추가.
  5. **성능 안전장치**: `core/performance.ts` 의 FPS 계측기를 재활용해, frame 시간이 임계(예: 100ms)를 넘으면 **VFX advance 를 건너뛰고** 렌더만 한다.
- **테스트 추가**: vitest 는 동기식이므로 영향 없음 (reducer 는 여전히 sync). e2e `web/e2e/game.spec.ts` / `smoke.spec.ts` 진행 스텝 통과 확인 + `npm run typecheck` + `npm test`.
- **밸런스 영향**: **없음 (pure-additive)** — 단, 이 제안 안에서 적 idle tick (P7) 을 함께 넣지 않을 것. **P7 은 별도 ADR 로 분리**하고, P9 는 렌더 루프만 담당한다. → **ADR-0229 drift check 불필요.**
- **주의**: rAF 은 백그라운드 탭에서 자동으로 멈춘다. 일시정지(pause) 화면과 탭 전환을 구분할 필요는 없다.

### TOP 3 — P4: combat log 확장 (`state.message` 1줄 → 최근 N줄)

- **가치**: "무엇이 일어났는지" 를 놓치지 않게 하는 최소한의 정보 설계. **현재 적 한 턴에 발생하는 이벤트 중 마지막 1건만 남는다** — `state_actions_combat.ts:417-420`. ADR-0226 의 shield/heal/regen/buff 메시지와 ADR-0228 의 `CRITICAL` 마커가 **대부분의 경우 사라진다**.
- **첫 단계 (file-level)**:
  1. `web/src/core/types.ts` — `GameState` 에 `readonly combatLog: ReadonlyArray<string>` 추가 (기본 `[]`).
  2. `web/src/core/state.ts` — `makeInitialState` (`:113` `vfxInstances: []` 인접) 에 `combatLog: []` 추가.
  3. `web/src/core/state_actions_combat.ts` — `processEnemyTurns` 의 `logMessages` 배열 전체를 `combatLog` 로 보존 (`:417-420` 의 `logMessages[logMessages.length-1]` 는 `message` 로 유지 — 기존 동작 유지). cap 8.
  4. `web/src/core/state_actions_programs.ts` — `useProgram` 의 message (`:361-363`) 를 combatLog 앞쪽에 prepend.
  5. `web/src/core/state.ts` — `buildHudLines` (`:179-210`) 의 `lines.push("", state.message)` (`:208`) 를 `lines.push("", ...state.combatLog.slice(0, 4))` 로 교체 — 최근 4줄 표시.
  6. `web/src/core/state.ts` — `stateToSaveSlot` / `slotToGameState` 에 combatLog 를 넣을지 결정 — **넣지 않는 게 안전** (저장 스키마 bump 회피). 리로드 시combatLog 는 비어 있고 다시 채워진다.
- **테스트 추가**: `web/tests/sound_triggers.test.ts` 의 상태전이 기반 패턴을 그대로 사용 — "적 턴에 2개 이상 이벤트가 발생하면 combatLog 에 2개가 남는가" 검증. `web/tests/layout.test.ts` 에 좁은 폭(40 cols) 회귀 추가.
- **밸런스 영향**: **없음 (pure-additive, 표시 전용)**. 어떤 수치 계산에도 관여하지 않음. → **ADR-0229 drift check 불필요.**
- **리스크**: HUD 줄 수 증가 → 좁은 화면에서 잘림. `renderHUD` 의 overflow 가드 (`renderer/hud.ts:69`) 를 combat HUD 경로에도 적용하거나, 40-col 화면에서는 2줄로 축소할 것.

### 3.1 밸런스 영향 요약 (ADR-0229 drift check 필요 여부)

| 제안 | 밸런스 영향 | ADR-0229 §A1 drift check |
| --- | --- | --- |
| P1 shake/hit-stop | 없음 (연출 전용) | 불필요 |
| **P2 VFX 배선** | **없음 (pure-additive)** | **불필요** |
| P3 데미지 넘버 | 없음 (표시 전용) | 불필요 |
| **P4 combat log** | **없음 (pure-additive)** | **불필요** |
| P5 SFX 레이어 | 없음 (표시 전용) | 불필요 |
| P6 ADR-0226 가시화 | 없음 (표시 전용) | 불필요 |
| **P7 입력이유시 tick** | **있음 — 승률 이동 가능** | **필수** (`npm run balance` before/after ±3pp) |
| **P8 crit 임계값 연동** | **있음 — crit 판정 변경** | **필수** |
| **P9 rAF 루프** | **없음 (렌더 전용)** | **불필요** (P7 을 별도 분리할 것) |
| P10 accessibility | 없음 | 불필요 |
| P11 온보딩 | 없음 | 불필요 |
| P12 터치 반응 | 없음 | 불필요 |
| P13 오디오 ducking | 없음 | 불필요 |
| P14 상태 HUD | 없음 | 불필요 |
| P15 전투 진입 연출 | 없음 | 불필요 |

---

## 4. 측정 방법 (Verification)

각 제안의 효과를 **관찰 가능한 신호**로 바꾼다. 측정 불가능한 제안은 taste-only 로 명시한다.

### 4.1 정량 측정 가능

| 제안 | 측정 방법 | 도구 | 기준선 |
| --- | --- | --- | --- |
| P1 shake/hit-stop | (a) shake offset 이 `AsciiRenderer.render` 에 전달되는지 unit 검증 (b) shake 지속 시간이 100-200ms 범위인지 | `web/tests/vfx_ms_timing.test.ts` 확장 (기존 ms 정밀 만료 테스트 패턴) | shake duration 100-200ms (설계 문서 `animations.md:171-174`) |
| P2 VFX 배선 | `processEnemyTurns` 후 `state.vfxInstances` 에 `player_hit` 가 존재하는가 (kind 단위 assert) | `web/tests/status.test.ts` + `web/tests/ice_combat_effects.test.ts` | 스폰 kind 집합 — 현재 17종 → 27종 |
| P3 데미지 넘버 | 특정 tick 에 `-N` 문자열이 grid 에 존재하는가 | `web/tests/combat_vfx_v2.test.ts` 패턴 | damage > 0 일 때 넘버 1개 |
| P4 combat log | 한 턴에 N개 이벤트 발생 시 combatLog 길이 = min(N, cap) | `web/tests/sound_triggers.test.ts` 패턴 | cap 8 |
| P5/P13 SFX | 플레이어 HP 감소 시 `SFX_IDS.DAMAGE` 호출 횟수 | `web/tests/audio.test.ts` + `web/e2e/sound_triggers.spec.ts` | HP 감소 1회 = DAMAGE 1회 |
| P7/P8 밸런스 | `npm run balance -- --runs 100` before/after, opening deck 6 grade + PPL 6 grade | `web/scripts/balance_harness.ts` (balance_sim.ts 는 real reducer 를 구동) | ADR-0229 §A1: ±3pp 창. 초과 시 되돌리거나 re-baseline |
| P9 루프 | idle 상태에서 1초 동안 VFX 인스턴스가 만료되는가 (현재는 만료 안 됨) | e2e: 전투 진입 후 VFX spawn → 대기 → 소멸 확인 | 만료율 100% |
| P10 accessibility | reduced-motion ON 일 때 shake offset 이 0 인지 | `web/tests/accessibility.test.ts` (현재 helper 단위만) | shake = 0, 팔레트 4모드 |
| P12 터치 | 250ms 내 3연타 → 3회 발화 | `web/tests/touch.test.ts` + `web/e2e/touch_input.spec.ts` | 3/3 |
| P14 상태 HUD | (a) player glyph 과 ice glyph 이 다른 위치에 렌더되는가 (b) ADR-0226 4종 glyph 이 표시되는가 | `web/tests/vfx.test.ts` (갱신) + `web/tests/status.test.ts` | target 분리 + 9종 glyph |

### 4.2 스크린샷 (Playwright)

`web/e2e/demo-screenshots.spec.ts` 가 기존 스크린샷 하네스를 제공하므로 이를 확장한다.

| 캡처 대상 | 시나리오 | 확인 포인트 |
| --- | --- | --- |
| 명중 순간 | 프로그램 사용 직후 frame | `HIT! -N` + 데미지 넘버 위치/색 |
| 플레이어 피격 | 적 턴 직후 frame | `!! DAMAGE !!` + shake offset |
| ICE 방패 | shield 스킬 후 frame | 방패 브래킷 + shield glyph |
| 승리 | ICE 처치 직후 frame | `ICE OFFLINE` 배너 + victory art |
| 첫 진입 | combat 첫 frame | `INCOMING: <ICE>` 배너 |

### 4.3 Playtest (사람 관점)

`docs/playtest/PLAYTEST_GUIDE.md` 의 시나리오 표에 **feel 전용 시나리오**를 추가한다.

| ID | 시나리오 | 성공 기준 |
| --- | --- | --- |
| **TF-01** | 더미 ICE 3기를 상대하며 1턴에 5개 프로그램 사용 | "명중이 눈으로 확인된다" 를主观 평가 5인 중 4인 이상 |
| **TF-02** | HP 50% 에서 방패를 가진 ICE와 전투 | "적의 방패 상태를 알아챘다" 5인 중 4인 이상 |
| **TF-03** | 30초 무입력 관찰 | "시간이 흐르는 느낌이 없다" 를 지적하는 비율 — 개선 전후 비교 |
| **TF-04** | 전투 진입 → 첫 프로그램 사용까지 | "뭘 해야 하는지 즉시 알겠다" 5인 중 4인 이상 |

### 4.4 taste-only (측정 불가능 — 명시)

아래는 **정량 검증이 불가능**하며, playtestCollective 의견만으로 판단한다. 지표로 제시하지 않는다.

| 제안 | 이유 |
| --- | --- |
| P13 BGM ducking 의 정확한 비율 (20% vs 30%) | "긴장감" 은 측정 불가능. 값 선택은 청각 취향 |
| P1 shake 강도 (1px vs 2px) | 동일 |
| P3 데미지 넘버 색상 (흰색 vs 노랑) | `animations.md:39`/`:62` 의 설계 값을 따르는 것이基準이나, "더 좋은 색" 은 취향 |
| P4 combat log 표시 줄 수 (3 vs 4 vs 8) | 정보량 vs 화면 점유 trade-off |
| P11 튜토리얼 문구 | 오브젝션 지향 copywriting |

---

## 5. 하지 말 것 (Rejected Ideas)

검토했지만 **기각한** feel 아이디어와 그 이유.

| # | 아이디어 | 기각 이유 |
| --- | --- | --- |
| R1 | **래스터/스프라이트 그림자, 파티클 엔진 도입** | ASCII/Canvas2D 를 의도적으로 유지한다 (`AGENTS.md` §4, `docs/design/pillars.md` P5 "깁슨 사이버펑크 미학"). 래스터화는 저사양 기기 대응과 일관된 미학을 동시에 깨뜨린다. **추천하지 않음.** |
| R2 | **WebGL / Three.js 전환** | Canvas2D ASCII 는 80×50 = 4000 cell 이며 GPU 필요성이 없다. 전환은 "feel" 개선이 아니라 엔진 교체이며, 범위를 완전히 벗어난다 |
| R3 | **히트스톱으로 실제 적 턴을 지연** | 적 턴 지연은 **밸런스 변경**이며 ADR-0229 drift 대상이다. 플레이어가 "기다림"을 Experience 하는 것은 좋은 feel 이 아니라 latency 다. 히트스톱은 **연출 전용(50ms 이내)** 로 제한할 것 |
| R4 | **연속 입력 큐 +hold-to-repeat** | "빠른 플레이" 를 위해 입력 버퍼를 넣으면 accidental play 가 늘고, 턴 구조(프로그램 1회 = 턴 1회)의 규칙성을 해친다. `keyboard.ts:72` 의 현재 repeat 처리는 modifier 만 걸러내는 정도가 적절하다. 숫자키 repeat 차단은 P6/P12 참고 (별도 판단) |
| R5 | **전투 중 실시간 타이머/스톱워치 UI** | 2000 ms `AUTO_ATTACK_INTERVAL_MS` (`combat_engine.ts:10`) 는 enemy turn 의 단위이지 플레이어 타이머가 아니다. 플레이어가 시간을 재는 게임이 아니다. UI 는 "모래를 새는 것" 이 아니라 **"결정"** 에 집중해야 한다 (P7 과 P11 이 이 축을 다룬다) |
| R6 | **damage number 를 떠오르는 스프라이트로 (Web Animations API)** | canvas 밖 DOM 레이어를引入하면 레이어 동기화 문제 + 폰트 스타일 불일치 + 접근성(readability) 저하. ASCII grid 위의 텍스트 이동이 이 미학에 맞다 (P3) |
| R7 | **화면 전체 flash 를 히트마다** | 깁슨 미학의 "깔끔한 미래" 와 충돌하고, 반복 플레이에서 피로 유발. `animations.md:176-179` 의 screen flash 는 **치명타 한정** 이며, 그 설계 의도를 유지한다 |
| R8 | **음향 파일 추가 (새 WAV 녹음)** | LFS 정책 (`ADR-0200`) 과 파일 크기. `web/public/sounds/sfx/` 에 이미 24개 SFX 파일이 있으며 **미사용 파일이 3개** (`damage.wav` / `attack.wav` / `ice_break.wav` — `audio/manager.ts:39-41`) 있다. 새 파일보다 **기존 파일 배선** 이 우선 (P5) |
| R9 | **BPM 동기화된 BGM (beat-matched)** | BGM 은 5개 무한 루프 WAV 다 (`public/sounds/bgm/`). 템포 메타데이터가 없고, combat cadence 가 프로그램 1회 = 1턴 인 가변 구조이므로 beat sync 가 의미를 잃는다 |
| R10 | **플레이어 HP 0 도달 시 confirm 게이트 (" REALLY? ")** | flatline 은 **즉각** 이 되어야 한다 (Pillar 3 "The Flatline" 의 무게, `animations.md:133-154`). 게이트는 긴장감을 *지연* 시킨다. 게이트 대신 **연출(2.4s death animation + 정적)** 로 무게를 준다 — 단 M1(루프) 이 선행되어야 |
| R11 | **명중 시 카메라 줌 (scale)** | Canvas2D ASCII 에서 셀 크기 변경은 `resizeGrid` 를 유발해 레이아웃 재계산 + `watchLayout` 과 상호작용한다 (`core/layout.ts:103-120`). 16ms 프레임마다 레이아웃을 흔드는 것은 성능·안정성 리스크가 크고, ASCII 폰트가 확대되면 그리드가 깨진다 |
| R12 | **모든 상태에 VFX 를 다 배선 (27/27)** | P2 는 배선 비용이 낮은 것만 우선한다. `ice_intro` / `ice_death` / `defeat` / `heal` / `shield` / `buff` / `debuff` / `stun` / `counter` / `lifesteal` / `status_apply` / `player_hit` 이 12종 남는다. 이 중 `counter` / `lifesteal` 은 **플레이어 측 스킬에서 spawn 하는 effect** 인데, 현재 플레이어 스킬 시스템에 그 개념이 없다 — 배선하려면 먼저 스킬 발생 지점이 필요하다. 스킬 없는 곳에 VFX 를 배선하면 "unwired" 의 반대편("연결될 대상 없는 배선")이 된다. **P15 로 12개 중 4개만 선취** 하고 나머지는 각 스킬 구현 시점에 함께 배선한다 |
| R13 | **`ice_hit` 를 "일반 = 무채색" 규칙에 맞게 회색으로 변경** | `animations.md:38` 은 **자동 공격**을 "일반"으로 부른다. 플레이어가 *선택한 프로그램* 은 `docs/design/systems/combat.md:53-57` 기준 "스킬" 이므로 무채색이 아니다. `ice_hit` 의 빨간 flash 는 선별된 프로그램 결과이므로 유지한다. 단 `attack` kind 의 `YELLOW_AMBER` (`combat_vfx_render_combat.ts:28`) 는 설계 문서와 어긋나므로 **문서 정합 차이로 기록** — 이건 feel 개선이 아니라 사양 정리다 |
| R14 | **`state.message` 를 없애고 HUD 만으로 대체** | `message` 는 combat log 의 "가장 최근 1줄" 로 유지한다 (P4). 제거하면 기존 테스트 (`web/tests/empty_deck_feedback.test.ts` 등) 다수가 깨지고, "Hand empty" 같은 즉시 피드백 경로가 사라진다 |

---

## 부록 A — 27개 VFX kind 도달 가능성 매트릭스

`web/src/data/effects.d.ts:43-71` 의 canonical 27종 중 런타임에 도달 가능한 것.

| 상태 | kind 수 | 목록 |
| --- | --- | --- |
| ✅ spawn 가능 (literal) | 11 | `ice_hit`, `critical_hit`(조건부), `dot`, `boss_phase_transition`, `victory`, `jackin_glitch`, `jackout_whiteout`, `room_flash`, `data_acquired` |
| ✅ spawn 가능 (`pickProgramVfxKind` 경유) | 8 | `attack`, `heavy_attack`, `pierce`, `multi_hit`, `shield`, `regen`, `buff`, `detect` |
| ❌ **스폰 호출 0건** | **10** | `heal`, `debuff`, `stun`, `counter`, `lifesteal`, `player_hit`, `status_apply`, `ice_intro`, `ice_death`, `defeat` |

- `pickProgramVfxKind` 의 반환 집합: `web/src/core/state_helpers.ts:58-70`
- literal spawn 지점: `web/src/core/state_actions_programs.ts:196`, `:216`, `:229`, `:230`, `:235`, `:249`, `:347` / `web/src/core/state_actions_combat.ts:87`, `:425` / `web/src/core/state_actions_phases.ts:76`, `:79`, `:157`, `:330`

## 부록 B — 이 제안서가 건드리지 않은 것

- `web/` 아래 **어떤 파일도 수정하지 않았다** (이 문서가 유일한 산출물)
- `docs/wiki/decisions/` 의 ADR **무수정**
- `log.md` , `web/src/data/ice_types.json` , `web/src/core/ice_scaling.ts` **무수정**
- `ice_scaling.ts` 의 calibration 배열 은 P7/P8 에서만 간접 영향 (P7/P8 는 본 proposal 에서 **제안만** 하고 구현하지 않음)
- `docs/design/` 의 기존 문서 **무수정** (본 문서 신규 생성만)

---

## 부록 C — 진행 상태 (2026-10-27)

> 본 제안서는 **research-only** 로 작성됐다. 아래는 이후 실제 반영 내역이다 (추적용).

### ✅ 반영 완료 (ADR-0231)

| 제안 | 반영 내용 | 밸런스 |
|---|---|---|
| **P2** | 미배선 VFX **7종 배선** (`player_hit`×2 · `defeat` · `ice_death` · `shield`/`heal`/`regen`/`buff`) — 기존 렌더러만 사용, 신규 kind·renderer 0 | 0.0pp |
| **P4** | `GameState.combatLog` (newest-first · cap 8) + `buildHudLines` 최근 4줄, `message` 시맨틱 불변, `SaveSlot` 미포함 | 0.0pp |
| **P9** | `main.ts` **rAF 렌더 루프** (`startLoop`/`loop`, `MAX_FRAME_ADVANCE_MS=100`, `draw(persist)`) | 0.0pp |

**구현 중 발견된 결함 2건**(ADR-0231 기록): ① `import_vfx` 가 `Math.random` 을 소비 → VFX spawn 추가 시 **시드 RNG 스트림이 이동**해 밸런스가 움직임 → `import_vfx_deterministic`(RNG 무소비) 신설로 0.0pp 복원 ② 루프의 초당 60회 `draw()` → **초당 ~60회 IDB autosave** → `draw(persist)` 로 루프만 차단.

### ✅ 반영 완료 — tier 2 (ADR-0232)

| 제안 | 반영 내용 | 밸런스 |
|---|---|---|
| **P1** | canvas 레벨 화면 흔들림 (2px · 200ms · 20/27Hz, `player_hit` 만) + **wall-clock 기반 히트스톱** (40ms, 연출 전용) | 0.0pp |
| **P3** | 부유 데미지 숫자 — `normal`(소형·백색) / `skill`(대형·황색) / `critical`(금색 `✦-N✦`), 그리드 내 렌더 | 0.0pp |
| **P5** | SFX 레이어링 — 플레이어 피격 `DAMAGE`(신규) · ICE 피격 `COMBAT_HIT`+`ATTACK` · ICE 파괴 `ICE_BREAK` | 0.0pp |

**구현 중 발견·수정된 결함 3건** (ADR-0232 기록): ① ADR-0231 의 `import_vfx_deterministic` **모노토닉 카운터가 reducer 순수성을 깨뜨림** (fuzz test 가 HEAD 에서 ~50% flaky) → FNV-1a content hash 로 교체 ② `COMBAT_HIT` **dead path** (`state.ice.hp` 는 init 후 불변 → 한 번도 발화 안 함) → `iceRoster` 기반 `pickCombatSfxLayers` 로 실제 배선 ③ **히트스톱 데드락** (hold 를 동결 대상인 `elapsedMs` 에서 파생 → >25fps 에서 VFX 영구 동결) → wall-clock deadline + identity 기반 arming.

### ✅ 반영 완료 — P6 · P13 · P14 (ADR-0233 / ADR-0234)

| 제안 | 반영 내용 | 밸런스 |
|---|---|---|
| **P13** | 오디오 ducking + SFX rate 변조 + **마스터 볼륨** (`playSfx(id, {rate?, duck?})` 옵션, 전투 임팩트 SFX 만 BGM duck — 곱셈 오프셋이라 영속 안 됨) | 0.0pp |
| **P6** | ADR-0226 효과 가시화 — **glyph 전용** (VFX 경로는 ADR-0231 에서 이미 live), `STATUS_GLYPHS` 5→8종 (`shield`/`regen`/`powered`; `heal` 은 비영속이라 glyph 없음) | 0.0pp |
| **P14** | 상태 effect HUD **타겟별 분리** (플레이어 vs 각 ICE 슬롯) + `[GLYPH<잔여턴>]` — `renderGrid` 를 `renderer/combat_grid.ts` 로 추출해 테스트 가능화 | 0.0pp |

### ✅ 반영 완료 — P11 · P12 · P15 (ADR-0235)

| 제안 | 반영 내용 | 밸런스 |
|---|---|---|
| **P11** | 첫 부팅 시 튜토리얼 **자동 표시** (기존 `wetrun_tutorial_completed` 플래그 재사용) + 전투 진입 힌트 `1-9: USE PROGRAM` (신규 `core/onboarding.ts`) | 0.0pp |
| **P12** | 터치 프로그램 버튼 **인게임 눌림 피드백** (월-클럭 deadline, 400ms) + `window.wetrun` 글로벌 의존 제거 → 직접 콜백 (신규 `core/touch_feedback.ts`) | 0.0pp |
| **P15** | 전투 진입 연출 — 미스폰 `ice_intro` 배너 1건 스폰 (**`import_vfx_deterministic`**, RNG 무소비) | 0.0pp |

### ⏸ 미착수

**P10** (accessibility — reduced-motion / 색각 palette / 텍스트 스케일, L 비용) · **P7 · P8** (밸런스 접촉 → ADR-0229 §A1 전후 측정 필요).

### ⚠️ 환경 관찰 (2026-10-27)

- **무료 모델 rate-limit**: 구현 작업 중 `openrouter/google/gemma-4-26b-a4b-it:free` 가 upstream rate-limit 으로 실패 → fallback 모델로 재시도. opencode Zen 도 **설정 화이트리스트가 무료 모델 4종뿐**이라 실제 호출이 `429 FreeUsageLimitError` → **유료 모델 활성화 또는 OpenCode Go 필요**.
- **RNG-중립 규칙**: 신규 VFX spawn 은 반드시 `import_vfx_deterministic` 사용(위 결함 ① 참조).
