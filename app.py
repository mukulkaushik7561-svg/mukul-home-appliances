import os
import re
from urllib.parse import urlencode

from flask import Flask, abort, jsonify, redirect, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

PHONE_RE = re.compile(r"^\+?[0-9][0-9 ()-]{6,18}[0-9]$")
SERVICES = {"RO Installation", "RO Service", "AMC / Maintenance", "Support / General Enquiry", "Bio+ Bottle Enquiry"}


def create_app(test_config=None):
    app = Flask(__name__)
    environment = os.environ.get("MUKUL_ENV", "development").lower()
    secret_key = os.environ.get("MUKUL_SECRET_KEY")
    if not secret_key:
        if environment == "production" and not test_config:
            raise RuntimeError("MUKUL_SECRET_KEY must be set in production.")
        secret_key = "development-only-change-me"

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        MAX_CONTENT_LENGTH=16 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("MUKUL_HTTPS", "0") == "1",
        WTF_CSRF_TIME_LIMIT=3600,
    )
    if test_config:
        app.config.update(test_config)

    if os.environ.get("MUKUL_BEHIND_PROXY", "0") == "1":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    CSRFProtect(app)
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["300 per day", "60 per hour"],
        storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
    )
    app.limiter = limiter
    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; "
            "object-src 'none'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
            "connect-src 'self'; font-src 'self'; upgrade-insecure-requests"
        )
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if request.path in {"/", "/enquiry"}:
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    @limiter.limit("30 per minute")
    def home():
        return render_template("index.html")

    @app.get("/health")
    @limiter.limit("10 per minute")
    def health():
        return jsonify(status="ok")

    @app.post("/enquiry")
    @limiter.limit("5 per minute")
    def enquiry():
        if request.form.get("website", "").strip():
            abort(400)

        name = clean_text("name", 80)
        phone = clean_text("phone", 20)
        service = clean_text("service", 80)
        message = clean_text("message", 1000)

        if not 2 <= len(name) <= 80 or any(char in name for char in "<>\r\n"):
            return validation_error("Please enter a valid name.")
        if not PHONE_RE.fullmatch(phone):
            return validation_error("Please enter a valid phone number.")
        if service not in SERVICES:
            return validation_error("Please choose a valid service.")
        if not 10 <= len(message) <= 1000 or any(char in message for char in "<>\x00"):
            return validation_error("Please add a short message (10–1000 characters).")

        whatsapp_message = "\n".join((
            "Hello Mukul Home Appliances,",
            "",
            "I would like to make a service enquiry.",
            f"Name: {name}",
            f"Phone: {phone}",
            f"Service: {service}",
            f"Message: {message}",
            "",
            "Please contact me regarding this enquiry.",
        ))
        whatsapp_url = f"https://wa.me/919466667561?{urlencode({'text': whatsapp_message})}"
        return redirect(whatsapp_url, code=303)

    @app.errorhandler(400)
    def bad_request(_error):
        return jsonify(error="Invalid request. Please check the form and try again."), 400

    @app.errorhandler(403)
    def forbidden(_error):
        return jsonify(error="Your session expired. Refresh the page and try again."), 403

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(error="The submitted form is too large."), 413

    @app.errorhandler(429)
    def rate_limited(_error):
        return jsonify(error="Too many requests. Please wait before trying again."), 429

    @app.errorhandler(500)
    def server_error(_error):
        return jsonify(error="Something went wrong. Please call us instead."), 500

    return app


def clean_text(field, max_length):
    return " ".join(request.form.get(field, "")[: max_length + 1].strip().split())


def validation_error(message):
    return jsonify(error=message), 400


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
