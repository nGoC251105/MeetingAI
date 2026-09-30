"""Real MySQL authentication integration tests; only UUID-owned users are removed.

Run: .venv/Scripts/python.exe -m unittest discover -s tests -p test_auth.py -v
The existing database must already be migrated. No schema is created or dropped.
"""

from datetime import datetime, timedelta
import secrets
import unittest
from unittest.mock import patch
import uuid

from sqlalchemy import text
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
        self.extra_emails = set()
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
            db.session.execute(db.delete(User).where(
                User.email.in_({self.email} | self.extra_emails)
            ))
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
        timestamp = datetime.fromisoformat(response.json["data"]["created_at"])
        self.assertEqual(timestamp.utcoffset(), timedelta(0))
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

    def authenticated_user(self):
        response = self.register()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.login().status_code, 200)
        return response.json["data"]["id"]

    def update_profile(self, **overrides):
        return self.client.put("/api/profile", json={
            "full_name": "Updated Name", "email": self.email,
        } | overrides)

    def change_password(self, **overrides):
        return self.client.post("/api/profile/change-password", json={
            "current_password": self.password,
            "new_password": "  New secure password 123  ",
            "confirm_password": "  New secure password 123  ",
        } | overrides)

    def test_profile_methods_and_paths_match_a005_a006(self):
        routes = {r.rule: r.methods - {"HEAD", "OPTIONS"}
                  for r in self.app.url_map.iter_rules()
                  if r.endpoint.startswith("profile.")}
        self.assertEqual(routes, {
            "/api/profile": {"PUT"}, "/api/profile/change-password": {"POST"},
        })

    def test_profile_update_normalizes_and_persists_only_own_profile(self):
        user_id = self.authenticated_user()
        new_email = f"profile-test-{uuid.uuid4().hex}@example.com"
        self.extra_emails.add(new_email)
        with self.app.app_context():
            before = db.session.get(User, user_id)
            original = (before.password_hash, before.created_at, before.is_active)
        response = self.update_profile(full_name="  New Name  ", email=f" {new_email.upper()} ")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"success": True, "message": None,
                         "data": {"id": user_id, "full_name": "New Name", "email": new_email}})
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(self.client.get("/api/auth/me").json["data"]["email"], new_email)
        with self.app.app_context():
            after = db.session.get(User, user_id)
            self.assertEqual((after.password_hash, after.created_at, after.is_active), original)
        self.assertEqual(self.login(email=new_email).status_code, 200)
        self.assert_error(self.login(), 401, "INVALID_CREDENTIALS")

    def test_profile_update_unchanged_email_is_allowed(self):
        self.authenticated_user()
        self.assertEqual(self.update_profile(email=f" {self.email.upper()} ").status_code, 200)

    def test_profile_rejects_invalid_missing_and_protected_fields(self):
        user_id = self.authenticated_user()
        cases = [{}, {"full_name": "Only name"}, {"email": self.email}]
        base = {"full_name": "New Name", "email": self.email}
        cases += [base | fields for fields in (
            {"full_name": "  "}, {"full_name": None}, {"full_name": []},
            {"full_name": "x" * 121}, {"email": "bad"}, {"email": None},
            {"email": []}, {"email": "a..b@example.com"},
            {"email": "x" * 180 + "@example.com"},
        )]
        cases += [base | {field: "forbidden"} for field in (
            "id", "user_id", "password_hash", "created_at", "updated_at", "is_active",
        )]
        for payload in cases:
            with self.subTest(fields=list(payload)):
                self.assert_error(self.client.put("/api/profile", json=payload),
                                  400, "VALIDATION_ERROR")
        with self.app.app_context():
            user = db.session.get(User, user_id)
            self.assertEqual(user.full_name, "Nguyễn Minh")
            self.assertEqual(user.email, self.email)
            self.assertEqual(user.is_active, 1)

    def test_duplicate_profile_email_and_constraint_race_preserve_users(self):
        user_id = self.authenticated_user()
        other_email = f"other-{uuid.uuid4().hex}@example.com"
        self.extra_emails.add(other_email)
        other_id = self.register(email=other_email, full_name="Other User").json["data"]["id"]
        self.assert_error(self.update_profile(email=f" {other_email.upper()} "), 409, "EMAIL_EXISTS")
        scalar = db.session.scalar

        def race(statement, *args, **kwargs):
            if statement.column_descriptions[0]["name"] == "id":
                return None  # Concurrent insert wins after the precheck.
            return scalar(statement, *args, **kwargs)

        with patch.object(db.session, "scalar", side_effect=race):
            self.assert_error(self.update_profile(email=other_email), 409, "EMAIL_EXISTS")
        with self.app.app_context():
            self.assertEqual(db.session.get(User, user_id).email, self.email)
            self.assertEqual(db.session.get(User, user_id).full_name, "Nguyễn Minh")
            self.assertEqual(db.session.get(User, other_id).full_name, "Other User")

    def test_account_mutations_require_active_session(self):
        self.assert_error(self.update_profile(), 401, "UNAUTHORIZED")
        self.assert_error(self.change_password(), 401, "UNAUTHORIZED")
        user_id = self.authenticated_user()
        with self.app.app_context():
            db.session.execute(db.update(User).where(User.id == user_id).values(is_active=0))
            db.session.commit()
        for operation in (self.update_profile, self.change_password):
            with self.client.session_transaction() as session:
                session["user_id"] = user_id
            self.assert_error(operation(), 401, "UNAUTHORIZED")
            with self.client.session_transaction() as session:
                self.assertNotIn("user_id", session)

    def test_profile_mutations_reject_malformed_json(self):
        self.authenticated_user()
        for method, path in (("PUT", "/api/profile"), ("POST", "/api/profile/change-password")):
            for body, content_type in (("{", "application/json"), ("[]", "application/json"),
                                       ("null", "application/json"), ("{}", "text/plain")):
                with self.subTest(path=path, body=body):
                    self.assert_error(self.client.open(path, method=method, data=body,
                                      content_type=content_type), 400, "VALIDATION_ERROR")

    def test_password_change_hashes_and_replaces_login_password(self):
        user_id = self.authenticated_user()
        new_password = "  New secure password 123  "
        with self.app.app_context():
            old_hash = db.session.get(User, user_id).password_hash
        response = self.change_password()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"success": True, "data": None, "message": None})
        with self.app.app_context():
            stored = db.session.get(User, user_id).password_hash
            self.assertNotEqual(stored, old_hash)
            self.assertNotEqual(stored, new_password)
            self.assertTrue(check_password_hash(stored, new_password))
            self.assertFalse(check_password_hash(stored, self.password))
        self.assert_error(self.login(), 401, "INVALID_CREDENTIALS")
        self.assertEqual(self.login(password=new_password).status_code, 200)

    def test_wrong_current_password_has_canonical_safe_error(self):
        self.authenticated_user()
        response = self.change_password(current_password="incorrect-current-secret")
        self.assert_error(response, 400, "INVALID_PASSWORD")
        self.assertEqual(response.json["error"]["details"], {})
        self.assertEqual(self.login().status_code, 200)

    def test_password_change_validation_and_minimum_length(self):
        self.authenticated_user()
        base = {"current_password": self.password, "new_password": "abcdefgh",
                "confirm_password": "abcdefgh"}
        cases = [{}, *[{k: v for k, v in base.items() if k != missing} for missing in base]]
        cases += [base | fields for fields in (
            {"current_password": ""}, {"current_password": []},
            {"new_password": None}, {"new_password": 12345678},
            {"new_password": "short", "confirm_password": "short"},
            {"confirm_password": None}, {"confirm_password": "mismatch"},
            {"password_hash": "forbidden"}, {"id": 1},
        )]
        for payload in cases:
            with self.subTest(fields=list(payload)):
                self.assert_error(self.client.post("/api/profile/change-password", json=payload),
                                  400, "VALIDATION_ERROR")
        self.assertEqual(self.login().status_code, 200)
        self.assertEqual(self.client.post("/api/profile/change-password", json=base).status_code, 200)
        self.assertEqual(self.login(password="abcdefgh").status_code, 200)

    def test_password_change_rechecks_latest_hash_under_lock(self):
        user_id = self.authenticated_user()
        concurrent_password = "Concurrent replacement password"
        with self.app.app_context():
            stale = db.session.get(User, user_id)
            with db.engine.begin() as connection:
                connection.execute(db.update(User).where(User.id == user_id).values(
                    password_hash=auth_service.hash_password(concurrent_password)))
            self.assertTrue(check_password_hash(stale.password_hash, self.password))
            with self.assertRaises(auth_service.AuthError) as caught:
                auth_service.change_password(user_id, {
                    "current_password": self.password, "new_password": "abcdefgh",
                    "confirm_password": "abcdefgh",
                })
            self.assertEqual(caught.exception.code, "INVALID_PASSWORD")
        self.assertEqual(self.login(password=concurrent_password).status_code, 200)

    def test_account_responses_and_logs_do_not_leak_secrets(self):
        user_id = self.authenticated_user()
        with patch.object(self.app.logger, "handle") as log:
            responses = [self.update_profile(), self.change_password(current_password="wrong-secret"),
                         self.change_password(), self.client.get("/api/auth/me")]
        with self.app.app_context():
            stored = db.session.get(User, user_id).password_hash
        output = str([r.json for r in responses]) + " ".join(c.args[0].getMessage() for c in log.call_args_list)
        for sensitive in (self.password, "  New secure password 123  ", "wrong-secret", stored,
                          "password_hash"):
            self.assertNotIn(sensitive, output)

    def test_account_commit_failures_rollback_without_leaking(self):
        user_id = self.authenticated_user()
        with self.app.app_context():
            original_hash = db.session.get(User, user_id).password_hash
        for operation in (self.update_profile, self.change_password):
            error = OperationalError("private SQL", {}, Exception(self.password + original_hash))
            with patch.object(db.session, "commit", side_effect=error), \
                    self.assertLogs(self.app.logger, level="ERROR") as logs:
                response = operation()
            self.assert_error(response, 500, "DB_ERROR")
            for secret in (self.password, original_hash, "private SQL"):
                self.assertNotIn(secret, str(response.json) + " ".join(logs.output))
            with self.app.app_context():
                user = db.session.get(User, user_id)
                self.assertEqual(user.password_hash, original_hash)
                self.assertEqual(user.full_name, "Nguyễn Minh")
        self.assertEqual(self.login().status_code, 200)

    def test_account_timestamp_matches_utc_database_instant(self):
        user_id = self.authenticated_user()
        value = datetime.fromisoformat(self.client.get("/api/auth/me").json["data"]["created_at"])
        self.assertEqual(value.utcoffset(), timedelta(0))
        with self.app.app_context():
            self.assertEqual(db.session.execute(text("SELECT @@session.time_zone")).scalar_one(), "+00:00")
            epoch = db.session.execute(text("SELECT UNIX_TIMESTAMP(created_at) FROM users WHERE id=:id"),
                                       {"id": user_id}).scalar_one()
            self.assertEqual(value.timestamp(), float(epoch))
            with db.engine.connect() as second_connection:
                self.assertEqual(second_connection.execute(text("SELECT @@session.time_zone")).scalar_one(),
                                 "+00:00")


if __name__ == "__main__":
    unittest.main()
