# 어포던스 진실성 정합 — 증거 (2026-11-03)

[ADR-0254](../../wiki/decisions/0254-affordance-truth-and-effect-honesty.md) 의 증거다.
결정은 **자가 플레이 검증 + AI 위임**(Jev 결정 계층 · Manus 독립 리뷰)으로 내렸다.

## 어떻게 결정했나

오너의 6개 미해결 항목 중 **내가 스스로 판단할 수 있는 것**을, 증거를 모아 위임해 골랐다.
추측으로 결정하지 않기 위해 파이프라인을 세웠다.

1. **재현** — ego-lite 실제 플레이(Chromium) + 결정적 테스트 + 코드 근거
2. **위임** — Jev 결정 계층(`scripts/jev-call.sh`, OpenRouter `/api/alpha/decisions`)에
   noul / choice 로 항목별 선택을 위임
3. **독립 검토** — Manus(max 프로파일)에 근거와 계획 전체를 주고 독립 리뷰를 받음
4. **구현 + 회귀 테스트** — red → green, 3개 레이아웃 캡처, 밸런스 byte-identical

| 항목 | Jev 선택 | 확률 | Manus 독립 리뷰 |
|---|---|---|---|
| #2 결정타 COST 표기 | 잔여 COST 예측 표기(→ N/100) 제거, 카드당 COST +N 만 | 0.96 / conf 0.94 | "표시 제거가 적절하나 남아있을 수 있음" — 표시만 변경 원칙 유지 |
| #4 프로그램 효과 | 라벨을 effect 기준으로 정합, 실제 효과 배선은 다음 세션 | 0.80 / conf 0.70 | "범위를 엄격히 제한" — 데이터 정합만 |
| #5 종결 노드 loot 화면 | 회복 문구·route selection 숨김, `ENTER: run ends` | 0.98 / conf 0.97 | "A·B는 UI 표시에 국한되어 위험 낮음" |
| #1 select→confirm | 도입하지 않고 진실한 라벨부터 (ADR-0243 불변) | 0.95 / conf 0.92 | "ADR-0243 변경을 피하기 위해 유지" |
| #3 tickIceEffects | 이번 세션 수정 + 회귀 테스트 | 0.53 / conf 0.44 | "**D는 독립 검증 묶음으로 분리**" — 별도 커밋으로 분리함 |
| #6 40×60 HUD 오버플로 | 다음 세션 | 0.52 / conf 0.42 | "**E는 즉시 처리 필요성이 강함**" — Jev와 상반 → 즉시 처리 |

Manus 리뷰 전문: [manus-review.md](manus-review.md)

## 실측 증거

### #2 결정타는 COST 를 청구하지 않는다 — 결정적 테스트
`useProgram` 이 마지막 ICE 를 쓰러뜨리면 승리 분기가 `alarm: newAlarm` 대입 **전에** 반환한다.

| 경우 | `player.alarm` |
|---|---|
| 비마지막 카드 | 10 → **12** (청구) |
| 결정타 | 10 → **10** (청구 없음) |

→ 손패 행의 `→ 41/100` 은 **약속되지 않은 COST** 를 보여줄 수 있다(킬 예측은 규칙 5 로 금지).
`tests/killing_blow_cost.test.ts` 가 이 계약을 고정한다.

### #4 프로그램 카탈로그의 설명문이 구현되지 않은 효과를 약속한다
`web/src/data/programs.json` 의 30개 항목은 파이썬 시대 필드(`damage` · `armor_pierce` · `role`)를
갖지만 웹 티어 리듀서는 `baseDamage = program.tier * 5` **하나만** 쓴다. 실측 부수효과도
설명과 무관했다 — `barrier`(방어막 문구) → `ICE SLOW off`, `decoy`(미끼 문구) → `ICE SLOW on`.

설명문은 그 어느 화면에도 렌더되지 않았지만, Oracle 합성의 다음 슬라이스가 **PROGRAM INSPECT**(설명문 표시)라
지금 정리하지 않으면 그때 거짓말이 된다.

### #5 종결 노드의 loot 화면이 회복도 경로도 약속한다
`applyLootAction` 은 종결 노드에서 `runPhase: "ending"` 으로 분기해 **회복 없이 런을 끝낸다**.
그런데 화면은 `HEAL applied → N/M` 과 `ENTER: route selection` 을 그렸다.
또 `applyLootAction` 은 `cancel` 과 이동 키를 **무시**하는데 화면은 `↑↓: navigate | ESC: back` 을 약속했다.

### #6 엔딩 HUD 라인이 좁은 패널에서 압축된다
캔버스는 HUD 라인을 잘라내지 않고 **가로로 압축**한다 → 글자가 겹쳐 판독 불가.
레이아웃 프리셋 hudCols 는 80×50 → 24, 60×40 → 20, 40×60 → **16** (사용 가능 폭은 23 / 19 / 15).

## 캡처 — 3개 레이아웃, before(HEAD) / after(작업 트리)

실제 `AsciiRenderer`(`web/src/renderer/canvas.ts`) 를 esbuild 로 번들해 headless Chromium 으로 렌더.
*before* = `git archive HEAD web/src`, *after* = 작업 트리. 같은 픽스처·같은 리듀서.

| 케이스 | 80×50 | 60×40 | 40×60 |
|---|---|---|---|
| 손패 | [pair](hand-80x50-pair.png) | [pair](hand-60x40-pair.png) | [pair](hand-40x60-pair.png) |
| loot (비종결) | [pair](loot-80x50-pair.png) | [pair](loot-60x40-pair.png) | [pair](loot-40x60-pair.png) |
| loot (종결) | [pair](loot-terminal-80x50-pair.png) | [pair](loot-terminal-60x40-pair.png) | [pair](loot-terminal-40x60-pair.png) |
| 엔딩 | [pair](ending-80x50-pair.png) | [pair](ending-60x40-pair.png) | [pair](ending-40x60-pair.png) |

### 폭 검사 (`*-width-check.json`)

| 케이스 | HUD 초과 (before) | HUD 초과 (after) | 그리드 초과 |
|---|---|---|---|
| loot | 42 자 | **0** | 0 |
| loot (종결) | 42 자 | **0** | 0 |
| 엔딩 | 29 자 | **0** | 0 |
| 손패 | 24 / 23 자 | 24 / 23 자 | 0 |

손패의 잔여 2건은 **기존 라인**(`> [1] Yakuza Enf HP: 165` 24자, `Mission: Aleph Fragment` 23자)이며
before/after 동일 — 이번 변경과 무관한 **별건**이다(아래 "남은 항목").

## 검증

| 항목 | 결과 |
|---|---|
| `npm run typecheck` | 0 errors — [typecheck.txt](typecheck.txt) |
| `npx eslint src` | 0 errors (기존 warning 1) — [lint.txt](lint.txt) |
| `npx vitest run` | **178 files / 3948 tests passed** (베이스라인 175 / 3932) — [npm-test.txt](npm-test.txt) |
| `npm run balance` (opening) | 100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0 — **ADR-0239 기준선과 동일** — [balance-opening.txt](balance-opening.txt) |
| `npm run balance -- --deck ppl` | 100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7 — **동일** — [balance-ppl.txt](balance-ppl.txt) |
| `npm run build` | PASS — [build.txt](build.txt) |
| Playwright e2e | 86 passed / 4 skipped / **2 failed** — [e2e.txt](e2e.txt) |

### e2e 실패 2건은 기존 실패다 (이번 변경과 무관)
`e2e/idle_alarm.spec.ts:48` "real input prevents alarm growth despite elapsed combat time" 이
데스크톱/모바일 두 뷰포트에서 실패한다. **세션 이전 커밋 `92ba417b` 의 소스로 되돌려도 동일하게
재현**되었고(직접 검증), 실패 지점은 `page.keyboard.press("Shift")` 다 — 창 포커스 문제로 보인다.
`docs/playtest/EGO_LITE_PLAY_CHECK.md` 도 "오너가 빈 화면이라고 하면 앱 버그가 아니라 **창 포커스** 문제" 라고
적어두었다. 이번 세션의 변경과 무관하며, 이 저장소에서 시간 게이트를 다루는 e2e 는 로컬 실행이 불안정하다.

## 남은 항목 (보고)

1. **HUD 좁은 레이아웃 압축** — `> [1] Yakuza Enf HP: 165`(24자)·`Mission: Aleph Fragment`(23자)가
   40×60(사용 가능 15자)에서 압축된다. 전투 HUD 의 기존 결함이며 이번 세션 범위 밖.
2. **프로그램별 실제 효과 배선** — `shield`·`boost`·`decoy`·`cloak`·`probe` 의 설계된 효과.
   이번 세션은 라벨만 정직하게 만들었고, 배선은 오너 결정 사항(밸런스 접촉)이다.
   `plannedDescription` 에 설계 의도를 보존해 두었다.
3. **결정타 COST 정책** — Jev 는 "결정타에도 청구"(리듀서 변경) 옵션을 0.46 으로 골랐지만
   확신도 0.19 로 사실상 동률이고, 밸런스 수치는 오너 결정 사항이라 **표시만** 손댔다.
   리듀서를 바꾸려면 ADR 이 새로 필요하다.
4. **PROGRAM INSPECT** — Oracle 합성의 축1 1순위. 이번에 라벨이 정직해졌으므로
   그때 `plannedDescription` 을 "계획" 으로 명시해 보여줄 수 있다.
