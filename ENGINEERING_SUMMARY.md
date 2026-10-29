# Engineering Summary

## 1. Executive Summary

This project is a lightweight URL shortener built with Python and FastAPI. It allows a user to submit a long destination URL, optionally assign a custom alias, create a short link, and then redirect visitors to the original destination. The application also stores persistent link metadata and records analytics for redirect activity.

The key problem being solved is the conversion of a long public URL into a compact, memorable route that can be shared and tracked. The project is implemented as a local, single-service application with a browser frontend, a FastAPI API, a SQLite persistence layer, and simple click analytics.

### Technology stack

The repository currently contains the following actual components:

- Python 3.15+ environment in the project virtual environment
- FastAPI for the web application and API
- SQLite for persistence
- Jinja2 templates for the HTML frontend
- Static HTML, CSS, and JavaScript for the landing page and user interactions
- Pytest for automated validation

### Current implementation status

The current codebase is a functioning prototype and meets the core assignment requirements for local development and validation. The implemented features include:

- URL creation with valid http/https destinations
- optional custom aliases
- redirect handling for active short codes
- admin-managed link listing, details, updates, and deactivation
- click analytics tracking
- admin API authentication via `X-ADMIN-KEY` header and `ADMIN_API_KEY`
- environment-driven base URL generation via `PUBLIC_BASE_URL`
- automated test coverage for core user and admin behaviors

The project is not described as production-deployed. It remains a local application suitable for evaluation, testing, and deployment-prep work.

---

## 2. Requirements and Assumptions

### Functional requirements implemented

- Enter a destination URL and a custom short alias.
- Validate both mandatory inputs before creating a link.
- Generate a working short URL using the app base URL and short code.
- Redirect active short codes to the destination URL.
- Persist links in SQLite.
- Reject duplicate aliases.
- Update a destination URL for an existing short code.
- Disable a link without deleting its database record.
- Track redirect counts and expose analytics.
- Support admin access to list, inspect, modify, and disable links.

### Non-functional requirements present in the project

- Simple local deployment model
- Environment-based URL configuration
- Minimal validation and error handling for user inputs
- Lightweight analytics tracking
- Simple browser interface with client-side validation
- Automated pytest regression coverage

### Assumptions made during implementation

- The application is a local prototype rather than a globally distributed production service.
- SQLite is acceptable for local persistence and evaluation.
- Admin APIs are intended for trusted operators, not public users.
- The application may be run locally or behind a public domain once DNS and HTTPS are configured externally.
- Short links are not user-scoped or multi-tenant; they are global aliases in a single SQLite database.

### Ambiguities and how they were resolved

- Alias lifecycle: The implementation resolves this with a global uniqueness policy. A deactivated alias remains reserved and cannot be reused for another destination.
- Redirect safety: The implementation now rejects unsupported schemes and malformed destinations before redirecting.
- Public deployment: The app supports a configurable base URL, but the actual domain and hosting configuration are external responsibilities rather than app-side functionality.

### Actual alias lifecycle policy

The implemented policy is:

- Aliases are globally unique.
- Deactivated aliases remain reserved.
- Deactivation prevents redirects while preserving the record and historical click analytics.
- The link record is not deleted on deactivation.

This behavior is enforced by the database uniqueness constraint and the `is_active` flag in the `links` table.

---

## 3. Architecture Overview

The application is composed of the following actual parts:

- Frontend: HTML, CSS, and JavaScript served from `templates/` and `static/`
- FastAPI application: route definitions and HTTP handling in `app/main.py`
- Service layer: link creation, lookup, analytics, validation, and deactivation logic in `app/service.py`
- Database layer: SQLite connection and table initialization in `app/database.py`
- Configuration layer: environment settings in `app/config.py`
- Request/response schema definitions in `app/models.py`

### Frontend responsibilities

The browser frontend allows a user to:

- paste a destination URL
- enter a custom short alias
- submit the request to the API
- see validation feedback
- copy the full short URL
- click the alias text that points to the generated short URL

The frontend uses client-side validation before sending the request and updates the generated link display after a successful response.

### FastAPI application responsibilities

The FastAPI app defines the route layer for:

- the homepage (`GET /`)
- custom alias creation (`POST /api/v1/links`)
- admin listing (`GET /api/v1/links`)
- admin detail retrieval (`GET /api/v1/links/{short_code}`)
- admin updates (`PATCH /api/v1/links/{short_code}`)
- admin deactivation (`DELETE /api/v1/links/{short_code}`)
- redirect resolution (`GET /{short_code}`)
- analytics retrieval (`GET /api/v1/links/{short_code}/analytics`)
- Swagger documentation (`/docs`)

### Service layer responsibilities

The service layer contains the core logic for:

- validating destination URLs
- creating short codes or accepting custom aliases
- normalizing URL values
- checking alias uniqueness
- recording redirect events
- incrementing click counts
- updating original URL destinations
- deactivating records without deleting them
- retrieving analytics

### Database responsibilities

SQLite stores the link data and analytics events. The current database includes:

- `links` table for link records
- `link_events` table for redirect access records

The database layer also initializes the schema on startup and adds compatibility columns for `updated_at` and `is_active` if missing.

### Request flow: create a link

1. The browser sends a POST to `/api/v1/links` with `original_url` and `custom_alias`.
2. FastAPI validates request JSON using Pydantic models.
3. The service layer validates the destination URL, checks alias uniqueness, and inserts a link record.
4. The app responds with the original URL, generated short code, and full short URL.
5. The browser updates the copy field and clickable short alias.

### Request flow: redirect a short link

1. A user requests `/SHORT_CODE`.
2. The FastAPI app calls the service-level redirect resolver.
3. The service checks whether the record exists and is active.
4. If active, it increments click count and inserts an event.
5. The app returns a 307 redirect to the destination URL.
6. If the record is missing or inactive, the app returns 404.

### Analytics recording

Click analytics are recorded in two ways:

- `click_count` field on the `links` table is incremented on every successful redirect.
- `link_events` stores a record with the short code and timestamp for each access event.

The analytics endpoint returns the latest `click_count` and record metadata while preserving the historical data even after a link is deactivated.

### Mermaid architecture diagram

```mermaid
flowchart LR
    Browser[Browser / HTML / JS] -->|POST original_url + alias| API[FastAPI app
    app/main.py]
    API --> Service[Service layer
    app/service.py]
    Service --> DB[(SQLite
    links + link_events)]
    DB --> Service
    Service -->|Redirect response| Browser
    Browser -->|GET /{short_code}| API
    API -->|307 redirect| Destination[Original destination URL]
    Browser -->|GET analytics| API
    API --> Analytics[Link analytics data]
```

---

## 4. API Contracts

The API contracts below are based on the actual route definitions and request models in the repository.

### `GET /`

- Method: `GET`
- Purpose: serves the browser UI homepage
- Response: HTML page rendered with Jinja2
- Status: `200 OK`
- No authentication required

### `GET /docs`

- Method: `GET`
- Purpose: FastAPI Swagger/OpenAPI documentation page
- Response: HTML/Swagger UI
- Status: `200 OK`
- No authentication required

### `POST /api/v1/links`

- Method: `POST`
- Purpose: create a new short link
- Body:

```json
{
  "original_url": "https://example.com/a/very/long/path",
  "custom_alias": "demo-link"
}
```

- Request model: `CreateLinkRequest`
- Validation:
  - `original_url` must be a valid `HttpUrl`
  - `custom_alias` is optional and must be 3-32 chars, using letters, numbers, hyphen, or underscore
- Response model: `LinkResponse`
- Success status: `201 Created`
- Failure status:
  - `400 Bad Request` for invalid destination or malformed request
  - `409 Conflict` for duplicate alias
  - `422 Unprocessable Entity` for invalid Pydantic input

Response example:

```json
{
  "original_url": "https://example.com/a/very/long/path",
  "short_code": "demo-link",
  "short_url": "http://127.0.0.1:8000/demo-link",
  "created_at": "2026-10-29T00:00:00+00:00",
  "click_count": 0
}
```

### `GET /api/v1/links`

- Method: `GET`
- Purpose: list links for admin management
- Query parameters:
  - `limit` (optional, integer, 1..200, default 50)
  - `offset` (optional, integer, default 0)
- Authentication: required via `X-Admin-Key` header
- Status: `200 OK`
- Failure status:
  - `401 Unauthorized` if missing header
  - `403 Forbidden` if key does not match configured `ADMIN_API_KEY`
  - `503 Service Unavailable` if no admin key is configured

Response example:

```json
{
  "items": [
    {
      "short_code": "demo-link",
      "original_url": "https://example.com/a/very/long/path",
      "short_url": "http://127.0.0.1:8000/demo-link",
      "created_at": "2026-10-29T00:00:00+00:00",
      "updated_at": "2026-10-29T00:00:00+00:00",
      "click_count": 3,
      "is_active": true
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### `GET /api/v1/links/{short_code}`

- Method: `GET`
- Purpose: retrieve link details for admin inspection
- Authentication: required via `X-Admin-Key`
- Success status: `200 OK`
- Failure status: `404 Not Found` if no link exists

### `PATCH /api/v1/links/{short_code}`

- Method: `PATCH`
- Purpose: update the destination URL
- Authentication: required via `X-Admin-Key`
- Body:

```json
{
  "original_url": "https://example.com/new-target"
}
```

- Request model: `UpdateLinkRequest`
- Success status: `200 OK`
- Failure status:
  - `400 Bad Request` for invalid or unsupported destination URL
  - `404 Not Found` if the short code does not exist
  - `401` / `403` for admin auth failures

### `DELETE /api/v1/links/{short_code}`

- Method: `DELETE`
- Purpose: deactivate a link without deleting its record
- Authentication: required via `X-Admin-Key`
- Success status: `200 OK`
- Response example:

```json
{
  "short_code": "demo-link",
  "status": "disabled",
  "message": "The link has been disabled and no longer redirects."
}
```

### `GET /{short_code}`

- Method: `GET`
- Purpose: resolve a short code and redirect to the original destination
- Response: `307 Temporary Redirect`
- Success conditions:
  - link exists
  - link is active
  - destination is valid
- Failure status:
  - `404 Not Found` for missing or deactivated short codes
  - `400 Bad Request` if a stored destination fails validation at runtime

### `GET /api/v1/links/{short_code}/analytics`

- Method: `GET`
- Purpose: return analytics for a given short code
- Authentication: not required for this endpoint in the current implementation
- Success status: `200 OK`
- Failure status: `404 Not Found` for unknown short code

Response example:

```json
{
  "short_code": "demo-link",
  "original_url": "https://example.com/a/very/long/path",
  "created_at": "2026-10-29T00:00:00+00:00",
  "updated_at": "2026-10-29T00:00:00+00:00",
  "click_count": 3,
  "is_active": true
}
```

### Authentication requirements

- Admin endpoints require the header `X-Admin-Key`.
- The value must match the runtime environment variable `ADMIN_API_KEY`.
- The public redirect route does not require authentication.

---

## 5. Data Model

### `links` table

The `links` table is created in `app/database.py` and contains the following fields:

- `id`: integer primary key
- `short_code`: unique text value used in the URL path
- `original_url`: text of the destination URL
- `created_at`: timestamp of creation
- `updated_at`: optional timestamp of the most recent update
- `click_count`: integer count of successful redirects
- `is_active`: integer flag, where `1` means active and `0` means disabled

Important characteristics:

- `short_code` is `UNIQUE` and enforces global alias uniqueness.
- `original_url` is required and stores the final destination URL.
- `click_count` is incremented when a redirect is successful.
- `is_active` is used to block redirect resolution without removing the row.

### `link_events` table

The `link_events` table stores analytics events:

- `id`: integer primary key
- `short_code`: foreign key reference to the target short code
- `accessed_at`: timestamp of redirect access

### Relationships and analytics behavior

- A link record may have many access events.
- `click_count` is a summary counter, while `link_events` records a timestamped history of redirect events.
- When a link is updated, the same short code remains reserved and the `click_count` remains preserved.
- When a link is deactivated, the row remains in the table and analytics remain available through the admin/detail and analytics API endpoints.
- Redirect resolution excludes inactive links by checking `is_active = 1`.

### Constraints and duplication policy

The current database design enforces a single global alias rule and prevents duplicate entries for the same short code. Deactivated records remain reserved; they are not automatically made available for a different URL.

---

## 6. Engineer-Led Task Decomposition

This project followed a task order that matches actual repository structure and behavior.

### 1. Requirement interpretation

The engineering task was broken into core functional concerns:

- creating short URLs
- validating user inputs
- redirecting active links
- persisting records
- tracking click analytics
- exposing admin management APIs
- supporting a local web UI

### 2. Application and API implementation

The FastAPI app was implemented in `app/main.py` to expose the UI and the API routes. This step created the user-facing and admin-facing behavior.

### 3. Persistence

The SQLite layer was implemented in `app/database.py` and the schema was created to support link records and events. This was a dependency for all later work.

### 4. Frontend integration

The Jinja2 template and static JavaScript were added to make the homepage functional: copy link, validation, and alias display logic.

### 5. Link management

The admin APIs were added to support listing, updating, and deactivation. These actions rely on the service layer and are protected by admin key validation.

### 6. Analytics

Click analytics and access event storage were added after core redirect behavior was working. This depended on the link persistence layer.

### 7. Testing

The test suite was developed to cover redirect creation, validation, duplicate alias handling, admin auth, and analytics. This validated the behavior before the final QA pass.

### 8. Security hardening

The redirect validation and alias lifecycle hardening were added after audit-driven review. These checks protect against malformed or unsafe destinations and prevent alias reuse after deactivation.

### 9. Documentation

The README and engineering summary were created to explain the system, setup, API behavior, and deployment limitations.

### 10. Deployment preparation

A deployment prep step is clearly identified as external to the app logic: public DNS, HTTPS, host configuration, secret management, and production database choices remain outside the current local codebase.

### Dependency relationships

These tasks are sequentially dependent:

- persistence before redirect and analytics
- UI before user validation completion
- link management before admin operations
- analytics before reporting completeness
- security hardening before public deployment preparation

---

## 7. AI-Assisted Development Process

The project documents a general AI-assisted engineering workflow, but the repository does not include a complete, timestamped history of individual prompts or specific tool calls. The section below distinguishes actual evidence from representative practice.

### Supported use of AI assistance

AI can help with:

- requirement analysis and decomposition
- creating initial FastAPI and SQLite scaffolding
- generating and refining validation logic
- proposing tests for edge cases like duplicate aliases and invalid URLs
- debugging route and redirect behaviors
- reviewing security assumptions and edge cases
- drafting documentation and architecture summaries

### Actual evidence available in the repository

The repo contains a README section describing the AI-assisted workflow in general terms, and the project itself demonstrates an iterative engineering pattern: solution design, implementation, validation, and risk review.

### Representative prompt examples

The following examples are representative of effective prompts for a project like this, but they are not historical records from the repository:

- "Review the FastAPI URL shortener and identify validation gaps around unsupported redirect schemes."
- "Add focused pytest coverage for duplicate aliases and analytics preservation without changing the UI."
- "Explain the alias lifecycle and how deactivation should affect redirects and historical analytics."

### Distinction between actual work and recommended practice

Actual evidence in the repository supports the existence of:

- working code
- tests
- documentation
- environment-based config

Recommended best practice includes:

- structured prompt tracking for future traceability
- explicit review of AI-generated changes before merge
- periodic security review of generated code
- keeping AI as an accelerator rather than a final decision-maker

The current repository supports the engineering outcome without claiming a complete or historical prompt log.

---

## 8. Validation and Testing

### Testing framework

The project uses:

- pytest
- FastAPI `TestClient`
- SQLite temporary database fixture during the harder tests

### Test organization

Tests are grouped in `tests/test_url_shortener.py` and cover:

- UI rendering for the home page
- creation and resolution of valid short links
- public base URL override behavior
- invalid URL rejection
- duplicate alias rejection
- analytics endpoint correctness
- admin API auth and management operations
- invalid destination handling
- unsupported schemes
- deactivated alias rules
- analytics preservation after update/deactivation
- unknown alias handling

### Latest verified test command and result

Verified command:

```bash
cd "C:\Users\RAJESH\url_shortener_ai"; & ".\.venv\Scripts\python.exe" -m pytest -q
```

Verified result:

- 15 passed
- 0 failed
- exit code 0
- runtime approximately 2.24s

### Manual browser checks

The repository does not contain a recorded browser test suite. Manual checks are therefore identified as a recommended validation step and not as an automated historical verification. The expected checks include:

- home page loads successfully
- Swagger docs page loads successfully
- create URL flow works in the browser
- copy-to-clipboard flow works
- invalid URL and alias messages display correctly
- deactivated links do not redirect

### Untested or unverified behavior

- Real public hosting configuration
- Load/performance testing
- Multi-user or concurrent access behavior under real traffic
- Database backup or restore process
- Production secret management pipeline

---

## 9. Security Review

### Destination URL validation

The current implementation uses both request validation and service-layer validation to permit only `http` and `https` destinations. Unsupported schemes and malformed values are rejected before redirecting or storing a destination. This is a meaningful security improvement over an unrestricted redirect target.

### Alias uniqueness

The `links.short_code` column is unique. This prevents duplicate alias collisions at the database layer and ensures short codes remain unique across the application.

### Admin authentication

Admin routes require the `X-Admin-Key` header. The value must match `ADMIN_API_KEY`, which is sourced from environment variables. No admin key value is embedded in frontend code or returned in API responses.

### Input validation

Input validation is implemented through:

- Pydantic `HttpUrl` validation for destination URLs
- alias-pattern validation for custom short codes
- service-layer checks for malformed or unsupported URLs
- custom validation messages for required fields

### Error handling

The app returns clear HTTP errors for:

- invalid URLs
- duplicate aliases
- missing admin key
- wrong admin key
- unknown short codes
- deactivated links

This is good for application behavior but is not a substitute for a full security review.

### Remaining risks

- Rate limiting is not implemented.
- Abuse prevention is not implemented.
- There is no explicit protection against spam or content abuse in the public redirect flow.
- No production-grade secret management or environment isolation is included in the repo.
- The application does not implement a trusted URL allowlist or policy engine for destination validation.

### Security conclusion

The current implementation is substantially safer than an unvalidated redirect system, but it should not be described as a complete production security audit or a hardened public Internet service.

---

## 10. Engineering Decisions and Trade-offs

### Implemented decisions

- FastAPI was chosen to deliver a lightweight API and web application quickly.
- SQLite was chosen for simplicity, local execution, and testability.
- Global alias uniqueness was chosen to avoid collisions and maintain a predictable short-link model.
- Deactivation preserves the database record and analytics instead of deleting it, which supports audit and historical reporting.
- Redirects are 307 responses to preserve the original method semantics while redirecting to the destination.

### Trade-offs

- SQLite is easy to run and test, but it is not a multi-node, high-scale production database.
- Global uniqueness is simple and safe for the prototype, but it restricts alias reuse and reactivation behavior.
- Keeping historical records for deactivated links improves traceability but requires explicit operational handling in admin tasks.
- The app uses environment variables for config, which is appropriate for local and hosting environments, but it still requires a deployment process for secret injection.

### Proposed future improvements

- Move to PostgreSQL or another production database for concurrency and scale
- Add rate limiting and request throttling
- Add structured logging and metrics
- Add monitoring, health checks, and alerting
- Add backup and restore configuration
- Add deployment manifests or container definitions for hosting

---

## 11. Required Example Scenarios

The following scenarios are engineering scenarios for requirement analysis and solution planning. They are not necessarily recorded historical incidents in the repository.

### A. Greenfield scenario

Scenario:

A new product team asks for a URL shortener that accepts a long URL, creates a short alias, redirects users, and stores analytics for click counts.

Ambiguities and assumptions:

- The team wants a simple internal prototype, but does not specify traffic or persistence requirements.
- The team expects a clean API and a browser UI.

Questions an engineer should ask:

- Do we need user accounts or a single shared service?
- Is the app public or private?
- What are the expected volumes and retention requirements?
- Which aliases should be reserved or prohibited?

Work breakdown:

1. Define the data model and validation rules.
2. Implement the API and UI.
3. Add SQLite persistence.
4. Add redirect support and analytics.
5. Validate with automated tests.

Where AI is useful:

- generating initial endpoints and validations
- suggesting test edge cases
- drafting docs and examples

Validation:

- run pytest
- verify redirect behavior
- verify analytics increase on redirects

### B. Brownfield scenario

Scenario:

An existing URL shortener has a working redirect flow, but it needs link deactivation, destination updates, and analytics preservation without breaking old links.

Ambiguities and assumptions:

- Existing links must remain traceable.
- Deactivation should not delete records.
- Historical analytics should remain visible.

Questions an engineer should ask:

- Should deactivated aliases be reused later?
- Should admin changes be allowed only for trusted operators?
- How should redirect failures be reported?

Work breakdown:

1. Review the current DB schema and analytics behavior.
2. Add `is_active` handling and preserve records.
3. Ensure admin APIs enforce authentication.
4. Add tests for update and deactivation flows.
5. Validate with the existing suite.

Where AI is useful:

- reviewing edge cases like analytics preservation
- spotting logic gaps in update/deactivate flows
- generating regression tests

Validation:

- verify that analytics remain after deactivation
- verify that redirects are blocked for deactivated records
- verify patch and delete endpoints behave correctly

### C. Ambiguous scenario

Scenario:

"Make the URL shortener scalable and production-ready" without specifying traffic, region, retention, SLA, or hosting constraints.

Ambiguities and assumptions:

- No production requirements are explicit.
- Requirements are underspecified for traffic, capacity, deployment, or security model.

Questions an engineer should ask:

- What is the expected daily volume?
- Which environments are required?
- What is the retention requirement for analytics?
- Is the service public-facing or private?
- Which external admin controls are required?

Work breakdown:

1. Clarify traffic and retention requirements.
2. Identify database and hosting needs.
3. Define security boundaries and access control.
4. Estimate scale before selecting a production architecture.
5. Document known assumptions.

Where AI is useful:

- helping with requirement clarification questions
- generating a risk register
- proposing architecture options with trade-offs

Validation:

- validate assumptions with stakeholders
- test the prototype locally
- document the remaining gaps as post-implementation work

---

## 12. Setup Instructions

### Required Python version and dependencies

The project is configured for Python 3.15 in the local environment and uses the following dependency set from `requirements.txt`:

- fastapi==0.115.0
- uvicorn==0.30.6
- pytest==8.3.2
- httpx==0.27.2
- jinja2==3.1.6

### Virtual environment setup

From the project root:

```bash
python -m venv .venv
```

Activate the virtual environment:

On macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the app

From the project root:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The local application is expected at:

- http://127.0.0.1:8000/

The Swagger UI is expected at:

- http://127.0.0.1:8000/docs

### Run tests

```bash
pytest -q
```

### Required environment variables

The project uses:

- `PUBLIC_BASE_URL` for generated short-link domain configuration
- `ADMIN_API_KEY` for admin API access

Example in PowerShell:

```powershell
$env:PUBLIC_BASE_URL = "https://deepak.example.com"
$env:ADMIN_API_KEY = "your-admin-key"
```

### Database path

The application stores SQLite data under the project `data/` directory:

- `data/shortener.db`

This is not a public-facing database and is not a production deployment configuration.

---

## 13. Deployment Readiness

### What is ready

The app is ready for local use and evaluation, with:

- API exposure
- UI rendering
- database persistence
- redirect behavior
- analytics recording
- admin management endpoints
- automated validation

### What remains incomplete

- real public domain ownership and DNS configuration
- HTTPS certificate setup outside localhost
- deployment automation or hosting config
- production secret management strategy
- production database selection and migration strategy
- rate limiting and abuse prevention
- monitoring and observability

### Public URL configuration

The app supports `PUBLIC_BASE_URL` to build generated short URLs. If the variable is unset, it falls back to the request base URL or localhost. This allows local development but does not make a domain public by itself.

A Render deployment should configure `PUBLIC_BASE_URL` to the final public host after the domain is assigned, rather than hard-coding a hostname into the source code. The app should keep working locally without this variable set.

### Secret management

`ADMIN_API_KEY` must be supplied through environment variables when running in an environment that allows secret injection. It should not be committed to source control.

### Web server configuration

The project now includes a script-safe startup path that reads `PORT` with a fallback to `8000` and binds to `0.0.0.0` when run directly:

```python
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
```

This preserves the local workflow while allowing a hosting environment to pass a different port. The equivalent Render command is:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Database limitations

SQLite is lightweight and appropriate for local use, but it is not a production-grade persistence layer for public traffic, concurrent writes, or multi-instance hosting.

On Render, the filesystem is not guaranteed to be persistent across redeployments or restarts. A persistent disk may be enough for this interview prototype if uptime and file durability are acceptable, but the safer recommendation for a real public deployment is managed PostgreSQL. For this repository, the simplest safe approach is to keep SQLite for local evaluation and treat deployment as a prototype-only environment until a managed database is selected.

### Steps required before public hosting

1. Choose a hosting provider and deployment method.
2. Configure a public DNS domain and SSL certificate.
3. Set `PUBLIC_BASE_URL` to the live domain.
4. Set `ADMIN_API_KEY` in the deployment environment.
5. Decide whether SQLite remains acceptable or whether PostgreSQL is needed.
6. Add monitoring, logging, and backup strategy.
7. Validate public redirect behavior through live hosting checks.

### Local testing vs deployment testing

Local testing validates the app on the developer machine, including the browser UI and API behavior. Deployment testing is a separate step and should only be performed after the hosting platform, domain, certificates, environment variables, and start command are all configured correctly.

---

## 14. Risks, Limitations, and Future Improvements

### Highest-priority remaining work

1. Choose a production database that supports concurrency and operational scale.
2. Add rate limiting and basic abuse protection.
3. Add logging, monitoring, and health checks.
4. Add backup and recovery procedures.
5. Document and automate deployment and secret management.
6. Validate performance under realistic traffic patterns.

### Current limitations

- No production database configuration
- No public hosting deployment yet
- No rate limiting or abuse protection
- No deployment artifact or deployment manifest
- No backup strategy or operational runbook
- No production-grade security or compliance assurance

### Future improvements

- move from SQLite to PostgreSQL or a managed database
- add user-level or service-level authentication if needed
- add quotas and per-domain constraints
- enable more detailed analytics and retention policies
- add CI/CD checks for linting, tests, and environment validation

---

## 15. Conclusion

The project is a functioning local URL shortener prototype with a complete FastAPI backend, SQLite persistence, browser UI, custom alias support, analytics, and admin management. The latest verified test run shows 15 passing tests with no failures.

The current implementation is strong for a local engineering prototype and interview assignment, but it remains a deployment-preparation project rather than a production-public service. The most important remaining work is to define the production hosting environment, move beyond SQLite if needed, and add operational safeguards such as rate limits, monitoring, and secret management.

This is a valid engineering result for the current repository state, but it should be described accurately as a local prototype with documented deployment preparation gaps.
