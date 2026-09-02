# ADR-0201: wet_run-web Tier 2b — Howler.js BGM 통합

**상태**: **Accepted (Option 1: 단순 통합)** — 2026-08-26 (this session; v1.4.0 Operational Release + Git LFS D4 후속)
**날짜**: 2026-08-26
**결정자**: 사용자 (operator gate 해제: 이전 세션 "silent per operator gate" → 본 세션 user 선택으로 gate 해제)
**우선순위**: P2 (wet_run-web feature, web MVP 완성도 ↑)
**관련**: ADR-0199 (Wet Run Web MVP, Tier 1), `.omo/plans/web-version-2026-08-25.md` §3.2 + §4.2

## 컨텍스트 (Context)

wet_run-web Tier 1 (2026-08-25 ADR-0199) + Tier 2a (2026-08-25, 5 missions + multi-slot save + touch UI) 후, **plan §8에서 명시한 Tier 2b = Howler.js 오디오 통합**이 마지막 unfinished Tier 2 항목:

| 항목 | Tier 1 | Tier 2a | **Tier 2b (this ADR)** |
|---|---|---|---|
| 5 missions | — | ✅ | — |
| Multi-slot save (autosave + 3 manual) | — | ✅ | — |
| Mobile touch UI (virtual gamepad) | — | ✅ | — |
| **Howler.js BGM** | ❌ silent | ❌ silent | **✅ 본 ADR** |

### 이전 세션 deferred 표시 (Tier 2b 직전 log):
- "Tier 2b (Howler.js audio) — silent per operator gate"

**Operator gate 해제**: 2026-08-26 본 세션에서 사용자 "wet_run-web Tier 2b (Howler.js audio)" 명시적 선택 → gate 해제 + 단순 통합 채택.

## 고려한 옵션

### Option 1: 단순 통합 (Minimal MVP) — **채택**

- **설명**: 단일 BGM (theme_sense_net.mp3), M 키 mute toggle, 볼륨 0.4. phase 기반 BGM 전환 없음.
- **장점**:
  - 1 트랙만 copy → bundle 영향 최소화 (+5.7 MB)
  - Howler.js 통합 코드 최소 (manager.ts ~150 LOC)
  - 사용자 인터페이스 단순 (mute toggle만)
  - Tier 3+ 확장 베이스라인 명확
- **단점**:
  - menu/combat 구분 없음 (같은 트랙 반복)
  - SFX 없음 (combat_hit, victory, defeat 등)
  - 12 트랙 중 1개만 사용
- **Pillar 정합**:
  - P1 (The Run): 중립 (런 구조 무관)
  - P2 (The Matrix): 중립
  - P3 (The Flatline): 약간 ↑ (audio atmosphere)
  - P4 (The Build): 중립
  - P5 (The Style): ↑ (Gibson 분위기 강화)

### Option 2: 확장 통합 (Phase-aware)

- **설명**: phase 기반 BGM 전환 (menu → theme_chiba / combat → theme_matrix_rain / victory → theme_broadcast), 5+ 트랙 사용
- **장점**: 더 풍부한 분위기
- **단점**: bundle +30 MB, manager.ts 복잡화, phase 전환 로직 추가

### Option 3: 전체 트랙 순환 (Shuffle 12)

- **설명**: 12 트랙 모두 random shuffle, phase 기반 셔플 재계
- **장점**: 가장 다양
- **단점**: 가장 복잡, ~70 MB bundle (12 × 평균 6 MB)

## 추천 (Recommendation)

**Option 1 (단순 통합) 채택**.

### 이유

1. **Minimal MVP 원칙**: wet_run-web은 4-6주 MVP (plan §1). 추가 복잡도는 3인 playtest 게이트 (§7) 이전에 지양.
2. **단일 트랙의 분위기 효과**: `theme_sense_net`은 Gibson atmosphere (`senses/net` 메타포) — wet_run 무드에 정확히 부합.
3. **확장 베이스라인 명확**: Option 1 manager.ts API (play/stop/mute/toggle)는 Option 2/3 확장의 foundation. `SOUND_IDS` enum이 track registry 역할.
4. **번들 크기 효율**: +5.7 MB (단일 트랙) vs +70 MB (12 트랙).
5. **mute toggle만으로 충분**: 웹 브라우저 환경에서 user gesture 후 자동재생 (autoplay policy) + mute 토글이 표준.

### 트리거 (Tier 3+ 확장 조건)

- 3인 playtest 통과 (PLAYTEST.md §1)
- 사용자 피드백: BGM 단조롭다는 불만 ≥ 1건
- SFX 필요성 (combat_hit / victory / defeat 사운드)
- Phase 전환 명확화 필요 (menu vs combat 구분)

## 사용자 결정 요청

- [x] Option 1 (단순 통합) — **채택**
- [ ] Option 2 (Phase-aware)
- [ ] Option 3 (Shuffle 12)
- [ ] Defer (Tier 3 이후)

## 결과 (Consequences)

### 2026-08-26 — Option 1 채택

**핵심 결정**: 단일 BGM + mute toggle.

### 구현 산출물

| 파일 | LOC | 역할 |
|---|--:|---|
| `src/audio/manager.ts` | ~140 | AudioManager singleton (Howl wrapper) |
| `tests/audio.test.ts` | 9 tests | Singleton + mute toggle + jsdom 환경 가드 |
| `public/sounds/theme_sense_net.mp3` | 5.7 MB | 단일 BGM (dashboard/sounds/full/에서 copy) |
| `src/main.ts` (수정) | +15 | boot()에 AudioManager 초기화 + M 키 mute listener |
| `package.json` (수정) | +2 deps | `howler ^2.2.4`, `@types/howler ^2.2.13` |

### 빌드 검증

- `npx tsc --noEmit`: ✅ 0 errors
- `npm test`: ✅ 47 passed (audio 9 + 기존 38)
- `npm run build`: ✅ `dist/assets/index-*.js = 97.46 kB` (gzip 27.43 kB), `dist/sounds/theme_sense_net.mp3 = 5.7 MB`
- Tier 2a 대비 bundle: 59.55 KB → 97.46 KB (+37.91 KB, Howler.js + manager)

### Accepted 직후 적용

- 본 ADR `decisions/README.md` 인덱스에 추가
- `log.md` 본 결정 기록
- wet_run-web `README.md` 에 BGM 사용법 명시
- wet_run-web `dist/` GitHub Pages 배포 가능

### 거부된 옵션

- **Option 2 (Phase-aware)**: 3인 playtest 결과 대기 — 사전 commit은 over-engineering
- **Option 3 (Shuffle 12)**: bundle +70 MB 부담 큼, Tier 3+ 후보

## 영향 받는 항목

- `wet_run-web/package.json` — howler, @types/howler 추가
- `wet_run-web/src/main.ts` — boot()에 audio 초기화
- `wet_run-web/src/audio/manager.ts` — 신규
- `wet_run-web/public/sounds/theme_sense_net.mp3` — 신규 (5.7 MB)
- `wet_run-web/tests/audio.test.ts` — 신규
- `wet_run-web/README.md` — BGM 사용법 명시
- `decisions/README.md` — ADR-0201 인덱스 추가
- `log.md` — 본 결정 기록

## 관련 결정

- **ADR-0199** (Accepted, 2026-08-25): Wet Run Web MVP — Tier 1 + Tier 2a 정의
- **`.omo/plans/web-version-2026-08-25.md`** §3.2 "Audio (silent in MVP; add Howler.js in Tier 2 if needed)"
- **`.omo/plans/web-version-2026-08-25.md`** §4.2 "Audio (Tier 2) | Howler.js | Browser audio standard"

## 향후 결정

- Tier 3: 3인 playtest 결과에 따라 Option 2 (phase-aware) 또는 Option 3 (shuffle) 확장
- SFX 추가 필요 시 `combat_hit`, `victory`, `defeat` 효과음 통합 (별도 ADR)
- 사용자 볼륨 슬라이더 UI (Phase-aware 통합 시 동시 검토)
- Howler.js → Web Audio API 직접 사용 검토 (번들 의존성 제거, Tier 4+)

## 변경 이력

- 2026-08-26: Draft 작성 (v1.4.0 Operational Release + Git LFS D4 후속)
- 2026-08-26: Draft → **Accepted (Option 1: 단순 통합)** — 본 세션. howler 2.2.4 + @types/howler 2.2.13 설치, public/sounds/theme_sense_net.mp3 copy (5.7 MB), AudioManager singleton (140 LOC), main.ts boot() 통합 (15 LOC), vitest audio.test.ts (9 tests, jsdom 환경 가드), vite build 성공 (97.46 KB JS + 5.7 MB mp3).