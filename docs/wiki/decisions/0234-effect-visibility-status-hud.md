# ADR-0234: ADR-0226 효과 가시화 + 상태 effect HUD 전면 개편 (제안 P6 / P14)

**상태**: Accepted
**날짜**: 2026-10-29
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — built-but-unreadable dead path, ADR-0216/0219/0222/0223/0224/0225/0226/0227/0228/0229/0230/0231/0232 sibling)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0195 — Accepted ADR Implementation Status Workflow](./0195-adr-implementation-workflow.md), [ADR-0210 — Combat VFX Effect Schema](./0210-combat-vfx-effect-schema.md), [ADR-0219 — non-damaging ICE 스킬 효과](./0219-non-damaging-ice-skill-effects.md), [ADR-0226 — Non-damaging ICE 스킬 효과를 구현한다](./0226-non-damaging-ice-skill-effects-implemented.md), [ADR-0229 — Grade 난이도 곡선 재기준화](./0229-grade-curve-rebaseline.md), [ADR-0231 — Combat-feel top-3 반영](./0231-combat-feel-top3-vfx-log-raf.md), [ADR-0232 — Combat-feel tier 2 반영](./0232-combat-feel-tier2-shake-damage-sfx.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-29 에 결정·구현·검증까지 완료되었다.
>
> **이 ADR 은 밸런스를 바꾸지 않는다.** 12개 grade 전부 **0.0pp drift** —
> ADR-0229 baseline 과 **byte-identical** 하다. §A1 은 발동하지 않았다.
>
> **이 ADR 은 순수 표시 계층이다.** `GameState` · reducer · 데미지 공식 ·
> calibration 배열 · `ice_types.json` · `skill_defs` 는 **하나도 건드리지
> 않았다.** ADR-0226 의 효과는 **이미 정확히 적용되고 있었다** — 이 ADR 이
> 한 것은 그것을 **보이게** 만드는 일뿐이다.

## 컨텍스트 (Context)

`docs/design/combat-feel-and-interaction-proposal.md` (§2) 의 두 행 —
**P6** (ADR-0226 ICE 효과 가시화) 과 **P14** (상태 effect HUD 전면 개편)
을 반영한다. 둘 다 **표시 전용** 이며 전투 수치에 관여하지 않는다.

| 제안 | 무엇이 없었나 | 근거 |
| --- | --- | --- |
| **P6** | ADR-0226 의 `shield` / `heal` / `regen` / `buff` 가 **HUD glyph 로 표시되지 않았다.** `STATUS_GLYPHS` 에 `shield` / `regen` / `powered` 항목이 없었다 | `web/src/renderer/vfx.ts:80-86` (개정 전 5종) |
| **P14** | glyph 가 **타겟 구분 없이** 전부 합쳐져 **활성 타겟 옆에만** 그려졌다. 플레이어 자신에게 붙은 `burn` 과 ICE 에 붙은 `burn` 이 **같은 칸** 에 섞였다 | `web/src/main.ts:1497` (개정 전 `statusEffects.map(e => e.kind)`), `:1736-1747` |

**제안 문서의 §4.1 은 P14 의 측정 기준을 "target 분리 + 9종 glyph" 로
적었다.** 이 ADR 은 **8종** glyph 로 구현한다 — 근거는 아래
「제안 문서와 다른一处」 절에 적었다.

### 이 ADR 의 질문

**ADR-0226 의 효과는 이미 화면에 보이고 있었나?** 답은 "**절반만**" 이었다.
VFX 는 이미 배선돼 있었지만 glyph 는 없었다. 그리고 **어느 ICE 가** 그
효과를 달고 있는지 화면은 말해주지 않았다.

## 결정에 이르게 된 근거

### 조사 결과 — VFX 배선은 이미 존재했다

`IceEffectOutcome.vfx` 가 `state.vfxInstances` 에 도달하는지 추적한 결과,
**이미 도달하고 있었다.** 경로는 세 단계다:

1. `web/src/core/ice_combat_effect_apply.ts` — 4개 적용 함수가 각자의 kind
   (`shield` / `heal` / `regen` / `buff`) 로 `import_vfx_deterministic(...)`
   를 호출해 `IceEffectOutcome.vfx` 를 채운다 (`:69`, `:105`, `:131`, `:173`).
2. `web/src/core/state_actions_combat.ts:289` — `enemyTurnVfx.push(...outcome.vfx)`.
3. `web/src/core/state_actions_combat.ts:473-476` — `enemyTurnVfx` 가
   `state.vfxInstances` 에 합쳐진다.

즉 **ADR-0231 (P2) 가 P6 의 VFX 절반을 이미 처리했다.** 남은 것은
**HUD glyph** 뿐이었다. 이 ADR 은 **배선을 새로 만들지 않았다** — 이미
있던 배선을 **검증하고** (테스트로 고정하고) 남은 절반 (glyph) 을
구현했다.

> **이 때문에 P6 는 "VFX 배선" 이 아니라 "glyph 추가" 로 착지했다.**
> 제안 문서가 P6 를 "① `IceEffectOutcome` 에 `vfx` 필드 추가" 로
> 기술했으나, 그 필드는 **ADR-0231 이 이미 추가해웠다.** 제안 문서는
> ADR-0231 이전 상태를 기준으로 쓰였다.

### P6 — ADR-0226 4종의 glyph

`web/src/renderer/vfx.ts` 의 `STATUS_GLYPHS` 에 3종을 추가했다.

| 효과 | 상태 kind | glyph | 이유 |
| --- | --- | --- | --- |
| `shield` | `shield` | `D` | **D**efense. `stun` 의 `S` 와 충돌하므로 다른 문자 필요 |
| `regen` | `regen` | `R` | **R**egeneration |
| `buff` | `powered` | `R` 와 다른 `P` — **P**owered | ADR-0226 의 `buff` 는 상태로 `powered` 로 저장된다 (`ice_combat_effect_apply.ts:158`) |

**`heal` 에는 glyph 이 없다.** `heal` 은 **순간 효과** 다 — 즉시 HP 를
복구하고 `statusEffects` 에 인스턴스를 남기지 **않는다**
(`ice_combat_effect_apply.ts:89-107`). 지속 상태가 아니므로 HUD 에
남을 것이 없다. glyph 을 정의해도 **도달 불가능** 하다.

### P14 — 타겟별 상태 HUD

`web/src/renderer/status_hud.ts` (신규) 가 순수하게 상태를 **타겟별 그룹**
으로 나눈다.

- `groupStatusByTarget(effects, activeIceIndex)` — 효과를 두 축으로 나눈다.
  - `target === "player"` → 플레이어 그룹.
  - `target === "ice"` → **로스터 슬롯별** 그룹. `iceIndex` 가 없으면
    **활성 ICE** 다 (`core/types.ts` 의 `StatusEffectInstance` 계약 —
    플레이어 측 `burn` / `slow` 가 `target: "ice"` + `iceIndex` 없음으로
    기록되는 이유).
- `formatStatusEntries(entries)` — `[GLYPH<턴>]` 형태. 예: `burn` 2턴
  남음 → `[B2]`, `shield` 3턴 + `powered` 2턴 → `[D3P2]`.
- `drawTargetStatus(grid, x, y, group, color)` — 그룹을 격자에 그린다.
  빈 그룹이면 **격자를 그대로 반환** 한다 (불필요한 재렌더 방지).

`web/src/renderer/combat_grid.ts` (신규) 가 `renderGrid` 를 `main.ts` 에서
**추출** 받아 배치 로직을 담당한다:

- **플레이어 행** (row 5, HP 바 옆) — 플레이어 그룹만.
- **각 ICE 행** (roster row) — **그 슬롯의** 그룹만. 활성 타겟 전용이
  아니다. 비활성 ICE 가 방패를 세웠다면 **그 ICE 의 행** 에 보인다.

`main.ts` 의 `renderGrid` 추출은 **순수 이동** 이다 — 로직 변경 없음.
추출 이유는 `main.ts` 가 import 시점에 **self-boot** 하므로 (canvas 필요)
vitest 가 이 함수를 테스트할 수 없었기 때문이다. 추출 후에는
`tests/combat_grid.test.ts` 가 **실제 전투 격자** 위에서 배치를 검증한다.

### 제안 문서와 다른 한 곳

제안 §4.1 은 P14 의 기준을 "**9종** glyph" 로 적었다. 이 ADR 은 **8종** 이다.
`shield` / `regen` / `powered` 3종 + 기존 5종 = 8. 제안이 9를 센 이유는
ADR-0226 의 **4종** (`shield` / `heal` / `regen` / `buff`) 을 그대로 센
것이다. **`heal` 은 순간 효과** 라 glyph 이 도달 불가능 하므로 —
**9종 에서 1종 을 뺀 것이 의도이며, 테스트가 이 사실을 고정한다.**

## 고려한 옵션

### Option 1 — VFX 배선 + glyph + 타겟별 HUD (선택)

- **설명**: 위와 같이 구현한다. VFX 배선은 **이미 존재** 했으므로
  검증만 하고, glyph 3종 을 추가하고, HUD 를 타겟별로 분리한다.
- **장점**: **밸런스가 증명 가능하게 무변경이다.** 12 grade 전부 0.0pp.
  `renderGrid` 가 테스트 가능해져 HUD 배치가 회귀로부터 보호된다.
- **Pillar 정합**: P6 (The Style) ✅ — ADR-0226 의 가치가 눈에 보인다.
  P14 (The Style) ✅ — "누가 무엇에 걸렸는가" 가 즉시 판독된다.
- **단점**: `renderGrid` 가 `main.ts` 에서 새 모듈로 이동했다. 이동은
  **순수 이동** 이고 `main.ts` 는 1991 → 1852 LOC 로 **줄었다**.

### Option 2 — glyph 만 추가하고 HUD 는 merged 유지

- **설명**: P6 만 반영하고 P14 를 건너뛴다.
- **단점**: **ADR-0226 의 4 효과는 보이지만** 어느 ICE 가 달았는지는
  여전히 모른다. 플레이어의 자가 `burn` 과 ICE 의 `burn` 이 계속 섞인다.
  제안이 명시한 **target 분리** 를 달성하지 못한다.
- **Pillar 정합**: 실패 (제안의 핵심 요구 미충족).

### Option 3 — 9종 glyph 을 그대로 정의

- **설명**: `heal` glyph 을 정의해 제안 문서의 "9종" 을 맞춘다.
- **단점**: **`heal` 은 `statusEffects` 에 존재하지 않는다.** 도달
  불가능한 glyph 을 정의하면 **테스트가 거짓말을 하게 된다** — "9종이
  있다" 는 사실이 무의미해진다.
- **Pillar 정합**: 실패 (도달 불가능한 정의).

### Option 4 — P7 / P8 까지 함께 구현

- **설명**: idle-turn pressure 와 crit threshold coupling 도 함께.
- **단점**: **전투 밸런스를 건드린다** — 별도 ADR 필요, ADR-0229 §A1
  drift check 필수.
- **Pillar 정합**: 실패 (범위 확장).

## 추천 (Recommendation)

**Option 1.** 두 제안 모두 순수 표시 계층이며 밸런스 수치에 관여하지
않는다. VFX 배선은 **이미 존재** 했으므로 새로 만드는 대신 **검증하고
고정** 하는 것이 옳다 (재발 방지).

**Option 3 은 명시적으로 배제한다.** `heal` glyph 은 도달 불가능하다.
**Option 4 는 명시적으로 배제한다.** P7 / P8 은 밸런스를 건드린다.

## 사용자 결정 (Decision)

**2026-10-29 — 제안 P6 와 P14 를 구현하되, VFX 배선은 이미 존재하므로
검증만 하고 glyph + 타겟별 HUD 에 집중하기로 결정했다.** 구현 완료·검증됨.

- [x] **Option 1 — glyph + 타겟별 HUD (VFX 배선은 검증만)** — **채택·구현됨**
- [ ] Option 2 — glyph 만 추가하고 HUD 는 merged 유지
- [ ] Option 3 — 9종 glyph 을 그대로 정의
- [ ] Option 4 — P7 / P8 까지 함께 구현

### 결정된 내용

1. **P6 — ADR-0226 효과의 HUD glyph.** `STATUS_GLYPHS` 에 `shield: "D"`,
   `regen: "R"`, `powered: "P"` 추가. 총 **8종**.
2. **`heal` 은 glyph 이 없다.** 순간 효과여서 `statusEffects` 에 남지
   않는다. 도달 불가능한 glyph 을 정의하지 않는다.
3. **P14 — 타겟별 그룹화.** `groupStatusByTarget` 가 플레이어 그룹과
   **로스터 슬롯별** ICE 그룹을 만든다. `iceIndex` 없는 ICE 대상 효과는
   활성 ICE 에 귀속된다.
4. **남은 턴 표기.** `[GLYPH<턴>]` 형식 — `[B2]` = 2턴 남음.
5. **배치.** 플레이어 glyph 는 **플레이어 HP 행** 옆. ICE glyph 는 **그
   ICE 의 이름 행** 옆 (활성 타겟 전용 아님).
6. **`renderGrid` 를 `renderer/combat_grid.ts` 로 추출.** 순수 이동.
   `main.ts` 는 1991 → 1852 LOC.
7. **표시 전용.** `GameState` · reducer · 데미지 공식 · calibration 배열 ·
   `ice_types.json` · `skill_defs` · `effects.json` **전부 미변경.**
8. **P7 / P8 은 하지 않는다.** 나머지 제안도 하지 않는다.
9. **기존 ADR 은 하나도 수정하지 않았다.** Accepted 결정은 immutable 이다
   (`AGENTS.md` §6). 관계는 이 ADR 에 기록했다.

## 결과 (Consequences)

### 긍정적 영향

- **ADR-0226 의 효과가 눈에 보인다.** "적이 방패를 세웠다" 가 HUD glyph
  로 읽힌다 — 전략적 예고가 된다.
- **"누가 무엇에 걸렸는가" 가 즉시 판독된다.** 플레이어의 자가 `burn` 과
  ICE 의 `burn` 이 다른 위치에 그려진다.
- **남은 턴이 보인다.** `[D3]` = 방패 3턴 남음. 방어 타이머를 예측할 수
  있다.
- **비활성 ICE 의 방패도 보인다.** 전투 중 시야가 넓어진다.
- **`renderGrid` 가 테스트 가능해졌다.** HUD 배치가 회귀로부터 보호된다.
- **`main.ts` 가 줄었다** (1991 → 1852 LOC). ADR-0110 모듈 사이즈 방향과
  부합.
- **밸런스가 증명 가능하게 무변경이다.**

### 부정적 영향 / 수용한 비용

- **HUD 폭이 늘었다.** glyph 이 최대 3종의 남은 턴 숫자를 붙이므로
  플레이어 행에 `[D3P2]` 처럼 최대 9자가 붙는다. `setText` 가 격자
  오른쪽 경계에서 잘라내므로 **wrap 은 되지 않는다** — 40-col 레이아웃
  회귀 테스트가 이를 검증한다.
- **glyph 문자가 늘었다.** `S` (stun) 와 `D` (shield) 가 나란히 있으면
  읽기 어렵다. `D` 는 대문자 `D` 다 — 소문자 `d` 가 아니라면 시차
  없이 구분되지만, **이건 미검증이다** (아래 「검증 한계」).
- **`renderGrid` 의 위치가 바뀌었다.** `main.ts` 의 private 함수가 아니라
  `renderer/combat_grid.ts` 의 export 다. 다른 코드가 이 함수를 참조하
  는 곳은 없다 (grep 확인).

### 후속 항목

1. **남은 제안** — P7 (idle-turn pressure — ADR-0229 §A1 필요), P8
   (crit threshold coupling — §A1 필요), P10 (accessibility wiring),
   P11 (onboarding), P12 (touch feedback), P13 (audio ducking — **다른
   ADR 에서 병행 진행 중**), P15 (`ice_intro` / `data_acquired`).
2. **`ST` / `SL` / `SM` / `SV` 같은 2문자 glyph** — `D` vs `S` 의 가독성
   문제가 실제로 bothering 하면 2문자 표기로 전환할 수 있다. 순수 표시
   변경이라 밸런스 영향 없음.
3. **`regen` / `powered` 의 남은 턴 단위** — `tickSource: "enemy"` 이므로
   남은 턴은 **적 턴** 기준이다. 플레이어 관점에서 "몇 번 더 맞으면
   풀리는가" 로 읽히므로, 이 의미가 HUD 에 명시되는지는 미검증이다.

## Implementation Status (2026-10-29)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:

**신규 파일 — 4개 (소스 2 + 테스트 2)**

- `web/src/renderer/status_hud.ts` — **P14.** `StatusGlyphEntry` (`:16`),
  `TargetStatusGroup` (`:23`), `statusGlyphFor` (`:30`),
  `groupStatusByTarget` (`:40`), `statusGroupForTarget` (`:80`),
  `formatStatusEntries` (`:91`), `formatTargetStatus` (`:100`),
  `drawTargetStatus` (`:107`).
- `web/src/renderer/combat_grid.ts` — **P14 + `renderGrid` 추출.**
  `renderGrid` (`:25`). 플레이어 행 (`:71`) · ICE 행 (`:106`) 배치.
- `web/tests/status_hud.test.ts` — **21** 개 `it()` (glyph 해석 · 타겟
  그룹화 · 턴 표기 · 격자 드로잉 · 경계 클리핑).
- `web/tests/combat_grid.test.ts` — **5** 개 `it()` (실제 전투 격자 위의
  플레이어/ICE 행 분리 · 비활성 ICE 행 · 40-col 회귀).

**변경된 파일 — 4개 (소스 2 + 테스트 2)**

- `web/src/renderer/vfx.ts` — **P6.** `STATUS_GLYPHS` 에 `shield: "D"` ·
  `regen: "R"` · `powered: "P"` 추가 (`:85-93`).
- `web/src/main.ts` — **P14 배선.** import (`:53-56`, `:79`),
  `groupStatusByTarget` 호출 (`:1534-1538`), `renderGrid` 호출부 인자
  교체 (`:1540-1548`). `renderGrid` **삭제** (`:1783-1924` → 모듈로 이동).
  `main.ts` 1991 → 1852 LOC.
- `web/tests/vfx.test.ts` — `STATUS_GLYPHS` assertion 갱신 (5종 → 8종,
  `:149-175`). **기존 assertion 을 약화하지 않았다** — 각 glyph 의 개별
  값 assertion 5건은 **전부 유지** 하고 **추가** 했다.
- `web/tests/ice_combat_effects.test.ts` — **P6 배선 검증.** combat path
  를 통한 `heal` / `regen` / `buff` VFX spawn 검증 3건 (`:438-473`),
  ADR-0226 효과의 타겟 그룹 귀속 검증 4건 (`:475-526`).

**테스트**

- `npm test` — **133 files / 3173 tests, 0 failures.** (ADR-0232 시점
  130 files / 3088 tests → **+3 files, +85 tests.**)
  - ※ ADR-0232 기록치는 130 files / 3088 tests 였다. 본 ADR 시점의
    전체 파일/테스트 수는 **다른 에이전트의 병행 작업 (P13 audio
    ducking) 을 포함한** 값이다.
- 신규 assertion 은 **변경 전 반드시 실패함을 확인했다.**
  - `tests/status_hud.test.ts` — 모듈 부재로 suite 자체가 실패.
  - `tests/combat_grid.test.ts` — 모듈 부재로 suite 자체가 실패.
  - `tests/vfx.test.ts` — "5 glyph mappings" assertion 이 **8** 을 기대하며
    실패 (`expected 5 to be 8` — 2건 실패).
  - `tests/ice_combat_effects.test.ts` — 새 import 모듈 부재로 suite
    자체가 실패.
  - **추가로**, `combat_grid.ts` 를 임시로 **구(舊) merged 동작** 으로
    되돌려 "구현이 실제로 검증하는지" 확인했다 — `combat_grid.test.ts`
    **5건 중 3건 실패** (플레이어 행 glyph 없음 · 두 행 미분리 · 비활성
    ICE 행 glyph 없음). 되돌린 뒤 전부 통과 확인.

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
byte-identical 하다. (표시 전용 변경이므로 예상된 결과다.)

**RNG draw count — 변화 없음.** `import_vfx_deterministic` 은 **RNG draw
0건** 이고, 이 ADR 은 **새 spawn site 를 만들지 않았다** — ADR-0231 의
기존 배선을 검증만 했다. 표시 계층(`renderer/`) 만 건드렸다.

**검증 한계 (정직하게 명시한다)**

- **실제 canvas 렌더링을 실행하지 않았다.** 검증된 것은 **격자 문자열**
  과 배치 좌표다. `AsciiRenderer.render()` 를 실제로 돌려 **픽셀** 을 본
  것은 아니다.
- **화면 위에서 실제로 읽히는지는 미검증이다.** `D` (shield) 와 `S`
  (stun) 가 나란히 있을 때 사람이 헷갈리는지는 **taste 판단** 이다
  (제안 §4.4 가 이 분류를 명시한다).
- **Playwright e2e 를 실행하지 못했다** — 브라우저와 live URL 이 필요하다.
- **`main.ts` 의 배선 자체는 코드 읽기로만 검증했다.** `main.ts` 는 import
  시점에 self-boot 하고 vitest 환경은 `node` 라서 import 할 수 없다.
  배선 검증은 `tests/combat_grid.test.ts` 가 **동일한 `renderGrid` 함수**
  를 직접 호출해 대신한다 — **`main.ts` 의 호출부 자체** 는 검증 대상이
  아니다.
- **ADR-0226 의 효과 *값* 은 검증하지 않았다.** 이미 정확히 적용되고
  있다는 전제 (그리고 `ice_combat_effects.test.ts` 의 기존 테스트) 를
  따른다. 이 ADR 은 값에 손대지 않았다.
- **LSP diagnostics 를 사용할 수 없었다** (daemon socket unreachable).
  그래서 **repo 가 자체로 mandate 한 gate 인 `tsc --noEmit` (strict) 이
  권위** 다.

**Notes**:

- **기존 assertion 을 하나도 약화·skip·삭제하지 않았다.** `vfx.test.ts` 의
  "5 glyph mappings" 는 **8로 갱신** 했지만 이는 제안이 명시적으로 요구한
  변경이며 (`web/tests/vfx.test.ts:150` 참조), 개별 glyph 값 assertion
  5건은 **전부 유지** 했다. **추가만** 했다.
- **`GameState` / `SaveSlot` 인터페이스 — 미변경** (schema bump 없음).
- **`web/src/data/effects.json`, `effects.d.ts`, `ice_types.json`,
  `missions.json`, `programs.json` — 미변경.** calibration 배열
  (`ENCOUNTER_HP_BY_GRADE`, `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`) 도
  미변경.
- **`web/src/core/ice_combat_effect_apply.ts` — 미변경.** 이미
  `vfx` 를 채우고 있었다. 이 ADR 은 **읽기만** 했다.
- **`web/src/core/ice_combat_effects.ts` — 미변경.** 효과의 크기와
  메커니즘은 그대로다.
- **`web/src/core/state_actions_combat.ts` — 미변경.** 배선이 이미
  존재했다.
- **`web/src/audio/` 및 `web/src/renderer/settings.ts` — 손대지 않았다.**
  (병행 진행 중인 다른 에이전트의 소유 영역.)
- **`Game/wet_run/log.md` 는 수정하지 않았다** (오케스트레이터 소유).
- **`docs/wiki/decisions/README.md` 는 수정하지 않았다** (오케스트레이터
  가 index 행을 추가한다).
- **`docs/design/combat-feel-and-interaction-proposal.md` — 미변경.**
- **ADR-0210 / 0219 / 0226 / 0229 / 0231 / 0232 를 포함한 기존 ADR 은
  하나도 수정하지 않았다** (immutable).
- **임시 파일을 남기지 않았다** (구현 검증용 백업 파일 삭제 확인).
- **re-calibration 은 하지 않았다.** ADR-0229 §A1 미발동 (grade 이동 0) →
  **re-baseline 불필요.**

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `docs/wiki/decisions/0234-effect-visibility-status-hud.md` — **신규**
  (이 ADR)
- `web/src/renderer/status_hud.ts` — **신규** (P14)
- `web/src/renderer/combat_grid.ts` — **신규** (P14 + `renderGrid` 추출)
- `web/src/renderer/vfx.ts` — `STATUS_GLYPHS` 3종 추가 (P6)
- `web/src/main.ts` — P14 배선 + `renderGrid` 이동
- `web/tests/status_hud.test.ts` — **신규**
- `web/tests/combat_grid.test.ts` — **신규**
- `web/tests/vfx.test.ts` — glyph assertion 갱신 + 추가
- `web/tests/ice_combat_effects.test.ts` — P6 배선 검증 추가

### 이번 결정으로 변경되지 않은 항목

- `web/src/core/ice_combat_effect_apply.ts`, `web/src/core/ice_combat_effects.ts`,
  `web/src/core/state_actions_combat.ts`, `web/src/core/state_actions_programs.ts`,
  `web/src/core/state.ts`, `web/src/core/types.ts`, `web/src/core/combat_engine.ts`,
  `web/src/core/ice_ai.ts`, `web/src/core/ice_scaling.ts`, `web/src/core/ice_crit.ts`,
  `web/src/core/ice_skills.ts`, `web/src/core/combat_models.ts` — **전부 미변경**
- `web/src/data/effects.json`, `effects.d.ts`, `ice_types.json`,
  `missions.json`, `programs.json` — **미변경**
- `GameState` / `SaveSlot` 인터페이스 — **미변경**
- `web/src/renderer/combat_vfx_render_combat.ts` — **미변경**
  (P6 은 **새 VFX kind 를 추가하지 않았다** — 제안 요구사항 그대로.
  `shield` / `heal` / `regen` / `buff` 렌더러는 이미 존재했다)
- `web/src/audio/manager.ts`, `web/src/renderer/settings.ts` — 다른 에이전트
  소유 영역
- `Game/wet_run/log.md`, `docs/wiki/decisions/README.md` — 오케스트레이터 소유
- ADR-0210 / 0219 / 0226 / 0229 / 0231 / 0232 — **미수정** (immutable)

## 관련 결정

- ADR-0226 (Non-damaging ICE 스킬 효과를 구현한다) — **이 ADR 이 가시화한
  효과의 owner.** `shield` / `heal` / `regen` / `buff` 의 매커니즘과
  magnitude 를 정의했다. **이 ADR 은 손대지 않았다** — 그 효과의 값은
  그대로이고 표시만 더했다. **ADR-0226 은 수정하지 않았다** (immutable).
- ADR-0231 (Combat-feel top-3 반영) — **직전 sibling.** P2 (VFX 배선) 가
  **P6 의 VFX 절반을 이미 처리** 했다. 이 ADR 은 그 배선을 **검증하고
  고정** 했을 뿐 새로 만들지 않았다. **ADR-0231 은 수정하지 않았다**
  (immutable) — 관계는 이 ADR 에 기록했다.
- ADR-0232 (Combat-feel tier 2 반영) — **직전 sibling.** P1 / P3 / P5 를
  처리했다. 이 ADR 은 P6 / P14 를 처리한다. **ADR-0232 은 수정하지
  않았다** (immutable).
- ADR-0210 (Combat VFX Effect Schema) — 27개 kind canonical taxonomy 의
  owner. 이 ADR 은 kind 를 **추가하지 않았다.** **ADR-0210 은 수정하지
  않았다** (immutable).
- ADR-0219 (non-damaging ICE 스킬 효과) — `IceEffectOutcome` 을 정의한
  owner. **수정하지 않았다** (immutable).
- ADR-0229 (Grade 난이도 곡선 재기준화) — **drift policy 의 owner.** 이 ADR
  의 0.0pp drift 로 §A1 미발동, re-baseline 불필요. §B hard invariant 전부
  성립. **ADR-0229 는 수정하지 않았다** (immutable).
- ADR-0195 (Accepted ADR Implementation Status Workflow) — 이 ADR 의
  Implementation Status 형식의 owner. **수정하지 않았다** (immutable).
- ADR-0110 (모듈 사이즈 정책) — 신규 모듈 2개가 모두 100–300 LOC 권장
  범위 안이다 (`status_hud.ts` 117 LOC, `combat_grid.ts` 166 LOC).
  `main.ts` 는 1991 → 1852 LOC 로 **139 LOC 감소**. **ADR-0110 은 수정하지
  않았다** (immutable).
- `docs/design/combat-feel-and-interaction-proposal.md` — 이 ADR 이 그
  §2 의 **P6** 와 **P14** 를 반영한다. 나머지 제안은 미반영.

## 변경 이력

- 2026-10-29: Draft 작성 (combat-feel 제안 문서 — P6 ADR-0226 효과 가시화
  + P14 상태 effect HUD 전면 개편)
- 2026-10-29: **Accepted (Option 1 — glyph + 타겟별 HUD, VFX 배선은
  검증만)** — 구현 완료·검증. **핵심 발견: ADR-0231 이 P6 의 VFX 배선을
  이미 구현해 두었다** — `IceEffectOutcome.vfx` → `enemyTurnVfx` →
  `state.vfxInstances` 경로가 살아 있었다. 남은 것은 **glyph** 뿐이어서
  P6 는 `STATUS_GLYPHS` 3종 추가로 착지했다. P14 는 **신규 모듈
  `renderer/status_hud.ts`** (타겟별 그룹화 + `[GLYPH<턴>]` 표기) 와
  **`renderer/combat_grid.ts`** (`renderGrid` 추출 — 테스트 가능화)로
  구현했다. **제안 문서의 "9종 glyph" 은 8종으로 착지** — `heal` 은 순간
  효과여서 도달 불가능하다. **12 grade 전부 0.0pp drift.** `npm test`
  133 files / 3173 tests 0 failures (+3 files / +85 tests). 신규 assertion
  은 **변경 전 실패 확인** 완료 — 모듈 부재로 suite 실패 + glyph count
  5≠8 + **구(舊) merged 동작으로 되돌렸을 때 `combat_grid.test.ts` 3/5
  실패**. **P7 / P8 및 나머지 제안은 미반영** — re-calibration 은 하지
  않았다.
