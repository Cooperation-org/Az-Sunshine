# Deployment Guide: Connecting React Frontend to Django Backend

## Overview
This guide explains how the React frontend connects to the Django backend API running at `http://167.172.30.134:8000`.

## What's Been Configured

### 1. Backend (Django) Configuration

#### CORS Settings (`backend/backend/settings.py`)
```python
# Allow requests from any origin (for development)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Allowed hosts
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "167.172.30.134", "*"]
```

**Important:** In production, you should restrict `CORS_ALLOW_ALL_ORIGINS` to specific origins:
```python
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
    "http://localhost:5173",  # For local development
]
```

### 2. Frontend (React) Configuration

#### API Client (`frontend/src/api/api.js`)
- Configured to use `http://167.172.30.134:8000/api/` as the base URL
- Supports environment variable override via `VITE_API_BASE_URL`
- Includes error handling and logging

## Running the Application

### 1. Start the Backend (on your server or locally)

```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```

**Note:** The `0.0.0.0:8000` binding allows the server to accept connections from other machines on the network.

### 2. Start the Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173` (or another port if 5173 is busy).

## Environment Variables

### Frontend Environment Variables

Create a `.env.local` file in the `frontend/` directory to override the default API URL:

```env
VITE_API_BASE_URL=http://167.172.30.134:8000/api/
```

For local development with a local backend:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/
```

## API Endpoints

The frontend connects to these backend endpoints:

- `GET /api/candidates/` - List all candidates
- `GET /api/candidates/{id}/` - Get candidate details
- `GET /api/committees/` - List all committees
- `GET /api/committees/top/` - Get top committees by spending
- `GET /api/donors/` - List all donors
- `GET /api/donors/top/` - Get top donors by contribution
- `GET /api/expenditures/` - List all expenditures
- `GET /api/expenditures/support_oppose_by_candidate/` - Get support/oppose breakdown
- `GET /api/metrics/` - Get dashboard metrics

## Troubleshooting

### Issue: "Network Error" or CORS errors

**Solution:**
1. Check that the backend server is running and accessible
2. Verify CORS settings in `backend/backend/settings.py`
3. Check browser console for detailed error messages
4. Test the API directly: `curl http://167.172.30.134:8000/api/candidates/`

### Issue: "Connection refused"

**Solution:**
1. Ensure the backend is running with `0.0.0.0:8000` binding
2. Check firewall rules on the server
3. Verify the IP address is correct

### Issue: Empty data in frontend

**Solution:**
1. Check the Django admin or database to ensure data exists
2. Look at browser Network tab to see API responses
3. Check Django logs for any errors

### Issue: Backend not accessible from external IP

**Solution:**
1. Run Django with: `python manage.py runserver 0.0.0.0:8000`
2. Check server firewall: `sudo ufw allow 8000`
3. Verify security group settings (if using cloud provider)

## Security Considerations for Production

### Backend
1. Set `DEBUG = False` in production
2. Use a proper secret key (use environment variables)
3. Restrict `ALLOWED_HOSTS` to your actual domain
4. Restrict `CORS_ALLOWED_ORIGINS` to your frontend domain(s)
5. Use HTTPS (configure SSL/TLS certificates)
6. Use a production-ready database (PostgreSQL recommended)
7. Use a production server (gunicorn + nginx)

### Frontend
1. Build for production: `npm run build`
2. Serve with a proper web server (nginx, Apache, or CDN)
3. Use HTTPS
4. Update `VITE_API_BASE_URL` to use HTTPS endpoint

## Production Deployment Example

### Backend (with gunicorn and nginx)

1. Install gunicorn:
```bash
pip install gunicorn
```

2. Run with gunicorn:
```bash
gunicorn backend.wsgi:application --bind 0.0.0.0:8000
```

3. Configure nginx to proxy to gunicorn (example config):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /admin/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Frontend (static hosting)

1. Build the frontend:
```bash
cd frontend
npm run build
```

2. Deploy the `dist/` folder to:
   - Netlify
   - Vercel
   - AWS S3 + CloudFront
   - Or serve with nginx

## Testing the Connection

### Test Backend API
```bash
# Test if backend is accessible
curl http://167.172.30.134:8000/api/candidates/

# Should return JSON with candidates data
```

### Test Frontend Connection
1. Open browser developer tools (F12)
2. Go to the Console tab
3. You should see: `🔗 API Base URL: http://167.172.30.134:8000/api/`
4. Check the Network tab to see API requests

## Current Status

✅ Backend CORS configured
✅ Frontend API client configured
✅ All components connected to API
✅ Error handling implemented
✅ Logging enabled for debugging

## Next Steps

1. Test the connection by running both backend and frontend
2. Verify data is loading correctly in all pages
3. Monitor browser console for any errors
4. Consider implementing loading states and error boundaries
5. Plan for production deployment with proper security measures


