# 콘텐츠 확장 계획 — 플레이 타임 증가

> **작성일**: 2026-06-25
> **현재 상태**: 15 missions, 17 stories, ~3.3 hours total play time
> **목표**: 30+ missions, 30+ stories, 10+ hours total play time

---

## 1. 현재 현황 분석

### 1.1 문제점

| 항목 | 현재 | 목표 | Gap |
|------|------|------|-----|
| 총 플레이 타임 | 3.3 hours | 10+ hours | 6.7 hours |
| 미션 수 | 15 | 30+ | 15 |
| 단편소설 | 17 | 30+ | 13 |
| Arc당 미션 수 | 1-4 | 5-7 | 2-3 |
| 미션당 Stage 수 | 4-6 | 6-10 | 2-4 |

### 1.2 현재 Stage Flow (한계)

```
PENDING → MEET_NPC → EXTRACT_DATA → DEFEAT_ICE → JACK_OUT → REWARD → COMPLETE
```

**문제**: Stage 종류가 적어 반복감이 있음

---

## 2. 확장 계획

### 2.1 Stage 확장 (4→10 stages)

현재 9개 Stage를 다음과 같이 세분화:

```
PENDING → BRIEFING → TRAVEL → MEET_NPC → EXTRACT_DATA → BYPASS_SECURITY → DEFEAT_ICE → JACK_OUT → REWARD → DEBRIEF → COMPLETE
```

**새 Stage 추가**:
1. `BRIEFING` — NPC가 미션 세부사항 제공
2. `TRAVEL` — 매트릭스 진입 전 이동/준비
3. `BYPASS_SECURITY` — 보안 시스템 우회 (미니게임/대화)

### 2.2 Arc 확장 (5→7 arcs)

| Arc | 현재 미션 | 목표 미션 | 테마 |
|-----|----------|----------|------|
| 1 | 4 | 7 | 튜토리얼, 첫 잭인 |
| 2 | 4 | 7 | 스프롤 탐험 |
| 3 | 3 | 7 | 테시에-애시풀对抗 |
| 4 | 3 | 7 | 로아 네트워크 |
| 5 | 1 | 3 | 피날레 |
| 6 | 0 | 4 | Afternmath (엔딩 후) |
| 7 | 0 | 3 | 뉴 게임+ |

### 2.3 미션당 스토리 확장

**현재**: 1 short story per mission
**목표**: 2-3 short stories per mission (전편/후편/파생)

**예시**:
```
first_jack/
├── 2026-06-23_first_jack.md (본편)
├── 2026-06-23_first_jack_aftermath.md (후편)
└── 2026-06-23_first_jack_variant.md (변형)
```

---

## 3. 단편소설 메타데이터 확장

### 3.1 현재 Frontmatter

```yaml
title: "First Trace"
original_title: "오리지널"
author: "..."
status: final
plot_summary: "..."
```

### 3.2 확장 Frontmatter

```yaml
title: "First Trace"
original_title: "..."
author: "..."
status: final

# 메타데이터 확장
grade_level: 2
difficulty: easy
estimated_minutes: 15

# 게임 연동
mission_id: first_trace
arc: 2
chapter: 1

# 스토리 메타
pov: case
setting: chiba_city
factions: [finn, tessier-ashpool]
tags: [tutorial, first-job, finn-intro]

# 플레이타임 조절
combat_encounters: 1
dialogue_nodes: 3
exploration_nodes: 5
```

---

## 4. 단계별 실행 계획

### Phase A: 미션 확장 (2주)

**목표**: 15 → 25 missions

| Week | 작업 | 산출물 |
|------|------|--------|
| 1 | Arc 1, 2 미션 3개씩 추가 | +6 missions |
| 1 | Arc 3, 4 미션 2개씩 추가 | +4 missions |
| 2 | 미션별 스토리 파일 2개씩 생성 | +20 stories |

### Phase B: Stage 세분화 (1주)

**목표**: 9 → 12 stages

| Stage | 현재 | 신규 | 설명 |
|-------|------|------|------|
| BRIEFING | 없음 | 신규 | NPC 브리핑 전용 |
| TRAVEL | 없음 | 신규 | 진입 애니메이션 |
| BYPASS_SECURITY | 없음 | 신규 | 보안 우회 미니게임 |

### Phase C: 스토리 심화 (2주)

**목표**: 17 → 35 stories

- 각 미션에 2-3개 스토리 파일
- 캐릭터별 엔딩 스토리 추가
- Hinterland 스토리 추가

### Phase D: 밸런스 조정 (1주)

**목표**: 플레이타임 검증

- 미션 난이도 재조정
- 보상 곡선 재계산
- 플레이타임 측정

---

## 5. 검증 체크리스트

### 5.1 미션 검증

```bash
# 미션 수 검증
python3 -c "
import json
with open('design/systems/stage_structure.json') as f:
    ss = json.load(f)
print(f'Missions: {len(ss[\"missions\"])}')
print(f'Total play time: {sum(m[\"estimated_minutes\"] for m in ss[\"missions\"])} min')
"

# 스토리 ↔ 미션 매핑 검증
ls Fiction/derivative/sprawl-trilogy/short-stories/*.md | wc -l
```

### 5.2 목표 지표

| 지표 | 현재 | Phase A 후 | Phase B+C 후 | 최종 목표 |
|------|------|------------|--------------|----------|
| 미션 수 | 15 | 25 | 30+ | 35 |
| 스토리 수 | 17 | 30 | 35 | 40 |
| 총 플레이타임 | 3.3h | 5h | 8h | 10h+ |
| Arc 수 | 5 | 5 | 7 | 7 |

---

## 6. 구현 우선순위

### P0 (즉시)

1. **Arc 1 미션 3개 추가** (tutorial 확장)
   - `tutorial_maze` — 매트릭스 처음 탐험
   - `first_contact` — 다른 NPC 첫 만남
   - `data_retrieval` — 간단한 데이터 회수

2. **Stage BRIEFING 추가**
   - NPC가 미션 목표 상세 설명
   - 선택지 제공 (용이/보통/어려움)

### P1 (1주 내)

3. **Arc 2 미션 3개 추가**
4. **스토리 파일命名 규칙 통일**
5. **Frontmatter 메타데이터 확장**

### P2 (2주 내)

6. **Arc 3, 4 미션 각 2개씩 추가**
7. **Stage TRAVEL, BYPASS_SECURITY 추가**
8. **각 미션에 2번째 스토리 추가**

### P3 (4주 내)

9. **Arc 5, 6, 7 추가**
10. **엔딩 스토리 확장**
11. **뉴 게임+ 콘텐츠**

---

## 7. 파일 구조 (확장 후)

```
Fiction/derivative/sprawl-trilogy/short-stories/
├── first_jack/
│   ├── 2026-06-23_first_jack.md
│   ├── 2026-06-25_first_jack_aftermath.md
│   └── metadata.yaml
├── first_trace/
│   ├── 2026-06-23_first_trace.md
│   ├── 2026-06-26_first_trace_foreshadow.md
│   └── metadata.yaml
└── ...

design/systems/
└── stage_structure.json (30+ missions)

design/missions/
├── arc1_tutorial.yaml
├── arc2_sprawl.yaml
├── arc3_ta_conflict.yaml
├── arc4_loa_network.yaml
├── arc5_finale.yaml
├── arc6_aftermath.yaml
└── arc7_newgame_plus.yaml
```

---

## 8. 리스크 및 대응

| 리스크 | 확률 | 대응 |
|--------|------|------|
| 스토리 작성 병목 | 높음 | 템플릿화 + LLM 활용 |
| 밸런스 붕괴 | 중간 | 자동 테스트 + 수동 검증 |
| 파일 관리 복잡화 | 중간 |.metadata.yaml 중앙化管理 |

---

## 9. 다음 단계

### 즉시 실행 가능 작업

1. **Arc 1용 3개 미션 스토리 작성** (600-800자 x 2 = 1200-1600자)
2. **Stage BRIEFING 스펙 작성** (ADR 신규)
3. **metadata.yaml 템플릿 작성**

### 검토 요청 사항

1. **미션당 스토리 수**: 2개로 할지 3개로 할지?
2. **새 Arc 테마**: Arc 6, 7 구체적 콘셉트?
3. **플레이타임 목표**: 10시간이妥当한지?
