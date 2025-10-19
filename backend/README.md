# Arizona Sunshine — Phase 1 Backend (Django + DRF)

## Overview
Django backend with:
- PostgreSQL (Docker)
- Playwright-based SOI scraper (management command)
- Celery + Redis for scheduling scrapes
- Django REST Framework API for frontend

## Quickstart (Docker)
1. Copy `.env.sample` to `.env` and set values.

2. Build & start services:
    docker-compose up --build -d

3. Create Django superuser:


docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

4. Run Playwright scraper manually:


docker-compose exec web python manage.py scrape_soi

5. Ingest purchased IE DB CSV:
- Put the CSV into the project (e.g. `data_raw/ie_az_2025.csv`)


docker-compose exec web python scripts/load_static_ie_db.py data_raw/ie_az_2025.csv


## API
- `/api/candidates/` — candidates endpoint
- `/api/candidates/<id>/mark_contacted/` — POST to mark as contacted
- `/api/expenditures/summary_by_race/` — aggregated sums by race

## Notes
- Update scrape selectors to match AZ SOS / apps.arizona.vote DOM.
- Keep `data_raw/` out of public repos (private data).
- For production, set `DEBUG=False` and use secure secrets.
