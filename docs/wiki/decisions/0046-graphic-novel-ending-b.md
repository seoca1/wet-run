# ADR-0046: 그래픽 노블 엔딩 B 추가

**상태**: Accepted
**날짜**: 2026-06-21
**결정자**: 사용자
**우선순위**: P1

## 컨텍스트 (Context)

현재 12개 씬 (3 캐릭터 × 4 씬) 모두 **엔딩 A** 만 존재:
- **Case**: Finn의 의뢰 수락 → 1차 잭 성공
- **Marly**: Tessier-Ashpool 데이터 브로드캐스트
- **Kumiko**: Loa 네트워크에 wheel 캐스팅

깁슨 원작은 모든 캐릭터에게 **대안적 결말** 이 있음:
- Case: 신비로운 사업가 (Willis Corto 등) 의 다양한 의뢰를 거절/수락
- Marly: T-A의 "계약"을 받아들여 내부자가 되거나, 독립적으로 방송
- Kumiko: 바퀴 캐스팅 대신 침묵하거나, 가족 안에서 활동

게임플레이 다양성 + replayability 증가 + 원작 충실도 위해 **엔딩 B** 추가.

## 고려한 옵션

### Option 1: 씬 파일 분리 + 명시적 ending 태그 ✓ 선택

- **설명**: 각 씬 JSON에 `"ending": "A" | "B"` 필드 추가. `load_scene_chain(scenes_dir, character, ending="A")` 시그니처 확장. 메뉴에 ending 선택 추가.
- **장점**:
  - 데이터 주도 (기존 패턴 준수)
  - 기존 씬 그대로 (A는 자동)
  - 선택적 추가 (한 캐릭터씩)
  - 디자인 / 테스트 / 메뉴 / 저장 모두 호환
- **단점**:
  - 씬 6개 추가 (작업)
  - ending 선택 로직 추가 (UI 복잡도 ↑)

### Option 2: choice 시스템 (런타임 분기)

- **설명**: 씬에 `"next": {"choice": "A": ..., "B": ...}}` 같은 분기 정의
- **장점**: 동적 분기
- **단점**: 상태 머신 복잡, ADR-0032 패턴과 다름

### Option 3: 메뉴 모드 (A vs B 별도 진입)

- **설명**: 메뉴에서 "Ending A" / "Ending B" 별도 옵션
- **장점**: 단순
- **단점**: 데이터 중복 (씬 6개를 양쪽에서 각각 로드)

## 추천 (Recommendation)

**Option 1** — 데이터 주도, 기존 호환, 점진적 확장 가능.

## 사용자 결정 (Decision)

[x] Option 1 — 씬 파일 분리 + ending 태그

## 결과 (Consequences)

### 긍정적
- **Replayability**: 한 캐릭터의 다른 결말 경험 가능
- **깁슨 충실도**: 원작의 대안 결말 반영
- **데이터 주도**: 씬 JSON에 ending 명시 → 런타임 분기 불필요
- **점진적 확장**: 다른 캐릭터/엔딩 C/D 추가 시 같은 패턴

### 부정적 / 위험
- 씬 6개 추가 작업 (각 캐릭터당 branch + payoff)
- 메뉴 UI 복잡도 (ending 선택 추가)
- GN 이어서 읽기 (`--continue`) 가 ending 결정도 저장해야 함

## 영향 받는 항목
- `prototype/data/scenes/{case,sil,kas}/05_*.json`, `06_*.json` — 6 새 씬
- `prototype/src/wet_run/engine/graphic_novel_view.py` — `load_scene_chain(ending=)`
- `prototype/scripts/graphic_novel.py` — `--ending {a,b}` flag
- `prototype/src/wet_run/engine/state.py` — `gn_ending: str`
- `prototype/src/wet_run/engine/graphic_novel_save.py` — `ending` 필드
- `design/scenario/graphic-novel.md` — ending 구조 명시
- `prototype/tests/unit/test_graphic_novel_endings.py` — 신규 테스트

## 엔딩 B 콘텐츠 디자인

### Case Ending B: 거부 (Refusal)
- **05_refusal**: Case가 Finn 사무실에서 의뢰를 거절. 돈은 이미 받았으니 새 의뢰는 거절. "다음엔 안 봐줄 거야."
- **06_freedom**: Case 잭아웃. Chiba 비 내리는 새벽, 커피 한 잔. 더 이상 console cowboy는 아님. Sprawl은 잊지 않는다.
- **톤**: 쓴맛 + 해방감. 영웅 서사 거부.

### Marly Ending B: 계약 (Contract)
- **05_contract**: T-A가 Marly에게 직접 접촉. "데이터 대신 우리와 함께." 그녀는 망설이다가 수락.
- **06_insider**: Marly가 T-A 오퍼레이브가 됨. 갤러리에서 보석 대신 데이터를 검사. Mara의 흔적은 사라짐.
- **톤**: 어두운 + 파우스트적. 데이터를 팔아넘.

### Kumiko Ending B: 침묵 (Silence)
- **05_silence**: Kumiko가 Loa 채널을 열지 않는다. 바퀴는 돌지만 그녀는 보지 않는다. 가족이 이기는 것에 동의.
- **06_shadow**: Shibuya를 떠난다. 어느 새벽, 무명. 로아의 드럼도 그녀를 부르지 않음.
- **톤**: 정적 + 관조적. 신성한 무관심.

## 관련 결정
- ADR-0032 (그래픽 노블 모드) — 기반
- ADR-0041 (콘텐츠 확장) — 톤 가이드라인 재사용
- ADR-0044 (이어서 읽기) — ending 필드 저장

## 변경 이력

- 2026-06-21: Draft 작성 (Option 1 채택)