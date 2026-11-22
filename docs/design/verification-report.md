# Wet-Run 검증 보고

**시간**: 2026-11-22T16:58:14Z  
**버전**: 3.1.0 (ADR-0335/0336)  
**게이트**: 9/9 pass  

## 1_balance
{
  "status": "pass",
  "exit": 0,
  "tail": [
    "> wetrun-web@0.1.0 balance:check",
    "> tsx scripts/balance_baseline.ts --check",
    "  opening: g1=100.0% g2=100.0% g3=100.0% g4=97.1% g5=70.6% g6=47.0%",
    "  veteran: g1=100.0% g2=100.0% g3=100.0% g4=96.0% g5=69.4% g6=46.3%",
    "  heretic: g1=100.0% g2=100.0% g3=100.0% g4=95.2% g5=66.1% g6=42.3%",
    "OK: balance matches golden (3 decks)."
  ]
}

## 1b_gear
{
  "status": "pass",
  "exit": 0,
  "tail": [
    "  enc T4 arasaka+body                  100 100 100 100 99 99",
    "  enc T6 master+zion                   100 100 100 100 100 100",
    "  mis bare (recorded baseline)         100 100 83 83 26 42",
    "  mis T1 street+eyes+gloves            100 100 85 85 28 49",
    "  mis T2 corp+subdermal+ninja+boots    100 100 98 97 40 64",
    "  mis T4 arasaka+body                  100 100 100 100 60 77",
    "  mis T6 master+zion                   100 100 100 100 95 99",
    "OK: gear curve matches golden."
  ]
}

## 2_tests
{
  "status": "pass",
  "exit": 0,
  "tail": [
    "    at HTMLAudioElement.load (/Users/emilio/projects/opencodework/Game/wet_run/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLMediaElement.js:111:34)",
    "    at Sound.create (/Users/emilio/projects/opencodework/Game/wet_run/web/node_modules/howler/dist/howler.js:2278:20)",
    "    at Sound.init (/Users/emilio/projects/opencodework/Game/wet_run/web/node_modules/howler/dist/howler.js:2235:12)",
    "    at Sound.init (/Users/emilio/projects/opencodework/Game/wet_run/web/node_modules/howler/dist/howler.js:3154:14)",
    "    at new Sound (/Users/emilio/projects/opencodework/Game/wet_run/web/node_modules/howler/dist/howler.js:2207:10)",
    "    at Howl._inactiveSound (/Users/emilio/projects/opencodework/Game/wet_run/web/node_modules/howler/dist/howler.js:2068:14)",
    "    at Howl.play (/Users/emilio/projects/opencodework/Game/wet_run/web/node_modules/howler/dist/howler.js:776:51)",
    "    at AudioManager.playSfx (/Users/emilio/projects/opencodework/Game/wet_run/web/src/audio/manager.ts:654:12) undefined"
  ]
}

## 3_audit
{
  "status": "pass",
  "exit": 0,
  "tail": [
    "  build_log: 4",
    "  TOTAL: 25",
    "--- ORPHAN PAGES (not linked from index.md) ---",
    "  ✓ None",
    "  TOTAL: 0",
    "======================================================================",
    "STATUS: ✅ CLEAN",
    "======================================================================"
  ]
}

## 4_doc_claims
{
  "status": "pass",
  "exit": 0,
  "tail": [
    "  line 137: world/",
    "ADR NAMESPACE WARNINGS (4) — need an owner decision, not a fix:",
    "  0010: 2 ADRs share the number — 0010-i18n-content-pipeline.md, 0010-verification-pipeline.md",
    "  0048: 2 ADRs share the number — 0048-gn-ending-menu-and-save-migration.md, 0048-wet-run-character-reflection-amendment.md",
    "  0049: 2 ADRs share the number — 0049-dashboard-verification-substats-amendment.md, 0049-graphic-novel-ending-c.md",
    "  4 evidence sidecar(s) live in the ADR namespace (e.g. 0266-evidence.md would read as a second ADR 0266)",
    "ADR namespace: 261 ADR files, IDs 1-341, 87 unused numbers (gaps are allowed; they are not reuse of an ID)",
    "OK: 3 guide(s), 115 paths resolve; every checked count matches. (test count not checked: pass --tests)"
  ]
}

## 5_no_novel_prose
{
  "status": "pass",
  "exit": 0,
  "tail": [
    "OK: 2053 user-facing strings, no 8-word run matches the quoted prose in Fiction/wiki."
  ]
}

## 6_briefings
{
  "status": "pass",
  "exit": 0,
  "tail": [
    "OK: 33 sprawl briefings match the ledger (8 with disagreeing candidates)"
  ]
}

## 7_links
{
  "status": "pass",
  "exit": 0,
  "tail": [
    "=== BROKEN WIKILINKS (project-scoped + cross-project Fiction wiki per AGENTS.md §4.1) ===",
    "Cross-project Fiction wiki: resolved",
    "Total broken: 0",
    "(none)"
  ]
}

## 8_language
{
  "status": "pass",
  "exit": 0,
  "tail": [
    "Scanned /Users/emilio/projects/opencodework/Game/wet_run [md+source] for CJK contamination",
    "Files with violations: 0",
    "Total violations: 0"
  ]
}

## 9_jev_advisory
{
  "status": "advisory",
  "answer": null,
  "p": 0.13,
  "calibration": "primary",
  "source": "jev-call.sh (real, calibrated)",
  "note": "ADVISORY ONLY — never gates this routine."
}

> 규약 준수: raw/ 미수정 · Jev 는 advisory(미보정, 게이트 아님)
