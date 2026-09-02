# ADR-0207: wet_run-web Tier 4 — SFX + Animation VFX + Status Effect Glyphs

**상태**: **Accepted (Option 1: 단순 통합 batch)** — 2026-08-26 (this session; "wet-run web 다음 Tier" 요청 응답)
**날짜**: 2026-08-26
**결정자**: 사용자 (operator: "Tier 3" 직후 "Tier 4" 지시, plan §8에 Tier 4 미정의 → 자체 정의)
**우선순위**: P2 (wet_run-web feature expansion)
**관련**: ADR-0199 (Tier 1), ADR-0201 (Tier 2b BGM), ADR-0202 (Tier 2c), ADR-0203 (Tier 3), `.omo/plans/web-version-2026-08-25.md` §3.2 (out-of-MVP)

## 컨텍스트 (Context)

wet_run-web Tier 3 (30+30) + Phase-aware BGM + Status VFX + Mission registry wiring 완료 후, 사용자 "wet-run web 다음 Tier도 이어서 진행" 지시.

### plan §8 Tier 진척:
- ✅ Tier 1, 2a, 2b, 2c, 3 완료
- 🟡 Tier 3 literal (cloud save + multiplayer + narrative) — MVP 초과
- **Tier 4 (이 ADR) — plan §8 미정의, 자체 정의**

### Tier 4 정의 (사용자 선택):

"wet-run-web 자체 확장" — plan §8 Tier 3 literal 대신 wet-run-web 강화. **3개 단순 통합 feature**:

1. **SFX** (combat_hit, victory, defeat) — Howler.js 기반
2. **Animation VFX** (hit flash + ICE/Player defeat art)
3. **Status effect glyphs** (burn/stun/slow/silence/vulnerable)

## 고려한 옵션

### Option 1: 단순 통합 batch (3 features) — **채택**

- **설명**: 3개 feature 각각 단순 통합. SFX 3 mp3, Animation VFX 5 ASCII art, Status glyphs 5 glyph mappings.
- **장점**:
  - MVP 범위 유지
  - Tier 2b/3 기반 위에 빌드업
  - Bundle 영향 합리적 (+2.5 KB total)
  - 93 tests passing
- **단점**:
  - Status effect glyphs는 mock data (state machine 미통합)
  - Animation VFX는 정적 표시 (animation timing 없음)
  - SFX는 3개만 (Tier 4+ 확장 가능)

## 추천 (Recommendation)

**Option 1 채택**.

### 이유

1. **MVP 범위 유지**: 3개 feature 각각 단순 통합
2. **Tier 2b/3 기반 활용**: AudioManager + renderGrid + vfx.ts 모듈 확장
3. **테스트 가능성**: 모든 feature가 pure function 또는 jsdom-safe
4. **Bundle 효율**: 126.10 → 128.65 KB (+2.55 KB, +2.0%)

## 사용자 결정 요청

- [x] Option 1 (단순 통합 batch) — **채택**
- [ ] Option 2 (Animation timing + state machine 통합 — out-of-MVP)
- [ ] Option 3 (Tier 3 literal 부분 — cloud save만, MVP 초과)

## 결과 (Consequences)

### 2026-08-26 — Option 1 채택

**핵심 결정**: 3 features 단순 통합.

### 구현 산출물

| Commit | File | Description |
|---|---|---|
| `feac61b` | `src/audio/manager.ts` | SOUND_IDS → BGM_IDS rename, SFX_IDS 추가 (3 effects), `playSfx()` + `stopAllSfx()` API, mute/unmute SFX 통합 |
| `feac61b` | `src/main.ts` | `syncPhase()` terminal phase SFX trigger (victory/defeat/exit) |
| `feac61b` | `public/sounds/sfx_*.wav` (3 files) | WAV copy from prototype (48 KB total) |
| `feac61b` | `tests/audio.test.ts` | +4 tests (SFX_IDS paths, playSfx, stopAllSfx, mute interaction) |
| `81cffb5` | `src/renderer/vfx.ts` | `hitFlashColor()`, `ICE_DEFEAT_ART`, `PLAYER_DEFEAT_ART`, `centerArt()` |
| `81cffb5` | `src/main.ts` | renderGrid signature 확장 (delta params), `applyAction` use_program triggers COMBAT_HIT SFX |
| `81cffb5` | `tests/vfx.test.ts` | +11 tests (hitFlashColor, defeat arts, centerArt) |
| `4afe25f` | `src/renderer/vfx.ts` | `STATUS_GLYPHS` (5 mappings), `formatStatusGlyph()` |
| `4afe25f` | `src/main.ts` | renderGrid `statusEffects` param, ICE name 옆 `[B]` 등 표시 |
| `4afe25f` | `tests/vfx.test.ts` | +6 tests (STATUS_GLYPHS, formatStatusGlyph) |

### 검증 결과

- `npx tsc --noEmit`: ✅ 0 errors
- `npm test`: ✅ **93 passed** (Tier 3 72 → +21)
- `npm run build`: ✅ 128.65 KB (Tier 3 126.10 → +2.55 KB)
- 3 atomic commits (`feac61b`, `81cffb5`, `4afe25f`) + governance commit

### Accepted 직후 적용

- 본 ADR `decisions/README.md` 인덱스에 추가
- `log.md` 본 결정 기록
- `wet_run-web/README.md` Tier 4 scope 갱신

## 영향 받는 항목

- `wet_run-web/src/audio/manager.ts` (BGM/SFX 통합)
- `wet_run-web/src/main.ts` (syncPhase + draw + renderGrid signature)
- `wet_run-web/src/renderer/vfx.ts` (Animation VFX + Status glyphs)
- `wet_run-web/public/sounds/sfx_*.wav` (3 files)
- `wet_run-web/tests/audio.test.ts` (+4 tests)
- `wet_run-web/tests/vfx.test.ts` (+17 tests)
- `wet_run-web/README.md` (scope 갱신)
- `decisions/README.md` (ADR-0207 인덱스)
- `log.md` (본 결정 기록)

## 관련 결정

- **ADR-0199** (Accepted): Wet Run Web MVP
- **ADR-0201** (Accepted): Tier 2b — Howler.js BGM (BGM_IDS 기반)
- **ADR-0202** (Accepted): Tier 2c — Mission + ICE Variety
- **ADR-0203** (Accepted): Tier 3 — 30 Missions + 30 ICE
- **ADR-0204** (Accepted): Phase-aware BGM (5 tracks)

## 향후 결정

- Status effects state machine 통합 (mock → real)
- Animation timing (hit flash 지속 시간)
- Volume slider UI (M key → mute, slider → 0..1)
- SFX 확장 (combat_block, combat_skill_* 등 9+ effects)
- Per-track fade in/out

## 변경 이력

- 2026-08-26: Draft → **Accepted (Option 1: 단순 통합 batch)** — 본 세션. 3 features (SFX + Animation VFX + Status glyphs) 단순 통합. 21 신규 tests (93 total). Bundle +2.55 KB. plan §8 Tier 4 자체 정의 (사용자 선택).