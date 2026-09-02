# Wet Run

사이버펑크 해킹 로그라이크 게임

## 개요

윌리엄 깁슨의 스프롤 3부작 세계관을 기반으로 한 로그라이크 게임.
Python 프로토타입에서 TypeScript Web으로 완전 마이그레이션 완료.

플레이어는 **콘솔 카우보이**가 되어 사이버스페이스에 진입, ICE를 뚫고 데이터를 탈취하며 임무를 수행한다.

## 기술 스택

- **Frontend**: TypeScript, Canvas2D
- **Build**: Vite
- **Test**: Vitest (997 tests)
- **PWA**: 서비스워커 (오프라인 플레이 지원)

## 빌드 및 실행

```bash
cd web
npm install
npm run dev      # 개발 서버
npm run build    # 프로덕션 빌드
npm test         # 테스트 실행
```

## 프로젝트 구조

```
wet_run/
├── prototype/              # Python 프로토타입 (원본)
├── web/                    # TypeScript Web (메인 개발)
│   ├── src/
│   │   ├── core/           # 게임 로직
│   │   ├── data/           # JSON 데이터
│   │   └── renderer/       # 캔버스 렌더링
│   ├── tests/              # 47개 테스트 파일
│   └── public/             # PWA 매니페스트
├── docs/                   # 문서
│   ├── design/             # 설계 문서
│   ├── architecture/       # 아키텍처 (ADR)
│   ├── sessions/           # 세션 기록
│   └── playtest/           # 플레이테스트
├── data/                   # 데이터 자원
├── scripts/                # 빌드/배포 스크립트
├── README.md               # 프로젝트 개요
├── CHANGELOG.md            # 변경기록
└── MIGRATION.md            # 마이그레이션 기록
```

## 문서

- [마이그레이션 기록](MIGRATION.md) — 전체 마이그레이션 과정
- [변경기록](CHANGELOG.md) — 버전별 변경사항
- [로드맵](ROADMAP.md) — 단계별 계획
- [설계 문서](docs/design/) — 게임 설계 명세
- [아키텍처 결정](docs/architecture/) — ADR 기록
- [세션 기록](docs/sessions/) — 개발 세션별 요약
- [플레이테스트](docs/playtest/) — 플레이테스트 가이드

## 핵심 기능

- **전투 시스템**: 13개 상태이펙트, Enemy AI (공격성/성격), Multi-Enemy, AoE, Boss 페이즈
- **프로그래밍**: ICE 해킹, 디코딩, 해독
- **그래픽노벨**: 9캐릭터 × 9씬 = 81 GN 씬
- **제작/장비**: 크래프팅, 장비 시스템
- **뮤테이터**: 런별 변형 (저체력, 더블알람, 스텔스온리 등)
- **업적**: 28개 업적 시스템
- **PWA**: 오프라인 플레이 지원

## 라이선스

MIT License
