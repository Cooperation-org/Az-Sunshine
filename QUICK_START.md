# Quick Start Commands

## Terminal 1 - Backend Server
```bash
cd backend
python manage.py runserver
```

## Terminal 2 - Frontend Server  
```bash
cd frontend
npm run dev
```

## Verify Endpoints (in browser or new terminal)

```bash
# Dashboard Summary
curl http://localhost:8000/api/v1/dashboard/summary/

# Candidate SOI
curl http://localhost:8000/api/v1/candidate-soi/

# Entities (Donors)
curl http://localhost:8000/api/v1/entities/

# Expenditures
curl http://localhost:8000/api/v1/expenditures/

# Top Donors
curl http://localhost:8000/api/v1/donors/top/
```

## Frontend URLs
- Dashboard: http://localhost:5173/
- Donors: http://localhost:5173/donors
- Candidates: http://localhost:5173/candidates
- Expenditures: http://localhost:5173/expenditures

