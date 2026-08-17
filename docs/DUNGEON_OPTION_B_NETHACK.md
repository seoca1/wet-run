# Dungeon Exploration Design — Option B-Nethack

> **NetHack 클래식 스타일 + 사이버스페이스 이펙트 오버레이**
> **2026-06-30 채택**: 옵션 B+ (철회) → 옵션 B-Nethack
> **참조**: `DUNGEON_EXPLORATION_REVIEW.md`, 검증 체크리스트.

---

## 1. 철회 노트: 옵션 B+ → 옵션 B-Nethack (2026-06-30)

옵션 B+ 의 다음은 사용자 결정에 반하여 자동 폐기됨:

- ❌ `NodeState` 4단계 enum (`?`/`·`/`◆`/`✓`)
- ❌ `#` 영구 루트 표시
- ❌ `←`/`→`/`↔` 백트래킹 방향 인디케이터
- ❌ `PathEdge` 자료구조
- ❌ `VisitType` enum (FIRST/REVISIT/BACKTRACK)

사유: 옵션 B+ 는 사이버스페이스 분위기를 **맵 글리프에 코딩**했음. 사용자 결정은 **맵은 게임플레이에 최적화**, 사이버스페이스는 **이펙트로 분리**.

---

## 2. 핵심 디자인 결정

| 결정 | 값 |
|---|---|
| **맵 스타일** | NetHack 클래식 (벽 `-`/`\|`/`+`, 통로 `─`/`│`/L-자) |
| **단위** | 카드 단위 (1 룸 = 1 셀) |
| **이동** | 4방향 N/S/E/W (↑↓←→) |
| **Fog** | 단순화: 현재 + 인접 + 방문한 방 |
| **룸 종류** | 7종 (Entry/Exit/Data/ICE/NPC/Router/Core) — 기존 유지 |
| **색상** | 룸종류별 (ICE=빨강, DATA=골드, NPC=마젠타, EXIT=녹색, CURRENT=시안) |
| **사이버스페이스** | **이펙트 레이어로 분리** (맵 글리프에 추상화 X) |

---

## 3. NetHack 매핑

| NetHack | 우리 게임 | 현재 dungeon_view.py |
|---|---|---|
| `@` (player) | `▶` (current room marker) | ✅ |
| `#` (wall) | `-` / `\|` / `+` (room border) | ✅ |
| `.` (corridor floor) | `─` / `│` + `┘` `└` 코너 | ✅ |
| `D` (dragon) | `!` (ICE) | ✅ |
| `$` (gold) | `$` (DATA) | ✅ |
| `:` (scavenged tile) | `·` (Router) | ✅ |
| `+` (closed door) | (없음 — 사변) | (없음) |

**결론**: 우리 `dungeon_view.py` (515 lines)는 이미 NetHack 클래식에 부합. 변경 최소.

---

## 4. 사이버스페이스 이펙트 레이어 (Phase 1.5)

맵 글리프에 사이버스페이스 추상화 X. 4 트리거:

| 트리거 | 함수 | 효과 | 깁슨 톤 |
|---|---|---|---|
| **매트릭스 진입** | `spawn_jackin_glitch` | 글리치 particle + shake + 3-phase 시네마틱 | "JACKING IN..." / "SCANNING HOST..." / "CYBERSPACE LOADED" |
| **룸 이동** | `spawn_room_flash` | 짧은 색상 플래시 + spark shower | 80ms 색상 변화 |
| **DATA 획득** | `spawn_data_acquired` | 골드 particle 폭발 + 2-phase 시네마틱 | "DATA FRAGMENT RECOVERED" / "+ CREDITS + REPUTATION" |
| **EXIT 도달** | `spawn_jackout_whiteout` | white-out + 3-phase 시네마틱 | "JACKING OUT..." / "CONNECTION SEVERED" / "MATRIX CLOSED" |

### 4-1. 구현 위치

- **신규 함수**: `prototype/src/wet_run/combat/effects.py`
  - `spawn_jackin_glitch(effects: CombatEffects)` — 진입 글리치
  - `spawn_room_flash(effects, color)` — 룸 전환
  - `spawn_data_acquired(effects, x, y)` — 데이터 파티클
  - `spawn_jackout_whiteout(effects)` — 탈출 whiteout
- **앱 통합**: `prototype/src/wet_run/engine/app.py:_maybe_spawn_jackin_glitch`
- **토글**: 키 `D` (MATRIX 화면에서만 동작)
- **데이터 흐름**: `AppState.combat_effects` → `combat_view.py` 가 렌더링 시 overlay

### 4-2. 레이어 통합

기존 5-Layer VFX 시스템 (ADR-0018)에 통합:
- **Layer 1** (Hit feedback): `spawn_hit_effects`, `spawn_critical`, `spawn_jackin_glitch`
- **Layer 3** (ICE-type cinematics): `spawn_ice_intro`, `spawn_ice_death`
- **신규 Layer 6** (Matrix-atmosphere): `spawn_jackin_glitch`, `spawn_room_flash`, `spawn_data_acquired`, `spawn_jackout_whiteout`

---

## 5. 코드 변경 요약

| 파일 | 변경 | 줄수 |
|---|---|---|
| `engine/state.py` | `dungeon_mode: bool = False` 필드 | +7 |
| `engine/app.py` | `dungeon_view` import + 키 `D` 토글 + `_maybe_spawn_jackin_glitch` 헬퍼 | +27 |
| `engine/dungeon_view.py` | 변경 없음 (이미 NetHack) | 0 |
| `combat/effects.py` | VFX 4종 추가 (`__all__` 갱신) | +106 |

**총 코드**: ~140 줄.

---

## 6. 테스트

| 파일 | 테스트 수 | 통과 |
|---|---:|:---:|
| `tests/unit/test_dungeon_view.py` | 8 | ✅ 8/8 |
| `tests/unit/test_combat_vfx.py` | 12 | ✅ 12/12 |

검증 시나리오:
- `test_default_is_false` — `dungeon_mode` 기본값
- `test_d_toggles_dungeon_mode_true` / `test_d_toggles_back_to_false` — 키 D 토글
- `test_shift_d_does_not_toggle` — Shift+D 는 토글 안 함
- `test_d_appends_status_message` — 상태 메시지 표시
- `test_render_dungeon_matrix_does_not_raise` — 렌더 스모크
- `test_populates_particles` — VFX 파티클 생성
- `test_sets_cinematic` / `test_cinematic_data_acquired` / `test_three_phase_cinematic` — 시네마틱 검증
- `test_triggers_shake_and_flash` / `test_white_flash` / `test_triggers_gold_flash` — shake/flash 검증
- `test_full_jackin_to_jackout_cycle` — 풀 사이클 통합

---

## 7. 로드맵

```
[Phase 1]   dungeon_view 활성화 (1일) ✓ DONE
   ├─ state.py dungeon_mode 필드
   ├─ app.py 키 D + 분기
   └─ 테스트 8개
   ↓
[Phase 1.5] VFX 오버레이 (1일) ✓ DONE
   ├─ combat/effects.py 4종 spawn 함수
   ├─ app.py _maybe_spawn_jackin_glitch
   └─ 테스트 12개
   ↓
[Phase 2]   절차적 BSP 미로 (3-5일) [다음]
[Phase 3]   미션 → 룸 매핑 (1-2일)
[Phase 4]   ECS 통합 (선택)
[Phase 5]   단편 연동 (선택)
```

---

## 8. 사용자 결정 사항

| 항목 | 결정 |
|---|---|
| **맵 스타일** | NetHack 클래식 (벽/통로/룸) |
| **사이버스페이스** | 이펙트 레이어 (VFX + ASCII 노이즈) |
| **맵 최적화 대상** | 탐색 / 획득 / 전투 / 레벨업 |
| **Fog 정책** | 옵션 B (현재 + 인접 + 방문) — NetHack 클래식 |
| **룸 종류** | 7종 (기존 유지) |
| **VFX 인프라** | 기존 5-Layer VFX 활용 |
| **이전 옵션 B+** | 자동 폐기 (철회 노트 §1) |
| **토글 키** | `D` (matrix ↔ dungeon) |

---

## 9. 다음 단계

### 9-1. 즉시 (Phase 2)

절차적 BSP 미로 생성:
1. `matrix/dungeon_generator.py` 강화
2. 미션 grade 1-5 → 룸 수 매핑
3. 캐릭터별 (novice/veteran/heretic) 분기
4. 시드 기반 재현성

### 9-2. 후속

- 미션 29개 → 룸 그래프 자동 매핑 (`missions_to_rooms`)
- 단편 발췌 매핑 (Phase 5)
- ADR-0060 작성 (`decisions/0060-dungeon-exploration-redesign.md`)

---

## 10. 참고 자료

| 자료 | URL |
|---|---|
| Cogmind 공식 | https://www.gridsagegames.com/cogmind/ |
| Cogmind 미디어 (ASCII 스크린샷) | https://www.gridsagegames.com/cogmind/media.html |
| NetHack Wiki | https://nethackwiki.com/wiki/NetHack |
| Brogue RogueBasin | https://www.roguebasin.com/index.php?title=Brogue |
| Wikipedia Roguelike | https://en.wikipedia.org/wiki/Roguelike |

---

*Generated: 2026-06-30 — 옵션 B-Nethack 채택, 옵션 B+ 폐기*
*Phase 1 + 1.5 완료, Phase 2 준비 중*
