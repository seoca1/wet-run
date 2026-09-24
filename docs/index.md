# Wet Run - Wiki Index

위키/디자인/결정/테스트 페이지 카탈로그. LLM Wiki 표준 패턴.

**현재 상태**: Phase 5+6 (Vertical Slice + Expansion) 완료. **3835 tests pass** (462 skipped, 1 xfailed, 4 xpassed; **4302 collected**). **111 missions** / **300 short stories** (150 EN + 150 KO) / **14 stages**. 5 arcs (1-5) × 12 grade ranges. Novel Hook Dispatch (ADR-0061) + Novel Integration (런타임 연동) + BRIEFING/TRAVEL/BYPASS_SECURITY/BLACK_MARKET/GHOST_ENCOUNTER stages. **2026-08-07 audit-tool fix**: `tools/audit_sprawl.py` path resolution 2-line 수정 → false orphan 10건 해소 (15 → 5, all expected). Working tree clean, 1 commit unpushed (`b87f330`).

## 메타
- [README](../README.md) - 프로젝트 개요
- [AGENTS](../AGENTS.md) - AI 에이전트 가이드
- [ROADMAP](../ROADMAP.md) - 단계별 계획 (Phase 4 완료)
- SETUP_LOG - 환경 구축 기록
- [log](../log.md) - 활동 로그
- [CHANGELOG](../CHANGELOG.md) - 버전별 변경 이력
- [prototype/](../prototype/) - **Phase 4: 코드 프로젝트**

## 세션 / 릴리스 노트
- SESSION_SUMMARY_2026-08-19_notion — **LATEST.** Notion 통합 (66 design pages, 명칭 통일)
- SESSION_SUMMARY_2026-08-19 — CI hygiene + Pages deploy 복구 (46d stale → live)
- SESSION_SUMMARY_2026-08-18 — Axis 5/4/6 closure
- SESSION_SUMMARY_2026-08-13 — mypy strict upgrade
- SESSION_SUMMARY_2026-08-10 — Phase 14 v1.3.0+ integration
- SESSION_SUMMARY_2026-08-08 — v1.3.0+ release
- SESSION_SUMMARY_2026-08-06 — dirty-tree closure
- _archive/audits/session-close-2026-08-05 — 16-iteration audit
- SESSION_SUMMARY_2026-08-05_cycle-audit — quality audit
- SESSION_SUMMARY_2026-08-05 — workspace reorg
- SESSION_SUMMARY_2026-08-03 — Fiction diagnostics
- _archive/sessions/SESSION_SUMMARY_2026-07-28_v1.1.0a1 — v1.1.0a1
- _archive/sessions/SESSION_SUMMARY_2026-07-28 — v1.0.0 FINAL
- _archive/sessions/SESSION_SUMMARY_2026-07-27 — Phase 1 game balance
- SESSION_SUMMARY_2026-07-11
- SESSION_SUMMARY_2026-07-12
- SESSION_SUMMARY_2026-07-13

## 대시보드
- [dashboard/DESIGN_METADATA_PLAN](dashboard/DESIGN_METADATA_PLAN.md) - 메타데이터 설계
- [dashboard/REORGANIZE_PLAN](dashboard/REORGANIZE_PLAN.md) - 재구성 계획

## 세계관 (World)
- Sprawl Universe - 시간/공간, 기본 컨셉
- Cyberspace - 매트릭스의 정의와 작동
- Factions - 주요 세력
- Glossary - 용어 사전
- Style Guide - 톤과 미적 가이드
- Boss ICE Reference - **Phase B-3 5개 보스 ICE 프로필 + AoE/미니언 스폰 (2026-07-26)**
- Derivative Stories - **이차 창작 단편 매핑 (150 KO + 150 EN = 300 stories / 111 missions mapped, ADR-0051 schema)**
- Cross-Project Integration - **Fiction ↔ wet_run 양방향 통합 (Phase α-J)**

> **Primary source**: `../../../Fiction/wiki/` — 깁슨 원작 분석 (Sprawl Trilogy, characters, settings). 게임 wiki는 게임용 요약.

## 디자인 (Design)
- Pillars - 디자인 기둥
- Core Loop - 핵심 게임 루프
- Character Paths - **3캐릭터 × 15미션 진행 경로 (2026-06-25 신규)**
- GDD - Game Design Document
- Glossary - 게임 용어
- Story Skeleton - **주요 줄기 뼈대 (5 arcs + 4+ endings)**
- Systems: ASCII Portraits - **인물/객체 시각 식별**
- Systems: Difficulty Rating (PPL & ZDR) - **전투 난이도 가시화**
- Systems: Story Events - **소설 스토리 부가 이벤트**
- Systems: Hacking (Cyberspace / Matrix) - **매트릭스 / 해킹 시스템 (Phase 5 신규)**
- Systems: Combat (RT-MS + Data Salvage) - **전투 + 전투 승리 보상 (ADR-0003 + ADR-0014)**
- Systems: Crafting (Material & 조합) - **3-tier 재료 & 조합 시스템 (ADR-0015)**
- Systems: Jockey Avatar (스탯 시각화) - **자키 아바타, 부위별 stat 표현 (ADR-0016)**
- Systems: Missions (미션-재료 통합) - **미션 시스템 + Hub 4-패널 + Recipe 트리 (ADR-0017)**
- Systems: Animations (전투 ASCII 애니메이션) - **Normal vs Skill ASCII 애니메이션 (ADR-0018)**
- Systems: Aftermath & Subtitles (전투 후일담 & 한글 자막) - **전투 후일담 + 소설 인물 반응 + 한글 자막 (ADR-0019)**
- Systems: Grade Progression (5단계 전투 검증) - **자키 등급 1~5 전투 & 결과 이벤트 (ADR-0008 + ADR-0019)**
- Systems: Exploration (Fog of War) - **안개 / 탐험 메카닉 (ADR-0020)**
- Scenario Overview - **오리지널 시나리오 통합 (ADR-0031)**
- Chapter 1: 케이 (Novice) - **첫 잭인**
- Chapter 2: 실 (Veteran) - **오래된 의문**
- Chapter 3: 카스 (Heretic) - **선언**
- Graphic Novel Mode - **그래픽 노블 자동플레이 (ADR-0032, 0041 톤 가이드라인 §10)**
- Death & Restart Cycle - **자키 사이클 + Hall of Dead (ADR-0040)**
- Story vs Stage Comparison - **단편소설/그래픽노블/게임스테이지 비교표**
- Game Structure (5-Chapter Architecture) - **챕터/Arc/Prologue 용어 재정의 + 5챕터 설계**
- Chapter Progress Tracker - **15챕터 구현 진도 추적표**
- Session Handover (v0.8.0, archived) - **다른 세션 인수인계 (구버전 v0.8.0 — 현재 상태는 SESSION_SUMMARY_2026-08-06.md 참조)**

## 결정 기록 (Decisions)
- [Index](wiki/decisions/README.md) - 모든 ADR 목록

## Round 4 — Index Reconciliation (2026-07-30) — Operational Docs + Guides

> Orphan pages reconciled from filesystem. Operational docs (DEPLOYMENT/NOTION/GitHub), character journey pages, prototype guides, session summaries.

### 문서 (docs — added 15)
- docs/DEPLOYMENT_GUIDE — 배포 가이드 (GitHub Pages + 대안)
- docs/DUNGEON_EXPLORATION_REVIEW — 던전 탐험 리뷰
- docs/DUNGEON_OPTION_B_NETHACK — NetHack BSP 옵션 분석 (ADR-0060)
- docs/DUNGEON_VERIFICATION_CHECKLIST — 던전 검증 체크리스트
- docs/GITHUB_PROJECTS_SETUP — GitHub Projects 보드 설정
- docs/GITHUB_SETUP — GitHub 저장소 설정
- docs/NOTION_IMPORT — Notion 가져오기 절차
- docs/REMOTE_DEV_SETUP — 원격 개발 환경 설정
- docs/REMOTE_DEV_SETUP_notion — 원격 개발 환경 설정 (Notion 발행용)
- SESSION_HANDOVER_NOTION (archived) — 세션 인수인계 (Notion 발행용, 과거 — 2026-08-05 archive 이동)
- docs/audits/2026-07-27_balance — 밸런스 감사 보고서 (2026-07-27)
- docs/bgm-external-generation-guide — BGM 외부 생성 가이드
- docs/cross-project/phase_beta_analysis — 크로스 프로젝트 Phase β 분석
- docs/prose_quality_report_2026-07-25 — 산문 품질 보고서 (2026-07-25)
- docs/video-generation-guide — 비디오 생성 가이드

### 자키 여정 (dashboard/stories/journey — added 3)
- [dashboard/stories/journey/heretic](dashboard/stories/journey/heretic.md) — 카스 (Heretic) 자키 여정 페이지
- [dashboard/stories/journey/novice](dashboard/stories/journey/novice.md) — 케이 (Novice) 자키 여정 페이지
- [dashboard/stories/journey/veteran](dashboard/stories/journey/veteran.md) — 실 (Veteran) 자키 여정 페이지

### 프로토타입 가이드 (prototype — added 9)
- prototype/CONTROLS — 조작 가이드
- prototype/DEMO_GUIDE — 데모 실행 가이드
- prototype/DUNGEON_NPC_GUIDE — 던전 NPC 가이드
- prototype/INTERACTIVE_GUIDE — 대화형 실행 가이드
- prototype/QUICK_START — 빠른 시작 가이드
- prototype/SOUND_PLAN — 사운드 플랜
- prototype/STATUS_PANEL_GUIDE — 상태 패널 가이드
- prototype/VISUAL_GUIDE — 비주얼 가이드
- prototype/docs/balance/E3-balance-audit — E-3 밸런스 감사

### 세션 요약 (root SESSION_SUMMARY — added 2)
- SESSION_SUMMARY — 마지막 세션 요약
- SESSION_SUMMARY_2026-07-28_v1.1.0a1 — v1.1.0a1 세션 요약 (2026-07-28)

## Round 2 — Index Reconciliation (2026-07-30)

> Orphan pages reconciled from filesystem. ADR status from each file's **상태** field. Design doc descriptions from filename or first content line.

### 결정 기록 (Decisions — added 54)
- [decisions/0001-engine-framework](wiki/decisions/0001-engine-framework.md) — python-tcod ECS 기반 엔진 (Accepted)
- [decisions/0002-rendering-style](wiki/decisions/0002-rendering-style.md) — ASCII 렌더링 스타일 (Accepted)
- [decisions/0003-combat-system](wiki/decisions/0003-combat-system.md) — RT-MS 전투 시스템 (Accepted, Revised 2026-06-17)
- [decisions/0004-code-architecture](wiki/decisions/0004-code-architecture.md) — 코드 아키텍처 (Accepted)
- [decisions/0005-cyberspace-representation](wiki/decisions/0005-cyberspace-representation.md) — 사이버스페이스 표현 (Accepted)
- [decisions/0006-run-structure](wiki/decisions/0006-run-structure.md) — 런 구조 (Accepted)
- [decisions/0007-platform-target](wiki/decisions/0007-platform-target.md) — 플랫폼 타겟 (Accepted)
- [decisions/0008-progression-system](wiki/decisions/0008-progression-system.md) — 메타 진행 시스템 (Accepted, Revised 2026-06-17)
- [decisions/0009-story-news-system](wiki/decisions/0009-story-news-system.md) — 스토리/뉴스 시스템 (Accepted)
- [decisions/0010-i18n-content-pipeline](wiki/decisions/0010-i18n-content-pipeline.md) — i18n 콘텐츠 파이프라인 (Accepted)
- [decisions/0011-ascii-portraits](wiki/decisions/0011-ascii-portraits.md) — ASCII 초상화 (Accepted)
- [decisions/0012-difficulty-rating](wiki/decisions/0012-difficulty-rating.md) — PPL/ZDR 난이도 등급 (Accepted)
- [decisions/0013-story-events](wiki/decisions/0013-story-events.md) — 스토리 이벤트 시스템 (Accepted)
- [decisions/0014-data-salvage](wiki/decisions/0014-data-salvage.md) — 데이터 살비지 (Accepted, auto-converted 2026-08-05)
- [decisions/0015-crafting-system](wiki/decisions/0015-crafting-system.md) — 제작 시스템 (Accepted, auto-converted 2026-08-05)
- [decisions/0016-jockey-avatar](wiki/decisions/0016-jockey-avatar.md) — 자키 아바타 (Accepted, auto-converted 2026-08-05)
- [decisions/0017-mission-material-integration](wiki/decisions/0017-mission-material-integration.md) — 미션-재료 통합 (Accepted, auto-converted 2026-08-05)
- [decisions/0018-combat-animation](wiki/decisions/0018-combat-animation.md) — 전투 애니메이션 (Accepted, auto-converted 2026-08-05)
- [decisions/0019-combat-aftermath-subtitles](wiki/decisions/0019-combat-aftermath-subtitles.md) — 전투 후일담 + 한글 자막 (Accepted, auto-converted 2026-08-05)
- [decisions/0020-fog-of-war-exploration](wiki/decisions/0020-fog-of-war-exploration.md) — 안개/탐험 메카닉 (Accepted, auto-converted 2026-08-05)
- [decisions/0030-github-utilization](wiki/decisions/0030-github-utilization.md) — GitHub 활용 전략 (Accepted)
- [decisions/0031-original-scenario-integration](wiki/decisions/0031-original-scenario-integration.md) — 오리지널 시나리오 통합 (Accepted, auto-converted 2026-08-05)
- [decisions/0032-graphic-novel-mode](wiki/decisions/0032-graphic-novel-mode.md) — 그래픽 노블 모드 (Accepted, auto-converted 2026-08-05)
- [decisions/0040-death-restart-cycle](wiki/decisions/0040-death-restart-cycle.md) — 사망-재시작 사이클 (Accepted, auto-converted 2026-08-05)
- [decisions/0041-graphic-novel-content-expansion](wiki/decisions/0041-graphic-novel-content-expansion.md) — GN 콘텐츠 4× 확장 (Accepted)
- [decisions/0042-chapter-title-cards](wiki/decisions/0042-chapter-title-cards.md) — 챕터 타이틀 카드 + fade (Accepted)
- [decisions/0043-sound-cue-integration](wiki/decisions/0043-sound-cue-integration.md) — 사운드 큐 매핑 (Accepted)
- [decisions/0044-graphic-novel-save](wiki/decisions/0044-graphic-novel-save.md) — GN 이어보기 save/load (Accepted)
- [decisions/0046-graphic-novel-ending-b](wiki/decisions/0046-graphic-novel-ending-b.md) — 엔딩 B 분기 (Accepted)
- [decisions/0047-text-visibility-typed-messages](wiki/decisions/0047-text-visibility-typed-messages.md) — 카테고리형 메시지 (Accepted)
- [decisions/0048-gn-ending-menu-and-save-migration](wiki/decisions/0048-gn-ending-menu-and-save-migration.md) — GN 엔딩 메뉴 + save 마이그레이션 (Accepted)
- [decisions/0049-graphic-novel-ending-c](wiki/decisions/0049-graphic-novel-ending-c.md) — 엔딩 C (소멸/망각/파괴) (Accepted, auto-converted 2026-08-05)
- [decisions/0050-boss-ice-system](wiki/decisions/0050-boss-ice-system.md) — Boss ICE 3-phase (Accepted, auto-converted 2026-08-05)
- [decisions/0051-mission-story-metadata](wiki/decisions/0051-mission-story-metadata.md) — 미션-단편 메타데이터 (Accepted, auto-converted 2026-08-05)
- [decisions/0052-short-story-expansion-plan](wiki/decisions/0052-short-story-expansion-plan.md) — 단편 확장 플랜 A~E (Accepted, All Complete)
- [decisions/0060-dungeon-exploration-redesign](wiki/decisions/0060-dungeon-exploration-redesign.md) — NetHack BSP 미로 (Accepted 2026-06-30)
- [decisions/0061-novel-integration-architecture](wiki/decisions/0061-novel-integration-architecture.md) — Novel Hook Dispatch 4-layer (Accepted 2026-06-30)
- [decisions/0090-salvation-phase-integration](wiki/decisions/0090-salvation-phase-integration.md) — Salvation 단계 통합 (Accepted)
- [decisions/0101-fiction-metadata-backfill](wiki/decisions/0101-fiction-metadata-backfill.md) — Fiction 메타데이터 백필
- [decisions/0102-v1-release-decision](wiki/decisions/0102-v1-release-decision.md) — v1.0.0 릴리스 결정 (Accepted)
- [decisions/0103-dungeon-only-mode](wiki/decisions/0103-dungeon-only-mode.md) — 던전 전용 모드 (Accepted)
- [decisions/0104-gn-save-slots](wiki/decisions/0104-gn-save-slots.md) — GN 세이브 슬롯 (Accepted 2026-07-25)
- [decisions/0110-module-size-policy](wiki/decisions/0110-module-size-policy.md) — 모듈 사이즈 정책 (250/500/1000 LOC) (Accepted 2026-07-12)
- [decisions/0111-graphic-novel-view-size](wiki/decisions/0111-graphic-novel-view-size.md) — GN view 사이즈 (Accepted 2026-07-12)
- [decisions/0112-combat-effects-size](wiki/decisions/0112-combat-effects-size.md) — 전투 이펙트 사이즈 (Accepted 2026-07-12)
- [decisions/0113-combat-view-size](wiki/decisions/0113-combat-view-size.md) — 전투 view 사이즈 (Accepted 2026-07-12)
- [decisions/0120-m2-docstring-batch](wiki/decisions/0120-m2-docstring-batch.md) — M2 docstring 배치 (Accepted 2026-07-12)
- [decisions/0125-boss-aoe-minion-spawn](wiki/decisions/0125-boss-aoe-minion-spawn.md) — Boss AoE 미니언 스폰 (Accepted 2026-07-26)
- [decisions/0130-balance-audit-and-ppl-sync](wiki/decisions/0130-balance-audit-and-ppl-sync.md) — 밸런스 감사 + PPL 동기화 (Accepted)
- [decisions/0131-faction-rep-cross-run-persistence](wiki/decisions/0131-faction-rep-cross-run-persistence.md) — Faction Rep cross-run 지속성 (Accepted)
- [decisions/0133-graphic-novel-view-split](wiki/decisions/0133-graphic-novel-view-split.md) — GN view 분리 (Accepted)
- [decisions/0140-engagement-layer](wiki/decisions/0140-engagement-layer.md) — Engagement Layer (Top 3 partial, Accepted)
- [decisions/0141-additional-module-splits](wiki/decisions/0141-additional-module-splits.md) — 추가 모듈 분할 (Top 2 partial, Accepted)
- [decisions/0142-graphic-novel-view-split-v2](wiki/decisions/0142-graphic-novel-view-split-v2.md) — GN view split v2 implementation (Accepted 2026-08-05)
- [decisions/0143-combat-view-split](wiki/decisions/0143-combat-view-split.md) — combat_view split implementation (Accepted 2026-08-05)
- [decisions/0144-combat-effects-split](wiki/decisions/0144-combat-effects-split.md) — combat/effects data extraction (Accepted 2026-08-05)
- [decisions/0145-effects-vfx-split](wiki/decisions/0145-effects-vfx-split.md) — combat/effects_vfx 3-way split (Accepted 2026-08-05)
- [decisions/0146-stage-flow-transitions](wiki/decisions/0146-stage-flow-transitions.md) — Stage Flow (black_market & ghost_encounter, Accepted 2026-08-05)
- [decisions/0147-data-salvage-phase6](wiki/decisions/0147-data-salvage-phase6.md) — Data Salvage Phase 6+ (HEAL + FRAG + CRED + alarm trade-off, Cycle 1 of A+B+C, Accepted 2026-08-07)
- [decisions/0148-combat-depth-expansion](wiki/decisions/0148-combat-depth-expansion.md) — Combat Depth (counter + defense + companion + aggression, Cycle 2 of A+B+C, Accepted 2026-08-07)
- [decisions/0149-boss-phase4-finale](wiki/decisions/0149-boss-phase4-finale.md) — Boss Phase 4 Finale (per-boss mechanics + death taunts + intro, Cycle 3 of A+B+C, Accepted 2026-08-07)
- [decisions/0150-module-split-depth-boss-phase4](wiki/decisions/0150-module-split-depth-boss-phase4.md) — Module Split (depth/boss_phase4 sub-packages, Cycle 4 of A+B+C, Accepted 2026-08-07)
- [decisions/0151-info-market-intel-items](wiki/decisions/0151-info-market-intel-items.md) — Info Market Intel Items (3 items, Cycle 6 v1.2.0+ bridge, Accepted 2026-08-07)
- [decisions/0152-multi-enemy-encounters](wiki/decisions/0152-multi-enemy-encounters.md) — Multi-Enemy Encounters (1v2/1v3 + HEAL rebalance, Cycle 8 v1.2.0+ core, Accepted 2026-08-07)
- [decisions/0153-matrix-encounter-spawn](wiki/decisions/0153-matrix-encounter-spawn.md) — Matrix Encounter Spawn Integration (1v1/1v2/1v3, Cycle 9 v1.2.0+ bridge, Accepted 2026-08-07)
- [decisions/0154-faction-expansion-i18n](wiki/decisions/0154-faction-expansion-i18n.md) — Faction Expansion (faction_rumor 4 factions + i18n ja/zh, Cycle 10 v1.2.0+ polish, Accepted 2026-08-07)
- [decisions/template](wiki/decisions/template.md) — ADR 작성 템플릿 (NNNN-short-title.md)

### 디자인 (Design — added 35)
- design/CONTENT_EXPANSION_PLAN — 콘텐츠 확장 플랜 (2026-06-25)
- design/research/unicode-block-art — 유니코드 블록 아트 조사 (2026-07-10)
- design/research/UNICODE_BLOCK_ART_SUMMARY — 유니코드 블록 아트 요약 (2026-07-10)
- design/balance/ppl_zdr_balance — PPL/ZDR 밸런스 노트
- design/scenario/CHARACTER_METADATA — 캐릭터 메타데이터 명세 (2026-06-23)
- design/scenario/chapter-4-bridge — Chapter 4: Bridge
- design/scenario/chapter-4-suit — Chapter 4: Suit
- design/scenario/chapter-5-veteran — Chapter 5: Veteran
- design/scenario/chapter-5-wigan — Chapter 5: Wigan
- design/scenario/chapter-6-angie — Chapter 6: Angie
- design/scenario/chapter-6-veteran — Chapter 6: Veteran
- design/scenario/chapter-7-sally — Chapter 7: Sally
- design/scenario/chapter-7-suit — Chapter 7: Suit
- design/scenario/chapter-8-3jane — Chapter 8: 3Jane
- design/scenario/chapter-9-neuromancer — Chapter 9: Neuromancer
- design/scenario/case-ch1-mapping — Case Ch1 매핑 (UPDATED)
- design/scenario/case-ch1-expansion-plan — Case Ch1 확장 플랜 (DRAFT)
- design/scenario/short-story-metadata-schema — 단편 메타데이터 스키마
- design/scenario/short-story-metadata-design — 단편 메타데이터 설계 (DRAFT)
- design/scenario/stat-difficulty-design — 스탯/난이도 설계 (DRAFT)
- design/scenario/WORLD_RELATIONSHIP — 세계관 관계 (2026-06-23)
- design/scenario/zone-expansion — 존 확장 (v0.1.0)
- design/scenario/PROGRESS_DASHBOARD — 시나리오 진도 대시보드 (Phase 7 완료, 2026-07-08)
- design/scenario/SALVATION_PHASE_INTEGRATION — Salvation 단계 통합 (v0.1-0.1.0)
- design/scenario/save-data-structure — 세이브 데이터 구조 (DRAFT)
- design/systems/i18n — 국제화 시스템
- design/systems/dialogue — 대화 시스템
- design/systems/inventory — 인벤토리 시스템 (ADR-0008 상속)
- design/systems/story-archive — 스토리 아카이브 시스템
- design/systems/dungeon_events — 던전 이벤트 시스템 (ADR-0060 상속)
- design/systems/economy — 경제 시스템
- design/systems/progression — 메타 진행 시스템 (ADR-0008 상속)
- design/systems/procgen — 절차적 생성 시스템
- design/story/prologue — 프롤로그 — 오리지널 주인공 3인
- design/story/characters — 캐릭터 명세 — 오리지널 주인공 3인

## 테스트 케이스
- [Index](testcases/README.md) - 모든 테스트 시나리오

## 최근 결정 (ADR-0041~0061, 2026-06-21 ~ 2026-07-01)
- **0041 Content Expansion** — 12 씬 dialogue 4× 확장 (4188 → 16862 chars)
- **0042 Chapter Cards** — 챕터 I-XII + fade transition (║ ─ ·)
- **0043 Sound Cues** — 15개 scene cue → file 매핑 (path 버그 fix)
- **0044 GN Save/Restore** — `GNProgress` atomic save + CONTINUE READING 메뉴
- **0045 Matrix Movement** — 15개 키 + Euclidian dot-product + 시각 힌트 (◄►▲▼)
- **0046 GN Ending B** — 엔딩 B 분기 (Refusal/Contract/Silence)
- **0047 Status Messages** — 카테고리형 메시지 (SUCCESS/INFO/WARN/ERROR) + 색상/아이콘
- **0048 GN Ending Menu** — 엔딩 A/B 메뉴 + Save 1.0.0→1.1.0 마이그레이션
- **0049 GN Ending C** — 엔딩 C (소멸/망각/파괴) + Save 1.1.0→1.2.0
- **0050 Boss ICE** — Wintermute + T-A Prime 3-phase + transition cinematics
- **0051 Mission Story Metadata** — 미션 ↔ 단편 직접 매핑 (ADR)
- **0052 Short Story Expansion Plan** — 17→35 단편 + 메타데이터 확장
- **0060 Dungeon Exploration Redesign** — NetHack 스타일 BSP 미로 (Phase 1+1.5+2+3+4)
- **0061 Novel Integration Architecture** — 4-layer Hook Dispatch (catalog/hooks/manifest/dispatcher) + 런타임 연동 (`engine/novel_integration.py`)

## 시스템 (Phase B 추가)
- **Novel Integration** (`engine/novel_integration.py`) — 미션 완료 시 `mission_to_stem` → `dispatch_for_state` 자동 호출
- **Stage BRIEFING / TRAVEL / BYPASS_SECURITY** — 9 → 13 stages (CONTENT_EXPANSION Phase B)
- **Boss Dispatch** (`combat/boss_dispatch.py`) — 11 zone bosses + 3 expansion bosses 통합 dispatch. `is_boss_id` / `build_boss_combatant_from_id` + tier-aware linear scaling (ADR-0190, 2026-08-18)
- **Zone Boss Registry** (`combat/boss_registry.py`) — `zone_bosses.json` (11 entries) → typed `ZoneBossProfile` lookup. ADR-0190, 2026-08-18
- **Boss F.4 Integration** — `combat/registry.py:build_ice_enemy` boss 가드 (zone_boss → boss_expansion → IceRegistry fallback)

## 데모 / 검증 스크립트
- Scripts 가이드 - **모든 데모/검증 스크립트 실행법 (27+ scripts, 추천 순서, 비교표)**
- Death in Action Demo - **전투 → 사망 사이클 end-to-end 데모 (ADR-0040 + combat 통합)**
- Combat Effects Demo - **5-Layer VFX 10-씬 검증 (palette, crit, 15 skills, 5 ICE, HUD, combo, Bundle)**
- Death Demo - 사망 화면 / 요약 / Hall of Dead 단독 데모
- Combat Grades - 5등급 진행 비교
- Visual Demo - 8개 시스템 한 번에 검증
- Demo All - 풀 게임 + 그래픽 노블 통합 자동플레이 (ADR-0032)
- Graphic Novel - 12-씬 그래픽 노블 자동플레이
- Play - 빠른 자동플레이 (MENU → HUB → MATRIX → COMBAT)
- Combat → Death Integration Test - **전투 패배 → trigger_death → 새 자키 (11 tests)**
- Boss Registry - **zone_bosses.json 11 entries → ZoneBossProfile lookup (27 tests, ADR-0190, 2026-08-18)**
- Boss Dispatch - **14 boss IDs dispatch 통합 + tier-aware scaling + lazy-cache (43 tests, ADR-0190, 2026-08-18)**
- Programs Schema - **programs.json 30 entries schema validity (ADR-0193)**
- Wetware Stacking - **wetware.json 10 augments tier-3 + new stats 누적**
- Augments - **lv1/lv2/lv3 progression + new stats (ADR-0173, ADR-0193)**
- Telemetry + Set Bonus Integration - **Ghost/Architect set bonus + telemetry 연동**
- Phase 14 Endings + Programs - **Axis 5/6 통합 테스트 (Phase 14)**
- Endings Handler - **21 endings trigger detect + reward/achievement handler (22 tests, ADR-0192)**
- Endings Persistence - **Save load + version migration + corruption tolerance (15 tests)**
- Ending Renderer - **rendering / queries / NG+ handling (19 tests, ADR-0192)**
- Graphic Novel Content Quality - **12 씬 dialogue 길이/톤/한글 동기화 (76 tests, ADR-0041)**
- Graphic Novel Novel Layout - **30줄 페이지 layout + pagination (28 tests)**
- Graphic Novel Chapter Cards - **챕터 타이틀 카드 + fade transition (37 tests, ADR-0042)**
- Graphic Novel Endings - **엔딩 A/B 분기 + 6 신규 씬 (22 tests, ADR-0046)**
- Status Message - **카테고리형 메시지 + 색상/아이콘 (43 tests, ADR-0047)**
- GN Ending Menu - **엔딩 A/B 메뉴 화면 + Save 1.0.0→1.1.0 마이그레이션 (35 tests, ADR-0048)**
- GN Ending C - **엔딩 C (소멸/망각/파괴) + 메뉴 4옵션 + Save 1.1.0→1.2.0 (62 tests, ADR-0049)**
- Boss ICE - **Wintermute + T-A Prime 3-phase 시스템 + transition cinematics (52 tests, ADR-0050)**
- Graphic Novel Audio - **15개 scene cue → file 매핑 검증 + path 버그 fix (23 tests, ADR-0043)**
- Graphic Novel Save/Restore - **이어보기 save/load + CONTINUE READING 메뉴 (24 tests, ADR-0044)**
- Matrix Movement - **15개 키 + direction vector + 시각 힌트 (27 tests, ADR-0045)**
