# Profile and Notification Security Audit

**Project:** ChhatraLekha  
**Audit ID:** AUD-STG02-PRFN-01  
**Target Codebase:** `chhatralekha/app/modules/profiles/`, `chhatralekha/app/modules/notifications/`  
**Audit Date:** 2026-11-06  
**Auditor:** Antigravity (Advanced Agentic Coding)  
**Overall Status:** FAIL (High-Severity IDOR in Notifications and Insecure Email Verification)

---

## 1. Executive Summary

This audit reviewed the security of the shared platform foundation modules: Profile Management (`app/modules/profiles/`) and Notification System (`app/modules/notifications/`).

While the profile module implements commendable role boundary protections (preventing privilege escalation during self-service profile updates) and validates avatar uploads, two serious security vulnerabilities were discovered:
1. **Notification IDOR (SEC-NOTIF-01):** The functions `mark_as_read` and `delete_notification` receive `user_id` as a parameter but omit it from the MongoDB mutation filters (`{"id": notification_id}`), allowing any authenticated user to tamper with or delete any other user's notifications.
2. **Insecure Email Verification (SEC-EMAIL-01):** Email verification codes are returned in plaintext in API responses (`demo_code`), a universal hardcoded bypass code (`"123456"`) is accepted unconditionally without environment checks, and codes lack expiration timestamps and brute-force attempt limits.

---

## 2. Findings Summary Table

| ID | Severity | File and Line | Title | Impact |
|---|---|---|---|---|
| **SEC-NOTIF-01** | **High** | `app/modules/notifications/service.py:175–209` | IDOR on Notification Mark Read and Deletion | Any user can mark as read or delete notifications belonging to any other user |
| **SEC-EMAIL-01** | **Medium** | `app/modules/profiles/service.py:399, 415` | Verification Code Disclosure and Hardcoded Bypass | Unauthorized email verification and spoofed institutional email association |

---

## 3. Profile Management Security Analysis (`app/modules/profiles/`)

### 3.1 Field-Level Update Restrictions

- **Endpoint:** `PATCH /api/profiles/me`
- **Schema:** `UserProfileUpdate` (`app/modules/profiles/schemas.py:53–67`)
- **Evaluation:** **SECURE**.
  - Permitted fields: `display_name`, `phone_number`, `preferred_language`, `theme`, `high_contrast`, `large_font`, `screen_reader_optimised`, `haptic_feedback_enabled`, `quiet_hours_start`, `quiet_hours_end`.
  - Privileged fields (`roles`, `permissions`, `institution_id`, `apaar_id`, `is_active`, `is_verified`) are strictly excluded from the schema and cannot be modified via self-service endpoints.

### 3.2 Avatar and Profile Picture Handling

- **Endpoint:** `POST /api/profiles/me/picture`
- **Validation:**
  - Enforces platform targeting (`all`, `web`, `android`, `ios`).
  - Decodes base64 payload and validates image magic bytes via `Pillow` (supporting PNG, JPEG, WEBP).
  - Maximum upload size capped at 2MB (`MAX_IMAGE_SIZE_BYTES = 2 * 1024 * 1024`).
  - Enforces bounding dimensions (`800x800` max resolution) and re-encodes clean image buffers, effectively mitigating image decompression bombs and malicious payload embedding.

### 3.3 SEC-EMAIL-01: Insecure Email Verification Workflow (Medium)

**Location:** `chhatralekha/app/modules/profiles/service.py:390–425`

```python
# In request_email_verification:
code = "".join(random.choices(string.digits, k=6))
...
return {
    "status": "code_sent",
    "email": email,
    "demo_code": code,  # <-- CRITICAL LEAKAGE
}

# In verify_email:
async def verify_email(db: Any, user_id: str, email: str, code: str) -> bool:
    ...
    if code == "123456" or code == entry.get("verification_code"): # <-- HARDCODED BYPASS
        ...
```

**Flaws Identified:**
1. **Plaintext Code Leak:** The generated verification code is returned directly in the JSON response payload (`demo_code`), defeating out-of-band email verification.
2. **Universal Bypass Code:** Entering `"123456"` validates any email address without checking whether the application is running in production or development.
3. **Missing Expiry Window:** Verification codes are stored without a TTL (Time-To-Live) or `expires_at` timestamp.
4. **No Rate Limiting:** No limit is placed on invalid verification attempts, enabling brute-force attacks against the 6-digit space.

**Remediation:**
1. Never return `demo_code` unless `settings.environment == "development"` and `settings.is_production is False`.
2. Remove hardcoded `"123456"` bypass or restrict strictly to non-production demo environments.
3. Add a 15-minute expiration timestamp to pending verification entries and limit attempts to 5 per code.

---

## 4. Notification Module Security Analysis (`app/modules/notifications/`)

### 4.1 SEC-NOTIF-01: IDOR on Single Notification Operations (High)

**Location:** `chhatralekha/app/modules/notifications/service.py:175–209`

```python
async def mark_as_read(db: Any, user_id: str, notification_id: str) -> bool:
    """Mark a single notification as read for a user."""
    now = datetime.now(timezone.utc)
    result = await db["notifications"].update_one(
        {"id": notification_id},                     # <-- USER_ID NOT IN FILTER
        {"$set": {"read": True, "read_at": now}},
    )
    return result.modified_count > 0


async def delete_notification(db: Any, user_id: str, notification_id: str) -> bool:
    """Delete a notification."""
    result = await db["notifications"].delete_one(
        {"id": notification_id}                      # <-- USER_ID NOT IN FILTER
    )
    return result.deleted_count > 0
```

**Flaws Identified:**
- Both service functions accept `user_id: str` from the authenticated caller (`principal.subject`), but neither function includes `user_id` in the MongoDB query filter.
- In `mark_as_read`: Any user who knows or guesses a `notification_id` can mark another user's critical notification (e.g., examination alert, disciplinary notice, fee reminder) as read.
- In `delete_notification`: Any user can permanently delete another user's notification from the database.

**Remediation:**
Include `user_id` in the MongoDB query filter:
```python
async def mark_as_read(db: Any, user_id: str, notification_id: str) -> bool:
    now = datetime.now(timezone.utc)
    result = await db["notifications"].update_one(
        {"id": notification_id, "user_id": user_id},
        {"$set": {"read": True, "read_at": now}},
    )
    return result.modified_count > 0


async def delete_notification(db: Any, user_id: str, notification_id: str) -> bool:
    result = await db["notifications"].delete_one(
        {"id": notification_id, "user_id": user_id}
    )
    return result.deleted_count > 0
```

### 4.2 Preference Enforcement and Quiet Hours

- **Endpoints:** `GET /api/notifications/preferences`, `PUT /api/notifications/preferences`
- **Evaluation:** **SECURE**.
  - Properly isolates preferences by `user_id`.
  - Enables granular toggling across notification categories (`academic`, `attendance`, `examinations`, `announcements`, `system`).
  - Supports channel enablement (`in_app`, `push`, `email`, `sms`).
  - Validates quiet hours time strings in `HH:MM` 24-hour format.

---

## 5. Prioritized Remediation Steps

1. **P1 (High):** Patch `mark_as_read` and `delete_notification` in `app/modules/notifications/service.py` to enforce `{"id": notification_id, "user_id": user_id}`.
2. **P2 (Medium):** Gate `demo_code` response and `"123456"` bypass code behind `settings.is_production is False` in `app/modules/profiles/service.py`. Add expiration timestamp verification.

