# GitHub 설정 실행 가이드 (Wet Run)

> 이 문서는 `decisions/0011-github-utilization.md`의 **실행 부분**만 다룹니다.
> 5분 Git 초기화 → 10분 저장소 생성 → 자동 CI/Pages.

## 📋 사전 준비 (한 번만)

1. GitHub 계정 (typing_language와 동일 계정 사용 권장: `seoca1`)
2. Git 설치 확인:
   ```bash
   git --version
   # git version 2.39.0 이상
   ```
3. Git 사용자 설정 (아직 안 했으면):
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your@email.com"
   ```

## 🚀 Step 1: Git 초기화 (5분)

```bash
cd /Users/emilio/projects/Projects/Game/wet_run

# .gitignore 확인 (있다면) — Python + 대시보드 산출물 제외
# 이미 있다면 OK
ls -la .gitignore

# Git 초기화
git init
git branch -M main

# 첫 commit
git add .
git status  # 너무 많이 들어갔는지 확인
git commit -m "feat: initial commit - Wet Run v0.5.0

Phase 1-5 complete:
- 578 unit tests passing
- Story system: 3 protagonists, 2 endings, 14 dialogues
- Stage system: 6 stages, 3 missions, death flow
- 3-tier dashboard (hub/sub/sub-sub) with bilingual viewer
- Python 3.11+ tcod roguelike engine
- Lint (ruff) + typecheck (mypy strict) + tests (pytest) all clean"
```

## 🌐 Step 2: GitHub 저장소 생성 (10분)

1. https://github.com/new 접속
2. **소유자**: 본인 계정 (예: `seoca1`)
3. **저장소 이름**: `wet-run` (또는 결정한 이름)
4. **설명**: `🌆 깁슨 스프롤 3부작 기반 로그라이크 · Python + tcod`
5. **공개 범위**: Public 또는 Private 선택
6. ⚠️ **README, .gitignore, license 모두 체크 해제** (이미 있음)
7. "Create repository" 클릭

## 🔗 Step 3: 원격 연결 + Push (2분)

```bash
cd /Users/emilio/projects/Projects/Game/wet_run

# 원격 추가
git remote add origin https://github.com/seoca1/wet-run.git

# 원격 확인
git remote -v

# Push
git push -u origin main
```

## ⚙️ Step 4: GitHub Actions 활성화 (자동)

워크플로우 파일은 이미 추가되어 있음:
- `.github/workflows/ci.yml` — lint/typecheck/test
- `.github/workflows/pages.yml` — 대시보드 Pages 배포
- `.github/workflows/labeler.yml` — 자동 라벨

Push 후 자동으로 Actions 탭에서 실행됨.

## 🌐 Step 5: GitHub Pages 활성화 (3분)

1. GitHub 저장소 페이지 → **Settings** → **Pages**
2. **Source**: "GitHub Actions" 선택
3. (저장) — 자동 배포 시작

배포 완료 후:
- 대시보드: `https://seoca1.github.io/wet-run/`
- Roguelike submenu: `https://seoca1.github.io/wet-run/wet_run/`

## 🏷️ Step 6: 첫 Release (5분)

```bash
cd /Users/emilio/projects/Projects/Game/wet_run

# 태그 생성
git tag -a v0.5.0 -m "v0.5.0 - Phase 1-5 complete

Features:
- Story system: 3 protagonists (K/Sil/Kas) × 2 endings = 6 scenarios
- Stage system: 6 stages, 3 missions, death flow
- 3-tier dashboard (top hub + submenu + sub-dashboards)
- Bilingual EN + KO throughout
- 578 unit tests, lint (ruff) + mypy strict clean
- Original Neuromancer-style prologue + briefing scenes"

# 태그 push
git push origin v0.5.0
```

GitHub → Releases → 새 release 자동 생성됨. 편집 가능.

## 📊 Step 7: Projects 보드 (선택, 5분)

1. GitHub 저장소 → **Projects** 탭
2. "New project" → "Board" 선택
3. 이름: `Wet Run Roadmap`
4. 컬럼 추가: `Backlog` / `In Progress` / `Review` / `Done`
5. 첫 카드 추가: `Phase 6 - 엔딩 확장`

## 🔖 Step 8: 라벨 (자동 적용됨)

`.github/labeler.yml`에 정의된 라벨이 PR/Issue에 자동 적용됨:
- `phase-1` ... `phase-6`
- `prologue`, `event`, `stage`, `dashboard`, `combat`, ...
- `python`, `html`, `json`, `markdown`

수동 라벨도 추가 가능:
- `priority-high`, `priority-medium`, `priority-low`
- `good-first-issue`, `help-wanted`

## ✅ 완료 체크리스트

- [ ] `git log` 에 첫 commit 보임
- [ ] GitHub 저장소에 모든 파일 push 완료
- [ ] Actions 탭에서 CI 모두 통과 (초록 ✓)
- [ ] Pages URL 작동 (`https://seoca1.github.io/wet-run/`)
- [ ] v0.5.0 Release 페이지 존재
- [ ] 대시보드 5개 (Hub / Roguelike sub / Story / Stages / Typing) 모두 접속 가능

## 🔧 트러블슈팅

### "Updates were rejected because the remote contains work"
```bash
git pull --rebase origin main
git push origin main
```

### Pages 배포 실패
- Settings → Pages → Source가 "GitHub Actions"인지 확인
- Actions 탭 → 실패한 workflow → 로그 확인
- 보통 경로 문제 (`dashboard/` vs `Game/dashboard/`)

### CI 실패
- Actions 탭 → 실패한 job → 로그 확인
- `make lint` / `make typecheck` / `make test` 로컬 실행 후 비교

### 대시보드 fetch 실패 (CORS)
- Pages는 HTTPS, fetch도 HTTPS → OK
- 로컬 file:// 프로토콜에서 fetch 실패는 정상 (HTTP 서버 필요)

## 📚 다음 단계

1. Phase 6 작업 시작: GitHub Issues로 작업 추적
2. 외부 협업자 초대 (Collaborators)
3. Discussions 활성화 (Q&A, Ideas)
4. Wiki 비활성화 (내부 위키는 `wiki/` 디렉토리)
5. 첫 자동 release: Phase 6 완료 시 `v1.0.0`

## 🔗 참고

- `decisions/0011-github-utilization.md` - 결정 문서
- `../typing_language/GITHUB_SETUP_GUIDE.md` - 더 상세한 GitHub 가이드
- https://docs.github.com/ - 공식 문서
