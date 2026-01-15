# Az-Sunshine Data Verification Guide

## Overview
This guide explains how to verify Az-Sunshine data against external sources:
1. **SeeTheMoney.az.gov** - Official Arizona Secretary of State data
2. **FollowTheMoney.org** - National Institute on Money in Politics

---

## Method 1: SeeTheMoney Manual Comparison

### Step 1: Export Az-Sunshine Data
```bash
cd /opt/az_sunshine/backend
source /opt/az_sunshine/venv/bin/activate

# Export 2022 IE summary
python manage.py export_ie_for_comparison --cycle 2022 --summary

# Export 2024 IE summary
python manage.py export_ie_for_comparison --cycle 2024 --summary
```

### Step 2: Download from SeeTheMoney
1. Go to https://seethemoney.az.gov
2. Click "Independent Expenditures" tile
3. Set filters (Year, Position, etc.)
4. Click "Export Independent Expenditures" button
5. Save CSV to `/opt/az_sunshine/backend/data/seethemoney/`

### Step 3: Run Comparison
```bash
python manage.py compare_seethemoney \
    --csv /opt/az_sunshine/backend/data/seethemoney/ie_export_2022.csv \
    --cycle 2022 \
    --verbose
```

---

## Method 2: FollowTheMoney API Verification

### Step 1: Get API Key
1. Go to https://www.followthemoney.org
2. Create a free myFollowTheMoney account
3. Get your API key from account settings

### Step 2: Configure Django
Add to settings.py:
```python
FOLLOWTHEMONEY_API_KEY = 'your-api-key-here'
```

Or set environment variable:
```bash
export FOLLOWTHEMONEY_API_KEY='your-api-key-here'
```

### Step 3: Run Full Verification
```bash
python manage.py verify_external_data --cycles 2022 2024 --verbose
```

---

## Quick Verification Commands

### Check Internal Data Quality
```bash
python manage.py verify_external_data --cycles 2022 2024
```

### Export Data for Manual Review
```bash
# Governor 2022
python manage.py export_ie_for_comparison --cycle 2022 --office Governor --summary

# All statewide offices 2022
python manage.py export_ie_for_comparison --cycle 2022 --summary
```

### Compare Total IE
Our database should match SeeTheMoney totals:
- 2024: ~$19.5M total IE
- 2022: ~$57.3M total IE
- 2020: ~$22.8M total IE
- 2018: ~$17.6M total IE

---

## Key Candidates to Verify (2022)

| Candidate | Office | Our IE Total |
|-----------|--------|--------------|
| Kari Lake | Governor | $10.9M |
| Katie Hobbs | Governor | $15.5M (2 committees combined) |
| Mark Finchem | Secretary of State | $3.7M |
| Kris Mayes | Attorney General | $2.0M |
| Abraham Hamadeh | Attorney General | $2.4M |

---

## Data Quality Status

Last Verification: 2026-01-13
- Critical Issues: 0
- High Issues: 0
- Overall Health: GOOD
- IE Coverage: 90.8%

For questions: Check `/opt/az_sunshine/backend/transparency/utils/data_verification.py`
