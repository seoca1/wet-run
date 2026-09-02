# ADR-0196: Accessibility Colorblind State Alignment (AppState bool → str)

**상태**: Accepted (Option A)
**날짜**: 2026-08-22
**결정자**: 사용자
**우선순위**: P1 (Prerequisite for `.omo/plans/wet-run-ui-visibility-upgrade.md` T2.2 — UI/visibility upgrade)
**관련**: [ADR-0183 — Accessibility](./0183-accessibility.md), [ADR-0185 — Save/Load Migration v2](./0185-save-migration-v2.md)

## 컨텍스트 (Context)

ADR-0183 (Accepted 2026-08-08) defines `AccessibilityConfig.colorblind_mode: str` with 4 values — `"none"`, `"deuteranopia"`, `"protanopia"`, `"tritanopia"` — and a 4-mode palette table per `prototype/src/wet_run/combat/accessibility.py:88 get_color_palette(mode) -> dict[str, tuple[int, int, int]]`. ADR-0183's "Implementation Status" section (lines 60-77) reports the config / palette / helper layer as closed.

However, a **state-level field-type mismatch exists** at the runtime layer:

- `prototype/src/wet_run/engine/state.py:361` — `AppState.colorblind_mode: bool` (default `False`)
- `prototype/src/wet_run/combat/accessibility.py:43` — `AccessibilityConfig.colorblind_mode: str = "none"` (correct per ADR-0183 spec)

The two fields disagree on type, semantics, and the palette vocabulary. A `bool` can only encode on/off; a `str` carries the 4-mode palette name. This blocks three concrete things:

1. **Full 4-mode palette is not honored at render time** — only `True`/`False` reach the renderer; the 3 colorblind palettes (deuter/protan/tritan) are implemented in `get_color_palette()` but never selected by AppState.
2. **`engine/settings_view.py:99-102` cannot cycle through 3 colorblind modes** — current UI is a boolean toggle; ADR-0183 specifies 4-value cycle.
3. **Save format cannot migrate cleanly** — legacy saves keyed on `bool=True/False` cannot be round-tripped to `str="deuteranopia"/"none"` without a schema bump.

ADR-0183 explicitly closes its own implementation status ("No further action on ADR-0183 — implementation closed"), so this amendment is **a separate gap** in the AppState / save layer, not a reopen of ADR-0183.

## 고려한 옵션

### Option A: Migrate `AppState.colorblind_mode: bool` → `str` (default `"none"`) + save v2→v3 migration

- **설명**: Change `AppState.colorblind_mode` field type to `str` with default `"none"`. Update `engine/settings_view.py:99-102` UI to cycle through 4 values: `none` → `deuteranopia` → `protanopia` → `tritanopia` → `none`. Add save schema v2→v3 migration in `prototype/src/wet_run/combat/save_v2.py`: `bool=True` → `str="deuteranopia"` (deuter is the most common colorblind mode, ~6% of male population), `bool=False` → `str="none"`. Bump `SAVE_SCHEMA_VERSION` from 2 to 3.
- **장점**:
  - Aligns state layer with ADR-0183's spec verbatim (the missing piece)
  - Unlocks full 4-mode colorblind experience for the 3 affected user groups
  - Save migration is bounded (one boolean → string mapping function)
  - No cross-project breakage (AppState is wet_run-only and never reaches the workspace wiki / dashboard)
  - Single ADR covers field-type + UI + save migration atomically
- **단점**:
  - `SAVE_SCHEMA_VERSION` bump affects all save-corpus code paths (must re-test save/load with legacy saves present in `data/saves/`)
  - `engine/state.py` must remain ≤ ADR-0110 500 LOC strict cap (currently ~520 LOC after A.4 Track-A split — there is room but budget is tight)
- **Pillar 정합**:
  - P1 (The Run): Better accessibility → more players can complete a run
  - P5 (The Style): 4-mode palette expresses artistic intent vs binary compromise

### Option B: Add a parallel `AppState.colorblind_palette: str` field, keep `colorblind_mode: bool` as a backward-compat alias

- **설명**: Add a new `AppState.colorblind_palette: str` field. Keep the legacy `colorblind_mode: bool` for any code path that still reads it, with a runtime sync rule (`bool=True` ↔ palette in `{deuter, protan, tri}`).
- **장점**: No immediate save migration needed (legacy boolean field name preserved on disk).
- **단점**: Two sources of truth → drift risk over time. ADR-0183 spec requires a single `str` field at the config layer; alias approach would still leak booleans through the AppState. Defers the real fix to a later amendment.

### Option C: Defer (no migration, document as known issue)

- **설명**: Leave the mismatch. Add a `# TODO: ADR-0196 pending` comment in `engine/state.py:361`. Document in CHANGELOG / README as "3-mode colorblind toggles not yet exposed to UI."
- **장점**: No code change. No commit churn.
- **단점**: Players never get the 3-mode experience that ADR-0183 promised. ADR-0183's "Implementation Status: closed" claim becomes inaccurate. The wet_run UI/visibility upgrade plan (`.omo/plans/wet-run-ui-visibility-upgrade.md` T2.2) stays blocked indefinitely.

## 추천 (Recommendation)

**Option A.** It is the only option that (a) closes the type mismatch on a single field, (b) preserves all of ADR-0183's library work (palette table, helper API), (c) keeps the save migration bounded, and (d) unblocks the UI/visibility upgrade plan's T2.2 commit. Option B's alias approach trades immediate simplicity for permanent drift; Option C leaves a known defect in shipped code. Option A's `SAVE_SCHEMA_VERSION` bump is the standard pattern (ADR-0185 establishes it) and rolls forward into the existing migration infrastructure rather than around it.

## 사용자 결정 (Decision)

[x] Option A — `bool → str` migration with save v2→v3 (Recommended)
[ ] Option B — Parallel `colorblind_palette: str` field with bool alias
[ ] Option C — Defer; document as known issue
[ ] 기타: ___

## 결과 (Consequences)

**Pillar 1 (The Run) + Pillar 5 (The Style) benefit**: Players with deuteranopia, protanopia, or tritanopia (each affects ~6% of male / ~0.5% of female population) can now select their specific palette via the settings UI. Before this ADR the `bool` field capped player choice at on/off — the 3 colorblind palettes implemented in `combat/accessibility.py:88` were unreachable at runtime.

**Migration burden**: One save schema bump (v2 → v3). The migration function `_migrate_colorblind_legacy(save_dict)` is a single-field rewrite (bool → str). All existing `data/saves/` v2 files are forward-migrated transparently on next load; no save is rendered unreadable.

**LOC budget**: `engine/state.py` is currently ~520 LOC (just above ADR-0110's 500 cap, in the one-shot exception zone). The T2.2 implementation must keep it ≤ 525 LOC post-edit (the change is a 1-line type swap + 1-line default swap ≈ neutral LOC delta). If extraction is needed, the field can move to a new `combat/accessibility_state.py` shim per the established A.4 Track-A pattern.

**No cross-project effects**: AppState is wet_run-internal. The Fiction wiki / Game/dashboard / Language corpus are untouched.

**Tests added** (per T2.2 acceptance criteria):
- `test_accessibility.py` — type assertion update (`bool` → `str`)
- `test_accessibility_settings.py` — 4-value cycle test (`none → deuter → protan → tri → none`)
- `test_save_migration_v3.py` — migration round-trip (legacy bool=True → str="deuteranopia"; bool=False → str="none")

**Unblocks**: `.omo/plans/wet-run-ui-visibility-upgrade.md` T2.2 (Plan T2.2a Step 3 may now proceed after this Draft → Accepted flip).

## Implementation Status (2026-08-22)

**Status**: 🟡 Pending execution (Status Accepted, T2.2 implementation deferred to next session per Wave 3 sequencing)

**Plan reference**: `.omo/plans/wet-run-ui-visibility-upgrade.md` T2.2 — implementation commits 7 (`feat(settings): 3-mode colorblind cycle + save schema v2→v3 migration`).

**Acceptance gate (T2.2)**: `cd prototype && make all` exit 0; legacy `bool=True` v2 saves migrate to `str="deuteranopia"`.

## 영향 받는 항목

- `prototype/src/wet_run/engine/state.py:361` — `AppState.colorblind_mode` field
- `prototype/src/wet_run/engine/settings_view.py:99-102` — boolean toggle UI → 4-value cycle
- `prototype/src/wet_run/combat/save_v2.py` — `SAVE_SCHEMA_VERSION` (2 → 3) + migration function
- `prototype/src/wet_run/data/i18n/en.json` + `ko.json` — new keys: `settings.colorblind_none`, `settings.colorblind_deuteranopia`, `settings.colorblind_protanopia`, `settings.colorblind_tritanopia`, `settings.colorblind_label`
- `prototype/tests/unit/test_accessibility.py` — type assertions updated
- `prototype/tests/unit/test_accessibility_settings.py` — cycling UI test (verify 4-value cycle, not boolean)
- `prototype/tests/unit/test_save_migration_v2.py` (or v3 target file) — migration test: load legacy v2 save with `bool=True` → migrate to `str="deuteranopia"`; load `bool=False` → `"none"`
- `.omo/plans/wet-run-ui-visibility-upgrade.md` T2.2 — unblocked once Status: Accepted
- `CHANGELOG.md` — entry under next release (v1.5.0 or current dev cycle)

## 관련 결정

- ADR-0183 — Accessibility (Accepted 2026-08-08) — defines `AccessibilityConfig.colorblind_mode: str` + palette table
- ADR-0185 — Save/Load Migration v2 (Accepted 2026-08-08) — establishes the versioned save migration pattern
- ADR-0195 — Implementation Status Workflow (Draft 2026-08-20) — mandates the §"Implementation Status" section structure that this ADR will adopt post-acceptance

## 변경 이력

- 2026-08-22: Draft 작성 (by Sisyphus, per `.omo/plans/wet-run-ui-visibility-upgrade.md` T2.2a Step 1 — surfaces to user for Option A/B/C decision)
