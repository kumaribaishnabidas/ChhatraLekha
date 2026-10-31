# ChhatraLekha — Authentication & Multi-Membership Workflow

**Document Version:** 1.0.0  
**Status:** Approved Target Architecture (Stage 0 Deliverable)

---

## 1. Authentication & Context Switching Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Student, Parent, Faculty, or Admin)
    participant Client as Frontend (Web/Mobile)
    participant Auth as Auth Service (/api/v1/auth)
    participant Membership as Membership Service
    participant Audit as Cryptographic Audit Trail
    
    User->>Client: Enters Email & Password
    Client->>Auth: POST /api/v1/auth/login { email, password }
    Auth->>Auth: Validate Credentials (bcrypt hash verify)
    Auth->>Membership: Query Active Memberships (user_id)
    Membership-->>Auth: [Membership A (College, Student), Membership B (School, Parent)]
    
    alt Single Membership
        Auth->>Auth: Mint JWT Token (Scoped to Primary Institution)
        Auth->>Audit: Append Signed Event (USER_LOGIN, actor=user_id)
        Auth-->>Client: 200 OK { access_token, refresh_token, active_membership, memberships: [1] }
        Client->>Client: Launch Role Dashboard directly
    else Multiple Memberships
        Auth->>Auth: Mint Global Identity Token
        Auth-->>Client: 200 OK { access_token, memberships: [A, B] }
        Client->>User: Display Institution & Role Chooser Modal
        User->>Client: Selects Membership A (e.g. College B - Student)
        Client->>Auth: POST /api/v1/auth/switch-context { institution_id: "INST-0421" }
        Auth->>Auth: Mint Scoped Access Token (X-Institution-ID: INST-0421)
        Auth-->>Client: 200 OK { scoped_access_token, role: "student" }
        Client->>Client: Launch College Student Workspace
    end
```

---

## 2. Key Lifecycle Operations

### 2.1 User Registration & Activation
1. **Self-Registration:** New users can sign up with email and phone verification. Upon creation, a central `User` identity is established with zero institutional memberships.
2. **Claim Code Activation:** When an educational institution imports or enrols a student, it generates a single-use claim code. The student inputs this claim code during onboarding, linking their central `User` account to their pre-created `StudentProfile` and activating their `InstitutionMembership`.

### 2.2 Token Refresh & Expiration
- Access tokens expire every **15 minutes**.
- The client silently issues `POST /api/v1/auth/refresh` using the HTTP-only secure refresh token (valid for 7 days).
- If the user's membership status in that institution has been suspended or revoked, refresh is immediately rejected (`401 Unauthorized`), terminating session access.

### 2.3 Secure Logout & Session Revocation
- When `POST /api/v1/auth/logout` is called:
  1. The client clears local stores (Keychain on iOS, EncryptedSharedPreferences on Android, memory in Web).
  2. The server records the token JTI in `revoked_credentials`.
  3. A cryptographic audit event (`USER_LOGOUT`) is permanently appended.

