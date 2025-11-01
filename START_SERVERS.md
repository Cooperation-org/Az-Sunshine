# Starting the Arizona Sunshine Application

## Quick Start

Your React frontend has been successfully connected to the Django backend API!

### ✅ What's Been Done:

1. **Backend CORS Configuration**: Updated to allow frontend connections
2. **Frontend API Client**: Configured to connect to `http://127.0.0.1:8000/api/`
3. **Database**: Populated with sample data:
   - 3000 Candidates
   - 500 IE Committees
   - 2000 Donors
   - 2000 Expenditures
   - 1500 Contributions
   - 900 Contact Logs

### 🚀 To Start the Application:

**Option 1: Using Batch Scripts (Recommended)**

Open **TWO** separate command prompts or PowerShell windows:

**Window 1 - Backend:**
```batch
start-backend.bat
```

**Window 2 - Frontend:**
```batch
start-frontend.bat
```

**Option 2: Manual Commands**

**Terminal 1 - Start Backend:**
```bash
cd backend
python manage.py runserver 127.0.0.1:8000
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
```

### 📡 Access Points:

- **Frontend**: http://localhost:5173 (or the port shown in terminal)
- **Backend API**: http://127.0.0.1:8000/api/
- **Django Admin**: http://127.0.0.1:8000/admin/

### 🔍 What You Should See:

When you open the frontend in your browser, you should see:
- **Dashboard** with:
  - Top 10 Donors bar chart (populated with real data)
  - Support vs Oppose pie chart
  - Metric cards showing total expenditures, candidates count, etc.
  - Latest independent expenditures table
  - Top 10 IE Committees list

- **Candidates Page**: Paginated list of all candidates with IE totals
- **Donors Page**: List of donor entities with contribution totals

### 🛠️ Troubleshooting:

**Issue: "Unable to connect to backend"**
- Make sure the backend server is running (Terminal 1)
- Check that you see "Starting development server at http://127.0.0.1:8000/"

**Issue: "Empty dashboard or no data"**
- The database should already be populated
- Check browser console (F12) for error messages
- Check the backend terminal for API request logs

**Issue: "Port already in use"**
- Backend: The port 8000 might be in use. Change it in the command to 8001
- Frontend: Vite will automatically use the next available port (5173, 5174, etc.)

### 📊 Testing the Connection:

1. Open your browser to http://localhost:5173
2. Open Developer Tools (F12)
3. Check the Console tab - you should see:
   ```
   🔗 API Base URL: http://127.0.0.1:8000/api/
   ✅ Metrics: {...}
   ✅ Top Committees: [...]
   ✅ Top Donors: [...]
   ✅ Expenditures: [...]
   ```

4. Check the Network tab to see successful API calls (status 200)

### 🔄 Switching to Remote Backend:

To use the remote backend at `http://167.172.30.134:8000`:

1. Create a `.env.local` file in the `frontend/` directory:
```env
VITE_API_BASE_URL=http://167.172.30.134:8000/api/
```

2. Restart the frontend server

OR

Edit `frontend/src/api/api.js` and change line 6:
```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://167.172.30.134:8000/api/";
```

### 📝 Next Steps:

1. Start both servers using the instructions above
2. Open http://localhost:5173 in your browser
3. Explore the dashboard, candidates, and donors pages
4. All data should load automatically from the backend API

### 🎉 You're All Set!

The React frontend is now fully connected to the Django backend. All components are fetching real data from the API endpoints.

