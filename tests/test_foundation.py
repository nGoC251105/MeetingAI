"""Foundation regression checks; no live database or schema writes required."""

import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

from app import create_app
from app.extensions import db, migrate
from config import Config


ROOT = Path(__file__).resolve().parents[1]


class ConfigurationTests(unittest.TestCase):
    def read_config(self, environment):
        # Isolate configuration tests from the developer's real .env and secrets.
        with patch.dict(os.environ, environment, clear=True), patch("dotenv.load_dotenv"):
            return runpy.run_path(str(ROOT / "config.py"))["Config"]

    def test_debug_defaults_off(self):
        self.assertFalse(self.read_config({}).DEBUG)

    def test_debug_environment_values(self):
        for value in ("1", "true", "True", " YES ", "on"):
            with self.subTest(value=value):
                self.assertTrue(self.read_config({"FLASK_DEBUG": value}).DEBUG)
        for value in ("0", "false", "False", "no", "off", "", "invalid"):
            with self.subTest(value=value):
                self.assertFalse(self.read_config({"FLASK_DEBUG": value}).DEBUG)

    def test_no_secret_fallback(self):
        self.assertIsNone(self.read_config({}).SECRET_KEY)

    def test_explicit_secret_is_preserved(self):
        self.assertEqual(self.read_config({"SECRET_KEY": "test-only-value"}).SECRET_KEY,
                         "test-only-value")

    def test_missing_or_blank_secret_rejects_startup(self):
        for value in (None, "", "   "):
            with self.subTest(value=value), patch.object(Config, "SECRET_KEY", value):
                with self.assertRaisesRegex(RuntimeError, "SECRET_KEY must be configured"):
                    create_app()

    def test_password_is_url_encoded(self):
        config = self.read_config({"DB_PASSWORD": "a@b:/?# %"})
        self.assertIn("a%40b%3A%2F%3F%23+%25@", config.SQLALCHEMY_DATABASE_URI)
        self.assertTrue(config.SQLALCHEMY_DATABASE_URI.endswith("?charset=utf8mb4"))

    def test_entrypoint_respects_debug_configuration(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled), patch.object(Config, "DEBUG", enabled), \
                    patch.object(Config, "SECRET_KEY", "test-only-value"), \
                    patch("flask.Flask.run") as run:
                runpy.run_path(str(ROOT / "run.py"), run_name="__main__")
                run.assert_called_once_with(host="127.0.0.1", port=5000, debug=enabled)


class FoundationTests(unittest.TestCase):
    def setUp(self):
        with patch.object(Config, "SECRET_KEY", "test-only-value"):
            self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "success")

    def test_extensions_share_database_instance(self):
        self.assertIs(self.app.extensions["sqlalchemy"], db)
        self.assertIs(self.app.extensions["migrate"].db, db)
        self.assertIs(self.app.extensions["migrate"].migrate, migrate)
        self.assertEqual(list(db.metadata.tables), [])

    def test_health_executes_select_one(self):
        with patch.object(db.session, "execute") as execute:
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["database"], "connected")
        execute.assert_called_once()
        self.assertEqual(str(execute.call_args.args[0]), "SELECT 1")

    def test_health_failure_does_not_expose_internal_details(self):
        sensitive = "password=audit-secret; mysql://private-host; C:/private/file; SELECT secret"
        for debug in (False, True):
            with self.subTest(debug=debug):
                self.app.config["DEBUG"] = debug
                with patch.object(db.session, "execute", side_effect=RuntimeError(sensitive)), \
                        self.assertLogs(self.app.logger, level="ERROR") as logs:
                    response = self.client.get("/health")
                self.assertEqual(response.status_code, 500)
                self.assertEqual(response.json, {
                    "status": "error", "database": "disconnected",
                    "error": "Database connection unavailable."
                })
                self.assertNotIn(sensitive, response.get_data(as_text=True))
                self.assertNotIn(sensitive, " ".join(logs.output))
                self.assertIn("RuntimeError", " ".join(logs.output))


if __name__ == "__main__":
    unittest.main()
