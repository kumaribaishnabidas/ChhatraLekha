# ChhatraLekha — System Architecture Specification

**Document Version:** 1.0.0  
**Status:** Approved Target Architecture (Stage 0 Deliverable)  
**Target:** Unified National Education Super Platform for India

---

## 1. Existing Architecture (Verified Repository Audit)

The source of truth for the existing system is the actual codebase in the Git repository:

```
ChhatraLekha/
├── frontend/                     # React 19 + Vite 6 + Tailwind CSS v4 SPA
│   ├── src/components/           # Layouts (AppLayout, PublicLayout, DemoGuide), common UI, AI drawer
│   ├── src/pages/                # 29 pages (Dashboard, Student, Teacher, Parent, Verification)
│   ├── src/services/api.js       # Axios client with interceptors, tokenStore, base URL configuration
│   ├── src/i18n/                 # 22 Eighth Schedule Indian languages catalogue & JSON bundles
│   └── src/test/                 # 68 Vitest test cases (DesignLint, API, Format, Auth, Pages)
├── chhatralekha/                 # FastAPI (Python 3.12+) asynchronous ASGI backend
│   ├── app/main.py               # Lifespan events, CORS, security headers, router mounts
│   ├── app/api/                  # 21 REST routers (auth, ai, students, academic, attendance, etc.)
│   ├── app/core/                 # config (Pydantic), security (JWT/bcrypt/HMAC), database (Motor)
│   ├── app/models/               # documents.py (Doc wrapper), enums.py (Domain enumerations)
│   ├── app/repositories/         # Data access classes (users, students, tokens, audit, institutions)
│   ├── app/services/             # Domain logic (apaar_validator, anomaly_engine, ai_assistant)
│   └── tests/                    # 24 pytest suites using in-memory MongoDB
├── android/                      # Native Android Kotlin application
│   └── app/src/main/             # Jetpack Compose UI, Room DB (AppDatabase), WorkManager sync
├── ios/                          # Native iOS application
│   └── ChhatraLekha/             # Swift 6, SwiftUI, SwiftData, Keychain token storage
├── docs/                         # Specifications, ADRs, user guides, landing page HTML
├── docker-compose.yml            # Multi-service container orchestration
└── README.md                     # Project documentation & statutory disclaimers
```

### Verified Existing Functionality:
1. **Multi-Role Authentication & Demo Access:** JWT access tokens (`15m`), refresh tokens (`7d`), bcrypt hashing, rate limiting, and 1-click ephemeral demo logins for 6 personas (`student.demo`, `parent.demo`, `teacher.demo`, `schooladmin.demo`, `collegeadmin.demo`, `universityadmin.demo`).
2. **Student Digital ID & Wallet:** Masked APAAR ID (`****-****-1234`), printable digital badge, opaque revocable QR verification tokens, and PDF certificates.
3. **Campus Operations:** Teacher session attendance marking, daily period timetables, internal assessment entry.
4. **Regulatory Anomaly Detection:** Real-time compliance engine enforcing AICTE Approval Process Handbook (APH) intake ceilings, supernumerary quotas, and cross-college duplicate enrollment detection.
5. **Cryptographic Audit Trail:** Immutable SHA-256 hash-chained log (`audit_events`) recording credential issuance, verification scans, and record revisions.
6. **Multilingual AI Assistant:** Permission-aware RAG query engine grounded in official documentation and regulatory rules with text/voice input and audio TTS playback in 22 languages.
7. **5,000 Fictional Synthetic Student Records:** Procedurally generated load-test database across Indian states with `is_demo: true`.

---

## 2. Proposed Target Architecture (Modular Monolith)

The platform is evolving into a unified **Education Super Platform** serving schools, colleges, universities, students, parents, and teachers without fragmenting into disconnected apps.

```mermaid
graph TD
    subgraph Client Layer
        Web["Web Application<br>(React 19 + TypeScript + Vite)"]
        Android["Android Application<br>(Kotlin + Jetpack Compose)"]
        iOS["iOS Application<br>(Swift 6 + SwiftUI)"]
        Admin["Institution & National Portal<br>(Role-Scoped Workspaces)"]
    end

    subgraph Access & Gateway Layer
        Gateway["API Gateway / FastAPI Core"]
        AuthMid["Authentication & Session Middleware"]
        TenantMid["Tenant Context Resolver (X-Institution-ID)"]
        RBACMid["Role & Resource Permission Guard"]
        AuditMid["Cryptographic Audit Middleware"]
    end

    Web --> Gateway
    Android --> Gateway
    iOS --> Gateway
    Admin --> Gateway

    Gateway --> AuthMid
    AuthMid --> TenantMid
    TenantMid --> RBACMid
    RBACMid --> AuditMid

    subgraph Modular Backend Core
        M1["Identity & Membership"]
        M2["Academics & Enrolment"]
        M3["Attendance & Timetable"]
        M4["Learning Management (LMS)"]
        M5["Examinations & Results"]
        M6["Communication & Notices"]
        M7["Digital Wallet & Documents"]
        M8["Admissions & Verification"]
        M9["Opportunities & Placements"]
        M10["Campus & Digital Library"]
        M11["Grievance & Support Desk"]
        M12["AI Assistant & Bharat Voice"]
    end

    AuditMid --> M1 & M2 & M3 & M4 & M5 & M6 & M7 & M8 & M9 & M10 & M11 & M12

    subgraph Infrastructure & Persistence Layer
        DB[("Database<br>Motor MongoDB / Future PostgreSQL")]
        Storage["Private Object Storage<br>(Encrypted Documents)"]
        Jobs["Background Worker & Job Queue"]
        AuditLog[("SHA-256 Hash-Chained Audit Trail")]
        Notifier["Central Notification Dispatcher"]
    end

    M1 & M2 & M3 & M4 & M5 & M6 & M7 & M8 & M9 & M10 & M11 & M12 --> DB
    M7 & M8 --> Storage
    M3 & M5 & M6 --> Notifier
    M5 & M8 --> Jobs
    AuditMid --> AuditLog
```

---

## 3. Frontend, Backend & Mobile Communication Contract

All clients (Web, Android, iOS) interact with the same versioned RESTful backend (`/api/v1/`):

1. **Protocol:** HTTPS with strict TLS 1.3 encryption.
2. **Standard Request Headers:**
   - `Authorization: Bearer <jwt_access_token>`
   - `X-Institution-ID: <target_institution_id>` (Specifies active institutional membership context)
   - `X-Request-ID: <uuid>` (Unique per client request for distributed tracing)
   - `Accept-Language: <iso_code>` (`en`, `hi`, `or`, `ta`, etc.)
3. **Response Envelope Conventions:**
   - Standard 2xx payloads return data directly or wrapped in domain objects: `{ "data": ... }`.
   - Error responses adhere to RFC 7807: `{ "detail": "Human readable message", "code": "ERROR_CODE", "field": "optional_field" }`.
4. **Mobile Synchronization Contract:**
   - Mobile clients send batch synchronization payloads containing an array of timestamped operations with client-generated UUIDs (`sync_id`).
   - Server validates tenant permissions, checks optimistic concurrency locks, applies valid operations, and returns a reconciliation state.

---

## 4. Authentication and Authorization Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as User
    participant App as Web / Mobile App
    participant Gateway as API Gateway
    participant Auth as Auth & Membership Module
    participant Tenant as Tenant Resolver
    participant Repo as Domain Repository
    
    User->>App: Input Credentials / Biometric
    App->>Gateway: POST /api/v1/auth/login { email, password }
    Gateway->>Auth: Validate Credentials & Fetch Memberships
    Auth-->>App: Return TokenPair + Active Memberships List
    
    App->>Gateway: GET /api/v1/attendance/session/current (Header: X-Institution-ID: INST-0421)
    Gateway->>Tenant: Resolve Membership for User at INST-0421
    Tenant->>Tenant: Verify Membership is ACTIVE & Has "attendance:record" Permission
    Tenant->>Repo: Execute Query with Injected Filter: { "institution_id": "INST-0421", ... }
    Repo-->>App: Return Tenant-Isolated Records
```

---

## 5. Deployment and Infrastructure

1. **Containerized Architecture:**
   - Backend packaged as non-root container with Uvicorn worker threads.
   - Frontend built into static bundle hosted on high-performance CDN / edge caches.
   - Docker Compose orchestrates local development environments with MongoDB and test mocks.
2. **Storage Architecture:**
   - Sensitive student documents (marksheets, transfer certificates) are stored in private object storage (S3/GCS compliant) with presigned, time-limited download URLs.
3. **Monitoring & Auditing:**
   - Structured JSON logging with request tracing (`X-Request-ID`).
   - Hash-chained audit records (`audit_events`) backed up to write-once append-only storage.
