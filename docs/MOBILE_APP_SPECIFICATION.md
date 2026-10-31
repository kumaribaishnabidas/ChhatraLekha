# ChhatraLekha — Android & iOS Mobile Application Specification

Version: 1.0  
Product: ChhatraLekha  
Platforms: Android (Kotlin 2.2 / Jetpack Compose) and iOS (Swift 5.10 / SwiftUI)  
Audience: Students, Parents/Guardians, Teachers/Faculty, and Institution Administrators  

---

## 1. Executive Architecture Summary

ChhatraLekha provides native mobile client applications for both **Android** and **iOS** communicating with a unified, secure FastAPI and MongoDB cloud backend. Both native clients share a common architectural philosophy:
- **Offline-First Resilience**: Local data persistence (Room on Android, local file store/Core Data on iOS) ensuring that student credentials, timetables, and class registers can be browsed and operated even without cellular or Wi-Fi connectivity.
- **Repository Pattern & MVVM**: Complete decoupling of presentation views from network clients and database layers.
- **Privacy by Design**: Compliance with the Digital Personal Data Protection (DPDP) Act 2023, ensuring zero commercial advertising, zero tracking cookies, and strict protection for minors under 18 years of age.
- **Opaque Verification Tokens**: Public QR verification codes never contain plaintext student identifiers (such as the 12-digit APAAR ID or contact numbers). Verification tokens are cryptographically generated, time-bounded, and revocable.

---

## 2. Multi-Role Matrix

Both Android and iOS clients implement persona-aware interfaces:

| Role | Target Persona | Primary Mobile Capabilities |
|---|---|---|
| **Student** | Enrolled learner | Academic wallet, verifiable credential QR seals, attendance logs, examination results, timetable, institutional announcements |
| **Parent / Guardian** | Family & guardians | Attendance updates, examination report cards, school notices, direct teacher consultation contacts |
| **Teacher / Faculty** | Classroom educators | Assigned course cohorts, daily roll-call attendance marking with offline queue, assessment mark entry |
| **Institution Administrator** | School/college leadership | Sanctioned intake quota tracking, student register, staff directories, audit trail inspection |
| **Third-Party Verifier** | Employers & universities | Instant QR badge scanning and token verification against cryptographic seals |

---

## 3. Offline-First Synchronization Protocol

Both mobile applications implement a resilient bidirectional synchronization protocol:

```
[User Action Offline] 
       │
       ▼
[Local Persistence Store] (Room on Android / OfflineDataStore on iOS)
       │
       ▼
[Pending Mutations Queue] (SQLite / Encrypted JSON)
       │
       ▼
[Network Monitor Observer] (NWPathMonitor on iOS / ConnectivityManager on Android)
       │
   (Network Satisfied)
       ▼
[Background Sync Worker] (WorkManager on Android / Task Background Sync on iOS)
       │
       ├──► 200 OK: Mark record SYNCED, remove from Pending Queue
       ├──► 409 Conflict: Apply server-authoritative resolution, flag for review
       └──► 5xx / Timeout: Exponential backoff (1s, 2s, 4s, 8s, max 5 retries)
```

---

## 4. Mobile Security & Credential Protection

### Android Security Architecture
- **Hardware Keystore**: Encryption keys for sensitive local databases and tokens are stored in the Android Keystore system (`AndroidKeyStore`).
- **Network Security Config**: Strictly mandates HTTPS (`cleartextTrafficPermitted="false"`) across all endpoints.
- **Tamper Evidence**: Digital credential seals calculated using HMAC-SHA256 and Ed25519 signatures.

### iOS Security Architecture
- **Apple Keychain Services**: Authentication JWT tokens and session keys are securely stored in the iOS Keychain (`kSecClassGenericPassword` with `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`).
- **App Transport Security (ATS)**: Enforces TLS 1.3 encryption across all network calls.
- **Biometric Authentication**: Native Face ID and Touch ID integration using `LocalAuthentication` with automatic fallback to device passcode.

---

## 5. Store Release Checklists

### Google Play Store (Android)
- [x] Application Package ID: `com.chhatralekha.app`
- [x] Target SDK: `36` (Android 16), Minimum SDK: `24` (Android 7.0)
- [x] Compilation: Modern Android App Bundle (`.aab`) with ProGuard/R8 optimization
- [x] Declarations: Complete Google Play Data Safety declaration reflecting zero advertising and zero third-party data sharing
- [x] Permissions: Strictly minimal (`INTERNET`, `CAMERA` for QR scanning only, `POST_NOTIFICATIONS`)

### Apple App Store (iOS)
- [x] Bundle Identifier: `com.chhatralekha.app`
- [x] Target Platform: iOS 16.0+, iPadOS 16.0+
- [x] Privacy Nutrition Labels: Discloses minimal authentication data usage, zero tracking, zero cross-app tracking
- [x] App Store Guidelines: Compliance with Guideline 5.1.1 (Data Collection and Storage) and minor protections under DPDP Act 2023
- [x] Declarations: Clean `ITSAppUsesNonExemptEncryption` set to `NO`

---

## 6. Development Priority Roadmap

1. **P0 (Critical Foundation)**:
   - Authenticated session management and role-based access control.
   - Offline-first cache reliability and pending mutation sync queues.
   - Privacy-preserving credential tokens without plaintext APAAR IDs.
2. **P1 (User Experience & Engagement)**:
   - Push notifications for attendance alerts and exam notices (FCM and APNs).
   - Accessibility compliance (WCAG 2.1 AA, TalkBack and VoiceOver).
   - Biometric unlock integration.
3. **P2 (Advanced Operations)**:
   - Batch offline CSV import for institutional leaders.
   - Comprehensive multi-cohort analytical reports.

