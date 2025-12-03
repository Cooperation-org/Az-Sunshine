#!/bin/bash
# Rollback to a specific backup

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKUP_ROOT="/opt/backups"
ENV_FILE="/opt/.env.az_sunshine"

echo -e "${BLUE}🔄 AZ Sunshine Rollback Tool${NC}"
echo ""

# Check if running as correct user
if [ "$EUID" -ne 0 ] && [ "$(whoami)" != "deploy" ]; then
    echo -e "${RED}Please run as root or deploy user${NC}"
    exit 1
fi

# List available backups
if [ ! -d "$BACKUP_ROOT" ] || [ -z "$(ls -A $BACKUP_ROOT 2>/dev/null)" ]; then
    echo -e "${RED}No backups found in $BACKUP_ROOT${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Available backups:${NC}"
echo ""

BACKUPS=($(ls -dt $BACKUP_ROOT/*/))
INDEX=1

for BACKUP in "${BACKUPS[@]}"; do
    BACKUP_NAME=$(basename "$BACKUP")
    SIZE=$(du -sh "$BACKUP" | cut -f1)
    HAS_DB=""
    HAS_GIT=""

    [ -f "$BACKUP/database.sql" ] && HAS_DB="✓ DB"
    [ -f "$BACKUP/git_state.txt" ] && HAS_GIT="✓ Git"

    echo "  $INDEX) $BACKUP_NAME ($SIZE) - $HAS_DB $HAS_GIT"
    ((INDEX++))
done

echo ""
read -p "Select backup number to restore (or 0 to cancel): " CHOICE

if [ "$CHOICE" = "0" ] || [ -z "$CHOICE" ]; then
    echo "Cancelled"
    exit 0
fi

if [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -ge "$INDEX" ]; then
    echo -e "${RED}Invalid selection${NC}"
    exit 1
fi

# Get selected backup
SELECTED_BACKUP="${BACKUPS[$((CHOICE-1))]}"
echo ""
echo -e "${YELLOW}⚠ WARNING: This will restore from backup:${NC}"
echo "  $SELECTED_BACKUP"
echo ""
read -p "Are you sure? This cannot be undone! (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo -e "${BLUE}🔄 Starting rollback...${NC}"

# Load environment
set -a
source "$ENV_FILE"
set +a

# Restore git state
if [ -f "$SELECTED_BACKUP/git_state.txt" ]; then
    COMMIT=$(cat "$SELECTED_BACKUP/git_state.txt")
    echo "📥 Restoring git to commit: $COMMIT"

    cd /opt/az_sunshine
    git reset --hard "$COMMIT"
    git clean -fd

    echo -e "${GREEN}✓ Git restored${NC}"
else
    echo -e "${YELLOW}⚠ No git state found in backup${NC}"
fi

# Restore database
if [ -f "$SELECTED_BACKUP/database.sql" ]; then
    echo "🗄️  Restoring database..."

    # Create a backup of current state before restoring
    EMERGENCY_BACKUP="/opt/backups/pre_rollback_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$EMERGENCY_BACKUP"

    echo "  Creating emergency backup at: $EMERGENCY_BACKUP"
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-owner \
        --no-privileges \
        > "$EMERGENCY_BACKUP/database.sql"

    echo "  Restoring from backup..."
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        < "$SELECTED_BACKUP/database.sql"

    echo -e "${GREEN}✓ Database restored${NC}"
    echo -e "${BLUE}  Emergency backup saved at: $EMERGENCY_BACKUP${NC}"
else
    echo -e "${YELLOW}⚠ No database backup found${NC}"
fi

# Show migration changes
if [ -f "$SELECTED_BACKUP/migrations_before.txt" ]; then
    echo ""
    echo -e "${BLUE}📋 Migration state from backup:${NC}"
    tail -5 "$SELECTED_BACKUP/migrations_before.txt"
fi

# Restart services
echo ""
echo -e "${BLUE}♻️  Restarting services...${NC}"

if systemctl list-units --full -all | grep -Fq 'az_sunshine_gunicorn.service'; then
    sudo systemctl restart az_sunshine_gunicorn
    sleep 2

    if systemctl is-active --quiet az_sunshine_gunicorn; then
        echo -e "${GREEN}✓ Gunicorn restarted${NC}"
    else
        echo -e "${RED}✗ Gunicorn failed to start${NC}"
        sudo systemctl status az_sunshine_gunicorn --no-pager -l
    fi
fi

if systemctl is-active --quiet nginx; then
    sudo systemctl reload nginx
    echo -e "${GREEN}✓ Nginx reloaded${NC}"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Rollback completed!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
