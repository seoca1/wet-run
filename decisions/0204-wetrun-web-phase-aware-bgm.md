# ADR-0204: wet_run-web Phase-aware BGM (Tier 2b Option 2 Expansion)

**상태**: **Accepted (Option 2)** — 2026-08-26 (this session; wet_run-web Tier 3 batch)
**날짜**: 2026-08-26
**결정자**: 사용자 (operator: "all" carry-over batch)
**우선순위**: P2 (wet_run-web feature expansion)
**관련**: ADR-0199 (Tier 1), ADR-0201 (Tier 2b — 단일 BGM), `.omo/plans/web-version-2026-08-25.md` §4.2

## 컨텍스트 (Context)

wet_run-web Tier 2b (ADR-0201) 는 단일 BGM (`theme_sense_net`)만 사용. Phase별 분위기 전환 부재. 사용자 "all" carry-over 지시로 **Tier 2b Option 2 (Phase-aware BGM)** 확장.

### 이전 상태 (Tier 2b 직후):
- 1 BGM (theme_sense_net, 5.7 MB)
- M 키 mute toggle
- 9 tests
- 97.46 kB bundle

### 목표:
- **5 BGM tracks** (GamePhase별 매핑)
- **Phase-aware 자동 전환** (GameState.phase 변경 시)
- AudioManager API 확장 (`playPhase()`)
- Mute toggle 유지

## 고려한 옵션

### Option 2: Phase-aware BGM (5+ tracks) — **채택**

- **설명**: GamePhase (menu/approach/combat/victory/defeat/exit) 별 BGM 자동 전환
- **장점**:
  - 풍부한 분위기 전환 (Gibson atmosphere 다층)
  - 자동화된 전환 (사용자 액션 불필요)
  - 5 tracks로 다양한 미션 무드
- **단점**:
  - Bundle 크기 증가 (+30 MB, 5 tracks × 평균 6 MB)
  - mp3 파일 copy 부담

## 추천 (Recommendation)

**Option 2 채택**.

### 이유

1. **Atmosphere 강화**: Gibson Sprawl 분위기 5 track이 미션 다양성과 매치
2. **Plan §4.2 권장**: "Audio (Tier 2) | Howler.js | Browser audio standard" — phase 통합 자연스러움
3. **Bundle trade-off**: +30 MB audio (총 ~36 MB) — 5 tracks. GitHub Pages 가능.

### Phase → BGM 매핑

| GamePhase | Track | Size | Atmosphere |
|---|---|--:|---|
| menu | theme_chiba | 6.9 MB | 도시 진입/선택 |
| approach | theme_sense_net | 5.4 MB | 매트릭스 진입/탐색 |
| combat | theme_matrix_rain | 8.0 MB | ICE 교전 |
| victory | theme_broadcast | 6.5 MB | 승리 |
| defeat | theme_industrial | 7.8 MB | 패배 |
| exit | (none) | — | BGM 정지 |

## 사용자 결정 요청

- [x] Option 2 (5 tracks, phase-aware) — **채택**
- [ ] Option 1 (단일 BGM 유지 — Tier 2b 그대로)

## 결과 (Consequences)

### 2026-08-26 — Option 2 채택

**핵심 결정**: 5 BGM tracks + GamePhase 자동 전환.

### 구현 산출물

| 파일 | 변경 | 역할 |
|---|---|---|
| `wet_run-web/src/audio/manager.ts` | +50 LOC | SOUND_IDS 5개, PHASE_TO_SOUND 매핑, `playPhase()` API, `currentTrack` 추적 |
| `wet_run-web/src/main.ts` | +10 LOC | `Game._lastPhase` 추적 + `syncPhase()` 메서드 + draw() 호출 |
| `wet_run-web/tests/audio.test.ts` | +4 tests | 5 tracks paths + playPhase 동작 |
| `wet_run-web/public/sounds/theme_*.mp3` | +4 files | chiba, matrix_rain, broadcast, industrial copy |

### 검증 결과

- `npx tsc --noEmit`: ✅ 0 errors
- `npm test`: ✅ **58 passed** (Tier 3 54 → Phase-aware 58, +4)
- `npm run build`: ✅
  - `dist/assets/index-DxFlt8g2.js = 125.43 kB` (gzip 43.50 kB)
  - Tier 3 대비 **+0.77 kB** (audio manager API 확장)
  - mp3 total: ~36 MB (5 tracks)

### Accepted 직후 적용

- 본 ADR `decisions/README.md` 인덱스에 추가
- `log.md` 본 결정 기록
- wet_run-web `README.md` 갱신 (다음 commit에서)

## 영향 받는 항목

- `wet_run-web/src/audio/manager.ts`
- `wet_run-web/src/main.ts`
- `wet_run-web/tests/audio.test.ts`
- `wet_run-web/public/sounds/theme_*.mp3` (4 new files)
- `decisions/README.md`
- `log.md`

## 관련 결정

- **ADR-0199** (Accepted, 2026-08-25): Wet Run Web MVP
- **ADR-0201** (Accepted, 2026-08-26): wet_run-web Tier 2b — Howler.js BGM (단일)

## 향후 결정

- SFX (combat_hit, victory, defeat) — Tier 4+
- Per-track fade in/out — Tier 4+ (현재 단순 즉시 전환)
- Volume slider UI — Tier 4+

## 변경 이력

- 2026-08-26: Draft → **Accepted (Option 2)** — 본 세션. 5 tracks + PHASE_TO_SOUND 매핑. AudioManager.playPhase() API 추가. Game.syncPhase()로 phase 추적. 58 tests 통과. 125.43 kB bundle (+0.77 kB).