# ChhatraLekha — API Route Specification (REST API v1)

**Document Version:** 1.0.0  
**Status:** Approved Target Architecture (Stage 0 Deliverable)

---

## 1. Global Conventions, Headers & Versioning

### 1.1 Versioning Strategy
All APIs are versioned under `/api/v1/`. Breaking changes will be introduced under `/api/v2/` without altering active `/api/v1/` contracts.

### 1.2 Global Request Headers
| Header | Required | Example | Description |
| :--- | :--- | :--- | :--- |
| `Authorization` | Yes | `Bearer eyJhbGci...` | User JWT access token |
| `X-Institution-ID` | Yes (for tenant routes) | `INST-0421` | Active institution tenant context |
| `X-Request-ID` | No | `req_9a8b7c6d` | Distributed tracing identifier |
| `Accept-Language` | No | `or`, `hi`, `en` | Preferred response localization |

### 1.3 Pagination & Filtering Conventions
- **Offset/Limit:** `?offset=0&limit=25` (Maximum limit: 100).
- **Sorting:** `?sort=-created_at` (Prefix with `-` for descending).
- **Search:** `?q=Sharma` (Case-insensitive substring / full-text match).
- **Envelope Response:**
  ```json
  {
    "items": [...],
    "total": 1420,
    "offset": 0,
    "limit": 25,
    "has_more": true
  }
  ```

### 1.4 Standardized Error Handling (RFC 7807)
All errors return consistent structure:
```json
{
  "type": "https://chhatralekha.edu.in/errors/permission-denied",
  "title": "Forbidden",
  "status": 403,
  "detail": "User lacks 'attendance:record' permission for INST-0421.",
  "instance": "/api/v1/attendance/session/submit",
  "request_id": "req_9a8b7c6d"
}
```

---

## 2. API Route Inventory by Domain

### 2.1 Identity & Access (`/api/v1/auth`)

| Method | Endpoint | Description | Scope / Permission |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Email & password credentials exchange | Public |
| `POST` | `/api/v1/auth/demo-login`| 1-click demo persona session | Public |
| `POST` | `/api/v1/auth/refresh` | Refresh access token | Public (Refresh Token) |
| `POST` | `/api/v1/auth/logout` | Invalidate active session & tokens | Authenticated |
| `GET` | `/api/v1/auth/memberships` | List user's institutional memberships | Authenticated |
| `POST` | `/api/v1/auth/switch-context` | Select active institution membership | Authenticated |

### 2.2 Institution Management (`/api/v1/institutions`)

| Method | Endpoint | Description | Scope / Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/institutions/me` | Fetch active institution details & settings | `institution:read` |
| `PATCH` | `/api/v1/institutions/me` | Update institution profile & grading rules | `institution:write` |
| `GET` | `/api/v1/institutions/structure`| Get full academic tree (Years, Depts, Classes) | `academics:read` |
| `POST` | `/api/v1/institutions/academic-years` | Create/activate academic year | `academic_year:manage` |

### 2.3 Student & Enrolment Management (`/api/v1/enrolments`)

| Method | Endpoint | Description | Scope / Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/enrolments` | List enrolled students in active institution | `students:read` |
| `POST` | `/api/v1/enrolments` | Enrol single student into programme & class | `students:enrol` |
| `POST` | `/api/v1/enrolments/batch-csv` | Bulk upload roster with schema validation | `students:import` |
| `GET` | `/api/v1/enrolments/{student_id}` | Detailed enrolment profile & quota | `students:read` |
| `POST` | `/api/v1/enrolments/{student_id}/claim-code` | Issue secure student claim/onboarding code | `students:manage` |

### 2.4 Attendance Engine (`/api/v1/attendance`)

| Method | Endpoint | Description | Scope / Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/attendance/session/current`| Get active roster for teacher's class period | `attendance:record` |
| `POST` | `/api/v1/attendance/session/submit` | Save period attendance (Present/Absent/Late) | `attendance:record` |
| `GET` | `/api/v1/attendance/student/{student_id}` | Cumulative & subject attendance summary | `attendance:view_own` / Parent / Teacher |
| `PATCH` | `/api/v1/attendance/record/{record_id}` | Correct attendance entry with audit remark | `attendance:correct` |

### 2.5 Examinations & Moderation (`/api/v1/examinations`)

| Method | Endpoint | Description | Scope / Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/examinations` | List scheduled assessments for active class | `assessments:read` |
| `POST` | `/api/v1/examinations` | Create new assessment or examination | `assessments:create` |
| `POST` | `/api/v1/examinations/{id}/marks` | Enter student marks | `marks:enter` |
| `POST` | `/api/v1/examinations/{id}/moderate` | Moderate marks before publication | `marks:moderate` |
| `POST` | `/api/v1/examinations/{id}/publish` | Approve & publish results to student wallet | `results:publish` |

### 2.6 Learning Hub & LMS (`/api/v1/learning`)

| Method | Endpoint | Description | Scope / Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/learning/materials` | List course study materials & lecture links | `learning:read` |
| `POST` | `/api/v1/learning/materials` | Teacher upload notes/materials (PDF, links) | `learning:upload` |
| `GET` | `/api/v1/learning/assignments` | List assignments and upcoming deadlines | `assignments:read` |
| `POST` | `/api/v1/learning/assignments` | Create assignment with rubric & deadline | `assignments:create` |
| `POST` | `/api/v1/learning/assignments/{id}/submit` | Student submits file attachment/answers | `assignments:submit` |
| `POST` | `/api/v1/learning/submissions/{id}/grade` | Faculty grades submission with feedback | `assignments:grade` |

### 2.7 Opportunities & Placements (`/api/v1/opportunities`)

| Method | Endpoint | Description | Scope / Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/opportunities` | Discover scholarships, internships, jobs | `opportunities:read` |
| `POST` | `/api/v1/opportunities` | Post verified campus placement / internship | `opportunities:post` |
| `POST` | `/api/v1/opportunities/{id}/apply` | Submit application linked to student portfolio | `opportunities:apply` |

### 2.8 Student Support & Grievances (`/api/v1/helpdesk`)

| Method | Endpoint | Description | Scope / Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/helpdesk/tickets` | View student tickets or department queue | `tickets:read` |
| `POST` | `/api/v1/helpdesk/tickets` | Submit complaint (Academic, Facility, Confidential) | `tickets:create` |
| `POST` | `/api/v1/helpdesk/tickets/{id}/reply` | Add authorized response or follow-up | `tickets:reply` |
| `PATCH` | `/api/v1/helpdesk/tickets/{id}/escalate` | Escalate unresolved ticket to committee | `tickets:escalate` |

### 2.9 ChhatraLekha AI Assistant (`/api/v1/ai`)

| Method | Endpoint | Description | Scope / Permission |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/ai/chat` | Natural language grounded assistant query | Authenticated |
| `GET` | `/api/v1/ai/prompts` | Role-tailored quick question chips | Authenticated |
