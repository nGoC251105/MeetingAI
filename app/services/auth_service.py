"""Authentication business rules; no Flask request or session dependency."""

import re
import secrets

from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User


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


def register_user(data):
    errors = {}
    name = data.get("full_name")
    if not isinstance(name, str) or not name.strip():
        errors["full_name"] = "required"
    elif len(name.strip()) > 120:
        errors["full_name"] = "too_long"
    email = normalize_email(data.get("email"))
    if email is None:
        errors["email"] = "invalid"
    password = data.get("password")
    if not isinstance(password, str):
        errors["password"] = "required"
    elif len(password) < 8:
        errors["password"] = "too_short"
    confirmation = data.get("confirm_password")
    if not isinstance(confirmation, str):
        errors["confirm_password"] = "required"
    elif confirmation != password:
        errors["confirm_password"] = "mismatch"
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
        result["created_at"] = user.created_at.isoformat()
    return result
