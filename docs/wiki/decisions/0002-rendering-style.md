# ADR-0002: 비주얼 스타일

**상태**: Accepted
**날짜**: 2026-06-17
**결정자**: 사용자
**우선순위**: P0

## 컨텍스트

게임의 비주얼 표현을 결정해야 한다. 결정은 다음에 영향을 미친다:
- 엔진 선택 (ADR-0001)
- 아트 에셋 작업량
- 매트릭스 톤 (Pillar 2, 5)
- 개발자 / 플레이어 진입장벽

## 고려한 옵션

### Option 1: Pure ASCII

- **설명**: 글자 / 기호로 모든 것을 표현. 컬러로 형광 효과.
- **장점**:
  - 매트릭스의 "추상화된 데이터"와 정확히 일치
  - 깁슨 미학 ("lines of light ranged in the nonspace of the mind")
  - 자산 작업 0
  - 절차적 생성이 가장 자연스러움
  - 1인 개발에 최적
  - "the matrix has its roots in primitive arcade games"
- **단점**:
  - 시각적 다양성 제한
  - 일부 플레이어에게 진입장벽
  - 애니메이션 표현 어려움
- **Pillar 정합**:
  - P2 (The Matrix): ⭐⭐⭐⭐⭐ 정확히 일치
  - P5 (The Style): ⭐⭐⭐⭐⭐ 거친 톤 유지

### Option 2: 타일 (픽셀 아트)

- **설명**: 16x16 또는 32x32 픽셀 아트 타일.
- **장점**:
  - Cogmind / Caves of Qud 스타일
  - 시각적 명확성
  - ASCII보다 덜 진입장벽
- **단점**:
  - 자산 작업 필요
  - 매트릭스의 "추상" 느낌 일부 손실
  - 깁슨 톤 회피 가능성 ("귀여운" 픽셀 아트)
- **Pillar 정합**:
  - P2 (The Matrix): ⭐⭐⭐⭐ 가능
  - P5 (The Style): ⭐⭐⭐ 톤 통제 필요

### Option 3: 하이브리드 (ASCII + 효과)

- **설명**: 기본은 ASCII, 일부 요소(파티클, 발광)는 이펙트.
- **장점**:
  - ASCII의 거친 느낌 + 시각 효과
  - 매트릭스의 "데이터 흐름" 표현 가능
- **단점**:
  - 구현 복잡
  - 톤 통제 어려움
- **Pillar 정합**:
  - P2 (The Matrix): ⭐⭐⭐⭐⭐
  - P5 (The Style): ⭐⭐⭐⭐

### Option 4: 벡터 / 와이어프레임 (3D)

- **설명**: 3D 벡터 그래픽, 와이어프레임 + 형광.
- **장점**:
  - "깁슨의 매트릭스" 시각적 묘사와 가장 가까움 (3D 기하)
  - 시각적으로 강렬
- **단점**:
  - 엔진이 3D 지원 필요 (Godot / Unity)
  - 자산 / 셰이더 작업 많음
  - ASCII의 거친 느낌 손실 가능
  - 1인 개발 부담 큼
- **Pillar 정합**:
  - P2 (The Matrix): ⭐⭐⭐⭐⭐ (시각적으로 가장 정확)
  - P5 (The Style): ⭐⭐⭐ 톤 통제 어려움

### Option 5: 미니멀 UI + 단색

- **설명**: 검은 배경 + 형광 색, 기하학적 도형, 텍스트 위주.
- **장점**:
  - 아트 작업 최소
  - 매트릭스 미학에 부합
  - 절차적 생성과 자연스러움
- **단점**:
  - "게임" 느낌 적음
  - 플레이어 매력 감소
- **Pillar 정합**:
  - P2 (The Matrix): ⭐⭐⭐⭐
  - P5 (The Style): ⭐⭐⭐⭐

## 추천

**Option 1: Pure ASCII** (1인 개발, 깁슨 톤 추구 시)
**Option 3: 하이브리드** (비주얼 약간 추가, 매트릭스 효과)

조건:
- 0001에서 Godot을 선택하면 Option 3 또는 4가 자연스러움
- 0001에서 libtcod를 선택하면 Option 1이 자연스러움

## 사용자 결정

[x] **Option 1: Pure ASCII** (2026-06-17)
[ ] **Option 2 보강**: ASCII Portrait 시스템 추가 (ADR-0011, 2026-06-17)

## 결과 (Consequences)

### 비주얼 가이드
- **폰트**: monospace, 8x16 또는 9x16
- **컬러 팔레트**:
  - 배경: 검은색 (`#000000`)
  - 데이터 / 라우터: 시안 (`#00FFFF`)
  - ICE / 위험: 마젠타 / 빨강 (`#FF00FF`, `#FF0040`)
  - 알람 / 경계: 노랑 (`#FFFF00`)
  - 텍스트: 흰색 / 연한 회색
  - 형광 그린 (선택적): `#00FF00`
- **효과**: 깜빡임, 색 반전, 컬러 시프트 (시간 / 알람 레벨에 따라)
- **아이콘**: Unicode / ASCII (▲▼◀▶▶♠♣◆●○◎◇◆□■△▽)
- **인물 / 객체 표현**: ASCII Portrait 시스템 (ADR-0011) — 데이터 파일의 ASCII / Unicode 기호로 시각 식별

### ASCII Portrait 시스템 (ADR-0011)

Pure ASCII 안에서 인물과 객체를 시각적으로 식별하는 시스템.

- **형식**: 5-7자의 ASCII / Unicode 기호 + 색상
- **예시**: 플레이어 `◉P◉`, Dixie `◊D◊`, Finn `♠F♠`, ICE `▲ICE▲`, Black ICE `█ICE█`
- **제약**: cyberspace 안의 존재에게만 — meatspace 인물은 직접 묘사 X (Pillar 2)
- **데이터**: `data/portraits.json`
- **상세**: `decisions/0011-ascii-portraits.md`, `design/systems/ascii-portraits.md`

### Pillar 정합
- P2 (The Matrix): "lines of light ranged in the nonspace of the mind" — ASCII가 정확히 일치. ASCII portrait는 cyberspace 안의 표현으로 강화.
- P5 (The Style): 거친 톤, C64 / amber monitor 분위기. 애니메 X, ASCII만.

### 구현 영향
- python-tcod의 `tcod.console` 사용
- 콘솔 레이어 (root + map + UI)
- 색상은 `tcod.constants` 또는 RGB 직접
- ASCII Portrait 렌더링: `tcod.console.print`로 위치 지정 + 색상

### 향후 결정
- 구체적 폰트 (monospace TTF)
- 컬러 테마 (밝은 배경 / 어두운 배경 / 컬러 블라인드 옵션)
- Portrait 애니메이션 (깜빡임 등)

## 영향 받는 항목

- ADR-0005 (사이버스페이스 표현): ASCII로 노드 그래프 표현
- `wiki/world/style_guide.md`: 비주얼 섹션 확정 필요

## 관련 결정

- ADR-0001 (Accepted), ADR-0005 (Pending)

## 변경 이력

- 2026-06-17: Draft 작성
- 2026-06-17: Accepted (Option 1: Pure ASCII)
