# 결정 기록 (ADR Index)

Architecture Decision Records. 모든 주요 결정은 여기 추적된다.

## 상태 범례

- **Draft**: 작성 중, 사용자 결정 대기
- **Accepted**: 결정됨. 변경 시 새 ADR 작성 필요
- **Deprecated**: 더 이상 유효하지 않음. 사유 명시
- **Superseded by ADR-XXXX**: 새 결정으로 대체됨

## 결정 목록

| 번호 | 제목 | 상태 | Impl | 날짜 | 우선순위 |
| --- | --- | --- | --- | --- | --- |
| 0001 | 엔진/프레임워크 | **Accepted** | — | 2026-06-17 | P0 |
| 0002 | 비주얼 스타일 | **Accepted** | — | 2026-06-17 | P0 |
| 0003 | 전투 시스템 (RT-MS) | **Accepted (Revised)** | — | 2026-06-17 | P1 |
| 0004 | 코드 아키텍처 | **Accepted** | — | 2026-06-17 | P0 |
| 0005 | 사이버스페이스 표현 | **Accepted** | — | 2026-06-17 | P1 |
| 0006 | 런 구조 (로그라이크 vs 로그라이트) | **Accepted** | — | 2026-06-17 | P0 |
| 0007 | 플랫폼 타겟 | **Accepted** | — | 2026-06-17 | P0 |
| 0008 | 진행 / 레벨업 시스템 | **Accepted (Revised)** | — | 2026-06-17 | P1 |
| 0009 | Story / News 전달 시스템 | **Accepted** | — | 2026-06-17 | P1 |
| 0010 | i18n + Content Pipeline | **Accepted** | — | 2026-06-17 | P1 |
| 0011 | ASCII Portraits (인물/객체 시각 식별) | **Accepted** | — | 2026-06-17 | P1 |
| 0012 | Combat Difficulty & Threat Level (PPL & ZDR) | **Accepted** | — | 2026-06-17 | P0 |
| 0013 | Story Events System (소설 스토리 이벤트) | **Accepted** | — | 2026-06-17 | P1 |
| 0014 | Data Salvage (전투 승리 보상 — 데이터 회수) | **Accepted** | — | 2026-06-18 | P1 |
| 0015 | Material & Crafting System (재료 & 조합) | **Accepted** | — | 2026-06-18 | P1 |
| 0016 | Jockey Avatar (자키 아바타 — 스탯 시각화) | **Accepted** | — | 2026-06-18 | P1 |
| 0017 | Mission-Material Integration (미션-재료 통합) | **Accepted** | — | 2026-06-18 | P1 |
| 0018 | Combat Animation (전투 ASCII 애니메이션) | **Accepted** | — | 2026-06-18 | P1 |
| 0019 | Combat Aftermath & Immersive Subtitles (전투 후일담 & 한글 자막) | **Accepted** | — | 2026-06-18 | P1 |
| 0020 | Fog of War + Exploration (안개 / 탐험 메카닉) | **Accepted** | — | 2026-06-18 | P1 |
| 0030 | GitHub Utilization Plan (GitHub 활용 계획) | **Accepted** | — | 2026-07-04 | P2 |
| 0031 | Original Scenario Integration (단편 → 챕터 → 초반 플레이 통합) | **Accepted** | — | 2026-06-20 | P1 |
| 0032 | Graphic Novel Auto-Play Mode + Main Menu 확장 (5 옵션) | **Accepted** | — | 2026-06-20 | P1 |
| 0040 | Death & Restart Cycle (자키 사이클 + Hall of Dead) | **Accepted** | — | 2026-06-20 | P1 |
| 0041 | Graphic Novel Content Expansion (씬 dialogue 4× 확장) | **Accepted** | — | 2026-06-20 | P1 |
| 0042 | Chapter Title Cards / Scene Transitions (로마 숫자 + fade) | **Accepted** | — | 2026-06-20 | P2 |
| 0043 | Sound Cue Integration (15개 cue → file 매핑) | **Accepted** | — | 2026-06-20 | P2 |
| 0044 | Graphic Novel Save/Restore (이어서 읽기) | **Accepted** | — | 2026-06-20 | P2 |
| 0046 | Graphic Novel Ending B (대안 결말) | **Accepted** | — | 2026-06-21 | P1 |
| 0047 | Text Visibility (Typed Status Messages) | **Accepted** | — | 2026-06-21 | P2 |
| 0048 | GN Ending Menu + Save Migration 1.1.0 | **Accepted** | — | 2026-06-21 | P2 |
| 0049 | Graphic Novel Ending C (3rd ending) + Save 1.2.0 | **Accepted** | — | 2026-06-21 | P2 |
| 0050 | Boss ICE System (Wintermute + T-A Prime 3-phase) | **Accepted** | — | 2026-06-21 | P1 |
| 0051 | Mission Story Metadata (미션 ↔ 단편 직접 매핑) | **Accepted** | — | 2026-06-22 | P1 |
| 0052 | Short Story Expansion Plan (단편 3편 보강) | **Accepted** | — | 2026-06-22 | P2 |
| 0060 | Dungeon Exploration Redesign (NetHack + VFX) | **Accepted** | — | 2026-06-30 | P2 |
| 0061 | Novel Integration Architecture (Hook 디스패치) | **Accepted** | — | 2026-06-30 | P2 |
| 0090 | Salvation Phase Integration (9자 × epilogue + ChapterState 3개 + Stage 1개) | **Accepted** | — | 2026-07-07 | P2 |
| 0104 | GN Save Slot 확장 (3 슬롯) | **Accepted (2026-07-25)** | 2026-06-21 | P2 |
| 0101 | Fiction Metadata 보강 계획 (status report, not ADR) | (status doc) | — | P3 |
| 0102 | v1.0.0 Release Decision | **Accepted** | — | 2026-07-08 | P2 |
| 0103 | Dungeon-only Mode — `D` 토글 제거, `matrix_view` 폐기 | **Accepted** | — | 2026-07-10 | P2 (The Matrix) |
| 0110 | 모듈 사이즈 정책 (현행 250 LOC) | **Accepted (Option 4)** | 2026-07-12 | P3 (The Build) |
| 0111 | graphic_novel_view.py (1,510 LOC) — 정당화 or 분할 | **Accepted (Option 4)** | 2026-07-12 | P3 (The Build) |
| 0112 | combat/effects.py (1,246 LOC) — 5-Layer VFX 시스템 | **Accepted (Option 4)** | 2026-07-12 | P3 (The Build) |
| 0113 | combat_view.py (1,053 LOC) — 전투 화면 렌더링 | **Accepted (Option 4)** | 2026-07-12 | P3 (The Build) |
| 0120 | M2 14 파일 docstring 보강 — 일괄 작업 | **Accepted (Option 1)** | 2026-07-12 | P3 (The Build) |
| 0125 | Boss Phase AoE + Minion Spawn (Phase B-3 Enhancement) | **Accepted (Option 4)** | 2026-07-26 | P3 (The Build) |
| 0130 | Balance Audit + PPL/보상 동기화 (Phase 1 정리) | **Accepted (Option 1)** | 2026-07-27 | P1 (The Build) |
| 0131 | Faction Reputation Cross-Run Persistence (Meta Progression) | **Accepted (Option 1)** | 2026-07-27 | P1 (The Build) |
| 0133 | graphic_novel_view.py Split — Implementation (Supplements ADR-0111) | **Accepted** | — | 2026-07-27 | P2 (Build Health) |
| 0140 | Engagement Layer for v1.1.0 (8 proposals) | **Accepted (Option 1 partial — Top 3)** | 2026-07-28 | P2 (v1.1.0 후보) |
| 0141 | Additional Module Splits (matrix_view, combat/state) | **Accepted (Option 1 partial — Top 2)** | 2026-07-28 | P3 (v1.1.0+ backlog) |
| 0142 | graphic_novel_view Split v2 — Implementation (3-way split) | **Accepted** | — | 2026-08-05 | P2 (Build Health) |
| 0143 | combat_view Split — Implementation (4-way split) | **Accepted** | — | 2026-08-05 | P2 (Build Health) |
| 0144 | combat/effects Split — Data Extraction | **Accepted** | — | 2026-08-05 | P2 (Build Health) |
| 0145 | combat/effects_vfx Split — 3-Way Concern Split | **Accepted** | — | 2026-08-05 | P2 (Build Health) |
| 0146 | Stage Flow — black_market & ghost_encounter 전이 추가 (Validator FAIL 해결) | **Accepted** | — | 2026-08-05 | P2 (The Matrix) |
| 0147 | Data Salvage — Phase 6+ Completion (HEAL + FRAG + CRED + alarm trade-off) | **Accepted** | — | 2026-08-07 | P1 (Cycle 1 of A+B+C) |
| 0148 | Combat Depth Expansion (counter window + defense stackable + companion skills + aggression tiers) | **Accepted** | — | 2026-08-07 | P1 (Cycle 2 of A+B+C) |
| 0149 | Boss Phase 4 Finale (per-boss mechanics + death taunts + intro enhancement) | **Accepted** | — | 2026-08-07 | P1 (Cycle 3 of A+B+C) |
| 0150 | Module Split — `depth.py` + `boss_phase4.py` (ADR-0110 follow-up) | **Accepted** | — | 2026-08-07 | P2 (Cycle 4 of A+B+C) |
| 0151 | Info Market Intel Items — CRED Consumption (3 items, close salvage trade-off) | **Accepted** | — | 2026-08-07 | P1 (Cycle 6, v1.2.0+ bridge) |
| 0152 | Multi-Enemy Encounters (1v2/1v3) + HEAL Rebalance 20%→15% | **Accepted** | — | 2026-08-07 | P1 (Cycle 8, v1.2.0+ core) |
| 0153 | Matrix Encounter Spawn Integration (1v1/1v2/1v3) | **Accepted** | — | 2026-08-07 | P1 (Cycle 9, v1.2.0+ bridge) |
| 0154 | Faction Expansion (faction_rumor 4 factions) + i18n (ja/zh) | **Accepted** | — | 2026-08-07 | P2 (Cycle 10, v1.2.0+ polish) |
| 0155 | NG+ Grade 5→6 PPL Actual Rebalance (T6 master tier bonus +10) | **Accepted** | — | 2026-08-07 | P2 (Cycle 11, v1.2.0+ balance) |
| 0156 | Combat State Module Split (state.py 890 → 3 files) | **Accepted** | — | 2026-08-07 | P3 (The Build, ADR-0110 follow-up) |
| 0157 | Combat Boss Module Split (boss.py 724 → 2 files) | **Accepted** | — | 2026-08-07 | P3 (The Build, ADR-0110 follow-up) |
| 0158 | Combat Combo Module Split (combo.py 685 → 2 files) | **Accepted** | — | 2026-08-07 | P3 (The Build, ADR-0110 follow-up) |
| 0159 | Combat Bosses Cinematic Module Split (bosses.py 627 → 2 files) | **Accepted** | — | 2026-08-07 | P3 (The Build, ADR-0110 follow-up) |
| 0160 | Status Effects System Expansion (DoT/Stun/Slow/Silence/Vulnerability) | **Accepted** | — | 2026-08-07 | P1 (The Build, Pillar 3 weight) |
| 0161 | ICE Personality Archetypes (4 behaviors beyond aggression) | **Accepted** | — | 2026-08-07 | P2 (Pillar 5 variety, Pillar 3 weight via different pressure) |
| 0162 | Boss Phase 4 Last Stand | **Accepted** | — | 2026-08-07 | P2 (Pillar 1 climax, Pillar 5 finale) |
| 0163 | Run Mutators System (5+ modifiers) | **Accepted** | — | 2026-08-07 | P1 (Pillar 1 run variety, Pillar 4 meta progression) |
| 0164 | Mission Archetypes (4 mission types) | **Accepted** | — | 2026-08-07 | P1 (Pillar 1 run variety) |
| 0165 | Random Matrix Events (4-6 mid-run surprises) | **Accepted** | — | 2026-08-07 | P2 (Pillar 1 variety, Pillar 5 atmosphere) |
| 0166 | Phase 6 Arc (Aftermath - Post-Ending NG+ Content) | **Accepted** | — | 2026-08-07 | P2 (Pillar 1 endgame, Pillar 4 meta progression) |
| 0167 | Mission Expansion (15 → 25 missions) | **Accepted** | — | 2026-08-07 | P2 (Pillar 1 content variety, Pillar 5 progression) |
| 0168 | Death Taunts Library (Per-Boss + Per-ICE) | **Accepted** | — | 2026-08-07 | P1 (Pillar 5 style, Pillar 3 death weight) |
| 0169 | Combat Cinematics (Per Boss Phase Intro) | **Accepted** | — | 2026-08-07 | P2 (Pillar 5 style, Pillar 1 climax) |
| 0170 | Gibson Fluff Library (200+ Status Messages) | **Accepted** | — | 2026-08-07 | P1 (Pillar 5 style) |
| 0171 | ASCII Battle Portrait Evolution | **Accepted** | — | 2026-08-07 | P2 (Pillar 5 style, Pillar 3 visual feedback) |
| 0172 | Cyberdeck Customization (8 Program Slots) | **Accepted** | — | 2026-08-08 | P1 (Pillar 4 Build depth) |
| 0173 | Wetware Augments (6 Passive Slots) | **Accepted** | — | 2026-08-08 | P1 (Pillar 4 Build depth) |
| 0174 | Meta-Progression (Persistent Unlocks) | **Accepted** | — | 2026-08-08 | P1 (Pillar 1 replay value) |
| 0175 | Tutorial System (3-Act Onboarding) | **Accepted** | — | 2026-08-08 | P2 (Pillar 1 learning curve) |
| 0176 | Achievement System (60+ Achievements) | **Accepted** | — | 2026-08-08 | P2 (Pillar 1 replay value) |
| 0177 | Breach Protocol (Matrix Hacking Minigame) | **Accepted** | — | 2026-08-08 | P1 (Pillar 2 Matrix, Pillar 5 style) |
| 0178 | Deck Building (6/8/10 Slot Limits) | **Accepted** | — | 2026-08-08 | P1 (Pillar 4 Build depth) |
| 0179 | Status Effects v2 (Bleed, Fatigue, Confused, Terrified) | **Accepted** | — | 2026-08-08 | P2 (Pillar 3 depth) |
| 0180 | Boss Expansion (+3 Boss Profiles) | **Accepted** | — | 2026-08-08 | P2 (Pillar 1 variety, Pillar 5 atmosphere) |
| 0181 | Combo System v2 (Player-Triggered Finisher Combos) | **Accepted** | — | 2026-08-08 | P2 (Pillar 5 style, Pillar 4 build) |
| 0182 | Run Replay System (Record + Playback) | **Accepted** | — | 2026-08-08 | P2 (Pillar 1 replay, Pillar 5 style) |
| 0183 | Accessibility (Colorblind 3 Modes, Text Size, Input Remapping) | **Accepted** | — | 2026-08-08 | P2 (Pillar 1 inclusivity + Pillar 5 style) |
| 0184 | Telemetry (Anonymous Player Behavior Tracking) | **Accepted** | — | 2026-08-08 | P3 (Pillar 4 balance + Pillar 1 tuning) |
| 0185 | Save/Load Migration v2 (Versioned, Cloud-Ready) | **Accepted** | — | 2026-08-08 | P2 (Pillar 1 persistence + Pillar 4 carry) |
| 0186 | Performance Optimization (Frame Rate, Memory) | **Accepted** | — | 2026-08-08 | P3 (Pillar 1 smoothness) |
| 0187 | Boss Phase 5 Expansion (Last Stand) | **Accepted** | — | 2026-08-08 | P2 (Pillar 1 climax, Pillar 5 finale) |
| 0188 | Mission Expansion (Phase 11 — Content Expansion, Axis 1) | **Accepted** | — | 2026-08-08 | P1 (Pillar 1 run variety) |
| 0189 | ICE Type Expansion (Phase 12 — Content Expansion, Axis 2) | **Accepted** | — | 2026-08-08 | P2 (Pillar 3 combat variety + Pillar 5 atmosphere) |
| 0190 | Boss Expansion + F.4 Integration (Phase 12 — Content Expansion, Axis 4) | **Accepted** | — | 2026-08-08 | P1 (Pillar 1 climax + Pillar 5 finale) |
| 0191 | Story Events Expansion (Phase 13 — Content Expansion, Axis 3) | **Accepted** | — | 2026-08-08 | P2 (Pillar 5 atmosphere + Pillar 1 variety) |
| 0192 | Ending Expansion (Phase 14 — Content Expansion, Axis 5) | **Accepted** | — | 2026-08-08 | P2 (Pillar 1 replay value + Pillar 5 closure) |
| 0193 | Programs/Equipment Expansion (Phase 14 — Content Expansion, Axis 6) | **Accepted** | — | 2026-08-08 | P2 (Pillar 4 Build depth + Pillar 5 style) |
| 0194 | ECS-lite 역할 명시화 (프로덕션은 OOP/dataclass, ECS는 실험/테스트 도구) | **Accepted** | — | 2026-08-19 | P3 (The Build, 아키텍처 명료화) | → **Accepted (Option 3 Hybrid)** 2026-08-26 [this session]
| 0195 | Accepted ADR Implementation Status Workflow (섹션 의무화 + 인덱스 Impl 컬럼) | **Accepted** | — | 2026-08-20 | P3 (The Build, 프로세스 명료화) | → **Accepted (Option 1+3 Hybrid)** 2026-08-26 [this session]
| 0196 | Accessibility Colorblind State Alignment (AppState bool → str) | **Accepted (Option A)** | — | 2026-08-22 | P1 (Plan T2.2 게이트, UI/visibility 업그레이드) |
| 0197 | Gamepad / Controller Input Support (Tier 1 — synthetic KeyDown adapter, 12 active ScreenKinds, 97 new tests) | **Accepted** | — | 2026-08-25 | P2 (ADR-0183 §Input Remapping Tier 1 surface; complements ADR-0196) |
| 0198 | Resolution Compatibility (Tablet / Phone / Steam Deck / 4K) + QA Agents (Design + Gameability) | **Accepted** | — | 2026-08-25 | P1 (Cross-device compatibility; +QA agents for ongoing QA; 6 Open Questions resolved; Phase 1 critical fixes shipped — GA-002/GA-004/GD-005) |
| 0199 | Wet Run Web MVP (Tier 1 — TypeScript + Canvas2D + 1 playable mission, supersedes ADR-0007 web/mobile scope) | **Accepted** | — | 2026-08-25 | P1 (Browser reach; 4-week MVP build autonomous) |
| 0200 | Git LFS D4 — 오디오 자산 관리 (현상 유지 + 명문화, 326MB audio in 258MB Git history) | **Accepted (Option 1)** | 2026-08-26 | P3 (Operational hygiene, 분기별 재평가) |
| 0201 | wet_run-web Tier 2b — Howler.js BGM 통합 (단일 BGM `theme_sense_net`, M 키 mute toggle, +37.91 KB bundle) | **Accepted (Option 1)** | 2026-08-26 | P2 (Web MVP 완성도 ↑, plan §8) |
| 0202 | wet_run-web Tier 2c — 미션 + ICE 다양성 확장 (5→15 missions T1-T3, 12 ICE Gibson-flavor, 85.52 KB bundle) | **Accepted (Option 1)** | 2026-08-26 | P2 (plan §8 Tier 2c: Full deck-building roster, ICE variety) |
| 0203 | wet_run-web Tier 3 — 30 Missions + 30 ICE Expansion (T1-T5, 6 zones, 10 fixers, 124.66 KB bundle) | **Accepted (Option 1)** | 2026-08-26 | P2 (plan §8 Tier 3: Full deck-building roster, ICE variety expansion) |
| 0204 | wet_run-web Phase-aware BGM (5 tracks, GamePhase 매핑, 125.43 KB bundle) | **Accepted (Option 2)** | 2026-08-26 | P2 (Tier 2b Option 2 확장: phase 기반 BGM 전환) |
| 0205 | wet_run-web Status Effect VFX + HUD Bars (HP bars + turn counter + status labels, pure function helpers, 126.10 KB bundle) | **Accepted (Option 1)** | 2026-08-26 | P2 (combat HUD 강화, plan §3.2 out-of-MVP 보완) |
| 0206 | Mission Registry Wiring — Arc6 + Expansion deferred 해결 (ZoneDepth.AFTERMATH + arc 1..6 + enrich_* + JobBoard 통합, 194→209 missions) | **Accepted (Option 1)** | 2026-08-26 | P1 (ADR-0166/0167 Consequences 후속 작업, 보드 wiring 활성화) |
| 0207 | wet_run-web Tier 4 — SFX (combat_hit/victory/defeat) + Animation VFX (hit flash/defeat art) + Status Effect Glyphs (5 effects), 단순 통합 batch (128.65 KB bundle, +21 tests) | **Accepted (Option 1)** | 2026-08-26 | P2 (wet_run-web 자체 확장, plan §8 Tier 4 자체 정의) |
| 0048 | Phase 189 — Wet Run Character Reflection (molly, johnny, rydell wiki pages cross-referenced to Fiction/wiki) | **Accepted** | — | 2026-08-24 | P2 |
| 0049 | Phase 190 — Dashboard Verification Framework Sub-Stats Panel (verification_framework sub-object in aggregate-stats.mjs) | **Accepted** | 2026-08-24 | P2 |

### 2026-07-01 통합 작업 (P1~P4 + B)

| 번호 | 제목 | 상태 | 날짜 | 우선순위 |
| --- | --- | --- | --- | --- |
| (—) | **Stage BRIEFING / TRAVEL / BYPASS_SECURITY** (Stage enum +3, 10→13) | **Implemented** | 2026-07-01 | P1 |
| (—) | **Novel Integration 런타임 연동** (`engine/novel_integration.py`, `mission_to_stem` + `dispatch_for_state`) | **Implemented** | 2026-07-01 | P1 |
| (—) | **CONTENT_EXPANSION Phase A+ 신규 미션 5개** (Arc 2-3: sense_net_infiltration, wigan_call, hosaka_core, straylight_approach, maas_heist) | **Implemented** | 2026-07-01 | P1 |
| (—) | **KO 번역 한자 잔재 0건** (missions/arcs/chapters/aftermath 일괄 정정) | **Implemented** | 2026-07-01 | P1 |
| (—) | **`stage_structure.json` v0.4.0** (stages 9→12, transitions 8→13) | **Implemented** | 2026-07-01 | P2 |

## 우선순위 정의

- **P0 (최우선)**: 0001, 0002, 0004, 0006, 0007, 0012 — Phase 4 시작 전 결정 필요
- **P1**: 0003, 0005, 0008, 0009, 0010, 0011, 0013, 0014, 0015, 0016, 0017, 0018, 0019, 0020 — Phase 5 시작 전 결정 필요
- **P2 (미정)**: 추가 결정은 Phase 5 이후 또는 진행 중 발생 시 추가

## 결정이 다른 결정에 미치는 영향 (Accepted 결정으로 인한 제약)

- **0001 → 0002**: libtcod + Python → Pure ASCII와 자연스러움
- **0001 → 0004**: Python → ECS-lite + 데이터 주도 권장
- **0001 → 0007**: libtcod은 macOS + Windows 모두 네이티브
- **0002 → 0005**: Pure ASCII → 노드 그래프 표현이 ASCII 기호로 가능
- **0003 → 0005**: AP 턴 → 노드 간 이동이 AP 비용
- **0006 → 0008**: 하이브리드 unlock → 자키 등급 시스템이 unlock 표현
- **0009**: meatspace 미표시, Story Archive로만 외부 세계 전달
- **0014**: HEAL 20% — Pillar 3 무게 유지; FRAG/CRED는 Phase 6+ 확장
- **0015**: 3-tier crafting (5 raw → 4 components → final) — Pillar 4 직접 표현
- **0016**: Stick Figure Avatar — 부위별 stat 표현 (HP 머리, programs 팔, deck 몸통, wetware 다리)
- **0017**: Mission-Material Integration — 6 미션 타입, Hub 4-패널, Recipe 트리 뷰
- **0018**: Combat Animation — 일반 240ms gray vs 스킬 600ms color, 깁슨 톤 글리치

## 일관성 (모두 Accepted)

| 항목 | 결정 |
| --- | --- |
| 언어 | Python 3.11+ |
| 엔진 | python-tcod |
| 비주얼 | Pure ASCII |
| 아키텍처 | ECS-lite + 데이터 주도 (i18n 포함) |
| 런 구조 | 하이브리드 (unlock만 메타) |
| 플랫폼 | macOS + Windows |
| 전투 | Real-Time + Menu Skills (RT-MS) |
| 매트릭스 | 노드 그래프 |
| 진행 | 런 내 스탯 고정 + 자키 등급 (메타) + 아이템 티어 (T1~T5) |
| meatspace | *절대 시각화되지 않음* |
| Story | Story Archive로 전달 |
| i18n | en (1차, 깁슨 톤) + ko (보조 번역/자막) |
| Content | 데이터 주도, 반복 보강, plot bones 사전 정의 |
| Portrait | ASCII / Unicode 기호 + 색상, cyberspace only |
| Difficulty | PPL (Player Power Level) & ZDR (Zone Difficulty Rating) |
| Events | Story Events (소설 스토리 부가 콘텐츠) |
| Combat Reward | Data Salvage (HEAL 20%, FRAG/CRED Phase 6+) |
| Crafting | 3-tier (5 raw → 4 components → program/item/construct) |
| Stat Display | Jockey Avatar (stick figure, 부위별 표현) |
| Mission-Material | 6 미션 타입, Hub 4-패널 (Avatar/Materials/Recipes/Job Board) |
| Combat Animation | Normal 240ms gray vs Skill 600ms color, 깁슨 톤 글리치 |
| Aftermath | 전투 후일담 4 importance + 소설 인물 7명 반응 + 한글 자막 |
| Exploration | Light Fog of War (현재+인접), 미니맵, breadcrumb |
| Scenario (0031) | 단편 → 챕터 → 초반 플레이 통합 (12 씬 dialogue, 4 캐릭터 × 3-4 씬) |
| Graphic Novel (0032) | 메인메뉴 5 옵션 + 12 씬 자동플레이 + Save Progress 카드 |
| Death Cycle (0040) | DEATH/DEATH_SUMMARY/HALL_OF_DEAD + restart_with_new_jockey (3 옵션) |
| Novel Layout (0041-0042) | 30줄 페이지 + chapter card I-XII + fade transition |
| Audio (0043) | 15개 scene cue → file 매핑 (theme/movement 카테고리) |
| GN Save (0044) | GNProgress atomic save + CONTINUE READING 메뉴 + version 1.0.0 |
| Ending B (0046) | 6 씬 추가 (Case/Sil/Kas × 2) + SceneData.ending 필드 + `--ending {A,B}` CLI |
| Text Visibility (0047) | MessageKind 8종 + 아이콘/색상/bg 하이라이트 + GN prose cream color |
| GN Ending Menu (0048) | GRAPHIC_NOVEL_ENDING_MENU 화면 + GNProgress.ending + Save 1.0.0→1.1.0 마이그레이션 |
| Ending C (0049) | 6 신규 씬 (Disappear/Erase/Burn) + 메뉴 4옵션 + Save 1.1.0→1.2.0 + 9 결말 조합 |
| Boss ICE (0050) | Wintermute + T-A Prime 보스 3-phase 시스템 + phase transition cinematics |
| Mission Metadata (0051) | 미션마다 `story.{synopsis_en, synopsis_ko, source, character_ref, arc, pillar, word_count_en, char_count_ko}` 메타데이터 필수 |
| Story Expansion (0052) | 단편 17→35+ 확장 + frontmatter 강화 (wiki_references, game_integration, character_ref) |
| Dungeon (0060) | NetHack BSP 미로 + 4 VFX spawner + Mission→Room 매핑 (29 미션) + ECS 통합 |
| Novel Integration (0061) | 4-layer Hook 디스패치 (catalog/hooks/manifest/dispatcher) + 런타임 자동 호출 (`engine/novel_integration.py`) |
| Salvation (0090) | 9자 × epilogue 씬 + SalvationRunner + ChapterState SALVATION_INTRO/EPILOGUE/DONE/FINAL + Stage SALVATION_EPILOGUE |

## 결정 절차 (참고용)

1. AI가 ADR 작성 (Draft 상태)
2. 사용자가 결정 또는 수정 요청
3. 결정되면 Status를 "Accepted"로 변경
4. Consequences 섹션 채우기
5. 영향 받는 design/ 시스템 명세 갱신
6. log.md에 기록

## 모든 결정 완료 — Phase 4 진입 가능

## Pillar 2 / 5 추가 영향 (ADR-0009)

meatspace 미표시는 디자인 전반에 영향을 미친다:
- **Pillar 2**: "The Matrix는 *유일한* 시각적 공간"으로 강화
- **Pillar 5**: "mediated world" 톤 — 외부 세계는 항상 텍스트/뉴스/이야기로만
- **디자인 리뷰 체크리스트**: "meatspace를 직접 묘사하고 있지 않은가?" 추가
- **세계관 wiki**: "새 플레이어", "meatspace 미표시" 명시

상세는 `decisions/0009-story-news-system.md` 참조.

## 콘텐츠 파이프라인 영향 (ADR-0010)

i18n + Content Pipeline:
- **모든 텍스트는 i18n JSON** — `data/i18n/{ko,en}.json`
- **모든 콘텐츠는 데이터** — JSON / YAML
- **plot bones 사전 정의** — `design/story_skeleton.md` (5 arcs + 4+ endings)
- **초반 미션 우선** — Arc 1 (1-3 jobs)
- **반복 보강** — 무한 side content, faction 뉴스, world events

상세는 `decisions/0010-i18n-content-pipeline.md` 및 `design/story_skeleton.md` 참조.

---

## ADR 인덱스 보강 (2026-07-25)

- **0051 번호 충돌 해결** (2026-07-25): 두 파일이 동일 번호 `0051` 사용 중이었음. Draft 파일 `0051-gn-save-slots.md`를 `0104-gn-save-slots.md`로 번호 이동. Accepted 결정(`0051-mission-story-metadata.md`) immutable 규칙 영향 없음.
- **0101-fiction-metadata-backfill.md** (status document): 전통적 ADR 형식(status/날짜 라인) 미사용 — `Fiction` 메타데이터 보강 진행 상황 추적용 status report. ADR 카운트에서 제외하거나, 별도 "Status Reports" 절로 분리 검토 가능.
- **신규 ADR 8개 추가 (2026-07-08 ~ 2026-07-12)**: 0102, 0103, 0110, 0111, 0112, 0113, 0120 + 0104-gn-save-slots.

## ADR-0104 Accepted (2026-07-25, Sisyphus + 사용자)

- **Status**: Draft → **Accepted**
- **구현 검증 완료**: 8개 파일에서 API 사용 중 (`engine/graphic_novel_save.py`, `state.py`, `app.py`, `menu.py`, `save_manager.py`, `scripts/graphic_novel.py`)
- **Save 파일**: `data/saves/gn_progress_slot_{1,2,3}.json` (3개 slot 파일 존재) + legacy `gn_progress.json` (보존)
- **신규 도구**: `prototype/scripts/save_slot_demo.py` (list / fill / load / delete / migrate / auto) — `--save-dir` 옵션으로 격리 테스트 가능
- **테스트**: `test_graphic_novel_save.py` (slot API + 마이그레이션) — ruff ✅, mypy ✅
- **코드 주석 보강**: `state.py:88, 265` — "ADR-0051 infra + ADR-0104 extension" 명시
- **Decisions**: Option 1 (3 슬롯 고정) — 9 결말 조합 시도 (3 chars × 3 endings) 인프라

## ADR 인덱스 보강 (2026-08-08)

- **0162 번호 충돌 해결** (2026-08-08): 두 파일이 동일 번호 `0162` 사용 중이었음. `0162-boss-phase-4.md`(canonical, 6 references)와 `0162-boss-phase-5.md`(no references, content는 Phase 5 expansion). 미참조 파일을 `0187-boss-phase-5-expansion.md`로 번호 이동. canonical 0162 title은 content 일치하도록 "Boss Phase 5 Last Stand" → "Boss Phase 4 Last Stand" 수정. 6 references 모두 그대로 유지 (참조 대상 변경 없음).
- **신규 ADR 31개 인덱스 추가** (2026-08-07~08): 0156–0186 (v1.2.0+ 후속 + v1.3.0+ Tracks E/F/G). 인덱스 누락 상태였음 — 본 동기화로 README 인덱스 최신화 완료. ADR 총 88개 (Accepted/Revised/Superseded 모두 포함, status docs 제외).
- **신규 ADR 7개 인덱스 추가** (2026-08-08~19): 0188–0194 (Phase 11~14 Content Expansion Axes 1~6 + ADR-0194 ECS-lite 역할 명시화). 7 ADR 파일은 2026-08-08~19 사이 생성되었으나 README 인덱스 누락 상태였음 — 본 동기화로 README 인덱스 최신화 완료. ADR 총 **106개** (Accepted/Revised/Draft 모두 포함, status docs 2개 제외).
- **ADR-0162 title fix**: content는 Phase 4 mechanics를 설명하지만 title이 "Boss Phase 5 Last Stand"로 잘못 표기되어 있었음. Content와 일치하도록 "Boss Phase 4 Last Stand"로 수정.

| 0208 | Mission Random Weight (ADR-0166/0167 weighted selection: 10 missions 1.5/1.2, random_weight field + apply_rule filter, 7/7 sub-steps) | **Accepted (Option 1)** | 2026-08-26 | P1 (ADR-0166/0167 wiring completion) |
| 0209 | wet_run-web IndexedDB Save Backend (Tier 3 literal partial: IDB-first + localStorage fallback, lazy migration, async API, TS1128 fix, 129.63 KB bundle) | **Accepted (Option 1)** | 2026-08-26 | P2 (Tier 3 literal cloud sync on-ramp, MVP上限) |
