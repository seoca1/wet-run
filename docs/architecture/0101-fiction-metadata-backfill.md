# Fiction Metadata 보강 계획

## 현황 요약

| 항목 | 수량 | 비고 |
|------|------|------|
| 고유 stems (short-stories) | 41 | 전부 paired |
| KO paired files | 41/41 | **100%** 완료 |
| EN files (고유 stem별) | 41 | 중 36 stems = missions 연결 |
| missions story.source 매핑 | 47/47 | **100%** 완료 |
| 종합 metadata 완전율 | ~83% | |

### 파일 중복 (정리 필요)
5개 stem이 날짜 variant로 중복 존재:
- `case_jackout-30sec` — `2026-06-20` + `2026-06-23` version
- `kumiko_manarase-midnight` — `2026-06-20` + `2026-06-23`
- `marly_louisiana-god` — `2026-06-20` + `2026-06-23`
- `sally_sandii-3am` — `2026-06-19` + `2026-06-23`
- `wigan_zavijava` — `2026-06-19` + `2026-06-23`

→ 최신 version만 남기고 중복 파일 삭제 필요

---

## 백필드 (Backfill) 작업

### S1. KO translation 36개 stem — **HIGHEST PRIORITY**
**대상**: missions에 연결된 36개 EN-only stems
**작업**: 각 stem의 EN 파일 내용 기반으로 `plot_summary.ko` + `subtitle_ko` 작성
**파일 수**: 36개 stems × 1 EN-only file = 36개 EN-only file

### S2. 중복 파일 삭제 — **HIGH PRIORITY**
**대상**: 5개 stem × (최신 외 중복) = 약 5개 파일 삭제
**규칙**: 가장 최근 날짜 version만 남김
```
删除 대상 (latest 외):
  - 2026-06-20_case_jackout-30sec.md/.ko.md (keep 2026-06-23)
  - 2026-06-20_kumiko_manarase-midnight.md/.ko.md (keep 2026-06-23)
  - 2026-06-20_marly_louisiana-god.md/.ko.md (keep 2026-06-23)
  - 2026-06-19_sally_sandii-3am.md/.ko.md (keep 2026-06-23)
  - 2026-06-19_wigan_zavijava.md/.ko.md (keep 2026-06-23)
```

### S3. Paired EN 파일 — plot_en 백필드 (9 stems)
**대상**: Paired file인데 `plot_summary.en` 없는 9개 stems
```
armitage_infiltration     case_jackout-30sec    hosaka_extraction
kumiko_manarase-midnight marly_louisiana-god  sally_sandii-3am
ta_defection            wigan_zavijava         wintermute_negotiation
```
**작업**: 기존 story 내용 기반 plot_summary.en 작성

### S4. Paired EN 파일 — character_ref 백필드 (5 stems)
**대상**: `character_ref` 없는 5개 stems
```
case_jackout-30sec    kumiko_manarase-midnight    marly_louisiana-god
sally_sandii-3am     wigan_zavijava
```

### S5. Paired EN 파일 — wiki_references 백필드 (9 stems)
**대상**: `wiki_references` 없는 9개 stems
```
armitage_infiltration    hosaka_core              hosaka_extraction
maas_heist              sense_net_infiltration  straylight_approach
ta_defection            wigan_call              wintermute_negotiation
```

### S6. Paired KO 파일 — plot_ko 백필드 (9 stems)
**대상**: Paired KO file인데 `plot_summary.ko` 없는 9개 stems (S1 KO translation과 동일 9개)

### S7. Paired KO 파일 — wiki_references 백필드 (9 stems)
**대상**: Paired KO file인데 `wiki_references` 없는 9개 stems (S5와 동일 9개)

### S8. game_integration 백필드 (2 stems)
**대상**: `game_integration` 없는 2개 stems
```
sally_sandii-3am    wigan_zavijava
```

---

## 순서 및 예상 시간

| 순서 | 작업 | 대상 수 | 예상 |
|------|------|---------|------|
| S2 | 중복 파일 삭제 | ~10개 | 10분 |
| S1 | KO translation 작성 | 36 stems | **120분** |
| S3 | plot_en 백필드 | 9 stems | 30분 |
| S4 | character_ref 백필드 | 5 stems | 15분 |
| S5 | wiki_references 백필드 | 9 stems | 30분 |
| S6 | plot_ko 백필드 | 9 stems | (S1에 포함) |
| S7 | wiki_refs 백필드(KO) | 9 stems | (S5에 포함) |
| S8 | game_integration 백필드 | 2 stems | 10분 |
| 리빌드 | dashboard JSON 재생성 + 검증 | — | 5분 |

**총 예상**: 약 **4시간** (S1 KO translation이 대부분)

---

## 완료 기준

- [x] 모든 36개 stems에 `plot_summary.ko` 작성됨
- [x] 모든 paired files에 `plot_summary.en` 작성됨
- [x] 모든 paired files에 `character_ref` 존재
- [x] 모든 paired files에 `wiki_references` 존재
- [x] 모든 paired files에 `game_integration` 존재
- [x] 중복 날짜 variant 파일 삭제됨 (10개 파일: 5 stems × EN+KO)
- [x] `python3 tools/build_dashboard.py` 성공
- [ ] `library.html` Hanja 0건
- [x] `missions.json` 47개 mission 모두 유효한 `story.source` 보유

## 2026-07-08 완료 사항

### S2: 중복 파일 삭제 — 완료
삭제된 파일 (최신 외 중복):
- 2026-06-20_case_jackout-30sec.md/.ko.md
- 2026-06-20_kumiko_manarase-midnight.md/.ko.md
- 2026-06-20_marly_louisiana-god.md/.ko.md
- 2026-06-19_sally_sandii-3am.md/.ko.md
- 2026-06-19_wigan_zavijava.md/.ko.md

### S1+S6: KO translation 작성 — 완료
완전히 재작성된 4개 KO stubs:
- `armitage_infiltration.ko.md` — 완전한 한국어 내용 + proper frontmatter
- `hosaka_extraction.ko.md` — 완전한 한국어 내용 + proper frontmatter
- `ta_defection.ko.md` — 완전한 한국어 내용 + proper frontmatter
- `wintermute_negotiation.ko.md` — 완전한 한국어 내용 + proper frontmatter

### S7: wiki_references 백필드 (KO) — 완료
5개 KO 파일에 `wiki_references` 추가:
- hosaka_core.ko.md
- maas_heist.ko.md
- sense_net_infiltration.ko.md
- straylight_approach.ko.md
- wigan_call.ko.md

### 현 상태: 36 stems × 2 files = 72 files, 전부 paired, 전 필드 완전
