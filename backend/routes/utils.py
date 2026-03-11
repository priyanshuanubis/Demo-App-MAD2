from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models import User


def current_user():
    identity = get_jwt_identity()
    return db.session.get(User, int(identity)) if identity else None


def role_required(*roles):
    def outer(fn):
        @wraps(fn)
        @jwt_required()
        def inner(*args, **kwargs):
            user = current_user()
            if not user or not user.active or user.role not in roles:
                return jsonify({"message": "Unauthorized"}), 403
            return fn(user, *args, **kwargs)

        return inner

    return outer
