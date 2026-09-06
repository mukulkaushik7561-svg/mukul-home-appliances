import re
import unittest
from urllib.parse import parse_qs, urlparse

from app import create_app


class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "RATELIMIT_ENABLED": False,
        })
        self.client = self.app.test_client()

    def csrf_token(self):
        html = self.client.get("/").get_data(as_text=True)
        return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)

    def valid_form(self):
        return {
            "csrf_token": self.csrf_token(),
            "name": "Test Customer & Family",
            "phone": "+91 9876543210",
            "service": "RO Service",
            "message": "Filter change & low water flow?",
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

    def test_valid_enquiry_redirects_to_encoded_whatsapp_message(self):
        response = self.client.post("/enquiry", data=self.valid_form())
        self.assertEqual(response.status_code, 303)
        destination = urlparse(response.headers["Location"])
        self.assertEqual(destination.scheme, "https")
        self.assertEqual(destination.netloc, "wa.me")
        self.assertEqual(destination.path, "/919466667561")
        message = parse_qs(destination.query)["text"][0]
        self.assertIn("Name: Test Customer & Family", message)
        self.assertIn("Phone: +91 9876543210", message)
        self.assertIn("Service: RO Service", message)
        self.assertIn("Message: Filter change & low water flow?", message)

    def test_service_allowlist_and_honeypot(self):
        invalid = self.valid_form()
        invalid["service"] = "Checkout"
        self.assertEqual(self.client.post("/enquiry", data=invalid).status_code, 400)
        spam = self.valid_form()
        spam["website"] = "https://spam.example"
        self.assertEqual(self.client.post("/enquiry", data=spam).status_code, 400)


if __name__ == "__main__":
    unittest.main()
