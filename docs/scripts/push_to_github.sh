#!/bin/bash
# GitHub Push Helper - 저장소 생성 후 실행
# 사용법: ./docs/scripts/push_to_github.sh

set -e

REPO_URL="https://github.com/seoca1/wet-run.git"
cd "$(dirname "$0")/.."

echo "=========================================="
echo "  Wet Run — GitHub Push"
echo "=========================================="
echo ""

# Check git state
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not a git repository"
    exit 1
fi

# Check remote
if ! git remote -v | grep -q "origin"; then
    echo "→ Adding remote origin..."
    git remote add origin "$REPO_URL"
fi

echo "→ Current remote:"
git remote -v | head -2
echo ""

# Verify commit exists
COMMIT=$(git rev-parse --short HEAD)
echo "→ Latest commit: $COMMIT"
echo ""

# Confirm
echo "이 스크립트는 다음을 수행합니다:"
echo "  1. main 브랜치를 origin에 push (267 files, 47,186 insertions)"
echo "  2. v0.5.0 태그를 origin에 push"
echo ""
read -p "계속하시겠습니까? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "취소됨."
    exit 0
fi

# Push main
echo ""
echo "→ Pushing main branch..."
git push -u origin main

# Push tag
echo ""
echo "→ Pushing v0.5.0 tag..."
git push origin v0.5.0

echo ""
echo "=========================================="
echo "  ✅ Push complete!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "  1. https://github.com/seoca1/wet-run 방문"
echo "  2. Settings → Pages → Source: GitHub Actions 선택"
echo "  3. Actions 탭에서 CI 통과 확인"
echo "  4. 5-10분 후 Pages URL 활성화:"
echo "     https://seoca1.github.io/wet-run/"
echo ""
echo "첫 Issue 생성: https://github.com/seoca1/wet-run/issues/new"
