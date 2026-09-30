from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

from app.utils.datetime_utils import serialize_datetime


class DatetimeTests(unittest.TestCase):
    def test_naive_database_utc_has_explicit_offset(self):
        self.assertEqual(serialize_datetime(datetime(2026, 9, 30, 1, 2, 3)),
                         "2026-09-30T01:02:03+00:00")

    def test_offset_conversion_preserves_instant_across_day_boundary(self):
        value = datetime(2026, 9, 30, 1, 2, 3, 456789,
                         tzinfo=timezone(timedelta(hours=7)))
        encoded = serialize_datetime(value)
        self.assertEqual(encoded, "2026-09-29T18:02:03.456789+00:00")
        self.assertEqual(datetime.fromisoformat(encoded).timestamp(), value.timestamp())

    def test_utc_and_negative_offset(self):
        for offset in (0, -5):
            value = datetime(2026, 9, 30, 23, tzinfo=timezone(timedelta(hours=offset)))
            decoded = datetime.fromisoformat(serialize_datetime(value))
            self.assertEqual(decoded.utcoffset(), timedelta(0))
            self.assertEqual(decoded, value)

    def test_business_timezone_default_and_environment_override(self):
        path = Path(__file__).resolve().parents[1] / "config.py"
        for env, expected in (({}, "Asia/Ho_Chi_Minh"), ({"APP_TIMEZONE": "UTC"}, "UTC")):
            with patch.dict(os.environ, env, clear=True), patch("dotenv.load_dotenv"):
                config = runpy.run_path(str(path))["Config"]
            self.assertEqual(config.APP_TIMEZONE, expected)


if __name__ == "__main__":
    unittest.main()
