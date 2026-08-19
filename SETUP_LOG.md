# Wet Run - Setup Log

## [2026-06-17] init | 프로젝트 환경 구축

### 작업 개요
Game/wet_run 경로에 로그라이크 게임 개발을 위한 문서 환경 구축.

### 컨셉
윌리엄 깁슨의 스프롤 3부작 세계관. 사이버스페이스에서 콘솔 카우보이로 플레이하는 로그라이크.

### 완료된 작업

#### 1. 디렉토리 구조
LLM Wiki 패턴을 게임 디자인에 맞게 변형:
- `raw/` - 원본 자료 (소설, 레퍼런스)
- `wiki/world/` - 세계관 위키
- `design/` - 활성 게임 디자인 스펙
- `testcases/` - 게임플레이 시나리오
- `decisions/` - 결정 기록 (ADR)
- `prototype/`, `src/`, `tests/`, `scripts/`, `config/` - 엔진 결정 후 채울 예정

#### 2. 메타 문서
- `README.md` - 프로젝트 개요
- `AGENTS.md` - AI 에이전트 가이드 (게임 전용)
- `index.md` - 위키 인덱스
- `log.md` - 활동 로그
- `ROADMAP.md` - 단계별 계획
- `SETUP_LOG.md` - 본 문서

#### 3. 템플릿
- `decisions/template.md` - ADR 템플릿
- `testcases/template.md` - 테스트 시나리오 템플릿

#### 4. 세계관 wiki (초안)
- `wiki/world/sprawl_universe.md` - 시간/공간/핵심 컨셉
- `wiki/world/cyberspace.md` - 매트릭스 정의
- `wiki/world/factions.md` - 주요 세력
- `wiki/world/glossary.md` - 용어 사전
- `wiki/world/style_guide.md` - 톤 가이드

#### 5. 디자인 문서 (초안)
- `design/pillars.md` - 디자인 기둥
- `design/core_loop.md` - 핵심 게임 루프
- `design/GDD.md` - GDD 골격
- `design/glossary.md` - 게임 용어

#### 6. 결정 기록
8개 핵심 결정 문서 작성 (모두 Draft 상태):
- 0001 엔진/프레임워크
- 0002 비주얼 스타일
- 0003 전투 시스템
- 0004 코드 아키텍처
- 0005 사이버스페이스 표현
- 0006 런 구조
- 0007 플랫폼 타겟
- 0008 진행 시스템

#### 7. 다음 단계
- `decisions/0001` 부터 사용자 결정
- 결정에 따라 Phase 1 (세계관 보강) 또는 Phase 2 (디자인 명세 확장) 또는 Phase 4 (코드 환경) 진행
