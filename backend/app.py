import csv
import io
import os
from datetime import date, datetime, timedelta
from enum import Enum

from celery import Celery
from flask import Flask, jsonify, request, send_file
from flask_caching import Cache
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "placement_portal.db")

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{DB_PATH}",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "dev-secret"),
    CELERY_BROKER_URL=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    CELERY_RESULT_BACKEND=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    CACHE_TYPE="RedisCache",
    CACHE_REDIS_URL=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    CACHE_DEFAULT_TIMEOUT=120,
)

# Graceful fallback when Redis isn't available locally.
if os.getenv("REDIS_DISABLED", "0") == "1":
    app.config["CACHE_TYPE"] = "SimpleCache"

CORS(app)
db = SQLAlchemy(app)
jwt = JWTManager(app)
cache = Cache(app)


def make_celery(flask_app: Flask):
    celery = Celery(
        flask_app.import_name,
        broker=flask_app.config["CELERY_BROKER_URL"],
        backend=flask_app.config["CELERY_RESULT_BACKEND"],
    )
    celery.conf.update(flask_app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(app)


class UserRole(str, Enum):
    ADMIN = "admin"
    COMPANY = "company"
    STUDENT = "student"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLACKLISTED = "blacklisted"


class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    SHORTLISTED = "shortlisted"
    SELECTED = "selected"
    REJECTED = "rejected"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    branch = db.Column(db.String(80), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    resume_link = db.Column(db.String(300), nullable=True)


class CompanyProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    company_name = db.Column(db.String(160), nullable=False)
    hr_contact = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(200), nullable=True)
    approval_status = db.Column(db.String(20), default=ApprovalStatus.PENDING.value)


class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company_profile.id"), nullable=False)
    job_title = db.Column(db.String(120), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    eligible_branch = db.Column(db.String(80), nullable=False)
    min_cgpa = db.Column(db.Float, nullable=False)
    eligible_year = db.Column(db.Integer, nullable=False)
    application_deadline = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default=ApprovalStatus.PENDING.value)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profile.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drive.id"), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default=ApplicationStatus.APPLIED.value)
    __table_args__ = (UniqueConstraint("student_id", "drive_id", name="uq_student_drive"),)


def seed_admin():
    admin = User.query.filter_by(role=UserRole.ADMIN.value).first()
    if not admin:
        db.session.add(
            User(email="admin@ppa.local", password="admin123", role=UserRole.ADMIN.value)
        )
        db.session.commit()


def user_payload(user: User):
    return {"id": user.id, "email": user.email, "role": user.role, "active": user.active}


def get_current_user() -> User:
    uid = int(get_jwt_identity())
    return User.query.get(uid)


def require_role(*roles):
    def wrapper(fn):
        @jwt_required()
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user or user.role not in roles or not user.active:
                return jsonify({"message": "Unauthorized"}), 403
            return fn(user, *args, **kwargs)

        decorated.__name__ = fn.__name__
        return decorated

    return wrapper


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/auth/register/student")
def register_student():
    data = request.get_json(force=True)
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "Email already exists"}), 400
    user = User(email=data["email"], password=data["password"], role=UserRole.STUDENT.value)
    db.session.add(user)
    db.session.flush()
    db.session.add(
        StudentProfile(
            user_id=user.id,
            full_name=data["full_name"],
            branch=data["branch"],
            cgpa=float(data["cgpa"]),
            year=int(data["year"]),
            resume_link=data.get("resume_link"),
        )
    )
    db.session.commit()
    return jsonify({"message": "Student registered"}), 201


@app.post("/api/auth/register/company")
def register_company():
    data = request.get_json(force=True)
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "Email already exists"}), 400
    user = User(email=data["email"], password=data["password"], role=UserRole.COMPANY.value)
    db.session.add(user)
    db.session.flush()
    db.session.add(
        CompanyProfile(
            user_id=user.id,
            company_name=data["company_name"],
            hr_contact=data["hr_contact"],
            website=data.get("website"),
        )
    )
    db.session.commit()
    return jsonify({"message": "Company registration submitted for approval"}), 201


@app.post("/api/auth/login")
def login():
    data = request.get_json(force=True)
    user = User.query.filter_by(email=data.get("email"), password=data.get("password")).first()
    if not user:
        return jsonify({"message": "Invalid credentials"}), 401
    if not user.active:
        return jsonify({"message": "Account deactivated"}), 403
    token = create_access_token(identity=str(user.id), expires_delta=timedelta(hours=6))
    return jsonify({"access_token": token, "user": user_payload(user)})


@app.get("/api/admin/dashboard")
@require_role(UserRole.ADMIN.value)
@cache.cached(timeout=30)
def admin_dashboard(current_user):
    return jsonify(
        {
            "students": User.query.filter_by(role=UserRole.STUDENT.value).count(),
            "companies": User.query.filter_by(role=UserRole.COMPANY.value).count(),
            "drives": PlacementDrive.query.count(),
            "applications": Application.query.count(),
        }
    )


@app.get("/api/admin/companies")
@require_role(UserRole.ADMIN.value)
def admin_companies(current_user):
    rows = (
        db.session.query(User, CompanyProfile)
        .join(CompanyProfile, CompanyProfile.user_id == User.id)
        .all()
    )
    return jsonify(
        [
            {
                "user_id": u.id,
                "company_id": c.id,
                "company_name": c.company_name,
                "status": c.approval_status,
                "active": u.active,
            }
            for u, c in rows
        ]
    )


@app.patch("/api/admin/companies/<int:company_id>/status")
@require_role(UserRole.ADMIN.value)
def set_company_status(current_user, company_id):
    status = request.get_json(force=True).get("status")
    company = CompanyProfile.query.get_or_404(company_id)
    company.approval_status = status
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Updated"})


@app.patch("/api/admin/users/<int:user_id>/active")
@require_role(UserRole.ADMIN.value)
def set_user_active(current_user, user_id):
    user = User.query.get_or_404(user_id)
    user.active = bool(request.get_json(force=True).get("active"))
    db.session.commit()
    return jsonify({"message": "Updated"})


@app.get("/api/admin/search")
@require_role(UserRole.ADMIN.value)
def admin_search(current_user):
    q = request.args.get("q", "")
    students = (
        db.session.query(User, StudentProfile)
        .join(StudentProfile, StudentProfile.user_id == User.id)
        .filter(StudentProfile.full_name.ilike(f"%{q}%"))
        .all()
    )
    companies = (
        db.session.query(User, CompanyProfile)
        .join(CompanyProfile, CompanyProfile.user_id == User.id)
        .filter(CompanyProfile.company_name.ilike(f"%{q}%"))
        .all()
    )
    return jsonify(
        {
            "students": [{"id": u.id, "name": s.full_name, "active": u.active} for u, s in students],
            "companies": [
                {
                    "id": u.id,
                    "company": c.company_name,
                    "status": c.approval_status,
                    "active": u.active,
                }
                for u, c in companies
            ],
        }
    )


@app.post("/api/company/drives")
@require_role(UserRole.COMPANY.value)
def create_drive(current_user):
    company = CompanyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    if company.approval_status != ApprovalStatus.APPROVED.value:
        return jsonify({"message": "Company not approved"}), 403
    data = request.get_json(force=True)
    drive = PlacementDrive(
        company_id=company.id,
        job_title=data["job_title"],
        job_description=data["job_description"],
        eligible_branch=data["eligible_branch"],
        min_cgpa=float(data["min_cgpa"]),
        eligible_year=int(data["eligible_year"]),
        application_deadline=date.fromisoformat(data["application_deadline"]),
    )
    db.session.add(drive)
    db.session.commit()
    return jsonify({"message": "Drive submitted for admin approval", "drive_id": drive.id}), 201


@app.get("/api/company/drives")
@require_role(UserRole.COMPANY.value)
def list_company_drives(current_user):
    company = CompanyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    return jsonify(
        [
            {
                "id": d.id,
                "title": d.job_title,
                "status": d.status,
                "deadline": d.application_deadline.isoformat(),
            }
            for d in drives
        ]
    )


@app.patch("/api/admin/drives/<int:drive_id>/status")
@require_role(UserRole.ADMIN.value)
def set_drive_status(current_user, drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = request.get_json(force=True).get("status", ApprovalStatus.PENDING.value)
    db.session.commit()
    return jsonify({"message": "Drive updated"})


@app.get("/api/student/drives")
@require_role(UserRole.STUDENT.value)
@cache.cached(timeout=60, query_string=True)
def student_drives(current_user):
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    q = request.args.get("q", "")
    drives = (
        db.session.query(PlacementDrive, CompanyProfile)
        .join(CompanyProfile, CompanyProfile.id == PlacementDrive.company_id)
        .filter(
            PlacementDrive.status == ApprovalStatus.APPROVED.value,
            PlacementDrive.application_deadline >= date.today(),
            PlacementDrive.eligible_year == student.year,
            PlacementDrive.min_cgpa <= student.cgpa,
            PlacementDrive.eligible_branch.ilike(f"%{student.branch}%"),
            PlacementDrive.job_title.ilike(f"%{q}%"),
        )
        .all()
    )
    return jsonify(
        [
            {
                "drive_id": d.id,
                "job_title": d.job_title,
                "company_name": c.company_name,
                "deadline": d.application_deadline.isoformat(),
            }
            for d, c in drives
        ]
    )


@app.post("/api/student/drives/<int:drive_id>/apply")
@require_role(UserRole.STUDENT.value)
def apply_drive(current_user, drive_id):
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.status != ApprovalStatus.APPROVED.value:
        return jsonify({"message": "Drive not open"}), 400
    if drive.application_deadline < date.today():
        return jsonify({"message": "Deadline crossed"}), 400
    if student.year != drive.eligible_year or student.cgpa < drive.min_cgpa or student.branch not in drive.eligible_branch:
        return jsonify({"message": "Not eligible"}), 400
    exists = Application.query.filter_by(student_id=student.id, drive_id=drive.id).first()
    if exists:
        return jsonify({"message": "Already applied"}), 400
    app_obj = Application(student_id=student.id, drive_id=drive.id)
    db.session.add(app_obj)
    db.session.commit()
    return jsonify({"message": "Applied"}), 201


@app.get("/api/student/applications")
@require_role(UserRole.STUDENT.value)
def student_applications(current_user):
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    rows = (
        db.session.query(Application, PlacementDrive, CompanyProfile)
        .join(PlacementDrive, PlacementDrive.id == Application.drive_id)
        .join(CompanyProfile, CompanyProfile.id == PlacementDrive.company_id)
        .filter(Application.student_id == student.id)
        .all()
    )
    return jsonify(
        [
            {
                "application_id": a.id,
                "job_title": d.job_title,
                "company_name": c.company_name,
                "status": a.status,
                "applied_on": a.application_date.isoformat(),
            }
            for a, d, c in rows
        ]
    )


@app.patch("/api/company/applications/<int:application_id>")
@require_role(UserRole.COMPANY.value)
def company_update_application(current_user, application_id):
    company = CompanyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    app_obj = Application.query.get_or_404(application_id)
    drive = PlacementDrive.query.get_or_404(app_obj.drive_id)
    if drive.company_id != company.id:
        return jsonify({"message": "Unauthorized application access"}), 403
    app_obj.status = request.get_json(force=True).get("status", ApplicationStatus.APPLIED.value)
    db.session.commit()
    return jsonify({"message": "Application status updated"})


@celery.task(name="tasks.export_student_history")
def export_student_history(student_user_id: int):
    student = StudentProfile.query.filter_by(user_id=student_user_id).first()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student ID", "Company", "Drive", "Status", "Applied Date"])
    rows = (
        db.session.query(Application, PlacementDrive, CompanyProfile)
        .join(PlacementDrive, PlacementDrive.id == Application.drive_id)
        .join(CompanyProfile, CompanyProfile.id == PlacementDrive.company_id)
        .filter(Application.student_id == student.id)
        .all()
    )
    for app_row, drive, company in rows:
        writer.writerow(
            [student.id, company.company_name, drive.job_title, app_row.status, app_row.application_date.isoformat()]
        )
    return output.getvalue()


@app.get("/api/student/export")
@require_role(UserRole.STUDENT.value)
def export_history(current_user):
    # In constrained setup we run task eagerly if CELERY_TASK_ALWAYS_EAGER=1
    if os.getenv("CELERY_TASK_ALWAYS_EAGER", "1") == "1":
        csv_data = export_student_history(current_user.id)
    else:
        task = export_student_history.delay(current_user.id)
        csv_data = task.get(timeout=20)
    return send_file(
        io.BytesIO(csv_data.encode("utf-8")),
        as_attachment=True,
        download_name="application_history.csv",
        mimetype="text/csv",
    )


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour=9, minute=0), send_daily_deadline_reminders.s())
    sender.add_periodic_task(crontab(day_of_month=1, hour=10, minute=0), send_monthly_admin_report.s())


from celery.schedules import crontab


@celery.task(name="tasks.daily_reminders")
def send_daily_deadline_reminders():
    upcoming = date.today() + timedelta(days=2)
    drives = PlacementDrive.query.filter(PlacementDrive.application_deadline <= upcoming).all()
    # Placeholder for email/SMS/webhook integration
    return f"Reminder count: {len(drives)}"


@celery.task(name="tasks.monthly_report")
def send_monthly_admin_report():
    month_start = date.today().replace(day=1)
    drives = PlacementDrive.query.filter(PlacementDrive.application_deadline >= month_start).count()
    selected = Application.query.filter_by(status=ApplicationStatus.SELECTED.value).count()
    return f"Monthly report -> drives: {drives}, selected: {selected}"


@app.post("/api/init")
def init_db():
    db.create_all()
    seed_admin()
    return jsonify({"message": "Database initialized with default admin"})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_admin()
    app.run(debug=True, host="0.0.0.0", port=5000)
