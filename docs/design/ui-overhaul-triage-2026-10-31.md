# Wet Run — UI 개편 트리아지 (2026-10-31)

> **updated**: 2026-10-31
> **성격**: 트리아지 (RESEARCH ONLY). 이 문서 작성 중 `web/` 아래 코드·테스트·설정은 **수정·실행하지 않았다**. 신규 파일은 이 문서 1개뿐이다.
> **입력 문서**: [ui-intuition-evaluation.md](ui-intuition-evaluation.md) (2026-10-24, 이하 **EVAL**) · [combat-feel-and-interaction-proposal.md](combat-feel-and-interaction-proposal.md) (2026-10-29, 이하 **FEEL**)
> **참조 규약**: [systems/animations.md](systems/animations.md) · [style_guide.md](../wiki/world/style_guide.md) · 저장소 `AGENTS.md` §3.2 / §4 / §6 / §8
> **표기 규약**: 형제 문서(`docs/design/*.md`)는 YAML frontmatter 를 쓰지 않는다 (전 17개 파일 1행이 `# 제목`). 따라서 이 문서도 frontmatter 없이 인용 블록에 `updated` 를 둔다.

---

## 0. 읽기 전 주의

- **경로 이동**: FEEL 이 인용한 `web/src/core/state_actions_*.ts`, `core/accessibility.ts` 등은 현재 `web/src/core/combat/`, `web/src/core/state/` 하위로 이동한 상태다 (동시 진행 중인 core/ 모듈 분할 — 미커밋일 수 있음). 이 문서의 `file:line` 은 **2026-10-31 작업 트리 기준**이며, 커밋 후 줄 번호가 달라질 수 있다.
- **판정 4종**: `✅ implemented` · `🟡 partial` · `❌ not started` · `⚪ superseded/rejected`. `❌` 를 제외한 모든 판정에는 `file:line` 근거 또는 `(unverified)` 를 붙였다.
- **판정 기준**: 코드에서 해당 동작이 **실제 호출 경로까지** 이어지는지를 봤다 (정의만 있고 호출자 없음 = 🟡 또는 ❌). 테스트·빌드는 실행하지 않았으므로 "동작한다"는 판정은 정적 근거에 한정된다.
- **FEEL 부록 C** 는 P1–P6·P9–P15 를 ADR-0231~0236 으로 반영 완료라 기록한다. 이 문서는 그 기록을 그대로 믿지 않고 코드로 재확인했다. 차이가 있는 항목(P2, P13)은 🟡 로 내렸다.

---

## 1. 상태 표

### 1.1 EVAL — 10축 루브릭 (R1–R4 / U1–U3 / A1–A3)

| ID | 항목 | 판정 | 근거 (`path:line`) | 비고 |
| --- | --- | --- | --- | --- |
| R1 | ASCII 격자 가독성 (monospace, DPR, `textBaseline: top`) | 🟡 partial | `web/src/renderer/canvas.ts:27-32` (셀 6×12 ~ 10×18), `:80`, `:84`; `web/index.html:41-45` | 구현 자체는 있다. 그러나 EVAL 의 "12-16px/cell" 은 코드와 다르며, CSS `max-width/max-height` 축소로 실제 글자가 더 작아진다 → §4 V3 |
| R2 | 색 규율 (Gibson 팔레트, 알람 임계 색, 색만으로 정보 전달 안 함) | ✅ implemented | `web/src/renderer/palette.ts:22`, `:60`; `web/src/renderer/vfx.ts:16` (`healthColor`); `web/src/main.ts:1650-1654` (알람 75%+ 황색, 수치 텍스트 병기) | |
| R3 | 일관 내비게이션 (`▸` 마커, 하단 조작 안내) | ✅ implemented | `web/src/main.ts:296` (`▸`), `:287` (`↑↓: navigate \| ENTER: launch \| ESC: back`); `web/src/renderer/menu_main.ts:114` | 번호 표기 불일치는 U3 로 분리 |
| R4 | 전투 HUD (조건부 콤보·보스 페이즈) | ✅ implemented | `web/src/core/state/state.ts:180-209` (`buildHudLines`: `Combo` `:190`, `BOSS PHASE` `:197`) | EVAL 이 말한 overflow 가드 `renderer/hud.ts:69` 는 미사용 `renderHUD` 쪽이다 (§1.3 X3). 기준 스크린샷 `05-combat.png` 의 HUD 줄이 잘려 있다 |
| U1 | 즉시 피드백 (stub 화면 `[ Coming soon — Tier 5+ ]`) | ✅ implemented | `web/src/renderer/menu_main.ts:190` | |
| U2 | 반응형 레이아웃 | ✅ implemented | `web/src/core/layout.ts:6-11`, `:44-94` | EVAL 은 3 breakpoint 라 적었으나 현재는 5단계 (`compact`/`small`/`medium`/`large`/`xlarge`) |
| U3 | 화면 간 번호 표기 통일 | ❌ not started | (불일치 근거) 메뉴 `[N]` `menu_main.ts:114` / 미션 `N.` `main.ts:270` / 매트릭스 0-기반 `[i]` `renderer/matrix.ts:94` | EVAL: "시간 있을 때만". 순수 구현 |
| A1 | 입력 중복성 (키보드 + 게임패드 + 터치 → 동일 `GameAction`) | ✅ implemented | `web/src/input/gamepad.ts:117`; `web/src/input/touch.ts:17`, `:288` | |
| A2 | 스크린 리더 대체 텍스트 | ⚪ superseded/rejected | EVAL §Decision (`ui-intuition-evaluation.md:48`): "out of scope" | 참고: `web/index.html:139-140` 에 `aria-live` 영역이 있고 `core/state/accessibility.ts:67` `getAriaLiveText` 가 있으나 **쓰는 코드 없음** (grep 0건) |
| A3 | 터치 타깃 ≥ 44×44px | 🟡 partial | `web/src/input/touch.ts:37-54` (D-pad 12-14vw), `:107` (A 14vw), `:115` (B 12vw), `:166`, `:184` (프로그램 버튼 `min-width: 8vw`, `min-height: 6vh`) | EVAL 의 "1×1 셀 8×16px" 서술은 **현재 코드와 맞지 않는다** (이미 vw 단위). 다만 px 하한이 없어 좁은 화면에서 44px 미만이 된다 → §4 V5 |

### 1.2 FEEL — 우선순위 제안 P1–P15

| ID | 항목 | 판정 | 근거 (`path:line`) | 비고 |
| --- | --- | --- | --- | --- |
| P1 | canvas 레벨 화면 흔들림 + 히트스톱 | ✅ implemented | `web/src/renderer/screen_shake.ts:22-32` (크기·`HIT_STOP_MS=40`, 상한 50), `:119`; `web/src/renderer/canvas.ts:151-165` (`offset` 인자); `web/src/main.ts:1726-1727`, `:1838-1843` | ADR-0232. reduced-motion 시 억제 (`main.ts:1726` 의 `this.reducedMotion`) |
| P2 | 미배선 VFX 10종 배선 | 🟡 partial | 배선됨: `player_hit` `core/combat/state_actions_combat.ts:263`, `:339` · `defeat` `:424` · `ice_death` `core/combat/state_actions_programs.ts:358` · `heal` `core/combat/ice_combat_effect_apply.ts:105` · `ice_intro` `core/state/state_actions_phases.ts:361` | 10종 중 **5종 배선**. 남은 5종 `debuff`/`stun`/`status_apply`/`counter`/`lifesteal` 은 리터럴 spawn 0건 (grep). FEEL R12 가 `counter`/`lifesteal` 을 "플레이어 스킬 구현 시점"으로 연기 |
| P3 | 부유 데미지 숫자 | ✅ implemented | `web/src/renderer/floating_damage.ts:26` (`normal`/`skill`/`critical`), `:136`; `web/src/renderer/combat_overlay.ts:105`; `web/src/main.ts:1720` | ADR-0232 |
| P4 | combat log (최근 N줄) | ✅ implemented | `web/src/core/state/state.ts:102`, `:209`, `:215-221`; `web/src/core/combat/state_actions_combat.ts:466-472`; `web/src/core/combat/state_actions_programs.ts:347`, `:381` | ADR-0231 |
| P5 | 명중 SFX 레이어 + 플레이어 피격 SFX | ✅ implemented | `web/src/core/combat/combat_sfx.ts:39-65` (`DAMAGE` / `COMBAT_HIT`+`ATTACK` / `ICE_BREAK`); `web/src/main.ts:1919-1924` | ADR-0232 |
| P6 | ADR-0226 ICE 효과 가시화 (VFX + glyph) | ✅ implemented | VFX `web/src/core/combat/ice_combat_effect_apply.ts:69`, `:85`, `:105`, `:131`, `:147`, `:173`, `:189`; glyph `web/src/renderer/vfx.ts:85-93` (`shield: "D"`, `regen: "R"`, `powered: "P"`) | ADR-0234 |
| P7 | 입력 유휴 시 적 행동 (시간 압력) | ❌ not started | — | **밸런스 접촉** — ADR-0229 §A1 전후 측정 필수 (FEEL 부록 C "미착수") |
| P8 | `critical_hit` 임계값을 실제 crit 과 연동 | ❌ not started | (현 상태) `web/src/core/combat/state_actions_programs.ts:235` 에 여전히 `damage >= 10` 하드코딩 | **밸런스 접촉** — ADR-0229 §A1 |
| P9 | rAF 렌더 루프 | ✅ implemented | `web/src/main.ts:163` (`MAX_FRAME_ADVANCE_MS = 100`), `:1796-1810` (`startLoop`/`loop`), `:1867`, `:1950` (`cancelAnimationFrame`) | ADR-0231 |
| P10 | reduced-motion · 고대비 · 색각 palette · 텍스트 스케일 | ✅ implemented | `web/src/renderer/accessibility_modes.ts:28-63`, `:124-129`; `web/src/renderer/palette.ts:221-230` (`applyPaletteMode`); `web/src/renderer/canvas.ts:92-102` (`setTextScale`); `web/src/main.ts:148-150`, `:1089-1101` (설정 필드), `:1141`, `:1169`, `:1221` | ADR-0236. 단 텍스트 스케일이 CSS 축소에 상쇄될 수 있음 → §4 V3 |
| P11 | 첫 부팅 튜토리얼 자동 표시 + 전투 진입 힌트 | ✅ implemented | `web/src/core/state/onboarding.ts:65-74`; `web/src/main.ts:2030-2033`, `:1442-1453` | ADR-0235 |
| P12 | 터치 프로그램 버튼 즉시 반응 + 탭 피드백 | ✅ implemented | `web/src/input/touch.ts:142` (디바운스 120ms), `:188-190` (`:focus-visible`), `:203-206` (직접 콜백); `web/src/main.ts:1455-1462` (인게임 눌림 표시) | ADR-0235. D-pad/AB 는 여전히 250ms (`touch.ts:286`) — FEEL 제안 범위 밖 |
| P13 | 오디오 ducking + SFX rate 변조 + 마스터 볼륨 | 🟡 partial | ducking 기본 활성 `web/src/audio/manager.ts:694-695`; 마스터 볼륨 `web/src/main.ts:1091`, `:1119-1122`, `:1147-1150`; rate API `manager.ts:171`, `:185-186`, `:669`, `:685` | ADR-0233 기록("main.ts 배선 미완")은 마스터 볼륨에 한해 해소됨. **`rate` 를 넘기는 호출자 0건** (`playSfx(id)` 만, `main.ts:502`, `:1924`) → 반복 SFX 피치 변조는 미동작 |
| P14 | 상태 HUD 타겟별 분리 + 잔여 턴 | ✅ implemented | `web/src/renderer/status_hud.ts:30-80`; `web/src/renderer/combat_grid.ts:21`, `:75`; `web/src/main.ts:1692` | ADR-0234 |
| P15 | 전투 진입 `ice_intro` + 승리 `ice_death` | ✅ implemented | `web/src/core/state/state_actions_phases.ts:359-365`; `web/src/core/combat/combat_entry_vfx.ts:16-31`; `web/src/core/combat/state_actions_programs.ts:358` | ADR-0235 / ADR-0231 |

### 1.3 FEEL — §1.2 / §1.3 / §1.5 중 P 번호로 흡수되지 않은 항목

FEEL 의 U1–U13 · M1–M10 대부분은 P 항목의 근거다 (매핑: U1·U2·U3·U4·U5→P2, U6→P8, U7·M8·M9·M10→P10, U10→P11, U12→P6, U13→P5, M1→P9, M2·M4→P1, M3→P3, M7→P13, M5→R4). 아래는 **어느 P 로도 다뤄지지 않은** 잔여 항목만이다.

| ID | 항목 (FEEL 원 위치) | 판정 | 근거 (`path:line`) | 비고 |
| --- | --- | --- | --- | --- |
| X1 | 알람 누적 루프 `tickAlarm` 배선 (U8) | ❌ not started | (현 상태) `web/src/core/combat/combat_engine.ts:198` 정의, `web/src/core/combat/ice_crit.ts:12-15` "not wired" 주석 | 밸런스 접촉. P7 과 묶어 판단 |
| X2 | ICE archetype `getAlarmMultiplier` / `shouldTargetAlly` 배선 (U9, ADR-0161) | ❌ not started | (현 상태) `web/src/core/combat/ice_ai.ts:333`, `:364` 정의, 호출자 0건 | 밸런스 접촉 |
| X3 | 미사용 `renderHUD()` 정리 (U11) | ❌ not started | (현 상태) `web/src/renderer/hud.ts:16` — `web/src/` 비테스트 호출자 0건 | 순수 정리. 삭제 또는 전투 HUD overflow 가드로 재사용 |
| X4 | 숫자키 OS auto-repeat 차단 (M6) | ❌ not started | (현 상태) `web/src/input/keyboard.ts:71-72` — modifier 조합일 때만 repeat 무시 | FEEL R4 가 "별도 판단"으로 남김 → 입력 정책 결정 필요 |
| X5 | 치명타 화면 flash (§1.5, `animations.md:176-179`) | ❌ not started | (현 상태) `web/src/renderer/accessibility_modes.ts:78` 에 `"flash"` 억제 분류만 있고 flash 렌더러 없음 | 매 명중 flash 는 R7 로 기각, **치명타 한정** flash 만 해당 |
| X6 | `attack` kind 무채색 규칙 정합 (§1.5, R13) | ❌ not started | (현 상태) `web/src/renderer/combat_vfx_render_combat.ts:28-29` `YELLOW_AMBER` vs `animations.md:38` gray | FEEL R13: "feel 개선이 아니라 사양 정리" — 코드 또는 문서 중 하나를 맞출 것 |
| X7 | `heavy_attack` 600ms 규칙 정합 (§1.5) | ❌ not started | (현 상태) `web/src/core/state/state_helpers.ts:268-269` (900ms), `:206-207` (9 tick) vs `animations.md:59` (600ms) | X6 과 같은 사양 정리 묶음 |
| X8 | 사망 연출 2.4s 시퀀스 (§1.5, `animations.md:133-154`) | 🟡 partial | `defeat` spawn `web/src/core/combat/state_actions_combat.ts:424`; 지속 `web/src/core/state/state_helpers.ts:310-311` (800ms); 배너 `web/src/renderer/combat_vfx_render_scene.ts:188` | 7프레임 + 1s 정지 + "FLATLINE. Static. Silence." 문구는 없음 (`state_actions_combat.ts:412` 는 `"FLATLINE"` 만) |

### 1.4 FEEL — §5 기각 아이디어 (R1–R14)

FEEL 이 명시적으로 기각했으므로 백로그가 아니다. 판정 근거는 FEEL 문서 자체다.

| ID | 아이디어 | 판정 | 근거 |
| --- | --- | --- | --- |
| R1 | 래스터/스프라이트·파티클 엔진 | ⚪ superseded/rejected | `combat-feel-and-interaction-proposal.md:286` (ADR-0002 Pure ASCII 와 정합) |
| R2 | WebGL / Three.js 전환 | ⚪ superseded/rejected | `combat-feel-and-interaction-proposal.md:287` |
| R3 | 히트스톱으로 실제 적 턴 지연 | ⚪ superseded/rejected | `:288` — 연출 전용 50ms 이내로 대체 (`screen_shake.ts:29` `HIT_STOP_MAX_MS = 50`) |
| R4 | 연속 입력 큐 / hold-to-repeat (M5 입력 버퍼 포함) | ⚪ superseded/rejected | `:289` |
| R5 | 전투 중 실시간 타이머 UI | ⚪ superseded/rejected | `:290` |
| R6 | DOM(Web Animations API) 데미지 숫자 | ⚪ superseded/rejected | `:291` — 격자 내 렌더 P3 으로 대체 |
| R7 | 매 명중 화면 전체 flash | ⚪ superseded/rejected | `:292` — 치명타 한정 flash 는 X5 |
| R8 | 신규 WAV 녹음 | ⚪ superseded/rejected | `:293` (ADR-0200 LFS) |
| R9 | BPM 동기 BGM | ⚪ superseded/rejected | `:294` |
| R10 | HP 0 confirm 게이트 | ⚪ superseded/rejected | `:295` |
| R11 | 명중 시 카메라 줌 | ⚪ superseded/rejected | `:296` |
| R12 | 27/27 VFX 일괄 배선 | ⚪ superseded/rejected | `:297` — 잔여 5종은 P2 🟡 로 추적 |
| R13 | `ice_hit` 를 회색으로 | ⚪ superseded/rejected | `:298` — `attack` 색 정합은 X6 |
| R14 | `state.message` 제거 | ⚪ superseded/rejected | `:299` |

### 1.5 집계

| 판정 | EVAL (10) | P1–P15 (15) | 잔여 X1–X8 (8) | R1–R14 (14) | **합계 (47)** |
| --- | --- | --- | --- | --- | --- |
| ✅ implemented | 6 | 11 | 0 | 0 | **17** |
| 🟡 partial | 2 | 2 | 1 | 0 | **5** |
| ❌ not started | 1 | 2 | 7 | 0 | **10** |
| ⚪ superseded/rejected | 1 | 0 | 0 | 14 | **15** |

---

## 2. 신규 ADR 필요 여부 (AGENTS.md §3.2)

현재 최신 ADR 은 `docs/wiki/decisions/0236-accessibility-modes.md` 다. 아래 "신규 ADR" 의 번호는 **아직 정하지 않았다** (번호 임의 부여 금지).

### 2.1 신규 ADR 필요 — 게임 디자인 변경

| 항목 | 이유 | 선행 조건 |
| --- | --- | --- |
| P7 입력 유휴 시 적 행동 | 전투 리듬·승률 변경 | ADR-0229 §A1 `npm run balance` 전후 ±3pp |
| P8 crit VFX 임계값 연동 | crit 판정 표시 기준 변경 (FEEL: 밸런스 영향 가능) | ADR-0229 §A1 |
| X1 `tickAlarm` 배선 | 알람 경제 변경 | ADR-0229 §A1, P7 과 동일 ADR 권장 |
| X2 archetype 2종 배선 | ADR-0161 동작 범위 확정 | ADR-0229 §A1 |
| X4 숫자키 repeat 정책 | 입력 정책 결정 (FEEL R4 가 미결로 남김) | 결정 요청 템플릿(§3.3) |
| P2 잔여 `counter`/`lifesteal` | 플레이어 스킬 개념 자체가 없음 (FEEL R12) — 스킬 시스템 ADR 이 먼저 | 스킬 설계 |
| §4 V1–V3 화면 구성 개편 (레이아웃 채우기 · 패널/테두리 · 글자 크기 정책) | 모든 화면의 시각 정체성 변경. ADR-0002(비주얼 스타일), ADR-0183(텍스트 크기), ADR-0199(web 렌더러) 와 접점 | 기준 스크린샷 16장 재촬영 계획 |

### 2.2 순수 구현 — 기존 ADR/사양 범위 안

| 항목 | 기댈 근거 |
| --- | --- |
| U3 번호 표기 통일 | EVAL 자체 권고 |
| A3 / V5 터치 타깃 px 하한 | EVAL A3 Fix, ADR-0235 (터치) |
| V4 빈 `#status-overlay` 숨김 | 표시 버그 정리 |
| X3 `renderHUD` 정리 | 데드 코드 |
| P2 잔여 `debuff`/`stun`/`status_apply` spawn | ADR-0210 (VFX 스키마) · ADR-0231 범위. **반드시 `import_vfx_deterministic`** (FEEL 부록 C "RNG-중립 규칙") + 0.0pp 확인 |
| P13 rate 변조 호출자 배선 | ADR-0233 |
| X5 치명타 flash | `animations.md:176-179` (ADR-0018 하위 사양). reduced-motion 억제 분류 `accessibility_modes.ts:78` 재사용 |
| X8 사망 2.4s 연출 | `animations.md:133-154` (ADR-0018 하위 사양) |
| X6 / X7 사양 정합 | **경계 사례** — 코드를 사양에 맞추면 순수 구현, `animations.md` 를 코드에 맞추면 §3.2 의 "design/systems 갱신" 절차. 어느 쪽인지 먼저 결정 |

---

## 3. 제안 순서

1. **즉시 정리 (순수 구현, 파일 1–2개씩)** — V4 빈 상태 박스 제거, U3 번호 통일, A3/V5 터치 px 하한, X3 `renderHUD` 정리. 화면 혼란을 가장 싸게 줄인다.
2. **화면 구성 ADR 초안 (V1–V3)** — 1번과 병행. 가장 체감이 큰 문제(빈 공간, 테두리 부재, 작은 글자)이며 모든 화면에 걸치므로 결정이 먼저다. ASCII/Canvas2D 유지 (R1·R2 기각과 정합), 박스 문자 패널은 이미 일부 화면에 선례가 있다 (`renderer/tutorial.ts:97`, `renderer/menu_dialogue.ts:218`).
3. **feel 잔여분 (순수 구현)** — P2 잔여 3종(`debuff`/`stun`/`status_apply`), P13 rate 호출자, X5 치명타 flash, X8 사망 연출. 모두 밸런스 0.0pp 확인만 필요.
4. **사양 정합 결정** — X6·X7 은 코드와 `animations.md` 중 어느 쪽을 진실로 둘지 사용자 결정.
5. **밸런스 접촉 묶음 (각각 ADR + ADR-0229 §A1)** — P7 + X1 을 한 ADR 로, P8 단독, X2 단독.
6. **보류** — X4 입력 정책, P2 의 `counter`/`lifesteal` (스킬 시스템 이후).

> AGENTS.md §8 ("한 세션에 너무 많은 파일 변경 금지") 에 따라 위 각 단계는 별도 세션·별도 커밋으로 나눌 것을 권한다.

---

## 4. 오케스트레이터 실측 시각 문제 5종

판정은 "원 문서가 이미 다뤘는가" 기준이다. 수치 중 `(계산)` 표시는 코드에서 유도한 값이며 실기기 측정이 아니다.

| ID | 문제 | 원 문서 커버 여부 | 코드 원인 (`path:line`) |
| --- | --- | --- | --- |
| V1 | 큰 미사용 검은 공간 / 내용이 화면 상단에 몰림 | **미커버.** EVAL U2 는 오히려 "Strong" 으로 평가 | canvas CSS 크기를 `열 수 × 셀 px` 로 **고정** (`renderer/canvas.ts:128-134`) 한 뒤 CSS 가 `max-width: 100vw; max-height: 100vh; width/height: auto` 로 **축소만** 한다 (`web/index.html:41-45`) → 확대 없음, 좌우 여백 발생. 메뉴는 상단 몇 줄에만 그린다 (`renderer/menu_main.ts:99`, `:114` 부근; 기준 스크린샷 `web/demo-screenshots/01-main-menu.png`). 예: 1280px 폭 → `xlarge` 100×60 + HUD 28 (`core/layout.ts:90-94`), 셀 10×18 (`canvas.ts:31`) → 1280×1080 CSS px → 720px 높이에 맞춰 약 0.67배 축소 (계산) |
| V2 | 패널/테두리/구획이 없어 화면 판독이 어려움 | **미커버.** 두 문서 모두 언급 없음 | 메인 메뉴·설정은 `─` 구분선 1줄뿐 (`renderer/menu_main.ts:99`, `renderer/settings.ts:250`). 미션 선택(`main.ts:274-307`)·전투(`renderer/combat_grid.ts`)는 테두리 없음. 그리드 영역과 HUD 영역 사이 구분도 없음 (`canvas.ts:201` 은 1셀 띄우기만). 반면 튜토리얼·대화·엔딩·스테이지 화면은 박스 문자 사용 (`renderer/tutorial.ts:97`, `renderer/menu_dialogue.ts:36`, `renderer/menu_endings.ts:40`, `renderer/menu_stages.ts:270`) → 화면 간 불일치 |
| V3 | 작은 monospace 글자가 텍스트 스케일 옵션과 충돌 | **부분 커버.** FEEL M8/P10 이 "사용자 조절 불가"를 지적했고 P10 으로 스케일 옵션이 생겼다. 그러나 **옵션이 CSS 축소에 상쇄되는 문제는 미커버** | 스케일은 셀 크기 배수 (`renderer/accessibility_modes.ts:58-63`: 0.85 / 1.0 / 1.25, `canvas.ts:92-102`) → canvas 가 커지지만 `index.html:41-42` 의 `max-*` 가 다시 축소하므로 화면 높이에 걸린 경우 실효 글자 크기가 거의 변하지 않는다 (계산, 실측 필요). `small` 은 최소 셀 6×12 를 약 5×10 으로 더 줄인다 (계산). EVAL R1 의 "12-16px/cell" 도 코드(`canvas.ts:27-32`)와 불일치 |
| V4 | 우상단의 설명 없는 작은 초록 테두리 표시 | **미커버** | `#status-overlay` 가 `position: fixed; top: 8px; right: 8px; padding: 8px 12px; border: 1px solid #00ff41` 로 **항상 표시** (`web/index.html:64-77`, `:136`), 그런데 `web/src/` 어디에서도 이 요소에 내용을 쓰지 않는다 (grep `status-overlay` 0건) → 빈 초록 박스. 기준 스크린샷 `01-main-menu.png`, `05-combat.png` 우상단에서 확인 |
| V5 | 터치 타깃 44×44px 미만 | **커버 (EVAL A3)**, 단 EVAL 의 원인 서술("1×1 셀 8×16px")은 현재 코드와 다름 | 버튼은 vw/vh 상대 단위이며 **px 하한이 없다**: B 버튼 12vw (`touch.ts:115`) → 360px 폭에서 약 43px (계산), 프로그램 버튼 `min-width: 8vw` (`touch.ts:166`, `:184`) → 393px 폭에서 약 31px 하한 (계산, 라벨 폭으로 실제는 더 클 수 있음). D-pad 는 가로 vw·세로 vh 를 섞어 배치 (`touch.ts:67-94`) → 화면 비율에 따라 버튼 간격이 달라짐 |

### 4.1 부수 관찰 (트리아지 범위 밖, 기록용)

- 기준 스크린샷 `web/demo-screenshots/05-combat.png` (파일 시각 2026-10-13) 에 `ICE HP: undefined`, `NaN/100` 이 찍혀 있다. 현재 `buildHudLines` 는 `iceRoster` 기반이라 (`core/state/state.ts:200-207`) 이미 고쳐졌을 가능성이 높으나 **(unverified)** — 스크린샷 재촬영이 필요하다.
- 스크린샷 16장은 P1–P15 반영(ADR-0231~0236) 이전 시점이다. §3 2단계 ADR 작성 전에 재촬영할 것.

---

## 5. 관련 문서

- [ui-intuition-evaluation.md](ui-intuition-evaluation.md) — EVAL
- [combat-feel-and-interaction-proposal.md](combat-feel-and-interaction-proposal.md) — FEEL (부록 C 진행 기록)
- [systems/animations.md](systems/animations.md) — ADR-0018 하위 애니메이션 사양
- [../wiki/world/style_guide.md](../wiki/world/style_guide.md) — 시각 톤 (검은 배경, 형광 그린·시안·마젠타·노랑, 거친 monospace)
- ADR: [0002](../wiki/decisions/0002-rendering-style.md) · [0018](../wiki/decisions/0018-combat-animation.md) · [0161](../wiki/decisions/0161-ice-personality-archetypes.md) · [0183](../wiki/decisions/0183-accessibility.md) · [0196](../wiki/decisions/0196-accessibility-colorblind-state-alignment.md) · [0199](../wiki/decisions/0199-wetrun-web-mvp.md) · [0210](../wiki/decisions/0210-combat-vfx-effect-schema.md) · [0229](../wiki/decisions/0229-grade-curve-rebaseline.md) · [0231](../wiki/decisions/0231-combat-feel-top3-vfx-log-raf.md) · [0232](../wiki/decisions/0232-combat-feel-tier2-shake-damage-sfx.md) · [0233](../wiki/decisions/0233-audio-ducking-master-volume.md) · [0234](../wiki/decisions/0234-effect-visibility-status-hud.md) · [0235](../wiki/decisions/0235-onboarding-touch-intro-vfx.md) · [0236](../wiki/decisions/0236-accessibility-modes.md)
