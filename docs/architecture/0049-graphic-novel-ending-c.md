# ADR-0049: 그래픽 노블 엔딩 C 추가 (3번째 결말)

**상태**: Accepted (auto-converted 2026-08-05, user-confirmed)
**날짜**: 2026-06-21
**결정자**: 사용자
**우선순위**: P2

## 컨텍스트 (Context)

ADR-0046 (엔딩 B) + ADR-0048 (메뉴/세이브 통합)으로 캐릭터당 2개 결말 (A/B) 지원.
깁슨 원작의 캐릭터들은 **세 가지 결말 패턴**을 따름:

- **Case (Novice)**: A=수락 / B=거절 / **C=소멸** (이 도시를 떠남, 새로운 정체성)
- **Sil (Veteran)**: A=브로드캐스트 / B=내부자 / **C=망각** (wetware 재배선, 자발적 기억소거)
- **Kas (Heretic)**: A=침묵 안에서 / B=그림자로 / **C=파괴** (T-A를 내부에서 무너뜨림, 자신도 함께)

엔딩 C는 **replayability × 1.5** 효과 + **깁슨 톤 "완전한 상실"** 테마 강화.

## 고려한 옵션

### Option 1: 엔딩 C 추가 (6 씬, 2× 확장) ✓ 선택

- **설명**: 캐릭터당 2 씬 × 3 캐릭터 = 6 씬 추가. ADR-0048에서 만든 메뉴/세이브 인프라가 이미 "ending" 필드를 str로 받으므로 자연스럽게 확장.
- **장점**:
  - 기존 인프라 그대로 활용 (menu 확장만)
  - "끝"의 결말 — A=희망, B=회색, C=완전한 상실 (깁슨 톤)
  - 9개 결말 조합 (3 chars × 3 endings) = **replayability × 3**
- **단점**:
  - 6 신규 씬 (~2300 chars × 6 = ~14000 chars)
  - 메뉴 옵션 4개로 증가 (시각 공간 +1)

### Option 2: 엔딩 C 추가 + 4× 확장 (ADR-0041 스타일)

- **설명**: 6 씬 × 4× 확장 = 24 씬 대화.
- **장점**: 콘텐츠 풍부.
- **단점**: 작업량 4배. 테스트 4배. 사용자가 명시적으로 4× 확장을 요청하지 않음.

### Option 3: 신규 콘텐츠 안 만들고 기존 인프라만 노출

- **설명**: 메뉴에 C 옵션 추가하되, 씬은 비어있음.
- **장점**: 작업량 0.
- **단점**: **Pillar 1 위반** — 메뉴에 있는 옵션이 작동하지 않으면 신뢰 파괴.

## 추천 (Recommendation)

**Option 1**. 자연스러운 확장 + 깁슨 "상실" 톤 + 기존 인프라 활용.

## 사용자 결정 (Decision)

[x] Option 1 (사용자 명령: "차례대로 이어서 진행")

## 결과 (Consequences)

### 신규 씬 (6개)

| 캐릭터 | 씬 ID | 제목 (EN) | 제목 (KO) | dialogue | EN chars |
| --- | --- | --- | --- | --- | --- |
| Case | 07_disappear | THE DISAPPEARANCE | 소멸 | 3 | ~2300 |
| Case | 08_freeside | THE MORNING AFTER | 다음 날 아침 | 2 | ~1800 |
| Sil | 07_erase | THE ERASE | 소거 | 3 | ~2300 |
| Sil | 08_blank | THE BLANK | 백지 | 2 | ~1800 |
| Kas | 07_weapon | THE WEAPON | 무기 | 3 | ~2300 |
| Kas | 08_burn | THE BURN | 연소 | 2 | ~1800 |

**총**: 6 씬, 15 dialogue, ~12,800 EN chars + KO 병행

### 테마 (깁슨 톤)

- **Case C — 소멸/도주**: "The sky above the port was the color of television, tuned to a dead channel." — Case의 마지막 의식. 스프롤을 떠나 Freeside로. 정체성 말소.
- **Sil C — 망각**: 자발적 기억소거. wetware 클리닉. 수술대 위의 마지막 생각. 깨어나면 모든 것이 비어있음.
- **Kas C — 파괴**: 가족을 내부에서 무너뜨리는 무기. 방송 송출. 가족이 타오르는 것을 지켜봄. 자신도 함께.

### 메뉴 변경

- **GRAPHIC_NOVEL_ENDING_MENU**: 3 옵션 → 4 옵션 (A/B/C + BACK)
- 캐릭터 모드에서만 표시 (prologue은 항상 A)
- **N1=A, N2=B, N3=C, N4=back** (key remap)

### Save 변경

- **GN_SAVE_VERSION 1.1.0 → 1.2.0** (additive)
- `GNProgress.ending` "A"/"B"/"C" 모두 지원 (이미 str이라 변경 없음)
- `from_dict`: "C"도 valid, 그 외 → "A"
- 마이그레이션: v1.1.0 (ending="B") → v1.2.0 그대로 로드

### 데이터 변경

- `data/scenes/{case,sil,kas}/07_*.json` × 3
- `data/scenes/{case,sil,kas}/08_*.json` × 3

### 스크립트 변경

- `play.py` / `demo.py` / `demo_all.py` / `graphic_novel.py`: cache key에 ending 포함 (이미 적용됨)
- `--ending {A,B,C}` CLI 확장
- `_ENDING_DESCRIPTIONS`에 (char, "C") 항목 추가

### 영향 받는 항목

- `design/scenario/graphic-novel.md` (§11 endings에 C 추가)
- `decisions/0044-graphic-novel-save.md` (Save 1.2.0 정책)
- `decisions/0046-graphic-novel-ending-b.md` (엔딩 시스템 일반화)
- `decisions/0048-gn-ending-menu-and-save-migration.md` (메뉴 옵션 4개로)
- `tests/unit/test_graphic_novel_ending_menu.py` (4 옵션 + key remap)
- `tests/unit/test_graphic_novel_content_quality.py` (씬 C 검증 추가)
- 신규: `tests/unit/test_graphic_novel_ending_c.py`

## 신규 테스트

- `tests/unit/test_graphic_novel_ending_c.py` (~25 tests):
  - 메뉴: 4 옵션 (N1=A, N2=B, N3=C, N4=back)
  - 렌더: _ENDING_DESCRIPTIONS[("novice","C")] 등 KO/EN 라벨
  - 체인 로드: load_scene_chain(ending="C") — 2 씬 (case) / 2 씬 (sil) / 2 씬 (kas)
  - Save: v1.2.0 with ending="C" round-trip
  - Save migration: v1.1.0 with ending="B" → v1.2.0 → "B" preserved
  - SceneData.ending="C" field acceptance
  - Visual: ending C chain load returns distinct scenes from A/B

## 변경 이력

- 2026-06-21: Draft 작성
- 2026-06-21: Accepted (구현 완료)

### 구현 결과

**Code**:
- `data/scenes/case/07_disappear.json` (THE DISAPPEARANCE)
- `data/scenes/case/08_freeside.json` (THE MORNING AFTER)
- `data/scenes/sil/07_erase.json` (THE ERASE)
- `data/scenes/sil/08_blank.json` (THE BLANK)
- `data/scenes/kas/07_weapon.json` (THE WEAPON)
- `data/scenes/kas/08_burn.json` (THE BURN)
- `src/wet_run/engine/graphic_novel_view.py`: `_ENDING_DESCRIPTIONS` 확장 (char × C), `available_endings()` 동적 옵션, `get_gn_ending_menu_options` N 옵션 지원
- `src/wet_run/engine/menu.py`: `handle_graphic_novel_ending_menu_input` 동적 키 매핑 (N1=A..N{count}={chr('A'+count-1)}, N{count+1}=back)
- `src/wet_run/engine/graphic_novel_save.py`: `GN_SAVE_VERSION 1.1.0 → 1.2.0`, `from_dict` accepts "C", forward-compat unknown → "A"
- `src/wet_run/engine/graphic_novel_audio.py`: SCENE_SOUND_MAP 확장 (theme_* + movement_neon_hum alias)
- `scripts/play.py`: `--ending {A,B,C}` CLI flag, `_action_graphic_novel_ending_menu` accepts C
- `scripts/graphic_novel.py`: `--ending {A,B,C}` choices

**Tests** (62 신규):
- `tests/unit/test_graphic_novel_ending_c.py`: 6 scenes exist + ending="C" field + available_endings (3 chars × A/B/C) + descriptions + menu 4 options + input N1=A/N2=B/N3=C/N4=back + Save 1.2.0 + round-trip + migration from v1.1.0 + load_scene_chain filter + scene quality (length 1000-2800 + duration 30ms/char + KO translation)
- `tests/unit/test_graphic_novel_view.py` 업데이트: list_scenes → 8 scenes per character
- `tests/unit/test_graphic_novel_ending_menu.py` 업데이트: N3=C, N4=back, 4 options
- `tests/unit/test_graphic_novel_audio.py` 업데이트: unique cues ≥15 (was ==15)

**검증**:
- pytest: **2518 passed** (2420 → 2518, +98)
- ruff check: All checks passed
- ruff format: 198 files already formatted
- mypy strict: Success: no issues found in 94 source files

**시각 검증**:
- EN: `[1] ENDING A — ... [2] ENDING B — ... > [3] ENDING C — The Disappearance — vanishing from the Sprawl`
- KO: `[1] 엔딩 A — ... [2] 엔딩 B — ... > [3] 엔딩 C — 소멸 — 도시를 떠나 새로운 정체성`
- 3 chars × 4 options 모두 정상
- N3 → "C", N4 → "back" 매핑 정확

### Auto-conversion Confirmation (2026-08-05)

본 ADR은 사용자 결정 (질의 응답으로 confirm, 2026-08-05)에 의해 auto-convert 완료. 증거 기반 검증 통과.

**구현 증거 (2026-08-05)**: ADR-0046/0048 (엔딩 B/메뉴 통합) + ADR-0104 (3 슬롯 세이브) already Accepted. ADR-0049는 캐릭터당 3번째 결말 (Case=소멸, Sil=망각, Kas=파괴) 추가 — `gn_menu.py` ending selection에서 처리.

**변경 후 immutable**: 본 ADR 의 결정 사항은 변경 불가. 향후 수정 필요 시 신규 ADR 작성 (AGENTS.md §8).
