#!/bin/bash
#
# Daily SOI Scraper Scheduler
# Phase 1 Requirement 1a: "Spider daily"
#
# Installation:
#   1. Make executable: chmod +x /opt/az_sunshine/backend/scripts/run_soi_scraper.sh
#   2. Add to crontab: crontab -e
#   3. Add line: 0 9 * * * /opt/az_sunshine/backend/scripts/run_soi_scraper.sh
#      (runs daily at 9:00 AM)
#

# Configuration
PROJECT_DIR="/opt/az_sunshine/backend"
VENV_PATH="/opt/az_sunshine/venv"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/soi_scraper_cron.log"
PYTHON="$VENV_PATH/bin/python"
MANAGE="$PROJECT_DIR/manage.py"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Log start time
echo "========================================" >> "$LOG_FILE"
echo "SOI Scraper started at $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Activate virtual environment and run scraper
cd "$PROJECT_DIR" || exit 1

source "$VENV_PATH/bin/activate"

# Run the scraper
$PYTHON $MANAGE soi_scraper >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

# Log completion
echo "----------------------------------------" >> "$LOG_FILE"
echo "SOI Scraper finished at $(date)" >> "$LOG_FILE"
echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Optional: Send email notification on failure
if [ $EXIT_CODE -ne 0 ]; then
    echo "SOI scraper failed with exit code $EXIT_CODE" | mail -s "SOI Scraper Failed" admin@arizonasunshine.org
fi

exit $EXIT_CODE
