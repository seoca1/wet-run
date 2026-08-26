# ADR-0205: wet_run-web Status Effect VFX + HUD Bars

**상태**: **Accepted** — 2026-08-26 (this session; wet_run-web Tier 3 batch, "all" carry-over)
**날짜**: 2026-08-26
**결정자**: 사용자 (operator: "all" carry-over batch)
**우선순위**: P2 (wet_run-web feature enhancement)
**관련**: ADR-0199 (Tier 1), ADR-0203 (Tier 3), `.omo/plans/web-version-2026-08-25.md` §3.2 (out-of-MVP)

## 컨텍스트 (Context)

wet_run-web Tier 3 (30+30) 완료 후, 사용자 "all" carry-over batch. Tier 3 literal (cloud save + multiplayer + narrative) — MVP 초과. Status effect VFX/SFX는 plan §3.2에서 "out of MVP" 명시.

### 현재 한계:
- Combat 중 단순 HP 숫자만 표시 (HP: 75, RED_BRIGHT)
- Status effect 시각화 없음
- Player HP bar 없음
- Turn counter 없음
- VICTORY/DEFEATED 메시지 없음

### 목표:
- **HP bar visualization** (player + ICE, 12-cell `[██████████░░]` 형태)
- **HP ratio color** (green/yellow/red thresholds)
- **Turn counter** 표시
- **VICTORY/DEFEATED** 상태 라벨
- **Pure function helper 모듈** (testable)

## 고려한 옵션

### Option 1: ASCII bar VFX (pure functions) — **채택**

- **설명**: `healthBar(filled, total)`, `healthColor(filled, total)`, `formatStatusLabel(phase)` 3개 pure function
- **장점**:
  - Pure function → 100% testable (jsdom/jsdom 없이)
  - 기존 ASCII grid 시스템 활용 (no engine change)
  - Bundle 영향 최소 (+0.67 kB)
  - Gibson 미니멀 aesthetic 유지
- **단점**:
  - 애니메이션 없음 (정적 표시)
  - Status effect icon 없음 (점화/스턴/슬로우 glyphs 미적용)

## 추천 (Recommendation)

**Option 1 채택**.

### 이유

1. **MVP 적합**: 정적 bar + color threshold + text label은 충분한 정보 전달
2. **Pure function**: 격리 테스트 가능, 의존성 없음
3. **Bundle 효율**: +0.67 kB
4. **Future 확장성**: bar/animation 추가는 별도 ADR

## 사용자 결정 요청

- [x] Option 1 (ASCII bar VFX, pure functions) — **채택**
- [ ] Option 2 (animation + sprite system — 과도)
- [ ] Defer

## 결과 (Consequences)

### 2026-08-26 — Option 1 채택

**핵심 결정**: HP bar + color threshold + status label.

### 구현 산출물

| 파일 | LOC | 역할 |
|---|--:|---|
| `wet_run-web/src/renderer/vfx.ts` | 31 | `healthBar()`, `healthColor()`, `formatStatusLabel()` |
| `wet_run-web/src/main.ts` | -8 inline, +12 grid 사용 | renderGrid에 bar/turn/status 통합 |
| `wet_run-web/tests/vfx.test.ts` | 14 tests | pure function 검증 |

### HUD Layout (combat phase)

```
60,1: T3                            ← turn count
2,5: P [████████████] 100/100      ← player HP bar (12 cells)
36,22: [ Watchdog       ]           ← ICE name (tier color)
36,24: [████████░░░░] 70/100       ← ICE HP bar (ratio color)
36,26: [ VICTORY ]                  ← status label (victory/defeat)
2,42: HAND: [abcd] [efgh] ...        ← existing deck hand
```

### 검증 결과

- `npx tsc --noEmit`: ✅ 0 errors
- `npm test`: ✅ **72 passed** (이전 58 → +14)
- `npm run build`: ✅ 126.10 kB (+0.67 kB)
- 20 modules (이전 19 → +1 vfx.ts)

### Accepted 직후 적용

- 본 ADR `decisions/README.md` 인덱스에 추가
- `log.md` 본 결정 기록

## 영향 받는 항목

- `wet_run-web/src/renderer/vfx.ts` (new)
- `wet_run-web/src/main.ts` (refactor)
- `wet_run-web/tests/vfx.test.ts` (new)
- `decisions/README.md`
- `log.md`

## 관련 결정

- **ADR-0199** (Accepted, 2026-08-25): Wet Run Web MVP
- **ADR-0203** (Accepted, 2026-08-26): wet_run-web Tier 3 (30+30)
- **ADR-0204** (Accepted, 2026-08-26): wet_run-web Phase-aware BGM

## 향후 결정

- Animation VFX (hit flash, ICE defeat) — Tier 4+
- Status effect glyphs (burn/stun/slow/silence/vulnerable icons)
- SFX (combat_hit, victory, defeat) — Howler.js 활용
- Per-frame animation timing (current state는 renderGrid 호출 시점)

## 변경 이력

- 2026-08-26: Draft → **Accepted (Option 1)** — 본 세션. vfx.ts pure function 모듈 생성 (3 helpers). main.ts renderGrid 통합 (HP bars + turn + status). 14 tests 추가. 72 tests 통과. 126.10 kB bundle (+0.67 kB).