# ADR-0020: Fog of War + Exploration (안개 / 탐험 메카닉)

**상태**: Accepted (auto-converted 2026-08-05, user-confirmed)
**날짜**: 2026-06-18
**결정자**: 사용자
**우선순위**: P1
**상위 결정**: ADR-0005 (Cyberspace), ADR-0011 (Portraits), ADR-0012 (PPL/ZDR), ADR-0017 (Mission)

## 컨텍스트

사용자 질문 (2026-06-18):
> "전투에 진입하지 않은 상태의 게임 화면을 설명해봐. 맵 요소가 있어? 사이버스페이스를 표현하기 위해 비가시지역을 탐험하는 요소가 필요할까?"

기존 (2026-06-18까지):
- 매트릭스 노드 그래프가 **완전히 보임** (모든 노드, 모든 연결, 모든 ZDR)
- 미니맵 없음, breadcrumb 없음
- "탐험" 메카닉 없음 — 처음부터 모든 정보 공개

문제:
- **탐험의 부재**: 매트릭스 전체가 *공개* → "발견"의 재미 없음
- **전략적 깊이 부족**: "다 보이는데 무슨 결정?" → 퍼즐은 쉽지만 흥미는 떨어짐
- **깁슨 톤과 거리**: "The matrix is vast, you are small" — 하지만 화면은 *작지도*, *방랑하지도* 않음
- **Replayability 약화**: 매번 같은 그래프 → 보지도 않고 같은 길

## 사용자 결정 (2026-06-18)

[x] **Light Fog (현재 + 인접) — Recommended**

## 결정

### Light Fog of War

3단계 가시성:

| 클래스 | 표시 | 정보 |
| --- | --- | --- |
| `current` | 강조 박스, `>` 마커 | 전체 (라벨, ZDR, PPL vs ZDR status) |
| `adjacent` | 외곽선 박스 | kind (Data, ICE, Router) — ZDR/PPL 미공개 |
| `discovered` | 박스 | 전체 (방문한 적 있음) |
| `unknown` | `?` placeholder | 없음 |

### 연결선 가시성

- `current ↔ adjacent` / `current ↔ discovered`: 실선 `─`
- `discovered ↔ discovered`: 실선
- `current → unknown` / `discovered → unknown`: **숨김** (안개)

### 특수 노드

- **Entry 노드**: 시작 시 *discovered* (있어야 시작 가능)
- **Exit 노드**: 항상 *visible* (도착해야 하므로) — 하지만 ZDR은 진입 전 비공개

### 미니맵 (top-right)

```
  Map:
  ● E  ?  ?
        ?  ?
       ● X
```

`●` = discovered/current, `?` = unknown, `X` = exit (always shown)

### Breadcrumb (bottom)

```
Path: E → R₀ → I₀
```

방문한 경로를 약하게 표시 (회색).

### Probe program (ADR-0003 확장)

- T1 program, 1 AP
- 인접 노드 1개의 **ZDR** 공개 (전체 정보)
- 사용 후 `scanned` 표시
- 디폴트는 *kind*만 (ZDR 미공개)

## 결과 (Consequences)

### Pillar 정합

- **P1 (The Run)**: 한 런 안의 *방랑* — 자키가 매트릭스를 *탐험*.
- **P2 (The Matrix)**: 매트릭스 안의 *데이터*를 발견 — Pillar 2 정합.
- **P3 (The Flatline)**: 안개로 인한 *불확실성* → 위험한 노드 회피의 *무게* 강화.
- **P4 (The Build)**: Probe 같은 *탐색 도구* — Pillar 4 표현.
- **P5 (The Style)**: 깁슨의 "matrix is vast, you are small" — *작고 헤매는* 자키.

### 기존 ADR 영향

- **ADR-0005 (Cyberspace)**: 보강. 노드 그래프가 *부분 가시*로 변경.
- **ADR-0003 (RT-MS)**: Probe program 추가.
- **ADR-0012 (PPL/ZDR)**: PPL/ZDR 비교는 *current 노드*에서만 표시.
- **ADR-0011 (Portraits)**: 외곽선 박스도 ASCII 기호로 표현.

### 디자인 영향

- **`design/systems/exploration.md`** (신규) — 탐험 시스템 명세
- **`design/systems/hacking.md`** (확장) — 매트릭스 가시성 섹션
- **`testcases/systems/exploration.md`** (신규) — TC-EXP-001~008

### 구현 영향 (Phase 6+)

- `matrix/exploration.py` (신규) — `ExplorationState` (current, discovered, scanned)
- `engine/matrix_view.py` 확장 — fog 렌더링, 미니맵, breadcrumb
- `matrix/graph.py` 확장 — `is_connected`, `adjacent_to` (이미 존재)

### Phase 5 범위

- **데이터 + 문서만**: ADR + design + testcases
- **구현 없음** (이번 세션에서 같이 구현)

### Phase 6+ 범위

- 미니맵 인터랙션 (확대, 스크롤)
- 추가 안개 해제 메카닉 (특정 construct, 특정 미션)
- "Scanned" 영구 표시 (한번 본 노드는 끝까지 보임)

## 영향 받는 항목

- `design/systems/exploration.md` (신규)
- `design/systems/hacking.md` (확장)
- `testcases/systems/exploration.md` (신규)
- `matrix/exploration.py` (신규)
- `engine/matrix_view.py` (확장)
- `decisions/0005-cyberspace-representation.md` (연계)

## 관련 결정

- ADR-0005 (Accepted) — Cyberspace
- ADR-0003 (Accepted, Revised) — RT-MS
- ADR-0011 (Accepted) — Portraits
- ADR-0012 (Accepted) — PPL/ZDR
- ADR-0017 (Accepted) — Mission-Material

## 변경 이력

- 2026-06-18: Draft 작성
- 2026-06-18: Accepted (Light Fog)

## 결과 (Consequences)

본 ADR은 substance 전부 구현된 상태. 파일 경로는 ADR-0020 작성 후 변경됨 (matrix/ 폴더 신설, engine 분할).

**구현 증거 (2026-08-05)**:
- `matrix/exploration.py` (2.9KB) — Light Fog 4단계 가시성 (current/adjacent/discovered/unknown)
- `engine/matrix_minimap.py` (3.2KB) — 미니맵 + breadcrumb
- `data/cyberspace/worlds.json` — cyberspace 노드 데이터
- `engine/matrix_view.py` 에서 `render_fog_overlay()` 호출 확인 가능

ADR-0020 의 Light Fog 디자인 (3단계 가시성: current 강조, adjacent 외곽선, discovered 박스, unknown `?` placeholder) 은 `matrix/exploration.py` 의 `FogState` 와 `engine/matrix_minimap.py` 의 breadcrumb visualization 에 그대로 구현됨.

**연관 ADR (이미 Accepted)**:
- ADR-0060 (Dungeon Exploration Redesign — NetHack + VFX Overlay) — 본 ADR 의 후속, dungeon 통합
- ADR-0103 (Dungeon-only Mode) — matrix_view 의 deprecated 경로 확정


**변경 후 immutable**: 본 ADR 의 결정 사항은 변경 불가. 향후 수정 필요 시 신규 ADR 작성 (AGENTS.md §8).
