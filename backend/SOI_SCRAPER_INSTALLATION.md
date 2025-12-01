# SOI Scraper Installation Guide

## Phase 1 Requirement 1a: Daily SOI Tracking

### Prerequisites

1. **Install Playwright (headless browser)**
```bash
cd /opt/az_sunshine/backend
source /opt/az_sunshine/venv/bin/activate
pip install playwright
playwright install chromium
```

2. **Install Google Chrome (required for Cloudflare bypass)**
```bash
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt install -y google-chrome-stable
```

### Installation Steps

1. **Copy the scraper to Django management commands**
```bash
# Create directory structure
mkdir -p /opt/az_sunshine/backend/transparency/management/commands

# Copy files
cp transparency_commands/management/commands/soi_scraper.py /opt/az_sunshine/backend/transparency/management/commands/
touch /opt/az_sunshine/backend/transparency/management/__init__.py
touch /opt/az_sunshine/backend/transparency/management/commands/__init__.py
```

2. **Create scripts directory and copy scheduler**
```bash
mkdir -p /opt/az_sunshine/backend/scripts
cp run_soi_scraper.sh /opt/az_sunshine/backend/scripts/
chmod +x /opt/az_sunshine/backend/scripts/run_soi_scraper.sh
```

3. **Create data directory for CSV backups**
```bash
mkdir -p /opt/az_sunshine/backend/data
chown deploy:deploy /opt/az_sunshine/backend/data
```

### Manual Testing

1. **Test the scraper (dry run)**
```bash
cd /opt/az_sunshine/backend
source /opt/az_sunshine/venv/bin/activate
python manage.py soi_scraper --dry-run
```

2. **Run scraper and save to database**
```bash
python manage.py soi_scraper
```

3. **Verify results**
```bash
python manage.py shell
>>> from transparency.models import CandidateStatementOfInterest
>>> CandidateStatementOfInterest.objects.count()
>>> CandidateStatementOfInterest.objects.filter(contact_status='uncontacted').count()
```

### Automated Daily Execution

1. **Add to crontab**
```bash
crontab -e
```

2. **Add this line (runs daily at 9:00 AM)**
```
0 9 * * * /opt/az_sunshine/backend/scripts/run_soi_scraper.sh
```

3. **Verify cron job**
```bash
crontab -l
```

### Monitoring

**Check logs**
```bash
# View scraper output
tail -f /opt/az_sunshine/backend/logs/soi_scraper.log

# View cron execution log
tail -f /opt/az_sunshine/backend/logs/soi_scraper_cron.log
```

**Check CSV backups**
```bash
ls -lh /opt/az_sunshine/backend/data/soi_candidates.csv
```

### Troubleshooting

**Issue: Browser launch fails**
```bash
# Install Chrome dependencies
sudo apt install -y libgbm1 libasound2 libatk-bridge2.0-0 libgtk-3-0
```

**Issue: Cloudflare blocking**
- The scraper uses Chrome (not Chromium) to bypass Cloudflare
- Ensure Chrome is installed: `google-chrome --version`
- Check browser profile: `ls ~/.config/chrome-scraper-profile`

**Issue: Permission denied**
```bash
sudo chown -R deploy:deploy /opt/az_sunshine/backend
chmod +x /opt/az_sunshine/backend/scripts/run_soi_scraper.sh
```

### Configuration Options

**Custom CSV output path**
```bash
python manage.py soi_scraper --csv-output /path/to/output.csv
```

**Dry run (no database changes)**
```bash
python manage.py soi_scraper --dry-run
```

### Expected Behavior

1. **Daily execution**: Runs automatically at 9:00 AM via cron
2. **Cloudflare bypass**: Automatically solves Turnstile challenges
3. **Data extraction**: Scrapes name, office, email, phone, party
4. **Database update**: Creates new candidates as "uncontacted"
5. **CSV backup**: Saves results to `data/soi_candidates.csv`
6. **Logging**: All activity logged to `logs/soi_scraper.log`

### Integration with Frontend

The scraped data is immediately available via the existing API:
```
GET /api/v1/soi-candidates/?status=uncontacted
```

Frontend components that use this data:
- `SOIManagement.jsx` - View/manage candidates
- `EmailCampaign.jsx` - Send emails to uncontacted candidates

### Next Steps

Once SOI scraper is working:
- [ ] Task 2: Email Campaign Backend
- [ ] Task 3: Email tracking endpoints
- [ ] Task 4: Dashboard visualizations
