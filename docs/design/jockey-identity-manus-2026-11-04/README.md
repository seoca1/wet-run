# 자키 정체성 설계 — Manus 제안과 그 검증 (2026-11-04)

ADR-0276 의 열린 질문 (a) — 자키 덱이 **tier(숫자)로만** 달라지고 **종류(메커니즘)로는** 달라지지
못하는 문제 — 에 대해 Manus 에 설계 제안을 의뢰하고, 돌아온 안을 **엔진에서 직접 검증**한 기록.

| | |
|---|---|
| task_id | `KEDqCAniDF6hKQbRoQBUZr` |
| URL | https://manus.im/app/KEDqCAniDF6hKQbRoQBUZr |
| 프로필 | 요청 `max-high` → **`manus-1.6-lite` 로 자동 다운그레이드** (무료 개인 계정 제약) |
| 비용 | 17 credits |
| 원문 | `proposal.md` (응답 본문) · `manus-reply.md` (채팅 요약) · `request.md` (보낸 프롬프트) |

> 제안 본문은 채팅이 아니라 **샌드박스 파일**(`/home/ubuntu/jockey_identity_proposal.md`)로만
> 나왔고, 채팅에는 요약만 왔다. 전문은 `task.listMessages` 의 `attachments[].url` 서명 링크로 회수했다.

## Manus 가 낸 것 (요약)

- **효과 우선순위 7개**: `exploit`(방어도 50%만 적용) → `scan`(3턴 방어도 −1) → `rewind`(현재 COST
  → 0, 턴당 1회) → `virus`(2 ICE 턴 방어도 −1) → `surge`(COST ≤ 50 이면 비용 1) → `shield`(다음
  피격 −4) → `heal`(+3 HP). 각각 수치·스택 규칙·의사코드 포함.
- **세 덱 (모두 tier 합 11 맞춤)**: CASE `scan,exploit,boost,barrier,decoy` /
  SIL `rewind,exploit,cloak,barrier,decoy` / KAS `strike,exploit,virus,surge,decoy`.
- **정직한 부분**: 승률을 **예측하지 않았다**("코드를 실행하지 않았으므로"), 실패 판정 기준 7개와
  조정 순서를 제시했고, `planned_description` 과 실제 구현 수치의 불일치(`boost`)를 정확히 지적했고,
  `wardrone` 반격을 **단일 피해 경로와 충돌한다며 구현 거부**했다.

## 검증 — 엔진에서 직접 확인한 것

### ✅ 맞은 것: 방어도는 실제로 피해에서 차감된다

`state_actions_programs.ts:91-99` → `defenderDefenseBonus = max(0, ice.armor − pierce)` →
`combat_engine.ts:159` → `dmg = max(0, dmg − defenderDefenseBonus)`.

그리고 방어도는 **평타의 20~35%** 로, 무시할 크기가 아니다:

| tier | ICE armor 평균 | 평타 `tier*5` | 방어도 비중 |
|---:|---:|---:|---:|
| 1 | 1.0 | 5 | 20.0% |
| 2 | 2.5 | 10 | 24.6% |
| 3 | 4.6 | 15 | 30.9% |
| 4 | 7.3 | 20 | 36.6% |
| 5 | 8.2 | 25 | 32.6% |
| 6 | 10.5 | 30 | 35.0% |

→ **방어도 조작은 정체성의 재료로 타당하다.** `exploit` 의 `floor(armor*0.5)` 는 g4 에서 방어도
7.3 → 3 으로 깎아 **한 방당 약 +4 피해**(20 → 24)를 만든다. 이건 진짜다.

### ✅ 구현 비용이 싸다 (Manus 가 몰랐던 부분)

확장 지점이 이미 있다: `program_effects.ts` 의 `PROGRAM_EFFECTS` 에 종류를 추가하고,
`state_actions_programs.ts:211` 의 `if/else if (effect.kind …)` 에 분기를 더해 기존
`applyStatus(target, kind, turns, magnitude, extras)` 로 적용하면 된다. `heal` 은
`applyBurnDamage(… healPlayer)` 경로가 **이미 있어** 거의 공짜다.

### ❌ 틀린 것 1 — `tier 합 11 맞춤`은 잘못된 불변식

Manus 의 출발 전제는 "전투력 = tier 합 × 5" 인데, 그 전제는 **방어도 차감을 무시**한다. 그런데
방어도가 평타의 20~35%다. 따라서 **tier 합이 같아도 전투력은 같지 않다** — `backdoor` 의
`pierce 2` 는 armor 0 인 ICE 에서는 0, armor 7 인 ICE 에서는 2의 가치가 있다.

→ "세 덱 tier 합을 11로 맞춘다"는 함정 방지 장치로 **작동하지 않는다.** Manus 는 자기가 발견한
방어도의 존재를 자기 전제에 반영하지 않았다.

### ❌ 틀린 것 2 — `rewind`(COST → 0)는 밸런스를 깨뜨린다

`alarm` 은 **런 단위 예산**이다. 턴마다 리셋되지 않고, 전투 진입에서도 리셋되지 않는다
(`state_actions_phases.ts:355` 의 `alarm: 0` 은 **죽은 뒤 재시작** 경로뿐). 상한 100 이고,
도달하면 모든 카드가 블록된다(ADR-0265/0266 이 다룬 그 동결이다).

`rewind` 를 **턴마다** 0으로 되돌리면 그 예산이 사실상 사라진다 → 런의 **소모 시계 자체가 제거**된다.
Manus 의 안전장치(실패 기준 #5)는 "blocked-turn rate 가 50% 이상 감소하고 g3 승률이 8%p 이상 상승하면
실패" 인데, 그건 **이미 만든 뒤에** 발동한다. 다른 항목이 ±1 방어도를 다투는 동안 이것 하나가
게임의 중심 압박을 지우는 규모다.

### ⚠️ 약한 것 — `scan`/`virus` 의 −1 방어도

g3 평균 방어도 4.6, g4 는 7.3 이다. −1 은 **5~7% 증폭**이고, 3등급에서는 `±5%p` 문턱 안에서
**보이지 않을 가능성**이 높다. Manus 스스로 이걸 KAS 함정 후보 1번으로 지목했다 — 그 자각은 옳다.

### ⚠️ 범위 문제 — CASE 덱까지 바꾼다

제안은 CASE 를 `strike,backdoor,boost,barrier,decoy`(tier 합 10) → `scan,exploit,boost,barrier,decoy`
(tier 합 11)로 바꾼다. 이는 **모든 신규 플레이어의 기본 오프닝**을 바꾸는 일이고, ADR-0260 이
"큐레이션된 기본 덱"으로 정한 것을 덮어쓴다. 자키 정체성보다 **더 큰 결정**이며, 실패 기준이
"기존 CASE 78.4% 대비"인 것도 그래서 두 변수(덱 교체 + 메커니즘 추가)를 한꺼번에 움직인다.

## 권고 (측정 우선, 축소 적용)

Manus 안을 통째로 받지 않고 **셋만** 가져오는 것을 권한다.

| 채택 | 항목 | 이유 |
|---|---|---|
| ① | **`surge`** (COST ≤ 50 → 비용 1) | **새 상태 0개.** 현재 alarm 의 순수 함수라 가장 싸고 측정이 깨끗하다 |
| ② | **`exploit`** (방어도 × 0.5) | 가장 큰 실효 레버(+4/방, g4). 이미 카탈로그에 "ignores 50% armor" 로 적혀 있다 |
| ③ | **`virus` 또는 `scan`** — 단 **−2**로 상향 | −1 은 안 보인다. 값은 측정으로 정한다 |
| ✂ | ~~`rewind`~~ | 런 소모 시계를 지운다. 쓰려면 **전투당 1회 / alarm −20** 처럼 유계로 재설계 |
| ✂ | `shield`, `heal` | 나쁘지 않으나 정체성과 무관한 일반 유틸. 나중에 |
| ✂ | CASE 덱 교체 | ADR-0260 을 건드린다. **오너 결정 사항**으로 분리 |

**불변식은 tier 합이 아니라 "측정된 곡선"으로 잡는다**: 세 자키가 g3 에서 ±5%p 이내, 어떤 덱도
기존 CASE 78.4% 보다 2%p 이상 낮지 않을 것. `npm run balance -- --deck-ids …` 로 후보를 채점한 뒤 채택.

## 오너 결정이 필요한 것

1. CASE 덱을 바꿔도 되는가? (기본값: **안 바꾼다** — SIL/KAS 만 차별화)
2. `rewind` 를 **유계 버전**으로 재설계할지, 버릴지.
3. 위 3개(①②③)로 진행할지, 아니면 Manus 안 전체를 A/B/C 파이프라인으로 돌릴지.
