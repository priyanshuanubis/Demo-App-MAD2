import csv
import io
from datetime import date, timedelta

from flask import current_app

from extensions import db
from models import Application, CompanyProfile, PlacementDrive, StudentProfile


def export_student_history_csv(student_user_id):
    profile = StudentProfile.query.filter_by(user_id=student_user_id).first()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student ID", "Company Name", "Drive Title", "Application Status", "Applied Date"])

    if profile:
        rows = (
            db.session.query(Application, PlacementDrive, CompanyProfile)
            .join(PlacementDrive, PlacementDrive.id == Application.drive_id)
            .join(CompanyProfile, CompanyProfile.id == PlacementDrive.company_id)
            .filter(Application.student_id == profile.id)
            .all()
        )
        for app, drive, company in rows:
            writer.writerow([profile.id, company.company_name, drive.job_title, app.status, app.application_date.isoformat()])

    memory = io.BytesIO(output.getvalue().encode("utf-8"))
    memory.seek(0)
    return memory


def daily_deadline_reminders():
    upcoming = date.today() + timedelta(days=2)
    drives = PlacementDrive.query.filter(PlacementDrive.application_deadline <= upcoming).all()
    return f"Daily reminders prepared for {len(drives)} near-deadline drives."


def monthly_admin_report():
    month_start = date.today().replace(day=1)
    drives = PlacementDrive.query.filter(PlacementDrive.created_at >= month_start).count()
    applications = Application.query.filter(Application.application_date >= month_start).count()
    selected = Application.query.filter_by(status="selected").count()

    html_report = f"""
    <h2>Monthly Placement Activity Report</h2>
    <ul>
      <li>Total drives created: {drives}</li>
      <li>Total applications submitted: {applications}</li>
      <li>Total students selected: {selected}</li>
    </ul>
    """
    current_app.logger.info("Generated monthly report: %s", html_report)
    return html_report
