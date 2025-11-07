# Starting the Project with Real Backend Data

This guide will help you start both the Django backend and React frontend servers to verify they work with real database data only.

## Prerequisites

1. **Database**: Ensure `backend/db.sqlite3` exists and contains real data
2. **Python Dependencies**: Install backend dependencies
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
3. **Node Dependencies**: Install frontend dependencies
   ```bash
   cd frontend
   npm install
   ```

## Step 1: Start Django Backend Server

Open a terminal and run:

```bash
cd backend
python manage.py runserver
```

**Expected Output:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

**Verify Backend is Running:**
- Open browser: http://localhost:8000/api/v1/dashboard/summary/
- You should see JSON data with real database values

## Step 2: Verify API Endpoints Return Real Data

Test these endpoints in your browser or using curl:

### 1. Dashboard Summary
```
http://localhost:8000/api/v1/dashboard/summary/
```
**Expected**: JSON with `total_ie_spending`, `candidate_committees`, etc. from database

### 2. Candidate SOI
```
http://localhost:8000/api/v1/candidate-soi/
```
**Expected**: List of candidate statements of interest from database

### 3. Entities (Donors)
```
http://localhost:8000/api/v1/entities/
```
**Expected**: Paginated list of donor entities from database

### 4. Expenditures
```
http://localhost:8000/api/v1/expenditures/
```
**Expected**: List of independent expenditures from database

### 5. Top Donors
```
http://localhost:8000/api/v1/donors/top/
```
**Expected**: Array of top donors with real contribution totals

## Step 3: Start Frontend Development Server

Open a **NEW terminal** (keep backend running) and run:

```bash
cd frontend
npm run dev
```

**Expected Output:**
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

## Step 4: Verify Frontend Displays Real Data

Open your browser to: **http://localhost:5173/**

### Dashboard Page
- **Top 10 Donors Chart**: Should show real donor names and amounts from database
- **Support vs Oppose Pie Chart**: Should show real spending totals
- **Total IE Spending Metric**: Should match database total
- **Top 10 IE Committees**: Should show real committee names and spending

### Donor Entities Page (`/donors`)
- Should display real donor/entity names from database
- Search functionality should filter real data
- Pagination should work with real data

### Candidates Page (`/candidates`)
- Should display real candidate committees from database
- Candidate names, races, parties should be real data
- Pagination should work

### Expenditures Page (`/expenditures`)
- Should display real independent expenditure transactions
- Committee names, amounts, dates should be from database
- Support/Oppose indicators should be accurate

## Verification Checklist

- [ ] Backend server running on port 8000
- [ ] Frontend server running on port 5173
- [ ] `/api/v1/dashboard/summary/` returns real data
- [ ] `/api/v1/candidate-soi/` returns real data
- [ ] `/api/v1/entities/` returns real data
- [ ] `/api/v1/expenditures/` returns real data
- [ ] `/api/v1/donors/top/` returns real data
- [ ] Dashboard displays real charts and metrics
- [ ] Donors page shows real entities
- [ ] Candidates page shows real committees
- [ ] Expenditures page shows real transactions
- [ ] No placeholder or mock data visible

## Troubleshooting

### Backend Won't Start
- Check if port 8000 is already in use: `netstat -ano | findstr :8000`
- Verify database exists: `backend/db.sqlite3`
- Check Django settings: `python manage.py check`

### Frontend Can't Connect to Backend
- Verify backend is running on port 8000
- Check `frontend/src/api/api.js` - API_BASE_URL should be `http://localhost:8000/api/v1/`
- Check browser console for CORS errors

### No Data Displayed
- Verify database has data: `python manage.py shell` then check model counts
- Check browser Network tab for API errors
- Verify API endpoints return data in browser

### Mock/Fake Data Still Showing
- All fake data CSV files have been moved to `backend/transparency/seed_test_data/`
- These files are NOT loaded by the application
- Application loads data from MDB files via management commands
- Check views.py - no hardcoded mock responses exist

## Confirming Real Data Only

The application is configured to use **real database data only**:

1. ✅ All fake data CSV files moved to `seed_test_data/` directory
2. ✅ No hardcoded mock responses in `views.py`
3. ✅ All API endpoints query the database
4. ✅ Frontend components fetch from API endpoints only
5. ✅ No placeholder JSON responses in codebase

All data displayed comes from the `db.sqlite3` database loaded via Django management commands.

