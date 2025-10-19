#!/bin/bash

echo "🚀 Starting Arizona Sunshine Backend (Docker + Django)..."

# Build and start containers
docker compose up -d --build

echo "⏳ Waiting for DB to be ready..."
sleep 5

# Apply migrations
echo "📌 Running migrations..."
docker compose exec web python manage.py migrate

# Create superuser if not exists
echo "📌 Creating superuser (if not exists)..."
docker compose exec web python manage.py createsuperuser --noinput || true

echo "✅ Backend is now running at: http://localhost:8000"
echo "✅ Admin is at: http://localhost:8000/admin"
echo "Login using your superuser credentials."
