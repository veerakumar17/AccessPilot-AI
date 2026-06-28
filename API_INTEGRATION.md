# AccessPilot AI — Backend API Integration Guide

Base URL: `http://localhost:8000`

**Prefix:** `/api/v1`

---

## 1. Authentication

### 1.1 Register

| Field             | Value                          |
|-------------------|--------------------------------|
| **Endpoint**      | `POST /api/v1/auth/register`   |
| **HTTP Method**   | POST                           |
| **Auth Required** | No                             |

**Request Schema:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "Jane Doe"
}
```

| Field      | Type   | Required | Constraints              |
|------------|--------|----------|--------------------------|
| email      | string | Yes      | Valid email format       |
| password   | string | Yes      | Minimum 8 characters     |
| full_name  | string | No       |                          |

**Response Schema (201 Created):**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "is_active": true,
  "created_at": "2026-06-19T10:00:00Z"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123","full_name":"Jane Doe"}'
```

**Example Response:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "is_active": true,
  "created_at": "2026-06-19T10:00:00Z"
}
```

---

### 1.2 Login

| Field             | Value                         |
|-------------------|-------------------------------|
| **Endpoint**      | `POST /api/v1/auth/login`     |
| **HTTP Method**   | POST                          |
| **Auth Required** | No                            |

**Request Schema:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

| Field    | Type   | Required | Constraints        |
|----------|--------|----------|--------------------|
| email    | string | Yes      | Valid email format |
| password | string | Yes      |                    |

**Response Schema (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

**Example Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzZmE4NWY2NC01NzE3LTQ1NjItYjNmYy0yYzk2M2Y2NmFmYTYiLCJleHAiOjE3MTc3OTQ4MDB9.example",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzZmE4NWY2NC01NzE3LTQ1NjItYjNmYy0yYzk2M2Y2NmFmYTYiLCJleHAiOjE3MTgzOTk2MDB9.example",
  "token_type": "bearer"
}
```

**Frontend action:** Store `access_token` and `refresh_token` securely (e.g., httpOnly cookie or secure local storage). Include `access_token` in subsequent requests as `Authorization: Bearer <access_token>`.

---

### 1.3 Get Current User

| Field             | Value                       |
|-------------------|-----------------------------|
| **Endpoint**      | `GET /api/v1/auth/me`       |
| **HTTP Method**   | GET                         |
| **Auth Required** | Yes (Bearer token)          |

**Response Schema (200 OK):**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "is_active": true,
  "created_at": "2026-06-19T10:00:00Z"
}
```

**Example Request:**
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Example Response:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "is_active": true,
  "created_at": "2026-06-19T10:00:00Z"
}
```

---

## 2. Projects

### 2.1 Create Project

| Field             | Value                             |
|-------------------|-----------------------------------|
| **Endpoint**      | `POST /api/v1/projects`           |
| **HTTP Method**   | POST                              |
| **Auth Required** | Yes (Bearer token)                |

**Request Schema:**
```json
{
  "name": "My Website",
  "base_url": "https://example.com",
  "description": "Company homepage accessibility check"
}
```

| Field       | Type   | Required | Constraints         |
|-------------|--------|----------|---------------------|
| name        | string | Yes      | 1–255 characters    |
| base_url    | string | Yes      | Valid HTTP(S) URL   |
| description | string | No       |                     |

**Response Schema (201 Created):**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "My Website",
  "base_url": "https://example.com",
  "description": "Company homepage accessibility check",
  "created_at": "2026-06-19T10:00:00Z",
  "updated_at": "2026-06-19T10:00:00Z"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{"name":"My Website","base_url":"https://example.com","description":"Company homepage accessibility check"}'
```

**Example Response:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "My Website",
  "base_url": "https://example.com",
  "description": "Company homepage accessibility check",
  "created_at": "2026-06-19T10:00:00Z",
  "updated_at": "2026-06-19T10:00:00Z"
}
```

---

### 2.2 List Projects

| Field             | Value                        |
|-------------------|------------------------------|
| **Endpoint**      | `GET /api/v1/projects`       |
| **HTTP Method**   | GET                          |
| **Auth Required** | Yes (Bearer token)           |

**Response Schema (200 OK):**
```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "My Website",
    "base_url": "https://example.com",
    "description": "Company homepage",
    "created_at": "2026-06-19T10:00:00Z",
    "updated_at": "2026-06-19T10:00:00Z"
  }
]
```

**Example Request:**
```bash
curl http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Example Response:**
```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "My Website",
    "base_url": "https://example.com",
    "description": "Company homepage",
    "created_at": "2026-06-19T10:00:00Z",
    "updated_at": "2026-06-19T10:00:00Z"
  }
]
```

---

### 2.3 Get Project

| Field             | Value                                   |
|-------------------|-----------------------------------------|
| **Endpoint**      | `GET /api/v1/projects/{project_id}`     |
| **HTTP Method**   | GET                                     |
| **Auth Required** | Yes (Bearer token)                      |

**Response Schema (200 OK):**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "My Website",
  "base_url": "https://example.com",
  "description": null,
  "created_at": "2026-06-19T10:00:00Z",
  "updated_at": "2026-06-19T10:00:00Z"
}
```

**Example Request:**
```bash
curl http://localhost:8000/api/v1/projects/3fa85f64-5717-4562-b3fc-2c963f66afa6 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

### 2.4 Delete Project

| Field             | Value                                      |
|-------------------|--------------------------------------------|
| **Endpoint**      | `DELETE /api/v1/projects/{project_id}`     |
| **HTTP Method**   | DELETE                                     |
| **Auth Required** | Yes (Bearer token)                         |

**Response:** `204 No Content` (no body)

**Example Request:**
```bash
curl -X DELETE http://localhost:8000/api/v1/projects/3fa85f64-5717-4562-b3fc-2c963f66afa6 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## 3. Audits

### 3.1 Start Audit

Launches an asynchronous audit pipeline (crawl → scan → AI enrichment → report). Returns immediately with `202 Accepted`.

| Field             | Value                        |
|-------------------|------------------------------|
| **Endpoint**      | `POST /api/v1/audits`        |
| **HTTP Method**   | POST                         |
| **Auth Required** | Yes (Bearer token)           |

**Request Schema:**
```json
{
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "target_url": "https://example.com"
}
```

| Field       | Type   | Required | Description                                       |
|-------------|--------|----------|---------------------------------------------------|
| project_id  | string | Yes      | UUID of the project to audit                      |
| target_url  | string | No       | Overrides the project's base_url if provided      |

**Response Schema (202 Accepted):**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "running",
  "error_message": null,
  "started_at": "2026-06-19T10:00:00Z",
  "completed_at": null
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/audits \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{"project_id":"3fa85f64-5717-4562-b3fc-2c963f66afa6","target_url":"https://example.com"}'
```

**Example Response:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "running",
  "error_message": null,
  "started_at": "2026-06-19T10:00:00Z",
  "completed_at": null
}
```

---

### 3.2 Get Audit Status

| Field             | Value                                   |
|-------------------|-----------------------------------------|
| **Endpoint**      | `GET /api/v1/audits/{audit_id}`         |
| **HTTP Method**   | GET                                     |
| **Auth Required** | Yes (Bearer token)                      |

**Response Schema (200 OK):**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "completed",
  "error_message": null,
  "started_at": "2026-06-19T10:00:00Z",
  "completed_at": "2026-06-19T10:05:00Z"
}
```

**Status enum:**
| Value       | Description                                    |
|-------------|------------------------------------------------|
| `pending`   | Created, pipeline not yet started              |
| `running`   | Pipeline in progress                           |
| `completed` | Pipeline finished successfully                 |
| `failed`    | Pipeline failed; check `error_message` field   |

**Example Request:**
```bash
curl http://localhost:8000/api/v1/audits/3fa85f64-5717-4562-b3fc-2c963f66afa6 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

### 3.3 Get Audit Summary

Returns combined audit status + report data. Report fields are `null` while the pipeline is running. **Poll this endpoint** every 3–5 seconds to track progress.

| Field             | Value                                         |
|-------------------|-----------------------------------------------|
| **Endpoint**      | `GET /api/v1/audits/{audit_id}/summary`       |
| **HTTP Method**   | GET                                           |
| **Auth Required** | Yes (Bearer token)                            |

**Response Schema (200 OK):**
```json
{
  "audit_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "completed",
  "started_at": "2026-06-19T10:00:00Z",
  "completed_at": "2026-06-19T10:05:00Z",
  "error_message": null,
  "accessibility_score": 72.5,
  "pages_scanned": 5,
  "total_violations": 14,
  "severity_breakdown": {
    "critical": 1,
    "serious": 3,
    "moderate": 6,
    "minor": 4
  },
  "summary_text": "Accessibility score: 72.5/100 (B). Found 14 violation(s) across 5 page(s). 1 critical issue(s) require immediate attention — they block access entirely for some users."
}
```

| Field                | Type          | Available When    | Description                           |
|----------------------|---------------|-------------------|---------------------------------------|
| audit_id             | string (UUID) | Always            |                                       |
| project_id           | string (UUID) | Always            |                                       |
| status               | string        | Always            | pending / running / completed / failed|
| started_at           | string (ISO)  | Always            |                                       |
| completed_at         | string|null   | After completion  |                                       |
| error_message        | string|null   | On failure        |                                       |
| accessibility_score  | float|null    | After completion  | 0.0 – 100.0                          |
| pages_scanned        | int|null      | After completion  |                                       |
| total_violations     | int|null       | After completion  |                                       |
| severity_breakdown   | object|null   | After completion  | critical / serious / moderate / minor |
| summary_text         | string|null   | After completion  | Human-readable summary                |

**Example Request:**
```bash
curl http://localhost:8000/api/v1/audits/3fa85f64-5717-4562-b3fc-2c963f66afa6/summary \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Example Response (completed):**
```json
{
  "audit_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "completed",
  "started_at": "2026-06-19T10:00:00Z",
  "completed_at": "2026-06-19T10:05:00Z",
  "error_message": null,
  "accessibility_score": 72.5,
  "pages_scanned": 5,
  "total_violations": 14,
  "severity_breakdown": {
    "critical": 1,
    "serious": 3,
    "moderate": 6,
    "minor": 4
  },
  "summary_text": "Accessibility score: 72.5/100 (B). Found 14 violation(s) across 5 page(s). 1 critical issue(s) require immediate attention — they block access entirely for some users."
}
```

**Example Response (running — note null fields):**
```json
{
  "audit_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "running",
  "started_at": "2026-06-19T10:00:00Z",
  "completed_at": null,
  "error_message": null,
  "accessibility_score": null,
  "pages_scanned": null,
  "total_violations": null,
  "severity_breakdown": null,
  "summary_text": null
}
```

---

### 3.4 Get Pages

Returns all pages crawled during the audit.

| Field             | Value                                      |
|-------------------|--------------------------------------------|
| **Endpoint**      | `GET /api/v1/audits/{audit_id}/pages`      |
| **HTTP Method**   | GET                                        |
| **Auth Required** | Yes (Bearer token)                         |

**Response Schema (200 OK):**
```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "audit_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "url": "https://example.com",
    "title": "Example Domain",
    "violation_count": 4,
    "crawled_at": "2026-06-19T10:02:00Z"
  }
]
```

**Example Request:**
```bash
curl http://localhost:8000/api/v1/audits/3fa85f64-5717-4562-b3fc-2c963f66afa6/pages \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

### 3.5 Get Violations

Returns all violations enriched with AI explanations, fix suggestions, and disability simulations.

| Field             | Value                                          |
|-------------------|------------------------------------------------|
| **Endpoint**      | `GET /api/v1/audits/{audit_id}/violations`     |
| **HTTP Method**   | GET                                            |
| **Auth Required** | Yes (Bearer token)                             |

**Response Schema (200 OK):**
```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "page_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "rule_id": "image-alt",
    "severity": "critical",
    "html_snippet": "<img src=\"logo.png\">",
    "selector": "#header > img",
    "wcag_criteria": "1.1.1",
    "ai_explanation": "This image is missing alt text, so screen readers cannot describe it to blind users.",
    "ai_fix": "{\"problem\":\"Image is missing alternative text\",\"recommended_fix\":\"Add an alt attribute with descriptive text\",\"code_example\":\"<img src=\\\\"logo.png\\\" alt=\\\\"Company logo\\\">\",\"implementation_steps\":[\"Locate the <img> element\",\"Add alt=\\\\"descriptive text\\\"\"],\"priority\":\"critical\"}",
    "fix_type": null,
    "ai_simulation": "{\"affected_groups\":[{\"disability\":\"blind\",\"impact\":\"Screen reader users cannot perceive the image content at all\"},{\"disability\":\"low_vision\",\"impact\":\"Users who zoom or use high contrast mode still cannot identify the image\"},{\"disability\":\"motor\",\"impact\":\"No direct impact — keyboard navigation is not affected\"},{\"disability\":\"cognitive\",\"impact\":\"Users with cognitive disabilities may miss contextual cues the image provides\"}],\"severity_explanation\":\"This is a critical issue because it completely blocks blind users from accessing image content, violating WCAG 1.1.1\",\"user_experience\":\"A blind user navigating the page with a screen reader will hear nothing as they land on the image element, losing the information or context the image was meant to convey\"}",
    "disability_types": ["blind"],
    "created_at": "2026-06-19T10:03:00Z"
  }
]
```

| Field             | Type              | Description                                                    |
|-------------------|-------------------|----------------------------------------------------------------|
| id                | string (UUID)     | Violation ID                                                   |
| page_id           | string (UUID)     | Page the violation was found on                                |
| rule_id           | string            | axe-core rule ID (e.g. `image-alt`, `color-contrast`)          |
| severity          | string            | `critical`, `serious`, `moderate`, `minor`                     |
| html_snippet      | string|null       | The violating HTML fragment                                    |
| selector          | string|null       | CSS selector to locate the element                             |
| wcag_criteria     | string|null       | WCAG success criterion (e.g. `1.1.1`)                          |
| ai_explanation    | string|null       | Plain-English explanation (generated by LLM)                   |
| ai_fix            | string|null       | **JSON string** — structured fix (parse to object)             |
| fix_type          | string|null       | Deprecated — prefer `ai_fix`                                   |
| ai_simulation     | string|null       | **JSON string** — disability simulation (parse to object)      |
| disability_types  | string[]          | Disability type codes affected (e.g. `["blind", "low_vision"]`) |
| created_at        | string (ISO)      | Timestamp of when the violation was recorded                   |

**`ai_fix` parsed structure:**
```json
{
  "problem": "Image is missing alternative text",
  "recommended_fix": "Add an alt attribute to the img element with descriptive text",
  "code_example": "<img src=\"logo.png\" alt=\"Company logo - Home\">",
  "implementation_steps": [
    "Locate the <img> element at #header > img",
    "Add an alt attribute with descriptive text",
    "If the image is decorative, use alt=\"\" (empty)"
  ],
  "priority": "critical"
}
```

**`ai_simulation` parsed structure:**
```json
{
  "affected_groups": [
    {
      "disability": "blind",
      "impact": "Screen reader users cannot perceive the image content at all"
    },
    {
      "disability": "low_vision",
      "impact": "Users who zoom or use high contrast mode still cannot identify the image"
    },
    {
      "disability": "motor",
      "impact": "No direct impact — keyboard navigation is not affected"
    },
    {
      "disability": "cognitive",
      "impact": "Users with cognitive disabilities may miss contextual cues the image provides"
    }
  ],
  "severity_explanation": "This is a critical issue because it completely blocks blind users from accessing image content, violating WCAG 1.1.1",
  "user_experience": "A blind user navigating the page with a screen reader will hear nothing as they land on the image element, losing the information or context the image was meant to convey"
}
```

**Disability type codes:**
| Value          | Description                     |
|----------------|---------------------------------|
| `blind`        | Blind / screen reader users     |
| `low_vision`   | Low vision / zoom users         |
| `motor`        | Motor / keyboard-only users     |
| `cognitive`    | Cognitive disability users      |

**Example Request:**
```bash
curl http://localhost:8000/api/v1/audits/3fa85f64-5717-4562-b3fc-2c963f66afa6/violations \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## 4. Reports

### 4.1 Get Report

Returns the computed accessibility report for a completed audit.

| Field             | Value                                    |
|-------------------|------------------------------------------|
| **Endpoint**      | `GET /api/v1/reports/{audit_id}`         |
| **HTTP Method**   | GET                                      |
| **Auth Required** | Yes (Bearer token)                       |

**Response Schema (200 OK):**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "audit_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "accessibility_score": 72.5,
  "total_violations": 14,
  "critical_count": 1,
  "serious_count": 3,
  "moderate_count": 6,
  "minor_count": 4,
  "pages_scanned": 5,
  "summary_text": "Accessibility score: 72.5/100 (B). Found 14 violation(s) across 5 page(s). 1 critical issue(s) require immediate attention — they block access entirely for some users.",
  "generated_at": "2026-06-19T10:05:00Z"
}
```

**Example Request:**
```bash
curl http://localhost:8000/api/v1/reports/3fa85f64-5717-4562-b3fc-2c963f66afa6 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Example Response:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "audit_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "accessibility_score": 72.5,
  "total_violations": 14,
  "critical_count": 1,
  "serious_count": 3,
  "moderate_count": 6,
  "minor_count": 4,
  "pages_scanned": 5,
  "summary_text": "Accessibility score: 72.5/100 (B). Found 14 violation(s) across 5 page(s). 1 critical issue(s) require immediate attention — they block access entirely for some users.",
  "generated_at": "2026-06-19T10:05:00Z"
}
```

---

## 5. Health Check

| Field             | Value               |
|-------------------|---------------------|
| **Endpoint**      | `GET /health`       |
| **HTTP Method**   | GET                 |
| **Auth Required** | No                  |

**Response Schema (200 OK):**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## 6. Error Responses

**Standard error (4xx/5xx):**
```json
{
  "detail": "Human-readable error message"
}
```

**Validation error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error"
    }
  ]
}
```

**Error codes:**
| Status | Meaning                          |
|--------|----------------------------------|
| 401    | Unauthorized — missing/invalid token |
| 403    | Forbidden — not your resource    |
| 404    | Resource not found               |
| 409    | Conflict (e.g. duplicate email)  |
| 422    | Validation error                 |
| 500    | Internal server error            |

---

## 7. Polling Workflow

The recommended frontend flow for running an audit:

```typescript
// 1. Register or login to get token
const { access_token } = await login(email, password);

// 2. Create project
const project = await createProject({ name, base_url });

// 3. Start audit (returns 202 — async)
const audit = await startAudit(project.id);

// 4. Poll summary until completed or failed
let summary = await getAuditSummary(audit.id);
while (summary.status === 'running') {
  await sleep(3000);
  summary = await getAuditSummary(audit.id);
}

if (summary.status === 'failed') {
  showError(summary.error_message);
} else {
  // 5. Fetch full data
  const pages = await getPages(audit.id);
  const violations = await getViolations(audit.id);

  // Parse AI-enriched fields
  for (const v of violations) {
    v.ai_fix = JSON.parse(v.ai_fix);          // object or null
    v.ai_simulation = JSON.parse(v.ai_simulation);  // object or null
  }

  renderDashboard(summary, pages, violations);
}