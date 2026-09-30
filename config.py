import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    DEBUG = os.getenv("FLASK_DEBUG", "false").strip().lower() in {
        "1", "true", "yes", "on"
    }

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "meeting_ai")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://"
        f"{DB_USER}:"
        f"{quote_plus(DB_PASSWORD)}@"
        f"{DB_HOST}:"
        f"{DB_PORT}/"
        f"{DB_NAME}"
        f"?charset=utf8mb4"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # MySQL TIMESTAMP reads and server-generated timestamps use UTC per D11.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"init_command": "SET time_zone = '+00:00'"},
    }
    APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Ho_Chi_Minh")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Only explicitly declared development may opt into HTTP cookies.
    # Missing/unknown environments and flags keep the HTTPS production default.
    SESSION_COOKIE_SECURE = (
        os.getenv("FLASK_ENV", "production").strip().lower() != "development"
        or os.getenv("SESSION_COOKIE_SECURE", "false").strip().lower()
        not in {"0", "false", "no", "off"}
    )
