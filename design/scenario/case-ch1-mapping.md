# 케이 Ch1 단편소설 → 게임 이벤트 매핑

**문서 상태**: UPDATED
**Updated**: 2026-06-23
**Target**: 케이 Ch1-5 확장 + 실/카스 동일 구조 적용

---

## 1. 게임플레이 순차 흐름표

| 순서 | 게임 상태 | Phase | Episode | 컷신 | 전투 | 행동 | 깨달음 | 얻음/손실 |
|------|---------|-------|---------|------|------|------|--------|----------|
| 1 | CHARACTER_SELECT | — | — | — | — | 캐릭터 선택 | — | — |
| 2 | PROLOGUE | — | — | Prologue GN scene | — | 프롤로그 컷신 | — | — |
| 3 | HUB | — | — | **CHATTO'S 24/7** | — | 잭아웃 후 기상, 소환 수령 | 매트릭스는 빚의 상태 | — |
| 4 | HUB | WAIT | ep_01 | — | — | 핀의 사무실로 이동 | — | — |
| 5 | HUB | BRIEFING | ep_02 | — | — | 미션 브리핑 수락 | 모든 일은 미래からの 대출 | 접근 코드 |
| 6 | HUB→MATRIX | — | — | **JACK-IN** | — | 챠토 24/7로 이동, 잭인 | — | — |
| 7 | MATRIX | JACK_IN | ep_03 | — | **Wisp T1 (bypass)** | Wisp T1 우회 | 매트릭스는 전쟁 구역 | — |
| 8 | MATRIX | EXTRACT_DATA | ep_04 | — | **Watchdog (피해 15HP)** | 데이터 추출, Watchdog 격파 | 죽어도 데이터는 진짜 | 급여 데이터 |
| 9 | JACK_OUT | — | — | — | — | 잭아웃 | — | — |
| 10 | DEBRIEF | DEBRIEF | ep_05 | **JACK-OUT** | — | 데이터 배달, 페이 수령 | 첫 잭은 마지막이 아니다 | 5,000 크레딧, -15 HP |

**전투 수**: 2회 (Wisp T1 우회 성공, Watchdog 피해 후 잭아웃)

---

## 2. 에피소드 vs 게임 비교표

| Episode | Type | 단편 서사 | Game Phase | Combat | 깨달음 | 얻음 |
|---------|------|---------|-----------|--------|--------|------|
| ep_01 | encounter | 기상, 핀의 소환 | HUB (WAIT) | 없음 | 매트릭스는 빚의 상태 | — |
| ep_02 | heist_briefing | 핀의 제의, 일 수락 | BRIEFING | 없음 | 모든 일은 미래からの 대출 | 접근 코드 |
| ep_03 | heist_execution | 잭인, Wisp T1 ICE | JACK_IN | ✅ Wisp T1 (bypass) | 매트릭스는 전쟁 구역 | — |
| ep_04 | heist_payday | 데이터 추출, Watchdog ICE | EXTRACT_DATA | ✅ Watchdog (피해) | 죽어도 데이터는 진짜 | 급여 데이터 |
| ep_05 | resolution | 배달, 페이, 몰리의 일 | DEBRIEF | 없음 | 첫 잭은 마지막이 아니다 | 5,000 크레딧 |

---

## 3. Combat 상세

| Encounter | Episode | Enemy | Type | Difficulty | Tactics | Outcome | Damage |
|-----------|---------|-------|------|------------|---------|---------|--------|
| ice_01 | ep_03 | Wisp T1 Patrol | ice_wisp_t1 | 1 | bypass_attempt + fragmentation_bomb | bypass | 0 |
| ice_02 | ep_04 | Watchdog Corporate ICE | ice_watchdog | 2 | stealth + speed_copy | damage_taken | 15 HP |

---

## 4. GN Scene → Episode 매핑

| GN Scene | Title | Episode | 사용 Beats |
|----------|-------|---------|-----------|
| 01_chattos.json | CHATTO'S 24/7 | ep_01 (cutscene_start) | beat_01_01, beat_01_02 |
| 02_jackin.json | JACK-IN | ep_03 (cutscene_mid) | beat_03_02, beat_03_03 |
| 03_jackout.json | JACK-OUT | ep_04 (cutscene_end) | beat_04_04 |
| 04_finn.json | THE FINN'S OFFICE | ep_02, ep_05 | beat_02_01, beat_05_01 |
| 05_refusal.json | THE REFUSAL | ep_05 | beat_05_02, beat_05_03 |
| 06_freedom.json | THE FREEDOM | ep_05 | beat_05_04 |

---

## 5. Phase → Story Beat 완전 매핑

### Phase 0: WAIT (ep_01)
- `beat_01_01` (interior_monologue) → `wake_up`
- `beat_01_02` (action) → `receive_summons`
- `beat_01_03` (dialogue) → `enter_finn_office`

### Phase 1: BRIEFING (ep_02)
- `beat_02_01` (dialogue) → `accept_mission`
- `beat_02_02` (dialogue) → `learn_mission_details`
- `beat_02_03` (action) → `receive_codes`

### Phase 2: JACK_IN (ep_03)
- `beat_03_01` (action) → `travel_to_jack_in_spot`
- `beat_03_02` (action) → `jack_in`
- `beat_03_03` (combat) → `ice_encounter` (Wisp T1)
- `beat_03_04` (action) → `navigate_past_ice`

### Phase 3: EXTRACT_DATA (ep_04)
- `beat_04_01` (action) → `access_database`
- `beat_04_02` (combat) → `ice_encounter` (Watchdog)
- `beat_04_03` (action) → `complete_extraction`
- `beat_04_04` (action) → `jack_out`

### Phase 4: DEBRIEF (ep_05)
- `beat_05_01` (dialogue) → `deliver_data`
- `beat_05_02` (dialogue) → `receive_next_mission_brief`
- `beat_05_03` (interior_monologue) → `leave_finn_office`
- `beat_05_04` (action) → `accept_side_quest`

---

## 6. 분량 비교

| 구분 | Before | After | 증가율 |
|------|--------|-------|--------|
| EN chars | 1,406 | 4,797 | **3.4x** |
| KO chars | 2,147 | 2,204 | 1.0x |
| Episodes | 0 | 5 | ✅ |
| Combat encounters | 0 | 2 | ✅ |
| Realizations | 0 | 5 | ✅ |
| Story beats | 0 | 18 | ✅ |

---

## 7. 대시보드 동적 로딩

**출처 파일**: `dashboard/data/story/arcs/chapter_flow.json`

```javascript
// story.html의 chapter-flow-viewer가 동적으로 로드
fetch('../data/story/arcs/chapter_flow.json')
  .then(r => r.json())
  .then(data => {
    // 케이/실/카스 캐릭터별 챕터 흐름 렌더링
    // Phase, Combat, Gain, Cutscene 정보 포함
  });
```

**연동 파일**:
- `prototype/src/wet_run/engine/chapter_cutscene.py` — `PhaseData`에 `combat`, `gain`, `loss` 필드 추가
- `prototype/data/story/arcs/case_arc.json` — phases에 story-specific 메타데이터 추가
- `dashboard/story.html` — 챕터 흐름 뷰어 섹션 추가
- `.github/workflows/pages.yml` — `dashboard/data/` 디렉토리 복사 추가

---

## 8. 다음 단계

1. **케이 Ch2-5** 동일한 구조로 확장
2. **실/카스** 동일 구조 적용 (case_expanded.json → sil_expanded.json, kas_expanded.json)
3. **HTML generator** episode/beat 기반 완전 재작성
4. **play.py** story beat 시스템 연동
