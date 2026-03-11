from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from extensions import db
from models import CompanyProfile, StudentProfile, User, UserRole

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def user_payload(user: User):
    return {"id": user.id, "email": user.email, "role": user.role, "active": user.active}


@bp.post("/register/student")
def register_student():
    data = request.get_json(force=True)
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "Email already exists"}), 400

    user = User(email=data["email"], password=data["password"], role=UserRole.STUDENT.value)
    db.session.add(user)
    db.session.flush()
    profile = StudentProfile(
        user_id=user.id,
        full_name=data["full_name"],
        phone=data.get("phone"),
        branch=data["branch"],
        cgpa=float(data["cgpa"]),
        year=int(data["year"]),
        resume_link=data.get("resume_link"),
    )
    db.session.add(profile)
    db.session.commit()
    return jsonify({"message": "Student registered successfully"}), 201


@bp.post("/register/company")
def register_company():
    data = request.get_json(force=True)
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "Email already exists"}), 400

    user = User(email=data["email"], password=data["password"], role=UserRole.COMPANY.value)
    db.session.add(user)
    db.session.flush()
    profile = CompanyProfile(
        user_id=user.id,
        company_name=data["company_name"],
        hr_contact=data["hr_contact"],
        website=data.get("website"),
        description=data.get("description"),
    )
    db.session.add(profile)
    db.session.commit()
    return jsonify({"message": "Company registration submitted for approval"}), 201


@bp.post("/login")
def login():
    data = request.get_json(force=True)
    user = User.query.filter_by(email=data.get("email"), password=data.get("password")).first()
    if not user:
        return jsonify({"message": "Invalid credentials"}), 401
    if not user.active:
        return jsonify({"message": "Account deactivated"}), 403

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token, "user": user_payload(user)})
