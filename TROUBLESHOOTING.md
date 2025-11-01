# 🔧 Troubleshooting Guide

## Current Status

✅ **Backend API is running and working perfectly!**
- Backend: http://127.0.0.1:8000
- All endpoints tested and returning data

❓ **Frontend status needs verification**

## Step-by-Step Testing

### 1. Test Backend API (Already Working ✅)

Open PowerShell and run:
```powershell
curl http://127.0.0.1:8000/api/metrics/
```

You should see JSON data with candidates, expenditures, etc.

### 2. Test Browser Connection

**Option A: Simple HTML Test**
1. Open `test-connection.html` in your browser
2. Click the test buttons to verify the API is accessible from browser
3. Check for any CORS errors in the browser console (F12)

**Option B: Direct URL Test**
1. Open your browser
2. Navigate to: http://127.0.0.1:8000/api/metrics/
3. You should see JSON data

### 3. Check Frontend Server

Open a **NEW** PowerShell window and run:
```powershell
cd frontend
npm run dev
```

Look for output like:
```
VITE v7.x.x  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### 4. Open Frontend in Browser

1. Open your browser
2. Go to: **http://localhost:5173**
3. Open Developer Tools (Press F12)
4. Check the Console tab for any errors
5. Check the Network tab to see if API calls are being made

## Common Issues & Solutions

### Issue 1: "Nothing is showing in the browser"

**Possible causes:**
- Frontend not loaded yet
- JavaScript errors
- API not responding

**Solution:**
1. Open http://localhost:5173 in browser
2. Press F12 to open DevTools
3. Look at Console tab - what errors do you see?
4. Look at Network tab - are requests being made to http://127.0.0.1:8000/api/?

### Issue 2: CORS Errors in Browser

**Error looks like:**
```
Access to fetch at 'http://127.0.0.1:8000/api/...' from origin 'http://localhost:5173' 
has been blocked by CORS policy
```

**Solution:**
The backend CORS settings should already be configured, but if you see this:

1. Open: `backend/backend/settings.py`
2. Verify these lines exist:
```python
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
```

3. Restart the backend server

### Issue 3: "Network Error" or "Connection Refused"

**Solution:**
1. Make sure backend is running:
```powershell
cd backend
python manage.py runserver 127.0.0.1:8000
```

2. You should see:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### Issue 4: Frontend shows "Loading..." forever

**Possible causes:**
- API calls failing
- Wrong API URL
- CORS issues

**Solution:**
1. Open browser DevTools (F12)
2. Go to Network tab
3. Refresh the page
4. Look for failed requests (they'll be red)
5. Click on a failed request to see the error details

### Issue 5: Port 5173 already in use

**Solution:**
Vite will automatically use the next available port (5174, 5175, etc.)
Check the terminal output to see which port it's using.

## Manual Testing Checklist

Run through these steps:

- [ ] Backend running? Test: `curl http://127.0.0.1:8000/api/metrics/`
- [ ] Frontend running? Check terminal for "Local: http://localhost:5173/"
- [ ] Browser open to http://localhost:5173?
- [ ] Browser console open (F12)?
- [ ] Any errors in console?
- [ ] Network tab showing API requests?
- [ ] API requests succeeding (status 200)?

## What to Check in Browser

1. **Open Browser DevTools (F12)**

2. **Console Tab** - Look for:
   - ✅ `🔗 API Base URL: http://127.0.0.1:8000/api/`
   - ✅ `✅ Metrics: {...}`
   - ✅ `✅ Top Committees: [...]`
   - ❌ Any red error messages

3. **Network Tab** - Look for:
   - Requests to `http://127.0.0.1:8000/api/...`
   - Status codes (should be 200)
   - Response preview (should show data)

## Quick Fix Commands

### Restart Everything

**Terminal 1 - Backend:**
```powershell
cd backend
python manage.py runserver 127.0.0.1:8000
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

**Terminal 3 - Test Backend:**
```powershell
curl http://127.0.0.1:8000/api/metrics/
```

Then open: **http://localhost:5173** in your browser

## Still Not Working?

If you've tried everything above, please provide:

1. **Backend terminal output** - Copy the last 20 lines
2. **Frontend terminal output** - Copy the last 20 lines
3. **Browser console errors** - Press F12, copy any red error messages
4. **Browser network tab** - Screenshot or describe failing requests

With this information, I can provide specific help!

## Expected Working State

When everything is working, you should see:

1. **Backend Terminal:**
```
Django version 5.0.7, using settings 'backend.settings'
Starting development server at http://127.0.0.1:8000/
```

2. **Frontend Terminal:**
```
VITE v7.x.x  ready in XXX ms
➜  Local:   http://localhost:5173/
```

3. **Browser at http://localhost:5173:**
   - Dashboard with charts and data
   - No errors in console
   - API requests in Network tab with status 200

4. **Browser Console (F12):**
```
🔗 API Base URL: http://127.0.0.1:8000/api/
🔄 Loading dashboard data from backend...
✅ Metrics: {total_expenditures: 101351069.65, ...}
✅ Top Committees: [{name: "...", total: ...}, ...]
✅ Top Donors: [{name: "...", total_contribution: ...}, ...]
✅ Expenditures: {count: 2000, results: [...]}
```

