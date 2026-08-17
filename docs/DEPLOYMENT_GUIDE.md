# 자동 배포 가이드 (Automated Deployment Guide)

> 깁슨 스프롤 로그라이크 — Dashboard가 모든 push마다 자동 배포되는 방식을 설명합니다.

## TL;DR

**`main` 브랜치에 push하는 순간, 1-2분 내로 https://seoca1.github.io/roguelike-sprawl/ 에 자동 반영됩니다.**

수동 작업 0회. Pages UI 클릭 불필요. GitHub UI 로그인 불필요.

---

## 1. 배포 파이프라인 (Deployment Pipeline)

```
로컬 코드 수정
    ↓ git commit -m "..."
git push origin main
    ↓
GitHub Actions 트리거 (조건: main push)
    ↓
┌──────────────────────────────────────┐
│  CI Workflow (.github/workflows/ci.yml)        │
│  - Lint (ruff)                                  │
│  - Typecheck (mypy strict)                      │
│  - Test (pytest) — 3.11 + 3.12                 │
│  - Dashboard validation                         │
└──────────────────────────────────────┘
    ↓ (성공 시)
┌──────────────────────────────────────┐
│  Pages Workflow (.github/workflows/pages.yml)  │
│  Step 1: 8 dashboard HTML 복사 → _pages/        │
│  Step 2: design/ 복사 (for fetch)               │
│  Step 3: favicon.svg 복사                       │
│  Step 4: peaceiris/actions-gh-pages@v4          │
│          → gh-pages 브랜치로 force_orphan push   │
│  Step 5: (선택) API로 Pages 활성화              │
└──────────────────────────────────────┘
    ↓
GitHub Pages 자동 감지 (Source: gh-pages)
    ↓ 1-2분
라이브: https://seoca1.github.io/roguelike-sprawl/
```

## 2. 자동 트리거 조건

`.github/workflows/pages.yml`:
```yaml
on:
  push:
    branches: [main]   # ← main push 시 자동 실행
  workflow_dispatch:   # ← 수동 트리거 가능
```

**main에 push만 하면 자동 배포.** feature 브랜치는 배포 안 됨 (의도적 — 검증된 main만 라이브).

## 3. 일반 작업 흐름 (Typical Workflow)

### 3.1 Dashboard 수정
```bash
# 1. 파일 수정 (e.g. dashboard/story.html)
# 2. 검증
make validate-dashboard   # 또는 직접 dashboard JSON 확인

# 3. Commit + push
git add dashboard/
git commit -m "feat(dashboard): update story content"
git push origin main

# 4. 1-2분 대기
# 5. https://seoca1.github.io/roguelike-sprawl/ 에서 확인
```

### 3.2 새 Dashboard 추가
```bash
# 1. dashboard/newpage.html 생성
# 2. pages.yml의 _pages 복사 단계에 추가
# 3. _system/top-nav 업데이트 (다른 dashboard의 nav)
# 4. 테스트 작성
# 5. Commit + push → 자동 배포
```

### 3.3 디자인/스펙 JSON 수정
```bash
# 1. design/systems/*.json 수정
# 2. 자동 deploy → dashboard에서 fetch()로 즉시 반영
```

## 4. 배포 확인 (Verify Deployment)

### 4.1 GitHub Actions UI
```
https://github.com/seoca1/roguelike-sprawl/actions
```
- ✅ 초록 = 배포 성공
- ❌ 빨강 = 빌드 실패 (로그 확인)

### 4.2 CLI로 빠른 검증
```bash
# Pages 사이트
curl -sI https://seoca1.github.io/roguelike-sprawl/

# Pages API
curl -s https://api.github.com/repos/seoca1/wet-run/pages

# 최근 workflow run 상태
gh run list --repo seoca1/wet-run --limit 3
```

### 4.3 캐시 무효화 (Hard Refresh)
- **Mac**: `Cmd + Shift + R`
- **Windows/Linux**: `Ctrl + Shift + R`
- 또는 시크릿 창

## 5. 배포 실패 시 (Troubleshooting)

### 5.1 Pages 빌드 실패
**원인**: dashboard HTML에 구문 오류, 잘못된 상대 경로, etc.

**대응**:
1. Actions 탭 → 빨간 run 클릭 → 로그 확인
2. `test_dashboard_meta` 같은 dashboard validation 테스트가 보통 잡음
3. 로컬에서 `make validate-dashboard` 실행

### 5.2 사이트가 404
**원인 1**: 첫 push 직후 (캐시) → 5분 대기
**원인 2**: Pages가 비활성화됨 → Settings → Pages → Source = "Deploy from a branch" 확인

### 5.3 오래된 콘텐츠가 보임
**원인**: CDN 캐시 → Hard refresh (Cmd+Shift+R)

### 5.4 gh-pages 브랜치 문제
```bash
# 로컬에서 확인
git fetch origin gh-pages
git log origin/gh-pages --oneline | head -5

# 강제 재동기화 (workflow re-run이 더 안전)
```

## 6. 롤백 (Rollback)

### 6.1 가장 안전한 방법: 직전 commit으로 revert
```bash
git revert HEAD
git push origin main
# → 1-2분 후 직전 버전이 라이브
```

### 6.2 gh-pages 브랜치를 특정 commit으로 강제 reset
```bash
git fetch origin gh-pages
git push origin --delete gh-pages  # 또는 force push
# → 다음 push 시 workflow가 새 gh-pages 생성
```

### 6.3 Pages 일시 비활성화
- Settings → Pages → Source = "None" (긴급 시)

## 7. 환경 설정 (One-time Setup, 이미 완료됨)

다음은 1회만 필요했고, 이미 적용된 상태입니다:

- ✅ GitHub Pages: `Settings → Pages → Source = Deploy from a branch, gh-pages / root`
- ✅ Repository: `seoca1/wet-run` (public)
- ✅ Workflow: `.github/workflows/pages.yml` (peaceiris/actions-gh-pages@v4)
- ✅ `_pages` artifact: 8 dashboard HTML + design/ + favicon.svg

**재설정 불필요.** 그냥 push만 하면 됨.

## 8. 모니터링 (Optional)

### 8.1 이메일 알림
- GitHub Settings → Notifications → Actions → Send notifications for failed workflows
- 실패 시에만 메일

### 8.2 Slack/Discord 웹훅
`.github/workflows/pages.yml`에 step 추가:
```yaml
- name: Notify on failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {"text": "❌ Pages deploy failed: ${{ github.run_id }}"}
  env:
    SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
```

## 9. 빠른 레퍼런스

| 작업 | 명령 | 시간 |
|---|---|---|
| Dashboard 수정 후 라이브 반영 | `git push` | 1-2분 |
| 강제 재배포 (no commit) | Actions → "Deploy Dashboard" → Run workflow | 1-2분 |
| 배포 상태 확인 | Actions 탭 또는 `curl -sI https://seoca1.github.io/...` | 0초 |
| 롤백 | `git revert HEAD && git push` | 1-2분 |

## 10. 한계 (Limitations)

- **빌드 시간**: push 후 1-2분. 즉시 반영 아님.
- **퍼블릭 전용**: `seoca1/wet-run`은 public. 비공개 repo는 GitHub Pro 필요.
- **도메인**: `seoca1.github.io/roguelike-sprawl/`만 지원. 커스텀 도메인은 CNAME 추가 필요.

---

**요약**: `git push`만 하면 끝. GitHub UI 클릭 0회.
