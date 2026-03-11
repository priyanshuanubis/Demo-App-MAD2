from flask import Flask, jsonify

from config import DevConfig
from extensions import cache, cors, db, jwt
from models import seed_admin_user
from routes.admin import bp as admin_bp
from routes.auth import bp as auth_bp
from routes.company import bp as company_bp
from routes.student import bp as student_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(DevConfig)

    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    cors.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(student_bp)

    @app.get("/api/health")
    def health_check():
        return jsonify({"status": "ok", "service": "placement-portal-api"})

    @app.post("/api/init")
    def init_database():
        db.create_all()
        seed_admin_user()
        return jsonify({"message": "Database initialized. Admin seeded."})

    return app


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_admin_user()
    app.run(host="0.0.0.0", port=5000, debug=True)
