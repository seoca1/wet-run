# System: Grade Progression (등급 진행 — 1-up to 5-up)

> **상위 결정**: `../../decisions/0008-progression-system.md` (Accepted, Revised)
> **관련**: ADR-0003 (Combat), ADR-0012 (PPL/ZDR), ADR-0014 (Data Salvage), ADR-0015 (Crafting), ADR-0016 (Avatar), ADR-0019 (Aftermath)

## 목적

자키의 5개 등급 (1-up to 5-up)이 **전투와 결과 이벤트**에서 *어떻게 다른지* 검증. 같은 적을 상대할 때, 등급이 높을수록:

- 빠른 전투 종료
- 적은 피해
- 강력한 스킬 (Wisp T1 → Kraken T5)
- 더 큰 HEAL 보상
- 다른 캐릭터 반응 (aftermath)

Pillar 4 (The Build) — *성장감*의 핵심 표현.

## 5 등급 정의 (ADR-0008 + ADR-0012)

| Grade | Deck | Programs | Wetware | Construct | PPL | HP | ATK | Skills |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **1-up 신참** | T1 | Wisp T1, Strike T1 | T1 | — | 8 | 100 | 5 | T1 |
| **2-up 일반** | T2 | Wisp T2, Hammer T2 | T2 | — | 16 | 120 | 7 | T1~T2 |
| **3-up 숙련** | T3 | Wisp T3, Goliath T3 | T3 | — | 24 | 150 | 9 | T3 |
| **4-up 베테랑** | T4 | Wisp T4, Goliath T4, Wardrone T4 | T4 | — | 40 | 200 | 12 | T3~T4 |
| **5-up 전설** | T5 | Kraken T5, Goliath T5, Wisp T5, Wardrone T5 | T5 | Dixie T5 | **65** | 300 | 15 | T3~T5 |
| **6-up 마스터** (Arc 5 finale) | T6 | Master programs (T6) ×4 | T6 | Dixie T6 | **78** | 400+ | 18+ | T6 |

> **F1-1 rebalance (2026-07-22)**: construct multiplier reduced from 3× to 1× to compress 5-up dominance. 5-up PPL: 75 → 65 (was 9.4× of 1-up, now 8.1×). All other grade values unchanged. 1-up PPL still 8.
>
> **2026-07-27 sync (ADR-0130)**: Grade 5 PPL 60 → **65** (코드 권위, `matrix/ppl.py` 기준). Grade 6 row 추가.

**PPL 공식** (ADR-0012, F1-1 후): `PPL = deck*3 + sum(prog*2) + wetware + (construct*1)`

## 진행 곡선 (Verified by Combat Simulator)

`scripts/combat_grades.py` 실행 결과 — 같은 Standard ICE (ZDR 6) 상대:

| Grade | PPL | Ratio | Status | Time | Damage Taken | Skill Uses | HEAL |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1-up | 8 | 1.33x | MATCH | 14.1s | 24 | 2 | +20 |
| 2-up | 16 | 2.67x | SAFE | 8.1s | 15 | 2 | +24 |
| 3-up | 24 | 4.00x | SAFE | 6.1s | 11 | 2 | +30 |
| 4-up | 40 | 6.67x | SAFE | 4.1s | 9 | 2 | +40 |
| 5-up | 75 | 12.50x | SAFE | 2.1s | 6 | 1 | +60 |

### 핵심 인사이트

1. **시간 단축**: 14.1s → 2.1s (7배 빨라짐)
2. **피해 감소**: 24 → 6 (4배 적게 입음)
3. **HEAL 증가**: +20 → +60 (3배 많이 회복)
4. **Status 상승**: MATCH → SAFE (점진적)
5. **스킬 효율**: 5-up은 1회 사용으로 끝, 1-up은 2회 필요

## 전투 외 등급별 차이 (Aftermath, ADR-0019)

각 등급마다 *다른 캐릭터*가 반응:

| Grade | Character | Tone |
| --- | --- | --- |
| 1-up | `case` | 내성적, "Your hands are shaking..." |
| 2-up | `finn` | 비즈니스, "Don't make a habit of dying." |
| 3-up | `dixie` | 기술적, "야, 잘 했어. T-A가 더 큰 거..." |
| 4-up | `3jane` | 차가움, "I see you. The next will not be." |
| 5-up | `dixie` | 시적, "Don't let it make you cold." |

## 스킬 트리 (ADR-0015)

각 등급에서 사용 가능한 *program* 등급:

```
1-up:  ·W· ·S·      (T1 only)
2-up:  :W: :H:      (T1, T2)
3-up:  |W| |G|      (T1~T3)
4-up:  ▓W▓ ▓G▓ ▓W▓  (T1~T4)
5-up:  ★K★ ★G★ ★W★ ★W▓  (T1~T5, with Kraken)
```

등급이 올라갈수록 *두꺼운* 테두리 (·W· → :W: → |W| → ▓W▓ → ★W★) — ASCII 시각 강화 (ADR-0011).

## 검증 (combat_grades.py)

`scripts/combat_grades.py` 실행:
```bash
uv run python scripts/combat_grades.py
uv run python scripts/combat_grades.py --enemy black --zdr 12  # harder
uv run python scripts/combat_grades.py --save  # JSON 저장
```

**테스트** (`tests/unit/test_grade_progression.py`, 13 tests):
- 5 등급 모두 존재
- PPL / HP / ATK 단조 증가
- 1-up PPL 8 (공식 검증)
- 5-up construct T5, kraken 포함
- `_run_one_grade` 결과 필드 검증
- `_run_one_grade`가 *fresh enemy* 생성
- 아바타 5등급 모두 렌더링
- Tier glyph가 program ID 사용
- HEAL 단조 증가
- Aftermath 5등급 모두 존재
- 5-up > 1-up (time, damage, HP)

## Pillar 정합

- **P1 (The Run)**: 한 런 안에서 등급별 차이 없음 (동일 시작). *메타 진행*이 등급을 바꿈.
- **P3 (The Flatline)**: 1-up DEADLY 시 사망, 5-up은 쉽게 생존 — 등급이 *무게*를 결정.
- **P4 (The Build)**: 가장 직접적 표현 — 등급 = 캐릭터의 *강도*.
- **P5 (The Style)**: PPL/ZDR/HEAL이 모두 등급에 따라 *숫자*로 표현 — 깁슨 톤의 *정량화*.

## Phase 범위

### Phase 5 (현재)

- **데이터 + 시뮬레이터 + 테스트**: ADR-0008의 5등급을 `scripts/combat_grades.py`로 검증
- 5등급 avatar, aftermath 데이터

### Phase 6+

- Hub에 등급 표시 (자키 카드)
- 5등급 unlock 트리 (1-up → 5-up 점진적)
- Construct unlock (Dixie = 5-up unlock, ADR-0013)
- 등급별 미션 풀 (Grade 1 = 쉬운 미션만, Grade 5 = 모든 미션)

## 향후 결정

- 1-up이 너무 약한가? (1-up PPL 8 vs ZDR 6 MATCH 1.33x — 비등비등한 승리)
- 5-up이 너무 강한가? (12.5x — instant kill)
- 등급 상승 조건 (N개 미션 완료, 특정 미션 클리어, etc.)
- 자키 등급의 *시각적* 표시 (Hub avatar, Matrix 진입 시)
- Construct의 등급별 해금 (Dixie = 5-up? Loa = 4-up?)

## 관련 문서

- `decisions/0008-progression-system.md` — 등급 시스템 ADR
- `decisions/0012-difficulty-rating.md` — PPL & ZDR
- `decisions/0014-data-salvage.md` — HEAL 보상
- `decisions/0016-jockey-avatar.md` — 아바타 (T1~T5 시각)
- `decisions/0019-combat-aftermath-subtitles.md` — 등급별 캐릭터 반응
- `design/systems/combat.md` — 전투 시스템
- `design/systems/avatar.md` — 아바타
- `design/systems/aftermath.md` — 후일담
- `scripts/combat_grades.py` — 시뮬레이터
- `tests/unit/test_grade_progression.py` — 검증 테스트
