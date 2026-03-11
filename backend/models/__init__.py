from datetime import datetime
from enum import Enum

from sqlalchemy import UniqueConstraint

from extensions import db


class UserRole(str, Enum):
    ADMIN = "admin"
    COMPANY = "company"
    STUDENT = "student"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"
    BLACKLISTED = "blacklisted"


class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    SHORTLISTED = "shortlisted"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    SELECTED = "selected"
    REJECTED = "rejected"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    branch = db.Column(db.String(80), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    resume_link = db.Column(db.String(255))


class CompanyProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    hr_contact = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(255))
    description = db.Column(db.Text)
    approval_status = db.Column(db.String(20), default=ApprovalStatus.PENDING.value, nullable=False)


class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company_profile.id"), nullable=False)
    job_title = db.Column(db.String(120), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    eligible_branch = db.Column(db.String(120), nullable=False)
    min_cgpa = db.Column(db.Float, nullable=False)
    eligible_year = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(120))
    ctc_lpa = db.Column(db.Float)
    application_deadline = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default=ApprovalStatus.PENDING.value, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profile.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drive.id"), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(30), default=ApplicationStatus.APPLIED.value, nullable=False)
    interview_at = db.Column(db.DateTime)
    remarks = db.Column(db.String(255))
    __table_args__ = (UniqueConstraint("student_id", "drive_id", name="uq_student_drive"),)


def seed_admin_user():
    existing = User.query.filter_by(role=UserRole.ADMIN.value).first()
    if existing:
        return existing

    admin = User(email="admin@ppa.local", password="admin123", role=UserRole.ADMIN.value)
    db.session.add(admin)
    db.session.commit()
    return admin
