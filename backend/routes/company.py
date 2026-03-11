from datetime import date, datetime

from flask import Blueprint, jsonify, request

from extensions import db
from models import Application, CompanyProfile, PlacementDrive, UserRole
from routes.utils import role_required

bp = Blueprint("company", __name__, url_prefix="/api/company")


@bp.get("/dashboard")
@role_required(UserRole.COMPANY.value)
def company_dashboard(current_user):
    company = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({"message": "Company profile not found"}), 404

    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    drive_ids = [drive.id for drive in drives]
    applicants = Application.query.filter(Application.drive_id.in_(drive_ids)).count() if drive_ids else 0

    return jsonify(
        {
            "company": {
                "name": company.company_name,
                "approval_status": company.approval_status,
                "hr_contact": company.hr_contact,
            },
            "drives_created": len(drives),
            "total_applicants": applicants,
        }
    )


@bp.post("/drives")
@role_required(UserRole.COMPANY.value)
def create_drive(current_user):
    company = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({"message": "Company profile not found"}), 404
    if company.approval_status != "approved":
        return jsonify({"message": "Company must be approved before creating drives"}), 403

    payload = request.get_json(force=True)
    drive = PlacementDrive(
        company_id=company.id,
        job_title=payload["job_title"],
        job_description=payload["job_description"],
        eligible_branch=payload["eligible_branch"],
        min_cgpa=float(payload["min_cgpa"]),
        eligible_year=int(payload["eligible_year"]),
        location=payload.get("location"),
        ctc_lpa=float(payload.get("ctc_lpa")) if payload.get("ctc_lpa") else None,
        application_deadline=date.fromisoformat(payload["application_deadline"]),
    )
    db.session.add(drive)
    db.session.commit()
    return jsonify({"message": "Drive created and pending admin approval", "drive_id": drive.id}), 201


@bp.get("/drives")
@role_required(UserRole.COMPANY.value)
def list_drives(current_user):
    company = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({"message": "Company profile not found"}), 404

    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    return jsonify(
        [
            {
                "id": drive.id,
                "title": drive.job_title,
                "status": drive.status,
                "deadline": drive.application_deadline.isoformat(),
            }
            for drive in drives
        ]
    )


@bp.get("/applications")
@role_required(UserRole.COMPANY.value)
def drive_applications(current_user):
    company = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({"message": "Company profile not found"}), 404

    rows = (
        db.session.query(Application, PlacementDrive)
        .join(PlacementDrive, PlacementDrive.id == Application.drive_id)
        .filter(PlacementDrive.company_id == company.id)
        .all()
    )

    return jsonify(
        [
            {
                "application_id": application.id,
                "drive": drive.job_title,
                "status": application.status,
                "interview_at": application.interview_at.isoformat() if application.interview_at else None,
            }
            for application, drive in rows
        ]
    )


@bp.patch("/applications/<int:application_id>")
@role_required(UserRole.COMPANY.value)
def update_application(current_user, application_id):
    company = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({"message": "Company profile not found"}), 404

    payload = request.get_json(force=True)
    app_obj = db.session.get(Application, application_id)
    if not app_obj:
        return jsonify({"message": "Application not found"}), 404

    drive = db.session.get(PlacementDrive, app_obj.drive_id)
    if drive.company_id != company.id:
        return jsonify({"message": "Unauthorized"}), 403

    app_obj.status = payload.get("status", app_obj.status)
    if payload.get("interview_at"):
        app_obj.interview_at = datetime.fromisoformat(payload["interview_at"])
    app_obj.remarks = payload.get("remarks", app_obj.remarks)
    db.session.commit()

    return jsonify({"message": "Application updated"})
