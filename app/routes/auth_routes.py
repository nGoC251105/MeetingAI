"""JSON transport, session cookie lifecycle and reusable route protection."""

from functools import wraps

from flask import Blueprint, current_app, g, request, session
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from app.services import auth_service


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

ERRORS = {
    "VALIDATION_ERROR": (400, "Dữ liệu gửi lên chưa hợp lệ."),
    "UNAUTHORIZED": (401, "Vui lòng đăng nhập để tiếp tục."),
    "EMAIL_EXISTS": (409, "Email đã được sử dụng."),
    "INVALID_CREDENTIALS": (401, "Email hoặc mật khẩu không đúng."),
    "ACCOUNT_DISABLED": (403, "Tài khoản hiện không hoạt động."),
    "DB_ERROR": (500, "Không thể lưu dữ liệu. Vui lòng thử lại."),
    "INTERNAL_ERROR": (500, "Không thể xử lý yêu cầu. Vui lòng thử lại."),
}


@auth_bp.errorhandler(auth_service.AuthError)
def error_response(error):
    status, message = ERRORS[error.code]
    if error.code == "ACCOUNT_DISABLED":
        current_app.logger.warning("Authentication rejected (ACCOUNT_DISABLED).")
    return {"success": False, "error": {
        "code": error.code, "message": message, "details": error.details,
    }}, status


def login_required(view):
    @wraps(view)
    def protected(*args, **kwargs):
        try:
            g.current_user = auth_service.get_authenticated_user(session.get("user_id"))
        except auth_service.AuthError:
            session.clear()
            raise
        return view(*args, **kwargs)
    return protected


def json_object():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise auth_service.AuthError("VALIDATION_ERROR", {"body": "json_object_required"})
    return data


def success(data=None, status=200):
    return {"success": True, "data": data, "message": None}, status


@auth_bp.after_request
def prevent_auth_caching(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@auth_bp.errorhandler(SQLAlchemyError)
def database_error(error):
    current_app.logger.error("Authentication database failure (%s).", type(error).__name__)
    return error_response(auth_service.AuthError("DB_ERROR"))


@auth_bp.errorhandler(Exception)
def internal_error(error):
    if isinstance(error, HTTPException):
        return error
    current_app.logger.error("Authentication internal failure (%s).", type(error).__name__)
    return error_response(auth_service.AuthError("INTERNAL_ERROR"))


@auth_bp.post("/register")
def register():
    user = auth_service.register_user(json_object())
    return success(auth_service.user_data(user), 201)


@auth_bp.post("/login")
def login():
    session.clear()
    user = auth_service.authenticate_user(json_object())
    data = auth_service.user_data(user)
    session["user_id"] = user.id
    return success(data)


@auth_bp.post("/logout")
def logout():
    # A003 explicitly permits successful logout after the session has expired.
    session.clear()
    return success()


@auth_bp.get("/me")
@login_required
def me():
    return success(auth_service.user_data(g.current_user, include_created_at=True))
