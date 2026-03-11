# Test Guide (Deployable Files Only)

This project now ships **source-only deployable files** (no binary DB committed).

## 1) Fresh setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Initialize database programmatically

Start backend:

```bash
python app.py
```

In another terminal:

```bash
curl -X POST http://localhost:5000/api/init
curl http://localhost:5000/api/health
```

Expected health response:

```json
{"status":"ok","service":"placement-portal-api"}
```

## 3) Run frontend

```bash
cd frontend
python -m http.server 8080
```

Open: `http://localhost:8080`

## 4) API smoke tests

### Admin login

```bash
curl -s -X POST http://localhost:5000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@ppa.local","password":"admin123"}'
```

### Student register

```bash
curl -s -X POST http://localhost:5000/api/auth/register/student \
  -H 'Content-Type: application/json' \
  -d '{"email":"student1@ppa.local","password":"pass123","full_name":"Student One","branch":"CSE","cgpa":8.2,"year":4}'
```

### Company register

```bash
curl -s -X POST http://localhost:5000/api/auth/register/company \
  -H 'Content-Type: application/json' \
  -d '{"email":"company1@ppa.local","password":"pass123","company_name":"TechNova","hr_contact":"hr@technova.com","website":"https://technova.example"}'
```

## 5) Optional async/scheduled test

```bash
redis-server
cd backend
source .venv/bin/activate
export CELERY_TASK_ALWAYS_EAGER=0
celery -A tasks.celery_app.celery worker -B --loglevel=info
```

## 6) Important

- Do **not** commit `backend/placement_portal.db`.
- DB is generated at runtime using model code and `/api/init`.
