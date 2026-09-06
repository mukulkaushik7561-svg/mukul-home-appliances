# Mukul Home Appliances — Service Website

A responsive Flask website for Mukul Home Appliances in Mahendergarh. It is an enquiry-led local service site, not an online store.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Production configuration

Set secrets and deployment settings in the hosting environment—never in HTML, CSS, JavaScript or source control.

```powershell
$env:MUKUL_ENV = "production"
$env:MUKUL_SECRET_KEY = "a-long-random-secret-created-for-this-deployment"
$env:MUKUL_HTTPS = "1"
$env:MUKUL_BEHIND_PROXY = "1" # only behind one trusted reverse proxy
$env:RATELIMIT_STORAGE_URI = "redis://..." # recommended for multiple workers
waitress-serve --listen=127.0.0.1:8000 app:app
```

Terminate TLS at a trusted reverse proxy, redirect HTTP to HTTPS, restrict and back up the database, and use a managed database plus shared rate-limit store for multiple instances.

## Security included

- CSRF-protected enquiry submissions
- strict server-side allow-list validation
- parameterized database queries
- per-IP request and submission rate limits
- honeypot spam trap and 16 KB request limit
- HTTP-only, SameSite cookies with production HTTPS support
- CSP, anti-framing, MIME-sniffing, referrer and permissions headers
- HSTS when served over HTTPS
- trusted-proxy handling only when explicitly enabled
- production startup blocked when the environment secret is missing
- generic server errors and no production debug mode
- minimal enquiry data collection

No website can be guaranteed impossible to hack. Keep dependencies and the host patched, monitor logs, rotate secrets, and review stored enquiries regularly.

## Business assets

The supplied RO visuals and Bio+ poster are in `static/images/`. RO images are identified as representative because the website does not sell exact models online. The bottle section intentionally avoids health-outcome claims.
