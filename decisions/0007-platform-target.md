# ADR-0007: 플랫폼 타겟

**상태**: Accepted
**날짜**: 2026-06-17
**결정자**: 사용자
**우선순위**: P0

## 컨텍스트

게임을 어떤 플랫폼에 출시할지 결정해야 한다. 결정은 다음에 영향을 미친다:
- 엔진 선택 (ADR-0001)
- 빌드 시스템
- 입력 방식 (키보드 / 마우스 / 게임패드)
- 배포 형태
- 성능 요구사항

## 고려한 옵션

### Option 1: macOS + Windows 데스크탑

- **설명**: macOS와 Windows 네이티브 데스크탑 앱.
- **장점**:
  - 로그라이크의 표준 플랫폼
  - 키보드 입력 최적
  - 터미널 / SDL2 활용
  - macOS 사용자 (개발자 본인) 우선
- **단점**:
  - 다른 플랫폼 사용자 제외
  - 크로스 빌드 복잡

### Option 2: 크로스 플랫폼 데스크탑 (Mac / Windows / Linux)

- **설명**: 모든 주요 데스크탑 OS 지원.
- **장점**:
  - 더 많은 사용자
  - 오픈소스 게임에 적합
- **단점**:
  - Linux 빌드 테스트 필요
  - 패키지 의존성 관리

### Option 3: 웹 (HTML5 / WebGL)

- **설명**: 브라우저에서 플레이. 별도 설치 불필요.
- **장점**:
  - 데모 / 프로토타입 공유 쉬움 (URL)
  - 설치 마찰 없음
  - 데스크탑 / 모바일 모두 가능
- **단점**:
  - 매트릭스 톤의 ASCII가 웹에서 폰트 의존
  - 오프라인 플레이 어려움
  - 게임패드 / 키맵 처리 복잡
  - 성능 한계

### Option 4: 모바일 (iOS / Android)

- **설명**: 터치 기반 모바일.
- **장점**:
  - 가장 많은 잠재 사용자
- **단점**:
  - Pillar 3 (The Flatline)과 충돌 (모바일은 F2P 경향)
  - 비-기둥 활성화 위험
  - 로그라이크는 모바일에 어색
  - 터치 입력이 턴 기반 전투와 맞지 않음

### Option 5: 단일 플랫폼 (macOS only)

- **설명**: macOS 전용.
- **장점**:
  - 가장 단순
  - 개발자 환경 그대로
- **단점**:
  - 다른 플랫폼 사용자 제외

## 추천

**Option 1: macOS + Windows** (표준, 권장)
**Option 2: 크로스 플랫폼 데스크탑** (오픈소스 의향이 있다면)

근거:
- 로그라이크는 데스크탑 게임
- 모바일은 Pillar 3과 충돌 (F2P 위험)
- 웹은 매트릭스 톤의 ASCII와 거리
- macOS + Windows가 가장 표준

**개발자 우선순위**: macOS (개발자 환경) → Windows (가장 많은 잠재 사용자) → Linux (옵션)

## 사용자 결정

[x] **Option 1: macOS + Windows** (2026-06-17)

## 결과 (Consequences)

### 빌드 타겟
- **macOS**: 네이티브 (arm64 + x86_64, universal2)
- **Windows**: 네이티브 (x86_64)
- **분배**: PyInstaller 또는 Nuitka로 단일 실행 파일
  - 또는 `python -m wet_run` (Python 설치 가정)
  - 결정 보류 (Poetry + pipx 또는 PyInstaller 중)

### CI / CD
- GitHub Actions: macOS + Windows 매트릭스
- PR마다: lint + test + build
- 릴리즈: macOS dmg + Windows exe (옵션)

### 입력
- **주 입력**: 키보드 (vi / 화살표 / WASD)
- **보조**: 마우스 (옵션)
- **게임패드**: 미지원 (Phase 7+)

### 성능
- python-tcod은 C 백엔드, 60fps 가능
- 1인 개발 규모, 성능 이슈 없음 예상

### 강제되는 결정
- 모바일 / 웹은 의도적으로 회피
- 비-기둥 (F2P, mobile) 활성화 위험 차단

### 향후 결정
- 정확한 빌드 도구 (PyInstaller vs Nuitka vs pipx)
- 코드 사이닝 (macOS notarization, Windows signing)

## 영향 받는 항목

- ADR-0001 (엔진): libtcod + Python은 macOS + Windows 모두 네이티브 지원
- 빌드 시스템 (Phase 4)
- CI / CD (GitHub Actions)

## 관련 결정

- ADR-0001 (Accepted)

## 변경 이력

- 2026-06-17: Draft 작성
- 2026-06-17: Accepted (Option 1: macOS + Windows)
