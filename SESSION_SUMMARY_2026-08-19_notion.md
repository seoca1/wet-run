# Wet Run — Session Summary 2026-08-19 (Part 2: Notion 통합)

> **Session scope**: Notion 통합 + 명칭 일관성. Same-day continuation
> of SESSION_SUMMARY_2026-08-19.md (which covered CI hygiene + Pages
> deploy recovery). This file covers the second half of the day:
> Notion progress report, Wet Run 명칭 변경, design 문서 66-page 통합.

## 1. Overview

After recovering the live dashboard in the first half of the day, the
session pivoted to a different infrastructure layer: Notion. Two
distinct needs converged:

1. **Session close documentation** — the first half's work needed a
   progress report in the existing `PROGRESS_REPORT_YYYY-MM-DD_NOTION_READY`
   series (last entry 2026-07-25, ~25 days stale).
2. **Design document access** — the user wanted a way to view all
   66 design files (18,573 lines) in Notion rather than only on
   GitHub/CLI.

A third discovery emerged: the Notion parent page was still titled
"Roguelike Sprawl - 프로젝트 가이드" — the same pre-rename naming
gap that the dashboard had.

## 2. Major Operations (4 total)

### 2.1 Progress report `PROGRESS_REPORT_2026-08-19_NOTION_READY`
- **Page ID**: `3c1f643d-3530-813a-8fc8-da99ba3f7c30`
- **URL**: https://app.notion.com/p/PROGRESS_REPORT_2026-08-19_NOTION_READY-3c1f643d3530813a8fc8da99ba3f7c30
- **Content**: 54 blocks (H1, Quote, Table 3x9, 5 work sections, verification, push log, backlog, related docs)
- **Parent**: `38df643d-3530-8103-af2c-e2277b4bcdfa` (Roguelike Sprawl → Wet Run)
- **Format**: Matches the 2026-07-25 PROGRESS_REPORT_YYYY-MM-DD_NOTION_READY template

### 2.2 Notion 명칭 변경: Roguelike Sprawl → Wet Run
- **Parent page rename**: `Roguelike Sprawl - 프로젝트 가이드` → **`Wet Run - 프로젝트 가이드`**
- **5 body updates** on the same page (1 H1, 1 code block, 2 URL bullets):
  - `cd ~/projects/Projects/Game/roguelike_sprawl/prototype` → `wet_run`
  - `github.com/seoca1/roguelike-sprawl` → `wet-run`
  - `seoca1.github.io/roguelike-sprawl/` → `wet-run/`
- **ROGUELIKE residual hits**: 0
- **Preserved historical reference**: 1 paragraph in the new progress report kept "ROGUELIKE SPRAWL" wording as accurate documentation of pre-fix state

### 2.3 Design Documents 통합 (66 pages, 3-tier)
- **Parent**: `📚 Design Documents` (3c1f643d-3530-81dc-8dae-d2dbf43f1bc4)
- **Structure**:
  - 5 Top-Level Specs (GDD, Pillars, Core Loop, Story Skeleton, Glossary)
  - 3 Auxiliary Specs (Character Paths, Content Expansion Plan, Gibson Tone Audit)
  - 1 Story (characters + prologue inlined, 191 blocks, 3 chunks)
  - 1 Systems Hub + 23 children (1:1 file mapping)
  - 1 Scenario Hub + 30 children (1:1 file mapping)
  - 1 Balance (PPL & ZDR)
  - 1 Research (2 files inlined, 343 blocks, 5 chunks)
- **Total**: 13 direct children + 53 nested = **66 pages** ✅
- **Tooling**: Built 2 reusable Python helpers at `/tmp/notion-payload/`:
  - `md2notion.py` — Markdown → Notion blocks converter (headings, lists, code, tables, quotes, callouts)
  - `notion_helper.py` — Notion API wrapper (create_page, append_blocks, upload_markdown_file, search)
- **API calls**: ~150 total (create + append with 90-block chunks under the 100-block API limit)

### 2.4 Largest content per category
- **Engagement** (systems): 498 blocks — single largest child page
- **Combat** (systems): 233 blocks
- **Missions** (systems): 188 blocks
- **Graphic Novel** (scenario): 180 blocks
- **Death & Restart** (scenario): 156 blocks
- **Story (characters + prologue)**: 191 blocks
- **Research (2 files inlined)**: 343 blocks

## 3. Verification

```
📚 Design Documents direct children: 13  ✅
   (5 top + 3 aux + 1 story + 1 systems hub + 1 scenario hub + 1 balance + 1 research)
📚 All nested descendants:           53  ✅
   (23 systems children + 30 scenario children)
📚 Total pages in tree:               66  ✅ (matches design/ file count)
```

Recursive API call confirmed all 66 pages exist and are children of
the new `📚 Design Documents` parent.

## 4. Cross-Project Sync Status (end of day)

| Location | Status |
|---|---|
| GitHub repo `seoca1/wet-run` | ✅ renamed 2026-08-17 |
| GitHub Pages URL `seoca1.github.io/wet-run/` | ✅ live (recovered 08:36 UTC) |
| Python package `wet_run` | ✅ |
| Dashboard `index.html` title | ✅ Wet Run |
| Notion parent page title | ✅ Wet Run - 프로젝트 가이드 (changed 08:37 UTC) |
| Notion progress report | ✅ PROGRESS_REPORT_2026-08-19_NOTION_READY (created 08:35 UTC) |
| Notion design docs | ✅ 66 pages (created 08:55 UTC) |

All seven surfaces now consistent on "Wet Run" naming.

## 5. Decisions / Out-of-Scope

- **No new ADRs needed**: This work is operational (CI hygiene,
  Notion mirroring), not design-level. Per AGENTS.md, ADRs are
  for "결정 사항" (decisions), not session reports.
- **AGENTS.md §4.0 Notion policy compliance**: ✅ Only meta docs
  (progress reports, design notes) uploaded. No derivative fiction,
  no game card bodies, no chapter text.
- **Cross-project deps respected**: No Fiction wiki touched,
  no Language project touched. Game/wet_run self-contained.

## 6. Next-Session Backlog (carried forward)

| Item | Effort | Source |
|---|---|---|
| wiki drift cleanup (146 broken wikilinks) | Medium | SESSION_SUMMARY_2026-08-19.md §3.1 |
| CI pytest 3.12 verify (no local 3.12) | Low | SESSION_SUMMARY_2026-08-19.md §5 |
| README badges sync (5578 → 5700) | Low | SESSION_SUMMARY_2026-08-19.md §5 |
| `build_dashboard.py` regen (81 vs 72 mismatch) | Low | SESSION_SUMMARY_2026-08-19.md §5 |
| Notion parent TOC enhancement (mention blocks) | Low | SESSION_SUMMARY_2026-08-19_notion.md §7 |
| Notion mirror automation (GitHub Action) | Medium | SESSION_SUMMARY_2026-08-19_notion.md §7 |

## 7. Files Touched This Half

| File | Change |
|---|---|
| `Game/wet_run/SESSION_SUMMARY_2026-08-19_notion.md` | New (this file) |
| `Game/wet_run/SESSION_SUMMARY.md` | Index → this file |
| `Game/wet_run/log.md` | New SESSION CLOSE entry (Notion section) |
| `Projects/log.md` | New cross-project SESSION CLOSE entry |
| Notion parent page | 5 body updates (rename) |
| Notion | 66 new pages under `📚 Design Documents` |
| `/tmp/notion-payload/{md2notion,notion_helper}.py` | New tooling (outside repo) |

## 8. Sessions Index Update

Previous: `SESSION_SUMMARY_2026-08-19.md` (CI hygiene + Pages deploy).
**Current**: **this file** (`SESSION_SUMMARY_2026-08-19_notion.md`).
