# ADR-0233: 오디오 ducking + SFX rate 변조 + 마스터 볼륨

**상태**: Accepted
**날짜**: 2026-10-29
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P3 (The Style — 오디오 층위, ADR-0231/0232 sibling)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0195 — Accepted ADR Implementation Status Workflow](./0195-adr-implementation-workflow.md), [ADR-0201 — wet_run-web Tier 2b Howler.js BGM 통합](./0201-wetrun-web-howler-audio.md), [ADR-0204 — wet_run-web Phase-aware BGM](./0204-wetrun-web-phase-aware-bgm.md), [ADR-0207 — wet_run-web Tier 4 SFX + Animation VFX + Status Effect Glyphs](./0207-wetrun-web-tier4-sfx-animation-glyphs.md), [ADR-0229 — Grade 난이도 곡선 재기준화](./0229-grade-curve-rebaseline.md), [ADR-0231 — Combat-feel top-3 반영](./0231-combat-feel-top3-vfx-log-raf.md), [ADR-0232 — Combat-feel tier 2 반영](./0232-combat-feel-tier2-shake-damage-sfx.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-29 에 결정·구현·검증까지 완료되었다.
>
> **이 ADR 은 밸런스를 바꾸지 않는다.** 12개 grade 전부 **0.0pp drift** —
> ADR-0229 baseline 과 **byte-identical** 하다. §A1 은 발동하지 않았다.
>
> **이 ADR 은 오디오 계층만 건드린다.** `GameState` · reducer · 전투 수치 ·
> calibration 배열 · `ice_types.json` · `skill_defs` 는 **하나도 건드리지 않았다.**
> RNG draw count 는 **0건** 추가다.

## 컨텍스트 (Context)

`docs/design/combat-feel-and-interaction-proposal.md` (§2) 의 **P13** —
"오디오: 볼륨 ducking + 레이어 + 마스터 볼륨" 을 반영한다.

| 제안 | 무엇이 없었나 | 근거 |
| --- | --- | --- |
| ① `playSfx()` 에 `rate` 파라미터 | Howl 을 그대로 재생 (`audio/manager.ts:432-456`) — pitch/rate 변조 없음. 동일 SFX 가 매 턴 똑같은 높이로 울려 반복 지루함이 생긴다 | 제안 P13 ① |
| ② BGM ducking | combat 중 SFX 가 BGM 위에 묻힐 수 있다. BGM(0.4) 과 SFX(0.6) 가 **같은 볼륨축**을 쓰고 ducking 이 없다 | 제안 P13 ② |
| ③ master 볼륨 | settings 에 슬라이더가 2개(BGM / SFX) 뿐이고 **전체 음량 조절축이 없다** (`renderer/settings.ts:59-78`) | 제안 P13 ③ |

### 이 ADR 의 질문

**기존 Howler 래퍼(ADR-0201/0204/0207)에 파라미터를 붙이는 것만으로
P13 을 충족할 수 있는가?** 답은 "세 항목 모두 가능하다" 다. 다만
**제안이 명시한 위험 하나가 실제로 구현 제약이 된다** — §"결정에 이르게 된
근거" 의 ② 를 보라.

## 결정에 이르게 된 근거

### ① `playSfx()` 의 rate 파라미터 — Howler `rate()` 재사용

- Howler 의 `Howl.rate(rate)` 는 이미 제공되는 API 다 (ADR-0201 이 도입한
  `howler ^2.2.4` 의 기본 기능). **새 오디오 인프라를 만들지 않는다** —
  파라미터 하나를 붙이고 `howl.rate(rate)` 를 호출할 뿐이다.
- `clampRate` (`web/src/audio/manager.ts:171`) 가 Howler 가 실제로 받아들이는
  범위 **[0.5, 4.0]** 로 클램프한다. Howler 의 `rate` 타입 문서는
  "0.5 to 4.0, with 1.0 being normal speed" 라고 명시한다. NaN 은 1 로
  되돌린다 (기본값 유지).
- `PlaySfxOptions` (`web/src/audio/manager.ts:184`) — `{ rate?, duck? }`.
  두 필드 모두 optional 이므로 **기존 8개 `playSfx(id)` 호출 sites 는
  한 글자도 바뀌지 않는다** (아래 「영향 받은 항목」 참고).

### ② BGM ducking — 곱연산 오프셋, 저장은 절대 안 한다

제안 문서가 이 항목의 위험을 명시했다:

> "ducking 이 BGM 볼륨 영속 값(`wetrun_audio_bgm_volume`) 을 덮으면
> 재접속 시 설정이 오염됨 — duck 는 **곱연산 오프셋** 으로 처리하고
> 저장하지 말 것."

**이 제약을 그대로 구현했다.** BGM 볼륨의 최종값은 4개 값의 곱이다:

```
effective_bgm = master × bgm × track_volume × duck
```

`duck` 는 **곱연산 오프셋** 이며 `composeBgmVolume`
(`web/src/audio/manager.ts:128`) 안에서만 적용된다. `writePersistedVolume`
은 `setBgmVolume` 에서만 호출되고 `setBgmVolume` 은 `_bgmVolume` (영속 값,
duck 미포함) 을 저장한다 — **duck 는 저장 경로에 존재하지 않는다.**
`setMasterVolume` 도 `_masterVolume` 만 저장한다.

**regression test 로 이 불변식을 직접 검증한다** —
"ducking never rewrites the persisted BGM volume": combat SFX 를 재생한 뒤에도
`localStorage["wetrun_audio_bgm_volume"]` 은 `"0.4"` 이고
`getBgmVolume()` 도 `0.4` 다.

#### duck envelope — attack / hold / release 3구간

`duckFactorFor` (`web/src/audio/manager.ts:151`) 가 순수 함수로 envelope 을
계산한다:

| 구간 | 길이 | 동작 |
| --- | --- | --- |
| attack | `BGM_DUCK_ATTACK_MS = 60`ms | 1.0 → `BGM_DUCK_FACTOR = 0.8` 으로 선형 하강 |
| hold | `BGM_DUCK_HOLD_MS = 120`ms | 0.8 유지 |
| release | `BGM_DUCK_RELEASE_MS = 240`ms | 0.8 → 1.0 으로 선형 상승 |

전체 420ms. **1.0 (무 ducking) 이 반환값의 기준값** 이므로 envelope 밖에서는
항상 1 이다. duck 비율 0.8 (20% 감소) 은 제안 문서의 "20% duck" 권장값이다.

#### 어느 SFX 가 duck 를 유발하는가 — `COMBAT_SFX_IDS`

`COMBAT_SFX_IDS` (`web/src/audio/manager.ts:77`) — 9개 id 의 `ReadonlySet`:

- `COMBAT_HIT`, `ATTACK`, `DAMAGE`, `ICE_BREAK`
- `COMBAT_BLOCK`, `COMBAT_SKILL_STRIKE`, `COMBAT_SKILL_BURST`,
  `COMBAT_SKILL_GUARD`, `COMBAT_SKILL_SUPPORT`

**UI 사운드(`CLICK` / `CONFIRM` / `BACK` / `EQUIP` / `HEAL`) 와 이동 사운드
(`MOVEMENT_STEP` / `MOVEMENT_NODE`) 는 duck 하지 않는다.** 메뉴 클릭마다
음악이 출렁이면 ducking 이 아니라 stutter 로 들린다 — 이것은 "ducking"
이 아니라 "버그" 다. `isCombatSfxId` (`web/src/audio/manager.ts:179`) 가
판정한다.

#### duck 해제 — 타이머가 아니라 클럭

`advanceDuckingClock(deltaMs)` (`web/src/audio/manager.ts:594`) 가 duck
envelope 을 전진시킨다. `setTimeout` 을 쓰지 않는 이유는 ADR-0232 의
hit-stop deadlock 교훈과 같다 — **타이머는 벽시계에 묶여 있고 게임 루프의
frame delta 에 묶여 있지 않다.** 게임 루프가 매 frame 호출하면 duck 은
게임을 멈추지 않고 자연히 release 된다.

`duckElapsedMs()` 는 **내부 누산값과 벽시계 경과시간 중 큰 값** 을 쓴다 —
루프가 `advanceDuckingClock` 를 부르지 않아도 (예: 메뉴 화면) 벽시계로
해제된다. 두 경로 모두 "420ms 후에는 반드시 1.0" 을 보장한다.

### ③ master 볼륨 — BGM 과 SFX 를 곱하는 축

- `DEFAULT_MASTER_VOLUME = 1.0` (`web/src/audio/manager.ts:94`) —
  **기본값 1.0 이라 기존 플레이어의 청감은 변하지 않는다.**
- 영속 키 `wetrun_audio_master_volume` (`STORAGE_KEY_MASTER`). BGM
  (`wetrun_audio_bgm_volume`) · SFX (`wetrun_audio_sfx_volume`) 와
  **같은 규약** — `readPersistedVolume` / `writePersistedVolume` 재사용,
  `[0,1]` 클램프, 손상된 값은 fallback.
- `composeSfxVolume` (`web/src/audio/manager.ts:139`) — `master × sfx`.
- `setMasterVolume` 은 BGM 과 SFX **양쪽에 즉시 재적용** 한다
  (`applyBgmVolume` + `applySfxVolumes`).

## 고려한 옵션

### Option 1 — 기존 Howler 래퍼에 파라미터 추가 + 순수 함수로 수학 분리 (선택)

- **설명**: `manager.ts` 와 `settings.ts` 만 손댄다. 볼륨 합성(`compose*`),
  duck envelope(`duckFactorFor`), rate 클램프(`clampRate`) 를 **exported
  순수 함수** 로 노출해 AudioContext 없이 단위 테스트한다.
- **장점**: **밸런스가 증명 가능하게 무변경이다** (12 grade 전부 0.0pp).
  신규 오디오 인프라 0건. 기존 `playSfx(id)` 호출 sites 무변경.
  오디오가 실제로 어떤 값을 갖는지 **관찰된 사실** 로 검증된다.
- **단점**: `main.ts` 가 여전히 master 볼륨을 **조작할 수 없다** —
  아래 「고려한 옵션: main.ts 배선」 참고.
- **Pillar 정합**: Pillar 3 (The Style) ✅ — 전투가 소리로 "층" 을 가진다.

### Option 2 — 새 오디오 모듈 (`web/src/audio/mixer.ts`) 분리

- **설명**: 볼륨 합성 · duck · rate 를 별도 모듈로 뽑는다.
- **단점**: **基础设施가 하나 늘어난다.** ADR-0201/0204/0207 이 이미
  `manager.ts` 를 오디오의 유일한 소유자로 확정했다. 순수 함수를
  `manager.ts` 안에 두면 **파일 수는 늘지 않고** 테스트 가능성은 같으며,
  Howler import 경계도 그대로다. 게다가 `manager.ts` 는 495 → 738 LOC 이며
  이미 ADR-0110 의 모듈 사이즈 권장 범위(100–300 LOC)를 넘어 있다 —
  **추가 분할은 별도 결정의 몫** 이고, 이 ADR 이 그 결정까지 대신하면
  범위가 두 배가 된다.
- **Pillar 정합**: 실패 (불필요한 구조 증가).

### Option 3 — Web Audio API 로 직접 전환

- **설명**: Howler 를 버리고 AudioContext 를 직접 쓴다.
- **단점**: ADR-0201 이 이미 "Web Audio API 직접 사용 검토" 를 **후속
  항목으로 명시적으로 남겨두었다** (§대안). 이 ADR 은 그 결정을
  뒤집지 않는다. P13 은 파라미터 3개가 필요할 뿐이며 AudioContext
  전환은 그것을 정당화하지 못한다.
- **Pillar 정합**: 실패 (범위 초과).

### 고려한 옵션: `main.ts` 배선

**`web/src/main.ts` 는 이 ADR 의 범위 밖이다.** 같은 세션에 다른 에이전트가
`main.ts` 를 작업 중이므로 손대지 않았다. 결과적으로:

- `SettingsField` 에 `"master"` 가 추가되었고 `SettingsState.masterVolume`
  이 채워지지만, **현재 `main.ts` 의 필드 순회 배열
  (`main.ts:1039-1047`) 에는 `"master"` 가 없다** — 즉 **마스터 슬라이더가
  화면에는 보이지만 키보드로 선택할 수 없다.**
- `masterVolume` 을 **`SettingsState` 에 optional 로 선언** 했다. 이것은
  `main.ts` 가 `fallbackSettingsState()` (`main.ts:104`) 에서 이 shape 를
  그대로 만들기 때문이다 — required 로 선언하면 **`main.ts` 를 고쳐야**
  하므로 컴파일이 깨진다. optional 로 두면 `main.ts` 는 **한 글자도
  바뀌지 않고** 컴파일된다. 렌더러는 `undefined` 를 1 로 취급한다.
- **마스터 볼륨의 실효 효과는 이미 동작한다** — `getInitialSettingsState`
  가 `audio.getMasterVolume()` 을 읽어 state 에 싣고, `AudioManager` 의
  `setMasterVolume` 이 BGM/SFX 에 곱한다. **값을 바꾸는 경로**(키보드
  조작)는 `main.ts` 소관이다.

**이것이 이 ADR 의 유일한 미완성 항목이며, 다른 에이전트의
`main.ts` 작업에 명시적으로 인계한다.**

## 추천 (Recommendation)

**Option 1.** 세 항목 모두 순수 오디오 계층이며 밸런스 수치에 관여하지
않는다. 순수 수학(볼륨 합성 · duck envelope · rate 클램프)을 exported
함수로 분리하면 **AudioContext 없이 단위 테스트** 가 가능해진다 — jsdom
에는 Web Audio 구현이 없어서 `new Howl()` 이 조용히 실패하기 때문이다.

## 사용자 결정 (Decision)

**2026-10-29 — P13 을 구현하되 `main.ts` 배선은 다른 에이전트에 인계하기로
결정했다.** 구현 완료·검증됨.

- [x] **Option 1 — 기존 Howler 래퍼에 파라미터 추가 + 순수 함수로 수학 분리** — **채택·구현됨**
- [ ] Option 2 — 새 오디오 모듈 분리
- [ ] Option 3 — Web Audio API 전환

### 결정된 내용

1. **`playSfx(id, options?)` — `{ rate?, duck? }` optional.** 기존 8개
   호출 sites 무변경. rate 는 Howler `rate()` API 재사용, `[0.5, 4.0]`
   클램프.
2. **BGM ducking — 곱연산 오프셋.** `effective_bgm = master × bgm ×
   track × duck`. duck 는 **저장하지 않는다** (제안 문서의 위험 회피).
3. **duck envelope — attack 60ms / hold 120ms / release 240ms**, 배율 0.8.
   `advanceDuckingClock` 으로 해제 (타이머 없음).
4. **master 볼륨 — 기본 1.0**, `wetrun_audio_master_volume` 에 영속,
   BGM 과 SFX 양쪽에 곱해진다.
5. **모든 수학은 exported 순수 함수** — `composeBgmVolume`,
   `composeSfxVolume`, `duckFactorFor`, `clampRate`, `isCombatSfxId`.
6. **`main.ts` 는 손대지 않았다** — `masterVolume` 을 optional 로 선언해
   컴파일을 유지했고, 키보드 배선은 다른 에이전트에 인계한다.
7. **밸런스는 무변경** — 12 grade 전부 0.0pp drift.
8. **RNG draw 0건** — 오디오 계층은 RNG 를 쓰지 않는다.
9. **기존 ADR 은 하나도 수정하지 않았다** (Accepted 결정은 immutable).

## 결과 (Consequences)

### 긍정적 영향

- **전투 사운드에 층이 생긴다** — combat SFX 가 나는 동안 BGM 이 20%
  낮아진다. 명중 SFX 가 음악에 묻히지 않는다.
- **마스터 볼륨 축이 생긴다** — BGM 과 SFX 를 한 번에 올리거나 내릴 수
  있다. BGM/SFX 밸런스는 각자 유지된다.
- **반복 SFX 의 지루함이 줄었다** — rate 변조로 같은 SFX 를 높이를 달리해
  재사용할 수 있다 (호출부는 아직 `rate` 를 쓰지 않지만 **API 는 준비**).
- **오디오 수학이 검증 가능하다** — AudioContext 없이 순수 함수로 테스트
  된다. jsdom 에서 "소리가 난다" 를 관찰할 수 없는 문제를 우회한다.

### 부정적 영향 / 수용한 비용

- **마스터 슬라이더가 지금은 키보드로 선택 불가** — `main.ts` 배선이
  다른 에이전트 소관이라 생긴 상태. 화면에는 보이지만 TAB 을 눌러도
  선택되지 않는다. **값 읽기와 실효는 동작한다** (state 에 실려 있고
  AudioManager 가 곱한다).
- **`SettingsState.masterVolume` 이 optional** — `main.ts` 의
  `fallbackSettingsState()` 가 이 shape 를 만들기 때문이다. required 로
  만들면 `main.ts` 를 고쳐야 한다. optional + 렌더러 기본값 1 로
  컴파일을 유지했다.
- **`manager.ts` 가 495 → 738 LOC** — 이미 ADR-0110 의 권장 범위
  (100–300 LOC) 를 넘어난 상태였고, 이번에 더 커졌다. 순수 함수를
  별도 모듈로 뽑는 것은 **후속 결정 사항**으로 남긴다 (Option 2).
- **`sound_system.calculateVolume` 가 `manager.ts` 에서 더는 쓰이지
  않는다** — `composeBgmVolume` 이 그 자리를 대신했다. `sound_system.ts`
  는 **수정하지 않았고** (다른 모듈에서 쓰일 수 있으므로) 함수도 그대로
  남겼다.
- **rate 를 실제로 쓰는 호출부는 아직 없다** — 제안 P13 ① 의 목적을
  충족하려면 전투 SFX dispatch 가 rate 를 넘겨야 한다. 그건 `main.ts`
  소관이라 인계한다.

### 후속 항목

1. **`main.ts` 배선** — 필드 순회 배열에 `"master"` 추가, 좌/우 조작으로
   `setMasterVolume` 호출, `fallbackSettingsState()` 에 `masterVolume`
   추가 후 `SettingsState.masterVolume` 을 required 로 승격.
2. **rate 를 전투 SFX dispatch 에 연결** — 동일 SFX 연속 재생 시 미세한
   rate 편차 (제안은 0.92~1.08 범위) 를 준다. **RNG 를 쓰면 안 된다** —
   현재 시드 난수와 섞이면 밸런스 drift 가 생긴다. 결정적 규칙(예:
   턴 수 기반 고정 패턴) 이어야 한다.
3. **`manager.ts` 분할** — 순수 수학(`compose*` / `duckFactorFor` /
   `clampRate`) 을 `web/src/audio/mixer.ts` 로 분리 (Option 2).
4. **나머지 제안** — P6, P7 (§A1 필요), P8 (§A1 필요), P10, P11, P12,
   P14, P15.
5. **duck 시각 튜닝** — 20% / 60ms 는 제안 문서의 권장값이지 측정된 값이
   아니다. 실제 청취 피드백으로 조정하려면 constant 만 바꾸면 된다.

## Implementation Status (2026-10-29)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented (단, `main.ts` 배선은 미완 — 위 「고려한 옵션:
`main.ts` 배선」 참고)

**Evidence**:

**변경된 파일 — 4개 (소스 2 + 테스트 2)**

- `web/src/audio/manager.ts` — **P13 전체.**
  - 순수 함수: `composeBgmVolume` (`:127`), `composeSfxVolume` (`:139`),
    `duckFactorFor` (`:151`), `clampRate` (`:171`), `isCombatSfxId`
    (`:179`).
  - 상수: `COMBAT_SFX_IDS` (`:77`), `DEFAULT_MASTER_VOLUME` (`:94`),
    `BGM_DUCK_FACTOR` (`:98`), `BGM_DUCK_ATTACK_MS` (`:100`),
    `BGM_DUCK_HOLD_MS` (`:102`), `BGM_DUCK_RELEASE_MS` (`:104`).
  - 타입: `PlaySfxOptions` (`:184`).
  - `AudioManager`: `getMasterVolume` (`:549`), `setMasterVolume` (`:553`),
    `getEffectiveBgmVolume` (`:561`), `getEffectiveSfxVolume` (`:572`),
    `getDuckFactor` (`:577`), `isDucking` (`:585`),
    `advanceDuckingClock` (`:594`), `armDuck` (`:649`), `clearDuck`
    (`:656`), `applyBgmVolume` (`:628`), `applySfxVolumes` (`:638`).
  - `playSfx(id, options?)` (`:664`) — `howl.rate(rate)` +
    `howl.volume(effective)` + combat SFX 면 `armDuck()`.
  - `play()` (`:295`) · `crossfadeTo()` (`:366`) — master/duck 반영.
  - `STORAGE_KEY_MASTER = "wetrun_audio_master_volume"`.
  - **495 → 738 LOC.**
- `web/src/renderer/settings.ts` — **P13 ③.**
  `SettingsField` 에 `"master"` (`:61`), `SettingsState.masterVolume`
  (optional, `:75`), `getInitialSettingsState` (`:118`) ·
  `getInitialSettingsStateAsync` (`:142`) 가 master 를 싣는다,
  `renderSettingsScreen` 이 "Master Volume" 슬라이더를 BGM 위(행 9)에
  그리고 BGM 을 9 → 12, SFX 를 13 → 15 로 밀었다.
  **411 → 439 LOC.**
- `web/tests/audio_ducking.test.ts` — **신규, 46개 `it()`.**
  `composeBgmVolume` · `composeSfxVolume` · `duckFactorFor` · `clampRate`
  · `isCombatSfxId` · master 볼륨 영속/독립성 · rate 파라미터 ·
  duck arm/clear/해제 · "ducking 이 영속 BGM 볼륨을 덮지 않는다".
- `web/tests/settings.test.ts` — **확장, +4개 `it()`.**
  Master 라벨 · master 퍼센트 · master 슬라이더 바 비율(16/4) ·
  `selectedField === "master"` 선택 표시. 기존 15개 assertion 은
  **하나도 약화·삭제하지 않았다.**

**테스트**

- `npm test` — **133 files / 3173 tests, 0 failures.**
  (ADR-0232 시점 130 files / 3088 tests → **+3 files, +85 tests**.)
  > 파일 수 증가는 **동시 작업 중인 다른 에이전트**의
  > `tests/combat_grid.test.ts` · `tests/status_hud.test.ts` 2개를
  > 포함한다 (P14 작업). **이 ADR 이 만든 파일은
  > `tests/audio_ducking.test.ts` 1개** 다.
- **신규 assertion 은 변경 전 반드시 실패함을 확인했다.**
  - `tests/audio_ducking.test.ts` (신규 파일) — **41 failed / 5 passed.**
    모듈 부재로 export 가 없어 import 단계에서 실패.
  - `tests/settings.test.ts` (기존 파일) — **4 failed.**
    `masterVolume` 이 `SettingsState` 에 없어 fixture 가 컴파일되지 않고,
    "Master Volume" 라벨이 렌더되지 않았다.
  - **합계 45 failed / 20 passed** → 구현 후 **65 passed / 0 failed.**
  - 복원은 **손으로** 했다 (`git checkout` / `git stash` 미사용 — 오케스트레이터
    소유).

**게이트**

- `npm test` — **133 files / 3173 tests, 0 failures.**
- `npx tsc --noEmit` — **0 errors.**
- `npx eslint src --ext ts` — **0 errors** (pre-existing warning 1건은
  `web/src/input/keyboard.ts:14` — 손대지 않았다).
- `npm run build` — **성공.** (`tsc --noEmit && vite build`)

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
byte-identical 하다. (오디오 계층은 전투 시뮬레이션에 일절 관여하지
않으므로 drift 0 은 구조적으로 보장된다.)

**검증 한계 (정직하게 명시한다)**

- **오디오를 듣지 못했다.** WAV 파일의 존재와 유효한 RIFF 헤더는
  확인했지만 (기존 `tests/audio.test.ts` 의 on-disk 검증), **ducking 이
  실제로 "듣기에" 적절한지는 미검증**이다. "20%" 와 "60ms" 는 제안
  문서의 권장값이지 측정값이 아니다.
- **Howler 의 `rate()` / `volume()` 호출은 jsdom 에서 관찰되지 않았다.**
  jsdom 에는 Web Audio 구현이 없어 `new Howl()` 이 `HTMLMediaElement.
  prototype.play` not-implemented 로 실패한다 (기존과 동일한 상태 —
  `tests/tick_kill_loot.test.ts` 의 stderr 와 동일). 따라서 **검증된 것은
  계산된 값과 상태 전이** 이고, 실제 Howl 객체에 그 값이 전달되는지는
  **코드 읽기로만** 확인했다.
- **`main.ts` 배선은 미완.** 「고려한 옵션: `main.ts` 배선」 참고.
  키보드로 master 슬라이더를 선택할 수 없다.
- **Playwright e2e 를 실행하지 못했다** — 브라우저와 live URL 이
  필요하다. 제안 문서가 지목한 `web/e2e/settings.spec.ts` 는 master
  슬라이더를 검증하도록 **확장되지 않았다** (`main.ts` 배선과 함께
  시점).
- **화면 위 결과물을 관찰하지 못했다.** 슬라이더가 실제로 보이는지는
  렌더 함수 출력 텍스트로만 확인했다 (테스트는 grid 를 문자열로
  변환해 "Master Volume" 라벨과 "80%" 를 찾는다).
- **LSP diagnostics 를 사용할 수 없었다** (daemon socket unreachable).
  그래서 **repo 가 자체로 mandate 한 gate 인 `tsc --noEmit` (strict) 이
  권위** 다.

**Notes**:

- **기존 assertion 을 하나도 약화·skip·삭제하지 않았다.** 추가만 했다.
  (`tests/settings.test.ts` 의 기존 15개 `it()` 는 그대로다.)
- **`GameState` 는 변경하지 않았다.** 볼륨 · duck · rate 은 전부
  **오디오 계층** 에 있다. `core/` 는 건드리지 않았다.
- **`web/src/data/ice_types.json`, `missions.json`, `programs.json`,
  `effects.json`, `effects.d.ts` — 미변경.** calibration 배열
  (`ENCOUNTER_HP_BY_GRADE`, `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`) 도
  미변경.
- **RNG draw 0건** — 이 ADR 이 추가한 코드는 난수를 쓰지 않는다.
  `rate` 는 상수 인자이고 duck envelope 는 시간 기반이다.
- **`web/src/main.ts` — 미변경** (다른 에이전트 소유).
- **`web/src/core/sound_system.ts` — 미변경.** `calculateVolume` 은
  `manager.ts` 에서 더는 쓰이지 않지만 함수는 그대로 남겼다.
- **`Game/wet_run/log.md` 는 수정하지 않았다** (오케스트레이터 소유).
- **`docs/wiki/decisions/README.md` 는 수정하지 않았다** (오케스트레이터가
  인덱스 행 추가).
- **기존 ADR 은 하나도 수정하지 않았다** (immutable).
- **임시 파일을 남기지 않았다.**
- **re-calibration 은 하지 않았다.** ADR-0229 §A1 미발동 (grade 이동 0) →
  **re-baseline 불필요.** §B hard invariant 전부 성립, §A4 해당 없음
  (calibration 배열 미변경).

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `docs/wiki/decisions/0233-audio-ducking-master-volume.md` — **신규**
  (이 ADR)
- `web/src/audio/manager.ts` — master 볼륨 · ducking · SFX rate ·
  exported 순수 함수
- `web/src/renderer/settings.ts` — master 볼륨 슬라이더 + `SettingsField`
- `web/tests/audio_ducking.test.ts` — **신규** (46 tests)
- `web/tests/settings.test.ts` — master 슬라이더 assertion 4건 추가

### 이번 결정으로 변경되지 않은 항목

- `web/src/main.ts` — **미변경** (다른 에이전트 소유 — 키보드 배선은
  후속)
- `web/src/core/sound_system.ts`, `combat_engine.ts`, `ice_ai.ts`,
  `state.ts`, `types.ts`, `state_actions*.ts`, `combat_models.ts`,
  `boss_phases.ts` — **전부 미변경**
- `web/src/data/*.json`, `effects.d.ts` — **미변경**
- `GameState` / `SaveSlot` 인터페이스 — **미변경** (schema bump 없음)
- `web/src/audio/index.ts` — **미변경** (`playSfx(id)` 시그니처는
  그대로 — optional 파라미터라 호환)
- `Game/wet_run/log.md` — 오케스트레이터 소유
- ADR-0201 / 0204 / 0207 / 0110 / 0195 / 0229 / 0231 / 0232 를 포함한
  기존 ADR — **미수정** (immutable)

## 관련 결정

- ADR-0229 (Grade 난이도 곡선 재기준화) — **drift policy 의 owner.** 이
  ADR 의 0.0pp drift 로 §A1 미발동, re-baseline 불필요. **ADR-0229 는
  수정하지 않았다** (immutable).
- ADR-0201 / 0204 / 0207 (Howler.js 오디오 통합 3연작) — **이 ADR 이
  확장한 래퍼의 owner.** `playSfx` 에 파라미터와 `setMasterVolume` /
  `setBgmVolume` / `setSfxVolume` 만 추가했고 **Howler 를 새로 쓰지
  않았다.** AudioContext 직접 전환은 ADR-0201 이 후속 항목으로 남겨둔
  결정을 뒤집는 것이므로 **기각**했다. **셋 다 수정하지 않았다**
  (immutable).
- ADR-0232 (Combat-feel tier 2) — **직전 sibling.** P1/P3/P5 를
  처리했다. 이 ADR 은 오디오 계층의 **다른 축** (볼륨 · duck · rate) 을
  다룬다. **hit-stop deadlock 교훈** (타이머 대신 게임 루프 클럭) 이
  여기에도 적용되었다 — duck 해제도 `setTimeout` 이 아니라
  `advanceDuckingClock` 다. **ADR-0232 는 수정하지 않았다** (immutable).
- ADR-0231 (Combat-feel top-3) — sibling. **미수정** (immutable).
- ADR-0110 (모듈 사이즈 정책) — `manager.ts` 495 → 738 LOC 로 이미
  권장 범위를 넘긴 상태. **분할은 후속 항목으로 명시**했다.
  **ADR-0110 은 수정하지 않았다** (immutable).
- ADR-0195 (Accepted ADR Implementation Status Workflow) — 이 ADR 의
  Implementation Status 형식의 owner. **수정하지 않았다** (immutable).
- `docs/design/combat-feel-and-interaction-proposal.md` — 이 ADR 이 그
  **P13** 을 반영한다. 나머지 제안은 미반영.

## 변경 이력

- 2026-10-29: Draft 작성 (combat-feel 제안 문서 P13 — 오디오 ducking +
  SFX rate + master 볼륨)
- 2026-10-29: **Accepted (Option 1 — 기존 Howler 래퍼에 파라미터 추가 +
  순수 함수로 수학 분리)** — 구현 완료·검증. `playSfx(id, { rate?, duck? })`,
  `effective_bgm = master × bgm × track × duck` (duck 는 곱연산 오프셋이며
  **저장하지 않는다** — 제안 문서의 위험 회피), duck envelope
  attack 60ms / hold 120ms / release 240ms (배율 0.8), master 볼륨
  기본 1.0 + `wetrun_audio_master_volume` 영속. 수학은 전부 exported
  순수 함수 (`composeBgmVolume` / `composeSfxVolume` / `duckFactorFor` /
  `clampRate` / `isCombatSfxId`) 로 분리해 AudioContext 없이 단위
  테스트. 신규 assertion **45 failed** 확인 후 구현 → `npm test`
  **133 files / 3173 tests 0 failures** (+3 files / +85 tests).
  `npx tsc --noEmit` **0 errors**, `npx eslint src --ext ts` **0 errors**
  (pre-existing warning 1), `npm run build` **성공**. **12 grade 전부
  0.0pp drift** (`100.0/88.6/73.1/39.3/35.7/0.0` · PPL
  `100.0/77.9/99.6/84.8/44.4/28.3`), RNG draw count **0건 추가**.
  **`main.ts` 배선은 미완 — 다른 에이전트에 인계.**
