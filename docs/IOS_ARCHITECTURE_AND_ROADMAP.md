# ChhatraLekha iOS Architecture & Engineering Roadmap

**Product:** ChhatraLekha iOS Client  
**Architecture:** Swift 6, SwiftUI, Swift Concurrency, Clean Architecture + MVVM  
**Offline Persistence:** GRDB.swift (SQLite) / Encrypted SQLCipher  
**Security:** Secure Enclave, Apple Keychain, CryptoKit  
**Compliance:** Indian DPDP Act 2023, Apple Privacy Manifest (`PrivacyInfo.xcprivacy`)  
**Companion Platforms:** Web (React 19, Vite, Tailwind), Backend (FastAPI, MongoDB), Android (Kotlin, Jetpack Compose, Room)  
**Date:** October 2026  

---

## 1. Executive Summary & Purpose

ChhatraLekha is a public-benefit, multi-tenant digital education platform engineered to serve schools, polytechnics, and higher education colleges across India. The platform is free to use for all institutions, students, teachers, and parents, funded via transparent educational research grants and corporate social responsibility infrastructure endowments, with an absolute prohibition on advertising, data monetization, and behavioral profiling.

To deliver universal access across India's mobile ecosystem, ChhatraLekha operates native mobile clients alongside its web portal. This document establishes the technical architecture, security model, data synchronization engine, and delivery roadmap for the native **ChhatraLekha iOS client**.

The iOS client is designed to mirror the offline-first capabilities of the Android application (`android/`) while adhering to Apple Human Interface Guidelines (HIG), modern Swift 6 language safety standards, and strict privacy regulations.

---

## 2. Core Architectural Principles

1. **Native Swift 6 & SwiftUI First**:
   - Modern declarative UI with 100% SwiftUI.
   - Strict concurrency (`Sendable` checking, Swift 6 language mode, actors for state synchronization).
   - Dynamic Type, VoiceOver accessibility, and system Dark Mode support out of the box.

2. **Offline-First Data Reliability**:
   - Academic records, digital ID cards, schedules, and draft attendance entries persist locally.
   - Network operations run through an offline mutation outbox queue with idempotent delivery.
   - Zero app crashes or blocked screens during intermittent or absent 2G/3G/4G connectivity.

3. **Zero Advertising, Surveillance, or Commercial Tracking**:
   - No commercial analytics frameworks, ad trackers, or third-party fingerprinting SDKs.
   - Apple Privacy Manifest (`PrivacyInfo.xcprivacy`) declares zero tracking and minimal required-reason APIs.

4. **Cryptographic Integrity & Secure Enclave**:
   - Auth tokens and institutional cryptographic seals stored in the iOS Keychain with `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`.
   - Tamper-evident credential verification implemented locally using Apple's `CryptoKit` (HMAC-SHA256 and Ed25519 signature checks).
   - Biometric authentication (Face ID / Touch ID) functions purely as a local convenience gate; biometric templates never leave the device Secure Enclave and are never required for basic verification.

5. **Pan-Indian Localization**:
   - Native support for 13 official Indian languages (Assamese, Bengali, English, Gujarati, Hindi, Kannada, Malayalam, Marathi, Odia, Punjabi, Tamil, Telugu, Urdu) using iOS String Catalogs (`.xcstrings`) with proper right-to-left (RTL) layout switching for Urdu.

---

## 3. System Architecture & Layered Design

The iOS application adopts Clean Architecture with MVVM (Model-View-ViewModel), separating concerns into four discrete, testable layers:

```
+-----------------------------------------------------------------------+
|                           PRESENTATION LAYER                          |
|  SwiftUI Views  *  @Observable ViewModels  *  Navigation Coordinators |
|  Design System (Royal Blue, Saffron, Ivory)  *  Accessibility Labels   |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                             DOMAIN LAYER                              |
|  UseCases / Interactors  *  Domain Entities  *  Repository Protocols  |
|  Business Rules  *  Role-Based UI Matrix  *  Credential Validators    |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                              DATA LAYER                               |
|  Repository Implementations  *  Sync Coordinator  *  Outbox Worker    |
+-----------------------------------+-----------------------------------+
                  |                                   |
                  v                                   v
+-----------------------------------+   +-------------------------------+
|        REMOTE DATA SOURCE         |   |       LOCAL DATA SOURCE       |
|  URLSession HTTP Client           |   |  GRDB.swift (SQLite Database) |
|  FastAPI REST API Monolith        |   |  Encrypted DB File (SQLCipher)|
|  Token Refresh Authenticator      |   |  KeychainWrapper (Tokens)     |
+-----------------------------------+   +-------------------------------+
```

### 3.1 Layer Responsibilities

- **Presentation Layer**:
  - Declarative SwiftUI views structured by feature module (Wallet, Attendance, Announcements, Results, Parent Portal).
  - `@Observable` macro (iOS 17+) ViewModels driving view states: `Idle`, `Loading`, `Success(Data)`, `Error(AppError)`.
  - Reusable design system components matching web and Android tokens (`BrandBlue`, `BrandOrange`, `SurfaceElevated`, `StatusBadge`).

- **Domain Layer**:
  - Independent of UI and persistence frameworks.
  - Contains core domain entities: `StudentProfile`, `AcademicRecord`, `AttendanceSession`, `AssessmentResult`, `NoticeAnnouncement`.
  - UseCases orchestrate user workflows: `RecordAttendanceUseCase`, `FetchPublishedResultsUseCase`, `VerifyCredentialSealUseCase`.

- **Data Layer**:
  - Implements repository interfaces defined in the domain layer.
  - Coordinates remote data synchronization and local database transactions.
  - Manages mutation queues ensuring offline actions (such as attendance marking) replay reliably upon network recovery.

- **Security & Core**:
  - `KeychainManager`: Manages JWT access tokens, refresh tokens, and encryption keys.
  - `CryptoSealValidator`: Verifies HMAC-SHA256 tamper seals and public key signatures on digital marksheets and APAAR ID cards.
  - `NetworkMonitor`: Uses `NWPathMonitor` to broadcast cellular, Wi-Fi, and offline status transitions.

---

## 4. Feature Parity Matrix

The iOS app maintains parity with the Web portal and Android application across roles and core capabilities:

| Feature Area | Web Portal | Android App (Kotlin) | iOS App (SwiftUI Target) |
|---|---|---|---|
| **Multi-Tenant Onboarding** | Full Portal (Register & Review) | View Status Only | View Status Only |
| **Academic Setup (Classes, Subjects)** | Full Configurator | Read-Only Summary | Read-Only Summary |
| **Student Digital ID Card (APAAR)** | Responsive View + Print | Jetpack Compose + Offline QR | SwiftUI + PassKit + Offline QR |
| **Credential Verification (Public)** | Web Scanner + Token Input | Camera Barcode Scanner | AVFoundation Camera Scanner |
| **Teacher Workspace (Attendance)** | Grid Table Entry | Offline Session Entry | Offline Session Entry |
| **Teacher Workspace (Timetable)** | Interactive Grid | Daily Agenda View | Daily Agenda / WidgetKit |
| **Assessments & Marks Entry** | Draft, Moderation, Publish | Draft Marks Entry | Draft Marks Entry |
| **Student / Parent Result View** | Full Detailed Marksheet | Grade Breakdown Card | Grade Breakdown Card |
| **Announcements & Notice Board** | Targeted Authoring & Feed | Notice Feed + Ack Button | Notice Feed + Ack Button |
| **Parent-Child Linkage** | Admin Approval Dashboard | Link Request & Child Card | Link Request & Child Card |
| **Multilingual UI (13 Languages)** | i18next (JSON catalogs) | Android String XMLs | Swift String Catalogs (`.xcstrings`)|
| **Offline Sync & Outbox** | ServiceWorker / IndexedDB | Room + WorkManager | GRDB + BGTaskScheduler |
| **Data Protection Transparency** | Dedicated `/transparency` | In-App Privacy Charter | In-App Privacy Charter |

---

## 5. Offline Data Synchronization Engine

Consistent with the Android Room architecture, iOS implements an offline-first storage engine using **GRDB.swift** (a high-performance, robust SQLite toolkit for Swift):

### 5.1 Outbox Mutation Pattern

When a teacher submits an attendance roster or a student acknowledges a notice without internet connectivity:
1. The mutation is saved immediately to the local SQLite database inside a transaction.
2. A record is added to the `mutation_outbox` table:
   ```sql
   CREATE TABLE mutation_outbox (
       id TEXT PRIMARY KEY,
       endpoint TEXT NOT NULL,
       http_method TEXT NOT NULL,
       payload_json TEXT NOT NULL,
       idempotency_key TEXT NOT NULL,
       created_at DATETIME NOT NULL,
       retry_count INTEGER DEFAULT 0,
       last_error TEXT
   );
   ```
3. The UI reflects the change optimistically with a subtle "Pending Sync" badge.
4. When `NWPathMonitor` detects internet connectivity, the `SyncEngine` processes pending outbox rows sequentially, sending requests with the client-generated `Idempotency-Key` header.
5. Upon successful HTTP 200/201 response, the row is deleted from the outbox.

### 5.2 Background Sync Operations

iOS schedules background sync utilizing Apple's `BackgroundTasks` framework:
- Register `BGAppRefreshTask` identifier: `in.gov.chhatralekha.refresh`.
- When triggered by iOS in the background (during charging or idle periods), the application refreshes cached attendance summaries, student credential tokens, and school announcements.
- All background network operations enforce strict timeout limits (30 seconds) to conserve user battery.

---

## 6. Security, Privacy & Keychain Architecture

### 6.1 Credential & Token Storage

- Authentication credentials (JWT access token and refresh token) are stored in the iOS Keychain using the following access control attributes:
  ```swift
  let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword,
      kSecAttrAccount as String: "auth_tokens",
      kSecAttrService as String: "in.gov.chhatralekha",
      kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
  ]
  ```
- Sensitive offline student records are encrypted at rest using SQLCipher database encryption with a 256-bit AES key securely derived and stored inside the iOS Secure Enclave.

### 6.2 Apple Privacy Manifest (`PrivacyInfo.xcprivacy`)

To comply with App Store privacy requirements and the Indian Digital Personal Data Protection (DPDP) Act 2023:
- **Tracking Domains**: Zero. `NSPrivacyTracking` is set to `false`.
- **Collected Data Types**:
  - `NSPrivacyCollectedDataTypeUserID`: For session authentication only; never linked to third-party ad networks.
  - `NSPrivacyCollectedDataTypeOtherUserContent`: Academic records and attendance submitted by authorized school staff.
- **Required Reason APIs**:
  - `NSPrivacyAccessedAPITypeUserDefaults`: App preference storage (selected language, theme).
  - `NSPrivacyAccessedAPITypeSystemBootTime`: Calculating relative network timeout offsets.
  - `NSPrivacyAccessedAPITypeDiskSpace`: Ensuring sufficient storage before downloading offline credentials.

---

## 7. Phased Implementation Roadmap

```
2026 Q4 (Phase 1)         2027 Q1 (Phase 2)         2027 Q2 (Phase 3)         2027 Q3 (Phase 4)
+-----------------------+ +-----------------------+ +-----------------------+ +-----------------------+
|  Foundation & Wallet  | |   Teacher Workspace   | |  Offline Sync Engine  | | Institutional Admin   |
|  * SwiftUI App Shell  | |  * Class Rosters      | |  * GRDB Outbox Engine | |  * Verification Scan  |
|  * Auth & Keychain    | |  * Session Attendance | |  * BGAppRefreshTasks  | |  * Mark Moderation    |
|  * Student Digital ID | |  * Timetable Viewer   | |  * Conflict LWW Logic | |  * PassKit Apple      |
|  * 13 Indian Locales  | |  * Notice Board Ack   | |  * Zero-Network Mode  | |    Wallet Integration |
+-----------------------+ +-----------------------+ +-----------------------+ +-----------------------+
```

### Phase 1: Core Foundation & Digital Identity Wallet (Weeks 1 to 6)
- Project scaffold in Xcode with Swift 6 and strict concurrency.
- Networking layer connecting to FastAPI endpoints (`/api/auth/login`, `/api/me/*`).
- Student Digital ID card with dynamic offline QR rendering.
- Parent portal read-only view for linked children.
- Complete localization across all 13 Indian languages via `.xcstrings`.
- Public sustainability and privacy charter viewer.

### Phase 2: Faculty Workspace & Class Attendance (Weeks 7 to 12)
- Teacher dashboard displaying assigned grades, sections, and subjects.
- Daily and period-wise attendance marking screen with bulk present/absent toggles.
- Timetable viewer with live day schedule highlights.
- Announcements notice board with urgent notification badges and acknowledgement capture.

### Phase 3: Offline Outbox & Background Sync (Weeks 13 to 18)
- GRDB.swift SQLite persistence layer with local entity migrations.
- Outbox mutation worker with retry policies and exponential backoff.
- Apple `BackgroundTasks` integration for background data refresh.
- Offline credential validation using CryptoKit.

### Phase 4: Institutional Verification & Platform Extensions (Weeks 19 to 24)
- Camera-based QR verification scanner using `AVFoundation`.
- Apple Wallet (PassKit) passes for validated student APAAR ID cards.
- Offline certificate verification against cryptographic HMAC and Ed25519 root keys.
- End-to-end automated UI test suite with XCTest and Accessibility Inspector validation.

---

## 8. Verification & Acceptance Criteria

Every milestone for the iOS client must pass the following acceptance gates prior to production release:
1. **Zero External Tracking**: Dynamic network audit verifies zero HTTP connections to third-party tracking or advertising endpoints.
2. **Offline Resilience**: App launches, navigates cached screens, renders digital ID QR codes, and records attendance while in Airplane Mode without error dialogs.
3. **Strict Concurrency**: Zero Swift 6 concurrency warnings or data race crashes.
4. **Accessibility Standards**: 100% WCAG 2.1 AA compliance verified via Apple Accessibility Inspector with VoiceOver support on all interactive controls.
5. **Localization Completeness**: Zero missing localization keys across all 13 supported Indian languages.

