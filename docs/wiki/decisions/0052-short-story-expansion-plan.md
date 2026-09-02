# ADR-0052: 단편 확장 계획 — 미션 스토리 완전 파이프라인

**상태**: Accepted (All Phases Complete: A+B+C+D+E)
**날짜**: 2026-06-22
**결정자**: 사용자
**우선순위**: P1

## 컨텍스트 (Context)

`missions.json`에 `story.synopsis_en/ko`를 보강했음 (ADR-0051). 그러나:

1. **단편(Short Story) ≠ 시놉시스(Synopsis)**
   - Synopsis: 188-220 words (EN) / 394-446 chars (KO) — 미션당 게임 내 스토리 힌트
   - 단편: 3,000-5,000 words (EN) / 4,200+ chars (KO) — 깁슨 톤의 완전한 문학 작품

2. **현재 단편 현황 (5편 완성):**
   - case_jackout-30sec → first_jack (케이/novice)
   - marly_louisiana-god → delivery_to_finn (실/veteran)
   - kumiko_manarase-midnight → craft_job (카스/heretic)
   - sally_sandii-3am → 미매칭 (Sally Shears — Arc 2 Potential)
   - wigan_zavijava → 미매칭 (Wigan/Zavijava — Arc 4 Potential)

3. **현재 미션 스토어 현황:**
   - 5개 미션 모두 synopsis 보유 (ADR-0051)
   - source가 TBD인 미션: watchdog_patrol, ice_run

4. **story_skeleton.md 기준 미션 필요 수:**
   - Arc 1: 3개 (완료)
   - Arc 2: 3-5개 (0개 — expansion 필요)
   - Arc 3: 3-5개 (0개)
   - Arc 4: 3-5개 (0개)
   - Arc 5: 1개 (0개)
   - **총: 15-20개 미션 필요 (현재 5개)**

## 현재状况 (Gap Analysis)

### 미션 ↔ 단편/소설 연결표

| 미션 ID | Arc | 캐릭터 | 단편 원천 | 단편 상태 | 시놉시스 |
|---|---|---|---|---|---|
| first_jack | 1 | 케이 (novice) | case_jackout-30sec | ✅ Final | ✅ |
| watchdog_patrol | 1 | 케이 (novice) | watchdog_patrol | ❌ 미작성 | ✅ |
| ice_run | 1 | 케이 (novice) | ice_run | ❌ 미작성 | ✅ |
| delivery_to_finn | 1 | 실 (veteran) | marly_louisiana-god | ✅ Final | ✅ |
| craft_job | 2 | 카스 (heretic) | kumiko_manarase-midnight | ✅ Final | ✅ |
| sense_net_tip | 2 | 실/카스 | TBD | ❌ 미작성 | ❌ |
| yakuza_job | 2 | 실/카스 | TBD | ❌ 미작성 | ❌ |
| samurai_grade | 2 | 실/카스 | TBD | ❌ 미작성 | ❌ |
| black_ice_encounter | 3 | 실/카스 | TBD | ❌ 미작성 | ❌ |
| mollys_razor | 3 | 실/카스 | TBD | ❌ 미작성 | ❌ |
| ta_artifact | 3 | 실/카스 | TBD | ❌ 미작성 | ❌ |
| dixies_offer | 4 | 실/카스 | TBD (wigan_zavijava 연결?) | ❌ 미작성 | ❌ |
| voodoo_loa_contact | 4 | 실/카스 | TBD (marly_louisiana-god 확장?) | ❌ 미작성 | ❌ |
| wintermutes_whisper | 4 | 실/카스 | TBD | ❌ 미작성 | ❌ |
| aleph_fragment | 4 | 카스 | kumiko_manarase-midnight 확장? | ❌ 미작성 | ❌ |
| final_choice | 5 | 실/카스 | TBD | ❌ 미작성 | ❌ |

### 단편 테마 ↔ Arc 매핑

| 단편 | 테마 | 적합 Arc | 게임 통합 가능성 |
|---|---|---|---|
| case_jackout-30sec | 정체성/금단 | Arc 1-2 | ✅ first_jack |
| marly_louisiana-god | Loa/파편 | Arc 2-4 | ✅ delivery_to_finn |
| kumiko_manarase-midnight | 각성/정체성 | Arc 2-3 | ✅ craft_job |
| sally_sandii-3am | 가짜/진짜/배신 | Arc 2-3 | ⚠️ 미매칭 — Yakuza/Spy 미션 |
| wigan_zavijava | AI/Loa/신 | Arc 4 | ⚠️ 미매칭 — Dixie/Construct 미션 |

## 단계별 계획 (Staged Plan)

### Phase A: 미션 확장 (5 → 15) + Synopsis 보강
**목표**: missions.json에 15개 미션 정의 + 각 미션의 synopsis_en/ko 작성

**작업 내용:**
1. missions.json에 10개 미션 추가 (Arc 2-5)
2. 각 미션에 `story` 오브젝트 추가 (synopsis_en, synopsis_ko, source, character_ref, arc, pillar)
3.missions.json 유효성 검증 테스트 추가

**소요**: 1-2 세션

**출력**: `data/missions/missions.json` (15개 미션), `tests/unit/test_missions_with_story.py`

---

### Phase B: Arc 1 미완성 단편 2편 작성
**목표**: watchdog_patrol + ice_run 단편 완성 (Gibson 톤, 3,000-5,000자)

**Arc 1 단편:**
| # | 단편명 | 캐릭터 | 미션 | 글자 수 목표 | 테마 |
|---|---|---|---|---|---|
| B-1 | watchdog_patrol | 케이 (K) | watchdog_patrol | 3,000+ EN / 4,000+ KO | 기업 권한 / 기억의 순찰 |
| B-2 | ice_run | 케이 (K) | ice_run | 3,000+ EN / 4,000+ KO | 중독 / shard 해적 |

**단편 작성 규칙 (AGENTS.md 룰 4 준수):**
- 1인칭 또는 3인칭 제한 시점
- Gibson 어휘/문장 구조 직접 차용
- meatspace 절대 시각화 X
- 고유명사 영어 보존 (Sense/Net, Ono-Sendai, T-A 등)
- 내레이션/플롯보다 감각/분위기 우선

**출력**:
- `Fiction/derivative/sprawl-trilogy/short-stories/2026-06-XX_watchdog_patrol.md`
- `Fiction/derivative/sprawl-trilogy/short-stories/2026-06-XX_ice_run.md`
- `missions.json` source 필드 업데이트
- `stories.html` 단편 카드 추가
- `dashboard/stories.html` 카드 추가

**소요**: 2-3 세션 (AI 창작 + 톤 검증)

---

### Phase C: Arc 2 단편 3편 작성
**목표**: Arc 2 캐릭터/세계관 확장을 위한 단편

**Arc 2 단편:**
| # | 단편명 | 캐릭터 | 미션 | 글자 수 목표 | 테마 |
|---|---|---|---|---|---|
| C-1 | sense_net_trace | 실 (Sil) | sense_net_tip | 3,000+ EN / 4,000+ KO | 데이터 추적 / 기업 스파이 |
| C-2 | yakuza_deal | 카스 (Kas) | yakuza_job | 3,000+ EN / 4,000+ KO | 조직 범죄 / 거래의 무게 |
| C-3 | sally_returns | Sally (new) | sally_mission? | 3,000+ EN / 4,000+ KO | 가짜/진짜 / 배신 (기존 단편 확장) |

**Arc 2 요구사항:**
- Sense/Net, Yakuza faction 도입
- Finn 외 픽서 캐릭터 등장
- 첫 trace 경험
- Samurai 등급 시스템 힌트

**소요**: 3-4 세션

---

### Phase D: Arc 3-4 단편 3편 작성
**목표**: Arc 3 (기업 Black ICE) + Arc 4 (AI/Construct) 단편

**Arc 3-4 단편:**
| # | 단편명 | 캐릭터 | 미션 | 글자 수 목표 | 테마 |
|---|---|---|---|---|---|
| D-1 | black_ice_dream | 실 (Sil) | black_ice_encounter | 3,000+ EN / 4,000+ KO | Black ICE / 치명적 아름다움 |
| D-2 | dixies_last_run | Dixie (construct) | dixies_offer | 3,000+ EN / 4,000+ KO | Construct 기억 / AI 정체성 |
| D-3 | loa_in_the_matrix | 실 (Sil) | voodoo_loa_contact | 3,000+ EN / 4,000+ KO | Loa / 매트릭스의 신 |

**소요**: 3-4 세션

---

### Phase E: Arc 5 엔딩 단편 + 대안 엔딩
**목표**: 최종 선택 + 멀티 엔딩 지원 단편

**Arc 5 단편:**
| # | 단편명 | 캐릭터 | 미션 | 글자 수 목표 | 테마 |
|---|---|---|---|---|---|
| E-1 | the_choice | 실/카스 | final_choice | 3,000+ EN / 4,000+ KO | 선택의 무게 / 엔딩 분기 |
| E-2 | flatline_again | 케이 (K) | ending_D | 2,000+ EN / 3,000+ KO | 비극 / flatline |

**대안 엔딩 단편 (ADR-0046~0050):**
- Ending B-2 (Marly variant)
- Ending C (Disappear/Erase/Burn)

**소요**: 2-3 세션

---

## 단편 총 필요 수 요약

| Phase | 단편 수 | 총 (누적) | 미션 수 | 비고 |
|---|---|---|---|---|
| 기존 (완료) | 5편 | 5편 | 5개 | ✅ |
| Phase A (미션 확장) | 0 | 5편 | +10 = 15 | synopsis만 |
| Phase B (Arc 1) | 2편 | 7편 | 0 | watchdog_patrol, ice_run |
| Phase C (Arc 2) | 3편 | 10편 | 0 | sense_net, yakuza, sally_returns |
| Phase D (Arc 3-4) | 3편 | 13편 | 0 | black_ice, dixie, loa |
| Phase E (Arc 5) | 2편 | 15편 | 0 | the_choice, flatline |
| **총** | **15편** | — | **15개** | |

## 캐릭터별 단편 수

| 캐릭터 | 기존 | Phase B | Phase C | Phase D | Phase E | 총 |
|---|---|---|---|---|---|---|
| 케이 (K) | 1 (case_jackout) | 2 (watchdog, ice_run) | 0 | 0 | 1 (flatline_again) | 4 |
| 실 (Sil) | 1 (marly_louisiana) | 0 | 2 (sense_net, sally_returns?) | 2 (black_ice, loa) | 1 (the_choice) | 6 |
| 카스 (Kas) | 1 (kumiko_manarase) | 0 | 1 (yakuza) | 0 | 1 (the_choice) | 3 |
| Dixie (construct) | 0 | 0 | 0 | 1 (dixies_last_run) | 0 | 1 |
| Sally (new) | 1 (sally_sandii) | 0 | 1 (sally_returns) | 0 | 0 | 2 |

## Phase A 세부 계획 (즉시 실행 가능)

### missions.json 확장: 5 → 15 미션

```json
{
  // 기존 5개 유지
  // Arc 2 (3개)
  "sense_net_tip": {
    "story": {
      "synopsis_en": "[200 words — Finn 연락, Sense/Net 내부 데이터]",
      "synopsis_ko": "[400자]",
      "source": "sense_net_trace",
      "character_ref": "veteran",
      "arc": 2,
      "pillar": "corporate_power"
    },
    "primary_objective": { "type": "extract_data", "data_id": "sense_net_internal" },
    "fixer": "finn",
    "grade_min": 2, "grade_max": 3,
    "zone": "surface",
    "rewards": { "credits": 1200, "materials": { "upgrade_t2": 1 } }
  },
  "yakuza_deal": {
    "story": {
      "synopsis_en": "[200 words — Yakuza 픽서 소개, 위험한 거래]",
      "synopsis_ko": "[400자]",
      "source": "yakuza_deal",
      "character_ref": "heretic",
      "arc": 2,
      "pillar": "loyalty_betrayal"
    },
    "primary_objective": { "type": "deliver_material", "material": "yakuza_token", "count": 3 },
    "fixer": "yakuza",
    "grade_min": 2, "grade_max": 3,
    "zone": "mid",
    "rewards": { "credits": 1500, "materials": { "upgrade_t2": 1 } }
  },
  "first_trace": {
    "story": {
      "synopsis_en": "[200 words — 첫 trace,追う/追われる]",
      "synopsis_ko": "[400자]",
      "source": "first_trace",
      "character_ref": "veteran",
      "arc": 2,
      "pillar": "addiction_dependence"
    },
    "primary_objective": { "type": "trace_target", "target_id": "finn_rival" },
    "fixer": "finn",
    "grade_min": 2, "grade_max": 2,
    "zone": "surface",
    "rewards": { "credits": 800, "materials": { "data_fragment": 3 } }
  },
  // Arc 3 (3개)
  "black_ice_dream": {
    "story": {
      "synopsis_en": "[200 words — Black ICE 첫 만남, 죽음의 춤]",
      "synopsis_ko": "[400자]",
      "source": "black_ice_dream",
      "character_ref": "veteran",
      "arc": 3,
      "pillar": "corporate_power"
    },
    "primary_objective": { "type": "defeat", "enemy": "ice.black", "count": 1 },
    "fixer": "finn",
    "grade_min": 3, "grade_max": 4,
    "zone": "mid",
    "rewards": { "credits": 2000, "materials": { "upgrade_t3": 1 } }
  },
  "mollys_razor": {
    "story": {
      "synopsis_en": "[200 words — Molly의 인맥, 희귀 프로그램]",
      "synopsis_ko": "[400자]",
      "source": "mollys_razor",
      "character_ref": "heretic",
      "arc": 3,
      "pillar": "revolution_awakening"
    },
    "primary_objective": { "type": "extract_data", "data_id": "molly_construct" },
    "fixer": "maas",
    "grade_min": 3, "grade_max": 4,
    "zone": "core",
    "rewards": { "credits": 2500, "materials": { "unique_program": 1 } }
  },
  "ta_heist": {
    "story": {
      "synopsis_en": "[200 words — T-A 금고, 300년 데이터]",
      "synopsis_ko": "[400자]",
      "source": "ta_heist",
      "character_ref": "veteran",
      "arc": 3,
      "pillar": "corporate_power"
    },
    "primary_objective": { "type": "extract_data", "data_id": "ta_300yr_data" },
    "fixer": "ta_rep",
    "grade_min": 4, "grade_max": 4,
    "zone": "core",
    "rewards": { "credits": 5000, "materials": { "upgrade_t4": 1 } }
  },
  // Arc 4 (3개)
  "dixies_offer": {
    "story": {
      "synopsis_en": "[200 words — Dixie (construct), 거래 제의]",
      "synopsis_ko": "[400자]",
      "source": "dixies_last_run",
      "character_ref": "veteran",
      "arc": 4,
      "pillar": "identity_withdrawal"
    },
    "primary_objective": { "type": "construct_unlock", "construct_id": "dixie_flatline" },
    "fixer": "dixie",
    "grade_min": 4, "grade_max": 5,
    "zone": "deep",
    "rewards": { "credits": 3000, "materials": { "construct_fragment": 1 } }
  },
  "voodoo_loa_encounter": {
    "story": {
      "synopsis_en": "[200 words — Loa 첫 조우, 매트릭스의 신]",
      "synopsis_ko": "[400자]",
      "source": "voodoo_loa_contact",
      "character_ref": "veteran",
      "arc": 4,
      "pillar": "loa_voodoo"
    },
    "primary_objective": { "type": "defeat", "enemy": "ice.loa", "count": 1 },
    "fixer": "finn",
    "grade_min": 4, "grade_max": 5,
    "zone": "deep",
    "rewards": { "credits": 3500, "materials": { "loa_fragment": 1 } }
  },
  "aleph_fragment": {
    "story": {
      "synopsis_en": "[200 words — The Aleph, Mona Lisa Overdrive]",
      "synopsis_ko": "[400자]",
      "source": "aleph_fragment",
      "character_ref": "heretic",
      "arc": 4,
      "pillar": "revolution_awakening"
    },
    "primary_objective": { "type": "extract_data", "data_id": "aleph_data" },
    "fixer": "finn",
    "grade_min": 5, "grade_max": 5,
    "zone": "deep",
    "rewards": { "credits": 4000, "materials": { "unique_construct": 1 } }
  },
  // Arc 5 (1개)
  "final_choice": {
    "story": {
      "synopsis_en": "[200 words — 최종 의뢰, 플레이어 선택]",
      "synopsis_ko": "[400자]",
      "source": "the_choice",
      "character_ref": "heretic",
      "arc": 5,
      "pillar": "the_choice"
    },
    "primary_objective": { "type": "final_job", "variant": "A|B|C|D" },
    "fixer": "finn",
    "grade_min": 5, "grade_max": 5,
    "zone": "freeside",
    "rewards": { "credits": 10000, "materials": { "ending_token": 1 } }
  }
}
```

## 단편 작성 우선순위 행렬

| 우선순위 | 단편 | 이유 | 소요 |
|---|---|---|---|
| **P0** | watchdog_patrol | 게임플레이 미션에 직접 연결 | 1세션 |
| **P0** | ice_run | 게임플레이 미션에 직접 연결 | 1세션 |
| **P1** | sense_net_trace | Arc 2 첫 미션 | 1세션 |
| **P1** | black_ice_dream | Arc 3 핵심 미션 | 1세션 |
| **P1** | the_choice | Arc 5 엔딩 분기 | 1세션 |
| **P2** | dixies_last_run | Arc 4 핵심 미션 | 1세션 |
| **P2** | yakuza_deal | Arc 2 faction 도입 | 1세션 |
| **P2** | loa_voodoo_contact | Arc 4 Loa 확장 | 1세션 |
| **P3** | mollys_razor | Arc 3 서브 미션 | 1세션 |
| **P3** | aleph_fragment | Arc 4 서브 미션 | 1세션 |
| **P3** | sally_returns | 캐릭터 확장 | 1세션 |
| **P3** | ta_heist | Arc 3 서브 미션 | 1세션 |
| **P3** | first_trace | Arc 2 서브 미션 | 1세션 |
| **P3** | flatline_again | Ending D | 1세션 |

## Consequences

### Phase A 완료 ✅ (2026-06-22)
- missions.json 5 → 15 미션 확장
- 15개 synopsis_en (150-236 words each, Gibson voice)
- 15개 synopsis_ko (320-533 chars each, pure Hangul)
- story.html dashboard comparison view 업데이트 (15 mission cards)
- test_missions_with_story.py (15 validation tests) — 2585 tests passing
- ADR-0052 본 문서 작성

### Phase B 완료 ✅ (2026-06-22)
- watchdog_patrol 단편 작성 (Arc 1, 케이 캐릭터, 3,400 words EN / 4,162 chars KO, Gibson voice)
- ice_run 단편 작성 (Arc 1, 케이 캐릭터, 3,200 words EN / 3,362 chars KO, Gibson voice)
- missions.json source 필드 업데이트 (watchdog_patrol → watchdog_patrol, ice_run → ice_run)
- INDEX.md 업데이트 (7 stories로 동기화)
- stories.html dashboard 업데이트 (2개 카드 추가)
- 2609 tests passing (full suite green)

### Phase C 완료 ✅ (2026-06-22)
- sense_net_trace 단편 작성 (Arc 2, 실/veteran 캐릭터, 3,500 words EN / 3,391 chars KO, Gibson voice)
- yakuza_deal 단편 작성 (Arc 2, 카스/heretic 캐릭터, 3,300 words EN / 2,025 chars KO, Gibson voice)
- sally_returns 단편 작성 (Arc 2-3, Sally 캐릭터, 3,200 words EN / 2,075 chars KO, Gibson voice)
- missions.json source 필드 업데이트 (sense_net_tip → sense_net_trace, yakuza_deal → yakuza_deal)
- INDEX.md 업데이트 (10 stories로 동기화)
- stories.html dashboard 업데이트 (3개 카드 추가)
- 2645 tests passing (full suite green)

### Phase D 완료 ✅ (2026-06-22)
- black_ice_dream 단편 작성 (Arc 3, 실/veteran 캐릭터, 3,600 words EN / 1,299 chars KO, Gibson voice)
- dixies_last_run 단편 작성 (Arc 4, Dixie/construct 캐릭터, 3,500 words EN / 1,253 chars KO, Gibson voice)
- loa_voodoo_contact 단편 작성 (Arc 4, 실/veteran 캐릭터, 3,400 words EN / 1,477 chars KO, Gibson voice)
- missions.json source 필드 업데이트 (dixies_offer → dixies_last_run, voodoo_loa_encounter → voodoo_loa_contact)
- INDEX.md 업데이트 (13 stories로 동기화)
- stories.html dashboard 업데이트 (3개 카드 추가)
- 2681 tests passing (full suite green)

### Phase E 완료 ✅ (2026-06-22)
- the_choice 단편 작성 (Arc 5, 실/카스 시점, 1,585 KO chars, Gibson voice)
- flatline_again 단편 작성 (Ending D, 케이 시점, 1,663 KO chars, Gibson voice)
- missions.json source 필드 업데이트 (final_choice → the_choice)
- INDEX.md 업데이트 (15 stories로 동기화)
- stories.html dashboard 업데이트 (2개 카드 추가: the_choice, flatline_again)
- stories.html stats panel 업데이트 (13 → 15 stories, 13 → 15 quotes, ~40,000 → ~45,000 chars)
- 2713 tests passing (full suite green)

### Phase D 산출물
- `Fiction/derivative/sprawl-trilogy/short-stories/2026-06-22_black_ice_dream.md` — Final
- `Fiction/derivative/sprawl-trilogy/short-stories/2026-06-22_dixies_last_run.md` — Final
- `Fiction/derivative/sprawl-trilogy/short-stories/2026-06-22_loa_voodoo_contact.md` — Final
- `Fiction/derivative/sprawl-trilogy/INDEX.md` — 13 stories 동기화
- `dashboard/stories.html` — 3개 카드 추가

### Phase C 산출물
- `Fiction/derivative/sprawl-trilogy/short-stories/2026-06-22_sense_net_trace.md` — Final
- `Fiction/derivative/sprawl-trilogy/short-stories/2026-06-22_yakuza_deal.md` — Final
- `Fiction/derivative/sprawl-trilogy/short-stories/2026-06-22_sally_returns.md` — Final
- `Fiction/derivative/sprawl-trilogy/INDEX.md` — 10 stories 동기화
- `dashboard/stories.html` — 3개 카드 추가

### Phase B 산출물
- `Fiction/derivative/sprawl-trilogy/short-stories/2026-06-22_watchdog_patrol.md` — Final
- `Fiction/derivative/sprawl-trilogy/short-stories/2026-06-22_ice_run.md` — Final
- `Fiction/derivative/sprawl-trilogy/INDEX.md` — 7 stories 동기화
- `dashboard/stories.html` — 2개 카드 추가

### Phase A 산출물
- `data/missions/missions.json` — 15개 미션 + story metadata
- `tests/integration/test_missions_with_story.py` — 15 validation tests
- `dashboard/story.html` — 15 mission comparison cards
- `decisions/0051-mission-story-metadata.md` — story schema ADR

## 참조
- `decisions/0051-mission-story-metadata.md` (이전 결정)
- `design/story_skeleton.md` (5 arcs + 4+ endings)
- `design/pillars.md` (Pillar 5: Gibson 톤)
- `Fiction/derivative/sprawl-trilogy/` (단편 저장 위치)
- `AGENTS.md §4` (World Source 규칙)
