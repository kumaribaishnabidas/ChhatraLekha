# ChhatraLekha iOS Native Application

The native iOS client for ChhatraLekha, built with **Swift 5** and **SwiftUI**.

## Overview
The iOS application mirrors the Android native application and web portal architectures, connecting to the unified FastAPI / MongoDB backend. It provides role-specific workspaces for:
- **Students**: Academic wallet, cryptographic credential seals, attendance logs, and exam marks.
- **Parents / Guardians**: Ward overview, session attendance monitoring, school notices, and teacher consultations.
- **Teachers / Faculty**: Class rosters, roll-call attendance recording with offline queuing, and marks review.
- **Institution Administrators**: Intake quota tracking, enrolled student register, and audit trail verification.
- **Third-Party Verifiers**: Instant QR/token verification without exposing student PII or raw 12-digit APAAR IDs.

---

## Architectural Highlights
- **Architecture**: Model-View-ViewModel (MVVM) with Repository and DataStore patterns.
- **User Interface**: 100% declarative SwiftUI with dynamic Light and Dark mode styling.
- **Networking**: `URLSession` with modern `async/await` concurrency and `NWPathMonitor` connection observer.
- **Offline-First Persistence**: `OfflineDataStore` local atomic serialization with `SyncQueue` mutation queue and exponential backoff.
- **Security & Cryptography**: Apple Keychain Services (`kSecClassGenericPassword`), biometric Face ID / Touch ID (`LocalAuthentication`), and DPDP Act 2023 compliance.
- **Verification Engine**: Native CoreImage QR generation and validation.

---

## Directory Structure
```
ios/
├── ChhatraLekha.xcodeproj/     # Xcode project configuration
├── ChhatraLekha/
│   ├── App/                   # Application entrypoint (@main)
│   ├── Core/
│   │   ├── Models/            # Domain models, UserRole, and SyncState
│   │   ├── Network/           # ApiClient, ApiEndpoint, NetworkMonitor
│   │   ├── Storage/           # KeychainManager, OfflineDataStore, SyncQueue
│   │   ├── Security/          # BiometricManager, PrivacyProtection
│   │   └── Validation/        # Deterministic 12-digit ApaarValidator
│   ├── UI/
│   │   ├── Theme/             # Colors, typography, and styling
│   │   ├── Components/        # StatCard, StatusBanner, PrimaryButton, EmptyState
│   │   └── Navigation/        # MainTabView with role-specific tab bars
│   ├── Features/              # Auth, Student, Guardian, Teacher, Admin, Verifier, Settings
│   ├── Resources/             # Info.plist, Assets.xcassets
│   └── Tests/                 # XCTest unit suites
└── README.md
```

---

## Build & Test Instructions
Open `ChhatraLekha.xcodeproj` in Xcode 15 or later:
```bash
# Build the application target using xcodebuild
xcodebuild -project ChhatraLekha.xcodeproj -scheme ChhatraLekha -destination "platform=iOS Simulator,name=iPhone 15" build

# Run unit test targets
xcodebuild test -project ChhatraLekha.xcodeproj -scheme ChhatraLekha -destination "platform=iOS Simulator,name=iPhone 15"
```

