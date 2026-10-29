# Deepak URL Shortener

This project is a local FastAPI-based URL shortener prototype built as part of an AI-assisted software engineering assignment. It supports creating short links, custom aliases, redirects, link management, and click analytics.

## Project overview

The application provides a browser UI and API for:

- creating short links from long URLs
- optionally assigning a custom alias
- redirecting visitors to the original destination
- updating a destination URL for an existing short code
- deactivating a short link without deleting its historical record
- retrieving click analytics for a short code
- managing admin-only operations using a configured API key

## Features

- FastAPI web application and API
- HTML, CSS, and JavaScript front end
- SQLite persistence
- custom alias support with alias uniqueness enforcement
- HTTP/HTTPS destination validation
- redirect tracking with click counts
- deactivation without deleting link history
- admin-authenticated management endpoints
- environment-based public URL configuration

## Technology stack

- Python
- FastAPI
- SQLite
- Jinja2 templates
- static HTML/CSS/JavaScript
- pytest

## Setup and run

### 1. Create a virtual environment

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app locally

From the project root:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open the app here:

- http://127.0.0.1:8000/

Open the API docs here:

- http://127.0.0.1:8000/docs

## Configuration variables

The current application uses the following environment variables:

- `PUBLIC_BASE_URL`: sets the public base domain used for generated short links
- `ADMIN_API_KEY`: required for admin API access

Example PowerShell configuration:

```powershell
$env:PUBLIC_BASE_URL = "https://deepak.example.com"
$env:ADMIN_API_KEY = "your-admin-key"
```

If `PUBLIC_BASE_URL` is not set, the app falls back to the local request base URL or localhost.

> A custom public domain only becomes reachable after DNS and HTTPS are configured externally. The environment variable alone does not create a public site.

## API documentation

The app exposes Swagger UI at:

- http://127.0.0.1:8000/docs

The actual implemented routes are documented in the engineering summary file:

- [ENGINEERING_SUMMARY.md](ENGINEERING_SUMMARY.md)

## Testing

Run the project tests from the project root:

```bash
pytest -q
```

Latest actual result verified from the repository:

- 15 passed
- 0 failed

## Deployment prerequisites

This project is currently a local prototype and is not deployed to a public hosting platform.

The application is ready for deployment preparation, but the following remain external to the repo:

- DNS configuration for the public domain
- HTTPS certificate setup
- hosting runtime configuration
- production database selection
- secret management at runtime

For Render deployment later, the app should run with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The repository also includes a local script entry point for development compatibility:

```bash
python -m app.main
```

When the app is started this way, it reads `PORT` from the environment and falls back to `8000` locally.

## Required environment variables

The current application uses the following environment variables:

- `PUBLIC_BASE_URL`: sets the public base domain used for generated short links
- `ADMIN_API_KEY`: required for admin API access
- `PORT`: used by the hosting environment to choose the server port

Example PowerShell configuration:

```powershell
$env:PUBLIC_BASE_URL = "https://deepak.example.com"
$env:ADMIN_API_KEY = "your-admin-key"
$env:PORT = "8000"
```

A custom public domain only becomes reachable after DNS and HTTPS are configured externally. The environment variable alone does not create a public site.

## Deployment database considerations

The current database uses SQLite at:

- `data/shortener.db`

This is suitable for a prototype and local testing, but it is not a production-grade persistence layer for multi-instance hosting. On Render, the filesystem is not guaranteed to be persistent across restarts and redeployments. A persistent disk can be enough for a prototype if the service remains single-instance and file durability is acceptable, but managed PostgreSQL is the safer long-term choice if the app is intended for public use.

For the interview prototype, the simplest safe recommendation is:

- keep SQLite for local evaluation and initial deployment testing
- avoid assuming the SQLite file persists across all platform lifecycle events
- treat the current setup as a prototype, not a production database
- plan a managed PostgreSQL migration before upgrading to production public traffic

## Deployment steps later

1. Set the required environment variables in the hosting platform.
2. Configure the public domain and HTTPS in the hosting provider.
3. Ensure the start command uses `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. Verify that generated links use `PUBLIC_BASE_URL` and not a hard-coded hostname.
5. Validate redirect routes and admin authentication in the deployed environment.
6. Keep local testing and deployment testing separate.

> Local testing is for running the app on the developer machine. Deployment testing should occur only after the host is configured and the public URL is set correctly.

## Alias lifecycle policy

The implemented alias policy is:

- aliases are globally unique
- a deactivated alias remains reserved
- deactivation prevents redirects while preserving the link record and analytics

## Known limitations

- SQLite is used for lightweight local persistence and is not a production-scale database.
- No rate limiting or abuse protection is included.
- No public hosting configuration is included in the repo.
- No `.gitignore` file is present in the repository root, so local runtime files may require manual exclusion if the project is versioned.

## Link to engineering summary

See [ENGINEERING_SUMMARY.md](ENGINEERING_SUMMARY.md) for the full architecture overview, API contracts, data model, task decomposition, AI-assisted development notes, validation details, security review, and deployment readiness assessment.
