#!/bin/bash
# Improved deployment script for AZ Sunshine
# Version 2.0 - With safety checks and migration validation

set -e  # Exit on error
set -o pipefail  # Catch errors in pipes

# ==================== CONFIGURATION ====================
PROJECT_DIR="/opt/az_sunshine"
VENV_PATH="/opt/az_sunshine/venv"
ENV_FILE="/opt/.env.az_sunshine"
BACKUP_DIR="/opt/backups/$(date +%Y%m%d_%H%M%S)"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"  # Override with: DEPLOY_BRANCH=dev ./deploy.sh

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ==================== HELPER FUNCTIONS ====================

log_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_header() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

rollback() {
    log_error "Deployment failed! Rolling back..."

    if [ -d "$BACKUP_DIR" ]; then
        log_info "Restoring from backup: $BACKUP_DIR"

        # Restore database if backup exists
        if [ -f "$BACKUP_DIR/database.sql" ]; then
            log_info "Restoring database..."
            source "$ENV_FILE"
            set -a && source "$ENV_FILE" && set +a
            PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_DIR/database.sql"
            log_success "Database restored"
        fi

        # Restore git state if backup exists
        if [ -f "$BACKUP_DIR/git_state.txt" ]; then
            PREV_COMMIT=$(cat "$BACKUP_DIR/git_state.txt")
            log_info "Restoring git to: $PREV_COMMIT"
            cd "$PROJECT_DIR"
            git reset --hard "$PREV_COMMIT"
            log_success "Git state restored"
        fi
    fi

    log_error "Rollback complete. Please check logs and try again."
    exit 1
}

# Trap errors and call rollback
trap rollback ERR

# ==================== PRE-FLIGHT CHECKS ====================

log_header "🚀 AZ Sunshine Deployment Script v2.0"
log_info "Deploy branch: ${DEPLOY_BRANCH}"
log_info "Timestamp: $(date)"
echo ""

# Check if running as correct user
CURRENT_USER=$(whoami)
if [ "$CURRENT_USER" != "deploy" ] && [ "$CURRENT_USER" != "root" ]; then
    log_warning "Running as user: $CURRENT_USER (expected: deploy or root)"
fi

# Verify project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "Project directory not found: $PROJECT_DIR"
    exit 1
fi

# Verify environment file exists
if [ ! -f "$ENV_FILE" ]; then
    log_error "Environment file not found: $ENV_FILE"
    exit 1
fi

# Load environment variables
log_info "Loading environment variables..."
set -a
source "$ENV_FILE"
set +a

# Verify critical environment variables
if [ -z "$DB_PASSWORD" ] || [ -z "$DB_NAME" ] || [ -z "$DB_USER" ]; then
    log_error "Critical environment variables missing (DB_PASSWORD, DB_NAME, DB_USER)"
    exit 1
fi

log_success "Environment loaded (DB: $DB_NAME, User: $DB_USER, Host: $DB_HOST)"

# Verify virtual environment exists
if [ ! -f "$VENV_PATH/bin/activate" ]; then
    log_error "Virtual environment not found: $VENV_PATH"
    exit 1
fi

log_success "Pre-flight checks passed"

# ==================== CREATE BACKUP ====================

log_header "💾 Creating Backup"

mkdir -p "$BACKUP_DIR"
log_info "Backup directory: $BACKUP_DIR"

# Save current git commit
cd "$PROJECT_DIR"
git rev-parse HEAD > "$BACKUP_DIR/git_state.txt"
log_success "Git state saved"

# Backup database
log_info "Backing up database..."
PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-privileges \
    > "$BACKUP_DIR/database.sql"

if [ -f "$BACKUP_DIR/database.sql" ] && [ -s "$BACKUP_DIR/database.sql" ]; then
    DB_SIZE=$(du -h "$BACKUP_DIR/database.sql" | cut -f1)
    log_success "Database backed up ($DB_SIZE)"
else
    log_error "Database backup failed or is empty"
    exit 1
fi

# Backup current migration state
cd "$PROJECT_DIR/backend"
source "$VENV_PATH/bin/activate"
python manage.py showmigrations --plan > "$BACKUP_DIR/migrations_before.txt"
log_success "Migration state saved"

# ==================== GIT OPERATIONS ====================

log_header "📥 Updating Code"

cd "$PROJECT_DIR"

# Configure git
git config --global --add safe.directory "$PROJECT_DIR"

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log_info "Current branch: $CURRENT_BRANCH"

# Check for local uncommitted changes
if ! git diff-index --quiet HEAD --; then
    log_warning "Uncommitted changes detected!"
    git status --short
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled"
        exit 0
    fi
fi

# Fetch latest changes
log_info "Fetching from remote..."
git fetch origin

# Check if branch exists on remote
if ! git show-ref --verify --quiet "refs/remotes/origin/$DEPLOY_BRANCH"; then
    log_error "Branch '$DEPLOY_BRANCH' does not exist on remote"
    exit 1
fi

# Show what will change
log_info "Changes to be deployed:"
git log HEAD..origin/$DEPLOY_BRANCH --oneline --decorate | head -10 || log_info "No new commits"

# Reset to target branch
log_info "Resetting to origin/$DEPLOY_BRANCH..."
git reset --hard "origin/$DEPLOY_BRANCH"
git clean -fd

CURRENT_COMMIT=$(git rev-parse HEAD)
log_success "Code updated to: $CURRENT_COMMIT"

# ==================== BACKEND DEPLOYMENT ====================

log_header "🔧 Backend Deployment"

cd "$PROJECT_DIR/backend"
source "$VENV_PATH/bin/activate"

# Install/update dependencies
log_info "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r "$PROJECT_DIR/requirements.txt"
log_success "Dependencies installed"

# Check for new migrations
log_info "Checking for new migrations..."
python manage.py makemigrations --check --dry-run || {
    log_warning "Unapplied model changes detected!"
    log_info "Generating migrations..."
    python manage.py makemigrations
}

# Show migration plan
log_info "Migration plan:"
python manage.py migrate --plan | tail -10

# Run migrations
log_info "Running database migrations..."
python manage.py migrate --noinput

# Save new migration state
python manage.py showmigrations --plan > "$BACKUP_DIR/migrations_after.txt"

# Compare migration states
if diff "$BACKUP_DIR/migrations_before.txt" "$BACKUP_DIR/migrations_after.txt" > /dev/null; then
    log_success "No new migrations applied"
else
    log_success "Migrations applied successfully"
    log_info "Migration diff saved to: $BACKUP_DIR/migration_diff.txt"
    diff "$BACKUP_DIR/migrations_before.txt" "$BACKUP_DIR/migrations_after.txt" > "$BACKUP_DIR/migration_diff.txt" || true
fi

# Collect static files
log_info "Collecting static files..."
python manage.py collectstatic --noinput --clear > /dev/null
log_success "Static files collected"

# Clear Django cache
log_info "Clearing Django cache..."
python manage.py shell -c "from django.core.cache import cache; cache.clear(); print('Cache cleared')"
log_success "Cache cleared"

deactivate

# ==================== FRONTEND DEPLOYMENT ====================

log_header "🎨 Frontend Deployment"

cd "$PROJECT_DIR/frontend"

# Clean build directory
log_info "Cleaning build directory..."
rm -rf dist
mkdir -p dist

# Install/update dependencies
if [ ! -d "node_modules" ]; then
    log_info "Installing npm dependencies (clean install)..."
    npm ci
else
    log_info "Checking npm dependencies..."
    npm install
fi

# Build frontend
log_info "Building React app..."
npm run build

if [ -d "dist" ] && [ "$(ls -A dist)" ]; then
    log_success "Frontend built successfully"
else
    log_error "Frontend build failed - dist directory is empty"
    exit 1
fi

# ==================== SERVICE RESTART ====================

log_header "♻️  Restarting Services"

# Restart Gunicorn
if systemctl list-units --full -all | grep -Fq 'az_sunshine_gunicorn.service'; then
    log_info "Restarting Gunicorn..."
    sudo systemctl restart az_sunshine_gunicorn
    sleep 3

    if systemctl is-active --quiet az_sunshine_gunicorn; then
        log_success "Gunicorn restarted successfully"
    else
        log_error "Gunicorn failed to start!"
        sudo systemctl status az_sunshine_gunicorn --no-pager -l
        exit 1
    fi
else
    log_warning "Gunicorn service not found (az_sunshine_gunicorn.service)"
fi

# Reload Nginx
if systemctl is-active --quiet nginx; then
    log_info "Reloading Nginx..."
    sudo systemctl reload nginx
    log_success "Nginx reloaded"
else
    log_warning "Nginx is not running"
fi

# ==================== HEALTH CHECKS ====================

log_header "🏥 Health Checks"

# Check if backend is responding
log_info "Checking backend health..."
sleep 2

if curl -sf http://localhost:8000/api/v1/health/ > /dev/null 2>&1; then
    log_success "Backend is responding"
else
    log_warning "Backend health check failed (this may be normal if no health endpoint exists)"
fi

# Check service status
log_info "Service status:"
systemctl is-active --quiet az_sunshine_gunicorn && echo "  ✓ Gunicorn: running" || echo "  ✗ Gunicorn: stopped"
systemctl is-active --quiet nginx && echo "  ✓ Nginx: running" || echo "  ✗ Nginx: stopped"

# ==================== COMPLETION ====================

log_header "✅ Deployment Completed Successfully"

echo ""
log_success "Deployed commit: $(git log -1 --oneline)"
log_success "Backup location: $BACKUP_DIR"
log_info "Application URL: https://167.172.30.134"
echo ""

# Cleanup old backups (keep last 5)
log_info "Cleaning up old backups..."
ls -dt /opt/backups/*/ | tail -n +6 | xargs rm -rf 2>/dev/null || true
log_success "Old backups cleaned"

echo ""
log_info "Deployment completed at: $(date)"
