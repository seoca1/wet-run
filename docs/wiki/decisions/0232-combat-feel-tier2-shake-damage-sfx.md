# ADR-0232: Combat-feel tier 2 반영 — 캔버스 흔들림 + 부유 데미지 숫자 + SFX 레이어링

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — built-but-unwired dead path, ADR-0216/0219/0222/0223/0224/0225/0226/0227/0228/0229/0230/0231 sibling)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0195 — Accepted ADR Implementation Status Workflow](./0195-adr-implementation-workflow.md), [ADR-0196 — Accessibility Colorblind State Alignment](./0196-accessibility-colorblind-state-alignment.md), [ADR-0210 — Combat VFX Effect Schema](./0210-combat-vfx-effect-schema.md), [ADR-0226 — Non-damaging ICE 스킬 효과를 구현한다](./0226-non-damaging-ice-skill-effects-implemented.md), [ADR-0229 — Grade 난이도 곡선 재기준화](./0229-grade-curve-rebaseline.md), [ADR-0231 — Combat-feel top-3 반영](./0231-combat-feel-top3-vfx-log-raf.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-27 에 결정·구현·검증까지 완료되었다.
>
> **이 ADR 은 밸런스를 바꾸지 않는다.** 12개 grade 전부 **0.0pp drift** —
> ADR-0229 baseline 과 **byte-identical** 하다. §A1 은 발동하지 않았다.
>
> **이 ADR 의 진짜 내용은 "무엇을 넣었느냐" 가 아니라 "구현 중에 발견한
> 세 개의 실제 결함" 이다.** ① reducer 가 **순수하지 않았다** (ADR-0231 의
> 자체 구현 결함), ② **죽은 SFX 경로** — `COMBAT_HIT` 가 애초에 울리지
> 않았다, ③ **hit-stop deadlock** — 영구 VFX freeze. 셋 다 아래에 기록한다.

## 컨텍스트 (Context)

`docs/design/combat-feel-and-interaction-proposal.md` (§2) 의 tier 2 —
P1 / P3 / P5 를 반영한다. ADR-0231 이 top-3 (P2 / P4 / P9) 을 처리한 뒤
남은 항목 중 **밸런스 영향이 없는 것** 만 골랐다.

| 제안 | 무엇이 없었나 | 근거 |
| --- | --- | --- |
| **P1** | 캔버스 레벨 화면 흔들림 + 히트스톱 | `player_hit` VFX 는 **격자 문자만** 흔들었고 canvas 자체는 한 번도 움직이지 않았다. `AsciiRenderer.render()` 에 offset 인자가 없었다. 히트스톱 개념 자체가 없었다 (§1.3 M2 / M4) |
| **P3** | 부유 데미지 숫자 | 데미지 표시가 **고정 위치 `HIT! -N` 한 줄**뿐이었다. `docs/design/systems/animations.md` 는 색상·크기 분기를 명시하지만 구현이 없었다 (§1.3 M3) |
| **P5** | 명중 SFX 레이어링 + 플레이어 피격 SFX | `SFX_IDS.DAMAGE` / `ATTACK` / `ICE_BREAK` 는 **정의돼 있고 WAV 파일도 디스크에 있었는데 아무도 재생하지 않았다** (§1.2 U13) |

**P7 (idle-turn pressure) 과 P8 (crit threshold coupling) 은 여전히
의도적으로 하지 않았다.** 이 둘은 **전투 밸런스를 건드린다** — 별도 ADR
로 분리해야 하고 ADR-0229 §A1 drift check 가 필요하다.

### 이 ADR 의 질문

**세 가지를 순수 추가(pure-additive)로 구현하면 되는가?** 답은 "세
항목의 표면적 구현은 그렇지만, 그 과정에서 **세 개의 실제 결함** 이
드러난다" 다. 하나는 **남의 ADR 의 결함**(ADR-0231) 이었고, 둘은
**이 ADR 가 새로 만든 결함** 이었다.

## 결정에 이르게 된 근거

### P1 — 캔버스 흔들림 + 히트스톱

- `web/src/renderer/screen_shake.ts` (신규) — 순수 함수만.
  `shakeOffsetFor` (`:76`) 은 2px peak · 200ms · 20/27Hz 의 감쇠 진동이며,
  **부호를 보존하는 반올림**(`roundWithSign`) 을 쓴다 — 그냥
  `Math.round` 하면 진동 중간에 `(0,0)` dead frame 이 생겨 화면이 200ms
  중 절반 동안 멈춘 것처럼 보인다. `shakeStateFor` (`:117`) 는 **기존
  `player_hit` VFX 인스턴스**에서 오프셋을 유도한다 — **새 spawn site 가
  없다** 그래서 RNG draw 가 늘지 않는다.
- `web/src/renderer/canvas.ts:114` — `render()` 가 optional `offset`
  파라미터를 얻었다. `ctx.save()` / `translate()` / `restore()` 로 **격자와
  HUD 가 함께** 이동한다 (`:118-122`) — shake 가 "정적 프레임 안에서
  ASCII 가 떨리는 것" 이 아니라 "뷰포트가 움직이는 것" 으로 읽히기 위해.
- 히트스톱은 **연출 전용** 이며 **적 턴을 절대 지연하지 않는다**
  (제안 §R3). reducer · 게임 클럭 · enemy turn 은 건드리지 않는다.

### P3 — 부유 데미지 숫자

- `web/src/renderer/floating_damage.ts` (신규) — 순수 geometry + 색상/크기
  분기. `animations.md` 를 따른다: `normal` = 작고 흰색 (`:38-39`),
  `skill` = 크고 노란색 (`:60-61`), `critical` = 금색 `✦-N✦`
  (`:108-112`). `floatingDamageKindFor` (`:164`) 가 VFX kind → branch
  매핑을 담당한다.
- 숫자는 **격자 안으로** 그려진다 (`renderFloatingDamage` `:136`) — 제안
  §R6 은 DOM/스프라이트 기반 숫자를 **기각** 했고, ASCII grid 위의 텍스트
  이동이 이 미학에 맞다.

### P5 — SFX 레이어링 + 플레이어 피격음

- `web/src/core/combat_sfx.ts` (신규) — 순수
  `pickCombatSfxLayers(previous, next)` (`:39`). 이전/다음 상태 쌍에서 재생할
  SFX id 목록을 결정한다: 플레이어 HP 감소 → `DAMAGE` (이전에는 **무음**),
  ICE HP 감소 → `COMBAT_HIT` + `ATTACK` 레이어, ICE HP 0 도달 → `+ ICE_BREAK`.
- `web/src/renderer/combat_overlay.ts` (신규) — shake 오프셋과 부유 숫자를
  VFX grid 위에 합성한다 (`overlayShake` `:51`, `composeFloatingDamage` `:63`).

## 구현 중 발견한 세 개의 실제 결함

> **이 절이 이 ADR 의 실체다.** 세 결함 모두 "구현하면 드러나는" 종류이며
> **제안 문서에는 존재하지 않는다.** 하나는 **남의 ADR 의 결함** —
> ADR-0231 이 만든 `import_vfx_deterministic` 이 reducer 를 순수하지 않게
> 만들었다.

### 1. reducer 가 순수하지 않았다 — ADR-0231 의 자체 구현 결함

**`import_vfx_deterministic` 가 모듈 레벨 단조 counter 를 썼다:**
`id: nextDeterministicVfxId++` (`web/src/core/state_helpers.ts` — ADR-0231
이 추가한 helper). 결과적으로 **동일한 `applyAction` 호출 두 번이 서로
다른 VFX id 를 만들었다** → `tests/property_reducer_fuzz.test.ts` 의
결정성 invariant 가 깨졌다.

**재현 (HEAD 기준, `src/` 를 HEAD 로 되돌리고 8회 실행): 4/8 회 실패.**

**원인 격리:** 두 번의 `applyAction` 결과의 유일한 차이는 `player_hit` VFX
의 `id` (`1` vs `2`) 였다. RNG 를 소비하는 `import_vfx` 의 id
(`11704754`, `405521689`, `466232633`) 는 동일했고, vfx id 를 정규화하면
상태 전체가 동일했다.

**해결:** id 를 **내용 hash** 로 바꿨다 — 31-bit FNV-1a over (kind, payload,
payloadNum, duration). `deterministicVfxId`
(`web/src/core/state_helpers.ts:68`). **여전히 RNG draw 0건** 이고, 이제
**호출 순서와 무관**하다. "가장 최근 인스턴스" 로직은 `id` 비교에서 **배열
순서** 로 바꿨다 — `composeCombatVfx` 가 원래부터 배열 순서로 합성하기
때문이다.

> **이 결함은 P1/P3/P5 와 무관하게 pre-existing 이었다.** 본 ADR 은 그
> 사실을 기록하고 고쳤을 뿐이다. 고치지 않으면 `npm test` 가 flaky 로 남는다.

### 2. 죽은 SFX 경로 — `COMBAT_HIT` 는 애초에 울리지 않았다

pre-existing `COMBAT_HIT` dispatch 는 `state.ice.hp` 를 읽었는데, **reducer
는 `iceRoster` 만 쓴다.** `state.ice` 는 `makeInitialState` 이후 갱신되지
않는다. probe 로 실측한 결과:

```
after confirms: state.ice.hp=165 roster=165
turn 1: state.ice.hp=165 roster=148 player.hp=87
turn 2: state.ice.hp=165 roster=139 player.hp=74
...
turn 7: state.ice.hp=165 roster=0   player.hp=0
```

`state.ice.hp` 가 165 에 고정된 채 roster 는 165 → 0 으로 떨어졌다. **즉 그
`COMBAT_HIT` 는 한 번도 울리지 않았다** (제안 §1.2 U13 의 다른 사례 — 정의는
있었으나 배선되지 않은 경로).

`pickCombatSfxLayers` 는 `iceRoster` 를 읽으므로 **죽은 경로를 실제로
배선한다.** 이중 재생 방지를 위해 죽은 branch 의 중복 `COMBAT_HIT` 호출은
제거했다 (제안 P5 의 "이중 재생 금지" 요구).

### 3. hit-stop deadlock — 오케스트레이터 리뷰가 발견했다

첫 구현은 hold 조건을 **`elapsedMs < HIT_STOP_MS`** 로 derives 했고, hold
자신이 **`elapsedMs` 를 멈추는** 함수였다:

```
const holdMs = hitStopMsFor(before);
const advanceMs = holdMs > 0 ? Math.max(0, deltaMs - holdMs) : deltaMs;
```

`deltaMs = 16.7` (60fps) 에서 `advanceMs = max(0, 16.7 - 40) = 0`. **즉 25fps
이상의 어떤 프레임 레이트에서도 `elapsedMs` 가 한 번도 움직이지 않아 hold
가 풀리지 않고, 인스턴스가 영원히 만료되지 않았으며, `changed = holdMs > 0`
이 매 프레임 redraw 를 강제했다.**

```
frame 1:   holdMs=40 advanceMs=0.00 elapsedMs=0
frame 60:  holdMs=40 advanceMs=0.00 elapsedMs=0
frame 600: holdMs=40 advanceMs=0.00 elapsedMs=0
```

**해결 — 벽시계(wall clock) deadline.** hold 는 절대 VFX 자신의 `elapsedMs`
로 판정하지 않는다. `hitStopDeadlineFor`
(`web/src/renderer/screen_shake.ts:209`) 와 `hitStopActiveAt` (`:235`) 가
**절대 벽시계 timestamp** 로 deadline 을 관리한다.

**arming 트리거는 identity 기반이다** — 이전 프레임 목록에 없던
`player_hit` 이 **새로 등장**했을 때만 `nowMs + HIT_STOP_MS` 로 arming.
`elapsedMs` 기반 트리거는 **또 다른 deadlock** 을 만든다: hold 중에는
`elapsedMs` 가 **0 에 머무르므로** 매 프레임 re-arm 되어 deadline 이 계속
앞으로 밀린다 — 같은 영구 freeze 가 다른 모양으로 나타난 것이다. (작업자가
실제로 겪었고 자체 테스트가 잡아낸 결함이다.)

**해제 확인 (frame rate 별):**

| frame rate | 이전 | 이후 | hold 프레임 |
| --- | --- | --- | --- |
| 60fps | **만료 안 됨** (600+ 프레임 고정) | **frame 15 에 만료** | 3 |
| 30fps | 만료 안 됨 | frame 9 에 만료 | 2 |
| 240fps | 만료 안 됨 | frame 59 에 만료 | 10 |
| 20fps (기존 deadlock 임계 아래) | 동작 | 동작 — frame 5 에 만료 | 1 |

## 고려한 옵션

### Option 1 — 세 가지를 순수 추가로 구현하고 부수 효과까지 해결 (선택)

- **설명**: P1 / P3 / P5 를 구현한다. 순수 표시/오디오 계층이며 reducer·
  게임 클럭·enemy turn 은 건드리지 않는다. 구현 중 드러난 세 결함도 함께
  고친다.
- **장점**: **밸런스가 증명 가능하게 무변경이다** (12 grade 전부 0.0pp).
  세 결함이 문서화되어 재발을 막는다. reducer 순수성이 복구된다.
- **단점**: 결함 1 수정은 **P1/P3/P5 범위를 넘어선다** — pre-existing flake
  를 고치지 않으면 `npm test` 가 0 failures 를 보장하지 못한다.
- **Pillar 정합**: P5 (The Style) ✅ — 피격 피드백이 화면과 소리로 동시에
  온다. P1 (The Flatline) ✅ — 죽은 SFX 경로가 실제로 배선된다.

### Option 2 — 세 가지만 구현하고 부수 효과는 무시

- **설명**: 제안 문서의 스펙대로만 구현한다.
- **단점**: **reducer 가 순수하지 않은 채 남는다** — `npm test` 가 flaky 로
  남고 (§결함 1), 죽은 `COMBAT_HIT` 가 계속 죽어 있고 (§결함 2), hit-stop 은
  영구 freeze 다 (§결함 3).
- **Pillar 정합**: 실패 (증거 없이 flake 와 freeze 가 남는다).

### Option 3 — P7 / P8 까지 함께 구현

- **설명**: tier 2 에 idle-turn pressure 와 crit threshold coupling 을
  추가한다.
- **단점**: **전투 밸런스를 건드린다** — 턴 구조와 crit 확률이 바뀐다.
  ADR-0229 §A1 drift check 가 필수고, re-baseline 가능성이 있다.
- **Pillar 정합**: 실패 (범위 확장 + 별도 결정 필요).

## 추천 (Recommendation)

**Option 1.** 세 항목 모두 순수 표시/오디오 계층이며 밸런스 수치에 관여하지
않는다. 발견된 세 결함은 **문서화하고 고치는 쪽이 낫다** — 그대로 두면
flaky test 와 죽은 SFX 와 영구 freeze 가 남는다.

**Option 3 은 명시적으로 배제한다.** P7 / P8 은 밸런스를 건드리는 변경이므로
ADR-0229 §A1 아래에서 별도 ADR 로 다뤄야 한다.

## 사용자 결정 (Decision)

**2026-10-27 — tier 2 (P1 / P3 / P5) 를 구현하되, 구현 중 발견된 세 개의
부수 효과를 함께 해결하기로 결정했다.** 구현 완료·검증됨.

- [x] **Option 1 — tier 2 구현 + 부수 효과 3건 해결** — **채택·구현됨**
- [ ] Option 2 — 세 가지만 구현 (부수 효과 무시)
- [ ] Option 3 — P7 / P8 까지 함께 구현

### 결정된 내용

1. **P1 — 캔버스 흔들림 + 히트스톱.** `screen_shake.ts` (신규) 의 순수 함수 +
   `canvas.ts` 의 `render()` offset 파라미터. 히트스톱은 **연출 전용**, 적
   턴을 지연하지 않는다 (제안 §R3).
2. **P3 — 부유 데미지 숫자.** `floating_damage.ts` (신규) 의 순수 geometry +
   색상/크기 분기. 격자 안으로 그린다 (제안 §R6 준수).
3. **P5 — SFX 레이어링 + 플레이어 피격음.** `combat_sfx.ts` (신규) 의 순수
   결정 함수 + `main.ts` 의 dispatch 배선.
4. **VFX spawn 은 RNG-neutral 유지** — 새 spawn site 없음. `player_hit` 의
   `payloadNum` 만 채웠고 `import_vfx_deterministic` 은 **RNG draw 0건** 이므로
   draw count 는 변하지 않는다.
5. **reducer 는 순수해야 한다** — `import_vfx_deterministic` 의 id 를 content
   hash 로 바꿨다 (RNG 0 draw 유지, 호출 순서 무관).
6. **`GameState` 는 안 건드린다** — shake 오프셋 · 부유 숫자 · 활성 사운드는
   모두 **렌더/오디오 계층** 에 있다.
7. **P7 / P8 은 하지 않는다.** 나머지 제안도 하지 않는다.
8. **기존 ADR 은 하나도 수정하지 않았다.** Accepted 결정은 immutable 이다
   (`AGENTS.md` §6). 관계는 이 ADR 에 기록했다.

## 결과 (Consequences)

### 긍정적 영향

- **화면이 실제로 흔들린다** — 이전에는 `player_hit` 가 격자 문자만 흔들었고
  canvas 는 정지해 있었다. 이제 grid 와 HUD 가 함께 이동한다.
- **피격이 눈으로 읽힌다** — 부유 데미지 숫자가 색상·크기로 분기한다 (일반
  흰색 작게 / 스킬 노란색 크게 / 치명타 금색).
- **플레이어가 맞았다는 소리가 난다** — 이전에는 무음이었다. 명중은 2음으로
  겹쳐 임팩트 두께가 생긴다.
- **죽은 `COMBAT_HIT` 가 실제로 울린다** — `iceRoster` 를 읽는다.
- **reducer 가 다시 순수하다** — 결정성 invariant 가 복구되고 `npm test` 가
  flaky 가 아니다.
- **밸런스가 증명 가능하게 무변경이다.**

### 부정적 영향 / 수용한 비용

- **결함 1 수정은 본 ADR 의 원래 범위를 넘어선다.** pre-existing flake 였지만,
  고치지 않으면 "0 failures" 를 보장할 수 없었다.
- **VFX id 는 이제 content hash 다.** 동일 content 의 spawn 은 id 를 공유한다.
  `CombatVfxInstance.id` 를 읽는 로직은 **없고** (identity key 뿐이다),
  렌더링은 배열 순서로 합성하므로 무해하다.
- **hit-stop 은 실제 턴 지연을 만들지 않는다.** "멈춘 느낌" 은 VFX advance 만
  늦춘 결과다. 더 강한 임팩트는 별도 ADR 이 필요하다.
- **loop 의 runtime 동작은 자동화 테스트로 덮이지 않는다** (아래 「검증 한계」).

### 후속 항목

1. **남은 제안** — P6 (ADR-0226 효과의 VFX 밖 가시성), **P7 (idle-turn
   pressure — ADR-0229 §A1 필요)**, **P8 (crit threshold coupling — §A1
   필요)**, P10 (accessibility wiring), P11 (onboarding), P12 (touch feedback),
   P13 (audio ducking), P14 (status HUD), P15 (`ice_intro` / `data_acquired`).
2. **`import_vfx` / `import_vfx_ms` 를 content hash 로** — 이 둘은 여전히 RNG
   를 소비하고 `Math.random` 기반 id 를 쓴다. 고치는 것 자체가 calibration
   baseline 을 움직이므로 — 미래의 ADR 가 의도적으로 re-baseline 하면서 해야 한다.
3. **loop 의 runtime coverage** — e2e 가 돌아갈 수 있게 되면 (예: Playwright
   frame-timing assertion) 추가한다.
4. **reduced-motion 과의 결합** — P10 이 들어오면 `prefersReducedMotion()` 으로
   shake 길이를 0 으로 만들어야 한다.

### 관계 — immutable 규칙 준수

ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 / 0228 / 0229 /
0230 / 0231 은 Accepted 이며 immutable 하므로 **하나도 수정하지 않았다**
(`AGENTS.md` §6). 관계는 이 ADR 에 기록했다.

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:

**신규 파일 — 7개 (소스 4 + 테스트 3)**

- `web/src/renderer/screen_shake.ts` — **P1.** `SHAKE_MAGNITUDE_PX = 2`
  (`:23`), `SHAKE_DURATION_MS = 200` (`:26`), `HIT_STOP_MAX_MS = 50` (`:29`),
  `HIT_STOP_MS = 40` (`:32`), `SHAKE_FREQ_X/Y` (`:59-60`), `shakeOffsetFor`
  (`:76`), `shakeStateFor` (`:117`), `HitStopInstance` (`:149`), `hitStopMsFor`
  (`:167`), `hitStopDeadlineFor` (`:209`), `hitStopActiveAt` (`:235`).
- `web/src/renderer/floating_damage.ts` — **P3.** `FloatingDamageKind` (`:26`),
  `FLOATING_DAMAGE_RISE_ROWS = 4` (`:36`), `floatingDamageFor` (`:85`),
  `floatingDamageRows` (`:114`), `renderFloatingDamage` (`:136`),
  `floatingDamageKindFor` (`:164`).
- `web/src/renderer/combat_overlay.ts` — **P1+P3.** `PLAYER_DAMAGE_ANCHOR`
  (`:35`), `iceDamageAnchor` (`:44`), `overlayShake` (`:51`),
  `composeFloatingDamage` (`:63`).
- `web/src/core/combat_sfx.ts` — **P5.** `pickCombatSfxLayers` (`:39`).
- `web/tests/screen_shake.test.ts` — **39** 개 `it()` (shake 상수 · 결정성 ·
  RNG-neutral · `hitStopDeadlineFor` · `hitStopActiveAt` · loop 시뮬레이션
  회귀 테스트).
- `web/tests/floating_damage.test.ts` — **28** 개 `it()` (geometry · 색상/크기
  분기 · VFX kind 매핑 · grid overlay · RNG-neutral).
- `web/tests/combat_sfx.test.ts` — **15** 개 `it()` (SFX id 매핑 · 레이어링
  규칙 · WAV 파일 on-disk 검증 · RNG-neutral).

**변경된 파일 — 5개 (소스 4 + 테스트 1)**

- `web/src/main.ts` — **P1 + P3 + P5 배선.** import (`:30-37`),
  `hitStopDeadlineMs` / `previousVfxInstances` 필드 (`:322`, `:325`), 키보드
  경로 SFX dispatch (`:451`), 전투 render path 의 `composeFloatingDamage` +
  `overlayShake` + `offset` 전달 (`:1560-1567`), `startLoop()` 의 deadline 리셋
  (`:1598-1599`), `loop` 의 벽시계 hold (`:1629-1646`), 터치 경로 SFX dispatch
  (`:1697`), `stop()` 의 리셋 (`:1710-1711`).
- `web/src/renderer/canvas.ts` — **P1.** `render()` 의 optional `offset`
  파라미터 (`:114`) + `ctx.save()` / `translate()` / `restore()` (`:118-122`).
- `web/src/core/state_helpers.ts` — **결함 1 수정.** `deterministicVfxId` (`:68`)
  — 31-bit FNV-1a content hash. `import_vfx_deterministic` (`:107`) 이 그 id 를
  쓴다 (`:117`). **RNG draw 는 여전히 0건.**
- `web/src/core/state_actions_combat.ts` — `player_hit` spawn ×2 가 `payloadNum`
  으로 데미지를 담는다 (`:268` 스킬 피해, `:344` auto-attack).
  `import_vfx_deterministic` 이므로 **draw count 불변**.
- `web/tests/state_helpers.test.ts` — `import_vfx_deterministic` 회귀 테스트
  4건 (`:195` describe: 동일 spawn → 동일 id · 다른 content → 다른 id · RNG
  0 draw · id 0 아님).

**테스트**

- `npm test` — **130 files / 3088 tests, 0 failures.** (ADR-0231 시점 127
  files / 3002 tests → **+3 files, +86 tests**.)
- 신규 assertion 은 **변경 전 반드시 실패함을 확인했다.** 복원은 **손으로**
  했다 (Python 패치로 파일 복사) — `git checkout` / `git stash` 는 쓰지 않았다.
  - deadlock 회귀: 원본 구현(`hitStopMsFor` + `max(0, deltaMs − holdMs)`) 을
    되살리면 **5건 실패** (`expected false to be true` = 만료 안 됨, `frozen at
    30fps`, `expected 120 to be less than or equal to 6` = hold 가 120 프레임 지속).
  - `elapsedMs === 0` re-arm 변종: **10건 실패** (`expected 1040 to be +0`,
    `expected 120 to be less than or equal to 6`).
  - `hitStopDeadlineFor` 유닛: **10건 실패**.
  - 신규 모듈 3개는 모듈 부재로 suite 자체가 실패했다.

**게이트**

- `npx tsc --noEmit` — **0 errors.**
- `npx eslint src --ext ts` — **0 errors** (pre-existing warning 1건은
  `web/src/input/keyboard.ts:14` — 손대지 않았다).
- `npm run build` — **성공.**

**밸런스 — 12 grade 전부 0.0pp drift (byte-identical)**

`npm run balance` (opening deck, 100 runs/mission):

| grade | win-rate | ADR-0229 baseline |
| --- | --- | --- |
| g1 | 100.0% | ✓ 일치 |
| g2 | 88.6% | ✓ 일치 |
| g3 | 73.1% | ✓ 일치 |
| g4 | 39.3% | ✓ 일치 |
| g5 | 35.7% | ✓ 일치 |
| g6 | 0.0% | ✓ 일치 |

`npm run balance -- --deck ppl` (100 runs/mission):

| grade | win-rate | ADR-0229 baseline |
| --- | --- | --- |
| g1 | 100.0% | ✓ 일치 |
| g2 | 77.9% | ✓ 일치 |
| g3 | 99.6% | ✓ 일치 |
| g4 | 84.8% | ✓ 일치 |
| g5 | 44.4% | ✓ 일치 |
| g6 | 28.3% | ✓ 일치 |

mean-turns · mean-HP-end · p5/p95 를 포함한 **모든 컬럼** 이 baseline 과
byte-identical 하다.

**RNG draw count — HEAD 와 독립적으로 확인.** seeded PRNG 를 계수하는 probe
로 전투별 `Math.random` draw 수를 측정했다:

- **`aleph_fragment` seed 777: HEAD 62 draws → 현재 62 draws** — 동일.
- **catalog 전체 (53 missions): HEAD 2382 draws → 현재 2382 draws** — 동일.
- per-mission 승패 · 턴 수 · HP 끝값 지문도 전부 동일 (`diff` 로 확인).

**검증 한계 (정직하게 명시한다)**

- **vitest 는 `main.ts` 의 rAF loop 을 실행하지 않는다.** `main.ts` 는 import
  시점에 self-boot 하고, vitest 는 동기적이다. deadlock 회귀 테스트는 loop 의
  hit-stop 블록을 **시뮬레이션** 해서 (실제 `hitStopDeadlineFor` /
  `hitStopActiveAt` / `advanceVfxListBy` 로) 검증한다 — **`Game.loop` 자체를
  실행한 것이 아니다.** `main.ts` 의 배선 (previous frame 목록 전달,
  `startLoop` / `stop` 리셋) 은 **코드 읽기로만** 검증했다.
- **실제 canvas 렌더링을 실행하지 않았다.** `AsciiRenderer.render()` 의 새
  `offset` 파라미터가 2D context 를 실제로 translate 하는지는 **관찰된 사실이
  아니다** — 검증된 것은 오프셋 **계산** 뿐이다.
- **Playwright e2e 를 실행하지 못했다** — 브라우저와 live URL 이 필요하다.
- **화면 위 애니메이션을 관찰하지 못했다.** shake 가 "임팩트로 읽히는가",
  데미지 숫자가 "읽히는가" 는 **taste 판단** 이다 (제안 §4.4 가 이 분류를
  명시한다). 구현은 설계 문서의 명시 값을 따랐지만 **느낌은 미검증** 이다.
- **오디오를 듣지 못했다.** WAV 파일이 존재하고 유효한 RIFF 인 것까지 확인했지만,
  2음 레이어가 "임팩트 두께" 로 들리는지는 미검증이다.
- **LSP diagnostics 를 사용할 수 없었다** (daemon socket unreachable). 그래서
  **repo 가 자체로 mandate 한 gate 인 `tsc --noEmit` (strict) 이 권위** 다.

**Notes**:

- **기존 assertion 을 하나도 약화·skip·삭제하지 않았다.** 추가만 했다.
- **`import_vfx` / `import_vfx_ms` 는 여전히 RNG 를 소비한다** — 이 ADR 은 그
  두 함수를 건드리지 않았다 (draw 횟수와 위치가 그대로다).
  `import_vfx_deterministic` 만 id 산출 방식을 바꿨고 **draw 0건은 유지** 했다.
- **`GameState` 는 변경하지 않았다.** shake 오프셋 · 부유 숫자 · 활성 사운드는
  모두 렌더/오디오 계층에 있다. `core/` 에 새 모듈이 추가됐지만
  (`combat_sfx.ts`) **reducer 를 바꾸지 않았다.**
- **`web/src/data/effects.json` / `effects.d.ts` 는 미변경** — kind 추가 0건이므로
  schema bump 가 필요 없었다.
- **`web/src/data/ice_types.json`, `missions.json`, `programs.json` — 미변경.**
  calibration 배열 (`ENCOUNTER_HP_BY_GRADE`, `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`)
  도 미변경.
- **`Game/wet_run/log.md` 는 수정하지 않았다** (오케스트레이터 소유).
- **ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 / 0228 / 0229 /
  0230 / 0231 을 포함한 기존 ADR 은 하나도 수정하지 않았다.**
- **임시 파일을 남기지 않았다** (검증용 probe 는 모두 삭제).
- **re-calibration 은 하지 않았다.** ADR-0229 §A1 미발동 (grade 이동 0) →
  **re-baseline 불필요.** §B hard invariant 전부 성립, §A4 해당 없음 (calibration
  배열 미변경).

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `docs/wiki/decisions/0232-combat-feel-tier2-shake-damage-sfx.md` — **신규**
  (이 ADR)
- `docs/wiki/decisions/README.md` — 0232 행 신규 (0231 행 다음, 6-컬럼 동일
  format)
- `web/src/renderer/screen_shake.ts` — **신규** (P1)
- `web/src/renderer/floating_damage.ts` — **신규** (P3)
- `web/src/renderer/combat_overlay.ts` — **신규** (P1+P3 합성)
- `web/src/core/combat_sfx.ts` — **신규** (P5)
- `web/src/main.ts` — P1 + P3 + P5 배선 + 결함 3 수정
- `web/src/renderer/canvas.ts` — `render()` offset 파라미터
- `web/src/core/state_helpers.ts` — `import_vfx_deterministic` id 산출 방식
  (content hash)
- `web/src/core/state_actions_combat.ts` — `player_hit` ×2 의 `payloadNum`
- `web/tests/` — 4개 파일, 신규 assertion 86건 (추가만)

### 이번 결정으로 변경되지 않은 항목

- `web/src/core/state.ts`, `types.ts`, `combat_engine.ts`, `ice_ai.ts`,
  `ice_scaling.ts`, `ice_crit.ts`, `ice_skills.ts`, `state_actions.ts`,
  `state_actions_phases.ts`, `state_actions_programs.ts`,
  `ice_combat_effects.ts`, `ice_combat_effect_apply.ts`, `combat_models.ts`,
  `boss_phases.ts` — **전부 미변경**
- `web/src/data/effects.json`, `effects.d.ts`, `ice_types.json`,
  `missions.json`, `programs.json` — **미변경**
- `GameState` / `SaveSlot` 인터페이스 — **미변경** (schema bump 없음)
- `web/src/audio/manager.ts` — **미변경** (`SFX_IDS` 에 이미 있던 3개 id 를
  배선했을 뿐이다)
- `Game/wet_run/log.md` — 오케스트레이터 소유
- ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 / 0228 / 0229 /
  0230 / 0231 — **미수정** (immutable)

## 관련 결정

- ADR-0229 (Grade 난이도 곡선 재기준화) — **drift policy 의 owner.** 이 ADR 의
  0.0pp drift 로 §A1 미발동, re-baseline 불필요. §B hard invariant 전부 성립.
  **ADR-0229 는 수정하지 않았다** (immutable).
- ADR-0231 (Combat-feel top-3 반영) — **직전 sibling.** P2/P4/P9 를 처리했다.
  이 ADR 이 **그 ADR 이 만든 결함 1** (`import_vfx_deterministic` 의 counter) 을
  고쳤다. **ADR-0231 은 수정하지 않았다** (immutable) — 관계는 이 ADR 에 기록했다.
- ADR-0226 (Non-damaging ICE 스킬 효과를 구현한다) — ADR-0231 과 함께 그
  효과들을 보이게 만든 owner. 이 ADR 은 **손대지 않았다.** **ADR-0226 은
  수정하지 않았다** (immutable).
- ADR-0210 (Combat VFX Effect Schema) — 27개 kind canonical taxonomy 의 owner.
  이 ADR 은 kind 를 **추가하지 않았다.** **ADR-0210 은 수정하지 않았다**
  (immutable).
- ADR-0196 (Accessibility Colorblind State Alignment) — 접근성. **손대지
  않았다.** shake 길이를 reduced-motion 에 연동하는 것은 P10 의 후속 항목이다.
  **ADR-0196 은 수정하지 않았다** (immutable).
- ADR-0195 (Accepted ADR Implementation Status Workflow) — 이 ADR 의
  Implementation Status 형식의 owner. **수정하지 않았다** (immutable).
- ADR-0110 (모듈 사이즈 정책) — 신규 모듈 4개가 모두 100–300 LOC 권장 범위 안이다
  (65 / 156 / 181 / 240 LOC). `main.ts` 는 1931 → 1991 LOC 로 60 LOC 증가.
  **ADR-0110 은 수정하지 않았다** (immutable).
- `docs/design/combat-feel-and-interaction-proposal.md` — 이 ADR 이 그 tier 2
  (P1 / P3 / P5) 를 반영한다. 나머지 제안은 미반영.

## 변경 이력

- 2026-10-27: Draft 작성 (combat-feel 제안 문서 tier 2 — P1 캔버스 흔들림 +
  히트스톱, P3 부유 데미지 숫자, P5 SFX 레이어링)
- 2026-10-27: **Accepted (Option 1 — tier 2 구현 + 부수 효과 3건 해결)** —
  구현 완료·검증. P1 은 `screen_shake.ts` (순수 shake + 벽시계 hit-stop) +
  `canvas.ts` offset, P3 은 `floating_damage.ts` (순수 geometry + 색상/크기 분기),
  P5 는 `combat_sfx.ts` (순수 SFX 결정) + `main.ts` 배선. **구현 중 세 개의
  실제 결함 발견** — ① **reducer 비순수성** (ADR-0231 의 단조 counter → content
  hash 로 해결, HEAD 에서 ~50% flaky 였음), ② **죽은 `COMBAT_HIT` 경로**
  (`state.ice.hp` → `iceRoster`, 실측으로 165 고정 확인), ③ **hit-stop deadlock**
  (오케스트레이터 리뷰가 발견 — `elapsedMs` 파생 hold → 벽시계 deadline,
  identity 기반 arming). **12 grade 전부 0.0pp drift**, RNG draw count HEAD 와
  일치 (62 = 62, catalog 2382 = 2382). `npm test` 130 files / 3088 tests
  0 failures (+3 files / +86 tests). **P7 / P8 및 나머지 제안은 미반영** —
  re-calibration 은 하지 않았다.
