# ADR-0001: 엔진/프레임워크

**상태**: Accepted
**날짜**: 2026-06-17
**결정자**: 사용자
**우선순위**: P0

## 컨텍스트

게임 코드 작성을 위한 엔진/프레임워크를 선택해야 한다. 결정은 다음에 영향을 미친다:
- 개발 속도 (iteration speed)
- 비주얼 표현 (ASCII / 타일 / 3D)
- 배포 형태
- 빌드 시스템
- AI 에이전트 지원 (현재 사용자 환경은 macOS)

## 고려한 옵션

### Option 1: libtcod + Python (python-tcod) — 추천

- **설명**: 클래식 로그라이크의 표준 라이브러리. 터미널 / SDL2 기반 렌더링, FOV, pathfinding, 절차적 생성을 위한 도구.
- **장점**:
  - 가장 빠른 프로토타이핑 (1-2 세션에 기본 셋업)
  - ASCII / 타일 둘 다 지원
  - Python — 광범위한 생태계, AI 에이전트가 가장 잘 다룸
  - Roguelike 커뮤니티의 표준
  - 절차적 생성 라이브러리 풍부 (tcod 자체에 내장)
  - macOS 네이티브 지원
  - Pillar 2 (The Matrix): ASCII + 네온이 매트릭스 미학에 정확히 부합
- **단점**:
  - 그래픽 표현 한계 (사실적 3D 불가)
  - "와이어프레임 3D" 같은 표현은 어려움
  - 매트릭스의 "데이터 흐르는" 이펙트는 직접 구현 필요
- **Pillar 정합**:
  - P1 (The Run): 매크로/미시 루프 모두 표현 용이
  - P2 (The Matrix): ASCII가 매트릭스의 "추상화된 데이터"와 정확히 일치
  - P3 (The Flatline): "you flatline" 정적 화면 표현 쉬움
  - P5 (The Style): 거친 톤 유지 용이

### Option 2: Godot 4 (GDScript 또는 C#)

- **설명**: 오픈소스 게임 엔진. 2D/3D 둘 다 가능. 무료.
- **장점**:
  - 비주얼 표현 풍부 (shader, particles, 3D)
  - 내장 에디터
  - 픽셀 아트 / 2D에 강함
  - 무료 오픈소스
  - 크로스플랫폼 빌드 쉬움
- **단점**:
  - 셋업 시간 더 걸림 (1-2 세션)
  - AI 에이전트 지원이 Python보다 약함
  - 매트릭스 "데이터 흐르는" 표현에 적합하나, ASCII의 거친 느낌은 잃을 수 있음
  - Godot의 GDScript / C# 컨벤션 학습 필요
- **Pillar 정합**:
  - P2 (The Matrix): 2D 픽셀 / 3D 와이어프레임 가능
  - P5 (The Style): 시각적으로 더 화려할 수 있지만 톤 통제 필요

### Option 3: Unity (C#)

- **설명**: 가장 인기 있는 게임 엔진. 2D/3D 둘 다 가능.
- **장점**:
  - 가장 큰 생태계
  - 모든 플랫폼
  - 비주얼 가능
- **단점**:
  - 가장 무거움
  - 라이선스 복잡 (개인용은 무료, 수익 발생 시 유료)
  - 로그라이크에 과함
  - AI 에이전트 지원 약함
  - macOS에서 Unity Hub 별도 설치
- **Pillar 정합**:
  - P2 (The Matrix): 모든 표현 가능
  - P5 (The Style): 톤 통제는 가능하나, Unity의 기본 미학 회피 필요

### Option 4: Bevy (Rust)

- **설명**: ECS 기반 Rust 게임 엔진.
- **장점**:
  - 매우 빠름
  - ECS가 게임 데이터에 적합
  - 무료 오픈소스
- **단점**:
  - 러닝 커브 (Rust 학습 + Bevy API)
  - AI 에이전트가 잘 다루지 않음
  - 셋업 복잡
  - 로그라이크에 over-engineering 위험
  - macOS 셋업 가능하나 디버깅 어려움
- **Pillar 정합**:
  - 모든 Pillar에서 가능하나, 개발 속도가 느림

### Option 5: 웹 (TypeScript + Canvas/WebGL)

- **설명**: 웹 브라우저 게임 (HTML5).
- **장점**:
  - 별도 설치 불필요
  - 데모 배포 쉬움 (URL)
  - 비주얼 가능
- **단점**:
  - 게임 디자인에 어색한 추상화
  - 매트릭스 톤을 ASCII로 표현하면 좋으나, 웹에서는 폰트/렌더링 통제 어려움
  - AI 에이전트가 잘 다루지 않음
  - 게임패드 / 키맵 처리 복잡
  - 오프라인 플레이 어려움
- **Pillar 정합**:
  - P1 (The Run): 가능
  - P5 (The Style): 톤 통제 가능하나 추가 노력 필요

### Option 6: 커스텀 (Python + curses / pygame / C + SDL2)

- **설명**: 직접 작성. curses (터미널) 또는 pygame (2D) 또는 SDL2 (저수준).
- **장점**:
  - 완전한 통제
  - 의존성 최소
- **단점**:
  - 셋업부터 모든 것 직접
  - FOV, pathfinding 등 직접 구현
  - 개발 속도 매우 느림
- **Pillar 정합**:
  - 가능하나, 권장 안 함

## 추천

**Option 1: libtcod + Python**

근거:
1. 사이버펑크 + 로그라이크의 정통 조합
2. 가장 빠르게 시작 가능 (1-2 세션에 vertical slice)
3. AI 에이전트와 잘 맞음
4. 1인 개발에 적합
5. Pillar 2 (The Matrix) 미학에 정확히 부합
6. 매트릭스의 "ASCII + 형광 네온"이 깁슨 톤과 일치

**대안**: Option 2 (Godot) — 비주얼 표현이 더 화려해야 한다면.

## 사용자 결정

[x] **Option 1: libtcod + Python** (2026-06-17)

## 결과 (Consequences)

### 채택된 기술 스택
- **python-tcod** (>= 16.0): 렌더링, FOV, pathfinding, 절차적 생성
- **Python 3.11+**: 메인 언어
- **pyproject.toml**: 의존성 관리 (Poetry 또는 pip + requirements.txt)
- **pytest**: 단위 테스트
- **ruff**: 린트 / 포맷터 (ruff format + ruff check)
- **mypy**: 정적 타입 체크
- **GitHub Actions**: CI (macOS + Windows 빌드 + 테스트)

### 디렉토리 구조 (Phase 4에서 확정)
```
prototype/ (또는 src/)
├── wet_run/
│   ├── __init__.py
│   ├── __main__.py
│   ├── engine/        # tcod 관련 (window, render, input)
│   ├── matrix/        # 사이버스페이스 (nodes, ICE, programs)
│   ├── jobs/          # 의뢰 (job board, missions, fixer)
│   ├── entities/      # 플레이어, 적 (ECS-lite)
│   ├── data/          # 정적 데이터 (decks, programs, ICE types, jobs)
│   ├── procgen/       # 절차적 생성
│   └── ui/            # UI 위젯
├── tests/
│   ├── unit/
│   └── integration/
├── data/              # JSON/YAML 데이터 파일
├── scripts/           # 유틸리티
├── pyproject.toml
├── README.md
└── .github/workflows/ci.yml
```

### 강제되는 결정
- ADR-0002 (스타일): Pure ASCII와 자연스러움
- ADR-0004 (아키텍처): Python 친화적 — ECS-lite 또는 데이터 주도
- ADR-0007 (플랫폼): macOS + Windows 네이티브 빌드

### 향후 결정
- 코딩 스타일: PEP 8 + ruff 기본 (AGENTS.md에 기록)
- 의존성 잠금: poetry.lock 또는 requirements.txt
- 데이터 포맷: JSON (가장 단순) 또는 YAML (가독성)

## 영향 받는 항목

- ADR-0002 (스타일): Pure ASCII와 일치
- ADR-0004 (아키텍처): Option 5 (ECS-lite + 데이터 주도) 권장
- ADR-0007 (플랫폼): macOS + Windows

## 관련 결정

- ADR-0002, ADR-0004, ADR-0007 (모두 Accepted)

## 변경 이력

- 2026-06-17: Draft 작성
- 2026-06-17: Accepted (Option 1: libtcod + Python)
