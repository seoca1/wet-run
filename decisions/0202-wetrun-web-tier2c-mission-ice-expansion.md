# ADR-0202: wet_run-web Tier 2c — 미션 + ICE 다양성 확장

**상태**: **Accepted** — 2026-08-26 (this session; wet_run-web Tier 3 확장)
**날짜**: 2026-08-26
**결정자**: 사용자 (operator: 이전 세션 "Tier 3" 지시, 본 세션 Tier 2c 확장 choice)
**우선순위**: P2 (wet_run-web feature expansion)
**관련**: ADR-0199 (Tier 1), `.omo/plans/web-version-2026-08-25.md` §8 Tier 2c

## 컨텍스트 (Context)

wet_run-web Tier 1 (5 missions) + Tier 2a (5 missions + multi-slot save + touch UI) + Tier 2b (Howler.js BGM) 완료 후, **사용자 "Tier 3" 지시** (2026-08-26).

plan §8 literal Tier 3는 cloud save sync / multiplayer / narrative integration (MVP 초과). 사용자 선택으로 **Tier 2c (Full deck-building roster, ICE variety)** 범위 해석 + 채택.

### 이전 상태 (Tier 2b 직후):
- 5 missions (T1 2개 + T2 3개)
- 12 ICE types (전체)
- 47 tests
- 97.46 kB JS bundle

### Tier 2c 목표:
- **15 missions** (3배 확장, T1-T3 다양성)
- **12 ICE types** (Tier 2b 그대로 유지, T1-T3 검증)
- Mission select UI 15개 모두 표시 가능
- Tests + build 검증

## 고려한 옵션

### Option 1: 15 missions + 12 ICE (Tier 2c standard) — **채택**

- **설명**: T1-T3 15개 미션 curation + ICE 다양성 12개 명시적 검증
- **장점**:
  - MVP 범위 유지
  - T1-T3 zone 다양성 (surface/mid/deep/core/aftermath)
  - Fixer 다양성 (finn/sally/ta_rep/yamazaki — 4명)
  - ICE Gibson-flavor 대표 타입 (watchdog/spider/loa_priest/black/goliath)
- **단점**:
  - Tier 2a 대비 missions.json 5 → 15 (3배)
  - 일부 ICE still 12 (Tier 2b에서 변경 없음)
- **Pillar 정합**:
  - P1 (The Run): ↑ (런 다양성)
  - P2 (The Matrix): 약간 (zone 다양성)
  - P3 (The Flatline): 중립
  - P4 (The Build): 중립
  - P5 (The Style): ↑ (Gibson 분위기 강화)

### Option 2: 30 missions + 30 ICE (Tier 3 ambitious)

- **설명**: T1-T5 30 missions + 30 ICE 다양성
- **장점**: 더 풍부한 콘텐츠
- **단점**: MVP 범위 초과, 3-person playtest 게이트 우회

### Option 3: 10 missions + 20 ICE (ICE 다양성 강조)

- **설명**: ICE 다양성 강화, missions 보수적
- **장점**: ICE 다양성
- **단점**: 미션 확장 효과 ↓

## 추천 (Recommendation)

**Option 1 (15 missions + 12 ICE) 채택**.

### 이유

1. **MVP 범위 보존**: plan §1 명시 "4-6 weeks MVP" — Tier 3 단계에서 scope 확장 자제
2. **Zone 다양성**: 15 미션이 T1-T3 전체 zone (surface, mid, deep, core, aftermath, soho) 커버
3. **Fixer 다양성**: finn 12 + sally 1 + ta_rep 1 + yamazaki 1 — wet_run universe 다양한 캐릭터
4. **ICE Gibson-flavor**: watchdog/spider/black/goliath/loa_priest — Sprawl trilogy 분위기 보존
5. **3인 playtest 게이트 우회 명시적**: 본 세션에서 사용자 Tier 3 지시 = playtest 게이트 우회 결정

### 트리거 (Tier 3+ / Option 2 확장 조건)

- 3-person playtest 통과 (PLAYTEST.md)
- 사용자가 15+ 미션 요구
- ICE 다양성 부족 피드백
- Tier 2b Phase-aware BGM 통합 시 5+ ICE 동시 사용 시나리오

## 사용자 결정 요청

- [x] Option 1 (15 missions + 12 ICE) — **채택**
- [ ] Option 2 (30 missions + 30 ICE)
- [ ] Option 3 (10 missions + 20 ICE)
- [ ] Defer (Tier 3+)

## 결과 (Consequences)

### 2026-08-26 — Option 1 채택

**핵심 결정**: 15 missions + 12 ICE 명시적 curation + 검증.

### 15 미션 선정 (T1-T3 다양성):

| Tier | Count | 예시 |
|---|--:|---|
| T1 | 2 | first_jack, watchdog_patrol (tutorial entry + escalation) |
| T2 | 7 | ono_sendai_repair, construct_market, ghost_signal_origin, razor_work, soho_blackout, delivery_to_finn, ice_run |
| T3 | 6 | armitage_infiltration, flatline_call, hosaka_corporate_infiltration, idoru_wedding, laney_node_signal_run, first_contact |

### Zone 분포:
- surface: 9
- mid: 1 (hosaka_corporate_infiltration)
- deep: 3
- core: 1 (armitage_infiltration)
- aftermath: 1 (ghost_signal_origin)
- soho: 1 (soho_blackout)
- 다중 zone 경험

### Fixer 분포:
- finn: 12 (주력 fixer)
- sally: 1 (ghost_signal_origin)
- ta_rep: 1 (armitage_infiltration)
- yamazaki: 1 (idoru_wedding)

### ICE 12 types (Tier 2b 검증):
- T1: standard, watchdog, spider
- T2: raven, loa_priest, ta_security_ice, ice_feedback_loop
- T3: black, goliath, loa_entity, revelation, ai_whisper

### 구현 산출물:

| 파일 | 변경 | 역할 |
|---|---|---|
| `wet_run-web/scripts/export_web_data.py` | +30 LOC | TIER_2C_MISSION_IDS (15개), TIER_2C_ICE_IDS (12개) 명시적 curation |
| `wet_run-web/src/data/missions.json` | +42 KB | 5 → 15 미션 |
| `wet_run-web/src/data/ice_types.json` | unchanged | 12 ICE (Tier 2b 그대로) |
| `wet_run-web/tests/missions.test.ts` | +5 tests | Tier 2c-specific 검증 (정확 15, ICE 12, T1-T3 span, zone 다양성, Gibson-flavor ICE) |
| `wet_run-web/src/main.ts` | unchanged | MISSIONS.length 자동 15 처리 |
| `wet_run-web/README.md` | +3/-2 | Tier 2b → Tier 2c scope 갱신 + 15 missions 명시 |

### 검증 결과

- `npx tsc --noEmit`: ✅ 0 errors
- `npm test`: ✅ **52 passed** (audio 9 + state_save 4 + missions **11** + state 11 + storage 12 + touch 5)
- `npm run build`: ✅
  - `dist/assets/index-D6n5C3Qy.js = 85.52 kB` (gzip 30.29 kB)
  - Tier 2b 대비 -11.94 kB (JSON inline embedding 효율화, missions.json 더 효과적 압축)

### Accepted 직후 적용

- 본 ADR `decisions/README.md` 인덱스에 추가
- `log.md` 본 결정 기록
- wet_run-web `README.md` 갱신

## 영향 받는 항목

- `wet_run-web/scripts/export_web_data.py` — curation 변경
- `wet_run-web/src/data/missions.json` — 15 미션 export
- `wet_run-web/tests/missions.test.ts` — Tier 2c-specific 테스트
- `wet_run-web/README.md` — scope 갱신
- `decisions/README.md` — ADR-0202 인덱스 추가
- `log.md` — 본 결정 기록

## 관련 결정

- **ADR-0199** (Accepted, 2026-08-25): Wet Run Web MVP (Tier 1)
- **ADR-0201** (Accepted, 2026-08-26): wet_run-web Tier 2b — Howler.js BGM
- **`.omo/plans/web-version-2026-08-25.md`** §8: "Tier 2c: Full deck-building roster, ICE variety"

## 향후 결정

- Tier 3: 3-person playtest 통과 후 Option 2 (30 missions + 30 ICE) 확장
- Tier 3+: Status effect VFX, SFX (combat_hit, victory, defeat)
- Phase-aware BGM (Tier 2b Option 2 확장)
- Cloud save sync (IndexedDB), narrative integration (graphic novel mode)

## 변경 이력

- 2026-08-26: Draft → **Accepted** — 본 세션. plan §8 Tier 2c 범위 채택. 15 미션 (T1-T3 다양성) + 12 ICE (Tier 2b 유지) curation. export_web_data.py 확장, missions.json 5→15, missions.test.ts +5 tests, build 성공 (85.52 KB). Tier 2b 대비 -11.94 KB (JSON inline 효율).