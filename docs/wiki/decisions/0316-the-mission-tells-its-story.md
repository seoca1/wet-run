# ADR-0316: 미션은 자기 이야기를 말한다 — 파생 소설에서 브리핑을 가져온다

**상태**: Accepted
**날짜**: 2026-11-16
**결정자**: AI 위임 (오너 "추천대로 해줘" — 파생 소설 → 게임 서사 완성 A→C→B 중 A)
**우선순위**: P1 (서사 · 콘텐츠)

## 컨텍스트 (Context)

"파생 소설을 스토리에 적용"하려던 의도는 **검증됐지만 완성되지 않았다.** 실측:

| 층 | 위치 | 규모 | 게임에서 보이나 |
|---|---|---|---|
| 파생 소설 | `Fiction/derivative/` | **455 파일 · 213 미션 id** | ❌ 직접 연결 없음 |
| 그래픽 노블 프롤로그 | `web/src/data/scenes.json` | **27씬 · 15 미션** (3자키×9) | ✅ 별도 모드 |
| 게임 `story` 링크 | `missions.json` | **20 미션 (전부 far-grid)** | 🔸 허브에 `[Source: …]` **경로만** |

**가설 검증**: 그래픽 노블의 씬은 파생 소설에서 **직접 개작**됐다 — `first_jack` 의
`scene_case_intro/jackin/jackout` 이 소설 `2026-06-23_case_jackout-30sec.md` 의 문장
("Thirty seconds. The Ono-Sendai electrodes lift from my scalp…")을 그대로 쓴다.

**그러나 게임은 고른 미션의 이야기를 보여주지 않는다**:
- GN은 **캐릭터 앤솔로지**다(`loadPrologueChain` 이 자키 3명 × 최대 8씬을 시드 셔플).
  `first_jack` 을 고른 플레이어가 그 씬을 보려면 우연히 걸려야 한다.
- far-grid 의 `story` 는 허브에 `[Source: …]` **라벨**로만 표시된다(본문 없음).
- **sprawl 미션에는 브리핑조차 없다**(`briefing` 필드는 far-grid 20개뿐).

**재료는 충분하다**: sprawl 33미션 중 **32개**에 파생 소설이 있고, 그중 **166편**이
`plot_summary`(깨끗한 한 문단)를 갖는다. 요약 168건을 슬롭 마커로 스캔해 **0건**을 확인했다
(슬롭은 소설 **본문**에 있고 요약에는 없다).

## 결정 (Decision)

**파생 소설의 `plot_summary` 를 미션의 `briefing` 으로 가져오고, 미션 선택 화면이 그것을
보여준다.**

- 도구: `scripts/tools/import_briefings.py` — `game_mission_id` + `plot_summary.en` 을 읽어
  정리(따옴표/이스케이프 해제 · **중복 단어 복구** · 150자 절단 · 꼬리 잘림에 `…`) 후
  `web/src/data/missions.json` 에 `briefing` 을 쓴다. **멱등**이고 **far-grid 는 건드리지 않는다.**
- 화면: `renderMissionList(..., briefing)` 이 목록 아래에 줄바꿈해 표시한다(40열 3줄).
- 언어: `briefing_ko` 가 있으면 한국어, 없으면 영어(sprawl KO 요약은 아직 없다 — 열린 질문 (a)).

## 결과 (Consequences)

- **32개 sprawl 미션**이 이제 "무엇에 관한 미션인지"를 말한다. 예:
  - `first_jack` — "Case experiences the thirty seconds after jack-out — the shaking hands, the matrix."
  - `first_trace` — "Case takes his first real trace job for The Finn. The target is a mid-level node…"
  - `final_choice` — "Case must decide what to do with proof of Wintermute's existence. Three paths…"
- 미션 선택 화면은 **미션 목록 + 선택된 미션의 브리핑**이 된다(밸런스 무영향, 표시 전용).
- **슬롭 격리**: 요약만 가져오므로 본문의 주입 문장은 게임에 들어오지 않는다. 도구가 슬롭
  마커를 만나면 그 요약을 **버린다**.
- 검사: `check_no_novel_prose.py` 1878 문자열 0건(요약은 파생 창작이며 깁슨 원문이 아니다).
- 테스트 **212 files / 4223 tests** · e2e menu·progression 6/6.

## 열린 질문

- **(a) 한국어 브리핑.** `plot_summary.ko` 는 대부분 비어 있다(`ko: ''`). 채우려면 Fiction 쪽
  번역이 필요하다.
- **(b) 그래픽 노블을 미션에 묶기.** 이 ADR 은 A(미션→브리핑)다. GN을 "고른 미션의 씬"으로
  바꾸는 것이 **B** 이고, 아직이다.
- **(c) 고아 id 181개.** 파생 소설이 가리키는 213개 미션 id 중 게임에 존재하는 것은 **32개**뿐이다
  (`3jane_straylight`·`angie_leopard_tracking`…). 재매핑하거나 은퇴 목록화해야 한다 — **C**.
- **(d) `dixies_offer` 만 브리핑이 없다.** 그 미션의 파생 소설이 아직 없다.
- **(e) 150자 상한.** 화면이 3줄로 자른다. 더 긴 이야기를 원하면 화면을 늘려야 한다.

## Implementation Status (2026-11-16)

**Status**: ✅ Implemented

**Evidence**:
- `scripts/tools/import_briefings.py` — 생성 도구(멱등 · 슬롭 거부 · far-grid 보존)
- `web/src/data/missions.json` — `briefing` 52건(sprawl 32 신규 + far-grid 20 기존)
- `web/src/renderer/mission_select.ts` — 목록 아래 브리핑(줄바꿈, 40열 대응 힌트)
- `web/src/main.ts` — 선택 미션의 브리핑 전달
- `web/tests/adr0316_mission_briefing.test.ts` — 5 tests
- `web/tests/adr0300_no_text_is_cut_off.test.ts` — 미션 선택 3 레이아웃 가드

**Notes**: 표시 전용. 밸런스·저장 스키마 무변경.

## 관련 결정

- ADR-0213 — Far Grid 의 `story`/`briefing` 필드(이 ADR 이 sprawl 로 확장)
- ADR-0272 · ADR-0273 · ADR-0274 — 그래픽 노블 프롤로그와 런 핸드오프
- ADR-0315 — 메뉴/진행 구조(같은 서사 흐름)
- ADR-0300 — 폭 가드(미션 선택도 케이스로 추가)

## 변경 이력

- 2026-11-16: Accepted — 파생 소설 → 브리핑(A) 구현
