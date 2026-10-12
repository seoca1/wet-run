# ADR-0213: Far Grid — 비-깁슨 사이버펑크 별도 영역 확장

**상태**: Accepted
**날짜**: 2026-10-07
**결정자**: 사용자 (2026-10-07 승인 — Option 1)
**우선순위**: P2 (세계관 확장 — 캐논 무결성 선행)
**관련**:
- [ADR-0054 (Fiction) — SF Collection Expansion Pilot](../../../../Fiction/decisions/0054-sf-collection-expansion.md) — 원천 인제스트 거버넌스
- `docs/wiki/world/cyberpunk-sources.md` — 사이버펑크 서브셋 prep (Hardwired / Halo / True Names / Otherland + adjacent)
- AGENTS.md §8 — 타 사이버펑크 톤/용어 차용 금지 (본 ADR 의 정합 대상)

## 컨텍스트 (Context)

Fiction `SF_F` 컬렉션에 Gibson 바깥 사이버펑크 원천이 있다 (W.J. Williams Hardwired, Maddox Halo, Vinge True Names, T. Williams Otherland — `cyberpunk-sources.md` 전수). wet-run 에 연결하고 싶다.

제약:
1. **§8**: 타 사이버펑크 작품의 톤/용어 차용 금지 — Sprawl 캐논에 섞으면 위반.
2. **Fiction charter**: Gibson-only — xauthors 인제스트는 ADR-0054 Accepted 이후에만.
3. **캐논 오염 불가역성**: 한 번 섞인 세계관은 되돌리기 어렵다. 격리가 합병보다 싸다.

그래서 방향은 "합치기"가 아니라 "별도 영역으로 확장"이다.

## 고려한 옵션

### Option 1: Far Grid — 별도 지역/허브 격리 (추천)
- **설명**: 게임 내 신규 영역 `far-grid`. Sprawl 맵과 분리된 허브/던전 풀, 입장 게이트 (예: Sprawl arc 클리어 후 해금 또는 메뉴 별도 진입). 미션에 `source_universe: "sprawl" | "far-grid"` 필드 1개 추가. Fiction 측도 네임스페이스 분리 (Gibson `wiki/` untouched).
- **장점**:
  - §8 정합 — 섞지 않으므로 차용 금지 위반 없음 ("여긴 다른 세계" 명시)
  - 원복 가능 — 영역 통째로 on/off 가능, 캐논 오염 0
  - ADR-0054 pilot 구조와 정합 (LeGuin → Far Grid 첫 입주 후보)
- **단점**:
  - 허브/게이팅 최소 구현 필요 (빈 껍데기 영역 금지 — 입장 조건 + 3개 이상 미션 세트)
  - `source_universe` 스키마 + resolver 분기 추가 (missions JSON, `data_loaders.ts` 계열)
- **Pillar 정합**:
  - P1 (The Run): 직접 영향 없음 (런 구조 동일, 무대만 분리)
  - P2 (The Matrix): 던전 풀 분리 — Sprawl 토폴로지와 독립 시드
  - P3 (The Flatline): 사망/계승 동일 규칙 (공유)
  - P4 (The Build): 덱/장비는 공유, far-grid 전용 드롭은 후순위
  - P5 (The Style): 영역별 스타일 분리 선언 — Sprawl = Gibson cold/detached, Far Grid = 출처별 톤 + "외부 세계" 프레임

### Option 2: Anthology 팩 — 미션 묶음만
- **설명**: 지역 없이 far-grid 태그 미션 세트만. Sprawl 허브에서 수주.
- **장점**:
  - 구현 최소 (데이터만, 허브 불필요)
- **단점**:
  - 세계관 몰입 약함 — Sprawl 한복판에서 비-깁슨 톤이 섞여 §8 경계가 흐려짐
  - 격리 선언이 태그 한 줄에 의존 (깨지기 쉬움)
- **Pillar 정합**:
  - P1 (The Run): 직접 영향 없음
  - P2 (The Matrix): 영향 없음
  - P3 (The Flatline): 영향 없음
  - P4 (The Build): 영향 없음
  - P5 (The Style): ⚠️ 톤 혼재 리스크 — Sprawl 메뉴에서 비-깁슨 미션 노출

### Option 3: 병렬 캠페인 — 별도 주인공선
- **설명**: Far Grid 전용 자키/아크/엔딩. 사실상 두 번째 게임.
- **장점**:
  - 격리 최강, 창작 자유도 최대
- **단점**:
  - Tier 5급 공수 — 캐릭터/아크/밸런스 전부 별도
  - 현 로드맵 (Tier 1-4 + IDB) 과 경합
- **Pillar 정합**:
  - P1 (The Run): 아크 구조 복제 필요
  - P2 (The Matrix): 던전 풀 복제
  - P3 (The Flatline): 공유 가능
  - P4 (The Build): 진행 분리 필요
  - P5 (The Style): 분리 용이하나 작업량 최대

## 추천 (Recommendation)

**Option 1 (Far Grid)**. §8을 지키면서 확장하는 유일한 안이고, ADR-0054 pilot (LeGuin) 의 입주처가 된다. 첫 입주: True Names (Vinge, txt 확보済 — 압축 해제 불필요) + Hardwired (Williams, txt 4건) — 둘 다 Far Grid 개척 세트로 충분.

선행 조건 (순서 엄수):
1. Fiction ADR-0054 Accepted (원천 인제스트 거버넌스)
2. 본 ADR Accepted (영역 설계)
3. Far Grid 구현 (허브 + 게이팅 + 미션 세트 ≥3 + `source_universe` 스키마)

## 사용자 결정 (Decision)

[x] Option 1 (Far Grid — 2026-10-07 확정)
[ ] Option 2 (Anthology 팩)
[ ] Option 3 (병렬 캠페인)
[ ] 기타: ___
[ ] Defer (다음 단계로 미룸)

## Implementation Status (2026-10-11)

**Status**: ✅ Implemented (Phase 1)

**Evidence**:
- `web/src/core/types.ts` — `Mission.source_universe` + `story?` fields, `ScreenKind "far_grid_hub"`
- `web/src/core/data_loaders.ts` — `parseMission` literal validation + sprawl default + story passthrough
- `web/src/core/missions_filter.ts` — `filterMissionsByUniverse` (frozen, undefined→sprawl)
- `web/src/renderer/menu.ts` — `FAR GRID` entry (14 options)
- `web/src/renderer/far_grid_hub.ts` — hub screen + `[Source: stem]` line
- `web/src/main.ts` — menu/input/draw wiring + filtered-index launch mapping
- `web/src/data/missions.json` — 3 Far Grid missions (far_grid_prelude, don_mac_audit, deathspiders_news)
- Gates: typecheck 0 · lint 0 errors · vitest 112 files / 2687 passed · build OK

**Notes**: Phase 1 display-only (stem strings, no resolution). Hardwired missions + gate logic deferred.

## Implementation Status (2026-10-12 — Phase 1b)

**Status**: ✅ Implemented (Phase 1b — content + hygiene)

**Evidence**:
- `web/src/data/missions.json` — 6 Far Grid missions (True Names 3 + Hardwired 3: warren_meadow, blue_silk_wall, maidens_first_run)
- `web/src/main.ts` — inline universe filters replaced with `filterMissionsByUniverse` helper (single source of truth)
- Gates: typecheck 0 · lint 0 errors · vitest 112 files / 2687 passed · build OK

**Notes**: Gate logic (entry condition) still deferred — Phase 2 decision item. Story-stem resolution still display-only.

## Implementation Status (2026-10-12 — Phase 2 gate)

**Status**: 🟡 Partial (gate shipped; story resolution + progression still open)

**Evidence**:
- `web/src/core/far_grid_gate.ts` (new) — pure unlock helpers, localStorage `wetrun_far_grid_unlocked`, default-fill (no save migration)
- `web/src/core/state_actions.ts` — `applyLootAction` mission-complete path sets flag when `arc === 1`
- `web/src/renderer/menu.ts` — FAR GRID renders `(locked)` + gray when flag absent
- `web/src/main.ts` — locked selection blocked with status message; defense-in-depth bounce in `far_grid_hub` input + render paths
- `web/tests/far_grid_gate.test.ts`, `menu_far_grid_gate.test.ts`, `far_grid_gate_signal.test.ts` — 25 new tests
- Gates: typecheck 0 · lint 0 errors · vitest 115 files / 2712 passed · build OK

**Notes**: Unlock fires on ANY Sprawl arc-1 mission win (no arc-final/completion-history concept exists in the codebase; inventing one was out of scope). Locked message states the implemented semantics verbatim. Tightening to full-arc clear needs completion tracking — Phase 3 candidate.

## Implementation Status (2026-10-12 — Wave 2 content)

**Status**: 🟡 Partial (14 missions + briefings + hub resolution; dungeon-pool separation still open)

**Evidence**:
- `web/src/data/missions.json` — 47 total, 14 far-grid (Wave 2 = TN 4: mailmans_last_letter, pollack_after_dark, limeys_long_game, wileys_gate + HW 4: hetmans_meeting, maurice_princes, dodgers_office, tin_soldiers_end)
- Grade spread 1–4 across the 14 (rookie 9 / intermediate 2 / focused 1 / deep 1 / hard 1); all zones stay `precursor`; no mission above grade 4 (Sprawl owns endgame)
- `Mission.briefing?: string` + `parseMission` passthrough (`types.ts`, `data_loaders.ts`) — 1–2 sentence EN briefings adapted from each story's `plot_summary.en`
- `web/src/renderer/far_grid_hub.ts` — selected-mission briefing block (wrapped, truncated, footer-safe)
- Tests: count assertions 39→47; `far_grid_hub.test.ts` +8 briefing cases
- Gates: typecheck 0 · lint 0 errors · vitest 115 files / 2720 passed · build OK

**Notes**: Seed dupes {555, 7, 444} are pre-existing Sprawl pairs (aleph_fragment/wintermute_negotiation, ice_run/sally_returns_arc3, voodoo_loa_encounter/ta_defection) — untouched, cleanup candidate.

## Implementation Status (2026-10-12 — Pillar-2 verification)

**Status**: 🟡 Partial (pool separation verified by construction + test; Wave 3 mapping still open)

**Evidence**:
- Layout RNG = `mulberry32(matrix_seed + mission-id hash)` (`applyMissionIdSeed`, `dungeon_layout.ts:411+`) — every mission id owns an independent topology stream, so no shared pool can exist between universes.
- `web/tests/dungeon_pool_separation.test.ts` (new, 4 tests) — same-seed/different-id divergence (incl. the 555/7/444 dupe pairs), far-grid vs sprawl divergence, determinism, null-id fallback.
- Gates: typecheck 0 · lint 0 errors · vitest 116 files / 2724 passed · build OK

**Notes**: Seed-dupe cleanup closed as non-issue (ids differentiate streams). Remaining: full-arc-clear gate tightening.

## Implementation Status (2026-10-12 — Wave 3 full roster)

**Status**: ✅ Implemented (content-complete: all 20 xauthors stories playable)

**Evidence**:
- `web/src/data/missions.json` — 53 total, 20 far-grid (Wave 3: moat_burned_blue, erythrinas_list, rogers_backyard, arkady_in_orange, dirtgirl_dispatch, firebuds_chair; all with briefings, grades 1–4, seeds 202624–202629)
- Correction: prior notes said "Wave 3 (26 unmapped)" — counting error. Only 20 xauthors stories exist (10 TN + 10 HW); 14 were mapped, 6 remained, now 0 unmapped. Agent correctly refused to invent missions for nonexistent stories (§8).
- Hub scroll-window unnecessary: 20-item list fits the smallest 50-row grid with briefing block intact.
- Tests: count assertions 47→53; far-grid ID list 14→20
- Gates: typecheck 0 · lint 0 errors · vitest 116 files / 2724 passed · build OK

## 결과 (Consequences) — 2026-10-07 Option 1 확정

- `cyberpunk-sources.md` Status: Prep → Ready (입주처 확정)
- 선행: Fiction ADR-0054 Accepted → Far Grid 구현 세션 (허브 + 게이팅 + 미션 세트 ≥3 + `source_universe` 스키마)
- 첫 입주 후보: True Names (Vinge) + Hardwired (Williams)
- Sprawl 캐논 직접 편입은 본 ADR 범위 밖 (별도 설계 결정 필요, §8 유지)
