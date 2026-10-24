# ADR-0214: 모바일 터치 대상 WCAG 최소 크기 충족

**상태**: Accepted
**날짜**: 2026-10-24
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P2 (The Style — accessibility)
**상위 ADR**: ADR-0183 (Accessibility), ADR-0199 (Web MVP)

## 컨텍스트 (Context)

UI 직관성 평가(2026-10-24)에서 A3 항목으로 식별: 모바일 가상 게임패드 버튼이
WCAG 44×44px 최소 터치 대상 크기 미달.

Pixel 5 (393×851) 기준 이전 레이아웃:
- D-pad: 12vw = 47px ✓
- A 버튼: 14vw = 55px ✓
- B 버튼: 10vw = **39px** ✗ (44px 미만)
- 프로그램 행 버튼: 높이 약 **20px** ✗ (44px 미만, 가장 심함)

手指는 대략 44×48px 크기이므로, 작은 버튼은 미스 Rates 상승.

## 고려한 옵션

### Option 1: vw 단위 확장 (선택)
- **설명**: 모든 버튼 size/fontSize를 vw 단위로 확장. D-pad 12→14vw, B 10→12vw, A 14vw 유지.
- **장점**: 간단한 숫자 변경. 반응형 vw 자동 스케일링 활용.
- **단점**: 작은 화면(320px 폰)에서 버튼이 과도하게 커질 수 있음. D-pad가 화면 절반 가량 차지.
- **Pillar 정합**: P5 (The Style) — accessibility는 스타일의 일부.

### Option 2: 고정 픽셀 + 미디어 쿼리
- **설명**: `min-height: 44px; min-width: 44px` 고정 + 화면 크기별 미디어 쿼리 조정.
- **장점**: WCAG 기준 명시적 보장. 반응형 제어 가능.
- **단점**: vw 레이아웃과의 충돌. 추가 CSS 유지보수.
- **Pillar 정합**: P5 — 명시적 표준 준수.

### Option 3: 하이브리드 (vw 확장 + min-size 게이트)
- **설명**: vw 단위로 확장하되, `min-height/min-width`로 WCAG 최소값 보장.
- **장점**: 반응형 + 최소값 이중 보장. 작은 화면에서도 타겟 보존.
- **단점**: 약간의 CSS 복잡도.
- **Pillar 정합**: P5 — 실용적 균형.

## 추천 (Recommendation)

**Option 3 (Hybrid)** — vw 확장으로 반응형 유지 + `min-*` 속성으로 WCAG 44px 최소값
보장. 작은 폰에서도 버튼이 축소되지 않도록.

## 사용자 결정 (Decision)

[ x ] Option 3 (Hybrid)

## 결과 (Consequences)

### 적용된 변경 (2026-10-24)

`web/src/input/touch.ts`:
- `LAYOUTS.portrait.dpadButtonSize`: 12→14vw, `dpadOffset`: 6→7vw
- `LAYOUTS.landscape.dpadButtonSize`: 10→12vw, `dpadOffset`: 5→6vw
- B 버튼: size 10→12vw, fontSize 5→6vw, left -22→-24vw (A/B 간격 확장)
- 프로그램 행: `min-height: 6vh; min-width: 8vw; padding: 2vh 2.5vw` 추가

### Pixel 5 (393×851) 적용 후
- D-pad: 14vw = **55px** ✓
- A 버튼: 14vw = **55px** ✓
- B 버튼: 12vw = **47px** ✓
- 프로그램 행: min-height 6vh = **51px** ✓

### 검증
- `npm run typecheck`: 0 errors
- E2E mobile-portrait-chromium: 4/4 touch tests passed
- E2E desktop-chromium: 4 skipped (overlay absent by design)
- 전체 스위트: 76 passed, 4 skipped

### 영향 받는 항목
- `web/src/input/touch.ts` — 가상 게임패드 레이아웃
- `docs/design/ui-intuition-evaluation.md` — A3 항목 해결

## 관련 결정
- ADR-0183 (Accessibility) — colorblind, text size, input remapping
- ADR-0197 (Gamepad Input) — synthetic keyboard adapter
- ADR-0199 (Web MVP) — mobile touch input scope

## 변경 이력
- 2026-10-24: Draft 작성 + Accepted (Option 3 Hybrid)