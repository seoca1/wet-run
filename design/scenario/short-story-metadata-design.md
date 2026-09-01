# 단편소설 → 게임 이벤트 매핑 설계

**문서 상태**: DRAFT
**Created**: 2026-06-23
**Target**: 케이 Ch1-5 확장 + 실/카스 동일 구조 적용

---

## 1. 문제 분석

### 현재 상태: 단편소설 = 문학적 ├⟨ introspection⟩ (심리 독白)

| 요소 | 현재 단편소설 | 실제 장르 단편소설 | 차이 |
|------|-------------|------------------|------|
| 사건 (Events) |杰克아웃 후 내면 독백 | 뚜렷한 플롯 비트 (체이스, 해킹, 배신) | ❌ |
| 전투 (Combat) | 없음 | ICE 뚫기, 총격전, 추격전 | ❌ |
| 깨달음 (Realization) | 암묵적 (반영 필요) | 핵심 결정적 순간明确规定 | ❌ |
| 얻음 (Gain) | 없음 | 데이터, 돈, 정보, 관계, 스킬 | ❌ |
| 분량 | ~1,400 EN chars | 장르 标准: 5,000-15,000 EN chars | ❌ |

**핵심 문제**: 현재 단편소설은 게임 플레이에 부합할 만큼의 **객관적 사건**이 부족

---

## 2. 메타데이터 구조 설계

### 새 단편소설 JSON 스키마

```json
{
  "character": "novice",
  "id": "chapter_novice",
  "title_en": "The First Jack",
  "title_ko": "첫 잭인",
  "subtitle_en": "...",
  "subtitle_ko": "...",

  "excerpt_en": "...",      // 기존: 문학적 intro
  "excerpt_ko": "...",

  // [NEW] 메타데이터
  "metadata": {
    "genre": "cyberpunk_heist",     // 장르 태그
    "target_length_en": 8000,       // 목표 분량 (EN chars)
    "target_length_ko": 12000,       // 목표 분량 (KO chars)
    "tone": "noir_tech",            // 톤
    "source": "neuromancer"         // 원작 출처
  },

  // [NEW] 에피소드 구조
  "episodes": [
    {
      "episode_id": "ep_01",
      "title_en": "The Meet",
      "title_ko": "만남",
      "type": "encounter",           // encounter | heist | chase | betrayal | revelation
      "location_en": "Chiba City",
      "location_ko": "지바 시",
      "summary_en": "Case arrives at the Finn's office...",
      "summary_ko": "케이가 핀의 사무실에 도착한다...",
      "beats": [
        {
          "beat_id": "beat_01_01",
          "type": "dialogue",         // dialogue | action | combat | exploration
          "text_en": "The Finn slides a credstick across the table.",
          "text_ko": "핀이 테이블 너머로 크레딧스틱을 밀어낸다.",
          "game_phase": "BRIEFING",
          "game_action": "accept_mission"
        },
        {
          "beat_id": "beat_01_02",
          "type": "combat",
          "text_en": "Corporate ICE patrol detected on the firewall.",
          "text_ko": "방화벽에서 기업 ICE 순찰이 감지됐다.",
          "game_phase": "EXTRACT_DATA",
          "game_action": "ice_encounter",
          "enemy_type": "ice_watchdog",
          "difficulty": 1
        }
      ],
      "realization": {
        "text_en": "The matrix is not a place. It is a state of mind.",
        "text_ko": "매트릭스는 장소가 아니다. 정신 상태다.",
        "insight_level": 1
      },
      "gain": {
        "type": "data",              // data | money | info | relationship | skill
        "item_id": "sense_net_payroll",
        "description_en": "Sense/Net employee payroll data",
        "description_ko": "Sense/Net 직원 급여 데이터"
      }
    }
  ],

  // [NEW] 전투/임무 로그
  "combat_log": [
    {
      " encounter_id": "ice_01",
      "location": "Sense/Net corporate firewall",
      "enemy": "Watchdog ICE (Grade 1)",
      "outcome": "bypass",           // victory | bypass | defeat | retreat
      "tactics_used": ["fragmentation_bomb", "stealth"],
      "damage_taken": 0,
      "earnings": 5000
    }
  ],

  // [NEW] 깨달음 트래킹
  "realizations": [
    {
      "id": "real_01",
      "episode_ref": "ep_01",
      "text_en": "The matrix is not a place...",
      "text_ko": "매트릭스는 장소가 아니라...",
      "unlocks": ["phase_jack_out", "skill_matrix_vision"]
    }
  ],

  // [NEW] 얻음 트래킹
  "gains": [
    {
      "id": "gain_01",
      "episode_ref": "ep_01",
      "type": "money",
      "amount": 5000,
      "currency": "credits"
    },
    {
      "id": "gain_02",
      "episode_ref": "ep_02",
      "type": "relationship",
      "character": "molly",
      "status": "neutral_to_allied"
    }
  ],

  // 기존 필드
  "duration_ms": 12000,
  "next_screen": "HUB",
  "char_delay_ms": 60
}
```

---

## 3. 단편 vs 게임 비교표 (신규)

### 케이 챕터 1 예시

| Story Beat | Type | Game Phase | Game Action | Combat | Realization | Gain |
|-----------|------|------------|-------------|--------|-------------|------|
| 핀의 사무실 도착 | encounter | BRIEFING | talk_to_npc | 없음 | — | 미션 수락 |
| Sense/Net 방화벽 돌파 | heist | EXTRACT_DATA | bypass_ice | ✅ Watchdog ICE | ICE는 살아있다 | 데이터 |
| 내부 네트워크 침투 | exploration | EXTRACT_DATA | navigate_nodes | 없음 | — | 내부 정보 |
| 백업 ICE遭遇 | heist | EXTRACT_DATA | fight_ice | ✅ Backup ICE | 죽으면 깨어난다 | 추가 데이터 |
| 잭아웃 | transition | JACK_OUT | jack_out | 없음 | 30초 후의 삶 | 보상 수령 |

### 비교표 템플릿

```
| 에피소드 | 유형 | 단편 서사 | 게임 Phase | 전투 | 깨달음 | 얻음 |
|---------|------|---------|-----------|------|--------|------|
| ep_01 | encounter | 핀의 첫 거래 | BRIEFING | 없음 | 거래에는 대가가 있다 | 5,000 크레딧 |
| ep_02 | heist | Sense/Net 해킹 | MATRIX | ✅ ICE | 매트릭스는 물리적이다 | 데이터 |
| ... | ... | ... | ... | ... | ... | ... |
```

---

## 4. 단계별 구현 계획

### Phase 1: 케이 Ch1 메타데이터 설계 (1시간)
- [ ] 에피소드 5개 정의
- [ ] 각 에피소드별 beats 정의
- [ ] 전투 로그 설계
- [ ] 깨달음/얻음 트래킹 설계

### Phase 2: 케이 Ch1 스토리 확장 (2시간)
- [ ] 현재 1,400 EN chars → 8,000 EN chars 목표로 확장
- [ ] 각 에피소드별 상세 narrative 작성
- [ ] 전투シーン 추가
- [ ] 내면 독백 → 실제 사건으로 변환

### Phase 3: 게임 Phase 매핑 (1시간)
- [ ] 각 story beat → game phase 매핑
- [ ] arc JSON phases 확장
- [ ] combat_log 기반 난이도 조정

### Phase 4: 실/카스 동일 구조 적용 (2시간)
- [ ] 실 Ch1-5 동일 메타데이터 구조
- [ ] 카스 Ch1-5 동일 메타데이터 구조
- [ ] 일관된 비교표 생성

### Phase 5: 테스트 및 검증 (1시간)
- [ ] play.py로 수동 테스트
- [ ] 단편소설 HTML 재生成
- [ ] 비교표 최종 갱신

---

## 5. 목표 분량 기준

| 구분 | 현재 | 목표 | 비고 |
|------|------|------|------|
| 케이 Ch1 EN | 1,406 chars | 8,000 chars | 5.7x 확장 |
| 케이 Ch1 KO | 2,147 chars | 12,000 chars | 5.6x 확장 |
| 전체 (3 chars × 5 ch) | 4,080 EN | 120,000 EN | 30x 확장 |

**장르 단편소설 표준**: 5,000-15,000 EN chars (약 2,000-6,000 단어)

---

## 6. 기존 문서와의 관계

- `chapter-progress.md` — 플레이어블 챕터 진도 (6/15)
- `PROGRESS_DASHBOARD.md` — 텍스트 분량 비교표 (현재: 4,080 EN chars)
- `case.json` → 메타데이터 추가 후 `case.json` 구조 변경
- `case_arc.json` — phases 확장 (generic → story-specific)

---

## 7. 열린 질문

1. **단편소설 분량 확장**: 기존 JSON excerpt를 직접 편집할 것인가, 아니면 별도 파일로 분리할 것인가?
2. **전투 심화도**: 현재 phases는 generic. story-specific combat을 phase에 매핑하는 방식?
3. **GN scene 재활용**: 확장된 narrative를 기존 8개 GN scene에 어떻게 배치할 것인가?
