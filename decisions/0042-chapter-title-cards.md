# ADR-0042: 챕터 타이틀 카드 / 씬 전환 효과

**상태**: Accepted
**날짜**: 2026-06-20
**결정자**: 사용자
**우선순위**: P2

## 컨텍스트 (Context)

ADR-0041 (씬 콘텐츠 확장) 후, **긴 페이지** 가 가능해졌지만 **씬과 씬 사이 전환이 즉시 잘림**.
소설/영화처럼 챕터 구분 + 부드러운 페이드인 효과 필요.

이전 흐름: 씬 A → (즉시) → 씬 B
요구 흐름: 씬 A → 챕터 카드 → (페이드인) → 씬 B

## 고려한 옵션

### Option 1: 챕터 타이틀 카드 + fade transition ✓ 선택

- **설명**:
  - 씬 진입 전 `render_chapter_card()` 표시 (~2.5초)
  - 책처럼 `CHAPTER I` 로마 숫자 + 씬 제목 + 캐릭터 라벨 + 씬 번호
  - ASCII 오너먼트: `═` border, `─` divider, `·` 장식
  - **마지막 씬 → "FINALE"** 표시
  - **Fade-in transition**: 600ms 동안 `═` → `▓` → `▒` 단계로 어두워짐
- **장점**:
  - 책/영화 같은 시각적 호흡
  - 12 씬을 독립 챕터로 인식
  - narrator 시점 구분 강화
- **단점**:
  - 전체 재생 시간 +2.5초 × 12 = 30초 늘어남
  - 구현 복잡도 ↑
- **Pillar 정합**:
  - P5 (The Style): **강화** — 책 페이지 메타포 직접 구현

### Option 2: fade-out 만 (카드 없음)

- **설명**: 씬 종료 시 fade-out → 빈 화면 → 다음 씬 fade-in
- **장점**: 구현 간단, 카드 디자인 작업 없음
- **단점**: 씬 제목 / 캐릭터 정보 안 보임 — 챕터 구분 약함

### Option 3: 비주얼 노벨 방식 (transition image)

- **설명**: 씬 사이 fullscreen ASCII 이미지 (예: "..." fade)
- **장점**: 더 시네마틱
- **단점**: 너무 복잡, 어색할 수 있음

## 추천 (Recommendation)

**Option 1 — 챕터 카드 + fade**. 책의 자연스러운 호흡. Phase state machine으로 통합.

## 사용자 결정 (Decision)

[x] Option 1 — 챕터 타이틀 카드 + fade transition

## 결과 (Consequences)

### 긍정적
- 진짜 소설 같은 챕터 구분 (CHAPTER I, II, ..., XII)
- 12 씬이 독립 챕터로 인식되어 navigation 명확
- Fade-in으로 부드러운 시각 전환
- 다국어 (영문/한글) 지원
- 로마 숫자 헬퍼 (`_to_roman`, 1-12 → I-XII)
- 마지막 씬 → "FINALE" 표시 (이야기 끝 느낌)

### 부정적 / 위험
- 전체 재생 시간 12 챕터 × 2.5초 = +30초
- 카드 스킵 옵션 (`--no-cards`) 제공으로 완화

## 영향 받는 항목
- `prototype/src/wet_run/engine/graphic_novel_view.py` — `render_chapter_card()`, `render_blank_transition()`, `_to_roman()`, `_character_label()`
- `prototype/scripts/graphic_novel.py` — Phase state machine, `--no-cards`, `--card-ms` 옵션
- `prototype/tests/unit/test_graphic_novel_chapter_cards.py` — 신규 테스트 37개

## 관련 결정
- ADR-0041 (씬 콘텐츠 확장) — 기반
- ADR-0032 (그래픽 노블 모드)

## 변경 이력

- 2026-06-20: Draft 작성 (Option 1 채택)
- 2026-06-20: Accepted — `render_chapter_card()` + fade transition 구현 완료
  - 로마 숫자 I-XII, ASCII 오너먼트 (═ ─ ·)
  - 600ms fade-in (═ → ▓ → ▒)
  - Phase state machine (chapter_card → scene)
  - 테스트 37개 추가 (`test_graphic_novel_chapter_cards.py`)
  - **Total tests**: 2196 → 2233 (+37)