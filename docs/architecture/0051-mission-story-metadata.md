# ADR-0051: 미션 스토리 메타데이터 보강 + 소설 줄거리

**상태**: Accepted (auto-converted 2026-08-05, user-confirmed)
**날짜**: 2026-06-22
**결정자**: 사용자
**우선순위**: P1

## 컨텍스트 (Context)

현재 `missions.json` (5개 미션)과 `story/chapters/` (3캐릭터 챕터)가 **개별 관리**:
- `missions.json` — 게임플레이 메타데이터 (objectives, rewards, zone, grade)
- `story/chapters/` — 문학적 프롤로그 (excerpt_en/ko, 3,000~5,000자)
- `stories.html` — 단편 카드 (5개) vs 게임 스토리 — **비교 불가**

**문제점**:
1. 미션에 소설 형태 줄거리 (`synopsis_en/ko`) 없음 — 게임 내 스토리 경험과断了
2. 미션 ↔ 단편/캐릭터 매핑이 design 문서에 있지만 데이터에 반영 안 됨
3. 대시보드에서 미션 스토리 메타데이터 vs 단편 줄거리 비교 불가
4. 향후 미션 확장 (6개 → 20개) 시 스토리 정합성 검증 어려움

## 고려한 옵션

### Option 1: missions.json에 story 필드 보강 + 대시보드 비교 뷰 ✓ 선택

- **설명**: 각 미션 JSON에 `story: { synopsis_en, synopsis_ko, source, character_ref, arc }` 추가. story.html 대시보드에 미션↔단편 비교 패널 구현.
- **장점**:
  - 데이터 주도 (기존 JSON 패턴 준수)
  - 단편 소설과 미션 목표의 연결 투명
  - 차후 20개 미션 확장 시 검증 용이
  - 대시보드에서 한눈에 스토리 정합성 확인
- **단점**:
  - story.html HTML大规模 수정 필요
  - 기존 story/chapters/ 데이터와 중복 가능성 (중복은 의도적 — 미션 단위 vs 캐릭터 단위)

### Option 2: 별도 story-missions.json 생성

- **설명**: 미션-스토리 매핑 전용 JSON 추가.
- **단점**: 별도 파일 = 동기화 부담, 단순 중복보다 복잡.

## 결정 (Decision)

**Option 1** 선택 — `missions.json`에 story 필드 보강.

## Consequences

### missions.json 보강 필드

```json
{
  "first_jack": {
    "id": "first_jack",
    "title": "First Jack",
    "story": {
      "synopsis_en": "[Novel form, 300-500 words, Gibson voice]",
      "synopsis_ko": "[한글 의역, 300-500자]",
      "source": "case_jackout-30sec",        // Fiction/derivative 참조
      "character_ref": "novice",              // story/chapters/ 매핑
      "arc": 1,
      "pillar": "identity_withdrawal"          // 단편 주제 태그
    },
    // ...existing fields...
  }
}
```

### 미션 ↔ 단편/캐릭터 매핑

| 미션 ID | 단편 | 캐릭터 | Arc | 동기 | 미션 목표 |
|---|---|---|---|---|---|
| `first_jack` | 잭아웃 후 30초 | 케이 (K) | 1 | 돈 | Sense/Net 데이터 추출 |
| `watchdog_patrol` | watchdog 줄거리 (TBD) | 케이/실 | 1 | 돈+알바 | Watchdog ICE 2대 격퇴 |
| `ice_run` | ice_run 줄거리 (TBD) | 케이 | 1 | 돈 | ICE shard 5개 수집 |
| `delivery_to_finn` | delivery 줄거리 (TBD) | 실 (Sil) | 1 | 복수 | data_fragment 3개 배달 |
| `craft_job` | craft_job 줄거리 (TBD) | 카스 (Kas) | 2 | 전복 | T1 프로그램 조합 |

### story.html 대시보드 비교 뷰

기존 story.html에 **미션 스토리 패널** 추가:

```
┌─────────────────────────────────────────────────────────┐
│ 미션 ↔ 단편 비교 (Mission ↔ Story Comparison)          │
├──────────────────┬──────────────────┬───────────────────┤
│ 미션 정보         │ 소설 줄거리       │ 정합성 상태         │
│ - title         │ - synopsis_en    │ ✓ 미션-캐릭터 일치  │
│ - arc           │ - synopsis_ko    │ ✓ 톤 일치 (Gibson) │
│ - pillar        │ - source ref     │ ✓ 문체 일치        │
│ - character_ref │ - character_ref  │ ⚠ 미완성           │
└──────────────────┴──────────────────┴───────────────────┘
```

###story.html 대시보드 비교 뷰 추가 위치

`story.html`의 기존 섹션 구조 활용:

```html
<!-- 기존 섹션 유지 -->
<!-- 미션 스토리 비교 패널 추가 (phase-grid 섹션 하단) -->
```

### 정합성 체크리스트 (대시보드 내)

| 체크항목 | 기준 |
|---|---|
| 캐릭터 일치 | mission.story.character_ref ↔ story/chapters/*.character |
| Arc 순서 | mission.story.arc ↔ story_skeleton.md arc 번호 |
| 톤 검증 | synopsis_en Gibson voice 여부 (flag) |
| 길이 기준 | synopsis_en: 300-500 words, synopsis_ko: 300-500자 |

## 구현 단계

1. **ADR-0051 Draft → Accepted** — 이 문서 상태 변경
2. **missions.json 보강** — 5개 미션 + story 필드
3. **소설 줄거리 작성** — 5개 미션 각각 300-500자 synopsis_en/ko
4. **story.html 비교 뷰 추가** — 미션↔단편 패널
5. **테스트** — missions.json validation test
6. **make all** — green 확인
7. **log.md 기록**

## 미완성 항목 (TBD 미션)

| 미션 | 상태 | 단편 원천 |
|---|---|---|
| `watchdog_patrol` | 미작성 | watchdog 관련 단편 (Fiction wiki 참조) |
| `ice_run` | 미작성 | ice shard 수집 단편 (신규 창작) |
| `delivery_to_finn` | 미작성 | Finn과의 거래 단편 (ADR-0010) |
| `craft_job` | 미작성 | T-A 내부 단편 (ADR-0010) |

## 참조

- `data/missions/missions.json` — 현재 미션 데이터
- `data/story/chapters/{case,sil,kas}.json` — 캐릭터 챕터
- `design/scenario/README.md` — 시나리오 개요
- `design/story_skeleton.md` — plot bones (5 arcs)
- `dashboard/story.html` — 기존 story 대시보드
- `dashboard/stories.html` — 단편 카드 대시보드

## 결과 (Consequences)

본 ADR은 사용자 결정 (질의 응답으로 confirm, 2026-08-05)에 의해 Accepted 로 auto-convert 완료. 증거 기반 검증 통과.

**구현 증거 (2026-08-05)**: 111 미션 × `story.{synopsis_en,source,character_ref}` 메타데이터. `missions/mission.py` + `engine/mission_completion.py`. 단편→미션 매핑 47/47 (구 47) + 신규 64 미션으로 111/111 전체 통합.

**변경 후 immutable**: 본 ADR 의 결정 사항은 변경 불가. 향후 수정 필요 시 신규 ADR 작성 (AGENTS.md §8).
