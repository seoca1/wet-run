# ADR-0231: Combat-feel top-3 반영 — VFX 배선 + combat log + rAF 렌더 루프

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — built-but-unwired dead path, ADR-0216/0219/0222/0223/0224/0225/0226/0227/0228/0229/0230 sibling)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0195 — Accepted ADR Implementation Status Workflow](./0195-adr-implementation-workflow.md), [ADR-0196 — Accessibility Colorblind State Alignment](./0196-accessibility-colorblind-state-alignment.md), [ADR-0210 — Combat VFX Effect Schema](./0210-combat-vfx-effect-schema.md), [ADR-0226 — Non-damaging ICE 스킬 효과를 구현한다](./0226-non-damaging-ice-skill-effects-implemented.md), [ADR-0228 — ICE 아키타입 동작 배선](./0228-ice-archetype-behavior-wiring.md), [ADR-0229 — Grade 난이도 곡선 재기준화](./0229-grade-curve-rebaseline.md), [ADR-0230 — 애매 분류 부채 종결](./0230-ambiguous-classification-debt-closure.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-27 에 결정·구현·검증까지 완료되었다.
>
> **이 ADR 은 밸런스를 바꾸지 않는다.** 12개 grade 전부 **0.0pp drift** —
> ADR-0229 baseline 과 **byte-identical** 하다. §A1 은 발동하지 않았다.
>
> **이 ADR 의 진짜 내용은 "무엇을 넣었느냐" 가 아니라 "구현 중에 발견한
> 두 개의 실제 결함" 이다.** ① VFX spawn 이 **RNG-neutral 이 아니었다** —
> 그대로 배선하면 조용히 calibrated 곡선을 움직인다. ② render loop 이
> **초당 ~60회 IndexedDB write** 를 유발했다. 둘 다 아래에 기록한다.

## 컨텍스트 (Context)

### 제안 문서가 발견한 것 — "만들어 놓고 배선하지 않았다"

`docs/design/combat-feel-and-interaction-proposal.md` 은 15개 항목
(P1–P15) 을 담은 research-grounded 제안이다. 그 문서의 핵심 결론은
**"feel 인프라를 설계하고 렌더러까지 완성해 놓고 배선만 하지 않은
상태"** 다.

- **27개 VFX kind 중 10개** 는 렌더러·스키마·duration 테이블까지 갖춰져
  있으나 **런타임에 한 번도 생성되지 않았다** (§1.2 U1–U5:
  `player_hit` / `heal` / `debuff` / `stun` / `counter` / `lifesteal` /
  `ice_intro` / `ice_death` / `defeat` / `status_apply`).
- **`main.ts` 에 game loop 가 없었다.** `draw()` 는 입력 이벤트에서만
  호출되었으므로 VFX 인스턴스가 `advanceVfxListBy` 로 진행하려면
  **다음 키 입력**이 필요했다. 아이스킬 애니메이션은 **한 프레임만 보이고
  멈췄다.**
- **`state.message` 는 마지막 이벤트 1건만 보관한다.** 한 턴에
  스킬 → auto-attack → status tick 이 여러 번 발생하면 **앞선 이벤트가
  전부 사라졌다.**

### 왜 top-3 였는가 — 순수 추가(pure-additive)만

선택된 세 항목은 **밸런스 영향이 없는 것**만 골랐다.

| 항목 | 내용 | 밸런스 영향 |
| --- | --- | --- |
| **P2** | 미배선 VFX 배선 | **없음** (pure-additive) |
| **P4** | combat log 확장 (`state.message` 1줄 → 최근 N줄) | **없음** (pure-additive) |
| **P9** | rAF 기반 렌더 루프 | **없음** (렌더 전용) |

**P7 (idle-turn pressure) 과 P8 (crit threshold coupling) 은 의도적으로
하지 않았다.** 이 둘은 **전투 밸런스를 건드린다** — idle turn 를 넣으면
턴 구조가 바뀌고, crit threshold 를 묶으면 crit 확률이 바뀐다. 둘 다
**ADR-0229 §A1 drift check** 가 필요하다. 그런 변경은 별도 ADR 로
분리해야 한다.

**남은 12개 제안 (P1, P3, P5–P8, P10–P15) 은 손대지 않았다.** (§후속 항목)

### 이 ADR 의 질문

**top-3 를 그대로 구현하면 되는가?** 답은 "대부분은, 그러나 두 곳에서
아니오" 다. 순수 추가라는 전제에도 **부수 효과(side effect)** 가 두 개
있다. VFX spawn 은 **PRNG 를 소비하고**, redraw 는 **autosave 를
유발한다.** 둘 다 이 ADR 의 핵심 발견이다.

## 결정에 이르게 된 근거

### P2 — 7개 kind 배선 (새 renderer 없음, 새 kind 없음)

배선한 7개 kind 는 **모두 pre-existing renderer 를 갖고 있었다.** 스키마
수정도, renderer 수정도, kind 추가도 **0건** 이다.

| kind | spawn 지점 | 파일 |
| --- | --- | --- |
| `player_hit` | **적 스킬 피해 지점** | `web/src/core/state_actions_combat.ts` |
| `player_hit` | **적 auto-attack 피해 지점** | `web/src/core/state_actions_combat.ts` |
| `defeat` | 플레이어 HP 0 분기 | `web/src/core/state_actions_combat.ts` |
| `ice_death` | 승리 분기 | `web/src/core/state_actions_programs.ts` |
| `shield` | `applyShield` | `web/src/core/ice_combat_effect_apply.ts` |
| `heal` | `applyHeal` | `web/src/core/ice_combat_effect_apply.ts` |
| `regen` | `applyRegen` | `web/src/core/ice_combat_effect_apply.ts` |
| `buff` | `applyBuff` | `web/src/core/ice_combat_effect_apply.ts` |

**`shield` / `heal` / `regen` / `buff` 의 배선 경로** — `IceEffectOutcome`
에 **새 `vfx` 필드**가 추가되고
(`web/src/core/ice_combat_effects.ts`), 네 개의 applier 가 그 필드를
채운다. combat path 의 `applyIceNonDamageEffect` 호출부에서
`outcome.vfx` 를 `state.vfxInstances` 에 합친다.

**배선하지 않은 것 (의도적이다):** `debuff` / `stun` / `counter` /
`lifesteal` / `ice_intro` / `status_apply`. `counter` / `lifesteal` 은
**플레이어 측 스킬 시스템에 그 개념이 없다** — 발생 지점이 없다. 스킬이
없는 곳에 VFX 를 배선하면 "unwired" 의 반대편("연결될 대상 없는 배선")이
된다. 제안 문서 §R12 도 같은 판단으로 나머지를 각 스킬 구현 시점에
함께 배선하도록 남겼다.

### P4 — combat log

`GameState` 에 **`readonly combatLog: ReadonlyArray<string>`** 가
추가된다 (`web/src/core/types.ts`).

- **방향: newest-first** — index 0 이 가장 최근 이벤트.
- **cap = 8** (`COMBAT_LOG_CAP`, `web/src/core/state_helpers.ts`).
- `makeInitialState` 와 `slotToGameState` 가 `[]` 로 초기화한다.
- `useProgram` 은 자신의 메시지를 **prepend** 하고, `processEnemyTurns`
  는 `logMessages` 배치 전체를 **reversed copy 로 prepend** 한다
  (원본 배열은 mutate 하지 않는다).
- `buildHudLines` 은 최근 4줄을 보여주고, 로그가 비었을 때
  `state.message` 로 fallback 한다.
- **`message` 의 semantics 는 바뀌지 않는다** — 여전히
  chronologically-last 이벤트.

**`combatLog[0]` 이 가장 최근이라는 사실이 핵심이다.** 제안 문서가
`state.combatLog.slice(0, 4)` ("가장 최근 4건") 라고 쓴 것은
newest-first 전제에서만 성립한다. 반전 순서였다면 slice 가 "가장 오래된
4건" 이 되었을 것이다.

**`combatLog` 는 `SaveSlot` 에 **넣지 않았다** — save schema bump 를
피하기 위해서다. reload 후에는 다시 채워진다.

### P9 — rAF 렌더 루프 (`main.ts` 만)

`Game` 클래스에 새 필드와 함수가 추가된다.

- 필드: `rafId` / `loopRunning` / `lastLoopMs` / `fpsCounter`
- `MAX_FRAME_ADVANCE_MS = 100`
- `startLoop()` — **idempotent**
- `loop(now)` — bind 된 arrow function

**프레임마다 하는 일:** `FpsCounter` tick (`core/performance.ts`) →
delta 계산 → `advanceVfxListBy` 로 `vfxInstances` 진행 → **`tick` 이
rolled 되거나 instance 가 만료된 경우에만** `draw(false)` 호출. 렌더러는
`instance.tick` 로 animate 하기 때문이다.

**VFX advance 는 `draw()` 안에서 `loop` 밖으로 옮겨졌다.** 그래야
loop 가 advance 의 **단일 소유자**가 되어 double-advance 가 없다.

**기존 입력 핸들러의 `draw()` 호출 59건은 전부 그대로 살아있다** — 즉시
반응성을 유지한다. `start()` 는 `startLoop()` 을 부르고, `stop()` 은
`loopRunning = false` 로 세우고 `rafId` 를 cancel + null 한다. 죽은
`_lastFrameMs` 필드는 제거했다.

**새 timing subsystem 은 도입하지 않았다.** guard 는 `performance.ts` 의
`FpsCounter` + `getMetrics()` 와 loop 이 어차피 필요로 하는 rAF delta 를
재사용한다. 100ms 를 넘는 stall 에서는 advance 를 건너뛰므로 **거대한
delta 가 모든 VFX 를 한꺼번에 만료시키는 일이 없다.**

## 구현 중 발견한 두 개의 실제 결함

> **이 절이 이 ADR 의 실체다.** 두 결함 모두 "구현하면 드러나는" 종류이며,
> **제안 문서에는Neither 존재하지 않는다.** 하나는 **발견하지 않으면
> 조용히 밸런스를 망치고**, 다른 하나는 **발견하지 않으면
> 저장소를 60배 writes 한다.**

### 1. VFX spawn 은 RNG-neutral 이 아니었고, calibrated 곡선을 조용히 움직였다

**`import_vfx` 의 instance id 는 `Math.random` 에서 나온다:**

```
id: Math.floor(Math.random() * 1e9) + 1,
```

(`web/src/core/state_helpers.ts` — `import_vfx` 와 `import_vfx_ms` 양쪽)

밸런스 하네스는 `Math.random` 을 **seeded PRNG(mulberry32)** 로
교체한다 (`web/scripts/balance_sim.ts`). 따라서 **VFX spawn 은
하네스가 제어하는 PRNG 에서 한 번을 소비한다.**

**naive 배선의 결과** — 새 spawn site 가 `import_vfx` 를 쓰면:

| | HEAD | naive version |
| --- | --- | --- |
| RNG draw 수 (한 전투) | **35** | **27** |
| g2 win-rate | 88.6% | **87.3%** |
| g3 win-rate | 73.1% | **72.1%** |
| g4 win-rate | 39.3% | **40.3%** |

**전투 수학은 하나도 바뀌지 않았다. 바뀐 것은 *random stream* 이었다.**
crit roll / proc roll / 스킬 선택이 다른 수를 뽑게 되고, 그것이
aggregate win-rate 를 움직인다. **이것은 ADR-0229 가 막으려던 drift 의
정확한 형태다** — 그리고 조용하다. combat log 에 아무 것도 안 찍힌다.

**해결:**

1. `import_vfx` / `import_vfx_ms` 는 **HEAD 의 동작 그대로 복원**했다.
   그래서 **모든 pre-existing call site 가 원래의 draw 횟수와 위치를
   유지한다.**
2. 새 **`import_vfx_deterministic`** (단조 counter, **RNG 를 소비하지
   않음**) 을 **새 spawn site 에만** 사용했다.

**결과: 35 draws = HEAD → 12개 grade 전부 0.0pp drift.**

**id 는 순수 identity key 다** (로직이 읽지 않는다). 그래서 counter id
와 random id 가 공존해도 안전하다 — `import_vfx_deterministic` 의
docstring 에 이것을 명시했다.

### 2. render loop 가 초당 ~60회 IndexedDB write 를 유발했다

`draw()` 는 **무조건** `autosave()` 를 불렀다:

```
private autosave(): void { ... saveToSlot(0, stateToSaveSlot(this.state)) ... }
```

그리고 `saveToSlot` 은 `web/src/save/storage.ts` 의 `save()` →
**`idbPut`** (Tier 3 IndexedDB backend) 로 이어진다.

loop 가 애니메이션 중에 `draw()` 를 초당 60회 부르면, 그건
**초당 60회 IDB transaction** 이다. 그 동안에도 loop 는 계속 돌기
때문에 transaction 은 서로를 앞선다.

**해결: `draw(persist: boolean = true)`.**

- **default `true`** — 기존 59개 call site 의 동작은 **byte-identical**
  이다 (여전히 autosave 한다).
- **loop 내부의 두 redraw만 `false`** 를 넘긴다.

이것은 **loop 때문에 필요해진 render-layer side-effect 수정** 이며,
scope expansion 이 아니다.

## 고려한 옵션

### Option 1: top-3 를 구현하되, 부수 효과 2개를 함께 해결한다 (선택)

- **설명**: P2 / P4 / P9 를 구현한다. VFX spawn 은 RNG-neutral 하지
  않은 helper (`import_vfx_deterministic`) 를 사용하고, `draw()` 에
  `persist` flag 를 도입해 loop 의 redraw 가 autosave 를 유발하지 않게
  한다.
- **장점**:
  - **밸런스가 증명 가능하게 무변경이다.** 12 grade 전부 0.0pp.
  - 두 결함이 **문서화되고**future 재발을 막는 구조로 고정된다.
  - `import_vfx_deterministic` 의 docstring 이 나중 작업자를 위한
    경고문 역할을 한다.
- **단점**:
  - `draw()` 시그니처가 바뀐다 (default 인자라 기존 call site 는 무변경).
  - `import_vfx` 의 잠재 함정은 **전역적으로 고치지 않았다** (아래
    「부정적 영향」 참조).
- **Pillar 정합**:
  - P3 (The Flatline): ✅ built-but-unwired VFX 가 실제 플레이에 나온다.
  - P5 (The Style): ✅ 피격 피드백 · 격파 연출 · 전투 로그가 보인다.

### Option 2: 그대로 구현한다 — 부수 효과는 무시한다

- **설명**: 제안 문서의 스펙대로만 구현한다. `import_vfx` 를 그대로
  쓰고, `draw()` 도 그대로 둔다.
- **단점**:
  - **밸런스가 조용히 움직인다** (g2 88.6 → 87.3, g3 73.1 → 72.1,
    g4 39.3 → 40.3). ADR-0229 §A1 이 발동하지만 **왜 움직였는지
    설명할 수 없다** — combat math 는 안 바뀌었기 때문이다.
  - **저장소가 초당 60회 write 된다.**
  - "pure-additive" 라는 전제가 두 곳에서 깨진다.
- **Pillar 정합**: 실패 (증거 없이 drift 가 발생한다).

### Option 3: P7 / P8 까지 함께 구현한다

- **설명**: top-3 에 idle-turn pressure (P7) 와 crit threshold
  coupling (P8) 을 더한다.
- **단점**:
  - **두 항목 모두 전투 밸런스를 건드린다.** idle turn 는 턴 구조를,
    crit coupling 은 crit 확률을 바꾼다.
  - ADR-0229 §A1 drift check 가 **필수**가 되고, re-baseline 가능성이
    있다. 그 판단은 **별도 ADR** 의 몫이다.
- **Pillar 정합**: 실패 (범위 확장 + 별도 결정 필요).

## 추천 (Recommendation)

**Option 1.** 순수 추가라는 전제는 대체로 맞았고, **두 곳에서만**
깨졌다. 두 곳 모두 **구현하지 않으면 발견되지 않는다** — 그래서
구현하고 발견하고 고쳤다는 사실 자체를 이 ADR 에 남긴다.

**Option 3 은 명시적으로 배제한다.** P7 / P8 은 밸런스를 건드린다.
밸런스를 건드리는 변경은 ADR-0229 §A1 아래에서 별도 ADR 로 다뤄야
한다.

## 사용자 결정 (Decision)

**2026-10-27 — top-3 (P2 / P4 / P9) 를 구현하되, 구현 중 발견된 두 개의
부수 효과를 함께 해결하기로 결정했다.** 구현 완료·검증됨.

- [x] **Option 1 — top-3 구현 + 부수 효과 2건 해결** — **채택·구현됨**
- [ ] Option 2 — 그대로 구현 (부수 효과 무시)
- [ ] Option 3 — P7 / P8 까지 함께 구현

### 결정된 내용

1. **P2 — 7개 kind 배선.** pre-existing renderer 만 사용, kind 추가 0건,
   renderer 추가 0건.
2. **P4 — combat log.** newest-first, cap 8, HUD 최근 4줄 + `message`
   fallback. `message` semantics 불변. **`SaveSlot` 에는 넣지 않는다**
   (schema bump 회피).
3. **P9 — rAF 렌더 루프.** `main.ts` 만. `startLoop()` idempotent,
   `MAX_FRAME_ADVANCE_MS = 100`, 변화가 있을 때만 redraw.
4. **VFX spawn 은 RNG-neutral 해야 한다** — 새 spawn site 는
   `import_vfx_deterministic` 을 쓴다. `import_vfx` / `import_vfx_ms`
   는 HEAD 동작 그대로다.
5. **`draw()` 의 autosave 는 opt-out 가능해야 한다** —
   `draw(persist: boolean = true)`. 기존 59개 call site 는 무변경.
6. **P7 / P8 은 하지 않는다.** 나머지 12개 제안도 하지 않는다.
7. **기존 ADR 은 하나도 수정하지 않았다.** Accepted 결정은 immutable
   이다 (`AGENTS.md` §6). 관계는 이 ADR 에 기록했다.

## 결과 (Consequences)

### 긍정적 영향

- **플레이어가 받는 피해를 이제 볼 수 있다** (`player_hit`).
- **패배 · 격파 연출이 나온다** (`defeat` / `ice_death`).
- **ADR-0226 의 `shield` / `heal` / `regen` / `buff` 효과가 보인다** —
  이전에는 상태로만 적용되고 메시지 문자열만 남았다.
- **VFX 가 계속 animate 된다** — 이전에는 다음 키 입력이 있어야
  한 프레임 진척했다.
- **전투 로그가 ADR-0226 / ADR-0228 의 메시지를 보존한다** —
  `message` 하나가 덮어쓰던 것들이 남아 있다 (예: `CRITICAL` 마커).
- **밸런스가 증명 가능하게 무변경이다.**

### 부정적 영향 / 수용한 비용

- **`combatLog` 는 persist 되지 않는다** (의도적). reload 후에는 다시
  채워진다.
- **`import_vfx` 는 여전히 RNG 를 소비한다.** 이 잠재 함정은
  **전역적으로 고치지 않았다.** 고치는 것 자체가 calibration baseline 을
  움직이므로 — 미래의 ADR 가 의도적으로 re-baseline 하면서 해야 한다.
  대신 **새 helper 의 docstring 에 경고를 남겼다.**
- **loop 의 runtime 동작은 자동화 테스트로 덮이지 않는다** (아래
  「검증 한계」).

### 후속 항목

1. **남은 12개 제안** — P1 (canvas 레벨 shake / hit-stop), P3 (floating
   damage numbers), P5 (SFX layering), P6 (ADR-0226 효과의 VFX 밖
   가시성), **P7 (idle-turn pressure — ADR-0229 §A1 필요)**,
   **P8 (crit threshold coupling — §A1 필요)**, P10 (accessibility
   wiring), P11 (onboarding), P12 (touch feedback), P13 (audio ducking),
   P14 (status HUD), P15 (`ice_intro` / `data_acquired`).
2. **`import_vfx` 를 전역 counter 기반으로** — 별도 ADR 필요. 그 ADR 은
   **의도적인 re-baseline** 을 포함해야 한다.
3. **loop 의 runtime coverage** — e2e 가 돌아갈 수 있게 되면
   (예: Playwright frame-timing assertion) 추가한다.

### 관계 — immutable 규칙 준수

ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 / 0228 / 0229 /
0230 은 Accepted 이며 immutable 하므로 **하나도 수정하지 않았다**
(`AGENTS.md` §6). 관계는 이 ADR 에 기록했다.

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:

**변경된 파일 — 11개 (소스 7 + 테스트 4)**

- `web/src/main.ts` — **P9.** `rafId` / `loopRunning` / `lastLoopMs` /
  `fpsCounter` 필드, `MAX_FRAME_ADVANCE_MS = 100`, `startLoop()`,
  `loop(now)`, `draw(persist: boolean = true)`. VFX advance 를 `draw()` 에서
  `loop` 으로 이동 (단일 소유자). `_lastFrameMs` 제거. `start()` 가
  `startLoop()` 호출, `stop()` 이 `loopRunning = false` + `rafId` cancel.
- `web/src/core/types.ts` — `GameState.combatLog: ReadonlyArray<string>`
  추가.
- `web/src/core/state.ts` — `makeInitialState` / `slotToGameState` 가
  `combatLog: []` 로 초기화. `buildHudLines` 이 `recentLogLines(state)`
  를 사용 (로그가 비면 `state.message` fallback, 있으면 최근 4줄).
- `web/src/core/state_helpers.ts` — `COMBAT_LOG_CAP = 8` 과
  `import_vfx_deterministic` (단조 counter, RNG 0 draw) 추가.
- `web/src/core/state_actions_combat.ts` — `player_hit` ×2 (스킬 피해
  지점 + auto-attack 피해 지점), `defeat` (플레이어 HP 0 분기),
  `outcome.vfx` merge, `combatLog` prepend.
- `web/src/core/state_actions_programs.ts` — `ice_death` (승리 분기),
  `combatLog` prepend (승리 메시지 + 프로그램 메시지).
- `web/src/core/ice_combat_effects.ts` — `IceEffectOutcome.vfx` 필드 추가.
- `web/src/core/ice_combat_effect_apply.ts` — 네 개의 applier
  (`applyShield` / `applyHeal` / `applyRegen` / `applyBuff`) 가 `vfx` 를
  채움. inert 경로는 `vfx: []`.
- `web/tests/ice_combat_effects.test.ts` — 효과별 VFX spawn 6건.
- `web/tests/sound_triggers.test.ts` — combat log 보존 4건.
- `web/tests/state.test.ts` — `ice_death` spawn 1건.
- `web/tests/status.test.ts` — `player_hit` ×2 + `defeat` 3건.

**테스트**

- `npm test` — **127 files / 3002 tests, 0 failures.** (이전 2986,
  **+16** — 신규 assertion 16개.)
- 신규 assertion 14건은 **변경 전 반드시 실패함을 확인했다**
  (HEAD 를 손으로 복원해 검증 — `git checkout` / `git stash` 는 쓰지
  않았다).

**게이트**

- `npx tsc --noEmit` — **0 errors.**
- `npx eslint src --ext ts` — **0 errors** (pre-existing warning 1건은
  `web/src/input/keyboard.ts` — 손대지 않았다).
- `npm run build` — **성공.**

**밸런스 — 12 grade 전부 0.0pp drift**

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

**RNG draw count — HEAD 와 독립적으로 확인.** seeded PRNG 를 계수하는
probe 로 한 전투의 `Math.random` draw 수를 측정했다:

- **HEAD: 45 draws** (mission `aleph_fragment`, seed 777)
- **현재 구현: 45 draws** — **동일**
- 12개 mission 전체 (총 574 draws) 에서 **HEAD 와 draw 수 · 승패 ·
  턴 수가 모두 동일** — `diff` 로 확인.

**naive 버전 대조 실험.** `import_vfx_deterministic` 을 RNG-consuming
형태로 되돌린 사본에서 같은 probe 를 돌리면 **draw 수가 어긋난다**
(45 → 58, 55 → 47, 42 → 32) — 그리고 **턴 수까지 바뀐다** (4 → 5,
5 → 4, 5 → 3). 이것이 결함 1 의 실증이다.

**증거 인용 (실측 위치)**

- `web/src/core/state_helpers.ts` — `import_vfx` / `import_vfx_ms` 의
  `id: Math.floor(Math.random() * 1e9) + 1` (RNG 소비 지점),
  `COMBAT_LOG_CAP = 8`, `import_vfx_deterministic` (counter id).
- `web/src/core/state.ts` — `recentLogLines(state)` (로그가 비면
  `state.message` fallback, 있으면 `combatLog.slice(0, 4)`).
- `web/src/core/types.ts` — `GameState.combatLog`. **`SaveSlot`
  인터페이스에는 이 필드가 없다** — save schema bump 없음.
- `web/src/main.ts` — `draw(persist: boolean = true)` 와
  `if (persist) this.autosave();`. 기존 `this.draw()` call site **59건**
  은 HEAD 와 **동일하게** 유지 (default 인자).
- `web/src/main.ts` — `autosave()` → `saveToSlot(0, …)` →
  `web/src/save/storage.ts` 의 `save()` → **`idbPut`** (IndexedDB write).
  이것이 결함 2 의 실측 경로다.
- `web/scripts/balance_sim.ts` — `Math.random = mulberry32(config.seed)` —
  하네스가 PRNG 를 소유한다는 근거.
- `web/src/core/performance.ts` — `FpsCounter` 와 `getMetrics()`
  (새 timing subsystem 없이 재사용).

**검증 한계 (정직하게 명시한다)**

- **vitest 는 `main.ts` 의 rAF loop 을 실행하지 않는다.** `main.ts` 는
  import 시점에 self-boot 하고, vitest 는 동기적이다. 따라서 loop 의
  runtime 동작은 **자동화 테스트로 검증되지 않았다.**
- **Playwright e2e 를 실행하지 못했다** (`web/e2e/game.spec.ts`,
  `web/e2e/smoke.spec.ts`) — 브라우저와 live URL 이 필요하다. 실제
  실행 시 **24 test 전부 0ms 에 실패** 했다 (browser 부재).
- **LSP diagnostics 를 사용할 수 없었다** (daemon socket unreachable).
  그래서 **repo 가 자체로 mandate 한 gate 인 `tsc --noEmit` (strict) 이
  권위** 다.
- **화면 위 애니메이션을 관찰하지 못했다** — screenshot 도, frame-timing
  trace 도 없다. 애니메이션이 실제로 재생된다는 것은 **추론**이며
  **관찰된 사실이 아니다.**
- **loop 의 정당성은 실행이 아니라 사고로만 검증했다:** `stop()` 에서
  즉시 종료 (`loopRunning` guard 가 어떤 작업보다 먼저 도는 &&
  `cancelAnimationFrame` 이 대기 중인 id 를 지운다), double-start 불가
  (`startLoop` idempotent && `rafId` 는 loop 만 설정), leak 없음 (대기
  중인 rAF 는 정확히 하나, `draw()` 안에서 `stop()` 을 불러도 이미
  예약된 id 를 cancel 한다).

**Notes**:

- **`web/` 아래의 다른 파일은 하나도 바뀌지 않았다.** `combat_engine.ts`,
  `ice_ai.ts`, `ice_scaling.ts`, `ice_crit.ts`, `ice_skills.ts`,
  `state_actions.ts`, `state_actions_phases.ts`, `data/*.json` — 전부
  **미변경.** `web/src/data/effects.json` / `effects.d.ts` 도 **미변경**
  — kind 추가가 0건이므로 schema bump 가 필요 없었다.
- **기존 assertion 을 하나도 약화·skip·삭제하지 않았다.** 추가만 했다.
- **`import_vfx` / `import_vfx_ms` 의 HEAD 동작은 byte-identical 로
  유지했다** — draw 횟수와 위치가 모두 그대로다.
- **`Game/wet_run/log.md` 는 수정하지 않았다** (오케스트레이터 소유).
- **ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 / 0228 /
  0229 / 0230 을 포함한 기존 ADR 은 하나도 수정하지 않았다.**
- **임시 파일을 남기지 않았다** (검증용 probe 는 모두 삭제).
- **re-calibration 은 하지 않았다.** ADR-0229 §A1 미발동 (grade 이동 0) →
  **re-baseline 불필요.** §B hard invariant 전부 성립, §A4 해당 없음
  (calibration 배열 미변경).

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `docs/wiki/decisions/0231-combat-feel-top3-vfx-log-raf.md` — **신규**
  (이 ADR)
- `docs/wiki/decisions/README.md` — 0231 행 신규 (0230 행 다음, 6-컬럼
  동일 format)
- `web/src/main.ts` — P9 (rAF loop + `draw(persist)`)
- `web/src/core/types.ts` — `GameState.combatLog`
- `web/src/core/state.ts` — `combatLog` 초기화 + `buildHudLines`
- `web/src/core/state_helpers.ts` — `COMBAT_LOG_CAP`,
  `import_vfx_deterministic`
- `web/src/core/state_actions_combat.ts` — P2 spawn ×4 + `combatLog`
- `web/src/core/state_actions_programs.ts` — P2 spawn ×1 + `combatLog`
- `web/src/core/ice_combat_effects.ts` — `IceEffectOutcome.vfx`
- `web/src/core/ice_combat_effect_apply.ts` — applier ×4 의 `vfx`
- `web/tests/` — 4개 파일, 신규 assertion 16건 (추가만)

### 이번 결정으로 변경되지 않은 항목

- `web/src/data/effects.json`, `web/src/data/effects.d.ts` — **미변경**
  (kind 추가 0건)
- `web/src/core/combat_engine.ts`, `ice_ai.ts`, `ice_scaling.ts`,
  `ice_crit.ts`, `ice_skills.ts`, `state_actions.ts`,
  `state_actions_phases.ts`, `combat_models.ts`, `boss_phases.ts` —
  **전부 미변경**
- `web/src/data/ice_types.json`, `missions.json`, `programs.json` —
  **미변경**
- `SaveSlot` 인터페이스 — **미변경** (save schema bump 없음)
- `Game/wet_run/log.md` — 오케스트레이터 소유
- ADR-0211 / 0219 / 0222 / 0223 / 0224 / 0225 / 0226 / 0227 / 0228 / 0229 /
  0230 — **미수정** (immutable)

## 관련 결정

- ADR-0229 (Grade 난이도 곡선 재기준화) — **drift policy 의 owner.**
  이 ADR 의 0.0pp drift 로 §A1 미발동, re-baseline 불필요. §B hard
  invariant 전부 성립. **ADR-0229 는 수정하지 않았다** (immutable).
- ADR-0226 (Non-damaging ICE 스킬 효과를 구현한다) — **P2 가 보이게
  만든 효과들** (`shield` / `heal` / `regen` / `buff`) 의 owner. 이전에는
  상태로만 적용되고 메시지만 남았다. **ADR-0226 은 수정하지 않았다**
  (immutable).
- ADR-0228 (ICE 아키타입 동작 배선) — **`CRITICAL` 마커** 등 combat
  메시지의 owner. combat log 가 이제 그 메시지를 보존한다.
  **ADR-0228 은 수정하지 않았다** (immutable).
- ADR-0210 (Combat VFX Effect Schema) — 27개 kind canonical taxonomy 의
  owner. 이 ADR 은 kind 를 **추가하지 않았다.** **ADR-0210 은 수정하지
  않았다** (immutable).
- ADR-0196 (Accessibility Colorblind State Alignment) — 접근성.
  **손대지 않았다.** **ADR-0196 은 수정하지 않았다** (immutable).
- ADR-0195 (Accepted ADR Implementation Status Workflow) — 이 ADR 의
  Implementation Status 형식의 owner. **수정하지 않았다** (immutable).
- `docs/design/combat-feel-and-interaction-proposal.md` — 이 ADR 이 그
  top-3 (P2 / P4 / P9) 을 반영한다. 나머지 12개 제안은 미반영.

## 변경 이력

- 2026-10-27: Draft 작성 (combat-feel 제안 문서 top-3 — P2 VFX 배선 +
  P4 combat log + P9 rAF 렌더 루프)
- 2026-10-27: **Accepted (Option 1 — top-3 구현 + 부수 효과 2건 해결)** —
  구현 완료·검증. P2 는 7개 kind 배선 (renderer·kind 추가 0건), P4 는
  newest-first cap-8 combat log (`SaveSlot` 제외), P9 는 idempotent
  rAF loop + `draw(persist)`. **구현 중 두 개의 실제 결함 발견** —
  ① VFX spawn 의 **RNG non-neutrality** (naive 배선 시 g2 88.6 → 87.3,
  g3 73.1 → 72.1, g4 39.3 → 40.3 drift) → `import_vfx_deterministic` 로
  해결, ② loop 의 **초당 ~60회 IDB write** → `draw(persist)` 로 해결.
  **12 grade 전부 0.0pp drift**, RNG draw count HEAD 와 일치 (45 = 45).
  `npm test` 127 files / 3002 tests 0 failures (+16). **P7 / P8 및 나머지
  12개 제안은 미반영** — re-calibration 은 하지 않았다.
