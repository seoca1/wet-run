# 과제: ASCII 로그라이크 카드배틀의 '자키 정체성' 설계 제안

## 0. 역할
당신은 수석 게임 시스템/밸런스 디자이너다. 아래 엔진 제약 안에서 **최소한의 새 메커니즘**으로, 세 자키의 시작 덱이 **숫자(tier)가 아니라 종류(메커니즘)로** 구별되도록 설계하라. 근거 없는 낙관 금지. 모든 제안은 수치와 함께, 측정 가능한 형태로만.

## 1. 게임 구조
- ASCII 로그라이크 덱배틀러 (TypeScript). 플레이어가 **자키를 고르고 → 미션 → 런**(매트릭스 보드 → ICE 조우 전투)을 진행한다.
- 전투는 손패에서 **프로그램 카드**를 쓴다. 각 카드는 tier(1~5), ap_cost(=COST/alarm)를 가진다.
- **데미지는 단일 경로**: 모든 프로그램이 ICE에게 `tier * 5` 데미지. 예외 없음.
- COST(alarm)가 상한(100)에 닿으면 모든 카드가 블록된다 → 그 턴은 ENTER 패스 또는 ESC(런 포기/실패).
- ICE는 방어도(armor)를 가진다. ICE 턴에는 플레이어를 공격한다.

## 2. 지금의 문제 (정확히 이것)
시작 덱 5장을 자키별로 나눴는데, **덱의 강함은 tier 합계로만 결정된다.** 이유:
- 실제 효과가 **구현된 프로그램은 5개뿐**이고, 나머지 25개는 설계 의도(planned_description)만 있고 전부 **평타**다.
- 그 5개 중 **4개를 기본 덱(CASE)이 이미 쥐고** 있다.
- 그래서 "효과 카드를 평타로 교체"는 **하향**이다. 실제로 그런 초안이 3등급 승률 **72.4%** 로 기본 덱(78.4%)보다 낮게 측정돼 **함정 선택**으로 기각됐다.
- 결론: "무모한 자키"를 만들려고 방어를 빼면 그냥 약해진다. **정체성을 만들려면 메커니즘을 늘려야 한다.**

측정된 현재 곡선 (등급 3/4/5, 100 runs/mission, 시드 고정):
- CASE `strike,backdoor,boost,barrier,decoy` → 78.4% / 38.9% / 33.4%
- SIL  `strike,backdoor,exploit,barrier,decoy` → 83.8% / 44.5% / 38.3%
- KAS  `strike,exploit,virus,surge,decoy` → 78.6% / 38.8% / 33.2%
- 참조(PPL, 등급에 맞춘 상위 5장) → 99.3% / 84.1% / 44.4%  ← 엔진이 허용하는 상한 감각

## 3. 구현된 효과 (수치 그대로. 충돌 금지)
| program | tier | ap_cost | 효과 |
|---|---|---|---|
| backdoor | 2 | 2 | pierce 2 |
| barrier | 3 | 3 | shield 2, 2턴 |
| boost | 2 | 2 | empower +2, 2턴 |
| cloak | 2 | 2 | evade 15%, 2턴 |
| decoy | 2 | 2 | 1턴 피해 50% 감소 |

주의: 카탈로그의 `planned_description` 텍스트는 위 수치와 **어긋난다**(예: boost는 "30% 3턴"이라 적혀 있으나 실제는 +2, 2턴). 텍스트를 근거로 삼지 말고 위 표를 근거로 삼아라. 텍스트도 함께 고쳐야 한다면 지적하라.

## 4. 전체 카탈로그 30개 (미구현 25개의 설계 의도)
| id | tier | ap_cost | type | 설계 의도 / 현재 구현 |
|---|---|---|---|---|
| heal | 1 | 2 | support | Basic heal. Restores 3 HP. |
| ice_break | 1 | 2 | attack | Targeted ICE break. Weak armor pierce. |
| inspire | 1 | 1 | support | Inspire program. +1 morale to all allies. |
| probe | 1 | 1 | detect | Reveal enemy weakness. |
| rewind | 1 | 1 | support | Rewind program. Resets AP to base value for 1 turn. |
| scan | 1 | 1 | detect | Reveal enemy stats and weaknesses for 3 turns. |
| shield | 1 | 1 | defense | One-time shield block. |
| strike | 1 | 1 | attack | Basic attack. Cheap, weak, reliable. |
| sweep | 1 | 1 | attack | AOE sweep attack. Hits all adjacent ICE. |
| wisp | 1 | 2 | defense | Defense program. Adds shield. |
| backdoor | 2 | 2 | attack | **구현됨** — pierce: 대상 방어도 2 무시 |
| boost | 2 | 2 | support | **구현됨** — empower: 플레이어 공격 +2 (평타에 가산), 2턴 |
| cloak | 2 | 2 | defense | **구현됨** — evade 15%, 2턴 |
| decoy | 2 | 2 | defense | **구현됨** — 1턴간 받는 피해 50% 감소 |
| decrypt | 2 | 2 | detect | Quick-decrypt ICE protection. Increases break speed. |
| hammer | 2 | 2 | attack | Medium attack. Faster than Goliath. |
| repair | 2 | 2 | support | Repair program. Restores HP to construct. |
| salvage | 2 | 1 | support | Salvage program. Gain bonus credits from defeated ICE. |
| trace | 2 | 2 | detect | Trace enemy location. Reveals boss positions. |
| virus | 2 | 2 | attack | Damage over time. Weaker per tick but stacks. |
| ward | 2 | 2 | defense | Area shield. Protects adjacent allies. |
| barrier | 3 | 3 | defense | **구현됨** — shield 2, 2턴 |
| echo | 3 | 2 | detect | Echo pulse. Attracts nearby ICE for ambush. |
| exploit | 3 | 3 | attack | Exploit attack. High damage, ignores 50% armor. |
| goliath | 3 | 3 | attack | Heavy attack. Slow but powerful. |
| payload | 3 | 4 | attack | High damage payload. Low AP cost for lethal strike. |
| reflect | 3 | 3 | defense | Reflects a portion of damage back at attacker. |
| surge | 3 | 2 | attack | Surge attack. Fast and reliable. |
| wardrone | 4 | 2 | defense | Auto-counter defense. +2 shield + retaliation. |
| kraken | 5 | 4 | attack | Strongest attack. The legend. |

## 5. 제약 (어기면 기각)
1. **결정론**: 새 난수원 금지. 시뮬레이터는 시드 고정이라 비결정 효과는 측정 불가.
2. **애니메이션/타이밍 금지**: 효과는 입력에 대한 즉시 계산이어야 한다(연출 대기 금지).
3. **새 서브시스템 최소화**: 상태 필드 추가는 허용하되 최소로. 각 효과는 (state, program) 쌍에 대한 **유계 계산**이어야 한다.
4. **형태 규칙 유지**: 각 덱은 5장, 최소 1장은 방어. (전부 공격인 덱은 2등급에서 무너지는 것이 이미 측정됨)
5. **함정 금지**: 세 자키가 3등급 승률에서 서로 **±5%p 이내**. 어떤 선택도 "그냥 약한 것"이면 안 된다.
6. 카탈로그에 없는 새 프로그램 **창작 금지**. 위 30개에서 고르라.
7. 검증 도구: `npm run balance -- --deck <opening|veteran|heretic>` 및 `--deck-ids a,b,c,d,e` (100 runs/mission, 시드 고정, 등급별 승률 표). 제안은 이걸로 검증 가능해야 한다.

## 6. 산출물 (마크다운, 간결하게)
**A. 먼저 구현할 효과 5~8개 순위.** 각각: 프로그램 id · 정확한 메커니즘 · 수치 · 지속/스택 규칙 · `(player, ice, program)` 위 의사코드 1~3줄 · "왜 정체성을 만드는가" 한 줄. **단순 추가 데미지가 아닌 것을 우선**하라.
**B. 세 자키 정체성 제안** (CASE/SIL/KAS): 각 5장 덱(위 30개 id만) + 정체성 한 줄 + "이 덱이 무엇을 다르게 하는가".
**C. 예상 곡선**: 각 정체성이 3·4·5등급 승률을 올릴지 내릴지, **어디가 함정/과강 후보**인지, 확신도(상/중/하).
**D. 검증 계획**: 어떤 지표를 어떻게 재는가. 실패로 판정할 기준.
**E. 하지 말 것 목록**: 이 엔진에서 위 제약을 깨는 흔한 실수.

## 7. 금지
- 일반론("재미있게 만들어라", "밸런스를 맞춰라") 금지. 모든 제안은 수치와 함께.
- 엔진에 없는 것을 당연시하는 제안 금지(예: 다중 스택 상태이상, 턴 큐, 파티 시스템, 실시간 조작).
- 근거 없는 승률 예측 금지. 예측이면 확신도를 밝히라.
