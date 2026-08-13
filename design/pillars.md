# Design Pillars (디자인 기둥)

이 게임이 절대 양보하지 않는 핵심 가치. 모든 디자인 결정은 이를 기준으로 평가된다.

## Pillar 1: The Run

> 한 번의 침투, 명확한 끝.

- 플레이는 항상 "잡(job)" 단위로 진행
- 한 런 = 한 의뢰
- 명확한 시작, 클라이맥스, 결과
- 죽으면 끝, 다음 런으로 (메타 진행은 Pillar 4)
- **PPL (Player Power Level) & ZDR (Zone Difficulty Rating)** — combat 위험 명시화, 회피 가능 (ADR-0012)
- **PPL은 동일 시작** (등급 외, ADR-0008) — 런 중 장비 변경으로만 변함
- **Story Events** — 부가 콘텐츠로 런 내 다양성 (ADR-0013)

**이게 깨지면 안 되는 것**:
- "이번엔 무한히 갈 수 있다" 모드 X
- "오늘의 일일 미션" X
- "10시간 플레이 가능한" 메인 스토리 X
- "어려운 곳 강제 진입" (FUTILE zone 강제) X (Pillar 1, 4)

## Pillar 2: The Matrix

> 사이버스페이스가 *유일한* 시각적 공간.

- **meatspace는 절대 시각화되지 않음** (ADR-0009, 2026-06-17 확정)
- 매트릭스 안의 모든 것은 데이터로 표현 가능 (그리고 해야 함)
- "I'm in the wet" 톤
- Hub (Job Board, Prep, 픽서 대화)도 cyberspace 안의 텍스트 인터페이스
- meatspace는 뉴스/이야기로만 전달 — Story Archive에서 다시 볼 수 있음
- **ASCII Portrait는 cyberspace 안의 존재에게만** (ADR-0011) — meatspace 인물 직접 묘사 X

**이게 깨지면 안 되는 것**:
- 매트릭스 밖이 메인인 게임 X
- meatspace에서의 무한 활동 X
- "현실 세계로 돌아가서도 계속 진행" X
- meatspace의 어떤 직접적 묘사 (이미지, 애니메이션, 대화 장면) X
- meatspace 인물의 ASCII portrait X (construct, jacked-in 상태로만 가능)

## Pillar 3: The Flatline

> 죽음에 진짜 무게.

- 평시: 캐릭터를 잃음
- 메타 진행: 있지만 공격적이지 않음 (Pillar 4 참조)
- "flatline" = 신경계 손상 = 게임 오버
- 죽음 후 묘사: 정적, "you flatline", 검은 화면

**이게 깨지면 안 되는 것**:
- 리스폰 / 무한 부활 X
- 죽음 페널티가 너무 가벼움 X
- death = positive outcome X

## Pillar 4: The Build

> 런 사이 진행은 더 좋은 도구로.

- 새 프로그램, 새 데크, 새 웨웨어, 새 construct
- **레벨업 = 아이템/장비 티어 (T1~T6)** (ADR-0008, Phase 7에서 T6 추가)
- 숫자가 아닌 "내가 뭘 할 수 있는가"가 변화
- "스킬"보다 "장비"와 "컨셉"
- 메타 진행은 unlock 중심 (강화 X)
- combat 강도는 program tier에 비례 (ADR-0003 RT-MS)

**이게 깨지면 안 되는 것**:
- 캐릭터 스탯의 영구 강화 X (런 내에서는 OK)
- "다음 런이 더 쉬워지는" 누적 X
- "difficulty" 자체가 사라지는 진행 X
- XP / 레벨 / 스탯 누적 X (장비/도구로만)

## Pillar 5: The Style

> 사이버펑크 미학 - 네온, 크롬, 가죽.

- 깁슨의 톤을 정확히
- 거칠고, 비관적, 명료한
- 절제된 미니멀 미학 아님
- 거친 미래, 거친 사람
- **mediated world** — 매트릭스 안의 시뮬레이션으로만 외부 세계가 전달됨 (ADR-0009)

**이게 깨지면 안 되는 것**:
- 미니멀/유토피아적 미래 X
- "기술이 모두에게 좋은" 신화 X
- 화려한 비주얼 폴리시 X
- Cyberpunk 2077 / Shadowrun 톤 X
- meatspace의 직접적 묘사 X (Pillar 2)

## 비-기둥 (반드시 회피)

이것들은 우리가 의도적으로 **만들지 않을** 것들:

- **Loot grind** — 무한히 강한 적 = 무한히 좋은 loot
- **Multiplayer / Social** — 1인칭 솔로 경험
- **Skins / Cosmetics** — 시각적 다양성보다 의미
- **Daily login / Engagement mechanics** — 게임이 사용자 시간을 빼앗지 않음
- **Infinite scaling** — 적이 계속 강해지는 시스템
- **Prestige** — 반복 플레이를 위한 인위적 시스템
- **Mobile / F2P** — PC/Mac 솔로 게임

## Pillar 우선순위 충돌 시

1. **Pillar 1 (The Run)** — 최우선
2. **Pillar 3 (The Flatline)** — 무결성 보호
3. **Pillar 2, 4, 5** — 동등
4. **비-기둥** — 항상 회피

## 디자인 리뷰 체크리스트

새 시스템을 만들 때 다음을 자문:

- [ ] 이 시스템은 한 런 안에서만 작동하는가? (Pillar 1, 4)
- [ ] 매트릭스 안의 표현인가? (Pillar 2)
- [ ] 죽음의 무게를 깎지 않는가? (Pillar 3)
- [ ] 깁슨 톤을 유지하는가? (Pillar 5)
- [ ] 비-기둥을 활성화하지 않는가?
- [ ] **meatspace를 직접 묘사하고 있지 않은가?** (Pillar 2, ADR-0009)
- [ ] **명시적 숫자 / 회피 옵션이 제공되는가?** (Pillar 1, ADR-0012)

## Phase 22 audit (2026-08-14)

> **Phase 18** (2026-08-13) noted: "No gaps (pillars unchanged by Phase 15-17)."
> **Phase 22** (this update) re-verifies the same: Phase 15-17 신규 메카닉 (Deck Size, Telemetry Opt-in, Wetware Stacking, F.4 Boss Phase, Random Rules Engine, Endings Persistence, Performance HUD, TELEMETRY_STATS screen) **모두 기존 5개 Pillar 의 강화 또는 무관** — 새로운 Pillar 도입 / 기존 Pillar 수정 없음.

### Re-verification matrix

| 신규 메카닉 | Pillar 1 (Run) | Pillar 2 (Matrix) | Pillar 3 (Flatline) | Pillar 4 (Build) | Pillar 5 (Style) | 비-기둥 회피 |
| --- | --- | --- | --- | --- | --- | --- |
| Deck Size (LIGHT/STANDARD/HEAVY) | ✓ 한 런 안 선택 | ✓ AP/cooldown 변동 | — 무관 | ✓ 빌드 핵심 선택 | — 중립 | ✓ |
| Telemetry Opt-in | — 무관 | — 무관 | — 무관 | — 무관 | — opt-out 기본 | ✓ privacy-first |
| Wetware Stacking | — 무관 | — 무관 | — 무관 | ✓ 누적 보너스 | — 중립 | ✓ |
| F.4 Boss Phase | ✓ 런 내 진행 | ✓ 매트릭스 안 전투 | ✓ phase 전환 시 무게 ↑ | ✓ 보스별 빌드 대응 | ✓ phase 별 glyph/color | ✓ |
| Random Rules Engine | ✓ 런 내 의뢰 편향 | — 무관 | — 무관 | — 의뢰 다양성 | — 중립 | ✓ |
| Endings Persistence | — 무관 | — 무관 | ✓ sacrifice 엔딩 무게 보존 | — unlock 추적 | — 무관 | ✓ |
| Performance HUD | — 무관 | — 무관 | — 무관 | — 무관 | — 디버그 전용 | ✓ |
| TELEMETRY_STATS screen | — 무관 | — 무관 | — 무관 | — 메타 진행 보조 | — ASCII 집계 | ✓ |

### 결론

- **Pillar 변경**: 없음. 5개 Pillar 모두 그대로 유지.
- **비-기둥 위반**: 없음. (Loot grind / Multiplayer / Cosmetics / Engagement / Infinite scaling / Prestige / Mobile-F2P 모두 회피.)
- **ADR 영향**: 없음 (Pillar 자체는 ADR 이 아니라 design philosophy 문서; ADR-0009 / ADR-0012 / ADR-0178 등이 Pillar 와 1:1 매핑).

향후 새 메카닉 추가 시 본 audit matrix 와 동일한 형식으로 영향 평가 권장.
