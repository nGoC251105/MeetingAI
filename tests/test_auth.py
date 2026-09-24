"""Real MySQL authentication integration tests; only UUID-owned users are removed.

Run: .venv/Scripts/python.exe -m unittest discover -s tests -p test_auth.py -v
The existing database must already be migrated. No schema is created or dropped.
"""

from datetime import datetime
import secrets
import unittest
from unittest.mock import patch
import uuid

from sqlalchemy.exc import OperationalError
from werkzeug.security import check_password_hash

from app import create_app
from app.extensions import db
from app.models import User
from app.routes.auth_routes import login_required
from app.services import auth_service
from config import Config


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        with patch.object(Config, "SECRET_KEY", secrets.token_hex(32)):
            self.app = create_app()
        self.app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
        self.client = self.app.test_client()
        self.email = f"auth-test-{uuid.uuid4().hex}@example.com"
        self.password = "  Mật khẩu an toàn 123  "
        self.payload = {
            "full_name": "  Nguyễn Minh  ", "email": self.email,
            "password": self.password, "confirm_password": self.password,
        }
        self.addCleanup(self.cleanup_user)

        @self.app.get("/test-private")
        @login_required
        def private():
            return {"private": True}

    def cleanup_user(self):
        with self.app.app_context():
            db.session.rollback()
            db.session.execute(db.delete(User).where(User.email == self.email))
            db.session.commit()
            self.assertIsNone(db.session.scalar(db.select(User).where(User.email == self.email)))
            db.session.remove()
            db.engine.dispose()

    def register(self, **overrides):
        return self.client.post("/api/auth/register", json=self.payload | overrides)

    def login(self, **overrides):
        return self.client.post("/api/auth/login", json={
            "email": self.email, "password": self.password,
        } | overrides)

    def assert_error(self, response, status, code):
        self.assertEqual(response.status_code, status)
        self.assertEqual(set(response.json), {"success", "error"})
        self.assertIs(response.json["success"], False)
        self.assertEqual(set(response.json["error"]), {"code", "message", "details"})
        self.assertEqual(response.json["error"]["code"], code)
        self.assertIsInstance(response.json["error"]["details"], dict)
        self.assertNotIn(self.password, response.get_data(as_text=True))

    def test_registration_hash_and_no_automatic_session(self):
        response = self.register(email=f"  {self.email.upper()}  ")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {
            "success": True,
            "data": {"id": response.json["data"]["id"],
                     "full_name": "Nguyễn Minh", "email": self.email},
            "message": None,
        })
        self.assertIs(type(response.json["data"]["id"]), int)
        with self.app.app_context():
            users = db.session.scalars(db.select(User).where(User.email == self.email)).all()
            self.assertEqual(len(users), 1)
            self.assertNotEqual(users[0].password_hash, self.password)
            self.assertTrue(check_password_hash(users[0].password_hash, self.password))
            self.assertLessEqual(len(users[0].password_hash), 255)
        with self.client.session_transaction() as session:
            self.assertNotIn("user_id", session)

    def test_auth_methods_and_paths_match_a001_through_a004(self):
        routes = {
            rule.rule: rule.methods - {"HEAD", "OPTIONS"}
            for rule in self.app.url_map.iter_rules()
            if rule.endpoint.startswith("auth.")
        }
        self.assertEqual(routes, {
            "/api/auth/register": {"POST"}, "/api/auth/login": {"POST"},
            "/api/auth/logout": {"POST"}, "/api/auth/me": {"GET"},
        })

    def test_auth_success_responses_and_logs_never_expose_passwords(self):
        with patch.object(self.app.logger, "handle") as log:
            responses = [self.register(), self.login(), self.client.get("/api/auth/me")]
            with self.app.app_context():
                stored_hash = db.session.scalar(
                    db.select(User.password_hash).where(User.email == self.email)
                )
            responses.append(self.client.post("/api/auth/logout"))
        for response, status in zip(responses, (201, 200, 200, 200)):
            self.assertEqual(response.status_code, status)
            self.assertEqual(set(response.json), {"success", "data", "message"})
            self.assertIs(response.json["success"], True)
            self.assertIsNone(response.json["message"])
            for sensitive in (self.password, stored_hash, "password_hash", "confirm_password"):
                self.assertNotIn(sensitive, str(response.json))
        for call in log.call_args_list:
            for sensitive in (self.password, stored_hash):
                self.assertNotIn(sensitive, call.args[0].getMessage())

    def test_duplicate_normalized_email(self):
        self.assertEqual(self.register().status_code, 201)
        self.assert_error(self.register(email=self.email.upper()), 409, "EMAIL_EXISTS")

    def test_database_unique_constraint_handles_registration_race(self):
        self.assertEqual(self.register().status_code, 201)
        # Simulate another request committing after the pre-insert check.
        with patch.object(db.session, "scalar", return_value=None):
            self.assert_error(self.register(), 409, "EMAIL_EXISTS")
        self.assertEqual(self.login().status_code, 200)

    def test_registration_validation_matches_canonical_example(self):
        response = self.register(full_name="", email="abc", password="123", confirm_password="456")
        self.assert_error(response, 400, "VALIDATION_ERROR")
        self.assertEqual(response.json["error"]["details"], {
            "full_name": "required", "email": "invalid",
            "password": "too_short", "confirm_password": "mismatch",
        })

    def test_registration_invalid_types_lengths_and_confirmation(self):
        cases = [
            {"full_name": None}, {"full_name": []}, {"full_name": "x" * 121},
            {"password": None}, {"password": 12345678},
            {"password": "short", "confirm_password": "short"},
            {"confirm_password": None}, {"confirm_password": "different"},
            {"email": "x" * 180 + "@example.com"}, {"email": []},
            {"email": "a..b@example.com"}, {"email": "a@-example.com"},
            {"email": "a@example..com"}, {"email": "a b@example.com"},
            {"email": "a@example.com\r\nBcc: other@example.com"},
        ]
        for fields in cases:
            with self.subTest(fields=list(fields)):
                self.assert_error(self.register(**fields), 400, "VALIDATION_ERROR")
        with self.app.app_context():
            self.assertIsNone(db.session.scalar(db.select(User).where(User.email == self.email)))

    def test_missing_registration_fields(self):
        self.assert_error(self.client.post("/api/auth/register", json={}), 400, "VALIDATION_ERROR")

    def test_login_sets_only_user_id_and_preserves_password_whitespace(self):
        self.register()
        with self.client.session_transaction() as session:
            session["old_session_value"] = "discard"
        response = self.login(email=f"  {self.email.upper()}  ")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json["data"]), {"id", "full_name", "email"})
        with self.client.session_transaction() as session:
            self.assertEqual(dict(session), {"user_id": response.json["data"]["id"]})
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)

    def test_wrong_password_and_unknown_account_are_indistinguishable(self):
        self.register()
        wrong = self.login(password="incorrect")
        missing = self.login(email=f"missing-{uuid.uuid4().hex}@example.com")
        self.assert_error(wrong, 401, "INVALID_CREDENTIALS")
        self.assertEqual(wrong.json, missing.json)
        self.assertEqual(wrong.status_code, missing.status_code)
        self.assert_error(self.client.get("/api/auth/me"), 401, "UNAUTHORIZED")

    def test_missing_invalid_login_credentials(self):
        for payload in ({}, {"email": self.email}, {"password": self.password},
                        {"email": [], "password": {}},
                        {"email": "bad", "password": "x"},
                        {"email": self.email, "password": ""}):
            with self.subTest(fields=list(payload)):
                self.assert_error(self.client.post("/api/auth/login", json=payload),
                                  400, "VALIDATION_ERROR")

    def test_malformed_and_non_json_requests(self):
        for path in ("/api/auth/register", "/api/auth/login"):
            for body, content_type in (("{", "application/json"), ("null", "application/json"),
                                       ("[]", "application/json"), ('"text"', "application/json"),
                                       ("email=example", "application/x-www-form-urlencoded"),
                                       ("{}", "text/plain"), ("", "application/json")):
                with self.subTest(path=path, body=body):
                    self.assert_error(self.client.post(path, data=body, content_type=content_type),
                                      400, "VALIDATION_ERROR")

    def test_failed_login_clears_previous_session(self):
        self.register()
        self.login()
        self.assert_error(self.login(password="wrong"), 401, "INVALID_CREDENTIALS")
        self.assert_error(self.client.get("/api/auth/me"), 401, "UNAUTHORIZED")

    def test_logout_is_idempotent_and_removes_access(self):
        self.register()
        self.login()
        for _ in range(2):
            response = self.client.post("/api/auth/logout")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, {"success": True, "data": None, "message": None})
            self.assert_error(self.client.get("/api/auth/me"), 401, "UNAUTHORIZED")
        with self.client.session_transaction() as session:
            self.assertEqual(dict(session), {})

    def test_protection_without_session_and_reusable_decorator(self):
        for path in ("/api/auth/me", "/test-private"):
            self.assert_error(self.client.get(path), 401, "UNAUTHORIZED")

    def test_protection_with_valid_session(self):
        self.register()
        self.login()
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json["data"]), {"id", "full_name", "email", "created_at"})
        datetime.fromisoformat(response.json["data"]["created_at"])
        self.assertEqual(self.client.get("/test-private").status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_inactive_login_only_disclosed_after_correct_password(self):
        self.register()
        with self.app.app_context():
            db.session.execute(db.update(User).where(User.email == self.email).values(is_active=0))
            db.session.commit()
        self.assert_error(self.login(password="wrong"), 401, "INVALID_CREDENTIALS")
        self.assert_error(self.login(), 403, "ACCOUNT_DISABLED")
        self.assert_error(self.client.get("/api/auth/me"), 401, "UNAUTHORIZED")

    def test_user_disabled_after_login_loses_access(self):
        self.register()
        self.login()
        with self.app.app_context():
            db.session.execute(db.update(User).where(User.email == self.email).values(is_active=0))
            db.session.commit()
        self.assert_error(self.client.get("/api/auth/me"), 401, "UNAUTHORIZED")
        with self.client.session_transaction() as session:
            self.assertNotIn("user_id", session)

    def test_deleted_user_session_is_rejected(self):
        self.register()
        self.login()
        with self.app.app_context():
            db.session.execute(db.delete(User).where(User.email == self.email))
            db.session.commit()
        self.assert_error(self.client.get("/api/auth/me"), 401, "UNAUTHORIZED")

    def test_invalid_session_ids_do_not_reach_database(self):
        for value in (None, True, "1", [], {}, -1, 0, 2**64):
            with self.subTest(value=value):
                with self.client.session_transaction() as session:
                    session["user_id"] = value
                with patch.object(db.session, "get") as get:
                    self.assert_error(self.client.get("/api/auth/me"), 401, "UNAUTHORIZED")
                    get.assert_not_called()

    def test_tampered_session_cookie_is_rejected(self):
        self.register()
        self.login()
        cookie = self.client.get_cookie("session")
        self.client.set_cookie("session", cookie.value + "tampered")
        self.assert_error(self.client.get("/api/auth/me"), 401, "UNAUTHORIZED")

    def test_expired_session_cookie_is_rejected(self):
        self.register()
        self.login()
        with patch("itsdangerous.timed.time.time", return_value=10**10):
            self.assert_error(self.client.get("/api/auth/me"), 401, "UNAUTHORIZED")

    def test_cookie_security_flags(self):
        self.register()
        self.app.config["SESSION_COOKIE_SECURE"] = True
        cookie = self.login().headers["Set-Cookie"]
        for flag in ("HttpOnly", "SameSite=Lax", "Secure"):
            self.assertIn(flag, cookie)

    def test_database_failure_is_safe_and_registration_rolls_back(self):
        sensitive = "password=private-secret SELECT users mysql://internal-host"
        error = OperationalError("INSERT secret", {}, Exception(sensitive))
        with patch.object(db.session, "commit", side_effect=error), \
                self.assertLogs(self.app.logger, level="ERROR") as logs:
            response = self.register()
        self.assert_error(response, 500, "DB_ERROR")
        self.assertNotIn(sensitive, response.get_data(as_text=True) + " ".join(logs.output))
        with self.app.app_context():
            self.assertIsNone(db.session.scalar(db.select(User).where(User.email == self.email)))
        self.assertEqual(self.register().status_code, 201)

    def test_database_read_failure_is_safe(self):
        error = OperationalError("secret SQL", {}, Exception("private-password"))
        with patch.object(db.session, "scalar", side_effect=error), \
                self.assertLogs(self.app.logger, level="ERROR") as logs:
            response = self.login()
        self.assert_error(response, 500, "DB_ERROR")
        self.assertNotIn("private-password", response.get_data(as_text=True) + " ".join(logs.output))

    def test_hashing_failure_is_safe_and_does_not_create_user(self):
        sensitive = "private-secret " + self.password
        with patch.object(auth_service, "hash_password", side_effect=RuntimeError(sensitive)), \
                self.assertLogs(self.app.logger, level="ERROR") as logs:
            response = self.register()
        self.assert_error(response, 500, "INTERNAL_ERROR")
        self.assertNotIn(sensitive, response.get_data(as_text=True) + " ".join(logs.output))
        self.assertEqual(self.register().status_code, 201)

    def test_hash_helpers_use_unique_salts_and_reject_invalid_hashes(self):
        first = auth_service.hash_password(self.password)
        second = auth_service.hash_password(self.password)
        self.assertNotEqual(first, second)
        self.assertTrue(auth_service.verify_password(first, self.password))
        self.assertFalse(auth_service.verify_password(first, "wrong"))
        for invalid in ("plaintext-password", "unsupported$salt$hash", None):
            self.assertFalse(auth_service.verify_password(invalid, self.password))


if __name__ == "__main__":
    unittest.main()
