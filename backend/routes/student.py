from datetime import date

from flask import Blueprint, jsonify, request, send_file

from extensions import cache, db
from models import Application, CompanyProfile, PlacementDrive, StudentProfile, UserRole
from routes.utils import role_required
from tasks.jobs import export_student_history_csv

bp = Blueprint("student", __name__, url_prefix="/api/student")


@bp.get("/dashboard")
@role_required(UserRole.STUDENT.value)
def dashboard(current_user):
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return jsonify({"message": "Student profile missing"}), 404

    apps = Application.query.filter_by(student_id=profile.id).all()
    return jsonify(
        {
            "name": profile.full_name,
            "branch": profile.branch,
            "cgpa": profile.cgpa,
            "year": profile.year,
            "applied_count": len(apps),
            "selected_count": sum(1 for app in apps if app.status == "selected"),
        }
    )


@bp.get("/drives")
@role_required(UserRole.STUDENT.value)
@cache.cached(timeout=60, query_string=True)
def eligible_drives(current_user):
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return jsonify({"message": "Student profile missing"}), 404

    q = request.args.get("q", "").strip()
    rows = (
        db.session.query(PlacementDrive, CompanyProfile)
        .join(CompanyProfile, CompanyProfile.id == PlacementDrive.company_id)
        .filter(
            PlacementDrive.status == "approved",
            PlacementDrive.application_deadline >= date.today(),
            PlacementDrive.eligible_year == profile.year,
            PlacementDrive.min_cgpa <= profile.cgpa,
            PlacementDrive.eligible_branch.ilike(f"%{profile.branch}%"),
            PlacementDrive.job_title.ilike(f"%{q}%"),
        )
        .all()
    )
    return jsonify(
        [
            {
                "drive_id": drive.id,
                "company": company.company_name,
                "job_title": drive.job_title,
                "deadline": drive.application_deadline.isoformat(),
                "location": drive.location,
                "ctc_lpa": drive.ctc_lpa,
            }
            for drive, company in rows
        ]
    )


@bp.post("/drives/<int:drive_id>/apply")
@role_required(UserRole.STUDENT.value)
def apply_drive(current_user, drive_id):
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return jsonify({"message": "Student profile missing"}), 404

    drive = db.session.get(PlacementDrive, drive_id)
    if not drive:
        return jsonify({"message": "Drive not found"}), 404
    if drive.status != "approved":
        return jsonify({"message": "Drive is not open for applications"}), 400
    if drive.application_deadline < date.today():
        return jsonify({"message": "Application deadline is over"}), 400

    eligible = (
        profile.year == drive.eligible_year
        and profile.cgpa >= drive.min_cgpa
        and profile.branch.lower() in drive.eligible_branch.lower()
    )
    if not eligible:
        return jsonify({"message": "You are not eligible for this drive"}), 400

    already_applied = Application.query.filter_by(student_id=profile.id, drive_id=drive.id).first()
    if already_applied:
        return jsonify({"message": "You have already applied"}), 400

    application = Application(student_id=profile.id, drive_id=drive.id)
    db.session.add(application)
    db.session.commit()
    return jsonify({"message": "Application submitted successfully"}), 201


@bp.get("/applications")
@role_required(UserRole.STUDENT.value)
def my_applications(current_user):
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return jsonify({"message": "Student profile missing"}), 404

    rows = (
        db.session.query(Application, PlacementDrive, CompanyProfile)
        .join(PlacementDrive, PlacementDrive.id == Application.drive_id)
        .join(CompanyProfile, CompanyProfile.id == PlacementDrive.company_id)
        .filter(Application.student_id == profile.id)
        .all()
    )
    return jsonify(
        [
            {
                "application_id": app.id,
                "company": company.company_name,
                "drive": drive.job_title,
                "status": app.status,
                "interview_at": app.interview_at.isoformat() if app.interview_at else None,
                "applied_on": app.application_date.isoformat(),
            }
            for app, drive, company in rows
        ]
    )


@bp.get("/export")
@role_required(UserRole.STUDENT.value)
def export_csv(current_user):
    csv_text = export_student_history_csv(current_user.id)
    return send_file(
        csv_text,
        as_attachment=True,
        download_name="application_history.csv",
        mimetype="text/csv",
    )


@bp.patch("/profile")
@role_required(UserRole.STUDENT.value)
def update_profile(current_user):
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return jsonify({"message": "Student profile missing"}), 404

    payload = request.get_json(force=True)
    for field in ["full_name", "phone", "branch", "resume_link"]:
        if field in payload:
            setattr(profile, field, payload[field])
    if "cgpa" in payload:
        profile.cgpa = float(payload["cgpa"])
    if "year" in payload:
        profile.year = int(payload["year"])

    db.session.commit()
    return jsonify({"message": "Profile updated"})
