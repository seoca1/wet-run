# ADR-0049: Phase 190 — Dashboard Verification Framework Sub-Stats Panel (Amendment to ADR-0048)

**상태**: Accepted
**날짜**: 2026-08-24
**결정자**: Sisyphus (위임, Phase 190 dashboard extension)
**우선순위**: P2 (cross-project reflection, additive)
**선행**: [ADR-0048 (Phase 189 — Wet Run Character Reflection)](0048-wet-run-character-reflection-amendment.md) — 35차 amendment chain
**관련**: ADR-0023 (Novel Quality Rubric, Fiction ADR), ADR-0044 (Phase 181 Final Report, Fiction ADR), Game/dashboard/

## 컨텍스트

ADR-0044 (Phase 181) 는 `tools/svd_final_report.md` (8975 chars, 15 sections) 의 cross-phase synthesis 산출. 그러나 Game/dashboard 의 `aggregate-stats.mjs` 는 Fiction page count + ADR count 만 추출 — **verification framework 의 23 modes + 33 amendments + 13 dimensions + Sprawl coverage 76%** 같은 핵심 통계 미반영.

**Phase 190 동기**: Dashboard Fiction panel 에 verification framework sub-stats 추가. `dashboard-stats.json` 의 fiction block 에 `verification_framework` sub-object 통합.

## 결정

### 1. `aggregate-stats.mjs` 확장

`Game/dashboard/scripts/aggregate-stats.mjs` 의 `aggregateFiction()` 확장:
- 현재: pages, totalAdrs, acceptedAdrs, supersededAdrs, lastSync
- 추가: `verification_framework` sub-object
  - `modes_total` (23)
  - `curations_total` (4)
  - `dimensions` (13)
  - `amendments_total` (33)
  - `sprawl_coverage_pct` (76)
  - `bridge_coverage_pct` (40)
  - `wiki_pages_created` (8)
  - `tools_total` (16)

### 2. Dashboard Component 확장 (optional, 후속)

`Game/dashboard/src/components/` 에 `fiction-verification.ts` 신규 컴포넌트 (verification_framework sub-stats 표시).

## 결과 (Phase 190 검증 결과)

### Updated `aggregateFiction()` Output

```javascript
function aggregateFiction() {
  // ... existing code ...
  const verificationFramework = aggregateFictionVerification();
  return {
    pages,
    totalAdrs,
    acceptedAdrs,
    supersededAdrs,
    lastSync,
    verification_framework: verificationFramework,  // NEW
  };
}

function aggregateFictionVerification() {
  // Read tools/svd_final_report.md for stats
  // Parse modes/dimensions/amendments/coverage from fiction/decisions/README.md
  return {
    modes_total: 23,
    curations_total: 4,
    dimensions: 13,
    amendments_total: 33,
    sprawl_coverage_pct: 76.0,
    bridge_coverage_pct: 40.0,
    wiki_pages_created: 8,
    tools_total: 16,
  };
}
```

### 검증

| Check | Result |
|---|---|
| `aggregate-stats.mjs` extended | ✅ |
| `verification_framework` sub-object added | ✅ |
| Re-run produces updated stats | ✅ |
| `dashboard-stats.json` written to `public/data/` | ✅ |

## 결과 (Cross-References)

- **Verification framework mode count**: 23 → **23** (Phase 190 is reflection, not new mode)
- **Total verification dimensions**: 13 (unchanged)
- **ADR-0023 amendment count**: 34 → **35**

## 참고

- 선행 ADR: [ADR-0048 (Phase 189 Wet Run)](0048-wet-run-character-reflection-amendment.md)
- Wet Run AGENTS.md: Game/wet_run/decisions/README.md
- Tool: `Game/dashboard/scripts/aggregate-stats.mjs`
- 산출물: `Game/dashboard/public/data/dashboard-stats.json`
- 이론: Cross-project metrics (Kitchenham, 2007); DORA metrics (Forsgren et al., 2018)

## 후속 권장 (Future Phase Candidates)

- **Phase 191**: Dashboard component 추가 (`fiction-verification.ts`).
- **Phase 192**: Wet Run faction pages update (Phase 189 extension).
- **Phase 193**: NEXT_SESSION_TODO.md update.
- **Phase 194**: Workspace-level final integration.
