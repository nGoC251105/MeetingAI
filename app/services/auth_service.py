"""Authentication business rules; no Flask request or session dependency."""

import re
import secrets

from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User
from app.utils.datetime_utils import serialize_datetime


class AuthError(Exception):
    def __init__(self, code, details=None):
        super().__init__(code)
        self.code = code
        self.details = details or {}


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password_hash, password):
    if not isinstance(password_hash, str) or not isinstance(password, str):
        return False
    try:
        return check_password_hash(password_hash, password)
    except (ValueError, TypeError):
        # Invalid/legacy hashes are never a plaintext fallback.
        return False


# Unknown accounts still perform the same expensive password verification.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(32))


def normalize_email(value):
    if not isinstance(value, str):
        return None
    email = value.strip().lower()
    if len(email) > 191 or email.count("@") != 1:
        return None
    local, domain = email.split("@")
    if not local or len(local) > 64 or local.startswith(".") or local.endswith("."):
        return None
    if ".." in local or not re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+", local):
        return None
    labels = domain.split(".")
    if len(labels) < 2 or any(
        not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
        for label in labels
    ):
        return None
    return email


def profile_fields(data, errors):
    name = data.get("full_name")
    if not isinstance(name, str) or not name.strip():
        errors["full_name"] = "required"
    elif len(name.strip()) > 120:
        errors["full_name"] = "too_long"
    email = normalize_email(data.get("email"))
    if email is None:
        errors["email"] = "invalid"
    return name.strip() if isinstance(name, str) else None, email


def password_fields(data, errors, field="password"):
    password = data.get(field)
    if not isinstance(password, str):
        errors[field] = "required"
    elif len(password) < 8:
        errors[field] = "too_short"
    confirmation = data.get("confirm_password")
    if not isinstance(confirmation, str):
        errors["confirm_password"] = "required"
    elif confirmation != password:
        errors["confirm_password"] = "mismatch"
    return password


def register_user(data):
    errors = {}
    name, email = profile_fields(data, errors)
    password = password_fields(data, errors)
    if errors:
        raise AuthError("VALIDATION_ERROR", errors)

    try:
        if db.session.scalar(db.select(User).where(User.email == email)) is not None:
            raise AuthError("EMAIL_EXISTS", {"email": "exists"})
        user = User(full_name=name.strip(), email=email,
                    password_hash=hash_password(password), is_active=1)
        db.session.add(user)
        db.session.commit()
        return user
    except IntegrityError as error:
        db.session.rollback()
        # The unique constraint also protects concurrent registrations.
        if getattr(error.orig, "args", (None,))[0] == 1062:
            raise AuthError("EMAIL_EXISTS", {"email": "exists"}) from None
        raise
    except Exception:
        db.session.rollback()
        raise


def authenticate_user(data):
    email = normalize_email(data.get("email"))
    password = data.get("password")
    errors = {}
    if email is None:
        errors["email"] = "invalid"
    if not isinstance(password, str) or not password:
        errors["password"] = "required"
    if errors:
        raise AuthError("VALIDATION_ERROR", errors)
    user = db.session.scalar(db.select(User).where(User.email == email))
    valid = verify_password(user.password_hash if user else _DUMMY_HASH, password)
    if not valid or user is None:
        raise AuthError("INVALID_CREDENTIALS")
    if not user.is_active:
        raise AuthError("ACCOUNT_DISABLED")
    return user


def get_authenticated_user(user_id):
    # Reject booleans, strings and out-of-range IDs before querying MySQL.
    if type(user_id) is not int or not 0 < user_id < 2**64:
        raise AuthError("UNAUTHORIZED")
    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        raise AuthError("UNAUTHORIZED")
    return user


def user_data(user, include_created_at=False):
    result = {"id": user.id, "full_name": user.full_name, "email": user.email}
    if include_created_at:
        result["created_at"] = serialize_datetime(user.created_at)
    return result


def require_fields_only(data, allowed):
    if data.keys() - allowed:
        # Do not reflect arbitrary client keys or values into error output.
        raise AuthError("VALIDATION_ERROR", {"body": "unexpected_fields"})


def locked_active_user(user_id):
    # Re-read under lock so concurrent account writes cannot verify an old
    # password or overwrite a user who has just been disabled/deleted.
    user = db.session.scalar(
        db.select(User).where(User.id == user_id).with_for_update()
        .execution_options(populate_existing=True)
    )
    if user is None or not user.is_active:
        raise AuthError("UNAUTHORIZED")
    return user


def update_profile(user_id, data):
    require_fields_only(data, {"full_name", "email"})
    errors = {}
    name, email = profile_fields(data, errors)
    if errors:
        raise AuthError("VALIDATION_ERROR", errors)
    try:
        user = locked_active_user(user_id)
        duplicate = db.session.scalar(
            db.select(User.id).where(User.email == email, User.id != user_id)
        )
        if duplicate is not None:
            raise AuthError("EMAIL_EXISTS", {"email": "exists"})
        user.full_name = name
        user.email = email
        db.session.commit()
        return user
    except IntegrityError as error:
        db.session.rollback()
        if getattr(error.orig, "args", (None,))[0] == 1062:
            raise AuthError("EMAIL_EXISTS", {"email": "exists"}) from None
        raise
    except Exception:
        db.session.rollback()
        raise


def change_password(user_id, data):
    require_fields_only(data, {"current_password", "new_password", "confirm_password"})
    errors = {}
    current = data.get("current_password")
    if not isinstance(current, str) or not current:
        errors["current_password"] = "required"
    password = password_fields(data, errors, "new_password")
    if errors:
        raise AuthError("VALIDATION_ERROR", errors)
    try:
        user = locked_active_user(user_id)
        if not verify_password(user.password_hash, current):
            raise AuthError("INVALID_PASSWORD")
        user.password_hash = hash_password(password)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
