# Authentication Security Audit

**Project:** ChhatraLekha  
**Audit ID:** AUD-STG02-AUTH-01  
**Target Codebase:** `chhatralekha/app/core/security.py`, `app/core/config.py`, `app/api/auth.py`, `app/api/deps.py`  
**Audit Date:** 2026-11-06  
**Auditor:** Antigravity (Advanced Agentic Coding)  
**Overall Status:** FAIL (Critical Authentication Bypass Identified)

---

## 1. Executive Summary

A comprehensive source code audit of ChhatraLekha's authentication layer was conducted. While core cryptographic primitives (bcrypt for passwords, PBKDF2-HMAC-SHA256 for student PINs) are sound, critical architectural vulnerabilities were identified that allow complete platform takeover in production.

Most critically, the demo login endpoint (`POST /api/auth/demo-login`) is exposed unconditionally with no environment check or authorization guard. An unauthenticated attacker can supply any role (including `national_admin` and `platform_operator`) to obtain fully signed administrative JWT tokens and upsert administrative records directly into the database. Furthermore, stateless JWT handling in the authentication dependency fails to verify user revocation status against the database per request, allowing invalidated sessions to remain active for up to 24 hours.

---

## 2. Authentication Vulnerabilities Summary

| ID | Severity | File and Line | Title | Impact |
|---|---|---|---|---|
| **SEC-AUTH-01** | **Critical** | `app/api/auth.py:186–250` | Unrestricted Demo Login Administrative Backdoor | Unauthenticated arbitrary admin token generation and full platform compromise |
| **SEC-AUTH-02** | **Low** | `app/api/auth.py:1–25` | Missing Documented Logout Endpoint | Inability for clients to explicitly invalidate server-side session state |
| **SEC-AUTH-03** | **Low** | `app/core/security.py:122–152` | Stateless Refresh Tokens without Rotation or Invalidation | Indefinite reuse of intercepted refresh tokens for up to 30 days |
| **SEC-AUTH-04** | **Medium** | `app/api/deps.py:42–85` | Token-Only Principal Construction Without Status Verification | Deactivated or modified users retain access until token expiry (up to 24 hours) |

---

## 3. Cryptographic Implementation and Token Lifecycle

### 3.1 Password and Credential Hashing

- **Password Hashing (`app/core/security.py:27–39`):**
  - Uses raw `bcrypt` with `bcrypt.gensalt(rounds=12)`.
  - Verification utilizes `bcrypt.checkpw()`.
  - Truncation handling: UTF-8 encoding is enforced prior to hashing.
  - Assessment: **STRONG**. Standard work factor of 12 provides robust defense against offline dictionary and brute-force attacks.
- **PIN Hashing (`app/core/security.py:42–62`):**
  - Uses `hashlib.pbkdf2_hmac` with SHA-256.
  - Iteration count: 120,000 iterations.
  - Salt generation: `secrets.token_hex(16)` (32 characters / 16 bytes entropy).
  - Verification utilizes `hmac.compare_digest` to prevent timing attacks.
  - Assessment: **STRONG**. Robust protection for low-entropy student/guardian numeric PINs.

### 3.2 Access Token Architecture

- **Token Generation (`app/core/security.py:65–98`):**
  - Algorithm: `HS256` symmetric signing.
  - Default Expiration: `settings.access_token_expire_minutes` = 1,440 minutes (24 hours).
  - Signed Claims:
    - `sub`: Principal subject identifier (`user_id`).
    - `role`: Primary role string (e.g., `institution_admin`, `teacher`).
    - `roles`: Role array.
    - `permissions`: Pre-computed list of granted permissions based on RBAC mapping.
    - `institution_id`: Assigned tenant institution identifier.
    - `exp`: Unix expiration timestamp.
    - `iat`: Unix issued-at timestamp.

### 3.3 Refresh Token Architecture

- **Token Generation (`app/core/security.py:122–152`):**
  - Algorithm: `HS256`.
  - Default Expiration: `settings.refresh_token_expire_days` = 30 days.
  - Signed Claims: `{"sub": subject, "type": "refresh", "exp": ..., "iat": ...}`.
- **Gaps Identified (SEC-AUTH-03):**
  - **No `jti` (JWT ID):** Refresh tokens lack unique identification.
  - **No Database Persistence:** Refresh tokens are entirely stateless; the database does not track issued refresh tokens or their associated devices/clients.
  - **No Refresh Token Rotation:** Calling `POST /api/auth/refresh` issues a new access token but does not issue or rotate the refresh token. The same refresh token can be used repeatedly for 30 days.
  - **No Revocation Mechanism:** If a user logs out, resets their password, or experiences device theft, existing refresh tokens cannot be revoked.

---

## 4. In-Depth Vulnerability Analysis

### 4.1 SEC-AUTH-01: Unrestricted Demo Login Administrative Backdoor (Critical)

**Location:** `chhatralekha/app/api/auth.py:186–250`

```python
@router.post("/demo-login", response_model=TokenResponse)
async def demo_login(
    payload: DemoLoginRequest,
    db: Any = Depends(get_database),
) -> TokenResponse:
    """Demo login helper for rapid evaluation and local testing.
    
    Generates a valid JWT for any role without requiring a password.
    Should be disabled or restricted in strict production deployments.
    """
    role = payload.role.strip()
    institution_id = (payload.institution_id or "INST-DEMO-001").strip()
    ...
```

**Flaws Identified:**
1. **Zero Environment Gating:** Despite the docstring stating it "should be disabled or restricted in strict production deployments," there is no conditional check against `settings.is_production` or `settings.environment`.
2. **Arbitrary Role Injection:** The caller can specify any arbitrary role in the JSON payload, including `national_admin`, `platform_operator`, or `aicte_admin`.
3. **Database Write and Persistence:** The endpoint executes an `upsert` on the production MongoDB `users` collection:
   ```python
   await db["users"].update_one(
       {"username": username},
       {"$set": user_doc},
       upsert=True,
   )
   ```
4. **Valid Token Generation:** It immediately signs and returns a production-grade access token and refresh token containing full administrative permissions.

**Remediation:**
1. Enforce strict environment gating at the top of `demo_login`:
   ```python
   if settings.is_production or settings.environment.lower() == "production":
       raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
           detail="Demo login is disabled in production environments",
       )
   ```
2. Restrict allowed demo roles to non-administrative roles (`student`, `teacher`, `parent`), or require a dedicated development secret key.

---

### 4.2 SEC-AUTH-04: Session Revocation and Principal Verification (Medium)

**Location:** `chhatralekha/app/api/deps.py:42–85`

```python
async def get_current_principal(
    token: str = Depends(oauth2_scheme),
) -> Principal:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return Principal(
        subject=payload["sub"],
        role=payload["role"],
        roles=payload.get("roles", [payload["role"]]),
        permissions=set(payload.get("permissions", [])),
        institution_id=payload.get("institution_id"),
    )
```

**Flaws Identified:**
1. `get_current_principal` constructs the `Principal` object solely from JWT claims without querying MongoDB to verify:
   - Whether the user account exists and has not been deleted.
   - Whether `is_active` remains `True`.
   - Whether the user's role or permissions have been updated or revoked by an administrator.
2. If an administrator deactivates a compromised student or teacher account, that user retains complete API access until their JWT token expires (up to 24 hours later).

**Remediation:**
1. Implement a lightweight cache or direct DB query check in `get_current_user` / `get_current_principal` to verify user active status.
2. Alternatively, reduce access token lifetime to 15–30 minutes, relying on refresh tokens for renewal.

---

### 4.3 SEC-AUTH-02: Missing Documented Logout Endpoint (Low)

**Location:** `chhatralekha/app/api/auth.py:1–25`

**Flaws Identified:**
The router docstring explicitly advertises:
```text
POST /api/auth/logout -> Invalidate current token / session
```
However, no `/logout` route exists in `chhatralekha/app/api/auth.py`. Clients cannot notify the backend of session termination, leaving tokens active in browser storage or client caches until expiration.

**Remediation:**
Implement `POST /api/auth/logout` that accepts the refresh token, revokes it (or logs the termination), and instructs the client to purge stored authentication tokens.

---

## 5. Prioritized Remediation Roadmap

1. **P0 (Critical):** Gate `POST /api/auth/demo-login` behind `not settings.is_production`. Prevent upsert of national/platform admin roles via demo login.
2. **P1 (High):** Add user status (`is_active`) verification in `get_current_principal` or reduce access token lifetime to 30 minutes.
3. **P2 (Medium):** Implement refresh token persistence and rotation in MongoDB with `jti` tracking and revocation.
4. **P3 (Low):** Implement `POST /api/auth/logout` endpoint matching API documentation.

