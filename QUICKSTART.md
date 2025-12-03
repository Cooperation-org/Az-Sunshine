# 🚀 Quick Start - Deploy Your Dashboard Fixes

## ⚠️ URGENT: Your Migration Issue

Your dashboard fixes (including migration `0017_transaction_dashboard_indexes.py`) are on the `dev` branch, but the old deployment script deploys from `main` branch.

**The old script WILL DELETE your fixes!**

## ✅ Safe Deployment - Choose One Method:

### Method 1: Deploy Dev Branch Directly (Fastest) ⚡

```bash
# On production server (/opt directory)
cd /opt
sudo -u deploy DEPLOY_BRANCH=dev ./deploy_az_sunshine_v2.sh
```

### Method 2: Merge to Main First (Recommended) 📋

```bash
# Step 1: On your local machine - Merge dev to main
cd /home/mg/Deploy/az_sunshine
./merge_dev_to_main.sh

# Step 2: Push to GitHub
git push origin main

# Step 3: On production server - Deploy
cd /opt
sudo -u deploy ./deploy_az_sunshine_v2.sh
```

## 🔍 Quick Commands

### Check Migration Status
```bash
cd /home/mg/Deploy/az_sunshine
./check_migrations.sh
```

### Verify Your Fixes Are Committed
```bash
cd /home/mg/Deploy/az_sunshine
git log --oneline -5
# Should see: "no more intermittent disappearing in the dashboard page"
```

### Check What Branch Has Your Fixes
```bash
git branch --contains 5101195
# Should show 'dev'
```

### See What Will Be Deployed
```bash
# Show commits that main is missing from dev
git log origin/main..dev --oneline
```

## 🆘 If Something Goes Wrong

### Rollback to Previous State
```bash
cd /opt
sudo ./rollback.sh
```

### Check Service Status
```bash
sudo systemctl status az_sunshine_gunicorn
sudo systemctl status nginx
```

### View Logs
```bash
sudo journalctl -u az_sunshine_gunicorn -f
```

## 📦 Files You Created Today

1. ✅ `check_migrations.sh` - Check migration status
2. ✅ `deploy_az_sunshine_v2.sh` - New safe deployment script
3. ✅ `merge_dev_to_main.sh` - Safely merge dev to main
4. ✅ `rollback.sh` - Rollback to any previous backup
5. ✅ `DEPLOYMENT.md` - Full documentation
6. ✅ `QUICKSTART.md` - This file

## 📝 What Was Fixed

Your dashboard had two critical issues:

1. **Intermittent Display Bug** - Charts randomly disappeared
   - Fixed in: `frontend/src/pages/Dashboard.jsx`
   - Problem: Unsafe nested property access
   - Solution: Added proper optional chaining

2. **Slow Loading** - Dashboard took too long to load
   - Fixed in: `backend/transparency/models.py`
   - Added: 2 new database indexes
   - Migration: `0017_transaction_dashboard_indexes.py`

## ✨ After Deployment

Your dashboard should:
- ✅ Display all 3 charts consistently (no more disappearing!)
- ✅ Load significantly faster
- ✅ Handle empty data gracefully

## 🎯 Next Steps

1. **Deploy using Method 1 or 2 above**
2. **Test your dashboard** at https://167.172.30.134
3. **Verify all 3 charts appear:**
   - Top 10 Donors
   - Top 10 IE Committees
   - IE Spending Type
4. **Check performance** - should load faster

## 💡 Pro Tips

- Always check `git log` before deploying
- Keep the rollback script handy
- Backups are stored in `/opt/backups/` (automatically cleaned, keeps last 5)
- Use `DEPLOY_BRANCH=dev` environment variable to deploy from dev branch
- The new script automatically backs up before deploying

---

**Need the old deployment script behavior?**

The old script is at: `/opt/deploy_az_sunshine.sh.backup`

But we recommend using the new one with proper safety checks!
