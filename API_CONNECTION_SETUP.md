# API Connection Setup Guide

## ✅ What Has Been Configured

Your React frontend is now connected to the Django backend API at `http://167.172.30.134:8000`. Here's what was set up:

### 1. Backend Configuration (Django)

#### File: `backend/backend/settings.py`

✅ **CORS Settings Updated:**
```python
CORS_ALLOW_ALL_ORIGINS = True  # Allows requests from any origin
CORS_ALLOW_CREDENTIALS = True
```

✅ **Allowed Hosts Updated:**
```python
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "167.172.30.134", "*"]
```

### 2. Frontend Configuration (React)

#### File: `frontend/src/api/api.js`

✅ **API Base URL Updated:**
- Default: `http://167.172.30.134:8000/api/`
- Supports environment variable override: `VITE_API_BASE_URL`
- Added console logging for debugging

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://167.172.30.134:8000/api/";
```

### 3. All API Functions Already Implemented

The following API functions are ready and working in `frontend/src/api/api.js`:

- ✅ `getCandidates()` - Fetch candidates list
- ✅ `getCandidate(id)` - Fetch single candidate
- ✅ `getRaces()` - Fetch races
- ✅ `getCommittees()` - Fetch committees
- ✅ `getTopCommittees()` - Fetch top committees by spending
- ✅ `getDonors()` - Fetch donors
- ✅ `getTopDonors()` - Fetch top donors
- ✅ `getExpenditures()` - Fetch expenditures
- ✅ `getSupportOpposeByCandidate()` - Fetch support/oppose data
- ✅ `getMetrics()` - Fetch dashboard metrics
- ✅ `getContributions()` - Fetch contributions

### 4. Components Connected to API

All pages are already connected and fetching data:

- ✅ **Dashboard** (`frontend/src/pages/Dashboard.jsx`)
  - Fetches metrics, top committees, top donors, expenditures
  - Displays charts and tables with real data

- ✅ **Candidates Page** (`frontend/src/pages/Candidates.jsx`)
  - Fetches and displays paginated candidate list
  - Shows IE totals for/against each candidate

- ✅ **Candidate Detail** (`frontend/src/pages/CandidateDetail.jsx`)
  - Fetches detailed candidate info
  - Shows expenditures and support/oppose charts

- ✅ **Donors Page** (`frontend/src/pages/Donors.jsx`)
  - Fetches and displays paginated donor list

## 🚀 How to Run

### Step 1: Start the Backend

```bash
cd backend

# Make sure dependencies are installed
pip install -r requirements.txt

# Run migrations (if not done already)
python manage.py migrate

# Start the server (accessible from other machines)
python manage.py runserver 0.0.0.0:8000
```

**Important:** The `0.0.0.0:8000` binding allows external connections. If you see:
```
Starting development server at http://0.0.0.0:8000/
```
Then it's working correctly!

### Step 2: Start the Frontend

```bash
cd frontend

# Install dependencies if not done already
npm install

# Start the development server
npm run dev
```

The frontend will start at `http://localhost:5173` (or another port if 5173 is busy).

### Step 3: Verify Connection

Open your browser to `http://localhost:5173` and check:

1. **Browser Console** (F12) should show:
   ```
   🔗 API Base URL: http://167.172.30.134:8000/api/
   ```

2. **Dashboard loads with data**

3. **No CORS errors** in console

## 🧪 Testing the Connection

### Option 1: Use the Test Page

Open `test_api_connection.html` in your browser. It will automatically test all API endpoints and show results.

### Option 2: Test with cURL

```bash
# Test metrics endpoint
curl http://167.172.30.134:8000/api/metrics/

# Test candidates endpoint
curl http://167.172.30.134:8000/api/candidates/

# Test committees endpoint
curl http://167.172.30.134:8000/api/committees/
```

### Option 3: Test in Browser DevTools

1. Open browser console (F12)
2. Go to Network tab
3. Navigate through the application
4. Watch API requests being made

## 🔧 Environment Variables (Optional)

To switch between different backend URLs without changing code:

### Create `.env.local` in `frontend/` directory:

```env
# For production backend
VITE_API_BASE_URL=http://167.172.30.134:8000/api/

# OR for local development
# VITE_API_BASE_URL=http://127.0.0.1:8000/api/
```

**Note:** A template file `frontend/env.example` is provided.

## 🐛 Troubleshooting

### Issue: "Failed to fetch" or Network Error

**Causes:**
- Backend is not running
- Backend is not accessible from your machine
- Firewall blocking the connection

**Solutions:**
1. Check backend is running: `curl http://167.172.30.134:8000/api/metrics/`
2. Check firewall on server: `sudo ufw allow 8000`
3. Verify Django is bound to `0.0.0.0:8000` not `127.0.0.1:8000`

### Issue: CORS Policy Error

**Error message:**
```
Access to fetch at 'http://167.172.30.134:8000/api/...' from origin 'http://localhost:5173' 
has been blocked by CORS policy
```

**Solution:**
1. Verify `CORS_ALLOW_ALL_ORIGINS = True` in `backend/backend/settings.py`
2. Check that `corsheaders` middleware is in `MIDDLEWARE` list
3. Restart Django server after changes

### Issue: 404 Not Found

**Solution:**
- Check the URL path in api.js
- Verify backend URL routes in `backend/transparency/urls.py`
- Check if trailing slashes are consistent

### Issue: Empty Data in Frontend

**Solution:**
1. Check Django admin: `http://167.172.30.134:8000/admin/`
2. Verify data exists in database
3. Check API response in browser Network tab
4. Look for errors in Django terminal

### Issue: Timeout Errors

**Solution:**
- Increase timeout in `api.js`:
  ```javascript
  const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,  // Increase from 10000 to 30000
  });
  ```

## 🔐 Security Notes

**Current Setup:** Development-friendly (allows all origins)

**For Production:** Update these settings:

### Backend (`backend/backend/settings.py`):

```python
# Set to False in production
DEBUG = False

# Restrict to specific hosts
ALLOWED_HOSTS = ["your-domain.com", "167.172.30.134"]

# Restrict CORS to specific origins
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
]

# Use environment variables for secrets
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
```

### Frontend:
- Build for production: `npm run build`
- Use HTTPS in production
- Update API URL to use HTTPS: `https://your-domain.com/api/`

## 📊 API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/metrics/` | GET | Dashboard summary metrics |
| `/api/candidates/` | GET | List candidates (paginated) |
| `/api/candidates/{id}/` | GET | Get single candidate |
| `/api/committees/` | GET | List committees |
| `/api/committees/top/` | GET | Top 10 committees by spending |
| `/api/donors/` | GET | List donors |
| `/api/donors/top/` | GET | Top 10 donors |
| `/api/expenditures/` | GET | List expenditures |
| `/api/expenditures/support_oppose_by_candidate/` | GET | Support/oppose breakdown |
| `/api/races/` | GET | List races |
| `/api/contributions/` | GET | List contributions |

## 📁 Files Modified

### Backend:
- `backend/backend/settings.py` - CORS and ALLOWED_HOSTS configuration

### Frontend:
- `frontend/src/api/api.js` - API base URL configuration

### New Files:
- `DEPLOYMENT.md` - Deployment guide
- `API_CONNECTION_SETUP.md` - This file
- `test_api_connection.html` - API testing page
- `frontend/env.example` - Environment variable template

## ✨ Next Steps

1. **Test the connection** using the test page or by running the app
2. **Monitor the console** for any errors
3. **Check data loading** in all pages (Dashboard, Candidates, Donors)
4. **Plan for production** deployment with proper security
5. **Consider adding:**
   - Loading states for better UX
   - Error boundaries for error handling
   - Retry logic for failed requests
   - Authentication if needed

## 📞 Need Help?

If you encounter issues:
1. Check the browser console for errors
2. Check Django terminal for backend errors
3. Use the test page to verify endpoint accessibility
4. Review the troubleshooting section above

The connection is now ready to use! 🎉

