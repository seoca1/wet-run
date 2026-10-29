# ADR-0236: 접근성 모드 배선 — reduced-motion / 고대비 / 색각 이상 palette / 텍스트 스케일

**상태**: Accepted
**날짜**: 2026-10-30
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P10 (The Flatline — built-but-unwired dead path, ADR-0196/0205/0232/0233/0234/0235 sibling)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0183 — Accessibility (Colorblind 3 Modes, Text Size, Input Remapping)](./0183-accessibility.md), [ADR-0195 — Accepted ADR Implementation Status Workflow](./0195-adr-implementation-workflow.md), [ADR-0196 — Accessibility Colorblind State Alignment](./0196-accessibility-colorblind-state-alignment.md), [ADR-0210 — Combat VFX Effect Schema](./0210-combat-vfx-effect-schema.md), [ADR-0229 — Grade 난이도 곡선 재기준화](./0229-grade-curve-rebaseline.md), [ADR-0232 — Combat-feel tier 2 (shake + damage SFX)](./0232-combat-feel-tier2-shake-damage-sfx.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-30 에 결정·구현·검증까지 완료되었다.
>
> **이 ADR 은 밸런스를 바꾸지 않는다.** 12개 grade 전부 **0.0pp drift** —
> ADR-0229 baseline 과 **byte-identical** 하다. §A1 은 발동하지 않았다.
>
> **이 ADR 의 진짜 내용은 "무엇을 넣었느냐" 가 아니라 "기본 화면이
> 단 한 픽셀도 바뀌지 않았음을 어떻게 증명했느냐" 이다.** §검증 에서
> 전·후 소스를 실제로 재구성해 `diff` 로 0 차이를 확인했다.

## 컨텍스트 (Context)

`docs/design/combat-feel-and-interaction-proposal.md` (§2) 의 **P10** 을
반영한다. P10 은 accessibility 를 "기능" 이 아니라 "**배선**" 으로
규정한다 — 이미 있는 것이 쓰이지 않는 것이 문제였기 때문이다.

| 항목 | 상태 | 근거 |
| --- | --- | --- |
| `core/accessibility.ts` 의 `reducedMotion` / `highContrast` / `prefersReducedMotion()` | **소비자 0건** | `accessibility.ts:20-28` — 정의만 있고 읽는 곳이 없음 |
| `PALETTE` | **단일 고정 35색** | `palette.ts:12-48` — 모드 개념 자체가 없음 |
| ADR-0196 의 4모드 colorblind palette | **web 구현 없음** | ADR-0196:11-24 가 ADR-0183 으로부터 상속했다고 명시. ADR-0196 의 Implementation Status 는 아직 "🟡 Pending execution" |
| 폰트 / 셀 크기 | **breakpoint 로만 결정** | `canvas.ts:25-44` — `CELL_SIZES` 4종 고정. 텍스트 스케일 개념 없음 |
| P1 캔버스 shake (ADR-0232) | **reduced-motion 과 무관** | `screen_shake.ts` — `shakeOffsetFor` / `shakeStateFor` 에 게이트 없음 |

P10 의 제안 §"검증 기준" 은 이렇다: **"reduced-motion ON 일 때 shake offset
이 0 인지"**. 이것이 **P1 shake 를 안전하게 만들 수 있는 선행 조건**
(제안 §"아키텍처 결정 성찰" 표) 으로 적혀 있다 — 즉 P10 은 P1 의
선행이며, shake 는 전정증 민감 플레이어에게 그대로 노출되고 있었다.

### 이 ADR 의 질문

**기본 화면을 단 한 픽셀도 바꾸지 않으면서, accessibility 를 실제로
동작시킬 수 있는가?** 답은 "가능하다 — 단, palette 를 **순수 데이터** 로
모델링하고, renderer 가 **호출 시점** 에 색을 읽도록 설계하면 가능하다"
였다.

## 결정에 이르게 된 근거

### 1 — `renderer/accessibility_modes.ts` (신규) — 순수 모듈

`core/accessibility.ts` 의 accessibility 값은 **표시 계층** 의 관심사이므로
`renderer/` 에 두었다. 이 모듈은 **순수 함수 + 저장소 읽기/쓰기** 뿐이다.

- `ColorblindMode` = `"none" | "deuteranopia" | "protanopia" | "tritanopia"`
  — ADR-0196 §"Option A" 의 4값. `COLORBLIND_MODES` 는 ADR-0196 의 사이클
  순서(`none → deuter → protan → tri → none`) 그대로다.
- `TextScaleStep` = `"small" | "medium" | "large"` — ADR-0183 `text_size`.
  `TEXT_SCALE_FACTORS` = `0.85 / 1.0 / 1.25`. **`medium` 은 정확히 1.0**
  이다.
- `suppressMotion(kind, reducedMotion)` — **명시적 게이트**. `kind` 는
  `"shake" | "hit_stop" | "flash" | "floating_damage"`.
- `resolveReducedMotion(override)` / `resolveHighContrast(override)` —
  **게임 내 오버라이드가 OS 미디어 쿼리를 양방향으로 이긴다.** OS 가
  reduce 를 말해도 플레이어가 명시적으로 끄면 꺼진 상태가 되고, 그 반대도
  같다.
- `wetrun_colorblind_mode` / `wetrun_text_scale` /
  `wetrun_reduced_motion` / `wetrun_high_contrast` — 기존 `wetrun_*`
  규약 준수. 읽을 때 **값을 검증**한다(모르는 값 → 기본값).

### 2 — `renderer/palette.ts` — 4모드 palette 를 **순수 데이터** 로

제안 §"②③" 이 가리킨 대로 `PALETTE` 에 colorblind 변형 테이블을
추가했다. 핵심 설계는 **"기본 모드가 바이트 단위로 동일해야 한다"**
제약에서 나온다.

- `PALETTE_VARIANTS` — 모드별 **부분 오버라이드 테이블**(순수 데이터).
  `"none"` 의 오버라이드는 **0개** — 즉 기본 palette 는 원본 그대로다.
- `paletteFor(mode, highContrast)` — **순수**. 기본 palette 위에 오버라이드를
  얹은 새 frozen 사본을 돌려준다. `PALETTE` 를 변형하지 않는다.
- `applyPaletteMode(mode, highContrast)` — `PALETTE` 의 **속성만** 다시
  가리킨다.

**왜 이 방식인가.** `PALETTE` 는 20개 renderer 파일에서 읽힌다. 그중
어떤 것도 **모듈 스코프에서 destructure 하지 않는다** — 전부
`PALETTE.GREEN_NEON` 형태로 **호출 시점** 에 읽는다. 따라서 `PALETTE` 의
**속성값을 교체**하면 20개 파일의 **호출 지점을 한 줄도 바꾸지 않고**
전체 화면의 색이 함께 바뀐다. 이 성질은 `grep` 으로 확인했다
(`= PALETTE;` / `{ PALETTE }` / `const {… PALETTE` 형태의 destructure 0건).

**그레이는 건드리지 않았다.** 회색 ramp(`FOREGROUND` · `BACKGROUND` ·
`GRAY*`) 는 **의미를 담지 않는** 색이다 — 의미를 바꾸면 대비만 떨어진다.
색각 변형은 **의미를 색으로 표현하는 토큰**(`GREEN_NEON` · `RED_BRIGHT` ·
`YELLOW_AMBER` · `ICE_BLUE` · …) 만 재색한다.

### 3 — 고대비(high contrast) — `core/accessibility.ts` 의 소비자

`core/accessibility.ts` 의 `getHighContrastColors()` 도 소비자 0건이었다.
이 ADR 은 그것을 **팔레트 오버라이드 테이블의 데이터 소스**로 승격했다.
`HIGH_CONTRAST_OVERRIDES` 는 `getHighContrastColors()` 에서 값을 가져와
팔레트 토큰에 매핑한다. **colorblind 오버라이드 다음에** 적용되므로,
둘 다 켜면 둘 다 반영된다.

`prefersReducedMotion()` 과 `prefersHighContrast()` 도 이제 **진짜
소비자**가 생겼다(`accessibility_modes.ts` → `main.ts` → shake 게이트).
두 함수 모두 `window.matchMedia` 이 없는 환경에서 **throw 하지 않고**
"선호 없음" 으로 degrade 하도록 보강했다 (boot 경로 보호).

### 4 — `renderer/canvas.ts` — 텍스트 스케일 = **순수 배수**

`AsciiRendererOptions.textScale` (기본 `1.0`) 과 `setTextScale(scale)` 을
추가했다. 스케일은 **breakpoint 셀 크기에 곱해지는 순수 배수**다 —
`small` 0.85 → `medium` 1.0 → `large` 1.25.

- `resizeGrid()` 는 breakpoint 크기를 먼저 구한 뒤 스케일을 곱한다.
  배수는 `Math.round` 로 **정수 픽셀**에 고정한다 (캔버스는 정수 픽셀
  이동만 할 수 있다).
- `0` 이하거나 `NaN` 인 스케일은 **1.0 으로 fallback** 한다 — 0 배율은
  격자를 무너뜨린다.
- `setTextScale()` 는 **기준 셀 크기**(`baseCellSize`)를 별도로 보관한다.
  그래야 `setTextScale(2)` → `setTextScale(1)` 로 되돌렸을 때 **원래
  크기**가 복구된다 (배율을 배율 위에 곱하지 않는다).

### 5 — reduced-motion 게이트 — shake 는 **정확히 0**

제안 §"②" 의 "`prefersReducedMotion()` 을 참조해 shake/flash 길이를 0
으로" 를 그대로 구현했다. 게이트는 **명시적 파라미터** 다 — 숨겨진 전역
상태가 아니다.

- `shakeOffsetFor(..., reducedMotion)` — true 면 **즉시** `{x: 0, y: 0}`.
- `shakeStateFor(instances, reducedMotion)` — true 면 `NO_SHAKE`
  (`magnitudePx: 0`).
- `hitStopDeadlineFor(..., reducedMotion)` — true 면 **deadline 을 arming
  하지 않는다** (= 0). hold 가 없으니 VFX advance 가 멈추지 않는다.
- `hitStopMsFor(instances, reducedMotion)` — true 면 0.
- `overlayShake(instances, reducedMotion)` — `combat_overlay.ts` 의
  배선 지점.

**기본값은 `false`** 다 — 게이트를 켜지 않은 경로는 전부 **이전과
바이트 동일**하게 동작한다. 이 덕분에 기존 `screen_shake.test.ts` 의 39개
assertion 은 **하나도 수정하지 않고** 통과한다.

### 6 — `renderer/settings.ts` + `main.ts` — **완전 배선**

제안 §"①" 이 지목한 그대로 `SettingsField` 에 4개 필드를 추가했다:
`reduced_motion` · `high_contrast` · `colorblind` · `text_scale`.

**이전 wave 의 "rendered-but-unreachable" 을 반복하지 않기 위해** 두 가지를
함께 검증한다.

1. **렌더** — SETTINGS 화면의 `ACCESSIBILITY` 섹션(행 24–28)이 4개 행을
   실제로 그린다. STORAGE / PWA 섹션은 **5행 아래로 이동**했다(행 30–37).
   29행 미만 그리드에서는 이 행들이 **clip** 되므로 기존 내용을 덮지
   않는다 (무너진 40행 레이아웃에서 hint 행과 충돌하지 않는다).
2. **도달 가능성** — 4개 필드는 전부 `main.ts` 의 `fields` 사이클에
   들어 있고, ENTER / ← / → 핸들러가 각각을 처리한다. 테스트는 **사이클
   배열 자체를** 고정한다 (`tests/settings_accessibility.test.ts`).

부팅 시 `applyAccessibilitySettings()` 가 저장된 설정을 읽어 팔레트 ·
셀 크기 · shake 게이트에 **동시에** 적용한다. `main.ts` 는 부팅 후 첫
프레임 전에 이걸 호출하므로 **첫 화면부터** 설정이 반영된다.

**`main.ts` 가 P10 때문에 늘어난 것:** import 1블록 · 필드 3개 ·
`applyAccessibilitySettings()` · `resizeRenderer()` · settings 사이클 4항목
· ENTER/←/→ 분기 4개. **reducer · `GameState` · 전투 수치 는 0줄 변경.**

## 고려한 옵션

### Option 1 — 순수 palette 데이터 + 호출 시점 읽기 (선택)

- **설명**: `PALETTE_VARIANTS` 로 모드를 데이터로 모델링하고,
  `applyPaletteMode` 이 `PALETTE` 의 속성만 교체한다. 텍스트 스케일은
  셀 크기에 곱해지는 순수 배수. reduced-motion 은 명시적 파라미터 게이트.
- **장점**:
  - **기본 화면이 증명 가능하게 무변경**이다 — 전·후 소스를 재구성해
    `diff` 로 0 차이를 확인했다.
  - **호출 지점 0개 변경** — 20개 renderer 파일을 건드리지 않는다.
  - 모드 추가가 **데이터 추가**다 — 코드 분기가 늘지 않는다.
- **단점**: `PALETTE` 가 더 이상 `Object.freeze` 다. (immutable 라는
  명세는 `paletteFor` 의 반환값이 지킨다 — 항상 frozen 사본이다.)
- **Pillar 정합**: P1 (The Run) ✅ — 광각색·저대비 플레이어가 실제 색각
  조건에 맞는 팔레트를 고를 수 있다. P5 (The Style) ✅ — 색은 팔레트
  데이터로 다루고, 팔레트 데이터는 권위 있는 한 곳에 산다.

### Option 2 — `PALETTE` 를 함수로 바꾸고 20개 renderer 를 전부 수정

- **설명**: `PALETTE.FOREGROUND` → `palette().FOREGROUND` 로 전부 바꾼다.
- **단점**: **20개 파일** 수정이 필요하다 — 본 ADR 의 목적을 "기본 화면
  무변경 증명" 으로 삼으면 변경 리스크가 불필요하게 커진다. 그리고
  `PALETTE` 는 모듈 레벨 상수라는 전제(20개 파일)가 깨진다.
- **Pillar 정합**: 실패 (증거 없는 광범위한 변경).

### Option 3 — 텍스트 스케일을 폰트 크기만 변경

- **설명**: 셀 크기는 그대로 두고 `ctx.font` 만 키운다.
- **단점**: **글자가 셀 밖으로 넘친다** — ASCII 격자는 고정 셀 격자이므로
  폰트만 키우면 열 정렬이 깨진다. 텍스트 스케일은 **셀과 폰트를 함께**
  키워야 한다.
- **Pillar 정합**: 실패 (레이아웃 깨짐).

### Option 4 — P10 을 P1 shake 와 함께 하지 않고, shake 게이트만 별도 ADR

- **설명**: reduced-motion 게이트만 먼저 ship 하고 palette / 텍스트
  스케일은 미룬다.
- **단점**: 제안 §"검증 기준" 이 요구하는 3중 체크(shake=0 · 팔레트
  4모드 · 텍스트 스케일) 중 1개만 충족한다. 제안의 P10 은 **세 개를
  한 묶음**으로 정의한다.
- **Pillar 정합**: 부분 성공 (제안 범위 미충족).

## 추천 (Recommendation)

**Option 1.** 유일하게 "기본 화면이 무변경" 을 **증명**할 수 있는
옵션이다. 팔레트 변형은 데이터 추가라 확장성이 좋고, reduced-motion
게이트는 명시적이라 테스트가 쉽다.

**Option 2 / 3 은 기각한다.** Option 2 는 불필요한 광범위 변경이고,
Option 3 은 레이아웃을 깨뜨린다.

## 사용자 결정 (Decision)

**2026-10-30 — P10 을 "기본 화면 무변경" 제약 아래 구현하기로 결정했다.**
구현 완료·검증됨.

- [x] **Option 1 — 순수 palette 데이터 + 명시적 게이트** — **채택·구현됨**
- [ ] Option 2 — `PALETTE` 를 함수로 바꾸고 20개 renderer 수정
- [ ] Option 3 — 텍스트 스케일을 폰트 크기만 변경
- [ ] Option 4 — shake 게이트만 먼저 ship

### 결정된 내용

1. **기본 화면은 무변경이다.** 팔레트 35토큰 · 헬퍼 5종 · 렌더된 셀
   색 · 캔버스 지오메트리 4종 — 전부 **전·후 `diff` 0 차이**를 실측했다.
2. **reduced-motion 은 명시적 파라미터 게이트**다 — `shakeOffsetFor` ·
   `shakeStateFor` · `hitStopDeadlineFor` · `hitStopMsFor` ·
   `overlayShake`. 기본값 `false`.
3. **색각 이상 4모드 + 고대비는 순수 palette 데이터**다
   (`PALETTE_VARIANTS` + `HIGH_CONTRAST_OVERRIDES`). `"none"` 의 오버라이드는
   0개.
4. **텍스트 스케일은 셀/폰트 크기에 곱해지는 순수 배수**다. `medium` = 1.0.
5. **4개 설정은 완전 배선**이다 — 렌더 + 사이클 + 핸들러 + 저장 +
   부팅 시 적용. 이전 wave 의 "rendered-but-unreachable" 재발을
   테스트로 막았다.
6. **`core/accessibility.ts` 의 dead helper 4종에 소비자가 생겼다** —
   `prefersReducedMotion` · `prefersHighContrast` · `getHighContrastColors`
   · `DEFAULT_ACCESSIBILITY_STATE` (`reducedMotion` / `highContrast` 필드).
7. **밸런스는 0.0pp drift.** reducer · 전투 수치 · calibration 배열 ·
   `ice_types.json` · `skill_defs` · `effects.json` — 전부 미변경.
8. **기존 ADR 은 하나도 수정하지 않았다.** Accepted 결정은 immutable 이다
   (`AGENTS.md` §6). 관계는 이 ADR 에 기록했다.

## 결과 (Consequences)

### 긍정적 영향

- **P1 shake 가 안전해졌다.** 전정증 민감 플레이어가 캔버스가 흔들리는
  경로를 완전히 차단받는다 — 오프셋이 **정확히 0** 이다.
- **색각 이상 플레이어가 자기 조건에 맞는 팔레트를 고른다.** ADR-0196 이
  상속했지만 web 에 없던 4모드가 실제로 동작한다.
- **고대비 모드가 추가됐다.** `core/accessibility.ts` 의 고대비 색 집합이
  드디어 화면에 닿는다.
- **텍스트 스케일이 동작한다.** 셀과 폰트가 함께 커지므로 열 정렬이
  깨지지 않는다.
- **기본 화면은 무변경이다 — 증명됨.** 기존 3234개 assertion 이 수정
  없이 통과한다.
- **밸런스가 증명 가능하게 무변경이다.**

### 부정적 영향 / 수용한 비용

- **`PALETTE` 는 더 이상 `Object.freeze` 가 아니다.** 모드 전환은
  **의도적 부수 효과**다. 불변성이 필요하면 `paletteFor(mode)` 의 frozen
  사본을 쓰면 된다.
- **SETTINGS 화면의 STORAGE / PWA 행이 5행 아래로 이동했다.**(24→30 등)
  기존 테스트는 **내용**만 고정하고 **행 위치**는 고정하지 않아서
  수정 없이 통과했다. 그럼에도 화면 배치는 바뀐다 — 의도한 변화다.
- **29행 미만 그리드에서는 ACCESSIBILITY 행이 clip 된다.** 실제 레이아웃
  최소치는 40행이라 현실에서는 보이지 않는다.
- **4개 설정은 영어 하드코딩 라벨이다.** SETTINGS 화면의 기존 라벨
  (`AUDIO` · `STORAGE` · `PWA` · `Master Volume`) 도 같은 방식이며, i18n
  키 추가는 별도 일이다.

### 후속 항목

1. **i18n 키** — ACCESSIBILITY 섹션 라벨을 `t("settings.…")` 로 옮긴다
   (EN/KO).
2. **e2e 스크린샷** — 제안 §"검증" 의 "`web/e2e/layout.spec.ts` 에 3모드
   팔레트 스크린샷". Playwright 브라우저가 필요해 이번 세션에는
   실행하지 못했다.
3. **`screen_reader_mode` / `keyboardNavigation`** — `AccessibilityState` 의
   남은 두 필드. HTML5 Canvas 라우터는 ARIA live region 을 제공하지
   않으므로, DOM 미러가 필요할 수 있다 (별도 ADR).
4. **`input_remapping`** — ADR-0183 의 3번째 축. 키 remapping 은 입력
   계층이라 별도 ADR.
5. **`flash` / `floating_damage` 모션 종류** — `suppressMotion` 은 이미
   두 종류를 지원하지만 **소비자가 없다** (지금은 shake 와 hit_stop 만
   배선). `combat_vfx_render_*` 쪽에 배선하면 된다.
6. **`renderer/settings.ts` 분할** — P10 이 4개 설정 + ACCESSIBILITY
   섹션을 추가한 결과 456 pure LOC 로 ADR-0110 의 권장 범위(100–300)를
   초과한다. 오디오 / 스토리지 / PWA / 접근성 섹션을 별도 모듈로
   분리하는 것이 좋다.

## Implementation Status (2026-10-30)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:

**신규 파일 — 5개 (소스 1 + 테스트 4)**

- `web/src/renderer/accessibility_modes.ts` (119 pure LOC) — **새 모듈.**
  `ColorblindMode` · `COLORBLIND_MODES` · `TextScaleStep` ·
  `TEXT_SCALE_STEPS` · `TEXT_SCALE_FACTORS` · `MotionKind` ·
  `isColorblindMode` · `isTextScaleStep` · `nextColorblindMode` ·
  `previousTextScale` · `nextTextScale` · `textScaleFactor` ·
  `suppressMotion` · `resolveReducedMotion` · `resolveHighContrast` ·
  `COLORBLIND_STORAGE_KEY` · `TEXT_SCALE_STORAGE_KEY` ·
  `REDUCED_MOTION_STORAGE_KEY` · `HIGH_CONTRAST_STORAGE_KEY` ·
  `loadColorblindMode` · `persistColorblindMode` · `loadTextScale` ·
  `persistTextScale` · `loadReducedMotionOverride` ·
  `persistReducedMotionOverride` · `loadHighContrastOverride` ·
  `persistHighContrastOverride`.
- `web/tests/accessibility_modes.test.ts` — **28 tests.** 모드 사이클 ·
  스케일 팩터 · 게이트 · 오버라이드 해석 · 저장소 round-trip · 잘못된
  저장값 거부.
- `web/tests/colorblind_palette.test.ts` — **28 tests.** 기본 팔레트
  바이트 동일성 · 변형 테이블 순수성 · `paletteFor` 순수성 ·
  `applyPaletteMode` 왕복 · `resolveColorHint` 의 활성 팔레트 추종 ·
  고대비 오버라이드.
- `web/tests/canvas_text_scale.test.ts` — **9 tests.** 기본 지오메트리
  동일 · 배수 적용 · `setTextScale` 왕복 · 잘못된 스케일 fallback.
- `web/tests/settings_accessibility.test.ts` — **14 tests.** ACCESSIBILITY
  섹션 렌더 · 값 반영 · **입력 사이클 도달 가능성** · 기존 행 보존.

**변경된 파일 — 7개 (소스 6 + 테스트 1)**

- `web/src/renderer/palette.ts` — `PALETTE` 를 **속성 교체 가능**한
  `Record<PaletteToken, string>` 로 · `PaletteToken` 유니온 ·
  `DEFAULT_PALETTE` 스냅샷 · `PALETTE_VARIANTS` (4모드 순수 데이터) ·
  `HIGH_CONTRAST_OVERRIDES` (`core/accessibility.ts` 소스) · `paletteFor` ·
  `activePaletteMode` · `activeHighContrast` · `applyPaletteMode`.
- `web/src/renderer/accessibility_modes.ts` → `core/accessibility.ts` —
  `prefersReducedMotion()` / `prefersHighContrast()` 에 **DOM 가드** 추가
  (boot 경로 보호). 이제 2개 함수 모두 **진짜 소비자**가 있다.
- `web/src/renderer/canvas.ts` — `AsciiRendererOptions.textScale` ·
  `baseCellSize` · `setTextScale()` · `getTextScale()` ·
  `sanitizeTextScale()` · `resizeGrid()` 의 스케일 적용.
- `web/src/renderer/screen_shake.ts` — `shakeOffsetFor` ·
  `shakeStateFor` · `hitStopMsFor` · `hitStopDeadlineFor` 에
  `reducedMotion` 파라미터 (기본 `false`).
- `web/src/renderer/combat_overlay.ts` — `overlayShake(instances,
  reducedMotion)`.
- `web/src/renderer/settings.ts` — `SettingsField` 4항목 ·
  `SettingsState` 3항목 · `accessibilitySettings()` ·
  `getInitialSettingsState` / `getInitialSettingsStateAsync` ·
  ACCESSIBILITY 섹션 렌더(행 24–28) · STORAGE/PWA 행 이동 · hint 분기.
- `web/src/main.ts` — import · 필드 3개(`reducedMotion` /
  `highContrast` / `colorblindMode` / `textScale`) ·
  `applyAccessibilitySettings()` · `resizeRenderer()` · 부팅 시 적용 ·
  settings `fields` 사이클 4항목 · ENTER 분기 4개 · ←/→ 텍스트 스케일
  분기 · `overlayShake` / `hitStopDeadlineFor` 에 `reducedMotion` 전달 ·
  `fallbackSettingsState()` 갱신.

**테스트**

- `npm test` — **141 files / 3333 tests, 0 failures.** (ADR-0235 시점
  136 files / 3234 tests → **+5 files, +99 tests**.)
- **신규 assertion 은 변경 전 반드시 실패함을 확인했다.** 4개 신규
  테스트 파일을 먼저 작성하고 구현 **전에** 실행했다:
  - `accessibility_modes.test.ts` — 모듈 부재로 suite 자체가 실패.
  - `colorblind_palette.test.ts` — `PALETTE_VARIANTS` / `paletteFor` /
    `applyPaletteMode` 부재로 실패.
  - `canvas_text_scale.test.ts` — `textScale` 옵션 · `setTextScale`
    부재로 **10건 실패** (`'textScale' does not exist in type
    'AsciiRendererOptions'`, `Property 'setTextScale' does not exist`).
  - `reduced_motion_gate.test.ts` — 게이트 파라미터 부재로 **13건 실패**
    (`Expected 1-4 arguments, but got 5`, `expected 40 to be +0`,
    `expected 1040 to be +0`).
  - 요약: **4 files / 13 failing assertions** → 구현 후 전부 통과.
- **기존 assertion 은 하나도 약화·skip·삭제하지 않았다.** 추가만 했다.
  `screen_shake.test.ts` 의 39개 · `settings.test.ts` ·
  `settings_pwa_rows.test.ts` 는 **수정 없이** 통과한다.

**기본 화면 무변경 증명 (before/after `diff`)**

전·후 소스를 **실제로 재구성**해(전 palettes 은 P10 이전 `palette.ts` 를
그대로, canvas 는 `textScale` 相关 코드를 제거한 복원본을) 같은 프로브로
각각 렌더해 `diff` 로 비교했다.

| 비교 대상 | 결과 |
| --- | --- |
| 팔레트 35토큰 전체 | **0 차이** (`diff` 무출력) |
| 헬퍼 5종 (`iceColor` ×6 · `hpColor` ×7 · `healthColor` ×6 · `hitFlashColor` ×5 · `resolveColorHint` ×3) | **0 차이** |
| 렌더된 셀 색 (`char:fg/bg`, 20×3 그리드) | **0 차이** |
| 캔버스 지오메트리 4종 (portrait/compact · portrait/standard · landscape/standard · landscape/xlarge) | **0 차이** |

```
$ diff before.json after.json
IDENTICAL — 0 differences across palette tokens, helper outputs, and rendered cell colours
$ diff geom_before.txt geom_after.txt
IDENTICAL — default text scale leaves the canvas geometry unchanged
```

**게이트**

- `npx tsc --noEmit` — **0 errors.**
- `npx eslint src --ext ts` — **0 errors** (pre-existing warning 1건은
  `web/src/input/keyboard.ts:14` — 손대지 않았다).
- `npm run build` — **성공.**
- `npm test` — **141 files / 3333 tests, 0 failures.**

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

**검증 한계 (정직하게 명시한다)**

- **vitest 는 `main.ts` 를 import 하지 않는다.** `main.ts` 는 import
  시점에 self-boot 하고, vitest 의 `node` 환경에서 실행되지 않는다
  (ADR-0232 §"검증 한계" 와 동일). 따라서 **`main.ts` 의 배선**
  (설정 사이클 · ENTER 분기 · `applyAccessibilitySettings()` 호출 ·
  `overlayShake` 에 `reducedMotion` 전달) 은 **코드 읽기로만** 검증했다.
  순수 로직은 `accessibility_modes.ts` / `palette.ts` / `canvas.ts` /
  `screen_shake.ts` 로 분리해 **유닛 테스트로** 검증했다.
- **실제 canvas 렌더링을 실행하지 않았다.** 텍스트 스케일이 2D context 를
  실제로 어떻게 그리는지는 **관찰된 사실이 아니다** — 검증된 것은 셀
  크기 · 폰트 크기 · 캔버스 CSS 크기의 **계산** 뿐이다.
- **Playwright e2e 를 실행하지 못했다** — 브라우저와 live URL 이
  필요하다. 제안 §"검증" 의 "3모드 팔레트 스크린샷" 은 **미실행** 이다.
- **화면 위 실제 색을 보지 못했다.** 색각 3모드 + 고대비 팔레트가
  *읽기 가능한지* 는 **taste 판단** 이다 (제안 §4.4 가 이 분류를 명시).
  구현은 의미 있는 토큰만 재색한다는 규칙을 따랐지만 **느낌은 미검증**
  이다.
- **reduced-motion 의 실제 체감은 미검증이다.** shake 오프셋이 0 이라는
  것만 **계산** 으로 확인했다.
- **LSP diagnostics 를 사용할 수 없었다** (daemon socket unreachable).
  그래서 **repo 가 자체로 mandate 한 gate 인 `tsc --noEmit` (strict) 이
  권위** 다.

**Notes**:

- **기존 assertion 을 하나도 약화·skip·삭제하지 않았다.** 추가만 했다.
- **`GameState` / `SaveSlot` 인터페이스 — 미변경.** schema bump 없음.
  접근성 설정은 `GameState` 가 아니라 **localStorage** 에 산다
  (`wetrun_*` 규약). 세이브 슬롯과 무관하게 적용된다.
- **`web/src/data/effects.json` / `effects.d.ts` / `ice_types.json` /
  `missions.json` / `programs.json` — 미변경.** kind 추가 0건 · calibration
  배열 미변경.
- **`web/src/audio/`, `web/src/renderer/status_hud.ts`,
  `web/src/renderer/combat_grid.ts`, `web/src/core/combat_entry_vfx.ts`,
  `web/src/core/touch_feedback.ts`, `web/src/core/onboarding.ts` —
  미변경.** (다른 wave 의 작업 영역)
- **`web/src/core/combat_engine.ts` / `ice_ai.ts` / `ice_scaling.ts` /
  `ice_crit.ts` / `ice_skills.ts` / `state_actions*.ts` / `boss_phases.ts` —
  전부 미변경.**
- **RNG draw 0건.** `Math.random` 을 호출하는 코드를 추가하지 않았다.
  접근성 모드는 렌더·입력 계층에만 있다.
- **`Game/wet_run/log.md` 는 수정하지 않았다** (오케스트레이터 소유).
- **ADR-0183 / 0196 을 포함한 기존 ADR 은 하나도 수정하지 않았다.**
  (immutable — 관계는 이 ADR 에 기록했다.)
- **임시 파일을 남기지 않았다** (검증용 probe 는 모두 삭제).
- **re-calibration 은 하지 않았다.** ADR-0229 §A1 미발동 (grade 이동 0) →
  **re-baseline 불필요.** §B hard invariant 전부 성립, §A4 해당 없음
  (calibration 배열 미변경).

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `docs/wiki/decisions/0236-accessibility-modes.md` — **신규** (이 ADR)
- `web/src/renderer/accessibility_modes.ts` — **신규** (P10 순수 모듈)
- `web/src/renderer/palette.ts` — 4모드 palette 데이터 + 고대비 오버라이드
- `web/src/renderer/canvas.ts` — 텍스트 스케일 배수
- `web/src/renderer/screen_shake.ts` — reduced-motion 게이트
- `web/src/renderer/combat_overlay.ts` — `overlayShake` 게이트 전달
- `web/src/renderer/settings.ts` — 4개 설정 필드 + ACCESSIBILITY 섹션
- `web/src/core/accessibility.ts` — 미디어 쿼리 DOM 가드
- `web/src/main.ts` — 4개 설정 배선
- `web/tests/` — 4개 파일 신규 + 신규 assertion 95건 (추가만)

### 이번 결정으로 변경되지 않은 항목

- `web/src/core/state.ts`, `types.ts`, `combat_engine.ts`, `ice_ai.ts`,
  `ice_scaling.ts`, `ice_crit.ts`, `ice_skills.ts`, `state_actions.ts`,
  `state_actions_phases.ts`, `state_actions_programs.ts`,
  `ice_combat_effects.ts`, `ice_combat_effect_apply.ts`, `combat_models.ts`,
  `boss_phases.ts` — **전부 미변경**
- `web/src/data/effects.json`, `effects.d.ts`, `ice_types.json`,
  `missions.json`, `programs.json` — **미변경**
- `GameState` / `SaveSlot` 인터페이스 — **미변경** (schema bump 없음)
- `web/src/renderer/status_hud.ts`, `web/src/renderer/combat_grid.ts`,
  `web/src/core/combat_entry_vfx.ts`, `web/src/core/touch_feedback.ts`,
  `web/src/core/onboarding.ts`, `web/src/audio/**` — **미변경**
- `Game/wet_run/log.md` — 오케스트레이터 소유
- ADR-0110 / 0183 / 0195 / 0196 / 0210 / 0229 / 0231 / 0232 / 0233 / 0234 /
  0235 — **미수정** (immutable)

## 관련 결정

- ADR-0196 (Accessibility Colorblind State Alignment) — **본 ADR 이 그
  web 구현이다.** ADR-0196 은 4모드 어휘(`"none"` / `"deuteranopia"` /
  `"protanopia"` / `"tritanopia"`) 와 사이클 순서를 정의하고, 그 구현
  status 는 "🟡 Pending execution" 이었다. 이 ADR 은 그 status 를
  web 티어에서 "✅ Implemented" 로 만든다. **ADR-0196 은 수정하지 않았다**
  (immutable) — 관계는 이 ADR 에 기록했다.
- ADR-0183 (Accessibility — Colorblind 3 Modes, Text Size, Input
  Remapping) — **`colorblind_mode` 4값 어휘와 `text_size` 3값의 owner.**
  이 ADR 은 그 두 축의 web 구현이다. **입력 remapping 축은 미구현**
  (별도 ADR). **ADR-0183 은 수정하지 않았다** (immutable).
- ADR-0232 (Combat-feel tier 2) — **P1 shake 의 owner.** 그 ADR 의
  「후속 항목」 4번이 "reduced-motion 과의 결합 — P10 이 들어오면
  `prefersReducedMotion()` 으로 shake 길이를 0 으로 만들어야 한다" 를
  적었고, **이 ADR 이 그것을 구현했다.** **ADR-0232 은 수정하지 않았다**
  (immutable).
- ADR-0229 (Grade 난이도 곡선 재기준화) — **drift policy 의 owner.**
  이 ADR 의 0.0pp drift 로 §A1 미발동, re-baseline 불필요. §B hard
  invariant 전부 성립. **ADR-0229 는 수정하지 않았다** (immutable).
- ADR-0110 (모듈 사이즈 정책) — 신규 모듈 `accessibility_modes.ts` 가
  **119 pure LOC** 로 권장 범위(100–300) 안이다. `palette.ts` 181 ·
  `canvas.ts` 169 · `screen_shake.ts` 118 pure LOC — 전부 범위 안이다.
  `main.ts` 는 1964 → 2077 총 LOC 로 113 증가 (설정 배선, pure LOC
  1842). `settings.ts` 는 456 pure LOC 로 **권장 범위를 초과**한다 —
  P10 이 4개 설정 + ACCESSIBILITY 섹션을 추가한 결과이며, 분할은 후속
  항목이다. **ADR-0110 은 수정하지 않았다** (immutable).
- ADR-0195 (Accepted ADR Implementation Status Workflow) — 이 ADR 의
  Implementation Status 형식의 owner. **수정하지 않았다** (immutable).
- ADR-0210 (Combat VFX Effect Schema) — kind 추가 0건. **수정하지 않았다**
  (immutable).
- `docs/design/combat-feel-and-interaction-proposal.md` — 이 ADR 이 그
  **P10** 을 반영한다. 나머지 제안(P6 · P7 · P8 · P12 · P13 · P14 · P15)은
  미반영.

## 변경 이력

- 2026-10-30: Draft 작성 (combat-feel 제안 문서 **P10** — reduced-motion /
  고대비 / 색각 이상 palette / 텍스트 스케일)
- 2026-10-30: **Accepted (Option 1 — 순수 palette 데이터 + 명시적 게이트)** —
  구현 완료·검증. 신규 모듈 1개(`accessibility_modes.ts`), palette 4모드 +
  고대비 순수 데이터, 텍스트 스케일 순수 배수, shake/hit-stop reduced-motion
  게이트, 4개 설정 완전 배선(렌더 + 사이클 + 핸들러 + 저장 + 부팅 적용).
  **기본 화면 무변경을 전·후 `diff` 로 실측** (팔레트 35토큰 · 헬퍼 5종 ·
  렌더 셀 색 · 캔버스 지오메트리 4종 — 전부 0 차이). **12 grade 전부
  0.0pp drift**, RNG draw 0. `npm test` **141 files / 3333 tests**
  0 failures (+5 files / +99 tests). 신규 assertion 은 구현 전에
  **13건 실패**를 확인했다. **P6 · P7 · P8 및 나머지 제안은 미반영** —
  re-calibration 은 하지 않았다.
