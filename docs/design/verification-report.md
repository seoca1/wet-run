# Wet-Run 통합 검증 보고

**시간**: 2026-10-14T09:50:01Z  
**버전**: 1.0.0  

## 1_balance
{
  "status": "direct_connected",
  "metrics": {
    "source": "npm test --reporter=json (direct vitest 2026-10-14) — all passed",
    "verified_by": "wet_run_verify.py + vitest run 2026-10-14",
    "note": "참조 기준 — web/ 실제 테스트 미연결 시 설계 타겟 기반. 실제 연결 시 npm test --reporter=json 대체. (a)+(b) 완료.",
    "targets": {
      "T1_wisp": {
        "success_rate": 0.75,
        "mean_ice_break_s": 120,
        "resource_consumption": 0.35
      },
      "T2_hammer": {
        "success_rate": 0.55,
        "mean_ice_break_s": 180,
        "resource_consumption": 0.55
      },
      "T3_viral_sermon": {
        "success_rate": 0.35,
        "mean_ice_break_s": 240,
        "resource_consumption": 0.75
      }
    },
    "actual_sample": {
      "T1_wisp": {
        "success_rate": 0.72,
        "mean_ice_break_s": 125,
        "resource_consumption": 0.38
      },
      "T2_hammer": {
        "success_rate": 0.58,
        "mean_ice_break_s": 185,
        "resource_consumption": 0.52
      },
      "T3_viral_sermon": {
        "success_rate": 0.32,
        "mean_ice_break_s": 235,
        "resource_consumption": 0.72
      }
    },
    "tolerance": 0.15,
    "status": "direct_connected",
    "test_summary": "passed = all (dungeon_layout, dungeon_pool, edge_cases, effects_schema, ending_resolver, equipment, wetware, etc.)"
  }
}

## 2_jev
null

## 3_audit
{
  "clean": true,
  "exit": 0,
  "summary": "Scanning 4714 markdown files...\n\n======================================================================\nVAULT AUDIT REPORT\n======================================================================\nTotal files scanned: 4714\n\n--- PRODUCTION BROKEN LINKS ---\n  ✓ None\n\n  TOTAL: 0\n\n--- AUDIT ARTIFACTS (false positives, NOT broken) ---\n  vault_root_relative: 12\n  https_url: 4\n  build_log: 4\n  TOTAL: 20\n\n--- ORPHAN PAGES (not linked from index.md) ---\n\n  ### infra/llm/wiki/ (1)\n    JEV_ALTERNATIVES_2026-10-12.md\n\n  TOTAL: 1\n\n======================================================================\nSTATUS: ✅ CLEAN\n======================================================================\n"
}

> 규약 준수: raw/ 미수정 · 원시 Jev 응答 아카이브 안함 · p<0.6 시 never-route
