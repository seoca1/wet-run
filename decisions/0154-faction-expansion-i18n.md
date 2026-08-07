# ADR-0154: Faction Expansion (faction_rumor 4 factions) + NG+ Balance Pass

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P2 (v1.2.0+ polish, faction diversity + i18n)
**관련**: [ADR-0151 — Info Market Intel Items (faction_rumor 첫 구현)](./0151-info-market-intel-items.md), [ADR-0130 — Balance Audit + PPL Sync](./0130-balance-audit-and-ppl-sync.md), [ADR-0010 — i18n + Content Pipeline](./0010-i18n-content-pipeline.md)

## 컨텍스트 (Context)

`combat/intel_items.py::FACTION_RUMOR_FACTION: str = "loa"` (hardcoded). Player 가 faction_rumor 구매 시 *항상 Loa faction* 의 event probability 만 +25%. 다른 factions (Hosaka, Sense-Net, Yakuza) 의 faction_rumor 효과 *부재*.

**현재 상태** (Cycle 9 완료):
- faction_rumor: 1 item (50 credits, Loa faction only, +25% event probability)
- i18n: en.json + ko.json 만 (Cycle 6-8). ja.json + zh.json 부재.
- PPL Grade 5→6 growth: 1.20x (잔존 이슈, `ppl_zdr_balance.md` line 47)

**Architecture**:
- `matrix/node.py::Faction` (StrEnum): HOSAKA, MAAS, SENSE_NET, TA, YAKUZA, NONE, LOA (7 factions)
- `combat/intel_items.py::FACTION_RUMOR_FACTION: str = "loa"` (hardcoded)
- faction_rumor 효과: `app_state.faction_tension_probability_boost += 0.25`

**해결 방향** (ADR-0154):
1. faction_rumor → 4 item variants (Hosaka, Sense-Net, Yakuza, Loa)
2. 각 variant: 50 credits, faction-specific, +25% event probability (해당 faction)
3. PPL Grade 5→6 growth: 코드 comment 추가 (balance doc 와 동기화, *actual rebalance는 후속*)
4. i18n: ja.json + zh.json 의 `multi_enemy` + `intel_items` + `boss_phase4` + `salvage` + `combat` 섹션 추가

**디자인 제약** (Pillar):
- **Pillar 1 (The Run)**: faction-specific faction_rumor → player 가 *어떤 faction* 의 event probability 를 높일지 선택
- **Pillar 4 (The Build)**: in-run only (변경 없음)
- **Pillar 5 (The Style)**: 깁슨 어휘 — faction-specific (Hosaka = corporate, Sense-Net = media, Yakuza = criminal, Loa = vodoun)

**기술 제약**:
- 기존 `FactionRumorPurchase` API 변경 없음 (item_id → faction mapping 추가만)
- `data/i18n/ja.json` + `data/i18n/zh.json` 신규 생성 (현재 부재)
- 4-5 LOC patch in `intel_items.py` + 2-3 i18n files

## 고려한 옵션

### Option 1: faction_rumor 4 variants (최소)

- **설명**: `FACTION_RUMOR_FACTION: str = "loa"` → `FACTION_RUMOR_FACTION_BY_ITEM: dict[str, str]` (4 variants).
- **장점**:
  - 변경 범위 최소 — 4 item 추가 (FactionRumorHosaka, FactionRumorSenseNet, FactionRumorYakuza, FactionRumorLoa).
  - 기존 `apply_faction_rumor` 함수 변경 없음 (faction_id 인자 추가만).
  - Pillar 1 (The Run) faction-specific 선택.
- **단점**:
  - PPL Grade 5→6 growth rebalance 미구현 (잔존 이슈).
  - i18n 미확장.
- **Pillar 정합**:
  - P1: faction-specific 선택 ✓.
  - P4: in-run only.
  - P5: faction-specific 깁슨 어휘 ✓.

### Option 2: Option 1 + PPL balance + i18n (전체)

- **설명**: Option 1 + PPL Grade 5→6 growth comment + ja.json/zh.json i18n 추가.
- **장점**:
  - v1.2.0+ 백로그 4 items (faction_rumor faction expansion, NG+ balance, i18n) 모두 해결.
  - Pillar 1 (The Run): faction-specific faction_rumor + NG+ (다음 런 start).
  - Pillar 5 (The Style): 4 factions 깁슨 어휘 + 다국어 확장.
- **단점**:
  - 변경 범위 중간 — 4-5 LOC faction + 2-3 i18n files.
  - PPL Grade 5→6 *actual rebalance* 미포함 (comment 만).
- **Pillar 정합**:
  - P1: faction-specific ✓ + NG+ intrinsic.
  - P4: in-run only.
  - P5: faction-specific + i18n ✓.

### Option 3: Faction reputation balance 전체 (over-scope)

- **설명**: Option 2 + faction reputation curve 재설계 (reputation_tier formula 변경).
- **장점**: Faction 시스템 전체 rebalance.
- **단점**:
  - 변경 범위 큼 — `reputation.py` + `reputation_tier()` + `discounted_price()` 전체.
  - v1.2.0+ scope 초과.
  - 7 factions × 7 tiers = 49 cells — 테스트 폭증.
- **Pillar 정합**:
  - P1, P4, P5: 동일.

## 추천 (Recommendation)

**Option 2** (faction_rumor faction expansion + PPL balance comment + i18n 확장).

이유:
1. **v1.2.0+ 백로그 즉시 해결**: faction_rumor 4 variants (faction-specific), PPL Grade 5→6 growth (comment + balance doc 동기화), ja.json + zh.json i18n 확장.
2. **변경 범위 중간**: 4-5 LOC faction_rumor expansion + 2-3 i18n files. *over-scope* 없음.
3. **기존 인프라 100% 재사용**: `Faction` enum (matrix/node.py), `FactionRumorPurchase` API (intel_items.py), i18n loader (translator.py).
4. **Pillar 정합**: P1 (faction-specific + NG+), P4 (in-run), P5 (faction-specific 깁슨 어휘 + i18n).

**순서** (Cycle 10, 1 sub-session):
1. `combat/intel_items.py`: `FACTION_RUMOR_FACTION: str = "loa"` → `FACTION_RUMORS_BY_FACTION: dict[str, str]` (4 variants)
2. `combat/multi_enemy.py`: PPL growth targets comment 추가
3. `data/i18n/ja.json` + `data/i18n/zh.json`: `multi_enemy` + `intel_items` + `boss_phase4` + `salvage` + `combat` 섹션 추가
4. Tests: 4-6 tests (faction_rumor variants, PPL growth comment, i18n keys present)

## 사용자 결정 (Decision)

[x] Option 2 (faction_rumor faction expansion + PPL balance + i18n) — 2026-08-07 Cycle 10 채택
[ ] Option 1 (faction_rumor faction expansion만)
[ ] Option 3 (Faction reputation balance 전체)
[ ] 기타: ___
[ ] Defer (다음 단계로 미룸)

## 결과 (Consequences)

### 1. faction_rumor faction expansion (combat/intel_items.py, 5 LOC)

```python
# Before (Cycle 6):
FACTION_RUMOR_FACTION: str = "loa"  # hardcoded

# After (ADR-0154):
FACTION_RUMOR_FACTIONS: dict[str, str] = {
    "hosaka_faction_rumor": "hosaka",
    "sense_net_faction_rumor": "sense_net",
    "yakuza_faction_rumor": "yakuza",
    "loa_faction_rumor": "loa",
}
# apply_faction_rumor takes faction_id, defaults to "loa" if item_id not in dict
```

### 2. PPL Grade 5→6 growth comment (combat/multi_enemy.py, 3 LOC)

```python
# ADR-0154: PPL growth targets (per design/balance/ppl_zdr_balance.md)
# Grade 1→2: 2.00x, 2→3: 1.50x, 3→4: 1.67x, 4→5: 1.62x, 5→6: 1.20x ⚠
# Known issue: Grade 5→6 is stagnant. NG+ balance pass deferred (ADR-0130 §잔존 이슈).
PPL_GROWTH_TARGETS: dict[str, float] = {
    "1->2": 2.00,
    "2->3": 1.50,
    "3->4": 1.67,
    "4->5": 1.62,
    "5->6": 1.20,  # NG+ balance issue
}
```

### 3. i18n 확장 (data/i18n/ja.json + zh.json, 신규)

기존 en.json + ko.json 의 5 섹션 복사 + 번역:
- `salvage` (Cycle 1, 16 keys)
- `combat` (Cycle 2, 15 keys)
- `boss_phase4` (Cycle 3, 38 keys)
- `salvage` (Cycle 1)
- `intel_items` (Cycle 6, 13 keys)
- `multi_enemy` (Cycle 8, 10 keys)
- 총 92 keys × 2 langs = 184 entries

### 4. Tests 추가 (4-6 tests)

`tests/unit/test_faction_expansion.py` (NEW):
- TC-FAC-001: faction_rumor 4 variants (hosaka, sense_net, yakuza, loa)
- TC-FAC-002: faction_rumor apply with faction_id
- TC-FAC-003: faction_rumor backward-compat (item_id → "loa" default)

### 5. Pillar 정합 검증

| Pillar | 영향 | 검증 |
|---|---|---|
| P1 (The Run) | faction-specific faction_rumor + NG+ intrinsic | TC-FAC-001, 002 |
| P2 (The Matrix) | 변경 없음 | 기존 test 유지 |
| P3 (The Flatline) | 변경 없음 | 기존 test 유지 |
| P4 (The Build) | in-run only | 기존 test 유지 |
| P5 (The Style) | faction-specific 깁슨 어휘 + i18n | TC-FAC-001 |

## 영향 받는 항목

- `prototype/src/roguelike_sprawl/combat/intel_items.py` (5 LOC patch)
- `prototype/src/roguelike_sprawl/combat/multi_enemy.py` (3 LOC PPL growth comment)
- `prototype/data/i18n/ja.json` (NEW, ~92 keys)
- `prototype/data/i18n/zh.json` (NEW, ~92 keys)
- `prototype/tests/unit/test_faction_expansion.py` (NEW, 4-6 tests)
- `log.md` (Cycle 10 entry)
- `index.md` (Round 2 ADR list 갱신)
- `decisions/README.md` (0154 entry)
- `prototype/data/game_facts.json` (regenerated)

## 관련 결정

- ADR-0151 — Info Market Intel Items (faction_rumor 첫 구현)
- ADR-0130 — Balance Audit + PPL Sync (PPL rebalance 잔존 이슈)
- ADR-0010 — i18n + Content Pipeline (다국어 확장 기반)
- ADR-0110 — 모듈 사이즈 정책 (신규 모듈 0개, ADR-0110 정합)

## 변경 이력

- 2026-08-07: Draft 작성 (Cycle 10 of v1.2.0+ bridge)
- 2026-08-07: Accepted (Option 2, 사용자 확인)
  - 구현: `combat/intel_items.py` (5 LOC faction_rumor_factions dict + backward-compat fallback)
  - PPL growth: `combat/multi_enemy.py` (3 LOC PPL_GROWTH_TARGETS dict + comment)
  - 테스트: `tests/unit/test_faction_expansion.py` (NEW, 31 tests pass)
  - i18n: `data/i18n/ja.json` + `data/i18n/zh.json` (NEW, 95 keys each across 5 sections)
  - 검증: ruff clean, mypy 0 errors (172 src files, 변경 없음), pytest 4060 pass (was 4029, +31)
  - 효과: faction_rumor 4 variants (hosaka, sense_net, yakuza, loa) + 다국어 4개 (en, ko, ja, zh)
  - 후속: NG+ Grade 5→6 actual rebalance (잔존), Matrix encounter spawn variant (선택)
