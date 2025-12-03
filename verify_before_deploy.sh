#!/bin/bash
# Show exactly what will happen if you deploy with the old script

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Deployment Impact Analysis${NC}"
echo ""

cd /home/mg/Deploy/az_sunshine

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}⚠️  WHAT THE OLD SCRIPT WILL DELETE:${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${RED}These commits will be LOST if deploying from 'main':${NC}"
git log --oneline main..dev | nl
echo ""

echo -e "${RED}These files were changed and will be RESET:${NC}"
git diff --name-status main..dev
echo ""

echo -e "${RED}Your dashboard fixes (commit 5101195) will be DELETED!${NC}"
git show --stat 5101195 | head -20
echo ""

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ SAFE OPTIONS:${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}Option 1:${NC} Deploy from dev branch"
echo "  cd /opt && sudo -u deploy DEPLOY_BRANCH=dev ./deploy_az_sunshine_v2.sh"
echo ""
echo -e "${GREEN}Option 2:${NC} Merge dev to main first"
echo "  ./merge_dev_to_main.sh"
echo "  git push origin main"
echo "  cd /opt && sudo -u deploy ./deploy_az_sunshine_v2.sh"
echo ""

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 Current Branch Status:${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Current branch: $(git rev-parse --abbrev-ref HEAD)"
echo "Latest commit: $(git log -1 --oneline)"
echo ""
echo "Branch: dev    - Commit: $(git rev-parse --short dev)"
echo "Branch: main   - Commit: $(git rev-parse --short main)"
echo "Remote: origin/main - Commit: $(git rev-parse --short origin/main)"
echo ""
