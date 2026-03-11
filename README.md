# Placement Portal Application (PPA) - V2

A full-stack placement portal built with **Flask + Vue + Bootstrap + SQLite + Redis + Celery**.

## Features
- Unified login for admin/company/student with role-based authorization.
- Programmatic DB initialization + pre-seeded admin (`admin@ppa.local` / `admin123`).
- Admin approvals for companies and drives, search, deactivation/blacklisting controls.
- Company drive creation and application status updates.
- Student eligibility-based drive listing, single-attempt apply, history tracking.
- Redis-backed API caching with TTL and fallback to in-memory cache.
- Celery jobs:
  - Daily reminders for upcoming deadlines.
  - Monthly activity report generation.
  - User-triggered async CSV export for student history.

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Optional Redis/Celery:
```bash
redis-server
celery -A app.celery worker -B --loglevel=info
```

Open `frontend/index.html` in browser (or serve using `python -m http.server 8080` from `frontend/`).

## Important default credentials
- Admin email: `admin@ppa.local`
- Admin password: `admin123`
