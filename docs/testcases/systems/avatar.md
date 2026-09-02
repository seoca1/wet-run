# TC-AVATAR: Jockey Avatar (자키 아바타 — 스탯 시각화)

> **관련**: `../../decisions/0016-jockey-avatar.md`, `../../design/systems/avatar.md`

자키 아바타의 부위별 stat 표현에 대한 시나리오.

## TC-AVATAR-001: HP 100% 머리 (P0, Active)

**Given**: 자키 HP 100/100
**When**: 아바타 렌더링
**Then**: 머리 = `◉P◉` (green, 완전 무결)

## TC-AVATAR-002: HP 50% 머리 (P0, Active)

**Given**: 자키 HP 50/100
**When**: 아바타 렌더링
**Then**: 머리 = `◉P/` (yellow, 기울어짐, 글리치)

## TC-AVATAR-003: HP 0% (flatline) (P0, Active)

**Given**: 자키 HP 0/100
**When**: 아바타 렌더링
**Then**: 머리 = `X` (dark_red, dead)
**Then**: "FLATLINE. Static. Silence." 메시지 표시

## TC-AVATAR-004: Program Tier 시각화 (P0, Active)

**Given**: 자키 인벤토리: Wisp (T1), Hammer (T2), Goliath (T3), Wardrone (T4), Kraken (T5)
**When**: 아바타 렌더링
**Then**: 슬롯 = `·W· :H: |G| ▓W▓ ★K★` (각 tier 시각화)

## TC-AVATAR-005: Program 소진 (P0, Active)

**Given**: 자키가 Shield (일회용) 사용
**When**: 아바타 렌더링
**Then**: 해당 슬롯 = `~S~` (소진 상태)
**Then**: 재사용 불가 (T1 program 1개 소모)

## TC-AVATAR-006: 빈 슬롯 (P1, Active)

**Given**: 자키가 1개 program만 보유 (Wisp), 2개 슬롯 비어있음
**When**: 아바타 렌더링
**Then**: `·W·    ` (빈 슬롯은 공백)

## TC-AVATAR-007: Status Pose — SAFE (P0, Active)

**Given**: PPL 25, ZDR 10 (ratio 2.5, SAFE)
**When**: 아바타 렌더링
**Then**: 자세 = `◉P◉ /|\ \|/` (직립)
**Then**: "Status: SAFE" 텍스트

## TC-AVATAR-008: Status Pose — TOUGH (P0, Active)

**Given**: PPL 6, ZDR 7 (ratio 0.86, TOUGH)
**When**: 아바타 렌더링
**Then**: 자세 = `◉P/ /|\ \|/` (약간 웅크림)
**Then**: "Status: TOUGH" 텍스트

## TC-AVATAR-009: Status Pose — DEADLY (P0, Active)

**Given**: PPL 6, ZDR 12 (ratio 0.5, DEADLY)
**When**: 아바타 렌더링
**Then**: 자세 = `◉Px /\ \/` (엎드림)
**Then**: "Status: DEADLY" 텍스트

## TC-AVATAR-010: Data Salvage — HEAL 효과 (P0, Active)

**Given**: HP 50/100, 머리 `◉P/`
**When**: HEAL 적용 (+20%, +20 HP)
**Then**: 새 HP 70/100, 머리 `◉P·` (75% 회복)
**Then**: 자세 MATCH로 완화 (PPL/ZDR 비율 개선)

## TC-AVATAR-011: Deck & Wetware Tier 표시 (P0, Active)

**Given**: 자키 Ono-Sendai 7 (T4), Biochip (T4)
**When**: 아바타 렌더링
**Then**: 데크 = `║DK4║`, 웨웨어 = `▓▓▓▓`

## TC-AVATAR-012: Construct Echo (P1, Active)

**Given**: 자키가 Dixie (T5 construct) 보유
**When**: 아바타 렌더링
**Then**: `◆D◆` 표시 (아바타 주변 또는 아래)
**Then**: PPL에 construct × 3 가산 (PPL 공식)

## TC-AVATAR-013: Construct 미보유 (P1, Active)

**Given**: 자키가 construct 없음 (1-up 기본)
**When**: 아바타 렌더링
**Then**: construct echo 표시 X
**Then**: PPL에 construct 가산 없음

## Phase 6+ 자동화 (예정)

- `tests/unit/test_avatar_render.py` — head_for_hp, program_for_tier, status_pose
- `tests/integration/test_avatar_flow.py` — HP 변화 / program 변경 / status 변화 → 아바타 업데이트
- 회귀 테스트: 매 avatar 시스템 변경 시
