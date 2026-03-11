# Deployment Guide (Easy Setup)

This guide gives you a **quick local deployment** and a **simple production deployment** for the Placement Portal Application (PPA v2).

> Note: Repository is source-only (deployable files only). SQLite DB is created at runtime via `/api/init`.

---

## 1) Prerequisites

Install these first:

- Python 3.10+
- Redis server
- `pip` and `venv`
- (Optional for production) `gunicorn`, `nginx`

---

## 2) Project Structure Expected

```text
project_root/
├── frontend/
│   └── src/
├── backend/
│   ├── app.py
│   ├── models/
│   └── routes/
└── DEPLOYMENT.md
```

---

## 3) Local Deployment (Recommended for Demo/Viva)

### Step A — Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set environment variables (optional defaults shown):

```bash
export JWT_SECRET_KEY="change-me"
export REDIS_URL="redis://localhost:6379/0"
export CELERY_TASK_ALWAYS_EAGER="1"
```

Initialize DB and run API:

```bash
python app.py
```

Backend runs at: `http://localhost:5000`

---

### Step B — Frontend

In a new terminal:

```bash
cd frontend
python -m http.server 8080
```

Frontend runs at: `http://localhost:8080`

---

### Step C — Initialize Database + Admin

Call once after first run:

```bash
curl -X POST http://localhost:5000/api/init
```

Default admin credentials:

- Email: `admin@ppa.local`
- Password: `admin123`

---

## 4) Enable Celery + Scheduled Jobs

> Use this when you want actual async export and scheduled reminders/reports.

Terminal 1: keep Flask running.

Terminal 2:

```bash
cd backend
source .venv/bin/activate
redis-server
```

Terminal 3:

```bash
cd backend
source .venv/bin/activate
export CELERY_TASK_ALWAYS_EAGER="0"
celery -A tasks.celery_app.celery worker -B --loglevel=info
```

This enables:

- Daily reminder job
- Monthly admin report job
- Async CSV export task

---

## 5) Simple Production Deployment (VM)

## 5.1 Install runtime packages

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip redis-server nginx
```

## 5.2 Backend app setup

```bash
cd /opt
sudo mkdir -p ppa && sudo chown -R $USER:$USER ppa
cd ppa
# copy project files here
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt gunicorn
```

Create `.env` (example):

```bash
JWT_SECRET_KEY=super-secret-key
REDIS_URL=redis://localhost:6379/0
CELERY_TASK_ALWAYS_EAGER=0
```

Run once for DB init:

```bash
source .venv/bin/activate
python app.py
# in another terminal:
curl -X POST http://localhost:5000/api/init
```

## 5.3 Run backend with Gunicorn

```bash
cd /opt/ppa/backend
source .venv/bin/activate
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

## 5.4 Run Celery worker + beat

```bash
cd /opt/ppa/backend
source .venv/bin/activate
celery -A tasks.celery_app.celery worker -B --loglevel=info
```

## 5.5 Serve frontend with Nginx

Copy `frontend/` to `/var/www/ppa-frontend` and use this Nginx site:

```nginx
server {
    listen 80;
    server_name _;

    root /var/www/ppa-frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable and reload:

```bash
sudo ln -s /etc/nginx/sites-available/ppa /etc/nginx/sites-enabled/ppa
sudo nginx -t
sudo systemctl restart nginx
```

---

## 6) Health Checks

```bash
curl http://localhost:5000/api/health
```

Expected:

```json
{"status":"ok","service":"placement-portal-api"}
```

---

## 7) Troubleshooting

- **Frontend can’t call API:** verify API URL in `frontend/src/api.js` and CORS.
- **Export stays pending:** ensure Redis is up and Celery worker is running with `CELERY_TASK_ALWAYS_EAGER=0`.
- **Login issues after reset:** call `/api/init` again after deleting old SQLite DB.
- **Port conflicts:** use different ports (`5001`, `8081`) and update frontend API base.

---

## 8) Submission Tip (Zip)

Before zipping for portal submission, ensure root contains exactly:

- `frontend/`
- `backend/`
- `README.md`
- `DEPLOYMENT.md`

Then zip from root:

```bash
zip -r project_name_2xfXXXXXX.zip backend frontend README.md DEPLOYMENT.md
```
