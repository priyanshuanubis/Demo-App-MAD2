from flask import Blueprint, jsonify, request

from extensions import cache, db
from models import Application, CompanyProfile, PlacementDrive, StudentProfile, User, UserRole
from routes.utils import role_required

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.get("/dashboard")
@role_required(UserRole.ADMIN.value)
@cache.cached(timeout=30)
def dashboard(_user):
    return jsonify(
        {
            "students": User.query.filter_by(role=UserRole.STUDENT.value).count(),
            "companies": User.query.filter_by(role=UserRole.COMPANY.value).count(),
            "drives": PlacementDrive.query.count(),
            "applications": Application.query.count(),
            "selected": Application.query.filter_by(status="selected").count(),
        }
    )


@bp.get("/companies")
@role_required(UserRole.ADMIN.value)
def list_companies(_user):
    rows = db.session.query(User, CompanyProfile).join(CompanyProfile, CompanyProfile.user_id == User.id).all()
    return jsonify(
        [
            {
                "user_id": user.id,
                "company_id": company.id,
                "name": company.company_name,
                "hr_contact": company.hr_contact,
                "website": company.website,
                "approval_status": company.approval_status,
                "active": user.active,
            }
            for user, company in rows
        ]
    )


@bp.patch("/companies/<int:company_id>/status")
@role_required(UserRole.ADMIN.value)
def approve_company(_user, company_id):
    payload = request.get_json(force=True)
    company = db.session.get(CompanyProfile, company_id)
    if not company:
        return jsonify({"message": "Company not found"}), 404

    company.approval_status = payload.get("status", company.approval_status)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Company status updated"})


@bp.patch("/drives/<int:drive_id>/status")
@role_required(UserRole.ADMIN.value)
def approve_drive(_user, drive_id):
    payload = request.get_json(force=True)
    drive = db.session.get(PlacementDrive, drive_id)
    if not drive:
        return jsonify({"message": "Drive not found"}), 404

    drive.status = payload.get("status", drive.status)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Drive status updated"})


@bp.get("/students")
@role_required(UserRole.ADMIN.value)
def list_students(_user):
    rows = db.session.query(User, StudentProfile).join(StudentProfile, StudentProfile.user_id == User.id).all()
    return jsonify(
        [
            {
                "user_id": user.id,
                "student_id": student.id,
                "full_name": student.full_name,
                "branch": student.branch,
                "year": student.year,
                "cgpa": student.cgpa,
                "active": user.active,
            }
            for user, student in rows
        ]
    )


@bp.patch("/users/<int:user_id>/active")
@role_required(UserRole.ADMIN.value)
def toggle_user(_user, user_id):
    payload = request.get_json(force=True)
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    user.active = bool(payload.get("active", user.active))
    db.session.commit()
    return jsonify({"message": "User status updated"})


@bp.get("/search")
@role_required(UserRole.ADMIN.value)
def search(_user):
    q = request.args.get("q", "").strip()
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
    drives = PlacementDrive.query.filter(PlacementDrive.job_title.ilike(f"%{q}%")).all()

    return jsonify(
        {
            "students": [{"name": s.full_name, "active": u.active} for u, s in students],
            "companies": [{"name": c.company_name, "status": c.approval_status, "active": u.active} for u, c in companies],
            "drives": [{"id": d.id, "title": d.job_title, "status": d.status} for d in drives],
        }
    )


@bp.get("/applications")
@role_required(UserRole.ADMIN.value)
def list_applications(_user):
    rows = (
        db.session.query(Application, StudentProfile, PlacementDrive)
        .join(StudentProfile, StudentProfile.id == Application.student_id)
        .join(PlacementDrive, PlacementDrive.id == Application.drive_id)
        .all()
    )
    return jsonify(
        [
            {
                "application_id": app.id,
                "student": student.full_name,
                "drive": drive.job_title,
                "status": app.status,
                "applied_on": app.application_date.isoformat(),
            }
            for app, student, drive in rows
        ]
    )
