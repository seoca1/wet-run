# GitHub Projects Board Setup (ADR-0030 §9)

> **Status**: Manual setup required (gh CLI not available locally)
> **Setup date**: 2026-07-04
> **Board URL**: https://github.com/users/seoca1/projects (to be created)

---

## 1. Web Setup Steps (one-time)

1. Go to https://github.com/users/seoca1/projects
2. Click **"New project"** → **"New classic project"**
3. Project name: **Wet Run Development**
4. Description: 깁슨 스프롤 3부작 기반 로그라이크 게임 개발 추적
5. Visibility: **Public**
6. Click **"Create project"**

## 2. Columns Setup

| Column | Purpose | WIP Limit |
|---|---|---|
| **Backlog** | 식별된 작업 (issue 없음) | - |
| **Ready** | 다음 스프린트 작업 (issue 있음) | - |
| **In Progress** | 진행 중 | 3 |
| **Review** | 코드 리뷰 대기 (PR 있음) | 3 |
| **Done** | 완료 | - |

## 3. Labels Setup (GitHub Repo → Issues → Labels)

기존 `labeler.yml` (12개) 외 추가:

| Label | Color | 용도 |
|---|---|---|
| `phase-7` | `#fbca04` | Phase 7 (Zone 5 zones) |
| `phase-8` | `#d93f0b` | Phase 8 (Sally) |
| `phase-9` | `#cccccc` | Phase 9 (3Jane, Neuromancer) |
| `epilogue` | `#7057ff` | Salvation Phase epilogue |
| `github-projects` | `#0e8a16` | GitHub Projects 관련 |

## 4. Issue Templates (기존 보강)

`.github/ISSUE_TEMPLATE/`에 추가:
- `phase-7.md` — Phase 7 zone 콘텐츠 보강
- `phase-8.md` — Phase 8 캐릭터 추가
- `phase-9.md` — Phase 9 Neuromancer + epilogue
- `meta.md` — 메타 작업 (문서, GitHub 설정)

## 5. Initial Cards (Backlog → Ready)

### Already Completed (move to Done)
- ✅ Phase 5 (combat, save/load, achievements, dashboards)
- ✅ Phase 6 (Graphic Novel Mode, Save slots 5→10, auto-save)
- ✅ Phase 7.1 (Suit, Wigan, Angie — 3 chars × 8 scenes)
- ✅ Phase 7.2 (Mid/Core/TA zone — 9 missions + 3 ICE)
- ✅ Phase 7.3 (10슬롯 + 자동저장)
- ✅ Phase 8 (Sally Shears — 8 scenes)
- ✅ Phase 9 (3Jane + Neuromancer — 16 scenes)
- ✅ MkDocs build + --strict 빌드
- ✅ lint/mypy 174 → 0 errors

### In Progress / Ready
- 🔄 Salvation Phase epilogue (모든 캐릭터 end state)

### Backlog (다음 세션용)
- 📋 10번째 자키 (Angie's voodoo 미래)
- 📋 GitHub Pages Wiki 추가 콘텐츠
- 📋 미션 단편 9편 매핑 (Mid/Core/TA)
- 📋 캐릭터별 통계 대시보드 강화
- 📋 Angie 6-7번째 자키 보강 (Wigan/3Jane 8자 추가 씬)

## 6. Automation

### GitHub CLI (with auth) - one-time setup
```bash
# Install gh (if needed)
brew install gh

# Auth
gh auth login

# Create project
gh project create --title "Wet Run Development" --public

# Add initial cards
gh project item-add 1 --owner seoca1 --url https://github.com/seoca1/wet-run/issues/1
```

### Auto-label (already enabled)
`.github/labeler.yml` — PR/Issue 자동 라벨링

### Auto-move
Issue close 시 자동으로 Done 컬럼으로 이동:
- Settings → Options → `Automatically move closed issues here`
- Project 설정 → Workflows → "Item closed" → Done

## 7. Update AGENTS.md

`AGENTS.md` 작업 시작 체크리스트에 GitHub Projects 보드 추가:

```markdown
## 8. 작업 시작 체크리스트
- [ ] `SESSION_SUMMARY.md` — 현재 세션 요약 (가장 먼저)
- [ ] `ROADMAP.md` 의 "Current Phase" 확인
- [ ] **GitHub Projects 보드** — https://github.com/users/seoca1/projects/1
- [ ] `decisions/README.md` 에서 미해결 결정 확인
- [ ] `CHARACTER_PATHS.md` — 캐릭터 비교
- [ ] `index.md` 에서 관련 위키 페이지 찾기
- [ ] 작업 완료 후 `log.md` 갱신
```

## 8. Verify

Web setup 완료 후:
- [ ] 보드 URL을 SESSION_SUMMARY.md에 추가
- [ ] ADR-0030 §9 체크박스 완료
- [ ] README.md에 보드 링크 추가
- [ ] log.md에 완료 기록
- [ ] 최종 commit

---

**Note**: 보드 셋업은 웹 UI에서만 가능 (gh CLI 없음). 자동화는 이후 gh CLI 가능할 때.
