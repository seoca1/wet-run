# ADR-0203: wet_run-web Tier 3 — 30 Missions + 30 ICE Expansion

**상태**: **Accepted** — 2026-08-26 (this session; wet_run-web Tier 3 literal interpretation)
**날짜**: 2026-08-26
**결정자**: 사용자 (operator: "Tier 3" 지시, "all" carry-over batch)
**우선순위**: P2 (wet_run-web feature expansion)
**관련**: ADR-0199 (Tier 1), ADR-0201 (Tier 2b), ADR-0202 (Tier 2c), `.omo/plans/web-version-2026-08-25.md` §8

## 컨텍스트 (Context)

wet_run-web Tier 1 + 2a + 2b + 2c 완료 후, 사용자 "Tier 3" + "all" 지시 (2026-08-26).

### Tier 진척 (plan §8):
- ✅ Tier 1 (MVP)
- ✅ Tier 2a (5 missions + multi-slot + touch UI)
- ✅ Tier 2b (Howler.js BGM)
- ✅ Tier 2c (15 missions + 12 ICE)
- **Tier 3 literal = 이 ADR** (30 missions + 30 ICE, Option 2 확장)
- 🟡 Tier 3 literal = cloud save + multiplayer + narrative (MVP 초과, deferred)

### 이전 상태 (Tier 2c 직후):
- 15 missions (T1-T3)
- 12 ICE types
- 52 tests, 85.52 kB bundle

### Tier 3 목표:
- **30 missions** (T1-T5, 2배 확장)
- **30 ICE types** (2.5배 확장, T1-T4)
- Mission select UI 30개 모두 표시 가능
- Tests + build 검증

## 고려한 옵션

### Option 1: 30 missions + 30 ICE — **채택**

- **설명**: T1-T5 30 missions + T1-T4 30 ICE types
- **장점**:
  - 더 풍부한 콘텐츠 다양성
  - 4-zone 다양성 (surface/mid/deep/core/aftermath/soho)
  - 10+ fixer (finn/sally/ta_rep/yamazaki/hideo/yakuza/masahiko/dixie/wintermute/slick_henry)
  - Tier 5 대표 미션 (aleph_fragment, core_extract_neuromancer_signature)
- **단점**:
  - Bundle 크기 증가 (~85 → ~125 KB)
  - 3-person playtest 게이트 미통과 상태
- **Pillar 정합**:
  - P1 (The Run): ↑↑ (런 다양성 큰 폭 ↑)
  - P2 (The Matrix): ↑ (zone 다양성 6 zones)
  - P3 (The Flatline): 중립
  - P4 (The Build): 중립
  - P5 (The Style): ↑ (Gibson 분위기 강화)

### Option 2: 50 missions + 50 ICE (Tier 3 aggressive)

- **설명**: T1-T5 전체 50 missions + 50 ICE
- **장점**: 매우 풍부한 콘텐츠
- **단점**: MVP 초과, bundle +70 KB 추가 부담

## 추천 (Recommendation)

**Option 1 (30 missions + 30 ICE) 채택**.

### 이유

1. **MVP 범위 보존 + 다양성**: T1-T5 30개가 wet_run universe의 핵심 미션 다양성 커버
3. **Zone 다양성**: 6 zones (surface 13, mid 4, deep 9, core 2, aftermath 1, soho 1)
4. **Fixer 다양성**: 10명 (finn 20, wintermute 2, +8 others)
5. **ICE Gibson-flavor**: 30 types T1-T4 (watchdog/spider/black/goliath/loa_priest/wintermute 등)
6. **Tier 3+ 차이**: Option 2 (50) vs Option 1 (30) — Option 1이 더 적합한 MVP 단계

### 트리거 (Tier 3+ / Option 2 확장 조건)

- 3-person playtest 통과
- 사용자가 50+ 미션 요구
- wet_run-web Tier 4 (Cloud save sync) 통합
- Narrative integration (graphic novel mode) 통합

## 사용자 결정 요청

- [x] Option 1 (30 missions + 30 ICE) — **채택**
- [ ] Option 2 (50 missions + 50 ICE)
- [ ] Defer

## 결과 (Consequences)

### 2026-08-26 — Option 1 채택

**핵심 결정**: 30 missions + 30 ICE 명시적 curation.

### 30 미션 선정 (T1-T5, 6 zones, 10 fixer):

| Tier | Count | Zone 분포 |
|---|--:|---|
| T1 | 2 | surface: 2 |
| T2 | 11 | surface: 9, soho: 1, aftermath: 1 |
| T3 | 10 | surface: 1, mid: 2, deep: 5, core: 1, deep: 1 |
| T4 | 5 | mid: 2, deep: 2, surface: 1 |
| T5 | 2 | core: 1, deep: 1 |

**Zone totals**: surface 13, mid 4, deep 9, core 2, aftermath 1, soho 1 = 30

**Fixer distribution**: finn 20, wintermute 2, ta_rep 1, yamazaki 1, hideo 1, yakuza 1, masahiko 1, dixie 1, slick_henry 1, sally 1 = 10 distinct fixers

### 30 ICE 선정 (T1-T4, Gibson-flavor):

| Tier | Count |
|---|--:|
| T1 | 7 (standard, watchdog, spider, wisp, zombie, hosaka_courier, sense_net_alert) |
| T2 | 10 (raven, loa_priest, ta_security_ice, ice_feedback_loop, ice_worm, ice_shadow_variant, romantics_ice, loa_disguised, ice_wheel_children, ice_harrow_3) |
| T3 | 8 (black, goliath, loa_entity, revelation, ai_whisper, ice_burned_cowboy, oua_entity, ice_weapon_construct) |
| T4 | 5 (prime_loa, voodoo, archive_sentinel, ice_wheel_guardians, wintermute) |

### 구현 산출물:

| 파일 | 변경 | 역할 |
|---|---|---|
| `wet_run-web/scripts/export_web_data.py` | TIER_2C → TIER_3 | 15 → 30 missions, 12 → 30 ICE |
| `wet_run-web/src/data/missions.json` | 41.6 → 89.2 KB | 15 → 30 미션 |
| `wet_run-web/src/data/ice_types.json` | 6.4 → 17.0 KB | 12 → 30 ICE |
| `wet_run-web/src/main.ts` | `y += 2` → `y += 1` | 30 미션 single-line 표시 |
| `wet_run-web/tests/missions.test.ts` | +2 tests | Tier 3 명시 (30 count + curation IDs) |

### 검증 결과

- `npx tsc --noEmit`: ✅ 0 errors
- `npm test`: ✅ **54 passed** (Tier 2c 52 → Tier 3 54, +2 신규)
- `npm run build`: ✅
  - `dist/assets/index-6LIHrY2A.js = 124.66 kB` (gzip 43.24 kB)
  - Tier 2c 대비 **+39.14 kB** (JSON inline embedding 효과)

### Accepted 직후 적용

- 본 ADR `decisions/README.md` 인덱스에 추가
- `log.md` 본 결정 기록
- wet_run-web `README.md` 갱신

## 영향 받는 항목

- `wet_run-web/scripts/export_web_data.py`
- `wet_run-web/src/data/missions.json`
- `wet_run-web/src/data/ice_types.json`
- `wet_run-web/src/main.ts` (mission select UI)
- `wet_run-web/tests/missions.test.ts`
- `wet_run-web/README.md`
- `decisions/README.md`
- `log.md`

## 관련 결정

- **ADR-0199** (Accepted, 2026-08-25): Wet Run Web MVP (Tier 1)
- **ADR-0201** (Accepted, 2026-08-26): wet_run-web Tier 2b — Howler.js BGM
- **ADR-0202** (Accepted, 2026-08-26): wet_run-web Tier 2c — 15 missions + 12 ICE

## 향후 결정

- Tier 3 literal (`plan §8` cloud save + multiplayer + narrative) — MVP 초과
- wet_run-web Tier 4 (Cloud save sync, IndexedDB)
- Status effect VFX, SFX — 별도 ADR
- Phase-aware BGM (Tier 2b Option 2)

## 변경 이력

- 2026-08-26: Draft → **Accepted (Option 1: 30 missions + 30 ICE)** — 본 세션. Tier 2c 15/12 → Tier 3 30/30. T1-T5 mission 다양성, 6 zone, 10 fixer, T1-T4 ICE 다양성. mission select UI `y += 1` 변경 (30 row). 54 tests 통과, 124.66 kB bundle.