# ChhatraLekha — System Architecture Specification

**Document Version:** 1.0.0  
**Status:** Approved Target Architecture (Stage 0 Deliverable)  
**Target:** Unified National Education Super Platform for India

---

## 1. Architectural Overview

ChhatraLekha is architected as a **Modular Monolith** supporting schools (K-12), colleges (UG/PG), universities, and regulatory directorates across Web, Android, and iOS. The modular monolith pattern delivers clean domain boundaries, unified transactions, simplified deployment, and shared security without the operational overhead of microservices, while maintaining strict domain separation to allow future microservice extraction if scale demands.

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
        TenantMid["Tenant Resolver (X-Institution-ID)"]
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

    subgraph Modular Backend Services
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

## 2. Core Architectural Principles

1. **Central Identity, Scoped Memberships:**
   A single user account (`User`) holds central credentials and demographic details. Institutional access is mediated entirely through `InstitutionMembership` records (`User -> InstitutionMembership -> Role -> Permissions`). A user can be an undergraduate student at College A, an alumnus of School B, and a parent of a student at School C.
2. **Tenant Isolation by Construction:**
   Every institution-owned entity carries an immutable `institution_id`. Backend data repositories reject queries that fail to enforce institution scoping.
3. **History-Preserving Academic Records:**
   Published marks, locked attendance sessions, and degree credentials are append-only. Corrections do not overwrite existing rows; they record versioned change-impact entries in the cryptographic audit trail.
4. **Offline-First Mobile Parity:**
   Mobile clients maintain a local SQLite/Room/SwiftData cache. Offline actions are queued and synchronized server-authoritatively with cryptographic nonces and conflict detection.
5. **Grounded AI with Strict Authorization:**
   The ChhatraLekha AI Assistant operates exclusively through the same permission-checked APIs as regular users, retrieving facts only from records the user is authorized to see.

---

## 3. Technology Stack Reference

| Tier | Technology | Purpose & Rationale |
| :--- | :--- | :--- |
| **Web Frontend** | React 19, TypeScript, Vite 6, Tailwind CSS v4 | High-performance, accessible, bundle-optimized SPA with strict design system enforcement. |
| **Android App** | Kotlin 2.0+, Jetpack Compose, Room, WorkManager | Modern declarative UI, offline-first local database, reliable background syncing. |
| **iOS App** | Swift 6, SwiftUI, SwiftData, AVFoundation | Native performance, Keychain token security, system-level voice integration. |
| **Backend** | Python 3.12+, FastAPI, Pydantic v2, Uvicorn | Async ASGI framework, high-throughput REST APIs, automated OpenAPI documentation. |
| **Database** | Motor async MongoDB (Current) / PostgreSQL (Target) | Dual-mode in-memory test harness; clean domain repository abstraction for future relational transition. |
| **Security** | PyJWT, bcrypt, HMAC-SHA256, cryptography | Tamper-evident verifiable credentials, encrypted local stores, masked APAAR tokens. |
| **i18n & Voice** | i18next, Web Speech API, BHASHINI-ready abstraction | Full 22 Eighth Schedule languages catalogue, STT voice input, TTS audio playback. |
