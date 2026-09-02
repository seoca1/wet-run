# Wet Run — 마이그레이션 기록

## 개요

Python 프로토타입 (236 파일, 54K LOC) → TypeScript Web 완전 마이그레이션

## 마이그레이션 단계

### Phase 1: 데이터 레이어 통합 ✅
- missions.json (209개 미션)
- programs.json (30개 프로그램)
- ice_types.json (97개 ICE 타입)
- i18n 문자열
- 내보내기 스크립트

### Phase 2: 코어 게임 로직 ✅
- combat_models.ts — 전투 모델
- combat_engine.ts — 데미지 계산
- boss_phases.ts — 보스 페이즈 전환
- status.ts — 13개 상태이펙트
- state.ts — 게임 상태 관리

### Phase 3: 매트릭스 강화 ✅
- dungeon.ts — BSP 던전 생성
- dungeon_bsp.ts — BSP 파티셔닝
- dungeon_layout.ts — 크루스칼 MST
- exploration.ts — 탐험 메커니즘

### Phase 4: 콘텐츠 시스템 ✅
- crafting.ts — 제작 시스템
- equipment.ts — 장비 시스템
- achievements.ts — 28개 업적
- run_mutators.ts — 뮤테이터 시스템

### Phase 5: 내러티브 시스템 ✅
- graphic_novel.ts — 그래픽노벨 엔진
- scenes.json — 27개 씬

### Phase 6: 폴리시 ✅
- TypeScript strict 모드
- 899개 테스트

### Phase 7: 통합 ✅
- 제작/장비 그래픽노벨 메인루프 연결

## 전투 시스템 고도화 (Tier A) ✅

| 모듈 | 설명 | 테스트 |
|------|------|--------|
| Enemy AI | 공격성/성격/자동공격 | 35 |
| Multi-Enemy | 타겟전환/로스터/HUD | 7 |
| AoE Skills | 전체 공격 지원 | 4 |
| Boss AI | 페이즈 전환/미니언 소환 | 7 |
| Skill Cooldown | 스킬 쿨다운 추적 | 4 |
| Personality | 성격 기반 스킬 선택 | 3 |
| Companion | Dixie 자동공격/시너지 | 4 |

## 콘텐츠/UX (Tier B) ✅

| 모듈 | 설명 | 테스트 |
|------|------|--------|
| ice_types.json | aggression/personality 필드 동기화 | ✅ |
| Loot System | 전리품 드롭 시스템 | 9 |
| Mutator Integration | 뮤테이터 실제 통합 | 10 |
| Achievement Triggers | 업적 트리거 시스템 | 8 |
| Graphic Novel Save | 그래픽노벨 세이브/로드 | 4 |

## 인프라 (Tier C) ✅

| 모듈 | 설명 |
|------|------|
| lz-string Fixes | 테스트 수정 |
| Bundle Optimization | tree-shaking 검증 (388KB gzip 112KB) |
| PWA Service Worker | 오프라인 플레이 지원 |

## 최종 통계

- **테스트**: 997개 통과
- **파일**: 47개 테스트 파일
- **번들**: 388KB (gzip 112KB)
- **PWA**: 서비스워커 등록 완료

## 디렉토리 구조

```
wet_run/
├── prototype/              # Python 프로토타입
├── web/                    # TypeScript Web (메인 개발)
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
