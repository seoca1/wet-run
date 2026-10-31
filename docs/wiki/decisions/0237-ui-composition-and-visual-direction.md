# ADR-0237: UI 화면 구성 개편 + 비주얼 방향 — B // "Green Grid"

**상태**: Accepted
**날짜**: 2026-10-31
**결정자**: 사용자 (프로젝트 오너)
**우선순위**: P2 (The Style — 전 화면 시각 정체성, 트리아지 §4 V1–V5)
**관련**: [ADR-0002 — 비주얼 스타일](./0002-rendering-style.md), [ADR-0018 — Combat Animation](./0018-combat-animation.md), [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0183 — Accessibility (Colorblind 3 Modes, Text Size, Input Remapping)](./0183-accessibility.md), [ADR-0195 — Accepted ADR Implementation Status Workflow](./0195-adr-implementation-workflow.md), [ADR-0196 — Accessibility Colorblind State Alignment](./0196-accessibility-colorblind-state-alignment.md), [ADR-0198 — Resolution Compatibility](./0198-resolution-compatibility-and-qa-agents.md), [ADR-0199 — Wet Run Web MVP](./0199-wetrun-web-mvp.md), [ADR-0214 — 모바일 터치 대상 WCAG 최소 크기 충족](./0214-adr-mobile-touch-target-size.md), [ADR-0236 — 접근성 모드 배선](./0236-accessibility-modes.md), [UI 개편 트리아지 (2026-10-31)](../../design/ui-overhaul-triage-2026-10-31.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-31 에 프로젝트 오너가
> 방향을 결정했다. **구현은 부분 진행 중이다** — 트리아지 §3 1단계
> (V4·V5·U3·X3) 는 커밋 `4c8f40f1`, 캔버스 지오메트리(V1·V3) 는 `e9eb6f1`,
> 패널 헬퍼 모듈은 `133286a`. 나머지(프레임 적용 · `main.ts` 분해)는
> §Implementation Status 참조.
>
> **이 ADR 은 밸런스를 건드리지 않는다.** 바뀌는 것은 표시 계층
> (`web/index.html` 의 inline `<style>`, `web/src/renderer/`, `web/src/input/touch.ts`)
> 뿐이다. reducer · `GameState` · 전투 수치 · calibration 배열은 범위 밖이다.
>
> **이 ADR 의 진짜 내용은 "어떤 색을 골랐느냐" 가 아니라 "왜 접근성
> 변형이 이미 깔려 있는 색을 기준으로 골랐느냐" 다.** 프레임 색은
> ADR-0236 의 색각 변형 테이블이 이미 재색하는 토큰 위에 얹는다.

## 컨텍스트 (Context)

증거 기반은 [`docs/design/ui-overhaul-triage-2026-10-31.md`](../../design/ui-overhaul-triage-2026-10-31.md)
(이하 **트리아지**) 의 §4 "오케스트레이터 실측 시각 문제 5종" 이다.
트리아지 §2.1 은 V1–V3 를 "모든 화면의 시각 정체성 변경 — ADR-0002 /
ADR-0183 / ADR-0199 와 접점" 이라는 이유로 **신규 ADR 필요** 로 분류했다.
이 ADR 이 그 결정이다. V4 / V5 는 트리아지 §2.2 에서 순수 구현으로
분류됐지만, 같은 화면 프레임 안에서 처리해야 하므로 여기에 함께 묶는다.

| ID | 문제 | 코드 원인 (트리아지 인용, 2026-10-31 작업 트리) |
| --- | --- | --- |
| **V1** | 큰 미사용 검은 공간 / 내용이 화면 상단에 몰림 | canvas CSS 크기를 `열 수 × 셀 px` 로 고정 (`web/src/renderer/canvas.ts:128-134`) 한 뒤 CSS 가 `max-width: 100vw; max-height: 100vh; width/height: auto` 로 **축소만** 한다 (`web/index.html:41-44`) — 확대 경로가 없다 |
| **V2** | 패널·테두리·구획 부재 | 메인 메뉴·설정은 `─` 구분선 1줄뿐 (`web/src/renderer/menu_main.ts:99`, `web/src/renderer/settings.ts:250`). 미션 선택 (`web/src/main.ts:273-307`) 과 전투 (`web/src/renderer/combat_grid.ts`) 는 테두리 0. 그리드와 HUD 사이는 1셀 띄우기뿐 (`canvas.ts:201`). 반면 튜토리얼·대화·엔딩·스테이지는 박스 문자 사용 (`web/src/renderer/tutorial.ts:97`, `web/src/renderer/menu_dialogue.ts:36`, `:218`, `web/src/renderer/menu_endings.ts:40`, `web/src/renderer/menu_stages.ts:270`) → **화면 간 불일치** |
| **V3** | 작은 monospace 글자 vs 텍스트 스케일 옵션 | ADR-0236 의 스케일은 셀 크기 배수 (`web/src/renderer/accessibility_modes.ts:58-63` — 0.85 / 1.0 / 1.25, `canvas.ts:92-102`). canvas 가 커져도 `index.html:41-42` 의 `max-*` 가 다시 축소한다 → **스케일 옵션이 상쇄된다** |
| **V4** | 우상단의 설명 없는 초록 테두리 박스 | `#status-overlay` 가 `position: fixed; top: 8px; right: 8px; border: 1px solid #00ff41` 로 **항상 표시** (`index.html:64-77`, 요소 `:136`). `web/src/` 안에 이 요소에 쓰는 코드 **0건** (grep `status-overlay`) |
| **V5** | 터치 타깃 44px 미만 | 버튼이 vw/vh 상대 단위이고 **px 하한이 없다** — B 버튼 `size: "12vw"` (`web/src/input/touch.ts:115`), 프로그램 버튼 `min-width: 8vw` (`touch.ts:166`, `:184`) |

### 실측 수치 (1280×720 뷰포트)

- 셀 8×16px (`canvas.ts:27-32` 의 `standard_landscape`) × 128열·60행
  → canvas CSS 크기 **1024×960px**.
- 720px 높이에 맞춰 **약 0.75배** 로 축소 → 실효 셀 **약 6×12px**.
- 축소된 폭 약 768px → 좌우에 **각각 약 256px** 의 검은 띠.
- 트리아지 §4 V1 의 "약 0.67배" 는 `xlarge` breakpoint (셀 10×18) 를
  가정한 **계산값**이다. 위 수치는 실제 뷰포트에서 측정한 값이며,
  breakpoint 가 다를 뿐 결론 (축소만 있고 확대가 없다) 은 같다.

### 이 ADR 의 질문

**ASCII / Canvas2D 정체성을 유지하면서, 모든 화면이 한 프레임 언어를
쓰고 화면 전체를 쓰게 만들 수 있는가 — 그리고 그 프레임의 기준색을
무엇으로 둘 것인가?** 기준색 후보 세 개는 Manus 가 생성한 컨셉 시트
`docs/design/manus-concepts-2026-10-31/index.html` (읽기 전용 참고 자료)
에 A / B / C 로 정리돼 있다.

### 지켜야 할 톤 제약 (`docs/wiki/world/style_guide.md`)

이 ADR 의 어떤 선택도 아래를 깨지 않는다.

- **검은 배경 · 거친 monospace** — 스타일 가이드 §"게임 시각화 → ASCII":
  "검은 배경 / 형광 그린, 시안, 마젠타, 노랑, 흰색 / 거친 monospace 폰트 /
  C64 / amber monitor 분위기".
- **회피 목록** — §"회피할 것 → 미학": 글래스 모피즘 / 애플 디자인 어휘,
  홀로그램 푸른빛, 미니멀 / 퓨어 화이트 미학, 밝은 색조의 미래.
  → 반투명 블러 패널, 둥근 카드, 그라데이션 광택을 **도입하지 않는다**.
- **너무 깔끔하지 않다** — §"핵심 톤": 프레임은 정돈하되, 터미널이
  "작동 중인 고물" 처럼 보여야 한다. 테두리는 박스 문자이지 벡터 선이
  아니다.
- **용어** — 깁슨 용어만 쓴다 (ICE, deck, console cowboy, construct).
  라벨에 다른 작품의 용어를 쓰지 않는다 (`AGENTS.md` §4).

## 결정에 이르게 된 근거

### 1 — 기준색: 왜 GREEN_NEON 인가 (접근성 반경)

현재 web 렌더러의 기준 신호색은 이미 `PALETTE.GREEN_NEON` (`#00ff41`,
`web/src/renderer/palette.ts:69`) 이다 — 메뉴 제목, 선택 마커, 미션
선택 강조, 터치 버튼 테두리 (`index.html` 의 `#wetrun-gamepad-root button`)
가 전부 이 색이다.

ADR-0236 의 색각 변형 테이블 `PALETTE_VARIANTS` (`palette.ts:115` 부터) 는
**녹색/적색 의미 분할** 위에 설계돼 있다.

- `deuteranopia` — `GREEN_NEON` → `#e8d44d` (노랑 계열), `RED_BRIGHT` →
  `#7a4fd0`, `ALARM_RED` → `#8a5ce0` (보라 계열).
- `protanopia` — 녹색은 그대로 두고 적색 계열만 갈색으로 내린다.
- `tritanopia` — 청색·노랑 계열을 재색하고 `YELLOW_AMBER` → `#ff90d0`
  (분홍 계열) 로 옮긴다.

이 성질에서 세 방향의 **접근성 반경**이 갈린다.

- **B (green 기준)** — 프레임이 `GREEN_NEON` 토큰을 쓰면, 이미 검증된
  변형 테이블이 프레임까지 **자동으로** 재색한다. 새 오버라이드 0개.
- **A (amber 기준)** — `deuteranopia` 에서 녹색이 노랑으로 가므로
  **"정상/안전" 신호와 amber 프레임이 같은 색역에 겹친다.** `tritanopia`
  에서는 `YELLOW_AMBER` 자체가 분홍으로 바뀌어 프레임 정체성이 모드마다
  달라진다. 변형 테이블을 프레임 기준으로 다시 짜야 한다.
- **C (magenta 기준)** — `deuteranopia` 에서 적색 경고가 보라 계열로
  가므로 **magenta 프레임과 위험 신호가 겹친다.** 또한 ADR-0002 의 비주얼
  가이드는 마젠타를 "ICE / 위험" 색으로 지정했다
  (`0002-rendering-style.md` §결과 → 컬러 팔레트). 프레임 전체를 마젠타로
  칠하면 **위험 신호가 배경 소음이 된다.**

### 2 — 프레임 언어: 모든 화면에 박스 문자 패널

V2 의 불일치는 "테두리를 쓰는 화면" 과 "안 쓰는 화면" 이 섞인 것이다.
선례는 이미 코드에 있다 — `tutorial.ts:97` 의 `╔═╗` 와
`menu_dialogue.ts:218` 의 `"╔" + "═".repeat(boxWidth - 2) + "╗"`.
이 ADR 은 그 언어를 **메인 메뉴 · 미션 선택 · 전투 · 던전 맵 · HUD** 에
일관되게 확장한다.

- 외곽 프레임과 영역 구획 (그리드 | HUD) 을 박스 문자로 그린다.
  `canvas.ts:201` 의 "1셀 띄우기" 를 실제 구획선으로 바꾼다.
- 프레임은 **격자 안의 문자**다 — DOM 테두리나 CSS `border` 가 아니다.
  따라서 색각 변형·고대비·텍스트 스케일을 그대로 따른다.
- 패널 헬퍼는 순수 함수로 둔다 (ADR-0234 의 `combat_grid.ts` 추출
  패턴, ADR-0110 의 모듈 크기 정책).

### 3 — 구성: canvas 가 프레임 전체를 쓴다

V1 의 원인은 "고정 픽셀 크기 → CSS 축소만" 이다. 결정은 **뷰포트에서
격자를 역산**하는 것이다 — 뷰포트 크기와 최소 가독 셀 크기로부터
열·행 수 또는 셀 크기를 정하고, CSS 가 다시 줄이지 않게 한다.

- 대상: `canvas.ts:112-139` (`resizeGrid`), `canvas.ts:27-32`
  (`CELL_SIZES`), `web/src/core/layout.ts` (breakpoint 별 열·행),
  `index.html:41-44` (`max-*` / `width: auto` / `height: auto`).
- 메뉴류 화면은 상단 몇 줄에만 그리는 대신 프레임 안에서 배치한다
  (`menu_main.ts:66` `renderMainMenu`, `main.ts:273-307`
  `renderMissionSelect`).
- **세로 여유 공간에 ko 자막 행을 예약**한다 (아래 §6).

### 4 — 타입 스케일: 확대가 살아남는다

V3 는 3번의 직접 결과다. CSS 가 canvas 를 다시 줄이지 않으면
`setTextScale` (`canvas.ts:92-102`) 의 배수가 **실제 화면 글자 크기**에
반영된다. 결정은 이렇다.

- 텍스트 스케일은 **셀 크기를 키우고 격자 열·행 수를 줄이는** 방향으로
  작동한다 (화면을 넘치면 CSS 축소로 되돌리는 것이 아니다).
- `small` (0.85) 이 최소 셀 6×12 를 더 줄이는 문제 (트리아지 §4 V3) 를
  막기 위해 **최소 실효 셀 크기 하한**을 둔다. 하한값은 구현 시 실측으로
  정한다 — 이 ADR 은 숫자를 미리 정하지 않는다.

### 5 — `#status-overlay`: 목적을 주거나 없앤다

V4 는 "내용 없는 장식" 이다. 결정은 **둘 중 하나**다.

- **(기본안)** 라벨이 붙은 신호 / 목적 표시로 쓴다 — 예: `SIGNAL` 라벨과
  현재 화면의 목적 한 줄. 컨셉 시트 B 의 "named SIGNAL cell" 이 이 안이다.
  이 경우에도 표시는 **격자 프레임 안의 셀**로 옮기는 것을 우선한다
  (DOM 오버레이는 색각 변형을 따르지 않는다 — `index.html:69` 의
  `#00ff41` 하드코딩).
- **(대안)** 쓸 내용이 없으면 요소와 CSS 를 제거한다 (`index.html:64-77`,
  `:112-130` 의 미디어 쿼리 2곳, `:136` 의 요소).
- `aria-live="polite"` 속성이 붙어 있으므로 (`index.html:136`), 제거 시
  스크린 리더 경로에 영향이 없는지 확인한다 (트리아지 §1.1 A2 — 현재 쓰는
  코드 없음).

### 6 — 터치 타깃 ≥ 44px (px 하한)

ADR-0214 는 vw 단위로 크기를 키웠지만 **px 하한**은 두지 않았다. 이
ADR 은 모든 터치 버튼에 `min-width` / `min-height` **44px** 하한을
추가한다 (`touch.ts:115` B 버튼, `touch.ts:166`, `:184` 프로그램 버튼,
D-pad `touch.ts:37-54`). 단위 선택은 `max(44px, Nvw)` 형태로 vw 의
비례성을 유지한다. **ADR-0214 는 수정하지 않는다** (immutable) — 이 ADR 이
px 하한을 덧붙인다.

### 7 — 유지하는 것

- **순수 ASCII / Canvas2D** — 스프라이트·WebGL 없음 (ADR-0002, 트리아지
  §1.4 R1·R2 기각과 정합).
- **검은 배경, 거친 monospace** — 스타일 가이드 그대로.
- **en 1차 + ko 자막** — `AGENTS.md` §6 i18n 가이드라인 (ADR-0010 이월).
  프레임 배치 시 ko 자막 행이 들어갈 **레이아웃 공간을 미리 예약**한다
  (자막을 켰을 때 프레임이 밀리지 않게).

## 고려한 옵션

세 방향 모두 "박스 문자 프레임 + 화면 채우기 + 44px 터치" 라는 **구조는
공유**한다 (컨셉 시트의 FRAME NOTE). 갈리는 것은 **프레임의 지배색**과
그 결과다.

### Option A — "Amber Rust" (amber 지배 프레임)

- **설명**: `YELLOW_AMBER` (`#ffa500`, `palette.ts:73`) 를 프레임 레일·
  제목·푸터 색으로 쓴다. 위험은 녹슨 적색. 컨셉 시트 Rationale: "Warm
  amber carries the old monitor burn while red corrosion marks danger
  without turning the frame glossy."
- **장점**: 스타일 가이드의 "C64 / amber monitor 분위기" 와 직접 맞닿는다.
  세 방향 중 가장 따뜻하고 "낡은" 인상.
- **단점**: 1번 근거대로 `deuteranopia` 에서 녹색 신호와 겹치고
  `tritanopia` 에서 프레임 자체가 분홍으로 바뀐다 → 변형 테이블 재설계
  필요. 현재 화면 전체의 기준색을 바꾸는 **대규모 재색**.
- **Pillar 정합**: P5 (The Style) ✅ (톤) / P1 (The Run) ⚠️ (색각 플레이어
  가독성 재검증 필요).

### Option B — "Green Grid" (green 지배 프레임) — **채택**

- **설명**: 현행 `GREEN_NEON` 신호 팔레트를 유지하고 프레임을 그 위에
  얹는다. 시안은 플레이어 데이터, 노랑은 경고. 컨셉 시트 Rationale:
  "Phosphor green makes the frame feel like a working terminal, with cyan
  player data and yellow alerts cutting through grime." FRAME NOTE:
  "repeated grid corners / denser content fill / named SIGNAL cell /
  touch row never under 44px."
- **장점**:
  - **접근성 반경이 가장 작다** — ADR-0236 변형 테이블이 프레임을 자동
    재색한다. 새 오버라이드 0개.
  - **기존 화면과 연속적** — 사용자가 이미 보고 있는 색이다. 바뀌는 것은
    구성과 프레임이지 정체성이 아니다.
  - 스타일 가이드 시각 키워드 "형광 그린" 에 포함된다.
- **단점**: 세 방향 중 **가장 덜 새롭다** — 개편 체감은 색이 아니라
  구성에서 나와야 한다. 녹색 단색 프레임이 단조로워질 위험 → 시안·노랑·
  회색 ramp 로 계층을 둔다.
- **Pillar 정합**: P5 (The Style) ✅ / P1 (The Run) ✅ (색각 플레이어
  경로 무변경).

### Option C — "Magenta Static" (magenta 지배 프레임)

- **설명**: `MAGENTA_NEON` (`#ff00ff`, `palette.ts:75`) 을 프레임 이중 레일·
  부식 표식에 쓰고, ICE 는 얼음 청색으로 분리한다. 컨셉 시트 Rationale:
  "Magenta holds the social rot and signal noise, while ice blue isolates
  the hostile ICE entity and cyan keeps the player readable."
- **장점**: 세 방향 중 시각적으로 가장 강렬하다. "사회적 부패 / 신호
  잡음" 이라는 서사적 해석이 뚜렷하다.
- **단점**: ADR-0002 가 마젠타를 "ICE / 위험" 색으로 지정했으므로 **의미
  충돌** — 프레임 전체가 경고처럼 읽힌다. `deuteranopia` 에서 적색 경고가
  보라로 가며 프레임과 겹친다. 대면적 마젠타는 스타일 가이드의 "밝은
  색조의 미래" 회피 항목에 가까워질 위험이 있다.
- **Pillar 정합**: P5 (The Style) ⚠️ / P3 (The Flatline) ❌ (위험 신호
  희석).

### 비교표

| 축 | A — Amber Rust | **B — Green Grid** | C — Magenta Static |
| --- | --- | --- | --- |
| 지배색 (현행 토큰) | `YELLOW_AMBER` `#ffa500` | `GREEN_NEON` `#00ff41` | `MAGENTA_NEON` `#ff00ff` |
| 현행 화면과의 연속성 | 낮음 (기준색 교체) | **높음 (기준색 유지)** | 낮음 (기준색 교체) |
| ADR-0236 색각 변형과의 정합 | ❌ deuter: 녹→노랑과 겹침 / trit: 프레임이 분홍 | **✅ 프레임이 기존 테이블로 자동 재색** | ❌ deuter: 적→보라와 겹침 |
| ADR-0002 색 의미와의 정합 | ⚠️ 노랑 = 알람/경계와 인접 | ✅ 형광 그린 (가이드 수록) | ❌ 마젠타 = ICE/위험 |
| 스타일 가이드 톤 | ✅ amber monitor | ✅ 형광 그린 / 작동 중인 터미널 | ⚠️ 대면적 고채도 |
| 위험 신호 대비 | 중간 | **높음 (녹 vs 적)** | 낮음 (프레임과 경쟁) |
| 재색 작업량 | 큼 | **작음** | 큼 |
| 새로움 (개편 체감) | 큼 | 작음 (구성으로 보완) | 가장 큼 |

## 추천 (Recommendation)

**Option B.** 프레임 색은 화면의 모든 셀에 닿는다. 그 색을 ADR-0236 이
이미 색각 모드별로 재색하는 토큰 위에 두면, 개편의 접근성 위험이 구성
변경 (V1–V3, V5) 에만 남는다. A·C 는 톤 면에서 매력이 있지만, 둘 다
변형 테이블을 프레임 기준으로 다시 설계해야 하고 C 는 ADR-0002 의 색 의미와
충돌한다.

## 사용자 결정 (Decision)

**2026-10-31 — 프로젝트 오너가 B // "Green Grid" 를 기준으로 화면 구성
개편을 결정했다.** 구현은 미착수.

- [ ] Option A — Amber Rust
- [x] **Option B — Green Grid** — **채택**
- [ ] Option C — Magenta Static

### 결정된 내용

1. **기준색은 `GREEN_NEON` (`#00ff41` 계열) 을 유지한다.** amber·magenta
   지배 프레임으로 옮기지 않는다. 근거: 색각 변형 (`palette.ts` 의
   `deuteranopia` / `protanopia` / `tritanopia`) 이 녹/적 의미 분할 위에
   세워져 있어 녹색 지배 프레임의 접근성 반경이 가장 작다.
2. **박스 문자 프레임/패널 언어를 모든 화면에 일관 적용한다** — 메인
   메뉴, 미션 선택, 전투, 던전 맵, HUD. 지금은 메뉴·미션 선택·전투에
   테두리가 없고 튜토리얼·대화·엔딩 화면에만 있다.
3. **canvas 가 프레임 전체를 쓴다.** 고정 픽셀 크기 + CSS 축소만 하는
   현재 구조 (`index.html` 의 `max-width`/`max-height` + `canvas.ts` 의
   셀 크기 결정) 를 뷰포트 기준 역산으로 바꾼다.
4. **타입 스케일이 확대를 견딘다.** ADR-0236 의 텍스트 스케일이 CSS
   `max-height` 재축소에 상쇄되지 않게 한다.
5. **`#status-overlay` 는 라벨이 붙은 신호/목적 표시로 쓰거나, 제거한다.**
   내용 없이 항상 보이는 지금 상태는 유지하지 않는다.
6. **터치 타깃 최소 폭 44px 을 px 단위로 강제한다** — vw 단위만으로는
   좁은 화면에서 하한이 깨진다.
7. **유지**: 순수 ASCII / Canvas2D (스프라이트·WebGL 없음), 검은 배경,
   거친 monospace, en 1차 + ko 자막 (레이아웃 공간 예약).
8. **기존 ADR 은 하나도 수정하지 않는다.** Accepted 결정은 immutable 이다
   (`AGENTS.md` §8). 관계는 이 ADR 의 §관련 결정 에 기록한다.

## 결과 (Consequences)

### 긍정적 영향

- **화면 간 시각 언어가 통일된다.** 플레이어가 화면을 넘길 때마다 "테두리
  있는 화면 / 없는 화면" 을 오가지 않는다.
- **넓은 화면에서 공간을 쓴다.** 1280×720 기준 좌우 약 256px 씩의 검은
  띠와 약 6×12px 실효 셀이라는 실측 문제가 해소 대상이 된다.
- **ADR-0236 의 텍스트 스케일이 실제로 동작하게 된다.** 지금은 옵션이
  있어도 화면 높이에 걸리면 효과가 상쇄된다.
- **색각 플레이어 경로가 바뀌지 않는다.** 프레임이 기존 토큰을 쓰므로
  `PALETTE_VARIANTS` 에 새 행을 추가할 필요가 없다.
- **설명 없는 UI 요소가 사라진다** (V4).
- **좁은 화면 터치 조작이 WCAG 44px 하한을 지킨다** (V5).

### 부정적 영향 / 수용한 비용

- **기본 화면이 바뀐다.** ADR-0236 은 "기본 화면 무변경" 을 증명했지만,
  이 ADR 은 의도적으로 **모든 화면의 픽셀을 바꾼다.** 기준 스크린샷
  (`web/demo-screenshots/`) 은 재촬영이 필요하다 (트리아지 §4.1 — 이미
  ADR-0231~0236 이전 시점이다).
- **격자 열·행 수가 뷰포트마다 달라질 수 있다.** 행 위치를 고정한 렌더러
  (예: ADR-0236 의 SETTINGS ACCESSIBILITY 행 24–28) 와 테스트가 영향을
  받을 수 있다. 각 화면 렌더러가 **가용 행 수 기준**으로 배치해야 한다.
- **프레임이 셀을 소비한다.** 외곽 테두리와 구획선만큼 내용 영역이 준다 —
  작은 breakpoint (`compact`) 에서 특히 민감하다.
- **B 는 가장 덜 새로운 선택이다.** 개편 체감은 구성 (V1–V3) 에서 나와야
  하며, 색만으로는 "바뀌었다" 는 인상이 약하다.
- **`main.ts` 가 커질 위험** — 미션 선택 렌더 (`main.ts:273-307`) 가
  `main.ts` 안에 있다. 이 화면을 프레임화하면서 렌더러 모듈로 옮기는 것이
  자연스럽지만, 범위를 키운다 (Open questions (b)).

### 후속 항목

1. **기준 스크린샷 재촬영 계획** — 트리아지 §2.1 의 선행 조건. 개편 전·후
   비교를 위해 착수 **전**에 현재 상태를 다시 찍는다.
2. **패널 헬퍼 순수 모듈** — 박스 문자 프레임/구획을 그리는 순수 함수와
   단위 테스트.
3. **뷰포트 역산 레이아웃** — `layout.ts` + `canvas.ts` 의 계산을 순수
   함수로 분리해 테스트 가능하게 만든다.
4. **e2e 레이아웃 스크린샷** — 색각 3모드 + 고대비 × 대표 뷰포트.
5. ~~**`index.html` inline `<style>` 정리**~~ — ✅ 2026-10-31 커밋 `4c8f40f1` 로 `#status-overlay` 요소·CSS·미디어 쿼리 제거 완료.

## Implementation Status (2026-10-31)

**Status**: 🟡 Partial — V4·V5·U3·X3 = `4c8f40f1` · V1·V3 = `e9eb6f1` · V2 헬퍼 = `133286a` · V2 3화면 = `f29c22f` · V2 1셀 인셋 + matrix·dungeon = `a97a4a7` · `main.ts` 분해 = `ffbfa41` · crafting·equipment 프레임 = `3e8041d` / 남은 것: `settings` 프레임(별건 후속), Open questions (a)·(e)

**Evidence**:
- `web/index.html:41-44` — canvas `max-width: 100vw; max-height: 100vh; width: auto; height: auto` — CSS 축소만 하는 지점 (V1, V3)
- `web/index.html:64-77` — `#status-overlay` 스타일 (`border: 1px solid #00ff41` 하드코딩) (V4)
- `web/index.html:112-130` — `#status-overlay` 미디어 쿼리 2곳 (V4)
- `web/index.html:136` — `<div id="status-overlay" aria-live="polite">` 요소, `web/src/` 쓰기 코드 0건 (V4)
- `web/src/renderer/canvas.ts:27-32` — `CELL_SIZES` 고정 4종 (V1, V3)
- `web/src/renderer/canvas.ts:92-102` — `setTextScale` — 스케일이 CSS 축소에 상쇄되는 경로 (V3)
- `web/src/renderer/canvas.ts:112-139` — `resizeGrid` — canvas CSS 크기를 `열 수 × 셀 px` 로 고정 (`:133` `style.width`) (V1)
- `web/src/renderer/canvas.ts:201` — `drawHud` 의 `hudX = (grid.width + 1) * cellWidth` — 그리드/HUD 구획이 1셀 띄우기뿐 (V2)
- `web/src/core/layout.ts:85-95` — breakpoint 별 열·행 (`xlarge` 100×60 + HUD 28) (V1)
- `web/src/renderer/accessibility_modes.ts:58-63` — `TEXT_SCALE_FACTORS` 0.85 / 1.0 / 1.25 (V3)
- `web/src/renderer/palette.ts:69` — `GREEN_NEON: "#00ff41"` — 채택 기준색
- `web/src/renderer/palette.ts:115-153` — `PALETTE_VARIANTS` 색각 3모드 — 기준색 선택 근거 (변경 없음 예정)
- `web/src/renderer/menu_main.ts:66`, `:99` — `renderMainMenu`, `─` 구분선 1줄 (V2)
- `web/src/renderer/settings.ts:250` — `─` 구분선 1줄 (V2)
- `web/src/main.ts:273-307` — `renderMissionSelect` — 테두리 0, 상단 배치 (V1, V2)
- `web/src/renderer/combat_grid.ts` — 전투 화면 테두리 0 (V2)
- `web/src/renderer/dungeon.ts:22`, `:300` — `renderDungeonMap` / `renderDungeonUi` — 프레임 적용 대상 (V2)
- `web/src/renderer/tutorial.ts:97`, `web/src/renderer/menu_dialogue.ts:36`, `:218`, `web/src/renderer/menu_endings.ts:40`, `web/src/renderer/menu_stages.ts:270` — 기존 박스 문자 선례 (V2, 프레임 언어 기준)
- `web/src/input/touch.ts:37-54` — D-pad vw/vh 크기 (V5)
- `web/src/input/touch.ts:115` — B 버튼 `size: "12vw"`, px 하한 없음 (V5)
- `web/src/input/touch.ts:166`, `:184` — 프로그램 버튼 `min-width: 8vw` / `min-height: 6vh`, px 하한 없음 (V5)

**Notes**:
- 줄 번호는 **HEAD `cc55d162` (2026-10-31) 의 커밋된 트리 기준**이다
  (트리아지 §0 — 동시 진행 중인 `core/` 모듈 분할로 달라질 수 있다).
- **트리아지 §3 1단계 ("즉시 정리") 는 커밋 `4c8f40f1` 로 반영됐다** (이 ADR
  검증 시점에는 미커밋이었고, 이후 별도 커밋으로 반영됨) — `web/index.html`
  에서 `#status-overlay` 요소·CSS·미디어 쿼리 제거 (V4 대안안),
  `web/src/input/touch.ts` 에 `MIN_TOUCH_TARGET_PX = 44` 및 `max(44px, …)`
  px 하한 (V5), `web/src/renderer/nav_index.ts` 신설 + 3화면 1-based `[N]`
  통일 (U3), `web/src/renderer/hud.ts` 의 죽은 `renderHUD()` 제거 (X3).
  게이트: `tsc --noEmit` 0 · `eslint` 0 errors · `vitest` **144 files /
  3345 tests PASS** (직전 141 / 3333) · `vite build` OK. **따라서 위 Evidence
  의 `index.html:64-77`, `:112-130`, `:136`, `touch.ts:115`, `:166`, `:184`
  줄 번호는 무효다** — V4 / V5 는 🟡 Partial 로 재판정한다.
- 이 ADR **최초 작성** 시점에는 `web/` 아래 어떤 파일도 수정·실행하지 않았다
  (테스트 수·빌드 결과를 측정하지 않았다). 이후 구현·측정 결과는 아래
  "구현 경과" 항목에 있다.
- 구현 시 **밸런스 0.0pp drift** (ADR-0229 §A1) 를 확인한다 — 표시 계층
  전용 변경이므로 drift 가 나면 결함이다.
- 구현은 `AGENTS.md` §8 ("한 세션에 너무 많은 파일 변경 금지") 에 따라
  V4·V5 (작은 정리) → 패널 헬퍼 → V1·V3 (레이아웃) → 화면별 프레임 적용
  순서로 나누는 것을 권한다 (트리아지 §3).
- **구현 경과 (2026-10-31, 오케스트레이터 검증)** — V1·V3 (`e9eb6f1`) 실측:
  1440×900 캔버스 박스 1280×900 → **1440×900** (사망 띠 186.67px → **0px**),
  390×844 는 56.38px → **0px**. 텍스트 스케일 medium→large 가 컨텍스트 폰트를
  15 → 18.75px (데스크톱) / 14.07 → 17.58px (폰) 로 **실제로** 키운다 (이전에는
  `index.html` 의 `max-*` 가 상쇄했다). 밸런스는 개방·PPL 양 덱 6등급 전부
  **0.0pp drift** — 표시 계층 전용 변경임이 확인됐다. V2 는 `133286a`(헬퍼) +
  `f29c22f`(메뉴·미션 선택·전투 3화면 적용, 전투는 우측 레일이 HUD 컬럼과의
  구분선을 겸함). **그 시점 미적용**: dungeon · matrix · pause · crafting ·
  equipment — 그중 **dungeon·matrix 는 `a97a4a7` 에서 적용**됐다.
  검증: `vitest` 147 files / 3428 tests · `vite build` OK.
- ~~**미해결로 남긴 관찰**: 3화면의 프레임이 그리드 최외곽 행/열에 그려져
  캔버스 가장자리에 붙는다~~ — ✅ **2026-10-31 해소** (`a97a4a7`):
  `panel.ts` 의 `screenFrameRect()` 가 프레임을 그리드 크기에서 파생해
  **(1,1)–(cols-2, rows-2)** 로 인셋 → 사방 1셀 검은 거터. 텍스트가 거터로
  새지 않도록 `clipToInner()` / `setInnerText()` 로 클립 (긴 텍스트는 이제
  잘린다 — 이전에는 그리드 가장자리 프레임이 위에 덮어 가렸다). 같은 커밋에서
  **matrix · dungeon 화면에도 프레임 적용**. 남은 미적용: pause · crafting ·
  equipment.
- **동반 발견 (이번 범위 밖, 기록)**: ① `renderer/dungeon.ts` 는 플레이어 `@`
  심볼을 **그리지 않는다** (HEAD 에서도 동일 — 후속 조사 대상) ② 런타임 던전
  크기는 **15×10** (100×60 그리드 / 내부 98×58) → 인셋 프레임이 던전을 자르지
  않는다 (`dungeon_crawler_generation.ts` 의 `80×45` 는 `state` 로 옮겨지기 전
  그래프 값) ③ 전투 HAND 행이 19행 미만 그리드에서 하단 레일에 가려 **보이지
  않던** 문제를 같은 커밋에서 클램프로 해소.
- **프레임 언어 최종 적용 (2026-10-31, `3e8041d`)**: `crafting` · `equipment`
  에도 동일한 인셋 프레임을 적용해 **7화면 완료** — menu · mission select ·
  combat · matrix · dungeon · crafting · equipment. 콘텐츠는 리플로우 없이
  +1열/+1행 평행 이동이고, 오프셋은 그리드가 아니라 프레임 코너 기준으로
  재측정됐다. **의도적 미적용 2건**: ① `pause` — 빈 격자가 설계다
  (`pre_game_screen.ts` 주석 "Pause intentionally has a blank grid" 및 테스트가
  전 셀을 공백으로 pin) ② `settings` — 푸터가 `rows-2`/`rows-1` 에 있고
  `rows-1` 이 프레임이 비워야 하는 거터 행이라 적용하려면 `settings.ts`
  리플로우가 필요하다 → **별건 후속**.

## Open questions

- **(a) 공격 색 / heavy attack 지속시간 — 코드→사양인가, 사양→코드인가?**
  (트리아지 X6 / X7.) `attack` kind 가 코드는 `YELLOW_AMBER`
  (`web/src/renderer/combat_vfx_render_combat.ts:28-29`) 인데 사양은 회색
  (`docs/design/systems/animations.md:38`). `heavy_attack` 은 코드 900ms
  (`web/src/core/state/state_helpers.ts:268-269`) vs 사양 600ms
  (`animations.md:59`). 프레임 지배색이 녹색으로 확정됐으므로 전투 VFX 의
  amber 사용이 프레임과 경쟁하는지도 함께 판단해야 한다. 코드를 사양에
  맞추면 순수 구현, 사양을 코드에 맞추면 `AGENTS.md` §3.2 의 사양 갱신
  절차다.
- ~~**(b) `main.ts` 분해는 같은 릴리스에 싣는가, 뒤로 미루는가?**~~ — ✅
  **2026-10-31 결정: 같은 릴리스에 포함** (`ffbfa41`). `main.ts` 는
  **2,074 → 1,658줄(-416)** 로 줄었고, 뷰 빌더를 `crafting_screen` ·
  `equipment_screen` · `graphic_novel_screen` · `pre_game_screen` ·
  `run_screen` · `combat_hints` 모듈로 옮겨 각각 순수 `*Layout()` + 단위
  테스트를 갖췄다. 컨트롤러(입력 · 상태 변경 · 로딩 · autosave · 렌더 루프 ·
  dispatch)는 `main.ts` 에 남는다 (ADR-0110 정합).
  **주의 기록**: 분해 중 장비 렌더러의 런타임 import 가 기존
  `equipment.ts ↔ loadout.ts` 순환을 앞당겨 부팅이
  `Cannot access 'EQUIP_SLOTS' before initialization` 로 실패했다 —
  **단위 테스트 3,456개가 전부 통과한 상태에서** 브라우저 스모크만이
  잡아냈다 (컨트롤러가 슬롯 목록을 넘기도록 고쳐 해소). `main.ts` 는 import
  시 자체 부팅해 vitest 대상이 아니므로, 이후 이 파일 변경은
  **브라우저 스모크를 회귀 게이트로 삼는다.**
- ~~**(c) `#status-overlay` 의 최종 형태**~~ — ✅ **2026-10-31 결정: 제거**
  (`4c8f40f1`). 소비자가 0건이라 빈 초록 박스로 항상 표시됐고, 표시할 내용도
  없었다.
- ~~**(d) 최소 실효 셀 크기 하한값**~~ — ✅ **2026-10-31 결정: 6×12 CSS px**
  (`e9eb6f1`, `renderer/canvas_geometry.ts` 의 최소 셀 하한). `small` 텍스트
  스케일과 `compact` breakpoint 에서도 이 하한이 적용된다.
- **(e) ko 자막 예약 행 수** — 1행 고정인지, 대사 길이에 따라 2행까지
  허용하는지.

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `docs/wiki/decisions/0237-ui-composition-and-visual-direction.md` — **신규** (이 ADR)

### 구현 시 변경될 항목 (예정)

- `web/index.html` — canvas CSS 축소 규칙 (V1/V3, 예정). `#status-overlay` 제거는 ✅ 커밋 `4c8f40f1`
- `web/src/renderer/canvas.ts` — 뷰포트 역산 셀/격자 크기, 그리드/HUD 구획
- `web/src/core/layout.ts` — breakpoint 별 열·행 계산
- `web/src/renderer/menu_main.ts`, `settings.ts`, `combat_grid.ts`,
  `dungeon.ts`, `matrix.ts` — 프레임/패널 적용
- `web/src/main.ts` — 미션 선택 렌더 프레임화 (Open questions (b))
- ~~`web/src/input/touch.ts` — 44px 하한~~ ✅ 커밋 `4c8f40f1` (`MIN_TOUCH_TARGET_PX = 44`)
- 신규 패널 헬퍼 모듈 + 테스트

### 이번 결정으로 변경되지 않는 항목

- `web/src/renderer/palette.ts` 의 색 값과 `PALETTE_VARIANTS` — **미변경 예정**
  (B 채택의 핵심 근거)
- reducer · `GameState` · `SaveSlot` · 전투 수치 · calibration 배열
- `web/src/data/*.json`
- `docs/design/ui-overhaul-triage-2026-10-31.md`,
  `docs/design/manus-concepts-2026-10-31/` — 읽기 전용 참고
- ADR-0002 / 0018 / 0110 / 0183 / 0195 / 0196 / 0198 / 0199 / 0214 / 0236 —
  **미수정** (immutable)

## 관련 결정

- ADR-0002 (비주얼 스타일) — **Pure ASCII 와 색 의미의 owner.** 이 ADR 은
  Pure ASCII 를 유지하고, 마젠타 = ICE/위험 의미를 보존하기 위해 C 를
  기각했다. ADR-0002 의 가이드는 형광 그린을 "선택적" 으로 적었으나, web
  티어는 ADR-0199 이후 `GREEN_NEON` 지배였고 이 ADR 이 그것을 **명시적
  결정**으로 기록한다. **ADR-0002 는 수정하지 않았다** (immutable).
- ADR-0018 (Combat Animation) — `animations.md` 사양의 상위. Open
  questions (a) 의 대상. **수정하지 않았다.**
- ADR-0183 (Accessibility) / ADR-0196 (Colorblind State Alignment) —
  색각 4모드 어휘와 텍스트 크기 축의 owner. B 채택은 그 어휘를 그대로
  쓴다. **수정하지 않았다.**
- ADR-0236 (접근성 모드 배선) — **이 ADR 의 직접 전제.** 그 변형 테이블이
  기준색 선택 근거이고, 그 텍스트 스케일이 V3 에서 상쇄되는 문제를 이
  ADR 이 고친다. **수정하지 않았다.**
- ADR-0199 (Wet Run Web MVP) — Canvas2D 렌더러와 `index.html` 구조의
  owner. 그 "can upgrade to WebGL later" 는 이 ADR 범위에서 채택하지
  않는다. **수정하지 않았다.**
- ADR-0198 (Resolution Compatibility) — 해상도 대응의 선행 결정. V1 의
  뷰포트 역산은 그 범위를 web 렌더러에서 구체화한다. **수정하지 않았다.**
- ADR-0214 (모바일 터치 대상 WCAG 최소 크기) — vw 단위 확대의 owner. 이
  ADR 이 px 하한을 덧붙인다. **수정하지 않았다.**
- ADR-0110 (모듈 사이즈 정책) — 패널 헬퍼와 `main.ts` 분해 판단의 기준.
- ADR-0195 (Implementation Status Workflow) — 이 ADR 의 Implementation
  Status 형식의 owner.
- [`docs/design/ui-overhaul-triage-2026-10-31.md`](../../design/ui-overhaul-triage-2026-10-31.md) —
  이 ADR 의 증거 기반 (§4 V1–V5, §2.1 신규 ADR 필요 목록, §1.3 X6/X7).
- `docs/design/manus-concepts-2026-10-31/index.html` — A / B / C 컨셉 시트
  (읽기 전용 참고).
- [`docs/wiki/world/style_guide.md`](../world/style_guide.md) — 톤 제약.

## 변경 이력

- 2026-10-31: 작성 + **Accepted (Option B — Green Grid)** — 프로젝트 오너
  결정. 박스 문자 프레임 전 화면 적용, 뷰포트 기준 구성, 텍스트 스케일
  상쇄 해소, `#status-overlay` 목적 부여 또는 제거, 터치 44px px 하한.
  Implementation Status ❌ Not started. (검증 시점에 V4 / V5 / U3 의 미커밋
  작업 트리 변경을 관찰 — §Implementation Status Notes.)
- 2026-10-31: 트리아지 §3 1단계 반영 — 커밋 `4c8f40f1` (V4 `#status-overlay`
  제거 · V5 44px px 하한 · U3 1-based 통일 · X3 죽은 `renderHUD()` 제거).
  Implementation Status → 🟡 Partial. 게이트: 144 files / 3345 tests PASS.
