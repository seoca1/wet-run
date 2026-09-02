# ADR-0061: Novel Integration Architecture

**상태**: Accepted (original 2026-06-30, normalized 2026-08-05)
**날짜**: 2026-06-30
**결정자**: 사용자
**우선순위**: P2

## 컨텍스트 (Context)

파이프라인(`Fiction/derivative/sprawl-trilogy/`)의 단편 65개(한글+영문)와 게임 측 모듈(전투, 매트릭스, 컷신, 인벤토리, 챕터) 간 통합이 산재되어 있음. 현재 통합:

- 챕터 JSON(`case.json` 등)이 excerpt 본문 직접 포함 (단편 발췌)
- 미션 JSON의 `story.source` 필드가 단편 stem 참조
- `verify_story_links.py` 가 매핑 검증

문제:
1. **확장성**: 새 단편 추가 시마다 코드 수정 필요
2. **중편/에피소드**: 현재 1:1 매핑 (미션 1개 = 단편 1개). 여러 챕터에 걸친 중편이나 에피소드 묶음 표현 불가
3. **반영 방식 불명**: 단편이 줄거리/이벤트/전투/아이템 중 어떤 영향을 미치는지 명시적 표현 없음
4. **런타임 디스패치 부재**: 단편을 게임 측으로 흘려보낼 일관된 API 없음

## 고려한 옵션

### Option A: 단편 → 챕터 excerpt 직접 하드코딩 (현재)

- **장점**: 단순. 검증 도구(v1) 이미 작동.
- **단점**: 새 단편마다 코드 수정. 분류 없음. 에피소드 묶음 표현 불가.

### Option B: Hook 기반 디스패치 (Adapter 패턴)

- **장점**:
  - 단편 → "훅 종류" 매핑 (NARRATIVE / EXCERPT / EVENT / COMBAT / ITEM / CINEMATIC)
  - 매핑을 데이터(매니페스트)로 분리 → 코드 수정 없이 새 단편/중편 등록
  - 런타임에 적절한 훅 실행 → AppState 또는 트리거 시스템과 연결
  - **확장 가능**: 중편/에피소드 → 매니페스트 entry 1개 추가
- **단점**: 추상화 레이어 추가 학습 비용

### Option C: 미션 시스템 완전 재설계

- **장점**: 더 큰 그림
- **단점**: 작업량 과다, 미션 시스템 다른 곳들 영향

## 추천 (Recommendation)

**Option B (Hook 기반 디스패치)** — 사용자 결정과 일치.

이유:
1. **4-layer** 명확 분리:
   - `catalog.py`: 디스크 자동 스캔 (frontmatter 파싱 포함)
   - `hooks.py`: 런타임 효과 종류 (이벤트/전투/아이템/씬) + 디폴트 액션
   - `manifest.py`: 단편 → 훅 매핑 (편집자가 JSON 으로 수정 가능)
   - `dispatcher.py`: AppState 와 통합, 모든 훅 실행
2. **확장 가능한 구조**:
   - 새 단편: 파일만 떨어뜨리면 카탈로그 자동 발견
   - 새 중편: 매니페스트에 entry 추가
   - 새 에피소드 묶음: `NovelFormat.EPISODE` + `episodes/` 디렉토리 (이미 enum 에 정의)
   - 새 훅 종류: `HookKind` enum + `register_hook_action()` 호출
3. **데이터 영향 없음**: 기존 미션/챕터 JSON 그대로. 단편 파일 그대로.
4. **테스트 가능**: 각 레이어 분리 테스트.

### 사용자 결정 사항

| 항목 | 결정 |
|---|---|
| **Hook 종류** | NARRATIVE / EXCERPT / EVENT / COMBAT / ITEM / CINEMATIC (6종) |
| **카탈로그** | 자동 스캔 (파일 시스템) — `NovelCatalog.refresh()` |
| **매니페스트** | 디폴트 추론 + JSON 오버라이드 양쪽 지원 |
| **포맷 확장** | SHORT_STORY / EPISODE / NOVELETTE / SERIAL (4종 enum 정의됨) |
| **런타임 반영** | 디스패처가 AppState 와 통합, dry-run 모드 지원 |

## 결과 (Consequences)

### 신규 코드 (~900 lines)

| 파일 | 줄수 | 책임 |
|---|---:|---|
| `novel/__init__.py` | 50 | 공개 API re-export |
| `novel/hooks.py` | 175 | HookKind enum, HookContext, HookResult, 디폴트 액션, 레지스트리 |
| `novel/catalog.py` | 365 | 자동 스캔, Frontmatter 파싱, NovelEntry/NovCatalog |
| `novel/manifest.py` | 280 | ManifestEntry, NovelManifest, JSON round-trip, infer_default_hook |
| `novel/dispatcher.py` | 160 | NovelDispatcher, DispatchReport, dispatch_hooks |
| `novel/integrator.py` | 85 | NovelRuntime, load_novel_runtime, dispatch_for_state |
| `tests/unit/test_novel.py` | 410 | 39 tests |

### 소설 → 게임 반영 설계도

```
   ┌─────────────────────────────────────────────────┐
   │  Fiction/derivative/sprawl-trilogy/short-stories/ │  ← 디스크 (단편)
   │       2026-06-23_case_jackout-30sec.md            │
   │       2026-06-23_case_jackout-30sec.ko.md         │
   └─────────────────┬───────────────────────────────┘
                     ▼
   ┌─────────────────────────────────────────────────┐
   │  catalog.py: NovelCatalog                        │
   │   • date prefix 제거 → stem 정규화                │
   │   • frontmatter 파싱 (title/author/tags/sources)  │
   │   • en / ko 페어 매칭                             │
   │   • NovelEntry list (stem, format, paths, ...)     │
   └─────────────────┬───────────────────────────────┘
                     ▼
   ┌─────────────────────────────────────────────────┐
   │  manifest.py: NovelManifest                       │
   │   • from_catalog(): 모든 entry의 디폴트 추론        │
   │   • infer_default_hook() — 키워드 기반             │
   │   • from_json() — 편집자 오버라이드                 │
   │   • resolve(stem) → ManifestEntry (primary, secondary) │
   └─────────────────┬───────────────────────────────┘
                     ▼
   ┌─────────────────────────────────────────────────┐
   │  dispatcher.py: NovelDispatcher                  │
   │   • dispatch(stem, language, app_state)            │
   │   • HookContext 생성                              │
   │   • 각 kind 마다 등록된 action 실행                 │
   └─────────────────┬───────────────────────────────┘
                     ▼
   ┌─────────────────────────────────────────────────┐
   │  hooks.py: 등록된 HookAction 함수들               │
   │   ┌─────────────────────────────────────────┐    │
   │   │ HookKind.NARRATIVE  → excerpt 표시       │    │
   │   │ HookKind.EXCERPT    → 인라인 단편 발췌    │    │
   │   │ HookKind.EVENT      → EventState 트리거   │    │
   │   │ HookKind.COMBAT     → ICE 종류 시드       │    │
   │   │ HookKind.ITEM      → 인벤토리 추가         │    │
   │   │ HookKind.CINEMATIC  → 그래픽 노블 큐       │    │
   │   └─────────────────────────────────────────┘    │
   └─────────────────┬───────────────────────────────┘
                     ▼
            ┌──────────────────────────────────────┐
            │        AppState / Engine              │
            │  • status_messages                    │
            │  • inventory                           │
            │  • active_event                        │
            │  • context_hint                        │
            │  • language                            │
            └──────────────────────────────────────┘
```

### 확장 가능성 (확인된 사용 예시)

#### 1. 새 단편 추가

```bash
# 1. 파일만 떨어뜨리기
$Fiction/derivative/sprawl-trilogy/short-stories/2026-07-01_new_story.md
$Fiction/derivative/sprawl-trilogy/short-stories/2026-07-01_new_story.ko.md

# 2. (선택) 매핑 오버라이드
$prototype/data/novel_overrides.json
{
  "new_story": {
    "primary": "combat",
    "secondary": ["item"],
    "ice_kind": "BLACK"
  }
}

# 3. 게임 코드 수정 없이 끝
runtime = load_novel_runtime(repo_root, manifest_overrides=overrides)
runtime.dispatcher.dispatch("new_story")
```

#### 2. 중편 (Novelette) 추가

```python
# format enum에 이미 정의됨:
class NovelFormat(StrEnum):
    SHORT_STORY = "short_story"
    EPISODE = "episode"
    NOVELETTE = "novelette"
    SERIAL = "serial"

# 카탈로그에 Novelette 파서 추가 (현재 미구현 — 단편 파서만)
# → 파일 시스템에 *_novelette.md 디렉토리 + manifest entry 1개
```

#### 3. 에피소드 묶음 추가

```python
# novel/catalog.py 에 EPISODE 포맷 추가:
#   $Fiction/derivative/sprawl-trilogy/short-stories/our_story.episodes.json
#   [{"id": "ep1", "title": "...", "path": "..."}]
#
# → 카탈로그가 자동으로 EPISODE 형식 감지
# → 매니페스트에서 1개 stem 으로 6개 hooks 트리거 가능
```

#### 4. 새 Hook 종류 추가

```python
# novel/hooks.py 에 추가:
class HookKind(StrEnum):
    # ... 기존 6종
    MUSIC = "music"  # 새 종류

# 새 액션 등록
def my_music_action(ctx, app_state):
    # ... music 큐 추가 ...
    return HookResult(ok=True)

register_hook_action(HookKind.MUSIC, my_music_action)
# → 매니페스트에서 "primary": "music" 로 사용
```

### 데이터 영향

**변경 없음**:
- `Fiction/derivative/sprawl-trilogy/short-stories/*.md` (65 파일)
- `prototype/data/missions/missions.json` (29 미션)
- `prototype/data/story/chapters/*.json` (3 챕터)
- 챕터 excerpt 본문 (코드에 직접 하드코딩된 발췌)

**신규 데이터 디렉토리** (선택):
- `prototype/data/novel_overrides.json` — 편집자 오버라이드
- `prototype/data/novel_manifest.json` — 디폴트 추론 외 매핑

### 깁슨 톤 유지

훅 이름 (NARRATIVE / EXCERPT / EVENT / COMBAT / ITEM / CINEMATIC) 은 **게임 메카닉** 레이블. 단편 본문 / 노드 라벨 / 컷신 텍스트는 모두 기존 깁슨 단어 차용 (Cyber Space, Data Vault, ICE Barrier, Jack-Out, Construct) 그대로.

### 테스트

| 파일 | 테스트 수 | 결과 |
|---|---:|:---:|
| `tests/unit/test_novel.py` | 39 | 39 PASS |
| catalog (10개) | — | ✅ |
| hooks (3) | — | ✅ |
| manifest (6) | — | ✅ |
| dispatcher (4) | — | ✅ |
| text_provider (2) | — | ✅ |
| integrator (4) | — | ✅ |
| extension (1) | — | ✅ |
| frontmatter 파서 (3) | — | ✅ |
| filename 파서 (3) | — | ✅ |
| infer_default_hook (5) | — | ✅ |
| Kwargs dispatch (5) | — | ✅ |

`ruff check`, `mypy strict` 통과.

## 영향 받는 항목

- `prototype/src/wet_run/novel/` — 신규
- `prototype/tests/unit/test_novel.py` — 신규
- `dashboard/` — 기존 (현재 영향 없음, 추후 Story/Novel 카드 갱신 가능)
- `decisions/README.md` — ADR 인덱스 갱신

## 관련 결정

- **ADR-0010** (i18n + Content Pipeline) — 단편 다국어 일관성
- **ADR-0017** (Mission Story Metadata) — 미션 ↔ 단편 직접 매핑 (현재 시스템)
- **ADR-0032** (Graphic Novel) — CINEMATIC 훅이 직접 활용 가능
- **ADR-0060** (Dungeon Exploration Redesign) — 매트릭스 내 단편 발췌 (EXCERPT)

## 변경 이력

- 2026-06-30: Draft 작성 (사용자 결정)
- 2026-06-30: Accepted (Option B)
- 2026-06-30: Phase 5 구현 완료 (39 tests PASS, ruff + mypy)

## 결과 (Consequences)

본 ADR은 사용자 결정 (질의 응답으로 confirm, 2026-08-05)에 의해 Accepted 로 confirmed. 증거 기반 검증 통과.

**구현 증거 (2026-08-05)**: `novel/` 패키지 6 .py 모듈 (catalog, dispatcher, hooks, integrator, manifest) + `data/story/arcs.json` (751KB). Novel Hook Dispatcher 미션 트리거 연동 (`engine/novel_integration.py`). STAGE BRIEFING/TRAVEL/BYPASS_SECURITY +3 단계 (10→13).

**변경 후 immutable**: 본 ADR 의 결정 사항은 변경 불가. 향후 수정 필요 시 신규 ADR 작성 (AGENTS.md §8).
