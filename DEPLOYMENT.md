# AZ Sunshine Deployment Guide

## 🚨 Critical Information

**Your current deployment script deploys from `origin/main`, but your fixes are on `dev` branch!**

- `dev` is **14 commits ahead** of `main`
- Running the old deployment script **WILL DELETE** your migration and all recent fixes
- You must merge `dev` to `main` first

## 📋 Available Scripts

### 1. `check_migrations.sh` - Check Migration Status
Compares local migrations with database state.

```bash
cd /home/mg/Deploy/az_sunshine
./check_migrations.sh
```

### 2. `merge_dev_to_main.sh` - Safely Merge Dev to Main
Merges your dev branch into main with safety checks.

```bash
cd /home/mg/Deploy/az_sunshine
./merge_dev_to_main.sh
```

This will:
- Show all commits to be merged
- Show changed files
- Require confirmation before merging
- NOT push automatically (you must push separately)

### 3. `deploy_az_sunshine_v2.sh` - Improved Deployment Script
The new and improved deployment script with safety features.

```bash
# Deploy from main branch (default)
cd /opt
sudo -u deploy ./deploy_az_sunshine_v2.sh

# Deploy from dev branch
cd /opt
sudo -u deploy DEPLOY_BRANCH=dev ./deploy_az_sunshine_v2.sh
```

**Features:**
- ✅ Automatic database backup before deployment
- ✅ Git state backup
- ✅ Migration validation (before/after comparison)
- ✅ No hardcoded `sed` fixes
- ✅ Automatic rollback on failure
- ✅ Health checks after deployment
- ✅ Cleans up old backups (keeps last 5)
- ✅ Shows what will be deployed before proceeding
- ✅ Warns about uncommitted changes
- ✅ Configurable deploy branch via environment variable

### 4. `rollback.sh` - Rollback to Previous State
Restore from any previous backup.

```bash
cd /opt
sudo ./rollback.sh
```

This will:
- List all available backups
- Let you choose which one to restore
- Create an emergency backup before rollback
- Restore git state and database
- Restart services

## 🚀 Deployment Workflow

### Option A: Deploy Dev Branch Directly (Quick)

```bash
# On production server
cd /opt
sudo -u deploy DEPLOY_BRANCH=dev ./deploy_az_sunshine_v2.sh
```

### Option B: Merge Dev to Main First (Recommended)

```bash
# On your local machine
cd /home/mg/Deploy/az_sunshine
./merge_dev_to_main.sh

# Review the merge
git log --oneline -5

# Push to remote
git push origin main

# On production server
cd /opt
sudo -u deploy ./deploy_az_sunshine_v2.sh
```

## 🔍 Checking Migration Status

### Local Machine
```bash
cd /home/mg/Deploy/az_sunshine
./check_migrations.sh
```

### Production Server
```bash
cd /opt/az_sunshine/backend
source /opt/az_sunshine/venv/bin/activate
python manage.py showmigrations transparency
```

### Compare Local and Remote Migrations
```bash
# Check what migrations exist locally
ls -1 backend/transparency/migrations/*.py | grep -v __pycache__

# Check what's in the remote branch
git ls-tree -r origin/main --name-only backend/transparency/migrations/

# Check if your migration is committed
git ls-files backend/transparency/migrations/0017_transaction_dashboard_indexes.py
```

## 🆘 Troubleshooting

### Problem: Migration Not Found After Deploy

**Cause:** Migration wasn't committed or wasn't pushed to the branch being deployed.

**Solution:**
```bash
# Check if migration is committed
git log --all --oneline -- backend/transparency/migrations/0017_transaction_dashboard_indexes.py

# If not committed, commit it
git add backend/transparency/migrations/0017_transaction_dashboard_indexes.py
git commit -m "Add dashboard performance indexes migration"

# Push to your branch
git push origin dev
```

### Problem: Deployment Failed

**Solution:** The script automatically rolls back. But you can also use:
```bash
cd /opt
sudo ./rollback.sh
```

### Problem: Migration Already Applied Manually

**Solution:** Mark it as applied without running it:
```bash
cd /opt/az_sunshine/backend
source /opt/az_sunshine/venv/bin/activate
python manage.py migrate transparency 0017 --fake
```

### Problem: Database and Code Out of Sync

**Check sync status:**
```bash
cd /opt/az_sunshine/backend
source /opt/az_sunshine/venv/bin/activate

# Show unapplied migrations
python manage.py showmigrations | grep "\[ \]"

# Show migration plan
python manage.py migrate --plan
```

## 📊 What Changed in the New Deployment Script

| Feature | Old Script | New Script |
|---------|-----------|------------|
| Backup before deploy | ❌ No | ✅ Yes (DB + Git state) |
| Rollback on failure | ❌ Manual | ✅ Automatic |
| Migration validation | ❌ No | ✅ Yes (before/after diff) |
| Configurable branch | ❌ Hardcoded `main` | ✅ Environment variable |
| Hardcoded sed fix | ❌ Yes | ✅ No - properly handles migrations |
| Shows what will deploy | ❌ No | ✅ Yes - commit list |
| Uncommitted changes warning | ❌ No | ✅ Yes |
| Health checks | ⚠️ Basic | ✅ Comprehensive |
| Old backup cleanup | ❌ No | ✅ Yes (keeps last 5) |
| Error handling | ⚠️ Basic | ✅ Full rollback on error |

## 🔒 Security Notes

- The new script doesn't modify migrations with `sed`
- Environment variables are properly scoped
- Database passwords are not logged
- Backups are timestamped and kept for recovery
- All operations are logged

## 📁 Backup Location

Backups are stored in: `/opt/backups/YYYYMMDD_HHMMSS/`

Each backup contains:
- `database.sql` - Full database dump
- `git_state.txt` - Git commit hash
- `migrations_before.txt` - Migration state before deploy
- `migrations_after.txt` - Migration state after deploy
- `migration_diff.txt` - Diff between before/after

## 🎯 Best Practices

1. **Always review changes before deploying:**
   ```bash
   git log origin/main..origin/dev --oneline
   ```

2. **Check migration status after deploy:**
   ```bash
   ./check_migrations.sh
   ```

3. **Keep backups for at least 30 days** (modify the cleanup count if needed)

4. **Test in dev first** before deploying to production

5. **Monitor logs after deployment:**
   ```bash
   sudo journalctl -u az_sunshine_gunicorn -f
   ```

## 🔄 Updating the Old Script

To use the new script on the production server:

```bash
# Backup the old script
sudo mv /opt/deploy_az_sunshine.sh /opt/deploy_az_sunshine.sh.backup

# Copy the new script
sudo cp /home/mg/Deploy/az_sunshine/deploy_az_sunshine_v2.sh /opt/deploy_az_sunshine.sh
sudo chmod +x /opt/deploy_az_sunshine.sh
sudo chown deploy:deploy /opt/deploy_az_sunshine.sh

# Also copy helper scripts
sudo cp /home/mg/Deploy/az_sunshine/rollback.sh /opt/rollback.sh
sudo chmod +x /opt/rollback.sh
```

## 📞 Need Help?

If you encounter issues:
1. Check the backup directory for the latest backup
2. Review logs: `sudo journalctl -u az_sunshine_gunicorn -n 100`
3. Use the rollback script if needed
4. Check migration status with `check_migrations.sh`
