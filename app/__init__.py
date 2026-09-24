from flask import Flask
from sqlalchemy import text

from config import Config
from app.extensions import db, migrate


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    if not app.config["SECRET_KEY"] or not app.config["SECRET_KEY"].strip():
        raise RuntimeError("SECRET_KEY must be configured in the environment.")

    db.init_app(app)
    from app import models  # noqa: F401
    migrate.init_app(app, db)

    @app.route("/")
    def home():
        return {
            "status": "success",
            "message": "MeetingAI Backend is running"
        }

    @app.route("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))

            return {
                "status": "success",
                "database": "connected",
                "system": "MeetingAI"
            }

        except Exception as e:
            # Exception messages can contain credentials, SQL, or local paths.
            app.logger.error("Database health check failed (%s).", type(e).__name__)
            return {
                "status": "error",
                "database": "disconnected",
                "error": "Database connection unavailable."
            }, 500

    return app
