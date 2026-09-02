# ADR-0041: 그래픽 노블 소설 콘텐츠 확장

**상태**: Accepted
**날짜**: 2026-06-20
**결정자**: 사용자
**우선순위**: P1

## 컨텍스트 (Context)

ADR-0032 (그래픽 노블 모드) 도입 후 사용자가 "프롤로그 문장 표현이 잘리는 느낌"이라고 피드백.
원인 분석:

- 80x50 화면에서 `render_scene`이 **3줄 dialogue box** 만 사용 (이전)
- 평균 dialogue 길이: **110자** (max 157자)
- 3줄 × 74 chars = 222 chars — 긴 문장은 잘림
- 결과: 깁슨 원문의 분위기 (긴 묘사, 페이지 호흡) 가 단절

해결: `render_scene`을 책 페이지 레이아웃으로 재설계 — **30줄 본문** (10× 확장), pagination,
챕터 헤딩 스타일 speaker.

**남은 문제**: 새 layout은 30줄을 지원하지만, **현재 씬은 평균 110자** (3줄) 만 사용.
소설 호흡을 살리려면 콘텐츠 자체를 확장해야 함.

## 고려한 옵션

### Option 1: 대화문 확장 (110자 → 300-500자) ✓ 선택

- **설명**: 각 dialogue를 **소설 paragraph 단위** 로 확장 (1-2문장 → 4-6문장).
  - 평균 dialogue: 110자 → 400자 (4×)
  - 씬당 3-4 dialogues → 1200-1600자 (페이지 2-3 매)
  - narration vs dialogue 구분 강화 (narrator는 시점 묘사, 캐릭터는 목소리)
  - 깁슨 톤 유지: cold, detached, cinematic, fragment 문장, sensory details
- **장점**:
  - 새 layout의 30줄을 자연스럽게 채움
  - 페이지 호흡 (2-3 pages/scene) → 진짜 소설 같은 읽기 경험
  - 캐릭터 voice / 세계관 깊이 강화
  - 기존 타이핑 효과 / pagination / chapter heading과 시너지
- **단점**:
  - 12 scenes × 평균 4 dialogues = 48 dialogues 재작성 (대규모 작업)
  - 씬 JSON 파일 12개 직접 수정 필요
  - 톤 일관성 유지 어려움 (AI가 쓰면 어색할 수 있음)
- **Pillar 정합**:
  - P1 (The Run): 영향 없음
  - P2 (The Matrix): 영향 없음
  - P3 (The Flatline): 영향 없음
  - P4 (The Build): 영향 없음
  - P5 (The Style): **강화** — 깁슨 스프롤 분위기 직접 보존

### Option 2: 챕터 헤더 / 페이지 장식 추가

- **설명**: 책처럼 CHAPTER X, 씬 전환 시 ASCII 오너먼트, 페이지 번호 등 타이포그래피 폴리시.
- **장점**: 시각적 개선, 구현 쉬움
- **단점**: 콘텐츠 자체는 여전히 짧음 — 근본 문제 미해결

### Option 3: 자키/배경 아트 업그레이드

- **설명**: 15개 ASCII 초상화 + 12개 배경을 더 시네마틱하게.
- **장점**: 시각적 몰입도 향상
- **단점**: 텍스트 호흡 문제는 그대로

### Option 4: 효과/사운드 추가

- **설명**: 페이드 효과, 타이핑 사운드, speaker별 다른 색상.
- **장점**: 다감각적 경험
- **단점**: 텍스트 길이 문제는 해결 못함

## 추천 (Recommendation)

**Option 1 — 대화문 확장**. 새 layout의 잠재력을 살리는 가장 직접적인 방법.
깁슨 톤 (cold, cinematic, fragment) 을 유지하면서도 페이지 호흡이 살아남.

## 사용자 결정 (Decision)

[x] Option 1 — 대화문 확장

## 결과 (Consequences)

### 긍정적

- **진짜 소설 같은 읽기 경험**: 페이지 넘기며 읽는 호흡
- **깁슨 세계관 깊이**: sensory details, 산업 이름 (Tessier-Ashpool, Maas, Sense/Net), 분위기
- **캐릭터 voice**: Case (jaded console cowboy), Marly (gallery curator / 데이터 사냥꾼),
  Kumiko (Loa priestess / heretic), narrator (cold camera eye)
- **페이지네이션 자연스러움**: 30줄 페이지 + 긴 텍스트 = 2-3 pages/scene 자동 발생
- **타이핑 효과 강화**: 한 페이지당 400자 × 30ms = 12초 — 긴 페이지일수록 효과 큼

### 부정적 / 위험

- **톤 일관성**: 12 씬 × 3-4 dialogues = 48 dialogues. AI 생성 시 어색한 톤 가능
  → 완화: 명확한 톤 가이드라인, 각 씬별 voice profile 명시
- **번역 부담**: 영어 확장 시 한글 자막도 동기화 필요 (별도 작업)
- **테스트 영향**: dialogue 길이 변화로 기존 테스트 (특히 pagination) 영향

## 영향 받는 항목

- `prototype/data/scenes/{case,sil,kas}/*.json` — 12 씬 dialogue 확장
- `prototype/tests/unit/test_graphic_novel_view.py` — dialogue 길이 assertion 업데이트
- `prototype/tests/unit/test_graphic_novel_novel_layout.py` — pagination 테스트 강화
- `prototype/scripts/graphic_novel.py` — duration_ms 조정 (긴 텍스트 = 더 긴 재생)
- `design/scenario/graphic-novel.md` — 톤 가이드라인 추가
- `log.md` — 진행 기록

## 관련 결정

- ADR-0032 (그래픽 노블 모드) — 기반
- ADR-0010 (i18n) — 한글 자막 동기화
- (polish session 2026-06-20) — 소설 페이지 layout 도입

## 변경 이력

- 2026-06-20: Draft 작성 (Option 1 채택)
- 2026-06-20: Accepted — 12 씬 dialogue 확장 완료 (4188 → 16862 chars, 4×).
  - Case (4): chattos, jackin, jackout, finn
  - Sil (4): louisiana, mask, payroll, broadcast
  - Kas (4): manarase, sally, declaration, wheel
  - 모든 dialogue 250-700자, 씬당 1000-2500자
  - 한글 자막 동기화 (38/38 dialogue), KO/EN ratio 0.4-1.8
  - 깁슨 어휘: Tessier-Ashpool, Sense/Net, Ono-Sendai, Chiba, loa
  - 디자인 가이드라인 `design/scenario/graphic-novel.md §10` 추가
  - 테스트 76개 추가 (`test_graphic_novel_content_quality.py`)
  - **Total tests**: 2092 → **2196** (+104 across 0041 + 0042)