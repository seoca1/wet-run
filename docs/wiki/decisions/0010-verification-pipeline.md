# 검증 파이프라인 아키텍처 (Verification Pipeline)

> **버전**: 0.1.0  
> **관련**: `docs/design/verification-framework.md`, `scripts/wet_run_verify.py`, `AGENTS.md` §3.1

## 구조

```
web/ (Vitest) ──→ balance_check() ──┐
                                     ├──→ wet_run_verify.py ──→ docs/design/verification-report.md
jev-alt-eval (WF1 gold) → jev_check()─┘
audit_vault.py ───────────→ audit_check()─┘
```

## 규약

- `raw/` (삭제됨) / `data/raw/` 비활성: 접근만
- Jev 원시 응답 아카이브 금지 (advisory 출력만)
- p < 0.6 → never-route (local advisory)
- 세션 종료 전 `audit_vault` 0 확인
