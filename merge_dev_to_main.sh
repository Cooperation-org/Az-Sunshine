#!/bin/bash
# Safely merge dev branch to main

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔀 Merging dev to main${NC}"
echo ""

cd /home/mg/Deploy/az_sunshine

# Make sure we're on dev and up to date
echo "📥 Fetching latest changes..."
git fetch origin

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "dev" ]; then
    echo -e "${YELLOW}⚠ Currently on branch: $CURRENT_BRANCH${NC}"
    echo "Switching to dev..."
    git checkout dev
fi

# Pull latest dev
echo "📥 Pulling latest dev..."
git pull origin dev

# Show what will be merged
echo ""
echo -e "${BLUE}📋 Commits to be merged into main:${NC}"
git log main..dev --oneline --decorate

# Count commits
COMMIT_COUNT=$(git log main..dev --oneline | wc -l)
echo ""
echo -e "${YELLOW}Total commits: $COMMIT_COUNT${NC}"

# Show changed files
echo ""
echo -e "${BLUE}📁 Changed files:${NC}"
git diff main...dev --name-status | head -20

echo ""
read -p "Proceed with merge? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Merge cancelled${NC}"
    exit 0
fi

# Switch to main
echo "🔄 Switching to main..."
git checkout main
git pull origin main

# Merge dev
echo "🔀 Merging dev into main..."
git merge dev --no-ff -m "Merge dev into main - $(date +%Y-%m-%d)"

echo ""
echo -e "${GREEN}✓ Merge completed successfully!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Review the merge: git log --oneline -5"
echo "  2. Push to remote: git push origin main"
echo "  3. Deploy: cd /opt && sudo -u deploy ./deploy_az_sunshine_v2.sh"
echo ""
