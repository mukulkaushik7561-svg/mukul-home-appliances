import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import create_app


class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "test.db"
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": self.database,
            "RATELIMIT_ENABLED": False,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def csrf_token(self):
        html = self.client.get("/").get_data(as_text=True)
        return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)

    def valid_form(self):
        return {
            "csrf_token": self.csrf_token(),
            "name": "Test Customer",
            "phone": "+91 9876543210",
            "service": "RO Service",
            "message": "My purifier needs a routine service.",
            "website": "",
        }

    def test_home_and_security_headers(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Content-Security-Policy", response.headers)
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_enquiry_requires_csrf(self):
        response = self.client.post("/enquiry", data={})
        self.assertEqual(response.status_code, 400)

    def test_valid_enquiry_is_stored(self):
        response = self.client.post("/enquiry", data=self.valid_form())
        self.assertEqual(response.status_code, 201)
        db = sqlite3.connect(self.database)
        try:
            row = db.execute("SELECT name, service FROM enquiries").fetchone()
        finally:
            db.close()
        self.assertEqual(row, ("Test Customer", "RO Service"))

    def test_service_allowlist_and_honeypot(self):
        invalid = self.valid_form()
        invalid["service"] = "Checkout"
        self.assertEqual(self.client.post("/enquiry", data=invalid).status_code, 400)
        spam = self.valid_form()
        spam["website"] = "https://spam.example"
        self.assertEqual(self.client.post("/enquiry", data=spam).status_code, 400)


if __name__ == "__main__":
    unittest.main()
