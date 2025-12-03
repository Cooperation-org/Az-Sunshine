# Server Commands Quick Reference

## 🚀 Deploy the Dashboard Fixes

```bash
ssh deploy@167.172.30.134
cd /opt
sudo -u deploy ./deploy_az_sunshine.sh
```

## 🔍 Check Status

```bash
# Check if services are running
ssh deploy@167.172.30.134 "sudo systemctl status az_sunshine_gunicorn nginx --no-pager"

# Check migration status
ssh deploy@167.172.30.134 "cd /opt/az_sunshine/backend && source /opt/az_sunshine/venv/bin/activate && python manage.py showmigrations transparency | tail -5"

# View logs
ssh deploy@167.172.30.134 "sudo journalctl -u az_sunshine_gunicorn -n 50"

# View deployment instructions
ssh deploy@167.172.30.134 "cat /opt/DEPLOYMENT_READY.txt"
```

## 🛟 Rollback if Needed

```bash
ssh deploy@167.172.30.134
cd /opt
sudo ./rollback.sh
```

## 📊 After Deployment - Test

1. Visit: https://167.172.30.134
2. Check all 3 charts appear consistently
3. Refresh page multiple times to verify no intermittent issues
4. Check loading speed

## 🔧 Useful Server Commands

```bash
# Check available backups
ssh deploy@167.172.30.134 "ls -lh /opt/backups/"

# Check migration status
ssh deploy@167.172.30.134 "/opt/check_migrations.sh"

# Restart services manually
ssh deploy@167.172.30.134 "sudo systemctl restart az_sunshine_gunicorn"

# View recent logs
ssh deploy@167.172.30.134 "sudo journalctl -u az_sunshine_gunicorn -f"
```

## 📁 Important Files on Server

```
/opt/deploy_az_sunshine.sh          - NEW deployment script
/opt/deploy_az_sunshine.sh.backup   - Old deployment script (backup)
/opt/rollback.sh                    - Rollback utility
/opt/check_migrations.sh            - Migration checker
/opt/DEPLOYMENT_READY.txt           - Deployment instructions
/opt/backups/                       - Automatic backups directory
/opt/az_sunshine/                   - Application code
```

## 🎯 What Got Fixed

- **Frontend:** `frontend/src/pages/Dashboard.jsx`
  - Added safe property access with optional chaining
  - Fixed intermittent chart disappearing bug

- **Backend:** `backend/transparency/models.py`
  - Added 2 database indexes for dashboard queries
  - Improved query performance

- **Backend:** `backend/transparency/views_dashboard_optimized.py`
  - Ensured consistent data structure
  - Better error handling

- **Migration:** `0017_transaction_dashboard_indexes.py`
  - Creates idx_txn_dash_ie_benefit index
  - Creates idx_txn_dash_donors index

## 🔐 SSH Connection

```bash
ssh deploy@167.172.30.134
```

Password: [You already have SSH key configured]
