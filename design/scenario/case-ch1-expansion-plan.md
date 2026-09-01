# 케이 Ch1 확장 계획

**문서 상태**: DRAFT
**Created**: 2026-06-23
**Target**: 케이 Ch1 완성 + Ch2-5 확장 + 실/카스 동일 구조 적용

---

## 1. 현재 상태 요약

### 케이 Ch1 완성도

| 항목 | 상태 | 비고 |
|------|------|------|
| 단편소설 분량 | ✅ 4,797 EN chars | 3.4x 증가 |
| 에피소드 구조 | ✅ 5 episodes | 메타데이터 완비 |
| 전투 시스템 | ✅ 2 ICE encounters | Wisp T1, Watchdog |
| 깨달음/얻음 트래킹 | ✅ 5 realizations, 3 gains | insight_level 1-4 |
| 게임 Phase 매핑 | ✅ 5 phases | WAIT→BRIEFING→JACK_IN→EXTRACT→DEBRIEF |
| GN Scene 재배치 | ✅ 6 scenes | CHATTO'S, JACK-IN, JACK-OUT, FINN, REFUSAL, FREEDOM |
| 대시보드 연동 | ✅ 동적 로딩 | chapter_flow.json + story.html |
| phases 메타데이터 | ✅ 완료 | combat, gain, loss 필드 |

### 테스트 상태

```
2690 passed ✅
ruff: All checks passed ✅
```

---

## 2. 확장 체크리스트

### Phase 1: 케이 Ch2 확장 (2시간)

- [ ] `case_expanded.json`에 ch2_episodes 추가 (5 episodes)
- [ ] `case_arc.json` ch2 phases 갱신 (story-specific)
- [ ] GN scene 재배치 (07_disappear, 08_freeside)
- [ ] Combat encounters 추가 (Molly's Deal)
- [ ] HTML 재生成

### Phase 2: 케이 Ch3-5 확장 (3시간)

- [ ] 케이 Ch3-5 episodes 각각 5개씩
- [ ] phases/story_beats/combat/gain/loss 매핑
- [ ] GN scene 재배치 (기존 scene 활용)
- [ ] Ending A/B/C 분기 검증

### Phase 3: 실/카스 동일 구조 적용 (4시간)

- [ ] `sil_expanded.json` 생성
- [ ] `kas_expanded.json` 생성
- [ ] 실/카스 arc JSON phases 갱신
- [ ] GN scene 재배치 (실 4 scenes, 카스 4 scenes)
- [ ] HTML 재生成 (6개 파일)

### Phase 4: 게임 연동 개선 (2시간)

- [ ] `current_phase_index` 추적 로직 play.py 연동
- [ ] Phase 전환 시 맵 카툭 업데이트
- [ ] Combat에서 phase advancement 검증
- [ ] realization/gain UI 표시

### Phase 5: 대시보드 완비 (1시간)

- [ ] Chapter Flow 뷰어에 realization/gain 표시
- [ ] Combat 시퀀스 시각화 추가
- [ ] GN scene→Episode 맵 시각화

---

## 3. 단편소설 분량 목표

| 구분 | 현재 | 목표 | 증가율 |
|------|------|------|--------|
| 케이 Ch1 EN | 4,797 | 8,000 | 1.7x |
| 케이 Ch2-5 EN | 0 | 40,000 | — |
| 실 Ch1-5 EN | 1,359 | 40,000 | 29x |
| 카스 Ch1-5 EN | 1,315 | 40,000 | 30x |
| **총합 EN** | 7,471 | **128,000** | **17x** |

---

## 4. 게임플레이 검증 순서

```
1. uv run python scripts/play.py --character novice --duration 60
   → 컷신 start (CHATTO'S 24/7) → BRIEFING → JACK-IN
   → 전투 1 (Wisp T1) → 전투 2 (Watchdog)
   → JACK-OUT → DEBRIEF (JACK-OUT 컷신)

2. uv run python scripts/play.py --character veteran --duration 60
   → 컷신 start → BRIEFING → JACK-IN
   → 전투 시퀀스

3. uv run python scripts/play.py --character heretic --duration 60
   → 컷신 start → BRIEFING → JACK-IN
   → 전투 시퀀스
```

---

## 5. 핵심 결정 사항

| ADR | 내용 | 상태 |
|-----|------|------|
| Phase = Stage alias | backward compat 유지 | ✅ Accepted |
| ChapterState enum | PROLOGUE → ENDING_A/B/C | ✅ Accepted |
| is_playable 분기 | false = cutscene만 재생 후 스킵 | ✅ Accepted |
| cutscene_end 매핑 | 다음 챕터 start scene 재사용 | ✅ Accepted |
| PhaseData combat 필드 | phase별 전투 메타데이터 | ✅ Accepted |
| current_phase_index | RunState 추적 필드 | ✅ Accepted |

---

## 6. 열린 질문

1. **케이 Ch2-5 미션 스토리**: Sense/Net → Molly → Villa Straylight → Flatline → Neuromancer 순서로 확장하는 것이原作者순서와 일치하는가?
2. **실/카스 동일 구조**: 실은 Count Zero, 카스는 Mona Lisa Overdrive 원작 기반으로 확장?
3. **전투 난이도 스케일**: 현재 diff 1-2 → Ch5에서는 diff 5+로 확장?
