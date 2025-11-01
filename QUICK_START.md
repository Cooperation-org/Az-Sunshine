# 🚀 Quick Start Guide

## Start the Application in 3 Steps

### 1️⃣ Start Backend

```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```

✅ Wait for: `Starting development server at http://0.0.0.0:8000/`

### 2️⃣ Start Frontend

Open a new terminal:

```bash
cd frontend
npm run dev
```

✅ Wait for: `Local: http://localhost:5173/`

### 3️⃣ Open Browser

Navigate to: **http://localhost:5173/**

You should see:
- Dashboard with charts
- Real data from the backend
- No CORS errors in console

## 🎯 Quick Test

Open browser console (F12) and look for:
```
🔗 API Base URL: http://167.172.30.134:8000/api/
```

## ❓ Problems?

### Backend won't start?
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Frontend won't start?
```bash
cd frontend
npm install
npm run dev
```

### No data showing?
1. Check backend is running at http://167.172.30.134:8000
2. Open http://167.172.30.134:8000/admin/ and verify data exists
3. Check browser console (F12) for errors

### CORS errors?
1. Verify `CORS_ALLOW_ALL_ORIGINS = True` in `backend/backend/settings.py`
2. Restart Django server

## 📚 More Help

- Full setup guide: See `API_CONNECTION_SETUP.md`
- Deployment guide: See `DEPLOYMENT.md`
- API test page: Open `test_api_connection.html` in browser

