# Placement Portal Application (PPA) - V2

A role-based campus placement platform built with the required stack:
- **Flask** (API)
- **VueJS** (UI via ESM modules)
- **Bootstrap** (styling)
- **SQLite** (database)
- **Redis + Flask-Caching** (cache)
- **Celery + Redis** (batch/scheduled jobs)

> This repository contains deployable source files only. The SQLite DB file is generated programmatically at runtime.

## Project Structure (aligned with requested schema)

```text
Demo-App-MAD2/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── extensions.py
│   ├── requirements.txt
│   ├── models/
│   │   └── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── company.py
│   │   ├── student.py
│   │   └── utils.py
│   └── tasks/
│       ├── __init__.py
│       ├── celery_app.py
│       └── jobs.py
└── frontend/
    ├── index.html
    └── src/
        ├── api.js
        ├── main.js
        └── components/
            ├── LoginRegisterPanel.js
            ├── AdminDashboard.js
            ├── CompanyDashboard.js
            └── StudentDashboard.js
```

## Implemented Functionalities

### Auth & Roles
- Admin login only (pre-seeded, no admin registration)
- Student self-registration and login
- Company self-registration and login
- Role-based route protection with JWT

### Admin
- Dashboard statistics
- Company approval/rejection/blacklist status updates
- Drive approval/rejection/closure updates
- Search students/companies/drives
- View all students and applications
- Activate/deactivate users

### Company
- Company dashboard with drive/applicant counts
- Create placement drives (only if company is admin-approved)
- View drives and applications
- Update application status (shortlist/reject/select/interview)

### Student
- Student dashboard and profile edits
- View approved + eligibility-filtered drives
- Apply once per drive only
- View application history
- Export applications CSV

### Jobs & Caching
- Daily reminder job placeholder
- Monthly HTML report generation placeholder
- CSV export service
- Redis cache with expiry

## Local Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

In another terminal for frontend:

```bash
cd frontend
python -m http.server 8080
```

Optional jobs:

```bash
cd backend
celery -A tasks.celery_app.celery worker -B --loglevel=info
```

## Default Admin
- Email: `admin@ppa.local`
- Password: `admin123`

## Testing
- Follow `TEST_GUIDE.md` for step-by-step backend/frontend/API smoke tests.
